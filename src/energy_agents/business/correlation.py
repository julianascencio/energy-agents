"""Synthetic standard-path hourly correlation cost screen; never an official bill."""

import argparse
import hashlib
import json
import math
from datetime import date, datetime, timedelta, timezone
from fractions import Fraction
from importlib.resources import files
from pathlib import Path
from zoneinfo import ZoneInfo

from ..orchestrator import AgentTask, run_orchestrator
from .bess import ROLE, _number
from .tandem import digest

SOURCE_URL = 'https://www.boe.es/diario_boe/xml.php?id=BOE-A-2026-24439'


def data_file(name):
    return json.loads(files('energy_agents').joinpath(f'data/correlation/{name}.json').read_text())


def month_hours(month):
    """UTC interval starts for a complete mainland Spanish civil month, including DST."""
    start = date.fromisoformat(month + '-01')
    end = (start.replace(day=28) + timedelta(days=4)).replace(day=1)
    zone = ZoneInfo('Europe/Madrid')
    first = datetime.combine(start, datetime.min.time(), zone).astimezone(timezone.utc)
    last = datetime.combine(end, datetime.min.time(), zone).astimezone(timezone.utc)
    return [(first + timedelta(hours=i)).isoformat()
            for i in range(int((last-first).total_seconds()/3600))]


def reference_case():
    case = data_file('case')
    case['hours'] = [{'timestamp':t, 'demand_mwh':20, 'backing_mwh':20 if i % 24 < 18 else 4,
                      'topup_mwh':0 if i % 24 < 18 else 12}
                     for i, t in enumerate(month_hours(case['month']))]
    return case


def validate_case(case):
    if (case['version'], case['classification'], case['currency'], case['pathway']) != (
        '1.0', 'synthetic', 'EUR', 'standard_article_8_80_percent'
    ):
        raise ValueError('Only synthetic EUR standard-path v1 cases supported')
    source = case['source']
    if source != data_file('case')['source']:
        raise ValueError('Source provenance must match the inspected BOE snapshot')
    if date.fromisoformat(case['as_of']) < date(2026, 11, 21):
        raise ValueError('Source publication is after as_of')
    if case['month'] < '2026-12':
        raise ValueError('Require a full month after entry into force')
    expected = month_hours(case['month'])
    if [h['timestamp'] for h in case['hours']] != expected:
        raise ValueError('Require complete contiguous Europe/Madrid month in canonical UTC')
    if case['scope'] != data_file('case')['scope']:
        raise ValueError('Require explicit scenario scope and eligibility assumptions')
    for key in ('limitations', 'evidence_gaps'):
        if not isinstance(case[key], list) or not case[key] or not all(
            isinstance(v, str) and v.strip() for v in case[key]
        ):
            raise ValueError('Explicit limitations and evidence gaps required')
    for h in case['hours']:
        for key in ('demand_mwh', 'backing_mwh', 'topup_mwh'):
            _number(h[key], key, upper=10000)
        if h['demand_mwh'] <= 0:
            raise ValueError('Zero-load hours require interpretation outside this screen')
    for key in ('topup_eur_mwh', 'implementation_eur'):
        _number(case[key], key, upper=1e9)


def _fraction(value):
    return Fraction(str(value))


def correlation_rate(deviation):
    """Article 9.3 bands; exact rational thresholds, 0 only for no deviation."""
    if not 0 <= deviation <= 1:
        raise ValueError('Deviation must be in [0,1]')
    if deviation == 0:
        return 0
    for upper, rate in [(Fraction(5, 100), 2), (Fraction(10, 100), 5),
                        (Fraction(20, 100), 8), (Fraction(50, 100), 11)]:
        if deviation < upper:
            return rate
    return 16


def correlation_audit(case):
    validate_case(case)
    traces = []
    for intervention in (False, True):
        rows = []
        for h in case['hours']:
            demand = _fraction(h['demand_mwh'])
            supply = _fraction(h['backing_mwh'])
            if intervention:
                supply += _fraction(h['topup_mwh'])
            deviation = max(Fraction(0), 1-supply/(Fraction(4, 5)*demand))
            rows.append({'timestamp':h['timestamp'], 'backing_mwh':float(supply),
                         'matched_mwh':float(min(demand, supply)),
                         'deviation_fraction':str(deviation)})
        traces.append(rows)
    return {'input_sha256':digest(case), 'baseline':traces[0], 'intervention':traces[1]}


