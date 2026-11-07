"""Advisory residential battery service screen; no device-control tools."""
import argparse
import hashlib
import json
import math
from copy import deepcopy
from datetime import date
from importlib.resources import files
from pathlib import Path

from ..orchestrator import AgentTask, run_orchestrator
from .bess import ROLE

EDI_COMMIT = 'dbd83f047b8d86f7940446c39b9ffe7fd78e7723'


def data_file(name):
    return json.loads(files('energy_agents').joinpath('data/reserve/' + name).read_text())


def validate_case(case):
    if case.get('version') != '1.0' or case.get('classification') != 'synthetic':
        raise ValueError('Version 1.0 synthetic case required')
    if case.get('currency') != 'USD':
        raise ValueError('Use explicit USD economics')
    source = case['source']
    if not source['url'].startswith('https://') or source['classification'] != 'utility_announcement':
        raise ValueError('Utility source provenance required')
    for key in ('event_date', 'publication_date'):
        date.fromisoformat(source[key])

    def number(v, low=0, high=math.inf):
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
            raise ValueError('Finite numeric input required')
        if not low <= v <= high:
            raise ValueError('Numeric input out of range')

    p = case['physical']
    number(p['event_hours'], .01, 24)
    number(p['round_trip_efficiency'], .01, 1)
    if not p['reserve_hours'] or len(set(p['reserve_hours'])) != len(p['reserve_hours']):
        raise ValueError('Unique reserve scenarios required')
    for h in p['reserve_hours']:
        number(h, 0, 48)
    if not 1 <= len(p['cohorts']) <= 100:
        raise ValueError('Supply 1..100 cohorts')
    ids = set()
    for c in p['cohorts']:
        if not c['id'] or c['id'] in ids:
            raise ValueError('Unique cohort IDs required')
        ids.add(c['id'])
        if type(c['count']) is not int or not 1 <= c['count'] <= 10000:
            raise ValueError('Invalid cohort count')
        for key in ('capacity_kwh', 'soc_kwh', 'power_kw', 'critical_load_kw'):
            number(c[key])
        if c['soc_kwh'] > c['capacity_kwh'] or c['critical_load_kw'] > c['power_kw']:
            raise ValueError('SOC or critical load exceeds rating')
        if any(type(c[k]) is not bool for k in ('consent', 'telemetry_fresh', 'available')):
            raise ValueError('Eligibility flags must be explicit booleans')
    for v in case['economics'].values():
        number(v)
    required = {'payment_usd_per_kwh', 'recharge_usd_per_kwh', 'wear_usd_per_kwh',
                'participant_usd_per_kwh', 'shortfall_usd_per_kwh', 'fixed_event_usd'}
    if set(case['economics']) != required:
        raise ValueError('Explicit economic cost fields required')


def physical_hash(case):
    return hashlib.sha256(json.dumps(case['physical'], sort_keys=True).encode()).hexdigest()


def build_edi_envelope(case):
    """Execute pinned EDI method on energy above household reserve, with kWh/MWh conversion.

    EDI is an explicit optional dependency. This is one flat event, no charging
    during the event. Reserve is DC SOC; critical load and service are AC.
    """
    import energy_methods.storage_peak_shift as method

    catalogue = data_file('edi_capabilities.json')
    entry = next(e for e in catalogue['entries'] if e['path'].endswith('storage_peak_shift.py'))
    if (catalogue['commit'] != EDI_COMMIT or
            hashlib.sha256(Path(method.__file__).read_bytes()).hexdigest() != entry['sha256']):
        raise ValueError('Installed EDI method differs from recorded source')
    simulate_storage_peak_shift = method.simulate_storage_peak_shift

    validate_case(case)
    p = case['physical']
    eta = math.sqrt(p['round_trip_efficiency'])
    scenarios = []
    for hours in p['reserve_hours']:
        rows = []
        for c in p['cohorts']:
            reserve = c['critical_load_kw'] * hours / eta
            eligible = all(c[k] for k in ('consent', 'telemetry_fresh', 'available'))
            usable = max(0, c['soc_kwh'] - reserve) if eligible else 0
            result = simulate_storage_peak_shift(
                [0.0], [c['power_kw'] / 1000], battery_power_mw=c['power_kw'] / 1000,
                battery_energy_mwh=max(0, c['capacity_kwh'] - reserve) / 1000,
                initial_soc_mwh=usable / 1000, timestep_hours=p['event_hours'],
                round_trip_efficiency=p['round_trip_efficiency'])
            delivered = result.peak_delivered_mwh * 1000
            rows.append({'id': c['id'], 'count': c['count'], 'eligible': eligible,
                         'reserve_dc_kwh': reserve,
                         'initial_reserve_deficit_kwh': max(0, reserve - c['soc_kwh']),
                         'delivered_ac_kwh_each': delivered,
                         'final_soc_kwh_each': c['soc_kwh'] - delivered / eta})
        scenarios.append({'reserve_hours': hours, 'cohorts': rows})
    return {'edi_commit': EDI_COMMIT, 'method': 'simulate_storage_peak_shift',
            'classification': 'modelled_synthetic', 'physical_sha256': physical_hash(case),
            'scenarios': scenarios}


