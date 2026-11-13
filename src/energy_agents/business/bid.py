"""Evidence-gated development-spend screening, never a bid submission."""
import argparse
import json
from datetime import date
from importlib.resources import files
from pathlib import Path
from urllib.parse import urlsplit

from ..orchestrator import AgentTask, run_orchestrator
from .bess import ROLE, _number
from .tandem import digest


def reference_case():
    return json.loads(files('energy_agents').joinpath('data/bid/case.json').read_text())


def edi_context():
    """Return bounded packaged metadata; no imports, retrieval or numerical execution."""
    return json.loads(files('energy_agents').joinpath('data/bid/edi_capabilities.json').read_text())


def validate_case(case):
    if (case['version'], case['classification'], case['currency'], case['cash_basis']) != (
            '1.0', 'synthetic', 'USD', 'present_value_at_decision'):
        raise ValueError('Require explicit synthetic USD decision-date PV version 1.0')
    s = case['source']
    url = urlsplit(s['url'])
    if s['classification'] != 'agency_announcement' or url.scheme != 'https' or not url.netloc:
        raise ValueError('Agency source with HTTPS URL required')
    for key in ('publication_date', 'event_date'):
        date.fromisoformat(s[key])
    if not s['publisher'] or not s['deadline_status']:
        raise ValueError('Publisher and explicit deadline verification status required')
    for key in ('evidence_gaps', 'limitations'):
        if not isinstance(case[key], list) or not case[key] or not all(
                isinstance(v, str) and v.strip() for v in case[key]):
            raise ValueError('Explicit evidence gaps and limitations required')
    a = case['assumptions']
    for key in ('qualification_probability', 'award_probability_given_qualification',
                'staging_award_probability_haircut', 'annual_discount_rate'):
        _number(a[key], key, upper=1)
    for key in ('qualification_cost_usd', 'full_bid_cost_usd', 'staging_overhead_usd',
                'award_project_npv_usd'):
        _number(a[key], key, upper=1e12)
    _number(a['stage_delay_months'], 'delay', upper=24)


def screen_bid(case):
    """Decision tree with separate conditional probabilities and application costs.

    All award-conditional project value is already discounted to decision date.
    Only the staged bid preparation expense needs a time adjustment here.
    A relative haircut captures assumed competitiveness lost through staging.
    """
    validate_case(case)
    a = case['assumptions']
    p, q = a['qualification_probability'], a['award_probability_given_qualification']
    staged_q = q * (1 - a['staging_award_probability_haircut'])
    c1, c2, overhead = (a[k] for k in ('qualification_cost_usd', 'full_bid_cost_usd',
                                     'staging_overhead_usd'))
    df = (1 + a['annual_discount_rate']) ** (-a['stage_delay_months'] / 12)
    value = a['award_project_npv_usd']
    upfront_spend, staged_spend = c1 + c2, c1 + overhead + p * c2 * df
    def row(probability, spend, maximum_loss):
        return {'award_probability': probability, 'expected_spend_usd': spend,
                'expected_net_value_usd': probability * value - spend,
                'worst_case_loss_usd': maximum_loss,
                'break_even_project_npv_usd': spend / probability if probability else None}
    # Worst case is across branches with nonzero probability, including no award.
    def worst(staged):
        outcomes = []
        initial = c1 + (overhead if staged else c2)
        win = staged_q if staged else q
        qualified_cost = initial + (c2 * df if staged else 0)
        if p < 1:
            outcomes.append(-initial)
        if p > 0 and win < 1:
            outcomes.append(-qualified_cost)
        if p > 0 and win > 0:
            outcomes.append(value - qualified_cost)
        return max(0, -min(outcomes))
    rows = {'no_bid': row(0, 0, 0),
            'upfront': row(p * q, upfront_spend, worst(False)),
            'staged': row(p * staged_q, staged_spend, worst(True))}
    delta = rows['staged']['expected_net_value_usd'] - rows['upfront']['expected_net_value_usd']
    return {'classification':'modelled_synthetic', 'currency':'USD',
            'input_sha256':digest(case), 'strategies':rows,
            'staged_incremental_expected_value_usd':delta,
            'scenario_preferred_strategy':max(rows, key=lambda k: rows[k]['expected_net_value_usd']),
            'evidence_gaps':list(case['evidence_gaps']), 'limitations':list(case['limitations']),
            'deadline_status':case['source']['deadline_status'],
            'human_review_required':True, 'spending_authorized':False,
            'live_llm_executed':False, 'llm_cost':None, 'llm_tokens':None, 'llm_latency':None}


def run_workflow(case, planner=None):
    def evidence(context):
        c = context['payload']['case']
        validate_case(c)
        return {'success':True, 'case':c, 'validation':'schema_not_source_truth'}
    def finance(context):
        return {'success':True, 'report':screen_bid(context['upstream']['evidence']['case'])}
    return run_orchestrator(
        [AgentTask('evidence', 'evidence_contract', payload={'case':case}),
         AgentTask('finance', ROLE.id, dependencies=('evidence',))],
        {'evidence_contract':evidence, ROLE.id:finance}, planner, max_calls=4)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', type=Path)
    parser.add_argument('--output', type=Path, default=Path('outputs/storage_bid'))
    args = parser.parse_args()
    case = json.loads(args.case.read_text()) if args.case else reference_case()
    run = run_workflow(case)
    if not run['success'] or run['results']['finance']['report'] != screen_bid(case):
        raise RuntimeError('Workflow or baseline parity failed')
    args.output.mkdir(parents=True, exist_ok=True)
    for name, value in [('inputs', case), ('report', run), ('edi_context', edi_context())]:
        (args.output / (name + '.json')).write_text(json.dumps(value, indent=2) + '\n')
    print(json.dumps(run['results']['finance']['report'], indent=2))


if __name__ == '__main__':
    main()
