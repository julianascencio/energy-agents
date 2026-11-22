"""Synthetic battery augmentation cost screen; no tender or engineering approval."""

import argparse
import hashlib
import json
import math
from copy import deepcopy
from datetime import date
from importlib.resources import files
from pathlib import Path

from ..orchestrator import AgentTask, run_orchestrator
from .bess import ROLE, _number
from .tandem import digest


def data_file(name):
    return json.loads(files('energy_agents').joinpath(f'data/augmentation/{name}.json').read_text())


def reference_case():
    return data_file('case')


def validate_case(case):
    """V1 is a source-bound synthetic 15-year, four-hour screening contract."""
    if (case['version'], case['classification'], case['currency'], case['cash_basis']) != (
        '1.0', 'synthetic', 'USD', 'constant_real_before_tax_at_service_start'
    ):
        raise ValueError('Require v1 synthetic constant-real USD case')
    if case['source'] != data_file('source'):
        raise ValueError('Source must match the reviewed evidence snapshot')
    if date.fromisoformat(case['as_of']) < date.fromisoformat(case['source']['access_date']):
        raise ValueError('Case predates evidence access')
    if type(case['years']) is not int or case['years'] != 15 or case['service_hours'] != 4:
        raise ValueError('This case supports the 15-year, four-hour scope only')
    if type(case['service_hours']) not in (int, float):
        raise ValueError('Numeric service hours required')
    if case['assumptions_classification'] != 'synthetic_not_supplier_quotes_or_warranties':
        raise ValueError('Costs and degradation must be labelled synthetic')
    for key in ('evidence_gaps', 'limitations'):
        if not isinstance(case[key], list) or not case[key] or not all(
            isinstance(x, str) and x.strip() for x in case[key]
        ):
            raise ValueError('Explicit evidence gaps and limitations required')
    for key, lower, upper in (
        ('target_mw', .01, 300), ('inverter_mw', .01, 1000),
        ('initial_soc', .01, 1), ('reserve_soc', 0, .99),
        ('discharge_efficiency', .01, 1), ('design_annual_retention', .8, 1),
        ('pack_mwh_dc', .001, 100), ('site_limit_mwh_dc', .01, 10000),
        ('installed_usd_per_mwh_dc', 0, 1e7), ('opex_usd_per_mwh_dc_year', 0, 1e6),
        ('augmentation_event_usd', 0, 1e9), ('discount_rate', 0, 1)
    ):
        _number(case[key], key, lower=lower, upper=upper)
    if case['initial_soc'] <= case['reserve_soc']:
        raise ValueError('Positive SOC service window required')
    times = case['augmentation_years']
    if (not isinstance(times, list) or not times or times[0] != 0
            or any(type(t) is not int or not 0 <= t < 15 for t in times)
            or sorted(set(times)) != times):
        raise ValueError('Unique increasing integer addition years starting at zero required')
    scenarios = case['scenarios']
    if not isinstance(scenarios, list) or not 1 <= len(scenarios) <= 20:
        raise ValueError('Require 1..20 stress scenarios')
    ids = [s['id'] for s in scenarios]
    if (any(not isinstance(x, str) or not x.strip() for x in ids)
            or len(set(ids)) != len(ids) or 'design' in ids):
        raise ValueError('Unique nonempty scenario IDs required')
    for s in scenarios:
        _number(s['annual_retention'], 'scenario retention', lower=.8, upper=1)
        _number(s['future_price_multiplier'], 'future price multiplier', lower=0, upper=10)


def _design(case, times):
    """Size integer packs for each interval's right endpoint, before the next addition."""
    factor = (case['initial_soc'] - case['reserve_soc']) * case['discharge_efficiency']
    required_dc = case['target_mw'] * case['service_hours'] / factor
    retention, pack = case['design_annual_retention'], case['pack_mwh_dc']
    cohorts = []
    for start, end in zip(times, times[1:] + [case['years']], strict=True):
        existing_at_end = math.fsum(
            c['nameplate_mwh_dc'] * retention ** (end-c['added_at_year']) for c in cohorts)
        needed_new = max(0, required_dc-existing_at_end) / retention ** (end-start)
        # Tolerance avoids a spurious extra pack from floating-point division at an integer.
        packs = math.ceil(needed_new / pack - 1e-12)
        if packs > 0:
            cohorts.append({'added_at_year':start, 'nameplate_mwh_dc':packs*pack,
                            'packs':packs})
    return cohorts