def validate_envelope(case, envelope):
    """Check provenance binding and independent one-event energy/power identities."""
    validate_case(case)
    if (envelope.get('physical_sha256') != physical_hash(case)
            or envelope.get('edi_commit') != EDI_COMMIT
            or envelope.get('classification') != 'modelled_synthetic'
            or envelope.get('method') != 'simulate_storage_peak_shift'):
        raise ValueError('Envelope provenance mismatch')
    p = case['physical']
    eta = math.sqrt(p['round_trip_efficiency'])
    if [s['reserve_hours'] for s in envelope['scenarios']] != p['reserve_hours']:
        raise ValueError('Scenario mismatch')
    for scenario in envelope['scenarios']:
        if len(scenario['cohorts']) != len(p['cohorts']):
            raise ValueError('Cohort mismatch')
        for c, row in zip(p['cohorts'], scenario['cohorts'], strict=True):
            eligible = all(c[k] for k in ('consent', 'telemetry_fresh', 'available'))
            reserve = c['critical_load_kw'] * scenario['reserve_hours'] / eta
            expected = min(c['power_kw'] * p['event_hours'],
                           max(0, c['soc_kwh'] - reserve) * eta) if eligible else 0
            if row['id'] != c['id'] or row['count'] != c['count'] or row['eligible'] != eligible:
                raise ValueError('Cohort identity or eligibility mismatch')
            checks = {'reserve_dc_kwh': reserve,
                      'initial_reserve_deficit_kwh': max(0, reserve - c['soc_kwh']),
                      'delivered_ac_kwh_each': expected,
                      'final_soc_kwh_each': c['soc_kwh'] - expected / eta}
            for key, value in checks.items():
                if type(row[key]) not in (float, int) or not math.isclose(row[key], value, abs_tol=1e-8):
                    raise ValueError(f'Envelope energy identity failed: {key}')


def screen_event(case, envelope):
    """Compare nameplate overcommitment with a reserve-limited advisory offer.

    Payment is per delivered AC kWh. Shortfall is contracted minus delivered
    energy. Recharge restores initial SOC after the event; costs include both
    conversion losses. No export payment or retail saving is double-counted.
    """
    validate_envelope(case, envelope)
    p, e = case['physical'], case['economics']
    nameplate = sum(c['power_kw'] * c['count'] for c in p['cohorts']) * p['event_hours']
    rows = []
    for scenario in envelope['scenarios']:
        energy = sum(c['delivered_ac_kwh_each'] * c['count'] for c in scenario['cohorts'])
        recharge = energy / p['round_trip_efficiency']
        revenue = energy * e['payment_usd_per_kwh']
        costs = (recharge * e['recharge_usd_per_kwh'] + energy *
                 (e['wear_usd_per_kwh'] + e['participant_usd_per_kwh']) + e['fixed_event_usd'])
        shortfall = max(0, nameplate - energy)
        net = revenue - costs
        rows.append({'reserve_hours': scenario['reserve_hours'], 'delivered_kwh': energy,
                     'homes_below_reserve_target': sum(c['count'] for c in scenario['cohorts']
                         if c['initial_reserve_deficit_kwh'] > 1e-8),
                     'reserve_limited_offer_kw': energy / p['event_hours'],
                     'nameplate_offer_kw': nameplate / p['event_hours'],
                     'nameplate_shortfall_kwh': shortfall,
                     'recharge_kwh': recharge, 'revenue_usd': revenue, 'cost_usd': costs,
                     'reserve_net_usd': net,
                     'nameplate_net_usd': net - shortfall * e['shortfall_usd_per_kwh'],
                     'avoided_penalty_usd': shortfall * e['shortfall_usd_per_kwh'],
                     'break_even_payment_usd_per_kwh': costs / energy if energy else None,
                     'recommended_action': 'review_offer' if net > 0 else 'abstain',
                     'best_net_usd': max(0, net)})
    return {'classification': 'modelled_synthetic', 'currency': 'USD',
            'source': deepcopy(case['source']), 'physical_sha256': physical_hash(case),
            'scenarios': rows, 'abstain_net_usd': 0, 'human_review_required': True,
            'llm': {'executed': False, 'tokens': None, 'cost': None, 'latency': None}}


def run_reserve_workflow(case, envelope, planner=None):
    """Fixed evidence-to-finance handoff through the existing orchestrator."""
    def evidence(context):
        payload = context['payload']
        validate_envelope(payload['case'], payload['envelope'])
        return {'success': True, **payload}

    def finance(context):
        payload = context['upstream']['evidence']
        return {'success': True, 'screen': screen_event(payload['case'], payload['envelope'])}

    return run_orchestrator(
        [AgentTask('evidence', 'evidence_contract', payload={'case': case, 'envelope': envelope}),
         AgentTask('finance', ROLE.id, dependencies=('evidence',))],
        {'evidence_contract': evidence, ROLE.id: finance}, planner, max_calls=4)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('outputs/reserve'))
    parser.add_argument('--edi', action='store_true', help='Recompute with installed pinned EDI')
    args = parser.parse_args()
    case = data_file('case.json')
    envelope = build_edi_envelope(case) if args.edi else data_file('envelope.json')
    run = run_reserve_workflow(case, envelope)
    assert run['success'] and run['results']['finance']['screen'] == screen_event(case, envelope)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / 'report.json').write_text(json.dumps(run, indent=2) + '\n')
    print(json.dumps(run['results']['finance']['screen'], indent=2))


if __name__ == '__main__':
    main()
