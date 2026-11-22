from copy import deepcopy

import pytest

from energy_agents.business.augmentation import (
    capacity_audit,
    edi_crosscheck,
    reference_case,
    run_workflow,
    screen_augmentation,
)


def test_independent_two_interval_arithmetic_and_cash_timing():
    c = reference_case()
    c.update(target_mw=1, inverter_mw=2, initial_soc=1, reserve_soc=0,
             discharge_efficiency=1, design_annual_retention=1,
             installed_usd_per_mwh_dc=10, opex_usd_per_mwh_dc_year=2,
             augmentation_event_usd=100, discount_rate=0, scenarios=[])
    # At least one explicit stress is required, even in this zero-fade test.
    c['scenarios'] = [{'id':'unchanged', 'annual_retention':1, 'future_price_multiplier':1}]
    r = screen_augmentation(c)
    a, b = r['comparisons'][0]['plans']
    assert a['additions'] == b['additions']
    assert a['additions'][0]['nameplate_mwh_dc'] == 4
    assert a['capex_pv_usd'] == 40
    assert a['opex_pv_usd'] == 4*2*15
    assert a['total_cost_pv_usd'] == 160
    assert r['comparisons'][0]['cost_reduction_pv_usd'] == 0
    assert r['break_even_future_equipment_price_multiplier'] is None


def test_hand_calculated_fixed_design_and_present_cost():
    c = reference_case()
    r = screen_augmentation(c)
    upfront, staged = r['comparisons'][0]['plans']
    # Separate calculations: ceil(80 / (.9 * .95) / .98**15) = 127.
    assert [a['nameplate_mwh_dc'] for a in upfront['additions']] == [127]
    assert [(a['added_at_year'], a['nameplate_mwh_dc']) for a in staged['additions']] == [
        (0, 104), (5, 10), (10, 10)]
    expected_upfront = 127*180000 + sum(127*1500/1.08**y for y in range(1,16))
    expected_staged = 104*180000 + sum((10*180000+250000)/1.08**t for t in (5,10))
    expected_staged += sum((104 + (10 if y>5 else 0) + (10 if y>10 else 0))*1500/1.08**y
                           for y in range(1,16))
    assert upfront['total_cost_pv_usd'] == pytest.approx(expected_upfront)
    assert staged['total_cost_pv_usd'] == pytest.approx(expected_staged)
    assert r['comparisons'][0]['cost_reduction_pv_usd'] == pytest.approx(
        expected_upfront-expected_staged)
    # Year five is before the next addition; year six includes the new cohort at age one.
    fifth, sixth = staged['years'][4:6]
    assert fifth['remaining_capacity_mwh_dc'] == pytest.approx(104*.98**5)
    assert sixth['remaining_capacity_mwh_dc'] == pytest.approx(104*.98**6 + 10*.98)
    assert fifth['installed_nameplate_mwh_dc'] == 104
    assert sixth['installed_nameplate_mwh_dc'] == 114
    assert all(y['meets_energy_power_screen'] for y in staged['years'])


def test_faster_fade_holds_fixed_cohorts_and_withholds_savings():
    r = screen_augmentation(reference_case())
    baseline, stress = r['comparisons'][0], r['comparisons'][-1]
    assert not stress['comparison_valid'] and stress['cost_reduction_pv_usd'] is None
    for designed, tested in zip(baseline['plans'],stress['plans'],strict=True):
        assert designed['additions'] == tested['additions']
        assert tested['first_failing_year'] is not None
        assert tested['minimum_sustainable_mw'] < 20


def test_price_crossover_and_cost_components():
    c = reference_case()
    r = screen_augmentation(c)
    multiplier = r['break_even_future_equipment_price_multiplier']
    c['scenarios'][0]['future_price_multiplier'] = multiplier
    changed = screen_augmentation(c)
    assert changed['comparisons'][1]['cost_reduction_pv_usd'] == pytest.approx(0,abs=1e-7)
    assert r['comparisons'][2]['cost_reduction_pv_usd'] < 0
    c.update(installed_usd_per_mwh_dc=0, opex_usd_per_mwh_dc_year=0,
             augmentation_event_usd=0)
    assert screen_augmentation(c)['comparisons'][0]['cost_reduction_pv_usd'] == 0
    assert screen_augmentation(c)['break_even_future_equipment_price_multiplier'] is None