def _physical(case, cohorts, retention):
    factor = (case['initial_soc'] - case['reserve_soc']) * case['discharge_efficiency']
    rows = []
    for year in range(1, case['years']+1):
        # An addition at t=5 cannot repair the end-of-year-five condition at t=5-minus.
        active = [c for c in cohorts if c['added_at_year'] < year]
        remaining_dc = math.fsum(c['nameplate_mwh_dc'] * retention ** (
            year-c['added_at_year']) for c in active)
        installed = math.fsum(c['nameplate_mwh_dc'] for c in active)
        energy_ac = remaining_dc * factor
        sustainable = min(case['inverter_mw'], energy_ac/case['service_hours'])
        rows.append({'year':year, 'installed_nameplate_mwh_dc':installed,
                     'remaining_capacity_mwh_dc':remaining_dc,
                     'available_ac_energy_mwh':energy_ac, 'sustainable_mw':sustainable,
                     'target_shortfall_mw':max(0, case['target_mw']-sustainable),
                     'meets_energy_power_screen':sustainable + 1e-9 >= case['target_mw'],
                     'within_site_limit':installed <= case['site_limit_mwh_dc'] + 1e-9})
    return rows


def capacity_audit(case):
    validate_case(case)
    plans = []
    for name, times in [('upfront', [0]), ('staged', case['augmentation_years'])]:
        cohorts = _design(case, times)
        scenarios = [{'id':'design', 'annual_retention':case['design_annual_retention']}]
        scenarios += case['scenarios']
        plans.append({'id':name, 'cohorts':cohorts, 'physical':[
            {'scenario':s['id'], 'years':_physical(case, cohorts, s['annual_retention'])}
            for s in scenarios]})
    return {'input_sha256':digest(case), 'plans':plans}


def _cost(case, plan, physical, multiplier):
    rate = case['discount_rate']
    additions = []
    for c in plan['cohorts']:
        t = c['added_at_year']
        equipment = c['nameplate_mwh_dc'] * case['installed_usd_per_mwh_dc']
        equipment *= multiplier if t > 0 else 1
        event = case['augmentation_event_usd'] if t > 0 else 0
        additions.append({**c, 'equipment_usd':equipment, 'event_usd':event,
                          'pv_usd':(equipment+event)/(1+rate)**t})
    years = [{**row, 'opex_usd':row['installed_nameplate_mwh_dc'] *
              case['opex_usd_per_mwh_dc_year']} for row in physical]
    for row in years:
        row['opex_pv_usd'] = row['opex_usd']/(1+rate)**row['year']
    capex = math.fsum(row['pv_usd'] for row in additions)
    opex = math.fsum(row['opex_pv_usd'] for row in years)
    return {'plan':plan['id'], 'additions':additions, 'years':years,
            'capex_pv_usd':capex, 'opex_pv_usd':opex, 'total_cost_pv_usd':capex+opex,
            'passes_screen':all(r['meets_energy_power_screen'] and r['within_site_limit']
                                for r in years),
            'minimum_sustainable_mw':min(r['sustainable_mw'] for r in years),
            'first_failing_year':next((r['year'] for r in years if not (
                r['meets_energy_power_screen'] and r['within_site_limit'])), None)}


