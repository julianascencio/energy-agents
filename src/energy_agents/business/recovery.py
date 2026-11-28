"""Synthetic BESS cost-to-complete and cash screen; no procurement or legal action."""

import argparse
import hashlib
import json
import math
from collections import Counter
from copy import deepcopy
from datetime import date
from importlib.resources import files
from pathlib import Path

from ..orchestrator import AgentTask, run_orchestrator
from .bess import ROLE, _number
from .tandem import digest


def data_file(name):
    return json.loads(files('energy_agents').joinpath(f'data/recovery/{name}.json').read_text())


def reference_case():
    return data_file('case')


def _integer(value, name, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f'{name} must be an integer in {low}..{high}')


def _ids(rows, label):
    ids = [r['id'] for r in rows]
    if any(not isinstance(i, str) or not i.strip() for i in ids) or len(set(ids)) != len(ids):
        raise ValueError(f'Unique nonempty {label} IDs required')
    return set(ids)


def validate_case(c):
    if (c['version'], c['classification'], c['currency'], c['cash_basis']) != (
        '1.0', 'synthetic', 'CAD', 'nominal_undiscounted_before_tax'
    ):
        raise ValueError('Require v1 synthetic nominal CAD case')
    if c['source'] != data_file('source'):
        raise ValueError('Source must match reviewed snapshot')
    if date.fromisoformat(c['as_of']) < date.fromisoformat(c['source']['access_date']):
        raise ValueError('Case predates evidence')
    for key in ('limitations', 'evidence_gaps'):
        if not isinstance(c[key], list) or not c[key] or not all(
            isinstance(v, str) and v.strip() for v in c[key]
        ):
            raise ValueError('Explicit limitations and evidence gaps required')
    _integer(c['horizon_months'], 'horizon', 1, 36)
    horizon = c['horizon_months']
    for key in ('budget_cad', 'spent_cad', 'opening_cash_cad', 'funding_limit_cad'):
        _number(c[key], key, upper=1e10)
    scope = c['required_scope']
    if not isinstance(scope, list) or not scope or any(
        not isinstance(s, str) or not s.strip() for s in scope
    ) or len(set(scope)) != len(scope):
        raise ValueError('Unique nonempty required work scopes needed')
    for key in ('unpaid', 'receipts', 'plans', 'scenarios'):
        if not isinstance(c[key], list) or len(c[key]) > 100:
            raise ValueError('Bounded input lists required')
    unpaid_ids = _ids(c['unpaid'], 'unpaid')
    for r in c['unpaid']:
        _number(r['amount_cad'], 'unpaid amount', upper=1e10)
        _integer(r['month'], 'unpaid month', 1, horizon)
    if _ids(c['plans'], 'plan') != {'replacement_epc', 'owner_prime'}:
        raise ValueError('Exactly replacement_epc and owner_prime required')
    for p in c['plans']:
        _integer(p['completion_month'], 'completion', 1, horizon)
        packages = p['packages']
        if not isinstance(packages, list) or not 1 <= len(packages) <= 50:
            raise ValueError('Require 1..50 packages per plan')
        if _ids(packages, 'package') & unpaid_ids:
            raise ValueError('Unpaid and new package IDs must be disjoint')
        coverage = []
        for r in packages:
            if not isinstance(r['scope'], list) or not r['scope'] or not all(
                isinstance(s, str) for s in r['scope']
            ):
                raise ValueError('Package scope required')
            coverage.extend(r['scope'])
            _number(r['amount_cad'], 'quote amount', upper=1e10)
            payments = r['payments']
            if not isinstance(payments, list) or not 1 <= len(payments) <= horizon:
                raise ValueError('Bounded payment schedule required')
            months = []
            for payment in payments:
                _integer(payment['month'], 'payment month', 1, p['completion_month'])
                _number(payment['fraction'], 'payment fraction', upper=1)
                months.append(payment['month'])
            if len(set(months)) != len(months) or not math.isclose(
                math.fsum(v['fraction'] for v in payments), 1, rel_tol=0, abs_tol=1e-12
            ):
                raise ValueError('Unique payment months and fractions summing to one required')
        if Counter(coverage) != Counter(scope):
            raise ValueError('Each required scope must appear exactly once per plan')
    _ids(c['receipts'], 'receipt')
    for r in c['receipts']:
        if (r['kind'], r['status']) not in {
            ('grant', 'assumed_conditional'), ('recovery', 'disputed')
        }:
            raise ValueError('Only conditional grants or excluded disputed recoveries supported')
        _number(r['amount_cad'], 'receipt amount', upper=1e10)
        _integer(r['lag_after_completion_months'], 'receipt lag', 0, 36)
    if not c['scenarios']:
        raise ValueError('At least one scenario required')
    _ids(c['scenarios'], 'scenario')
    for s in c['scenarios']:
        _number(s['owner_quote_uplift'], 'quote uplift', lower=-1, upper=3)
        _number(s['capacity_fraction'], 'capacity fraction', upper=1)
        _integer(s['receipt_delay_months'], 'receipt delay', 0, 36)
    service = c['service']
    for key in ('power_mw', 'capacity_mwh_dc', 'target_mw', 'hours'):
        _number(service[key], key, lower=.001, upper=10000)
    for key in ('initial_soc', 'reserve_soc', 'efficiency'):
        _number(service[key], key, upper=1)
    if service['efficiency'] <= 0 or service['initial_soc'] <= service['reserve_soc']:
        raise ValueError('Positive efficiency and SOC window required')


