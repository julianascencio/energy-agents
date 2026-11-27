from copy import deepcopy

import pytest

from energy_agents.business.recovery import (
    completion_audit,
    edi_crosscheck,
    reference_case,
    run_workflow,
    screen_recovery,
)


def test_independent_budget_and_cash_reconciliation():
    report = screen_recovery(reference_case())
    base = report['comparisons'][0]
    epc, owner = (base['plans'][k] for k in ('replacement_epc', 'owner_prime'))
    assert epc['cost_to_complete_cad'] == 11000000
    assert owner['cost_to_complete_cad'] == 9600000
    assert epc['gross_forecast_at_completion_cad'] == 35000000
    assert owner['gross_forecast_at_completion_cad'] == 33600000
    assert owner['budget_headroom_cad'] == 1400000
    assert base['conditional_cost_reduction_cad'] == 1400000
    # CAD1m opening cash; all invoices paid before CAD1.5m completion grant arrives.
    assert [p['peak_new_funding_cad'] for p in (epc, owner)] == [10000000, 8600000]
    assert [p['terminal_new_funding_cad'] for p in (epc, owner)] == [8500000, 7100000]
    assert epc['peak_funding_shortfall_cad'] == 1200000
    assert owner['peak_funding_shortfall_cad'] == 0
    # CAD2m old invoice + 80% of CAD3m remedial package less opening cash.
    assert owner['monthly'][0]['funding_before_receipts_cad'] == 3400000
    for p in (epc, owner):
        assert sum(r['outflow_cad'] for r in p['monthly']) == p['cost_to_complete_cad']
        assert sum(r['receipt_cad'] for r in p['monthly']) == 1500000
        assert p['ignored_disputed_recoveries_cad'] == 2000000
    assert not report['procurement_authorized'] and not report['physical_readiness_verified']
    assert report['llm'] == {'executed':False,'tokens':None,'cost':None,'latency':None}


def test_sunk_costs_change_headroom_but_not_forward_decision_or_funding():
    c = reference_case()
    before = screen_recovery(c)['comparisons'][0]
    c['spent_cad'] += 1000000
    after = screen_recovery(c)['comparisons'][0]
    assert before['conditional_cost_reduction_cad'] == after['conditional_cost_reduction_cad']
    for key in before['plans']:
        a,b = before['plans'][key], after['plans'][key]
        assert a['peak_new_funding_cad'] == b['peak_new_funding_cad']
        assert a['budget_headroom_cad']-b['budget_headroom_cad'] == 1000000


def test_quote_stress_and_algebraic_crossover():
    c = reference_case()
    r = screen_recovery(c)
    assert r['comparisons'][1]['conditional_cost_reduction_cad'] == -120000
    assert r['algebraic_owner_quote_uplift_at_cost_parity'] == pytest.approx(14/76)
    c['scenarios'][0]['owner_quote_uplift'] = 14/76
    assert screen_recovery(c)['comparisons'][0]['conditional_cost_reduction_cad'] == pytest.approx(0)
    for package in c['plans'][1]['packages']:
        package['amount_cad'] = 0
    assert screen_recovery(c)['algebraic_owner_quote_uplift_at_cost_parity'] is None


def test_late_and_disputed_receipts_never_net_gross_cost_or_earlier_peak():
    c = reference_case()
    r = screen_recovery(c)
    for key in ('replacement_epc','owner_prime'):
        base = r['comparisons'][0]['plans'][key]
        late = r['comparisons'][2]['plans'][key]
        assert late['terminal_new_funding_cad'] == base['terminal_new_funding_cad']+1500000
        assert late['receipts_after_horizon_cad'] == 1500000
        assert late['peak_new_funding_cad'] == base['peak_new_funding_cad']
        assert late['gross_forecast_at_completion_cad'] == base['gross_forecast_at_completion_cad']
    c['receipts'][1]['amount_cad'] = 999999999
    changed = screen_recovery(c)['comparisons'][0]['plans']['owner_prime']
    assert changed['peak_new_funding_cad'] == 8600000
    assert changed['gross_forecast_at_completion_cad'] == 33600000
    # Even a same-month grant is received after outflows by the documented convention.
    c['receipts'][0]['lag_after_completion_months'] = 0
    assert screen_recovery(c)['comparisons'][0]['plans']['owner_prime'][
        'peak_new_funding_cad'] == 8600000