def screen_augmentation(case, audit=None):
    reference = capacity_audit(case)
    if audit is not None and audit != reference:
        raise ValueError('Capacity handoff differs from input-bound reference')
    scenarios = [{'id':'design', 'future_price_multiplier':1}] + case['scenarios']
    comparisons = []
    for index, s in enumerate(scenarios):
        results = [_cost(case, p, p['physical'][index]['years'], s['future_price_multiplier'])
                   for p in reference['plans']]
        upfront, staged = results
        comparable = all(r['passes_screen'] for r in results)
        comparisons.append({'scenario':s['id'], 'plans':results,
                            'cost_reduction_pv_usd':upfront['total_cost_pv_usd'] -
                            staged['total_cost_pv_usd'] if comparable else None,
                            'comparison_valid':comparable})
    base = comparisons[0]
    upfront, staged = base['plans']
    future_pv = math.fsum(a['equipment_usd']/(1+case['discount_rate'])**a['added_at_year']
                         for a in staged['additions'] if a['added_at_year'] > 0)
    ceiling = (upfront['total_cost_pv_usd'] - staged['total_cost_pv_usd'] + future_pv) / (
        future_pv or 1)
    return {'classification':'modelled_synthetic', 'currency':'USD', 'horizon_years':15,
            'input_sha256':digest(case), 'comparisons':comparisons,
            'break_even_future_equipment_price_multiplier':ceiling if (
                base['comparison_valid'] and future_pv > 0 and ceiling >= 0) else None,
            'economic_scope':'battery capacity and augmentation costs only; no project NPV or revenue',
            'tender_compliance_verified':False, 'purchase_authorized':False,
            'human_review_required':True, 'evidence_gaps':list(case['evidence_gaps']),
            'limitations':list(case['limitations']),
            'llm':{'executed':False, 'tokens':None, 'cost':None, 'latency':None}}


def edi_crosscheck(case):
    """Execute the existing EDI service envelope on every cohort/year/scenario result."""
    import energy_methods.bess_service_envelope as method

    audit = capacity_audit(case)
    metadata = data_file('edi_capabilities')
    actual = hashlib.sha256(Path(method.__file__).read_bytes()).hexdigest()
    if actual != metadata['source_sha256']:
        raise ValueError('Installed EDI method differs from inspected source')
    count = 0
    for plan in audit['plans']:
        for scenario in plan['physical']:
            for row in scenario['years']:
                result = method.screen_bess_service(
                    case['inverter_mw'], row['remaining_capacity_mwh_dc'],
                    case['service_hours'], target_power_mw=case['target_mw'],
                    initial_soc_fraction=case['initial_soc'], reserve_soc_fraction=case['reserve_soc'],
                    usable_capacity_fraction=1, discharge_efficiency=case['discharge_efficiency'])
                if not math.isclose(result.sustainable_power_mw, row['sustainable_mw'],
                                    rel_tol=1e-12, abs_tol=1e-9):
                    raise ValueError('EDI service envelope disagrees with capacity audit')
                count += 1
    return {'executed':True, 'parity':True, 'rows_checked':count, 'source_sha256':actual,
            'catalogue_commit':metadata['commit'], 'input_sha256':digest(case),
            'scope':'constant-power AC service envelope only; no lifecycle or warranty validation'}


def run_workflow(case, planner=None):
    def evidence(context):
        c = context['payload']['case']
        return {'success':True, 'case':c, 'audit':capacity_audit(c),
                'validation':'schema_and_arithmetic_not_source_truth'}

    def finance(context):
        upstream = context['upstream']['evidence']
        return {'success':True, 'report':screen_augmentation(upstream['case'], upstream['audit'])}

    return run_orchestrator(
        [AgentTask('evidence', 'evidence_contract', payload={'case':deepcopy(case)}),
         AgentTask('finance', ROLE.id, dependencies=('evidence',))],
        {'evidence_contract':evidence, ROLE.id:finance}, planner, max_calls=4)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', type=Path)
    parser.add_argument('--output', type=Path, default=Path('outputs/augmentation'))
    parser.add_argument('--edi', action='store_true')
    args = parser.parse_args()
    case = json.loads(args.case.read_text()) if args.case else reference_case()
    report, workflow = screen_augmentation(case), run_workflow(case)
    if not workflow['success'] or workflow['results']['finance']['report'] != report:
        raise RuntimeError('Direct/scripted workflow parity failed')
    edi = edi_crosscheck(case) if args.edi else {'executed':False, 'parity':None}
    args.output.mkdir(parents=True, exist_ok=True)
    for name, value in [('inputs',case), ('report',report), ('workflow',workflow),
                        ('capacity_audit',capacity_audit(case)), ('edi_execution',edi),
                        ('edi_capabilities',data_file('edi_capabilities')), ('skill',data_file('skill'))]:
        (args.output/(name+'.json')).write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')
    print(json.dumps({'cost_reduction_pv_usd':report['comparisons'][0]['cost_reduction_pv_usd'],
                      'scripted_parity':True, 'edi':edi}, indent=2))


if __name__ == '__main__':
    main()
