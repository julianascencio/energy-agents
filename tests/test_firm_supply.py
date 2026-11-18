from copy import deepcopy

import pytest

from energy_agents.business.firm_supply import (
    delivery_audit,
    edi_crosscheck,
    reference_case,
    run_workflow,
    screen_firm_supply,
)


def test_independent_week_ledger_and_different_meanings_of_coverage():
    result = screen_firm_supply(reference_case())
    a, b = result['offers']
    assert a['renewable_energy_fraction'] == b['renewable_energy_fraction'] == .9
    assert (a['fully_served_hours_without_backup'], b['fully_served_hours_without_backup']) == (126, 0)
    assert (a['fully_served_hours_with_backup'], b['fully_served_hours_with_backup']) == (126, 168)
    assert (a['peak_shortfall_mw'], b['peak_shortfall_mw']) == (4, 1)
    # Seven days * six shortfall hours/day * (4 - 2) MW.
    assert a['residual_unserved_mwh'] == 84
    assert a['backup_energy_mwh'] == 84
    assert b['backup_energy_mwh'] == 168
    assert b['residual_unserved_mwh'] == 0
    assert a['cash_cost_usd'] == 126000 + 2*200*7 + 84*200
    assert b['cash_cost_usd'] == 133000 + 2*200*7 + 168*200
    assert a['modelled_lost_contribution_usd'] == 84*2000
    assert a['economic_cost_usd'] == 313600
    assert b['economic_cost_usd'] == 169400
    assert b['economic_cost_reduction_vs_baseline_usd'] == 144200
    assert b['break_even_lost_contribution_usd_mwh'] == pytest.approx(23800/84)
    assert result['fee_only_baseline_choice'] == 'concentrated_gap'
    assert result['lowest_modelled_economic_cost'] == 'distributed_gap'
    for row in result['offers']:
        assert row['demand_mwh'] == (row['renewable_served_mwh'] + row['backup_energy_mwh']
                                     + row['residual_unserved_mwh'])


def test_cost_and_capacity_sensitivities_reverse_choice():
    case = reference_case()
    case['assumptions']['lost_contribution_usd_mwh'] = 0
    assert screen_firm_supply(case)['lowest_modelled_economic_cost'] == 'concentrated_gap'
    case['assumptions']['lost_contribution_usd_mwh'] = 23800/84
    a, b = screen_firm_supply(case)['offers']
    assert a['economic_cost_usd'] == pytest.approx(b['economic_cost_usd'])
    case['assumptions'].update(backup_mw=4, lost_contribution_usd_mwh=2000)
    a, b = screen_firm_supply(case)['offers']
    assert a['residual_unserved_mwh'] == b['residual_unserved_mwh'] == 0
    assert a['economic_cost_usd'] == 165200
    assert b['economic_cost_usd'] == 172200
    assert b['break_even_lost_contribution_usd_mwh'] is None


def test_surplus_zero_demand_hour_and_finite_window_not_annualized():
    case = reference_case()
    case['hours'] = case['hours'][:2]
    case['hours'][0]['demand_mw'] = 0
    for offer in case['offers']:
        offer['delivered_mw'] = [15, 3]
    case['assumptions']['backup_mw'] = 0
    report = screen_firm_supply(case)
    assert report['horizon_hours'] == 2
    assert report['offers'][0]['demand_mwh'] == 10
    assert report['offers'][0]['renewable_served_mwh'] == 3
    assert report['offers'][0]['residual_unserved_mwh'] == 7
    audit = delivery_audit(case)['portfolios'][0]['hours']
    assert audit[0]['excess_mwh'] == 15
    # Excess energy in another hour must not fill a shortfall without a storage model.
    assert report['offers'][0]['renewable_energy_fraction'] == .3
    assert report['offers'][0]['window_fee_usd'] == 126000


@pytest.mark.parametrize('value', [True, float('nan'), float('inf'), -1, '2'])
def test_invalid_power_and_cost(value):
    case = reference_case()
    case['assumptions']['backup_mw'] = value
    with pytest.raises(ValueError):
        screen_firm_supply(case)
    case = reference_case()
    case['offers'][0]['delivered_mw'][0] = value
    with pytest.raises(ValueError):
        screen_firm_supply(case)


@pytest.mark.parametrize('timestamp', [
    '2026-01-01T00:00:00+00:00', '2026-01-01T02:00:00+00:00',
    '2026-01-01T01:00:00', '2026-01-01T01:00:00+01:00', 'bad-date'])
def test_bad_alignment(timestamp):
    case = reference_case()
    case['hours'][1]['timestamp'] = timestamp
    with pytest.raises(ValueError):
        delivery_audit(case)


def test_missing_profile_duplicate_offer_and_zero_demand():
    case = reference_case()
    case['offers'][0]['delivered_mw'].pop()
    with pytest.raises(ValueError, match='align'):
        delivery_audit(case)
    case = reference_case()
    case['offers'][1]['id'] = case['offers'][0]['id']
    with pytest.raises(ValueError, match='Unique'):
        delivery_audit(case)
    case = reference_case()
    for row in case['hours']:
        row['demand_mw'] = 0
    with pytest.raises(ValueError, match='Positive'):
        delivery_audit(case)


def test_reported_medians_do_not_price_the_offers():
    case = reference_case()
    before = screen_firm_supply(case)
    case['source']['reported_model']['global_median_with_wind_90_percent_usd_mwh'] = 99999
    after = screen_firm_supply(case)
    assert before['offers'] == after['offers']
    assert before['input_sha256'] != after['input_sha256']


def test_evidence_handoff_and_scripted_parity():
    case = reference_case()
    original = deepcopy(case)
    workflow = run_workflow(case)
    assert workflow['success']
    assert workflow['results']['finance']['report'] == screen_firm_supply(case)
    assert case == original
    audit = delivery_audit(case)
    audit['portfolios'][0]['hours'][0]['renewable_served_mwh'] += 1
    with pytest.raises(ValueError, match='handoff'):
        screen_firm_supply(case, audit)
    audit = delivery_audit(case)
    case['assumptions']['backup_mw'] += 1
    with pytest.raises(ValueError, match='handoff'):
        screen_firm_supply(case, audit)
    for key, value in [('url', 'file:///tmp/news'), ('publication_date','2026-11-18'),
                       ('classification','observed')]:
        case = reference_case()
        case['source'][key] = value
        assert run_workflow(case)['states'] == {'evidence':'failed', 'finance':'blocked'}
    case = reference_case()
    case['evidence_gaps'] = []
    assert run_workflow(case)['states']['finance'] == 'blocked'


@pytest.mark.parametrize('action', [
    {'tool':'trade_energy','arguments':{}}, {'tool':'buy_backup','arguments':{}},
    {'tool':'delegate','arguments':{'task_id':'finance'}}])
def test_no_external_actions_or_premature_finance(action):
    class Planner:
        def next_action(self, context):
            return action
    workflow = run_workflow(reference_case(), Planner())
    assert not workflow['success']
    assert all(row['status'] == 'rejected' for row in workflow['trace'])


def test_optional_edi_execution_and_hash_guard(monkeypatch):
    pytest.importorskip('energy_methods.hybrid_dispatch')
    result = edi_crosscheck(reference_case())
    assert result['executed'] and result['parity']
    import energy_agents.business.firm_supply as module
    original = module.data_file

    def changed(name):
        value = original(name)
        value['source_sha256'] = '0'*64
        return value

    monkeypatch.setattr(module, 'data_file', changed)
    with pytest.raises(ValueError, match='differs'):
        edi_crosscheck(reference_case())
