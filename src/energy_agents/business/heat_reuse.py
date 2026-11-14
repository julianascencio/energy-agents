"""Advisory heat-recovery economics; no plant controls or contract execution."""

import argparse
import hashlib
import json
import math
from copy import deepcopy
from datetime import date
from importlib.resources import files
from pathlib import Path
from urllib.parse import urlsplit

from ..orchestrator import AgentTask, run_orchestrator
from .bess import ROLE, _number
from .tandem import digest


def data_file(name):
    return json.loads(files('energy_agents').joinpath(f'data/heat_reuse/{name}.json').read_text())


def reference_case():
    return data_file('case')


def validate_case(case):
    """Validate declared evidence and a synthetic repeating 8760-hour year."""
    if (case['version'], case['classification'], case['currency'], case['cash_basis']) != (
        '1.0', 'synthetic', 'CHF', 'constant_real_year_end_incremental_before_tax'
    ):
        raise ValueError('Require synthetic real CHF, version 1.0')
    s = case['source']
    url = urlsplit(s['url'])
    if (s['classification'] != 'company_announcement' or not s['publisher']
            or url.scheme != 'https' or not url.netloc):
        raise ValueError('HTTPS company announcement required')
    if not (date.fromisoformat(s['event_date']) <= date.fromisoformat(s['publication_date'])
            <= date.fromisoformat(case['as_of'])):
        raise ValueError('Evidence dates must precede the as-of date')
    for key in ('evidence_gaps', 'limitations'):
        if not isinstance(case[key], list) or not case[key] or not all(
            isinstance(v, str) and v.strip() for v in case[key]):
            raise ValueError('Explicit evidence gaps and limitations required')
    a = case['assumptions']
    if a['classification'] != 'synthetic_assumptions':
        raise ValueError('Financial and operating assumptions must be labelled')
    for key in ('it_capacity_mw', 'heat_pump_output_capacity_mw'):
        _number(a[key], key, upper=10000)
    for key in ('recoverable_it_heat_fraction', 'network_delivery_efficiency'):
        _number(a[key], key, upper=1)
    if a['network_delivery_efficiency'] == 0:
        raise ValueError('Positive delivery efficiency required')
    for key in ('capex_chf', 'fixed_opex_chf_year'):
        _number(a[key], key, upper=1e12)
    for key in ('electricity_chf_mwh', 'source_heat_fee_chf_mwh',
                'variable_opex_chf_mwh_delivered', 'baseline_heat_cost_chf_mwh_delivered'):
        _number(a[key], key, upper=10000)
    _number(a['discount_rate'], 'discount_rate', upper=1)
    if type(a['years']) is not int or not 1 <= a['years'] <= 50:
        raise ValueError('Use 1..50 whole years')
    periods = case['periods']
    if not isinstance(periods, list) or not 1 <= len(periods) <= 8760:
        raise ValueError('Require 1..8760 non-overlapping periods')
    ids = [p['id'] for p in periods]
    if any(not isinstance(i, str) or not i.strip() for i in ids) or len(set(ids)) != len(ids):
        raise ValueError('Unique nonempty period IDs required')
    for p in periods:
        _number(p['hours'], 'hours', lower=1, upper=8760)
        _number(p['it_load_fraction'], 'it_load_fraction', upper=1)
        _number(p['demand_mw'], 'demand_mw', upper=10000)
        _number(p['heating_cop'], 'heating_cop', lower=1.01, upper=20)
    if not math.isclose(math.fsum(p['hours'] for p in periods), 8760, abs_tol=1e-8, rel_tol=0):
        raise ValueError('Period hours must sum to a non-leap 8760-hour year')


def heat_balance(case):
    """Flat simultaneous load per period; no storage, temperature or hydraulic simulation.

    Heating COP = Q_out / W. Source heat = Q_out - W. Distribution losses
    occur after the heat pump. Only useful heat is produced; unused source heat
    is bypassed. The model assumes modulating equipment with no minimum output.
    """
    validate_case(case)
    a = case['assumptions']
    eta = a['network_delivery_efficiency']
    rows = []
    for p in case['periods']:
        source = (a['it_capacity_mw'] * p['it_load_fraction'] * p['hours']
                  * a['recoverable_it_heat_fraction'])
        potential = min(source / (1 - 1 / p['heating_cop']),
                        a['heat_pump_output_capacity_mw'] * p['hours']) * eta
        demand = p['demand_mw'] * p['hours']
        delivered = min(potential, demand)
        produced = delivered / eta
        electricity = produced / p['heating_cop']
        recovered = produced - electricity
        rows.append({'id':p['id'], 'hours':p['hours'], 'source_available_mwh':source,
                     'potential_delivered_mwh':potential, 'demand_mwh':demand,
                     'delivered_mwh':delivered, 'pump_electricity_mwh':electricity,
                     'recovered_source_mwh':recovered, 'network_loss_mwh':produced-delivered,
                     'bypassed_source_mwh':max(0, source-recovered),
                     'remaining_supply_mwh':max(0, demand-delivered)})
    return {'input_sha256':digest(case), 'periods':rows}


def validate_balance(case, balance):
    """Recompute the deterministic contract before accepting a role handoff."""
    if balance != heat_balance(case):
        raise ValueError('Heat balance handoff differs from the input-bound reference')


