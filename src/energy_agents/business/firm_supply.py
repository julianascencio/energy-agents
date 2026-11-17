"""Audit delivered renewable profiles before buying backup; advisory only."""

import argparse
import hashlib
import json
import math
from datetime import date, datetime, timedelta
from importlib.resources import files
from pathlib import Path
from urllib.parse import urlsplit

from ..orchestrator import AgentTask, run_orchestrator
from .bess import ROLE, _number
from .tandem import digest


def data_file(name):
    return json.loads(files('energy_agents').joinpath(f'data/firm_supply/{name}.json').read_text())


def reference_case():
    return data_file('case')


def validate_case(case):
    """Only synthetic, aligned hourly delivery scenarios are accepted in v1."""
    if (case['version'], case['classification'], case['currency'], case['cash_basis']) != (
        '1.0', 'synthetic', 'USD', 'undiscounted_finite_window_before_tax'
    ):
        raise ValueError('Require version 1.0 synthetic finite-window USD')
    source = case['source']
    url = urlsplit(source['url'])
    if (source['classification'] != 'published_model_not_observed_operation'
            or not source['publisher'] or url.scheme != 'https' or not url.netloc):
        raise ValueError('Require an HTTPS source with model classification')
    if not (date.fromisoformat(source['event_date']) <= date.fromisoformat(source['publication_date'])
            <= date.fromisoformat(case['as_of'])):
        raise ValueError('Invalid evidence dates')
    for key in ('limitations', 'evidence_gaps'):
        if not isinstance(case[key], list) or not case[key] or not all(
            isinstance(x, str) and x.strip() for x in case[key]
        ):
            raise ValueError('Explicit limitations and evidence gaps required')
    if case['assumptions']['classification'] != 'synthetic_assumptions':
        raise ValueError('Economic assumptions must be labelled synthetic')
    a = case['assumptions']
    for key, upper in [('backup_mw', 10000), ('backup_usd_mw_day', 1e6),
                       ('backup_usd_mwh', 1e5), ('lost_contribution_usd_mwh', 1e6)]:
        _number(a[key], key, upper=upper)
    hours = case['hours']
    if not isinstance(hours, list) or not 1 <= len(hours) <= 87840:
        raise ValueError('Require 1..87840 hourly samples')
    previous = None
    for row in hours:
        timestamp = datetime.fromisoformat(row['timestamp'])
        if timestamp.utcoffset() != timedelta(0):
            raise ValueError('UTC timestamps required')
        if previous is not None and timestamp - previous != timedelta(hours=1):
            raise ValueError('Require contiguous, unique, increasing hourly timestamps')
        previous = timestamp
        _number(row['demand_mw'], 'demand_mw', upper=10000)
    if math.fsum(row['demand_mw'] for row in hours) == 0:
        raise ValueError('Positive total demand required')
    offers = case['offers']
    if not isinstance(offers, list) or not 2 <= len(offers) <= 20:
        raise ValueError('Require 2..20 competing offers')
    ids = [offer['id'] for offer in offers]
    if any(not isinstance(x, str) or not x.strip() for x in ids) or len(ids) != len(set(ids)):
        raise ValueError('Unique nonempty offer IDs required')
    if case['baseline_offer'] not in ids:
        raise ValueError('Baseline must identify an offer')
    for offer in offers:
        if offer['profile_classification'] != 'synthetic_net_delivery_after_storage':
            raise ValueError('Require labelled net-delivery traces, not generation forecasts')
        _number(offer['window_fee_usd'], 'window_fee_usd', upper=1e12)
        profile = offer['delivered_mw']
        if not isinstance(profile, list) or len(profile) != len(hours):
            raise ValueError('Delivery profile must align with demand hours')
        for value in profile:
            _number(value, 'delivered_mw', upper=10000)


def delivery_audit(case):
    """No storage dispatch: audit each supplied net delivery at the customer meter."""
    validate_case(case)
    portfolios = []
    for offer in case['offers']:
        rows = []
        for hour, supply in zip(case['hours'], offer['delivered_mw'], strict=True):
            demand = hour['demand_mw']
            served = min(demand, supply)
            rows.append({'timestamp':hour['timestamp'], 'demand_mwh':demand,
                         'supplied_mwh':supply, 'renewable_served_mwh':served,
                         'excess_mwh':max(0, supply-demand),
                         'shortfall_mwh':max(0, demand-supply)})
        portfolios.append({'offer_id':offer['id'], 'hours':rows})
    return {'input_sha256':digest(case), 'portfolios':portfolios}


