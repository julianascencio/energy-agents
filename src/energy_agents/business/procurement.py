"""Advisory manufacturing-slot reservation under explicit joint scenarios.

Reuses the project-controls DAG scheduler and existing finance/orchestrator roles.
No procurement, supplier contact, live data retrieval or equipment control.
"""

import argparse
import hashlib
import json
import math
from copy import deepcopy
from datetime import date
from importlib.resources import files
from pathlib import Path

from ..commissioning import ROLE as CONTROLS_ROLE
from ..commissioning import number, schedule
from ..orchestrator import AgentTask, run_orchestrator
from .bess import ROLE as FINANCE_ROLE


def reference_case():
    return json.loads(files('energy_agents').joinpath('data/procurement/case.json').read_text())


def validate_case(case):
    """Validate declared evidence, not source truth or a supplier's ability to deliver."""
    if (case.get('schema_version'), case.get('currency'), case.get('classification')) != (
        '1.0', 'EUR', 'synthetic_scenario'
    ):
        raise ValueError('Expected version 1.0, EUR and synthetic_scenario')
    source = case['source']
    if (source['classification'] != 'operator_report' or
            not source['url'].startswith('https://') or not source['locator']):
        raise ValueError('Cited operator report required')
    published = date.fromisoformat(source['publication_date'])
    if date.fromisoformat(source['event_date']) > published:
        raise ValueError('Report release cannot follow publication')
    if published > date.fromisoformat(case['as_of']):
        raise ValueError('Future evidence')
    a = case['assumptions']
    if a['classification'] != 'synthetic_assumptions' or not a['cost_boundary']:
        raise ValueError('Explicit assumption classification and cost boundary required')
    for key in ('reservation_fee_eur', 'exercise_premium_eur', 'downside_limit_eur'):
        number(a[key], key, minimum=0, maximum=1e12)
    number(a['monthly_contribution_eur'], 'monthly_contribution_eur',
           minimum=-1e12, maximum=1e12)
    for key in ('annual_discount_rate', 'cancel_refund_fraction'):
        number(a[key], key, minimum=0, maximum=1)
    for key in ('decision_month', 'horizon_months', 'installation_months'):
        if type(a[key]) is not int or not 0 <= a[key] <= 120:
            raise ValueError(f'{key} must be an integer in 0..120')
    if a['horizon_months'] <= a['decision_month']:
        raise ValueError('Horizon must exceed decision month')
    states = case['scenarios']
    if not isinstance(states, list) or not 1 <= len(states) <= 20:
        raise ValueError('Supply 1..20 mutually exclusive joint scenarios')
    ids = [s['id'] for s in states]
    if any(not isinstance(i, str) or not i.strip() for i in ids) or len(set(ids)) != len(ids):
        raise ValueError('Scenario IDs must be unique nonempty strings')
    for s in states:
        number(s['probability'], 'probability', minimum=0, maximum=1)
        if type(s['proceed']) is not bool:
            raise ValueError('proceed must be boolean')
        if s['proceed']:
            for key in ('site_ready_month', 'wait_arrival_month', 'reserved_arrival_month'):
                if type(s[key]) is not int or not 0 <= s[key] <= 120:
                    raise ValueError(f'{key} must be an integer in 0..120')
            if s['wait_arrival_month'] < a['decision_month']:
                raise ValueError('Wait delivery cannot precede the order decision')
    if not math.isclose(math.fsum(s['probability'] for s in states), 1, abs_tol=1e-12,
                        rel_tol=0):
        raise ValueError('Joint probabilities must sum to one; no silent normalization')


def delivery_scenarios(case):
    """Reuse DAG scheduling with an explicit 30-day planning-month conversion.

    Delivery, site readiness and approval must all finish before installation.
    Monthly financial periods are equal planning periods, not calendar forecasts.
    """
    validate_case(case)
    a = case['assumptions']
    rows = []
    for s in case['scenarios']:
        row = deepcopy(s)
        for option, arrival in [('wait', 'wait_arrival_month'),
                                ('reserve', 'reserved_arrival_month')]:
            completion = None
            if s['proceed']:
                tasks = [{'id': name, 'dependencies': [], 'duration_days': months * 30}
                         for name, months in [('approval', a['decision_month']),
                                              ('site', s['site_ready_month']),
                                              ('delivery', s[arrival])]]
                tasks.append({'id': 'installation',
                              'dependencies': ['approval', 'site', 'delivery'],
                              'duration_days': a['installation_months'] * 30})
                completion = int(schedule(tasks)['completion_day'] / 30)
            row[f'{option}_cod_month'] = completion
        rows.append(row)
    return rows


