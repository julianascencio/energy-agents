from copy import deepcopy

import pytest

from energy_agents.business.reserve import (
    build_edi_envelope,
    data_file,
    run_reserve_workflow,
    screen_event,
    validate_case,
    validate_envelope,
)


def test_independent_storm_case():
    result = screen_event(data_file('case.json'), data_file('envelope.json'))['scenarios'][1]
    # AC energy after eight-hour reserves, then bounded by each power * 3h.
    assert result['delivered_kwh'] == pytest.approx(50 * 14.8 + 50 * 5 + 25 * 18)
    assert result['reserve_limited_offer_kw'] == 480
    recharge = 1440 / (.95 * .95)
    net = 1440 * .6 - recharge * .15 - 1440 * (.04 + .1) - 50
    assert result['reserve_net_usd'] == pytest.approx(net)
    assert result['nameplate_net_usd'] == pytest.approx(net - 210 * 3)
    assert result['avoided_penalty_usd'] == 630


def test_break_even_abstain_and_no_fake_llm():
    case, envelope = data_file('case.json'), data_file('envelope.json')
    report = screen_event(case, envelope)
    case['economics']['payment_usd_per_kwh'] = report['scenarios'][1]['break_even_payment_usd_per_kwh']
    assert screen_event(case, envelope)['scenarios'][1]['reserve_net_usd'] == pytest.approx(0)
    case['economics']['payment_usd_per_kwh'] = 0
    assert all(r['recommended_action'] == 'abstain' for r in screen_event(case, envelope)['scenarios'])
    assert report['llm'] == {'executed': False, 'tokens': None, 'cost': None, 'latency': None}


@pytest.mark.parametrize('key,value', [('event_hours', 0), ('event_hours', True),
    ('round_trip_efficiency', float('nan')), ('round_trip_efficiency', 1.1)])
def test_bad_physical_inputs(key, value):
    case = data_file('case.json')
    case['physical'][key] = value
    with pytest.raises(ValueError):
        validate_case(case)


@pytest.mark.parametrize('key,value', [('count', True), ('consent', 'yes'),
    ('soc_kwh', 100), ('critical_load_kw', 20), ('power_kw', -1)])
def test_bad_cohort_inputs(key, value):
    case = data_file('case.json')
    case['physical']['cohorts'][0][key] = value
    with pytest.raises(ValueError):
        validate_case(case)


def test_physical_change_cannot_replay_stale_envelope():
    case, envelope = data_file('case.json'), data_file('envelope.json')
    case['physical']['cohorts'][0]['telemetry_fresh'] = False
    with pytest.raises(ValueError, match='provenance'):
        screen_event(case, envelope)


@pytest.mark.parametrize('field', ['delivered_ac_kwh_each', 'final_soc_kwh_each', 'reserve_dc_kwh'])
def test_tampered_physics_blocked(field):
    case, envelope = data_file('case.json'), data_file('envelope.json')
    envelope['scenarios'][0]['cohorts'][0][field] += 1
    run = run_reserve_workflow(case, envelope)
    assert run['states'] == {'evidence': 'failed', 'finance': 'blocked'}


def test_parity_and_isolated_handoff():
    case, envelope = data_file('case.json'), data_file('envelope.json')
    before = deepcopy(case)
    run = run_reserve_workflow(case, envelope)
    assert run['success']
    assert [r['task_id'] for r in run['trace']] == ['evidence', 'finance']
    assert run['results']['finance']['screen'] == screen_event(case, envelope)
    assert case == before


@pytest.mark.parametrize('action', [{'tool': 'control_battery', 'arguments': {}},
    {'tool': 'delegate', 'arguments': {'task_id': 'finance'}}])
def test_permissions_and_order(action):
    class InvalidPlanner:
        def next_action(self, context):
            return action
    run = run_reserve_workflow(data_file('case.json'), data_file('envelope.json'), InvalidPlanner())
    assert not run['success'] and len(run['trace']) == 4
    assert all(t['status'] == 'rejected' for t in run['trace'])


def test_source_required():
    case = data_file('case.json')
    case['source']['url'] = ''
    with pytest.raises(ValueError):
        validate_case(case)


def test_edi_execution_matches_fixture_and_respects_optout():
    pytest.importorskip('energy_methods.storage_peak_shift')
    case = data_file('case.json')
    assert build_edi_envelope(case) == data_file('envelope.json')
    case['physical']['cohorts'][0]['consent'] = False
    case['physical']['cohorts'][1]['soc_kwh'] = 0
    envelope = build_edi_envelope(case)
    validate_envelope(case, envelope)
    for scenario in envelope['scenarios']:
        assert scenario['cohorts'][0]['delivered_ac_kwh_each'] == 0
        assert scenario['cohorts'][1]['delivered_ac_kwh_each'] == 0
        assert scenario['cohorts'][1]['initial_reserve_deficit_kwh'] > 0


def test_edi_source_drift_rejected(monkeypatch):
    method = pytest.importorskip('energy_methods.storage_peak_shift')
    monkeypatch.setattr(method, '__file__', __file__)
    with pytest.raises(ValueError, match='recorded source'):
        build_edi_envelope(data_file('case.json'))
