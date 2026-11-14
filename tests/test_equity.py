from copy import deepcopy

import pytest

from energy_agents.business.equity import edi_context, reference_case, run_workflow, screen_equity


def test_independent_two_year_waterfall_and_arrears():
    c = reference_case()
    c['assumptions'].update(equity_requirement_usd=1000, preferred_capital_usd=400,
        transaction_fee_usd=10, preferred_annual_rate=.1, discount_rate=0,
        annual_cash_usd=[20,100], terminal_equity_proceeds_usd=500)
    r = screen_equity(c)
    assert r['annual'][0]['coupon_arrears_usd'] == 20
    assert r['annual'][1]['coupon_paid_usd'] == 60
    assert r['annual'][1]['redemption_usd'] == 400
    assert r['annual'][1]['common_distribution_usd'] == 140
    assert r['common_only_sponsor_npv_usd'] == -380
    assert r['preferred_funded_sponsor_npv_usd'] == -470
    assert r['preferred_investor_npv_usd'] == 80
    assert r['sponsor_incremental_npv_usd'] == -90


def test_terminal_loss_not_fabricated_future_payment():
    c = reference_case()
    c['assumptions'].update(preferred_capital_usd=400, transaction_fee_usd=0,
        preferred_annual_rate=.1, annual_cash_usd=[0,0], terminal_equity_proceeds_usd=50)
    r = screen_equity(c)
    assert r['terminal_coupon_shortfall_usd'] == 30
    assert r['terminal_capital_shortfall_usd'] == 400
    assert all(row['common_distribution_usd'] == 0 for row in r['annual'])


@pytest.mark.parametrize('capital,rate,exit_value', [(0,0,0),(1e6,0,0),(4e6,.08,12e6),
    (4e6,1,0),(1e7,.2,1e9)])
def test_conservation_value_transfer_and_zero_capital(capital,rate,exit_value):
    c = reference_case()
    c['assumptions'].update(preferred_capital_usd=capital, transaction_fee_usd=0,
        preferred_annual_rate=rate, terminal_equity_proceeds_usd=exit_value)
    r = screen_equity(c)
    for row in r['annual']:
        assert row['available_usd'] == pytest.approx(sum(row[k] for k in
            ('coupon_paid_usd','redemption_usd','common_distribution_usd')))
        assert row['coupon_arrears_usd'] >= 0
    assert r['sponsor_incremental_npv_usd'] == pytest.approx(-r['preferred_investor_npv_usd'])
    if not capital:
        assert r['sponsor_incremental_npv_usd'] == 0


def test_coupon_does_not_compound_and_never_redeems_early():
    c = reference_case()
    c['assumptions'].update(annual_cash_usd=[0,0,1e7], terminal_equity_proceeds_usd=0)
    r = screen_equity(c)
    assert r['annual'][-1]['coupon_paid_usd'] == 960000
    assert [x['redemption_usd'] for x in r['annual']] == [0,0,4000000]


@pytest.mark.parametrize('key,value', [('preferred_capital_usd',True),
    ('preferred_capital_usd',10000001),('transaction_fee_usd',4000001),
    ('preferred_annual_rate',-1),('discount_rate',float('nan')),
    ('terminal_equity_proceeds_usd',float('inf')),('annual_cash_usd',[]),
    ('annual_cash_usd',[True]),('annual_cash_usd',[-1]),('annual_cash_usd',[0]*51)])
def test_reject_invalid_inputs(key,value):
    c = reference_case()
    c['assumptions'][key] = value
    with pytest.raises(ValueError):
        screen_equity(c)


def test_workflow_parity_isolation_evidence_and_fee_identity():
    c = reference_case()
    before = deepcopy(c)
    run = run_workflow(c)
    r = screen_equity(c)
    assert run['success'] and run['results']['finance']['report'] == r
    assert c == before
    assert r['sponsor_incremental_npv_usd'] + r['preferred_investor_npv_usd'] == pytest.approx(-100000)
    assert r['evidence_gaps'] == c['evidence_gaps']
    assert r['investment_authorized'] is False and edi_context()['execution'] is False
    c['source']['terms_disclosed'] = True
    assert run_workflow(c)['states'] == {'evidence':'failed','finance':'blocked'}
    c = reference_case()
    c['source']['url'] = 'file:///tmp/terms'
    assert run_workflow(c)['states']['finance'] == 'blocked'


@pytest.mark.parametrize('action',[{'tool':'transfer_funds','arguments':{}},
    {'tool':'delegate','arguments':{'task_id':'finance'}}])
def test_permissions_and_handoff_order(action):
    class Planner:
        def next_action(self,context):
            return action
    run = run_workflow(reference_case(),Planner())
    assert not run['success']
    assert all(t['status']=='rejected' for t in run['trace'])