def test_zero_cost_large_opening_cash_and_no_receipts():
    c = reference_case()
    c['opening_cash_cad'] = 20000000
    c['receipts'] = []
    for plan in screen_recovery(c)['comparisons'][0]['plans'].values():
        assert plan['peak_new_funding_cad'] == 0
        assert plan['terminal_new_funding_cad'] == 0
        assert plan['monthly'][-1]['surplus_at_month_end_cad'] > 0
    c['unpaid'] = []
    for p in c['plans']:
        for package in p['packages']:
            package['amount_cad'] = 0
    r = screen_recovery(c)['comparisons'][0]
    assert r['conditional_cost_reduction_cad'] == 0
    assert r['plans']['owner_prime']['gross_forecast_at_completion_cad'] == c['spent_cad']


def test_service_shortfall_withholds_comparison_even_if_cheaper():
    r = screen_recovery(reference_case())
    stress = r['comparisons'][-1]
    assert stress['service']['available_ac_mwh'] == pytest.approx(35.91)
    assert stress['service']['sustainable_mw'] == pytest.approx(8.9775)
    assert not stress['comparison_valid']
    assert stress['conditional_cost_reduction_cad'] is None
    c = reference_case()
    c['service']['power_mw'] = 9
    assert not screen_recovery(c)['comparisons'][0]['comparison_valid']


@pytest.mark.parametrize('value',[True,float('nan'),float('inf'),-1,'1'])
def test_invalid_money(value):
    c = reference_case()
    c['unpaid'][0]['amount_cad'] = value
    with pytest.raises(ValueError):
        completion_audit(c)


@pytest.mark.parametrize('mutation',[
    lambda c: c['plans'][1]['packages'].pop(),
    lambda c: c['plans'][1]['packages'][0]['scope'].append('commissioning'),
    lambda c: c['plans'][1]['packages'][0].update(id='certified_legacy'),
    lambda c: c['plans'][0]['packages'][0]['payments'][0].update(fraction=.3),
    lambda c: c['plans'][0]['packages'][0]['payments'][0].update(month=5),
    lambda c: c['plans'][0]['packages'][0]['payments'][0].update(month=10),
    lambda c: c['unpaid'][0].update(month=True),
    lambda c: c['receipts'][1].update(status='settled'),
    lambda c: c['receipts'][0].update(lag_after_completion_months=-1),
    lambda c: c['scenarios'][1].update(id='base'),
    lambda c: c['scenarios'][1].update(owner_quote_uplift=-2),
    lambda c: c['scenarios'][1].update(receipt_delay_months=True),
    lambda c: c['service'].update(efficiency=0),
    lambda c: c['service'].update(reserve_soc=1),
    lambda c: c.update(classification='observed'),
    lambda c: c.update(evidence_gaps=[]),
    lambda c: c.update(as_of='2026-11-26'),
    lambda c: c['source']['facts'].update(project_budget_cad=34000000),
])
def test_scope_payment_evidence_and_schema_errors_block_handoff(mutation):
    c = reference_case()
    mutation(c)
    result = run_workflow(c)
    assert result['states'] == {'evidence':'failed','finance':'blocked'}


def test_handoff_integrity_and_deterministic_parity():
    c = reference_case()
    before = deepcopy(c)
    workflow = run_workflow(c)
    assert workflow['success']
    assert workflow['results']['finance']['report'] == screen_recovery(c)
    assert c == before
    audit = completion_audit(c)
    audit['unpaid_cad'] += 1
    with pytest.raises(ValueError,match='handoff'):
        screen_recovery(c,audit)
    audit = completion_audit(c)
    c['opening_cash_cad'] += 1
    with pytest.raises(ValueError,match='handoff'):
        screen_recovery(c,audit)


@pytest.mark.parametrize('action',[
    {'tool':'purchase','arguments':{}}, {'tool':'submit_claim','arguments':{}},
    {'tool':'physical_controls','arguments':{}}, {'tool':'contact_supplier','arguments':{}},
    {'tool':'delegate','arguments':{'task_id':'finance'}},
])
def test_permissions_and_premature_finance(action):
    class Planner:
        def next_action(self, context):
            return action
    result = run_workflow(reference_case(),Planner())
    assert not result['success']
    assert all(t['status'] == 'rejected' for t in result['trace'])


def test_edi_execution_and_hash_guard(monkeypatch):
    pytest.importorskip('energy_methods.bess_service_envelope')
    r = edi_crosscheck(reference_case())
    assert r['executed'] and r['parity'] and r['scenarios_checked'] == 4
    import energy_agents.business.recovery as module
    original = module.data_file

    def changed(name):
        data = original(name)
        if name == 'edi_capabilities':
            data['source_sha256'] = '0'*64
        return data

    monkeypatch.setattr(module,'data_file',changed)
    with pytest.raises(ValueError,match='differs'):
        edi_crosscheck(reference_case())