def completion_audit(c):
    validate_case(c)
    physical = []
    v = c['service']
    for s in c['scenarios']:
        energy = (v['capacity_mwh_dc'] * s['capacity_fraction'] *
                  (v['initial_soc']-v['reserve_soc']) * v['efficiency'])
        power = min(v['power_mw'], energy/v['hours'])
        physical.append({'scenario':s['id'], 'available_ac_mwh':energy,
                         'sustainable_mw':power, 'passes_screen':power+1e-9 >= v['target_mw']})
    return {'input_sha256':digest(c), 'physical':physical,
            'unpaid_cad':math.fsum(r['amount_cad'] for r in c['unpaid']),
            'quotes_cad':{p['id']:math.fsum(r['amount_cad'] for r in p['packages'])
                          for p in c['plans']}, 'scope_checked':True}


def _ledger(c, p, scenario, audit):
    multiplier = 1+scenario['owner_quote_uplift'] if p['id'] == 'owner_prime' else 1
    quotes = audit['quotes_cad'][p['id']] * multiplier
    ctc = audit['unpaid_cad']+quotes
    gross = c['spent_cad']+ctc
    balance, peak, rows = -c['opening_cash_cad'], 0.0, []
    receipts = []
    for receipt in c['receipts']:
        receipts.append({**receipt, 'month':p['completion_month']+
                         receipt['lag_after_completion_months']+scenario['receipt_delay_months'],
                         'included':receipt['status'] != 'disputed'})
    for month in range(1, c['horizon_months']+1):
        out = math.fsum(r['amount_cad'] for r in c['unpaid'] if r['month'] == month)
        out += math.fsum(r['amount_cad'] * multiplier * payment['fraction']
                         for r in p['packages'] for payment in r['payments']
                         if payment['month'] == month)
        inflow = math.fsum(r['amount_cad'] for r in receipts if r['included'] and
                          r['month'] == month)
        balance += out
        before = max(0, balance)
        peak = max(peak, before)
        balance -= inflow
        rows.append({'month':month, 'outflow_cad':out, 'receipt_cad':inflow,
                     'funding_before_receipts_cad':before,
                     'funding_at_month_end_cad':max(0, balance),
                     'surplus_at_month_end_cad':max(0, -balance)})
    return {'plan':p['id'], 'new_quote_cost_cad':quotes, 'cost_to_complete_cad':ctc,
            'gross_forecast_at_completion_cad':gross, 'budget_headroom_cad':c['budget_cad']-gross,
            'peak_new_funding_cad':peak, 'terminal_new_funding_cad':max(0, balance),
            'peak_funding_shortfall_cad':max(0, peak-c['funding_limit_cad']),
            'ignored_disputed_recoveries_cad':math.fsum(r['amount_cad'] for r in receipts
                                                      if not r['included']),
            'receipts_after_horizon_cad':math.fsum(r['amount_cad'] for r in receipts
                                                  if r['included'] and
                                                  r['month'] > c['horizon_months']),
            'receipts':receipts, 'monthly':rows}


