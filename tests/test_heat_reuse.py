from copy import deepcopy

import pytest

from energy_agents.business.heat_reuse import (
    edi_crosscheck,
    heat_balance,
    reference_case,
    run_workflow,
    screen_heat_reuse,
)


def two_season_case():
    c = reference_case()
    c['assumptions'].update(it_capacity_mw=1, recoverable_it_heat_fraction=1,
        heat_pump_output_capacity_mw=10, network_delivery_efficiency=.8,
        capex_chf=1000, fixed_opex_chf_year=100, electricity_chf_mwh=2,
        source_heat_fee_chf_mwh=1, variable_opex_chf_mwh_delivered=1,
        baseline_heat_cost_chf_mwh_delivered=10, years=2, discount_rate=0)
    c['periods'] = [dict(id='winter', hours=4380, it_load_fraction=1, heating_cop=2,
                         demand_mw=3),
                    dict(id='summer', hours=4380, it_load_fraction=1, heating_cop=2,
                         demand_mw=0)]
    return c


def test_independent_energy_and_cash_ledger():
    r = screen_heat_reuse(two_season_case())
    t = r['annual_energy']
    assert t['source_available_mwh'] == 8760
    assert t['delivered_mwh'] == 7008
    assert t['pump_electricity_mwh'] == 4380
    assert t['recovered_source_mwh'] == 4380
    assert t['network_loss_mwh'] == 1752
    assert t['bypassed_source_mwh'] == 4380
    assert r['annual_matching_ceiling_mwh'] == 13140
    assert r['annual_avoided_supply_cost_chf'] == 70080
    # 70080 - 8760 electricity - 4380 source fee - 7008 variable - 100 fixed.
    assert r['annual_net_savings_chf'] == 49832
    assert r['incremental_npv_chf'] == 98664
    assert r['break_even_avoided_cost_chf_mwh'] == pytest.approx(20748/7008)
    assert r['baseline_annual_supply_cost_chf'] == 131400
    assert r['intervention_annual_supply_cost_chf'] == 81568


@pytest.mark.parametrize('key,value', [('it_capacity_mw',0),
    ('recoverable_it_heat_fraction',0),('heat_pump_output_capacity_mw',0)])
def test_no_heat_still_incurs_committed_costs(key,value):
    c = two_season_case()
    c['assumptions'][key] = value
    r = screen_heat_reuse(c)
    assert r['annual_energy']['delivered_mwh'] == 0
    assert r['incremental_npv_chf'] == -1200
    assert r['break_even_avoided_cost_chf_mwh'] is None


def test_capacity_demand_conservation_and_break_even():
    c = reference_case()
    c['assumptions']['heat_pump_output_capacity_mw'] = .5
    r = screen_heat_reuse(c)
    for row,p in zip(r['periods'], c['periods'], strict=True):
        produced = row['recovered_source_mwh']+row['pump_electricity_mwh']
        assert produced == pytest.approx(row['delivered_mwh']+row['network_loss_mwh'])
        assert produced <= .5*p['hours']+1e-8
        assert row['source_available_mwh'] == pytest.approx(
            row['recovered_source_mwh']+row['bypassed_source_mwh'])
        assert row['delivered_mwh']+row['remaining_supply_mwh'] == pytest.approx(row['demand_mwh'])
    c['assumptions']['baseline_heat_cost_chf_mwh_delivered'] = r['break_even_avoided_cost_chf_mwh']
    assert screen_heat_reuse(c)['incremental_npv_chf'] == pytest.approx(0,abs=1e-7)


def test_announcement_targets_do_not_determine_model_output():
    c = reference_case()
    before = screen_heat_reuse(c)
    c['source']['reported_project_targets']['heat_with_heat_pumps_gwh_year'] = 999
    after = screen_heat_reuse(c)
    assert before['annual_energy'] == after['annual_energy']
    assert before['incremental_npv_chf'] == after['incremental_npv_chf']
    assert before['input_sha256'] != after['input_sha256']


@pytest.mark.parametrize('section,key,value',[
    ('assumptions','it_capacity_mw',True),('assumptions','discount_rate',float('nan')),
    ('assumptions','years',1.5),('assumptions','network_delivery_efficiency',0),
    ('assumptions','source_heat_fee_chf_mwh',-1),('assumptions','classification','observed'),
    ('period','hours',0),('period','heating_cop',1),('period','it_load_fraction',1.1),
    ('period','demand_mw',float('inf'))])
def test_invalid_physical_and_financial_inputs(section,key,value):
    c = reference_case()
    (c['periods'][0] if section == 'period' else c[section])[key] = value
    with pytest.raises(ValueError):
        screen_heat_reuse(c)


def test_period_alignment_and_zero_demand():
    c = reference_case()
    c['periods'][0]['hours'] += 1
    with pytest.raises(ValueError, match='8760'):
        heat_balance(c)
    c = reference_case()
    c['periods'][0]['id'] = c['periods'][1]['id']
    with pytest.raises(ValueError, match='Unique'):
        heat_balance(c)
    c = reference_case()
    for p in c['periods']:
        p['demand_mw'] = 0
    assert screen_heat_reuse(c)['annual_energy']['pump_electricity_mwh'] == 0


def test_evidence_gates_and_handoff_integrity():
    c = reference_case()
    before = deepcopy(c)
    run = run_workflow(c)
    assert run['success'] and run['results']['finance']['report'] == screen_heat_reuse(c)
    assert c == before
    balance = heat_balance(c)
    balance['periods'][0]['delivered_mwh'] += 1
    with pytest.raises(ValueError,match='handoff'):
        screen_heat_reuse(c,balance)
    balance = heat_balance(c)
    c['assumptions']['capex_chf'] += 1
    with pytest.raises(ValueError,match='handoff'):
        screen_heat_reuse(c,balance)
    for bad_source in [dict(url='file:///tmp/news'),dict(publication_date='2026-11-15')]:
        c = reference_case()
        c['source'].update(bad_source)
        assert run_workflow(c)['states'] == {'evidence':'failed','thermal':'blocked','finance':'blocked'}
    c = reference_case()
    c['evidence_gaps'] = []
    assert run_workflow(c)['states']['finance'] == 'blocked'


@pytest.mark.parametrize('action',[{'tool':'set_heat_pump','arguments':{}},
    {'tool':'execute_contract','arguments':{}},
    {'tool':'delegate','arguments':{'task_id':'finance'}}])
def test_permissions_and_premature_handoff(action):
    class Planner:
        def next_action(self,context):
            return action
    run = run_workflow(reference_case(),Planner())
    assert not run['success']
    assert all(row['status']=='rejected' for row in run['trace'])


def test_optional_edi_adapter_and_source_guard(monkeypatch):
    pytest.importorskip('energy_methods.hybrid_dispatch')
    r = edi_crosscheck(reference_case())
    assert r['executed'] and r['parity']
    assert r['delivered_mwh'] == pytest.approx(13024.32)
    import energy_agents.business.heat_reuse as module
    original = module.data_file
    def changed(name):
        value = original(name)
        value['source_sha256'] = '0'*64
        return value
    monkeypatch.setattr(module,'data_file',changed)
    with pytest.raises(ValueError,match='differs'):
        edi_crosscheck(reference_case())