def screen_firm_supply(case, audit=None):
    reference = delivery_audit(case)
    if audit is not None and audit != reference:
        raise ValueError('Delivery handoff differs from input-bound reference')
    a = case['assumptions']
    demand = math.fsum(h['demand_mw'] for h in case['hours'])
    hours = len(case['hours'])
    rows = []
    for offer, profile in zip(case['offers'], reference['portfolios'], strict=True):
        trace = profile['hours']
        deficits = [h['shortfall_mwh'] for h in trace]
        backup = [min(v, a['backup_mw']) for v in deficits]
        unserved = [max(0, v-a['backup_mw']) for v in deficits]
        served = math.fsum(h['renewable_served_mwh'] for h in trace)
        backup_energy = math.fsum(backup)
        residual = math.fsum(unserved)
        capacity_cost = a['backup_mw'] * a['backup_usd_mw_day'] * hours/24
        variable_cost = backup_energy * a['backup_usd_mwh']
        cash_cost = offer['window_fee_usd'] + capacity_cost + variable_cost
        loss = residual * a['lost_contribution_usd_mwh']
        rows.append({'offer_id':offer['id'], 'demand_mwh':demand,
                     'renewable_served_mwh':served, 'renewable_energy_fraction':served/demand,
                     'fully_served_hours_without_backup':sum(v <= 1e-9 for v in deficits),
                     'fully_served_hours_with_backup':sum(v <= 1e-9 for v in unserved),
                     'peak_shortfall_mw':max(deficits), 'backup_energy_mwh':backup_energy,
                     'residual_unserved_mwh':residual, 'window_fee_usd':offer['window_fee_usd'],
                     'backup_capacity_cost_usd':capacity_cost,
                     'backup_variable_cost_usd':variable_cost, 'cash_cost_usd':cash_cost,
                     'modelled_lost_contribution_usd':loss,
                     'economic_cost_usd':cash_cost+loss,
                     'economic_cost_usd_per_demand_mwh':(cash_cost+loss)/demand})
    baseline = next(row for row in rows if row['offer_id'] == case['baseline_offer'])
    for row in rows:
        row['economic_cost_reduction_vs_baseline_usd'] = (
            baseline['economic_cost_usd'] - row['economic_cost_usd'])
        avoided = baseline['residual_unserved_mwh'] - row['residual_unserved_mwh']
        row['break_even_lost_contribution_usd_mwh'] = (
            (row['cash_cost_usd'] - baseline['cash_cost_usd'])/avoided if avoided > 0 else None)
    return {'classification':'modelled_synthetic', 'currency':'USD',
            'input_sha256':digest(case), 'horizon_hours':hours, 'offers':rows,
            'fee_only_baseline_choice':min(rows, key=lambda r:r['window_fee_usd'])['offer_id'],
            'lowest_modelled_economic_cost':min(rows, key=lambda r:r['economic_cost_usd'])['offer_id'],
            'economic_basis':'cash supply cost plus scenario lost contribution, not realised profit',
            'human_review_required':True, 'purchase_authorized':False,
            'evidence_gaps':list(case['evidence_gaps']), 'limitations':list(case['limitations']),
            'llm':{'executed':False, 'cost':None, 'latency':None, 'tokens':None}}


def edi_crosscheck(case):
    """Reuse pinned EDI energy matching, with zero battery to avoid double dispatch."""
    import energy_methods.hybrid_dispatch as method

    validate_case(case)
    metadata = data_file('edi_capabilities')
    actual = hashlib.sha256(Path(method.__file__).read_bytes()).hexdigest()
    if actual != metadata['source_sha256']:
        raise ValueError('Installed EDI method differs from inspected source')
    report = screen_firm_supply(case)
    for offer, expected in zip(case['offers'], report['offers'], strict=True):
        result = method.simulate_hybrid(
            offer['delivered_mw'], [0.0]*len(case['hours']),
            [h['demand_mw'] for h in case['hours']], battery_mwh=0, battery_mw=0)
        if not math.isclose(result.served_mwh, expected['renewable_served_mwh'], abs_tol=1e-8):
            raise ValueError('EDI delivery matching disagrees with reference')
    return {'executed':True, 'parity':True, 'source_sha256':actual,
            'catalogue_commit':metadata['commit'], 'input_sha256':digest(case),
            'scope':'net renewable delivery matching only; no battery or backup simulation'}


def run_workflow(case, planner=None):
    def evidence(context):
        c = context['payload']['case']
        validate_case(c)
        return {'success':True, 'case':c, 'audit':delivery_audit(c),
                'validation':'schema_and_arithmetic_not_source_truth'}

    def finance(context):
        upstream = context['upstream']['evidence']
        return {'success':True, 'report':screen_firm_supply(upstream['case'], upstream['audit'])}

    return run_orchestrator(
        [AgentTask('evidence', 'evidence_contract', payload={'case':case}),
         AgentTask('finance', ROLE.id, dependencies=('evidence',))],
        {'evidence_contract':evidence, ROLE.id:finance}, planner, max_calls=4)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', type=Path)
    parser.add_argument('--output', type=Path, default=Path('outputs/firm_supply'))
    parser.add_argument('--edi', action='store_true')
    args = parser.parse_args()
    case = json.loads(args.case.read_text()) if args.case else reference_case()
    run = run_workflow(case)
    direct = screen_firm_supply(case)
    if not run['success'] or run['results']['finance']['report'] != direct:
        raise RuntimeError('Scripted workflow/direct baseline parity failed')
    edi = edi_crosscheck(case) if args.edi else {'executed':False, 'parity':None}
    args.output.mkdir(parents=True, exist_ok=True)
    for name, value in [('inputs',case), ('workflow',run), ('report',direct),
                        ('delivery_audit',delivery_audit(case)), ('edi_execution',edi),
                        ('edi_capabilities',data_file('edi_capabilities'))]:
        (args.output/(name+'.json')).write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')
    print(json.dumps(direct, indent=2))


if __name__ == '__main__':
    main()