@pytest.mark.parametrize('key,value', [('site_limit_mwh_dc',110), ('inverter_mw',19)])
def test_site_and_inverter_constraints_are_not_fixed_by_energy(key,value):
    c = reference_case()
    c[key] = value
    result = screen_augmentation(c)
    assert not result['comparisons'][0]['comparison_valid']
    assert result['comparisons'][0]['cost_reduction_pv_usd'] is None
    assert result['break_even_future_equipment_price_multiplier'] is None


@pytest.mark.parametrize('value', [True, float('nan'), float('inf'), -1, '1'])
def test_bad_numeric_inputs(value):
    c = reference_case()
    for key in ('target_mw', 'discharge_efficiency', 'pack_mwh_dc', 'augmentation_event_usd'):
        invalid = deepcopy(c)
        invalid[key] = value
        with pytest.raises(ValueError):
            capacity_audit(invalid)


@pytest.mark.parametrize('years', [[0,5,5], [1,5], [0,15], [0,10,5], [False,5], []])
def test_invalid_addition_times(years):
    c = reference_case()
    c['augmentation_years'] = years
    with pytest.raises(ValueError):
        capacity_audit(c)


def test_evidence_scope_and_soc_rejections():
    for key,value in [('classification','observed'), ('currency','EUR'),
                      ('years',True), ('years',14), ('service_hours',True),
                      ('service_hours',5), ('evidence_gaps',[]),
                      ('as_of','2026-11-18'), ('reserve_soc',1),
                      ('design_annual_retention',1.01)]:
        c = reference_case()
        c[key] = value
        assert run_workflow(c)['states'] == {'evidence':'failed','finance':'blocked'}
    c = reference_case()
    c['source']['facts']['storage_duration_hours'] = 2
    with pytest.raises(ValueError,match='Source'):
        capacity_audit(c)
    c = reference_case()
    c['scenarios'][0]['id'] = 'design'
    with pytest.raises(ValueError):
        capacity_audit(c)


def test_handoff_integrity_scripted_parity_and_input_isolation():
    c = reference_case()
    before = deepcopy(c)
    run = run_workflow(c)
    assert run['success']
    assert run['results']['finance']['report'] == screen_augmentation(c)
    assert c == before
    audit = capacity_audit(c)
    audit['plans'][0]['cohorts'][0]['nameplate_mwh_dc'] += 1
    with pytest.raises(ValueError,match='handoff'):
        screen_augmentation(c,audit)
    audit = capacity_audit(c)
    c['augmentation_event_usd'] += 1
    with pytest.raises(ValueError,match='handoff'):
        screen_augmentation(c,audit)


@pytest.mark.parametrize('action', [
    {'tool':'submit_bid','arguments':{}}, {'tool':'purchase_battery','arguments':{}},
    {'tool':'physical_controls','arguments':{}},
    {'tool':'delegate','arguments':{'task_id':'finance'}}])
def test_forbidden_actions_and_premature_handoffs(action):
    class Planner:
        def next_action(self,context):
            return action
    result = run_workflow(reference_case(),Planner())
    assert not result['success']
    assert all(t['status']=='rejected' for t in result['trace'])


def test_optional_edi_parity_and_hash_rejection(monkeypatch):
    pytest.importorskip('energy_methods.bess_service_envelope')
    r = edi_crosscheck(reference_case())
    assert r['executed'] and r['parity'] and r['rows_checked'] == 120
    import energy_agents.business.augmentation as module
    original = module.data_file

    def changed(name):
        data = original(name)
        if name == 'edi_capabilities':
            data['source_sha256'] = '0'*64
        return data

    monkeypatch.setattr(module,'data_file',changed)
    with pytest.raises(ValueError,match='differs'):
        edi_crosscheck(reference_case())
