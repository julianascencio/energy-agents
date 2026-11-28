"""Synthetic benefit-sharing cash flows; no tender qualification or agreements."""

import argparse
import json
import math
from datetime import date
from importlib.resources import files
from pathlib import Path

from ..orchestrator import AgentTask, run_orchestrator
from .bess import ROLE, _number
from .tandem import digest


def data_file(name):
    return json.loads(files('energy_agents').joinpath(f'data/sharing/{name}.json').read_text())


def reference_case():
    return data_file('case')


def validate_case(c):
    if (c['version'], c['classification'], c['currency'], c['cash_basis']) != (
        '1.0', 'synthetic', 'AUD', 'nominal_year_end_after_debt_and_tax_before_sharing'
    ):
        raise ValueError('Require v1 synthetic nominal AUD after-debt/tax case')
    if c['source'] != data_file('source'):
        raise ValueError('Source must match reviewed public snapshot')
    if date.fromisoformat(c['as_of']) < date.fromisoformat(c['source']['access_date']):
        raise ValueError('Case predates source review')
    for key in ('limitations', 'evidence_gaps'):
        if not isinstance(c[key], list) or not c[key] or not all(
            isinstance(s, str) and s.strip() for s in c[key]
        ):
            raise ValueError('Explicit limitations and evidence gaps required')
    rows = c['annual']
    if not isinstance(rows, list) or not 1 <= len(rows) <= 50:
        raise ValueError('Require 1..50 annual rows')
    for year, row in enumerate(rows, 1):
        if type(row['year']) is not int or row['year'] != year:
            raise ValueError('Consecutive integer years required')
        for key in ('gross_revenue_aud', 'distributable_cash_aud'):
            _number(row[key], key, upper=1e10)
        if row['distributable_cash_aud'] > row['gross_revenue_aud']:
            raise ValueError('Cash cannot exceed revenue in this bounded model')
    _number(c['discount_rate'], 'discount rate', upper=1)
    for key in ('initial_equity_aud', 'terminal_equity_proceeds_aud'):
        _number(c[key], key, upper=1e10)
    equity, revenue = c['equity'], c['revenue_share']
    for plan in (equity, revenue):
        for key in ('fraction',):
            _number(plan[key], key, upper=1)
        for key in ('recipient_contribution_aud', 'setup_cost_aud', 'annual_admin_aud'):
            _number(plan[key], key, upper=1e10)
        if plan['recipient_contribution_aud'] > c['initial_equity_aud']:
            raise ValueError('Recipient contribution cannot exceed total initial equity')
    if equity['fraction'] <= 0:
        raise ValueError('Positive equity benchmark required')
    if equity['recipient_contribution_aud'] > equity['fraction'] * c['initial_equity_aud']:
        raise ValueError('Contribution cannot exceed pro-rata initial equity in this model')
    for key in ('start_year', 'end_year'):
        if type(revenue[key]) is not int or not 1 <= revenue[key] <= len(rows):
            raise ValueError('Revenue-sharing years must be within horizon')
    if revenue['start_year'] > revenue['end_year']:
        raise ValueError('Revenue-sharing period is reversed')


def sharing_audit(c):
    validate_case(c)
    rate = c['discount_rate']
    eligible = [r for r in c['annual'] if
                c['revenue_share']['start_year'] <= r['year'] <= c['revenue_share']['end_year']]
    return {'input_sha256':digest(c), 'years':len(c['annual']),
            'eligible_revenue_pv_aud':math.fsum(
                r['gross_revenue_aud']/(1+rate)**r['year'] for r in eligible),
            'evidence_validation':'reviewed_snapshot_and_schema_only'}


