"""Synthetic preferred-equity cash allocation; no financing or tax execution."""
import argparse
import json
import math
from datetime import date
from importlib.resources import files
from pathlib import Path
from urllib.parse import urlsplit

from ..orchestrator import AgentTask, run_orchestrator
from .bess import ROLE, _number
from .tandem import digest


def reference_case():
    return json.loads(files('energy_agents').joinpath('data/equity/case.json').read_text())


def edi_context():
    """Bounded source metadata, not an upstream method execution."""
    return json.loads(files('energy_agents').joinpath('data/equity/edi_capabilities.json').read_text())


def validate_case(case):
    if (case['version'], case['classification'], case['currency'], case['cash_basis']) != (
        '1.0', 'synthetic', 'USD',
        'nominal_year_end_after_senior_debt_before_equity_distributions',
    ):
        raise ValueError('Require synthetic nominal USD after-debt cash, version 1.0')
    s = case['source']
    url = urlsplit(s['url'])
    if (s['classification'] != 'company_announcement' or not s['publisher']
            or s['terms_disclosed'] is not False or url.scheme != 'https' or not url.netloc):
        raise ValueError('Company announcement and explicitly undisclosed terms required')
    for key in ('publication_date', 'event_date'):
        date.fromisoformat(s[key])
    for key in ('evidence_gaps', 'limitations'):
        if not isinstance(case[key], list) or not case[key] or not all(
            isinstance(v, str) and v.strip() for v in case[key]
        ):
            raise ValueError('Explicit evidence gaps and limitations required')
    a = case['assumptions']
    for key in ('equity_requirement_usd', 'preferred_capital_usd',
                'transaction_fee_usd', 'terminal_equity_proceeds_usd'):
        _number(a[key], key, upper=1e12)
    if not 0 < a['equity_requirement_usd'] or not (
        a['transaction_fee_usd'] <= a['preferred_capital_usd'] <= a['equity_requirement_usd']
    ):
        raise ValueError('Require positive equity need and fee <= preferred <= equity need')
    for key in ('preferred_annual_rate', 'discount_rate'):
        _number(a[key], key, upper=1)
    cash = a['annual_cash_usd']
    if not isinstance(cash, list) or not 1 <= len(cash) <= 50:
        raise ValueError('Require 1..50 annual cash values')
    for v in cash:
        _number(v, 'annual_cash_usd', upper=1e12)


def screen_equity(case):
    """Allocate coupon first, then terminal capital, then common distributions.

    Coupon accrues annually on original preferred capital, without compounding.
    Capital is repaid only at terminal liquidation. Unpaid terminal amounts are
    reported as shortfalls, not assumed future cash. There are no taxes, capital
    calls, additional borrowing, refinancing or preferred upside participation.
    """
    validate_case(case)
    a = case['assumptions']
    capital = a['preferred_capital_usd']
    arrears = 0.0
    rows = []
    for year, operating in enumerate(a['annual_cash_usd'], 1):
        terminal = year == len(a['annual_cash_usd'])
        available = operating + (a['terminal_equity_proceeds_usd'] if terminal else 0)
        due = arrears + capital * a['preferred_annual_rate']
        coupon = min(available, due)
        arrears = due - coupon
        redemption = min(capital, available - coupon) if terminal else 0.0
        common = available - coupon - redemption
        rows.append({'year':year, 'available_usd':available, 'coupon_due_usd':due,
                     'coupon_paid_usd':coupon, 'coupon_arrears_usd':arrears,
                     'redemption_usd':redemption, 'common_distribution_usd':common})
    rate = a['discount_rate']
    def pv(key):
        return math.fsum(row[key] / (1 + rate) ** row['year'] for row in rows)
    baseline = pv('available_usd') - a['equity_requirement_usd']
    sponsor_initial = a['equity_requirement_usd'] - capital + a['transaction_fee_usd']
    sponsor_npv = pv('common_distribution_usd') - sponsor_initial
    investor_npv = pv('coupon_paid_usd') + pv('redemption_usd') - capital
    return {'classification':'modelled_synthetic', 'currency':'USD', 'input_sha256':digest(case),
            'years':len(rows), 'annual':rows,
            'common_only_sponsor_npv_usd':baseline,
            'preferred_funded_sponsor_npv_usd':sponsor_npv,
            'preferred_investor_npv_usd':investor_npv,
            'sponsor_incremental_npv_usd':sponsor_npv-baseline,
            'sponsor_initial_cash_usd':sponsor_initial,
            'sponsor_initial_cash_saved_usd':capital-a['transaction_fee_usd'],
            'terminal_coupon_shortfall_usd':arrears,
            'terminal_capital_shortfall_usd':capital-rows[-1]['redemption_usd'],
            'evidence_gaps':list(case['evidence_gaps']), 'limitations':list(case['limitations']),
            'human_review_required':True, 'investment_authorized':False,
            'live_llm_executed':False, 'llm_cost':None, 'llm_tokens':None, 'llm_latency':None}


def run_workflow(case, planner=None):
    def evidence(context):
        c = context['payload']['case']
        validate_case(c)
        return {'success':True, 'case':c, 'validation':'schema_not_source_truth'}
    def finance(context):
        return {'success':True, 'report':screen_equity(context['upstream']['evidence']['case'])}
    return run_orchestrator(
        [AgentTask('evidence', 'evidence_contract', payload={'case':case}),
         AgentTask('finance', ROLE.id, dependencies=('evidence',))],
        {'evidence_contract':evidence, ROLE.id:finance}, planner, max_calls=4)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', type=Path)
    parser.add_argument('--output', type=Path, default=Path('outputs/preferred_equity'))
    args = parser.parse_args()
    case = json.loads(args.case.read_text()) if args.case else reference_case()
    run = run_workflow(case)
    if not run['success'] or run['results']['finance']['report'] != screen_equity(case):
        raise RuntimeError('Workflow or deterministic baseline parity failed')
    args.output.mkdir(parents=True, exist_ok=True)
    for name, value in [('inputs',case), ('report',run), ('edi_context',edi_context())]:
        (args.output/(name+'.json')).write_text(json.dumps(value, indent=2)+'\n')
    print(json.dumps(run['results']['finance']['report'], indent=2))


if __name__ == '__main__':
    main()
