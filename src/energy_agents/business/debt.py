"""Advisory operating-period debt capacity; commitments are not drawn debt."""
import argparse
import json
import math
from datetime import date
from importlib.resources import files
from pathlib import Path

from ..orchestrator import AgentTask, run_orchestrator
from .bess import ROLE, _number
from .tandem import digest


def reference_case():
    return json.loads(files('energy_agents').joinpath('data/debt/case.json').read_text())


def edi_context():
    """Bounded packaged source-derived metadata, not external method execution."""
    return json.loads(files('energy_agents').joinpath('data/debt/edi_capabilities.json').read_text())


def validate_case(case):
    if (case.get('version'), case.get('classification'), case.get('currency'),
        case.get('cash_basis')) != ('1.0', 'synthetic', 'GBP', 'constant_real_year_end'):
        raise ValueError('Explicit synthetic GBP constant-real version 1.0 required')
    s = case['source']
    if s['classification'] != 'issuer_announcement' or not s['url'].startswith('https://'):
        raise ValueError('Cited issuer evidence required')
    for key in ('publication_date', 'event_date'):
        date.fromisoformat(s[key])
    for key in ('cash_facilities_gbp', 'ancillary_facilities_gbp'):
        _number(s[key], key)
    if s['drawn_debt_gbp'] is not None:
        _number(s['drawn_debt_gbp'], 'drawn debt')
    a = case['assumptions']
    for key in ('capacity_mw', 'value_gbp_mwh', 'annual_opex_gbp', 'proposed_debt_gbp'):
        _number(a[key], key, upper=1e13)
    if a['capacity_mw'] == 0 or a['proposed_debt_gbp'] == 0:
        raise ValueError('Positive capacity and proposed debt required')
    if type(a['years']) is not int or not 1 <= a['years'] <= 40:
        raise ValueError('Horizon must be integer 1..40')
    _number(a['real_interest_rate'], 'real rate', upper=1)
    _number(a['minimum_dscr'], 'coverage threshold', lower=1, upper=10)
    if not isinstance(a['capacity_factors'], dict) or not 1 <= len(a['capacity_factors']) <= 10:
        raise ValueError('Supply 1..10 named resource scenarios')
    for name, cf in a['capacity_factors'].items():
        if not isinstance(name, str) or not name:
            raise ValueError('Scenario name required')
        _number(cf, 'capacity factor', lower=1e-9, upper=1)
    if not case['limitations']:
        raise ValueError('Explicit limitations required')


def screen_debt(case):
    """PV of level permitted debt service, using annual real interest.

    CFADS here is a simplified pre-tax revenue-minus-OPEX proxy. No sculpting,
    stochastic calibration, actual CfD settlement or financing approval.
    """
    validate_case(case)
    a = case['assumptions']
    factor = math.fsum((1 + a['real_interest_rate']) ** -y
                      for y in range(1, a['years'] + 1))
    service = a['proposed_debt_gbp'] / factor
    rows = {}
    for name, cf in a['capacity_factors'].items():
        energy = a['capacity_mw'] * 8760 * cf
        cash = energy * a['value_gbp_mwh'] - a['annual_opex_gbp']
        supported = max(0, cash / a['minimum_dscr']) * factor
        dscr = cash / service
        rows[name] = {'annual_mwh': energy, 'annual_cfads_proxy_gbp': cash,
                      'dscr': dscr, 'supported_debt_gbp': supported,
                      'debt_reduction_gbp': max(0, a['proposed_debt_gbp'] - supported),
                      'clears_screen': dscr >= a['minimum_dscr']}
    required_cash = service * a['minimum_dscr'] + a['annual_opex_gbp']
    denominator = a['capacity_mw'] * 8760 * a['value_gbp_mwh']
    threshold = required_cash / denominator if denominator else None
    return {'classification': 'modelled_synthetic', 'currency': 'GBP',
            'input_sha256': digest(case), 'annual_debt_service_gbp': service,
            'scenarios': rows, 'break_even_capacity_factor': threshold,
            'feasible_capacity_factor_exists': threshold is not None and threshold <= 1,
            'actual_project_leverage': None,
            'facility_warning': 'Cash and ancillary commitments are not drawn debt',
            'human_review_required': True, 'live_llm_executed': False,
            'llm_cost': None, 'llm_tokens': None, 'llm_latency': None}


def run_workflow(case, planner=None):
    def evidence(context):
        c = context['payload']['case']
        validate_case(c)
        return {'success': True, 'case': c, 'validation': 'schema_not_source_truth'}

    def finance(context):
        return {'success': True, 'report': screen_debt(context['upstream']['evidence']['case'])}

    return run_orchestrator(
        [AgentTask('evidence', 'evidence_contract', payload={'case': case}),
         AgentTask('finance', ROLE.id, dependencies=('evidence',))],
        {'evidence_contract': evidence, ROLE.id: finance}, planner, max_calls=4)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', type=Path)
    parser.add_argument('--output', type=Path, default=Path('outputs/wind_debt'))
    args = parser.parse_args()
    case = json.loads(args.case.read_text()) if args.case else reference_case()
    run = run_workflow(case)
    if not run['success'] or run['results']['finance']['report'] != screen_debt(case):
        raise RuntimeError('Workflow or baseline parity failed')
    args.output.mkdir(parents=True, exist_ok=True)
    for name, value in [('report', run), ('inputs', case), ('edi_context', edi_context())]:
        (args.output / (name + '.json')).write_text(json.dumps(value, indent=2) + '\n')
    print(json.dumps(run['results']['finance']['report'], indent=2))


if __name__ == '__main__':
    main()