def screen_correlation(case, audit=None):
    reference = correlation_audit(case)
    if audit is not None and audit != reference:
        raise ValueError('Modified or stale evidence handoff')
    demand = sum((_fraction(h['demand_mwh']) for h in case['hours']), Fraction(0))
    topup = sum((_fraction(h['topup_mwh']) for h in case['hours']), Fraction(0))
    rows = []
    for name in ('baseline', 'intervention'):
        trace = reference[name]
        mean = sum((Fraction(h['deviation_fraction']) for h in trace), Fraction(0))/len(trace)
        rate = correlation_rate(mean)
        premium = topup*_fraction(case['topup_eur_mwh']) if name == 'intervention' else 0
        fixed = _fraction(case['implementation_eur']) if name == 'intervention' else 0
        rows.append({'scenario':name, 'mean_hourly_deviation_percent':float(100*mean),
                     'rate_eur_mwh':rate, 'modelled_compensation_eur':float(demand*rate),
                     'matched_energy_fraction':sum(h['matched_mwh'] for h in trace)/float(demand),
                     'topup_premium_eur':float(premium), 'implementation_eur':float(fixed),
                     'relevant_cost_eur':float(demand*rate+premium+fixed)})
    avoided = rows[0]['modelled_compensation_eur']-rows[1]['modelled_compensation_eur']
    return {'classification':'modelled_synthetic_not_official_invoice', 'currency':'EUR',
            'input_sha256':digest(case), 'source':case['source'], 'month':case['month'],
            'hours':len(case['hours']), 'demand_mwh':float(demand), 'topup_mwh':float(topup),
            'scenarios':rows, 'avoided_correlation_compensation_eur':avoided,
            'net_cost_reduction_eur':rows[0]['relevant_cost_eur']-rows[1]['relevant_cost_eur'],
            'break_even_topup_eur_mwh':(
                (avoided-case['implementation_eur'])/float(topup) if topup else None),
            'scope':case['scope'], 'limitations':case['limitations'],
            'evidence_gaps':case['evidence_gaps'], 'human_review_required':True,
            'purchase_authorized':False, 'compliance_certified':False,
            'llm':{'executed':False, 'cost':None, 'latency':None, 'tokens':None}}


def edi_crosscheck(case):
    """Execute EDI only for the physical min(backing, load) comparator, not legal rules."""
    import energy_methods.hybrid_dispatch as method

    validate_case(case)
    metadata = data_file('edi_capabilities')
    actual = hashlib.sha256(Path(method.__file__).read_bytes()).hexdigest()
    if actual != metadata['source_sha256']:
        raise ValueError('EDI source hash mismatch')
    audit = correlation_audit(case)
    for name in ('baseline', 'intervention'):
        trace = audit[name]
        result = method.simulate_hybrid(
            [r['backing_mwh'] for r in trace], [0.0]*len(trace),
            [h['demand_mwh'] for h in case['hours']], battery_mwh=0, battery_mw=0)
        if not math.isclose(result.served_mwh, sum(r['matched_mwh'] for r in trace), abs_tol=1e-8):
            raise ValueError('EDI physical matching parity failed')
    return {'executed':True, 'parity':True, 'source_sha256':actual,
            'catalogue_commit':metadata['commit'], 'input_sha256':digest(case),
            'scope':'physical matching comparator only; no legal or tariff validation'}


def run_workflow(case, planner=None):
    def evidence(context):
        c = context['payload']['case']
        return {'success':True, 'case':c, 'audit':correlation_audit(c),
                'validation':'schema_and_arithmetic_not_eligibility_certification'}

    def finance(context):
        upstream = context['upstream']['evidence']
        return {'success':True, 'report':screen_correlation(upstream['case'], upstream['audit'])}

    return run_orchestrator(
        [AgentTask('evidence', 'evidence_contract', payload={'case':case}),
         AgentTask('finance', ROLE.id, dependencies=('evidence',))],
        {'evidence_contract':evidence, ROLE.id:finance}, planner, max_calls=4)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', type=Path)
    parser.add_argument('--output', type=Path, default=Path('outputs/correlation'))
    parser.add_argument('--edi', action='store_true')
    args = parser.parse_args()
    case = json.loads(args.case.read_text()) if args.case else reference_case()
    workflow = run_workflow(case)
    report = screen_correlation(case)
    if not workflow['success'] or workflow['results']['finance']['report'] != report:
        raise RuntimeError('Direct/scripted parity failed')
    edi = edi_crosscheck(case) if args.edi else {'executed':False, 'parity':None}
    args.output.mkdir(parents=True, exist_ok=True)
    for name, value in [('inputs', case), ('report', report), ('workflow', workflow),
                        ('audit', correlation_audit(case)), ('edi_execution', edi),
                        ('edi_capabilities', data_file('edi_capabilities'))]:
        (args.output/(name+'.json')).write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
