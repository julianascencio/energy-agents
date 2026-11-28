from copy import deepcopy

import pytest

from energy_agents.business.sharing import (
    reference_case,
    run_workflow,
    screen_sharing,
    sharing_audit,
)


def test_hand_calculated_two_year_case_and_conservation():
    c = reference_case()
    c['annual'] = [dict(year=y,gross_revenue_aud=1000,distributable_cash_aud=200)
                   for y in (1,2)]
    c.update(initial_equity_aud=1000,terminal_equity_proceeds_aud=400,discount_rate=0)
    c['equity'].update(fraction=.1,recipient_contribution_aud=40,
                       setup_cost_aud=10,annual_admin_aud=5)
    c['revenue_share'].update(fraction=.02,recipient_contribution_aud=0,
                             setup_cost_aud=20,annual_admin_aud=3,start_year=1,end_year=2)
    r = screen_sharing(c)
    e, s = (r['plans'][k] for k in ('equity','revenue_share'))
    assert e['recipient_npv_aud'] == 40  # 20+20+40-40
    assert s['recipient_npv_aud'] == 40
    assert e['sponsor_incremental_cost_pv_aud'] == 60
    assert s['sponsor_incremental_cost_pv_aud'] == 66
    assert r['revenue_fraction_at_recipient_npv_parity'] == .02
    assert r['no_sharing_sponsor_npv_aud'] == -200
    assert e['sponsor_npv_aud'] == -260
    for plan in (e,s):
        for y, row in enumerate(plan['annual'],1):
            assert row['recipient_total_aud']+row['admin_aud']+row['sponsor_net_cash_aud'] == (
                200+(400 if y == 2 else 0))


def test_discount_and_terminal_timing_independent_formula():
    c = reference_case()
    r = screen_sharing(c)
    annuity = (1-1.08**-20)/.08
    e = 400000*annuity+2000000/1.08**20
    assert r['plans']['equity']['recipient_npv_aud'] == pytest.approx(e)
    assert r['plans']['equity']['sponsor_incremental_cost_pv_aud'] == pytest.approx(
        e+100000+20000*annuity)
    assert r['revenue_fraction_at_recipient_npv_parity'] == pytest.approx(e/(30000000*annuity))
    assert r['tender_qualification'] == 'not_determined'
    assert not r['agreement_authorized'] and not r['community_support_verified']


def test_shorter_duration_and_contributions_change_parity():
    c = reference_case()
    original = screen_sharing(c)['revenue_fraction_at_recipient_npv_parity']
    c['revenue_share']['end_year'] = 10
    assert screen_sharing(c)['revenue_fraction_at_recipient_npv_parity'] > original
    c['equity']['recipient_contribution_aud'] = 2500000
    funded = screen_sharing(c)['revenue_fraction_at_recipient_npv_parity']
    c['revenue_share']['recipient_contribution_aud'] = 1000000
    assert screen_sharing(c)['revenue_fraction_at_recipient_npv_parity'] > funded


def test_zero_revenue_and_negative_target_do_not_invent_positive_parity():
    c = reference_case()
    for row in c['annual']:
        row.update(gross_revenue_aud=0,distributable_cash_aud=0)
    assert screen_sharing(c)['revenue_fraction_at_recipient_npv_parity'] is None
    c['annual'][0]['gross_revenue_aud'] = 1
    r = screen_sharing(c)
    assert r['revenue_fraction_at_recipient_npv_parity'] > 1
    assert not r['parity_fraction_within_zero_one']
    c['equity']['recipient_contribution_aud'] = 2500000
    assert screen_sharing(c)['revenue_fraction_at_recipient_npv_parity'] is None


def test_shortfall_not_hidden_by_terminal_proceeds_or_payment_cap():
    c = reference_case()
    c['annual'][-1]['distributable_cash_aud'] = 100000
    r = screen_sharing(c)['plans']['revenue_share']['annual'][-1]
    assert r['recipient_total_aud'] == 450000
    assert r['operating_funding_gap_aud'] == 400000
    assert r['sponsor_net_cash_aud'] == 39600000


@pytest.mark.parametrize('value',[True,float('inf'),float('nan'),-1,'0.05'])
def test_invalid_fraction(value):
    c = reference_case()
    c['equity']['fraction'] = value
    with pytest.raises(ValueError):
        sharing_audit(c)


@pytest.mark.parametrize('mutation',[
    lambda c: c.update(classification='observed'),
    lambda c: c.update(currency='USD'),
    lambda c: c.update(as_of='2026-11-27'),
    lambda c: c.update(evidence_gaps=[]),
    lambda c: c.update(annual=[]),
    lambda c: c['source']['facts'].update(economic_interest_threshold_fraction=.04),
    lambda c: c['annual'][0].update(year=True),
    lambda c: c['annual'][1].update(year=1),
    lambda c: c['annual'][0].update(distributable_cash_aud=31000000),
    lambda c: c['equity'].update(fraction=0),
    lambda c: c['equity'].update(recipient_contribution_aud=3000000),
    lambda c: c['revenue_share'].update(recipient_contribution_aud=51000000),
    lambda c: c['revenue_share'].update(start_year=21),
    lambda c: c['revenue_share'].update(start_year=2,end_year=1),
    lambda c: c['revenue_share'].update(start_year=True),
])
def test_invalid_evidence_or_schema_blocks_finance(mutation):
    c = reference_case()
    mutation(c)
    assert run_workflow(c)['states'] == {'evidence':'failed','finance':'blocked'}


def test_input_immutability_and_handoff_integrity():
    c = reference_case()
    before = deepcopy(c)
    result = run_workflow(c)
    assert result['success'] and result['results']['finance']['report'] == screen_sharing(c)
    assert c == before
    audit = sharing_audit(c)
    audit['eligible_revenue_pv_aud'] += 1
    with pytest.raises(ValueError,match='handoff'):
        screen_sharing(c,audit)
    audit = sharing_audit(c)
    c['equity']['annual_admin_aud'] += 1
    with pytest.raises(ValueError,match='handoff'):
        screen_sharing(c,audit)


@pytest.mark.parametrize('action',[
    {'tool':'sign_agreement','arguments':{}}, {'tool':'submit_bid','arguments':{}},
    {'tool':'contact_community','arguments':{}}, {'tool':'trade','arguments':{}},
    {'tool':'delegate','arguments':{'task_id':'finance'}},
    {'tool':'delegate','arguments':{'task_id':'unknown'}},
])
def test_permissions_and_handoff_order(action):
    class Planner:
        def next_action(self, context):
            return action
    result = run_workflow(reference_case(),Planner())
    assert not result['success']
    assert all(t['status'] == 'rejected' for t in result['trace'])