def screen_recovery(c, audit=None):
    reference = completion_audit(c)
    if audit is not None and audit != reference:
        raise ValueError('Evidence handoff differs from input-bound reference')
    comparisons = []
    for scenario, physical in zip(c['scenarios'], reference['physical'], strict=True):
        plans = {p['id']:_ledger(c,p,scenario,reference) for p in c['plans']}
        difference = (plans['replacement_epc']['cost_to_complete_cad'] -
                      plans['owner_prime']['cost_to_complete_cad'])
        comparisons.append({'scenario':scenario['id'], 'service':physical, 'plans':plans,
                            'comparison_valid':physical['passes_screen'],
                            'conditional_cost_reduction_cad':difference
                            if physical['passes_screen'] else None})
    owner, epc = (reference['quotes_cad'][k] for k in ('owner_prime', 'replacement_epc'))
    return {'classification':'modelled_synthetic', 'currency':'CAD',
            'cash_basis':c['cash_basis'], 'horizon_months':c['horizon_months'],
            'input_sha256':digest(c), 'comparisons':comparisons,
            'algebraic_owner_quote_uplift_at_cost_parity':epc/owner-1 if owner > 0 else None,
            'crossover_scope':'equal prospective cost only; not budget, financing or technical approval',
            'procurement_authorized':False, 'physical_readiness_verified':False,
            'human_review_required':True, 'evidence_gaps':list(c['evidence_gaps']),
            'limitations':list(c['limitations']),
            'llm':{'executed':False, 'tokens':None, 'cost':None, 'latency':None}}


def edi_crosscheck(c):
    import energy_methods.bess_service_envelope as method

    audit = completion_audit(c)
    metadata = data_file('edi_capabilities')
    actual = hashlib.sha256(Path(method.__file__).read_bytes()).hexdigest()
    if actual != metadata['source_sha256']:
        raise ValueError('Installed EDI method differs from inspected source')
    v = c['service']
    for s, physical in zip(c['scenarios'], audit['physical'], strict=True):
        result = method.screen_bess_service(
            v['power_mw'], v['capacity_mwh_dc'], v['hours'], target_power_mw=v['target_mw'],
            initial_soc_fraction=v['initial_soc'], reserve_soc_fraction=v['reserve_soc'],
            usable_capacity_fraction=s['capacity_fraction'], discharge_efficiency=v['efficiency'])
        if not all(math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-9) for a,b in (
            (result.sustainable_power_mw, physical['sustainable_mw']),
            (result.available_ac_energy_mwh, physical['available_ac_mwh'])
        )):
            raise ValueError('EDI service envelope disagrees')
    return {'executed':True, 'parity':True, 'scenarios_checked':len(c['scenarios']),
            'source_sha256':actual, 'catalogue_commit':metadata['commit'],
            'input_sha256':digest(c), 'scope':'single-event energy/power arithmetic only'}


def run_workflow(c, planner=None):
    def evidence(context):
        case = context['payload']['case']
        return {'success':True, 'case':case, 'audit':completion_audit(case),
                'validation':'schema_and_arithmetic_not_source_truth'}

    def finance(context):
        upstream = context['upstream']['evidence']
        return {'success':True, 'report':screen_recovery(upstream['case'], upstream['audit'])}

    return run_orchestrator(
        [AgentTask('evidence','evidence_contract',payload={'case':deepcopy(c)}),
         AgentTask('finance',ROLE.id,dependencies=('evidence',))],
        {'evidence_contract':evidence,ROLE.id:finance},planner,max_calls=4)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', type=Path)
    parser.add_argument('--output', type=Path, default=Path('outputs/recovery'))
    parser.add_argument('--edi', action='store_true')
    args = parser.parse_args()
    case = json.loads(args.case.read_text()) if args.case else reference_case()
    report, workflow = screen_recovery(case), run_workflow(case)
    if not workflow['success'] or workflow['results']['finance']['report'] != report:
        raise RuntimeError('Direct/scripted parity failed')
    edi = edi_crosscheck(case) if args.edi else {'executed':False,'parity':None}
    args.output.mkdir(parents=True, exist_ok=True)
    for name, value in [('inputs',case),('report',report),('workflow',workflow),
                        ('audit',completion_audit(case)),('edi_execution',edi),
                        ('edi_capabilities',data_file('edi_capabilities')),('skill',data_file('skill'))]:
        (args.output/(name+'.json')).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'first_scenario_cost_reduction_cad':report['comparisons'][0]
                      ['conditional_cost_reduction_cad'],'scripted_parity':True,'edi':edi},indent=2))


if __name__ == '__main__':
    main()