def _value(case, deliveries):
    a = case['assumptions']
    def discount(month):
        return (1 + a['annual_discount_rate']) ** (-month / 12)

    rows = []
    for s in deliveries:
        cash = []
        for month in range(1, a['horizon_months'] + 1):
            wait = s['proceed'] and month > s['wait_cod_month']
            reserve = s['proceed'] and month > s['reserve_cod_month']
            incremental = (int(reserve) - int(wait)) * a['monthly_contribution_eur']
            if incremental:
                cash.append({'month_end': month, 'incremental_contribution_eur': incremental,
                             'pv_eur': incremental * discount(month)})
        premium = a['exercise_premium_eur'] if s['proceed'] else 0
        refund = 0 if s['proceed'] else a['reservation_fee_eur'] * a['cancel_refund_fraction']
        operating_pv = math.fsum(c['pv_eur'] for c in cash)
        net = operating_pv - a['reservation_fee_eur'] + (refund - premium) * discount(
            a['decision_month'])
        rows.append({**deepcopy(s), 'operating_cash': cash,
                     'incremental_operating_pv_eur': operating_pv,
                     'exercise_premium_eur': premium, 'refund_eur': refund,
                     'incremental_npv_eur': net})
    expected = math.fsum(s['probability'] * s['incremental_npv_eur'] for s in rows)
    active = [s for s in rows if s['probability'] > 0]
    worst_loss = max(0, -min(s['incremental_npv_eur'] for s in active))
    cancel_p = math.fsum(s['probability'] for s in rows if not s['proceed'])
    before_fee = math.fsum(s['probability'] * (s['incremental_operating_pv_eur'] -
                          s['exercise_premium_eur'] * discount(a['decision_month'])) for s in rows)
    fee_factor = 1 - cancel_p * a['cancel_refund_fraction'] * discount(a['decision_month'])
    ceiling = before_fee / fee_factor if fee_factor > 1e-12 else None
    feasible = worst_loss <= a['downside_limit_eur']
    return {'classification': 'modelled_from_synthetic_inputs', 'currency': 'EUR',
            'case_sha256': hashlib.sha256(json.dumps(case, sort_keys=True).encode()).hexdigest(),
            'source': deepcopy(case['source']), 'scenarios': rows,
            'wait_incremental_npv_eur': 0.0, 'reserve_expected_npv_eur': expected,
            'reserve_worst_loss_eur': worst_loss,
            'reserve_loss_probability': math.fsum(s['probability'] for s in rows
                                                  if s['incremental_npv_eur'] < 0),
            'break_even_reservation_fee_eur': ceiling,
            'downside_limit_passed': feasible,
            'screened_choice': 'reserve_for_diligence' if feasible and expected > 0 else 'wait',
            'human_review_required': True,
            'llm_evaluation': {'executed': False, 'cost': None, 'latency': None, 'tokens': None}}


def screen_reservation(case):
    """Expected incremental NPV versus ordering at approval; no full project valuation."""
    return _value(case, delivery_scenarios(case))


def run_procurement_workflow(case, planner=None):
    """Fixed evidence -> project controls -> finance handoffs; no new professional role."""
    def evidence(context):
        original = context['payload']['case']
        validate_case(original)
        return {'success': True, 'case': original, 'validation': 'declared_evidence_only'}

    def controls(context):
        original = context['upstream']['evidence']['case']
        return {'success': True, 'case': original, 'deliveries': delivery_scenarios(original)}

    def finance(context):
        upstream = context['upstream']['controls']
        # Check handoff against deterministic scheduling before accepting financial output.
        if upstream['deliveries'] != delivery_scenarios(upstream['case']):
            raise ValueError('Schedule handoff mismatch')
        return {'success': True, 'report': _value(upstream['case'], upstream['deliveries'])}

    return run_orchestrator(
        [AgentTask('evidence', 'evidence_contract', payload={'case': deepcopy(case)}),
         AgentTask('controls', CONTROLS_ROLE.id, ('evidence',)),
         AgentTask('finance', FINANCE_ROLE.id, ('controls',))],
        {'evidence_contract': evidence, CONTROLS_ROLE.id: controls, FINANCE_ROLE.id: finance},
        planner, max_calls=5,
    )


def cancellation_sensitivity(case, probabilities=(0, 0.2, 0.4, 0.6, 0.8, 1)):
    """Vary cancellation probability, keeping conditional proceed/cancel mixes fixed."""
    validate_case(case)
    totals = {flag: math.fsum(s['probability'] for s in case['scenarios'] if s['proceed'] == flag)
              for flag in (True, False)}
    if min(totals.values()) <= 0:
        raise ValueError('Sensitivity requires positive proceed and cancellation weights')
    rows = []
    for p in probabilities:
        number(p, 'cancellation probability', minimum=0, maximum=1)
        altered = deepcopy(case)
        for s in altered['scenarios']:
            s['probability'] *= (1 - p if s['proceed'] else p) / totals[s['proceed']]
        r = screen_reservation(altered)
        rows.append({'cancellation_probability': p,
                     'expected_npv_eur': r['reserve_expected_npv_eur'],
                     'choice': r['screened_choice']})
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('outputs/procurement'))
    args = parser.parse_args()
    case = reference_case()
    workflow = run_procurement_workflow(case)
    direct = screen_reservation(case)
    if not workflow['success'] or workflow['results']['finance']['report'] != direct:
        raise RuntimeError('Workflow/baseline parity failed')
    args.output.mkdir(parents=True, exist_ok=True)
    output = {'case': case, 'workflow': workflow, 'baseline_parity': True,
              'cancellation_sensitivity': cancellation_sensitivity(case)}
    (args.output / 'report.json').write_text(json.dumps(output, indent=2, allow_nan=False) + '\n')
    print(json.dumps({k: v for k, v in direct.items() if k != 'scenarios'}, indent=2))


if __name__ == '__main__':
    main()