def screen_sharing(c, audit=None):
    reference = sharing_audit(c)
    if audit is not None and audit != reference:
        raise ValueError('Evidence handoff differs from input-bound audit')
    rate, horizon = c['discount_rate'], len(c['annual'])
    baseline_pv = math.fsum(r['distributable_cash_aud']/(1+rate)**r['year']
                             for r in c['annual'])
    baseline_pv += c['terminal_equity_proceeds_aud']/(1+rate)**horizon
    plans = {}
    for name in ('equity', 'revenue_share'):
        p = c[name]
        rows = []
        for r in c['annual']:
            y = r['year']
            terminal = c['terminal_equity_proceeds_aud'] if y == horizon else 0.0
            active = name == 'equity' or p['start_year'] <= y <= p['end_year']
            if name == 'equity':
                operating = p['fraction'] * r['distributable_cash_aud']
                exit_payment = p['fraction'] * terminal
            else:
                operating = p['fraction'] * r['gross_revenue_aud'] if active else 0.0
                exit_payment = 0.0
            admin = p['annual_admin_aud'] if active else 0.0
            # Exit receipts cannot fund an earlier operating shortfall in the same year.
            funding = max(0, operating+admin-r['distributable_cash_aud'])
            recipient = operating+exit_payment
            sponsor = r['distributable_cash_aud']+terminal-recipient-admin
            rows.append({'year':y, 'recipient_operating_aud':operating,
                         'recipient_exit_aud':exit_payment, 'recipient_total_aud':recipient,
                         'admin_aud':admin, 'sponsor_net_cash_aud':sponsor,
                         'operating_funding_gap_aud':funding})
        def pv(key):
            return math.fsum(r[key]/(1+rate)**r['year'] for r in rows)
        contribution = p['recipient_contribution_aud']
        recipient_npv = pv('recipient_total_aud')-contribution
        sponsor_cost = recipient_npv+p['setup_cost_aud']+pv('admin_aud')
        plans[name] = {'annual':rows, 'recipient_npv_aud':recipient_npv,
                       'sponsor_incremental_cost_pv_aud':sponsor_cost,
                       'sponsor_initial_outlay_aud':c['initial_equity_aud']-contribution+
                       p['setup_cost_aud'],
                       'sponsor_npv_aud':baseline_pv-c['initial_equity_aud']-sponsor_cost,
                       'total_operating_funding_gap_aud':math.fsum(
                           r['operating_funding_gap_aud'] for r in rows)}
    target = plans['equity']['recipient_npv_aud']+c['revenue_share']['recipient_contribution_aud']
    denominator = reference['eligible_revenue_pv_aud']
    fraction = target/denominator if denominator > 0 and target >= 0 else None
    return {'classification':'modelled_synthetic', 'currency':'AUD',
            'horizon_years':horizon, 'input_sha256':digest(c), 'plans':plans,
            'no_sharing_sponsor_npv_aud':baseline_pv-c['initial_equity_aud'],
            'recipient_value_difference_aud':plans['revenue_share']['recipient_npv_aud']-
            plans['equity']['recipient_npv_aud'],
            'revenue_fraction_at_recipient_npv_parity':fraction,
            'parity_fraction_within_zero_one':fraction is not None and fraction <= 1,
            'parity_scope':'equal modelled recipient NPV only; not tender economic equivalence',
            'tender_qualification':'not_determined', 'community_support_verified':False,
            'agreement_authorized':False, 'human_review_required':True,
            'evidence_gaps':list(c['evidence_gaps']), 'limitations':list(c['limitations']),
            'llm':{'executed':False, 'tokens':None, 'cost':None, 'latency':None}}


def run_workflow(c, planner=None):
    def evidence(context):
        case = context['payload']['case']
        return {'success':True, 'case':case, 'audit':sharing_audit(case)}

    def finance(context):
        upstream = context['upstream']['evidence']
        return {'success':True, 'report':screen_sharing(upstream['case'],upstream['audit'])}

    return run_orchestrator(
        [AgentTask('evidence','evidence_contract',payload={'case':c}),
         AgentTask('finance',ROLE.id,dependencies=('evidence',))],
        {'evidence_contract':evidence,ROLE.id:finance},planner,max_calls=4)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', type=Path)
    parser.add_argument('--output', type=Path, default=Path('outputs/sharing'))
    args = parser.parse_args()
    case = json.loads(args.case.read_text()) if args.case else reference_case()
    report, workflow = screen_sharing(case), run_workflow(case)
    if not workflow['success'] or workflow['results']['finance']['report'] != report:
        raise RuntimeError('Direct/scripted parity failed')
    args.output.mkdir(parents=True, exist_ok=True)
    for name, value in [('inputs',case), ('report',report), ('workflow',workflow),
                        ('audit',sharing_audit(case)), ('skill',data_file('skill')),
                        ('edi_capabilities',data_file('edi_capabilities'))]:
        (args.output/(name+'.json')).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k != 'plans'},indent=2))


if __name__ == '__main__':
    main()
