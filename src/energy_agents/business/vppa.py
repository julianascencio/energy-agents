"""Advisory VPPA buyer cash-flow reconciliation, not trade execution."""
import argparse
import hashlib
import json
import math
from copy import deepcopy
from datetime import datetime, timedelta
from importlib.resources import files
from pathlib import Path

from ..orchestrator import AgentTask, run_orchestrator
from .bess import ROLE


def reference_case():
    return json.loads(files('energy_agents').joinpath('data/vppa/case.json').read_text())


def validate_case(case):
    if case.get('version') != '1.0' or case.get('classification') != 'synthetic':
        raise ValueError('Explicit version 1.0 synthetic inputs required')
    if case.get('currency') != 'EUR' or not case['source']['url'].startswith('https://'):
        raise ValueError('EUR and cited source required')
    if case['source']['classification'] != 'issuer_announcement':
        raise ValueError('Source classification required')
    for key in ('publication_date', 'event_date'):
        datetime.strptime(case['source'][key], '%Y-%m-%d')

    def number(x, nonnegative=False):
        if isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x):
            raise ValueError('Finite numeric inputs required')
        if nonnegative and x < 0:
            raise ValueError('Energy and costs must be nonnegative')

    for key in ('strike_eur_mwh', 'fee_eur_mwh', 'budget_eur'):
        number(case[key], key != 'strike_eur_mwh')
    rows = case['intervals']
    if not 1 <= len(rows) <= 8784:
        raise ValueError('Bounded nonempty interval series required')
    previous_end = None
    for row in rows:
        start = datetime.fromisoformat(row['start_utc'].replace('Z', '+00:00'))
        if start.utcoffset() != timedelta(0):
            raise ValueError('UTC interval start required')
        number(row['hours'], True)
        if row['hours'] <= 0 or (previous_end is not None and start != previous_end):
            raise ValueError('Intervals must be contiguous, unique and positive-duration')
        previous_end = start + timedelta(hours=row['hours'])
        for key in ('load_mwh', 'solar_mwh', 'wind_mwh'):
            number(row[key], True)
        for key in ('load_price_eur_mwh', 'reference_price_eur_mwh'):
            number(row[key])
    if sum(r['load_mwh'] for r in rows) <= 0:
        raise ValueError('Positive load required')
    if not case['mixes'] or len(case['mixes']) > 20:
        raise ValueError('Supply 1..20 explicit mixes')
    for name, solar_share in case['mixes'].items():
        if not name:
            raise ValueError('Mix name required')
        number(solar_share, True)
        if solar_share > 1:
            raise ValueError('Solar fraction outside 0..1')
    # Profile comparisons preserve contracted energy; no hidden normalization.
    solar = sum(r['solar_mwh'] for r in rows)
    wind = sum(r['wind_mwh'] for r in rows)
    if not solar or not math.isclose(solar, wind, rel_tol=1e-10):
        raise ValueError('Solar and wind alternatives must have equal positive MWh')


def reconcile_vppa(case):
    """Buyer pays retail load bill, receives Q*(reference-strike), and pays fees.

    Q is contracted generation MWh, never load or power. Negative settlement is
    a buyer payment. No physical supply or environmental-credit assertion.
    """
    validate_case(case)
    base = math.fsum(r['load_mwh'] * r['load_price_eur_mwh'] for r in case['intervals'])
    load = math.fsum(r['load_mwh'] for r in case['intervals'])
    alternatives = {}
    for name, share in case['mixes'].items():
        rows = []
        for row in case['intervals']:
            q = share * row['solar_mwh'] + (1 - share) * row['wind_mwh']
            settlement = q * (row['reference_price_eur_mwh'] - case['strike_eur_mwh'])
            bill = row['load_mwh'] * row['load_price_eur_mwh']
            fee = q * case['fee_eur_mwh']
            rows.append({'start_utc': row['start_utc'], 'contracted_mwh': q,
                         'retail_bill_eur': bill, 'buyer_receipt_eur': settlement,
                         'fee_eur': fee, 'net_cost_eur': bill - settlement + fee})
        energy = math.fsum(r['contracted_mwh'] for r in rows)
        receipts = math.fsum(r['buyer_receipt_eur'] for r in rows)
        fees = math.fsum(r['fee_eur'] for r in rows)
        net = base - receipts + fees
        alternatives[name] = {'intervals': rows, 'contracted_mwh': energy,
            'generation_to_load_energy_ratio': energy / load,
            'capture_reference_eur_mwh': case['strike_eur_mwh'] + receipts / energy,
            'buyer_receipt_eur': receipts, 'fees_eur': fees, 'net_cost_eur': net,
            'change_vs_unhedged_eur': net - base, 'effective_cost_eur_load_mwh': net / load,
            'over_budget_eur': max(0, net - case['budget_eur']),
            'break_even_strike_eur_mwh': case['strike_eur_mwh'] + (receipts - fees) / energy}
    return {'classification': 'modelled_synthetic', 'currency': 'EUR',
            'source': deepcopy(case['source']), 'unhedged_cost_eur': base,
            'load_mwh': load, 'alternatives': alternatives,
            'case_sha256': hashlib.sha256(json.dumps(case, sort_keys=True).encode()).hexdigest(),
            'human_review_required': True,
            'llm': {'executed': False, 'cost': None, 'tokens': None, 'latency': None}}


def run_vppa_workflow(case, planner=None):
    def evidence(context):
        validated = context['payload']['case']
        validate_case(validated)
        return {'success': True, 'case': validated}

    def finance(context):
        return {'success': True, 'report': reconcile_vppa(context['upstream']['evidence']['case'])}

    return run_orchestrator(
        [AgentTask('evidence', 'evidence_contract', payload={'case': case}),
         AgentTask('finance', ROLE.id, dependencies=('evidence',))],
        {'evidence_contract': evidence, ROLE.id: finance}, planner, max_calls=4)


def inspect_edi_wind(catalogue_root, country_code='ROU'):
    """Optional EDI loader/validator reuse; inventory context, never price calibration."""
    from energy_data_retrieval.wind_catalogue.catalogue import load_records, validate_record

    root = Path(catalogue_root)
    if not (root / 'records').is_dir():
        raise ValueError('Expected wind catalogue records directory')
    sources = json.loads((root / 'sources.json').read_text())
    rows = [r for r in load_records(root) if r.get('country_code') == country_code]
    for row in rows:
        validate_record(row, sources)
    return {'country_code': country_code, 'records': len(rows),
            'input_sha256': hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest(),
            'use': 'inventory_only_not_cash_flow_calibration'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('outputs/vppa'))
    args = parser.parse_args()
    case = reference_case()
    run = run_vppa_workflow(case)
    assert run['success'] and run['results']['finance']['report'] == reconcile_vppa(case)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / 'report.json').write_text(json.dumps(run, indent=2) + '\n')
    print(json.dumps(run['results']['finance']['report'], indent=2))


if __name__ == '__main__':
    main()
