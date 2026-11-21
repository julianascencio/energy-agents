from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
from importlib.resources import files

import pytest

from energy_agents.business.correlation import (
    correlation_audit,
    correlation_rate,
    edi_crosscheck,
    month_hours,
    reference_case,
    run_workflow,
    screen_correlation,
)


def test_independent_monthly_ledger_and_break_even():
    r = screen_correlation(reference_case())
    a, b = r['scenarios']
    assert r['hours'] == 28*24
    assert r['demand_mwh'] == 28*24*20
    assert a['matched_energy_fraction'] == .8
    # Six hours/day have 75% deviation: average 18.75%, not 20% energy deficit.
    assert a['mean_hourly_deviation_percent'] == 18.75
    assert a['rate_eur_mwh'] == 8
    assert a['modelled_compensation_eur'] == 107520
    assert b['mean_hourly_deviation_percent'] == b['rate_eur_mwh'] == 0
    assert r['topup_mwh'] == 28*6*12 == 2016
    assert b['topup_premium_eur'] == 80640
    assert b['relevant_cost_eur'] == 85640
    assert r['net_cost_reduction_eur'] == 21880
    assert r['break_even_topup_eur_mwh'] == pytest.approx(102520/2016)
    assert not r['purchase_authorized'] and not r['compliance_certified']


@pytest.mark.parametrize(('value', 'rate'), [
    ('0', 0), ('0.000000000001', 2), ('.049999999999', 2), ('.05', 5),
    ('.099999999999', 5), ('.10', 8), ('.199999999999', 8), ('.20', 11),
    ('.499999999999', 11), ('.50', 16), ('1', 16)])
def test_tariff_boundaries(value, rate):
    assert correlation_rate(Fraction(value)) == rate


def test_unweighted_mean_and_no_cross_hour_netting():
    case = reference_case()
    for i, h in enumerate(case['hours']):
        h.update(demand_mwh=1 if i % 2 else 100, backing_mwh=0 if i % 2 else 200,
                 topup_mwh=0)
    r = screen_correlation(case)
    assert r['scenarios'][0]['mean_hourly_deviation_percent'] == 50
    assert r['scenarios'][0]['rate_eur_mwh'] == 16
    assert r['scenarios'][0]['matched_energy_fraction'] == pytest.approx(100/101)
    assert r['break_even_topup_eur_mwh'] is None


def test_exact_band_through_audit_and_sensitivity():
    case = reference_case()
    for h in case['hours']:
        h.update(demand_mwh=10, backing_mwh=7.6, topup_mwh=0)
    assert screen_correlation(case)['scenarios'][0]['rate_eur_mwh'] == 5
    case = reference_case()
    case['topup_eur_mwh'] = 60
    assert screen_correlation(case)['net_cost_reduction_eur'] == -18440
    for h in case['hours']:
        h['topup_mwh'] /= 2
    assert screen_correlation(case)['scenarios'][1]['rate_eur_mwh'] == 5


@pytest.mark.parametrize(('month', 'count'), [('2027-03',743), ('2027-10',745),
                                           ('2028-02',696)])
def test_dst_and_leap_calendar_month(month, count):
    hours = month_hours(month)
    assert len(hours) == len(set(hours)) == count
    case = reference_case()
    case['month'] = month
    case['hours'] = [dict(timestamp=t, demand_mwh=10, backing_mwh=8, topup_mwh=0)
                     for t in hours]
    assert screen_correlation(case)['scenarios'][0]['rate_eur_mwh'] == 0


@pytest.mark.parametrize('value', [True, float('nan'), float('inf'), -1, '3'])
def test_invalid_numeric_inputs(value):
    for key in ('demand_mwh', 'backing_mwh', 'topup_mwh'):
        case = reference_case()
        case['hours'][0][key] = value
        with pytest.raises(ValueError):
            screen_correlation(case)
    case = reference_case()
    case['topup_eur_mwh'] = value
    with pytest.raises(ValueError):
        screen_correlation(case)


def test_month_scope_source_and_zero_load_fail_closed():
    cases = []
    c = reference_case()
    c['hours'].pop()
    cases.append(c)
    c = reference_case()
    c['hours'][1]['timestamp'] = c['hours'][0]['timestamp']
    cases.append(c)
    c = reference_case()
    c['hours'][0]['demand_mwh'] = 0
    cases.append(c)
    c = reference_case()
    c['pathway'] = 'SRAP'
    cases.append(c)
    c = reference_case()
    c['source']['publication_date'] = '2026-11-20'
    cases.append(c)
    c = reference_case()
    c['scope']['additionality'] = 'unknown'
    cases.append(c)
    c = reference_case()
    c['evidence_gaps'] = []
    cases.append(c)
    for case in cases:
        assert run_workflow(case)['states'] == {'evidence':'failed', 'finance':'blocked'}


def test_evidence_handoff_deterministic_parity_and_source_fixture():
    case = reference_case()
    original = deepcopy(case)
    result = run_workflow(case)
    assert result['success']
    assert result['results']['finance']['report'] == screen_correlation(case)
    assert case == original
    raw = files('energy_agents').joinpath('data/correlation/boe-articles-8-9.txt').read_bytes()
    assert sha256(raw).hexdigest() == case['source']['excerpt_sha256']
    audit = correlation_audit(case)
    audit['baseline'][0]['deviation_fraction'] = '1'
    with pytest.raises(ValueError, match='handoff'):
        screen_correlation(case, audit)
    audit = correlation_audit(case)
    case['implementation_eur'] += 1
    with pytest.raises(ValueError, match='handoff'):
        screen_correlation(case, audit)


@pytest.mark.parametrize('action', [
    {'tool':'trade_energy','arguments':{}}, {'tool':'certify_compliance','arguments':{}},
    {'tool':'delegate','arguments':{'task_id':'finance'}}])
def test_permissions_and_handoff_order(action):
    class Planner:
        def next_action(self, context):
            return action
    result = run_workflow(reference_case(), Planner())
    assert not result['success']
    assert all(row['status'] == 'rejected' for row in result['trace'])


def test_edi_physical_comparator_and_hash_guard(monkeypatch):
    pytest.importorskip('energy_methods.hybrid_dispatch')
    assert edi_crosscheck(reference_case())['parity']
    import energy_agents.business.correlation as module
    original = module.data_file

    def changed(name):
        value = original(name)
        if name == 'edi_capabilities':
            value['source_sha256'] = '0'*64
        return value

    monkeypatch.setattr(module, 'data_file', changed)
    with pytest.raises(ValueError, match='hash'):
        edi_crosscheck(reference_case())