def screen_heat_reuse(case, balance=None):
    balance = heat_balance(case) if balance is None else balance
    validate_balance(case, balance)
    a = case['assumptions']
    rows = balance['periods']
    totals = {key:math.fsum(p[key] for p in rows) for key in rows[0] if key.endswith('_mwh')}
    delivered = totals['delivered_mwh']
    avoided = delivered * a['baseline_heat_cost_chf_mwh_delivered']
    electricity = totals['pump_electricity_mwh'] * a['electricity_chf_mwh']
    fee = totals['recovered_source_mwh'] * a['source_heat_fee_chf_mwh']
    variable = delivered * a['variable_opex_chf_mwh_delivered']
    operating = electricity + fee + variable + a['fixed_opex_chf_year']
    savings = avoided - operating
    annuity = math.fsum((1+a['discount_rate'])**(-y) for y in range(1, a['years']+1))
    baseline = totals['demand_mwh'] * a['baseline_heat_cost_chf_mwh_delivered']
    return {'classification':'modelled_synthetic', 'currency':'CHF',
            'input_sha256':digest(case), 'periods':deepcopy(rows), 'annual_energy':totals,
            'annual_matching_ceiling_mwh':min(totals['potential_delivered_mwh'],
                                               totals['demand_mwh']),
            'baseline_annual_supply_cost_chf':baseline,
            'intervention_annual_supply_cost_chf':baseline-avoided+operating,
            'annual_avoided_supply_cost_chf':avoided,
            'annual_pump_electricity_cost_chf':electricity,
            'annual_source_heat_fee_chf':fee, 'annual_variable_opex_chf':variable,
            'annual_fixed_opex_chf':a['fixed_opex_chf_year'],
            'annual_net_savings_chf':savings,
            'incremental_npv_chf':-a['capex_chf']+savings*annuity,
            'break_even_avoided_cost_chf_mwh':(
                (operating+a['capex_chf']/annuity)/delivered if delivered else None),
            'baseline_incremental_npv_chf':0.0,
            'evidence_gaps':list(case['evidence_gaps']), 'limitations':list(case['limitations']),
            'human_review_required':True, 'investment_authorized':False,
            'llm':{'executed':False, 'cost':None, 'latency':None, 'tokens':None}}


def edi_crosscheck(case):
    """Optional executed EDI energy-matching check; thermal conversion stays local.

    Map delivered-side heat potential to the generic supply channel of
    simulate_hybrid, with zero solar and zero battery. Names in that upstream
    API refer to electricity; here only its dimensionally identical MW/MWh
    no-storage arithmetic is reused. No electric generation or thermal-storage
    simulation is claimed. Hash mismatch fails closed.
    """
    import energy_methods.hybrid_dispatch as method

    metadata = data_file('edi_capabilities')
    actual = hashlib.sha256(Path(method.__file__).read_bytes()).hexdigest()
    if actual != metadata['source_sha256']:
        raise ValueError('Installed EDI method differs from inspected source')
    expected = heat_balance(case)
    served = []
    for row in expected['periods']:
        hours = row['hours']
        result = method.simulate_hybrid(
            [row['potential_delivered_mwh']/hours], [0.0], [row['demand_mwh']/hours],
            battery_mwh=0, battery_mw=0, timestep_hours=hours)
        if not math.isclose(result.served_mwh, row['delivered_mwh'], abs_tol=1e-8):
            raise ValueError('EDI matching disagrees with reference')
        served.append(result.served_mwh)
    return {'executed':True, 'method':'simulate_hybrid', 'source_sha256':actual,
            'catalogue_commit':metadata['commit'], 'input_sha256':digest(case),
            'delivered_mwh':math.fsum(served), 'parity':True}


def run_workflow(case, planner=None):
    def evidence(context):
        c = context['payload']['case']
        validate_case(c)
        return {'success':True, 'case':c, 'validation':'schema_not_source_truth'}

    def thermal(context):
        c = context['upstream']['evidence']['case']
        return {'success':True, 'case':c, 'balance':heat_balance(c)}

    def finance(context):
        upstream = context['upstream']['thermal']
        return {'success':True, 'report':screen_heat_reuse(upstream['case'], upstream['balance'])}

    return run_orchestrator(
        [AgentTask('evidence', 'evidence_contract', payload={'case':case}),
         AgentTask('thermal', 'liquid_cooling_engineer', dependencies=('evidence',)),
         AgentTask('finance', ROLE.id, dependencies=('thermal',))],
        {'evidence_contract':evidence, 'liquid_cooling_engineer':thermal, ROLE.id:finance},
        planner, max_calls=5)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', type=Path)
    parser.add_argument('--output', type=Path, default=Path('outputs/heat_reuse'))
    parser.add_argument('--edi', action='store_true', help='Execute pinned optional EDI check')
    args = parser.parse_args()
    case = json.loads(args.case.read_text()) if args.case else reference_case()
    run = run_workflow(case)
    direct = screen_heat_reuse(case)
    if not run['success'] or run['results']['finance']['report'] != direct:
        raise RuntimeError('Workflow/baseline parity failed')
    edi = edi_crosscheck(case) if args.edi else {'executed':False, 'parity':None}
    args.output.mkdir(parents=True, exist_ok=True)
    for name, value in [('inputs',case), ('workflow',run), ('report',direct),
                        ('edi_execution',edi), ('edi_capabilities',data_file('edi_capabilities'))]:
        (args.output/(name+'.json')).write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in direct.items() if k != 'periods'}, indent=2))


if __name__ == '__main__':
    main()
