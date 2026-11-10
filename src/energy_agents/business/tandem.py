"""Advisory module premium ceiling from explicit annual clipped-energy scenarios."""
import argparse
import hashlib
import json
import math
from datetime import date
from importlib.resources import files
from pathlib import Path

from ..orchestrator import AgentTask, run_orchestrator
from .bess import ROLE, _number


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def reference_case():
    return json.loads(files('energy_agents').joinpath('data/tandem/case.json').read_text())


def validate_case(case):
    if case.get('version') != '1.0' or case.get('classification') != 'synthetic':
        raise ValueError('Explicit synthetic version 1.0 case required')
    if case.get('currency') != 'USD' or case.get('cash_basis') != 'constant_real_year_end':
        raise ValueError('USD constant-real year-end cash basis required')
    s = case['source']
    if s['classification'] != 'manufacturer_claim' or not s['url'].startswith('https://'):
        raise ValueError('Cited manufacturer claim required; not field validation')
    for k in ('publication_date', 'event_date'):
        date.fromisoformat(s[k])
    n = case['years']
    if type(n) is not int or not 1 <= n <= 40:
        raise ValueError('Horizon must be integer 1..40')
    for k in ('premium_usd', 'extra_opex_usd_year', 'discount_rate'):
        _number(case[k], k)
    _number(case['value_usd_mwh'], 'value', lower=-10000, upper=10000)
    _number(case['discount_rate'], 'discount', upper=1)
    e = case['energy']
    if not 1 <= len(e['alternatives']) <= 10 or len(e['baseline_mwh']) != n:
        raise ValueError('Bounded alternatives and aligned baseline required')
    for values in [e['baseline_mwh'], *e['alternatives'].values()]:
        if len(values) != n:
            raise ValueError('Annual energy lengths must match horizon')
        for x in values:
            _number(x, 'annual MWh')
    p = case['provenance']
    if p['energy_sha256'] != digest(e) or p['classification'] != 'synthetic_edi_execution':
        raise ValueError('Energy provenance mismatch')
    if len(p['commit']) != 40 or len(p['method_sha256']) != 64:
        raise ValueError('Pinned EDI method required')


def screen_premium(case):
    """Incremental energy value less extra O&M, discounted before upfront premium.

    The premium includes ALL incremental installed costs, not just modules.
    Negative ceilings are retained: they mean a discount would be needed.
    """
    validate_case(case)
    scenarios = {}
    for name, values in case['energy']['alternatives'].items():
        rows = []
        for y, (base, alt) in enumerate(zip(case['energy']['baseline_mwh'], values), 1):
            delta = alt - base
            cash = delta * case['value_usd_mwh'] - case['extra_opex_usd_year']
            rows.append({'year': y, 'incremental_mwh': delta, 'net_operating_usd': cash,
                         'discounted_usd': cash / (1 + case['discount_rate']) ** y})
        ceiling = math.fsum(r['discounted_usd'] for r in rows)
        scenarios[name] = {'annual': rows, 'premium_ceiling_usd': ceiling,
                           'incremental_npv_usd': ceiling - case['premium_usd'],
                           'clears_financial_screen': ceiling >= case['premium_usd']}
    return {'scenarios': scenarios, 'currency': 'USD', 'input_sha256': digest(case),
            'classification': 'modelled_synthetic', 'human_review_required': True,
            'llm_cost_usd': None, 'llm_latency_seconds': None, 'llm_tokens': None,
            'limitation': 'No field validation, probability weights, warranty or purchase approval'}


def run_workflow(case, planner=None):
    def evidence(context):
        c = context['payload']['case']
        validate_case(c)
        return {'success': True, 'case': c}

    def finance(context):
        return {'success': True, 'report': screen_premium(context['upstream']['evidence']['case'])}

    return run_orchestrator(
        [AgentTask('evidence', 'evidence_contract', payload={'case': case}),
         AgentTask('finance', ROLE.id, dependencies=('evidence',))],
        {'evidence_contract': evidence, ROLE.id: finance}, planner, max_calls=4)


def edi_energy():
    """Bounded local EDI call; no network, shell, dynamic source loading or controls.

    Synthetic inverter-input-equivalent DC profile, 8760 one-hour samples.
    Same usable module area; 20% uplift is a scenario, not predicted tandem yield.
    """
    from energy_methods.pv_repowering import lifetime_intervention

    profile = [0.44 * max(0, math.sin(math.pi * ((h % 24) - 6) / 12))
               * (0.75 + 0.25 * math.sin(2 * math.pi * (h // 24 - 80) / 365))
               for h in range(8760)]

    def energy(scale, rate, limit):
        frame = lifetime_intervention(
            [x * scale for x in profile], [(1 - rate) ** y for y in range(20)],
            ac_limit_mw=limit, availability=[0.98] * 20, price_per_mwh=0,
            annual_opex=0, upfront_cost=0, discount_rate=0)
        return [float(x) for x in frame['energy_mwh']]

    return {'baseline_mwh': energy(1, .005, .30), 'alternatives': {
        'equal_degradation': energy(1.2, .005, .30),
        'faster_degradation': energy(1.2, .02, .30),
        'no_yield_uplift': energy(1, .005, .30)}}, digest(profile)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, default=Path('outputs/tandem'))
    p.add_argument('--verify-edi', action='store_true')
    args = p.parse_args()
    case = reference_case()
    if args.verify_edi:
        energy, profile_hash = edi_energy()
        if digest(energy) != case['provenance']['energy_sha256'] or profile_hash != case['provenance']['profile_sha256']:
            raise ValueError('EDI replay differs from pinned fixture')
    run = run_workflow(case)
    if not run['success'] or run['results']['finance']['report'] != screen_premium(case):
        raise RuntimeError('Workflow/baseline mismatch')
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / 'report.json').write_text(json.dumps(run, indent=2) + '\n')
    print(json.dumps({k: v['incremental_npv_usd'] for k, v in
                      run['results']['finance']['report']['scenarios'].items()}, indent=2))


if __name__ == '__main__':
    main()
