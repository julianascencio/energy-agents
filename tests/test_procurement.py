from copy import deepcopy

import pytest

from energy_agents.business.procurement import (
    cancellation_sensitivity,
    delivery_scenarios,
    reference_case,
    run_procurement_workflow,
    screen_reservation,
)


def test_independent_zero_discount_accounting_and_bottleneck():
    case = reference_case()
    case['assumptions']['annual_discount_rate'] = 0
    r = screen_reservation(case)
    ready, late, cancel = r['scenarios']
    assert (ready['wait_cod_month'], ready['reserve_cod_month']) == (51, 39)
    assert len(ready['operating_cash']) == 12
    assert ready['incremental_npv_eur'] == 12 * 400000 - 600000 - 200000
    assert (late['wait_cod_month'], late['reserve_cod_month']) == (57, 57)
    assert late['operating_cash'] == []
    assert late['incremental_npv_eur'] == -800000
    assert cancel['reserve_cod_month'] is None
    assert cancel['incremental_npv_eur'] == -600000
    assert r['reserve_expected_npv_eur'] == 1640000
    assert r['reserve_worst_loss_eur'] == 800000
    assert r['reserve_loss_probability'] == 0.5


def test_discount_timing_and_economic_fee_ceiling():
    c = reference_case()
    r = screen_reservation(c)
    operating = sum(400000 / 1.08 ** (m / 12) for m in range(40, 52))
    assert r['reserve_expected_npv_eur'] == pytest.approx(
        .5 * operating - 600000 - .8 * 200000 / 1.08)
    c['assumptions']['reservation_fee_eur'] = r['break_even_reservation_fee_eur']
    assert screen_reservation(c)['reserve_expected_npv_eur'] == pytest.approx(0, abs=1e-8)


def test_refund_and_premium_are_conditional_and_discounted():
    c = reference_case()
    c['assumptions']['cancel_refund_fraction'] = 0.5
    r = screen_reservation(c)
    cancel = r['scenarios'][2]
    assert cancel['incremental_npv_eur'] == pytest.approx(-600000 + 300000 / 1.08)
    assert cancel['exercise_premium_eur'] == 0
    assert all(s['refund_eur'] == 0 for s in r['scenarios'][:2])
    c['assumptions']['reservation_fee_eur'] = r['break_even_reservation_fee_eur']
    assert screen_reservation(c)['reserve_expected_npv_eur'] == pytest.approx(0, abs=1e-8)


def test_risk_limit_can_override_positive_expectation():
    c = reference_case()
    c['assumptions']['downside_limit_eur'] = 700000
    r = screen_reservation(c)
    assert r['reserve_expected_npv_eur'] > 0
    assert not r['downside_limit_passed'] and r['screened_choice'] == 'wait'


def test_all_cancel_full_immediate_refund_is_undefined_fee_ceiling():
    c = reference_case()
    c['scenarios'] = [{'id': 'cancel', 'probability': 1, 'proceed': False}]
    c['assumptions'].update(decision_month=0, cancel_refund_fraction=1)
    r = screen_reservation(c)
    assert r['reserve_expected_npv_eur'] == 0
    assert r['break_even_reservation_fee_eur'] is None
    assert r['screened_choice'] == 'wait'


def test_reservation_delay_and_negative_margin_preserve_losses():
    c = reference_case()
    c['scenarios'][0]['reserved_arrival_month'] = 60
    r = screen_reservation(c)
    assert r['scenarios'][0]['incremental_operating_pv_eur'] < 0
    assert r['screened_choice'] == 'wait'
    c = reference_case()
    c['assumptions']['monthly_contribution_eur'] = -100
    assert screen_reservation(c)['screened_choice'] == 'wait'


def test_horizon_truncates_and_approval_is_required():
    c = reference_case()
    c['assumptions']['horizon_months'] = 40
    r = screen_reservation(c)
    assert [row['month_end'] for row in r['scenarios'][0]['operating_cash']] == [40]
    c['scenarios'][0].update(site_ready_month=0, reserved_arrival_month=0)
    assert delivery_scenarios(c)[0]['reserve_cod_month'] == 15


@pytest.mark.parametrize('key,value', [('reservation_fee_eur', float('nan')),
    ('monthly_contribution_eur', float('inf')), ('exercise_premium_eur', -1),
    ('cancel_refund_fraction', 1.1), ('decision_month', True), ('horizon_months', 12),
    ('annual_discount_rate', -0.1), ('installation_months', 1.5)])
def test_invalid_assumptions(key, value):
    c = reference_case()
    c['assumptions'][key] = value
    with pytest.raises(ValueError):
        screen_reservation(c)


@pytest.mark.parametrize('key,value', [('probability', -1), ('probability', 0.6),
    ('probability', True), ('id', 'proceed_site_delayed'), ('proceed', 'yes'),
    ('wait_arrival_month', 6), ('site_ready_month', -1)])
def test_invalid_joint_states(key, value):
    c = reference_case()
    c['scenarios'][0][key] = value
    with pytest.raises(ValueError):
        screen_reservation(c)


@pytest.mark.parametrize('key,value', [('url', ''), ('publication_date', '2026-11-09'),
    ('event_date', '2026-11-04'), ('classification', 'measured'), ('locator', '')])
def test_failed_evidence_blocks_all_downstream_work(key, value):
    c = reference_case()
    c['source'][key] = value
    r = run_procurement_workflow(c)
    assert r['states'] == {'evidence': 'failed', 'controls': 'blocked', 'finance': 'blocked'}


def test_parity_and_mutating_scheduler_cannot_change_handoff():
    c = reference_case()
    before = deepcopy(c)

    class MutatingPlanner:
        def next_action(self, context):
            context['tasks'][0]['payload']['case']['assumptions']['reservation_fee_eur'] = 0
            return {'tool': 'delegate', 'arguments': {'task_id': context['ready_tasks'][0]}}

    r = run_procurement_workflow(c, MutatingPlanner())
    assert r['success'] and r['results']['finance']['report'] == screen_reservation(c)
    assert c == before
    assert [t['task_id'] for t in r['trace']] == ['evidence', 'controls', 'finance']


@pytest.mark.parametrize('action', [{'tool': 'place_order', 'arguments': {}},
    {'tool': 'contact_supplier', 'arguments': {}},
    {'tool': 'delegate', 'arguments': {'task_id': 'finance'}}])
def test_permissions_and_premature_handoff(action):
    class Forbidden:
        def next_action(self, context):
            return action
    r = run_procurement_workflow(reference_case(), Forbidden())
    assert not r['success'] and r['budget_exhausted']
    assert r['results'] == {} and len(r['trace']) == 5
    assert all(t['status'] == 'rejected' for t in r['trace'])


def test_sensitivity_preserves_conditional_mix_and_zero_weight_risk():
    c = reference_case()
    rows = cancellation_sensitivity(c)
    assert rows[1]['expected_npv_eur'] == screen_reservation(c)['reserve_expected_npv_eur']
    assert rows[-1]['expected_npv_eur'] == -600000
    assert rows[-1]['choice'] == 'wait'
    c['scenarios'][0]['probability'] = c['scenarios'][1]['probability'] = 0
    c['scenarios'][2]['probability'] = 1
    assert screen_reservation(c)['reserve_worst_loss_eur'] == 600000
    with pytest.raises(ValueError, match='positive'):
        cancellation_sensitivity(c)
