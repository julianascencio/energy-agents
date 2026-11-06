"""Incremental, advisory bridge-power screen for an existing finance role.

No provider calls, contracts, equipment control or external writes are available.
"""
import argparse
import hashlib
import json
import math
from copy import deepcopy
from importlib.resources import files
from pathlib import Path

from ..orchestrator import AgentTask, run_orchestrator
from .bess import ROLE


def reference_case():
    return json.loads(files('energy_agents').joinpath('data/bridge_power/case.json').read_text())


def validate_case(case):
    if case.get('schema_version') != '1.0' or case.get('currency') != 'EUR':
        raise ValueError('Expected version 1.0, EUR')
    if case.get('classification') != 'synthetic_scenario':
        raise ValueError('This model requires explicitly synthetic scenario inputs')
    source = case['source']
    if not source['url'].startswith('https://') or source['classification'] != 'issuer_announcement':
        raise ValueError('Cited issuer announcement required')
    for key in ('publication_date', 'event_date'):
        from datetime import date
        date.fromisoformat(source[key])
    a = case['assumptions']
    for key in ('it_mw', 'pue', 'utilization', 'availability', 'margin_eur_per_it_mwh',
                'power_eur_per_facility_mwh', 'monthly_fixed_eur', 'upfront_eur',
                'annual_discount_rate', 'hours_per_month'):
        v = a[key]
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v < 0:
            raise ValueError(f'{key} must be nonnegative finite numeric')
    if a['it_mw'] <= 0 or a['pue'] < 1 or not 0 < a['hours_per_month'] <= 744:
        raise ValueError('Invalid IT power, PUE or month length')
    if any(a[k] > 1 for k in ('utilization', 'availability', 'annual_discount_rate')):
        raise ValueError('Fraction outside 0..1')
    for key in ('grid_month', 'bridge_month'):
        if type(a[key]) is not int or not 0 <= a[key] <= 120:
            raise ValueError('Commissioning months must be integers in 0..120')
    if not a['cost_basis']:
        raise ValueError('Cost boundaries required')


def screen_bridge_power(case):
    """Incremental NPV over waiting for the grid; equal operations afterwards cancel.

    Month 0 is today; operating intervals are [bridge_month, grid_month).
    Cash is paid at each interval end. Incremental upfront expense is paid today.
    Facility energy = IT energy * PUE. Margin excludes electricity costs.
    """
    validate_case(case)
    a = case['assumptions']
    months = max(0, a['grid_month'] - a['bridge_month'])
    it_energy = a['it_mw'] * a['hours_per_month'] * a['utilization'] * a['availability']
    facility_energy = it_energy * a['pue']
    contribution = it_energy * a['margin_eur_per_it_mwh']
    power_cost = facility_energy * a['power_eur_per_facility_mwh']
    monthly_cash = contribution - power_cost - a['monthly_fixed_eur']
    rows = []
    for month in range(a['bridge_month'] + 1, a['grid_month'] + 1):
        factor = (1 + a['annual_discount_rate']) ** (-month / 12)
        rows.append({'month_end': month, 'it_mwh': it_energy, 'facility_mwh': facility_energy,
                     'contribution_eur': contribution, 'power_cost_eur': power_cost,
                     'fixed_cost_eur': a['monthly_fixed_eur'], 'net_cash_eur': monthly_cash,
                     'discount_factor': factor, 'pv_eur': monthly_cash * factor})
    factors = math.fsum(r['discount_factor'] for r in rows)
    npv = math.fsum(r['pv_eur'] for r in rows) - a['upfront_eur']
    break_even = ((a['upfront_eur'] / factors + power_cost + a['monthly_fixed_eur']) / it_energy
                  if factors and it_energy else None)
    return {'classification': 'modelled_from_synthetic_inputs', 'currency': 'EUR',
            'case_sha256': hashlib.sha256(json.dumps(case, sort_keys=True).encode()).hexdigest(),
            'source': deepcopy(case['source']), 'early_months': months, 'monthly': rows,
            'baseline_wait_npv_eur': 0.0, 'bridge_incremental_npv_eur': npv,
            'screened_choice': 'bridge_for_diligence' if npv > 0 else 'wait_for_grid',
            'best_incremental_npv_eur': max(0.0, npv),
            'break_even_margin_eur_per_it_mwh': break_even, 'human_review_required': True,
            'llm_evaluation': {'executed': False, 'cost': None, 'latency': None, 'tokens': None}}


def run_bridge_workflow(case, planner=None):
    """Reuse the orchestrator and finance role with validation before evaluation.

    The finance runner consumes the validated upstream case, not mutable planner data.
    Scheduler permissions remain limited to delegation of these two fixed tasks.
    """
    def evidence_runner(context):
        validated = context['payload']['case']
        validate_case(validated)
        return {'success': True, 'case': validated,
                'validation': 'schema_and_classification_only_not_source_truth'}

    def finance_runner(context):
        validated = context['upstream']['evidence']['case']
        return {'success': True, 'screen': screen_bridge_power(validated)}

    return run_orchestrator(
        [AgentTask('evidence', 'evidence_contract', payload={'case': deepcopy(case)}),
         AgentTask('finance', ROLE.id, dependencies=('evidence',))],
        {'evidence_contract': evidence_runner, ROLE.id: finance_runner}, planner, max_calls=4,
    )


def inspect_edi_inventory(catalogue_root):
    """Optional explicit EDI loader/validator execution; inventory only, no economics.

    Requires energy-data-retrieval 0.1.0 from the recorded source commit; see case history.
    Never aggregate IT, facility and grid ratings or turn design PUE into measured PUE.
    """
    from energy_data_retrieval.data_center_catalogue.catalogue import load_records, validate_record

    root = Path(catalogue_root)
    if not (root / 'records').is_dir():
        raise ValueError('Expected catalogue/records directory')
    sources = json.loads((root / 'sources.json').read_text())
    rows = list(load_records(root))
    for row in rows:
        validate_record(row, sources)
    return {'records': len(rows), 'input_sha256': hashlib.sha256(
        json.dumps(rows, sort_keys=True).encode()).hexdigest(),
        'execution': 'EDI load_records and validate_record',
        'use': 'inventory_context_only_not_financial_calibration'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('outputs/bridge_power'))
    args = parser.parse_args()
    case = reference_case()
    run = run_bridge_workflow(case)
    if not run['success']:
        raise RuntimeError('Workflow failed')
    baseline = screen_bridge_power(case)
    assert run['results']['finance']['screen'] == baseline
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / 'report.json').write_text(json.dumps(run, indent=2) + '\n')
    print(json.dumps(baseline, indent=2))


if __name__ == '__main__':
    main()
