from copy import deepcopy

import pytest

from energy_agents.business.tandem import digest, reference_case, run_workflow, screen_premium


def test_hand_calculation_and_signed_ceiling():
    c = reference_case()
    c.update(years=2, discount_rate=0, premium_usd=100, extra_opex_usd_year=10,
             value_usd_mwh=50)
    c['energy'] = {'baseline_mwh': [10, 10], 'alternatives': {'higher': [12, 11]}}
    c['provenance']['energy_sha256'] = digest(c['energy'])
    r = screen_premium(c)['scenarios']['higher']
    assert r['premium_ceiling_usd'] == 130
    assert r['incremental_npv_usd'] == 30
    c['value_usd_mwh'] = -50
    assert screen_premium(c)['scenarios']['higher']['premium_ceiling_usd'] == -170


def test_premium_and_opex_sensitivity():
    c = reference_case()
    r = screen_premium(c)['scenarios']['equal_degradation']
    c['premium_usd'] = r['premium_ceiling_usd']
    assert screen_premium(c)['scenarios']['equal_degradation']['incremental_npv_usd'] == 0
    c['extra_opex_usd_year'] += 100
    assert screen_premium(c)['scenarios']['equal_degradation']['incremental_npv_usd'] < 0


def test_fixture_has_clipping_and_downside():
    c = reference_case()
    e = c['energy']
    assert 1 < e['alternatives']['equal_degradation'][0] / e['baseline_mwh'][0] < 1.2
    assert e['alternatives']['faster_degradation'][-1] < e['baseline_mwh'][-1]
    r = screen_premium(c)['scenarios']
    assert r['equal_degradation']['incremental_npv_usd'] == pytest.approx(40235.37702)
    assert r['faster_degradation']['incremental_npv_usd'] < 0


@pytest.mark.parametrize('key,value', [('years', True), ('years', 41),
    ('premium_usd', -1), ('value_usd_mwh', float('nan')), ('discount_rate', 2),
    ('extra_opex_usd_year', True), ('currency', 'EUR'), ('classification', 'observed')])
def test_invalid_inputs(key, value):
    c = reference_case()
    c[key] = value
    with pytest.raises(ValueError):
        screen_premium(c)


def test_tampered_energy_and_mismatched_horizon():
    c = reference_case()
    c['energy']['baseline_mwh'][0] += 1
    with pytest.raises(ValueError, match='provenance'):
        screen_premium(c)
    c = reference_case()
    c['years'] -= 1
    with pytest.raises(ValueError):
        screen_premium(c)


def test_workflow_parity_input_isolation_and_evidence_gate():
    c = reference_case()
    before = deepcopy(c)
    r = run_workflow(c)
    assert r['success'] and r['results']['finance']['report'] == screen_premium(c)
    assert c == before
    c['source']['classification'] = 'field_validated'
    r = run_workflow(c)
    assert r['states'] == {'evidence': 'failed', 'finance': 'blocked'}


@pytest.mark.parametrize('action', [{'tool': 'buy', 'arguments': {}},
    {'tool': 'delegate', 'arguments': {'task_id': 'finance'}}])
def test_permissions_and_order(action):
    class BadPlanner:
        def next_action(self, context):
            return action
    r = run_workflow(reference_case(), BadPlanner())
    assert not r['success'] and all(t['status'] == 'rejected' for t in r['trace'])


def test_optional_edi_replay():
    pytest.importorskip('energy_methods.pv_repowering')
    from energy_agents.business.tandem import edi_energy
    e, ph = edi_energy()
    c = reference_case()
    assert digest(e) == c['provenance']['energy_sha256']
    assert ph == c['provenance']['profile_sha256']
