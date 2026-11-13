from copy import deepcopy

import pytest

from energy_agents.business.bid import edi_context, reference_case, run_workflow, screen_bid


def test_hand_calculation():
    c = reference_case()
    c['assumptions']['annual_discount_rate'] = 0
    r = screen_bid(c)
    assert r['strategies']['upfront']['expected_net_value_usd'] == pytest.approx(60000)
    assert r['strategies']['staged']['expected_net_value_usd'] == pytest.approx(100000)
    assert r['staged_incremental_expected_value_usd'] == pytest.approx(40000)
    assert r['strategies']['staged']['worst_case_loss_usd'] == 250000
    assert r['strategies']['staged']['break_even_project_npv_usd'] == pytest.approx(170000/.135)


def test_zero_probability_and_no_bid():
    c = reference_case()
    c['assumptions']['qualification_probability'] = 0
    r = screen_bid(c)
    assert r['scenario_preferred_strategy'] == 'no_bid'
    assert r['strategies']['staged']['worst_case_loss_usd'] == 50000
    assert r['strategies']['staged']['expected_spend_usd'] == 50000
    assert r['strategies']['staged']['break_even_project_npv_usd'] is None


def test_certain_award_and_timing_competitiveness_penalty():
    c = reference_case()
    c['assumptions'].update(qualification_probability=1, award_probability_given_qualification=1,
                            staging_award_probability_haircut=0, annual_discount_rate=0)
    r = screen_bid(c)
    assert r['strategies']['staged']['worst_case_loss_usd'] == 0
    assert r['staged_incremental_expected_value_usd'] == -10000
    c['assumptions']['staging_award_probability_haircut'] = 1
    r = screen_bid(c)
    assert r['strategies']['staged']['worst_case_loss_usd'] == 250000
    assert r['strategies']['staged']['expected_net_value_usd'] == -250000


@pytest.mark.parametrize('key,value', [('qualification_probability',1.01),
    ('award_probability_given_qualification',-.1), ('annual_discount_rate',float('nan')),
    ('staging_award_probability_haircut',True), ('full_bid_cost_usd',-1),
    ('stage_delay_months',25), ('award_project_npv_usd',float('inf'))])
def test_input_bounds(key,value):
    c = reference_case()
    c['assumptions'][key] = value
    with pytest.raises(ValueError):
        screen_bid(c)


def test_evidence_parity_and_input_isolation():
    c = reference_case()
    before = deepcopy(c)
    r = run_workflow(c)
    assert r['success'] and r['results']['finance']['report'] == screen_bid(c)
    assert c == before
    assert r['results']['finance']['report']['evidence_gaps'] == c['evidence_gaps']
    assert not r['results']['finance']['report']['spending_authorized']
    c['source']['url'] = 'file:///etc/passwd'
    assert run_workflow(c)['states'] == {'evidence':'failed','finance':'blocked'}
    assert edi_context()['execution'] is False


@pytest.mark.parametrize('action', [{'tool':'submit_bid','arguments':{}},
    {'tool':'delegate','arguments':{'task_id':'finance'}}])
def test_reject_external_action_and_premature_handoff(action):
    class Planner:
        def next_action(self, context):
            return action
    r = run_workflow(reference_case(),Planner())
    assert not r['success']
    assert all(t['status'] == 'rejected' for t in r['trace'])


def test_monetary_value_sensitivity_and_break_even():
    c = reference_case()
    r = screen_bid(c)
    c['assumptions']['award_project_npv_usd'] = r['strategies']['staged']['break_even_project_npv_usd']
    assert screen_bid(c)['strategies']['staged']['expected_net_value_usd'] == pytest.approx(0)
    c['assumptions']['award_project_npv_usd'] = 1e8
    assert screen_bid(c)['staged_incremental_expected_value_usd'] < 0


@pytest.mark.parametrize('p,q,h', [(0,0,0), (1,1,0), (.3,.4,.2), (.9,0,1)])
def test_explicit_branch_enumeration(p,q,h):
    c = reference_case()
    c['assumptions'].update(qualification_probability=p, award_probability_given_qualification=q,
                            staging_award_probability_haircut=h)
    a = c['assumptions']
    df = 1.08 ** (-.25)
    for strategy, win, fail_cost, qualified_cost in (
        ('upfront',q,240000,240000),
        ('staged',q*(1-h),50000,50000+200000*df),
    ):
        branches = [(1-p,-fail_cost), (p*(1-win),-qualified_cost),
                    (p*win,a['award_project_npv_usd']-qualified_cost)]
        row = screen_bid(c)['strategies'][strategy]
        assert row['expected_net_value_usd'] == pytest.approx(sum(w*v for w,v in branches))
        assert row['worst_case_loss_usd'] == max(0,-min(v for w,v in branches if w>0))
