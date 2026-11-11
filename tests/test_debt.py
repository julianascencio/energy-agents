from copy import deepcopy

import pytest

from energy_agents.business.debt import edi_context, reference_case, run_workflow, screen_debt


def test_two_year_zero_rate_hand_calculation():
    c = reference_case()
    c['assumptions'].update(capacity_mw=1, value_gbp_mwh=1, annual_opex_gbp=80,
                            years=2, real_interest_rate=0, minimum_dscr=2,
                            proposed_debt_gbp=1000, capacity_factors={'test': .5})
    r = screen_debt(c)
    assert r['annual_debt_service_gbp'] == 500
    assert r['scenarios']['test']['annual_cfads_proxy_gbp'] == 4300
    assert r['scenarios']['test']['dscr'] == 8.6
    assert r['scenarios']['test']['supported_debt_gbp'] == 4300
    assert r['break_even_capacity_factor'] == pytest.approx(1080/8760)


def test_downside_and_facility_separation():
    c = reference_case()
    r = screen_debt(c)
    assert r['scenarios']['base']['clears_screen']
    assert not r['scenarios']['downside']['clears_screen']
    assert r['actual_project_leverage'] is None
    c['source']['cash_facilities_gbp'] *= 2
    assert screen_debt(c)['scenarios'] == r['scenarios']
    c['assumptions']['real_interest_rate'] += .01
    assert screen_debt(c)['scenarios']['base']['supported_debt_gbp'] < r['scenarios']['base']['supported_debt_gbp']


def test_negative_cash_zero_price_and_break_even():
    c = reference_case()
    c['assumptions']['value_gbp_mwh'] = 0
    r = screen_debt(c)
    assert r['break_even_capacity_factor'] is None
    assert not r['feasible_capacity_factor_exists']
    assert r['scenarios']['base']['supported_debt_gbp'] == 0
    assert r['scenarios']['base']['dscr'] < 0
    c = reference_case()
    cf = screen_debt(c)['break_even_capacity_factor']
    c['assumptions']['capacity_factors'] = {'threshold': cf}
    assert screen_debt(c)['scenarios']['threshold']['dscr'] == pytest.approx(1.3)


@pytest.mark.parametrize('key,value', [('years', True), ('years', 41),
    ('real_interest_rate', float('nan')), ('real_interest_rate', -1),
    ('proposed_debt_gbp', 0), ('capacity_mw', True), ('minimum_dscr', .9),
    ('capacity_factors', {'bad': 1.1}), ('capacity_factors', {})])
def test_reject_bad_input(key, value):
    c = reference_case()
    c['assumptions'][key] = value
    with pytest.raises(ValueError):
        screen_debt(c)


def test_parity_and_failed_evidence_blocks_handoff():
    c = reference_case()
    before = deepcopy(c)
    r = run_workflow(c)
    assert r['success'] and r['results']['finance']['report'] == screen_debt(c)
    assert c == before
    c['classification'] = 'observed'
    assert run_workflow(c)['states'] == {'evidence': 'failed', 'finance': 'blocked'}
    assert edi_context()['execution'] is False


@pytest.mark.parametrize('action', [{'tool':'trade','arguments':{}},
    {'tool':'delegate','arguments':{'task_id':'finance'}}])
def test_permissions_and_handoff(action):
    class BadPlanner:
        def next_action(self, context):
            return action
    r = run_workflow(reference_case(), BadPlanner())
    assert not r['success']
    assert all(t['status'] == 'rejected' for t in r['trace'])
