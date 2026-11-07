from copy import deepcopy

import pytest

from energy_agents.business.vppa import reconcile_vppa, reference_case, run_vppa_workflow


def test_hand_calculated_settlement_and_capture():
    report = reconcile_vppa(reference_case())
    assert report['unhedged_cost_eur'] == 32000
    solar, wind = report['alternatives']['solar'], report['alternatives']['wind']
    assert solar['buyer_receipt_eur'] == -20000
    assert solar['capture_reference_eur_mwh'] == 15
    assert solar['net_cost_eur'] == 52800
    assert wind['buyer_receipt_eur'] == -5000
    assert wind['net_cost_eur'] == 37800
    assert solar['generation_to_load_energy_ratio'] == wind['generation_to_load_energy_ratio'] == 1
    assert solar['over_budget_eur'] == 12800
    assert wind['over_budget_eur'] == 0


def test_basis_shock_is_not_hedged():
    case = reference_case()
    before = reconcile_vppa(case)
    for row in case['intervals']:
        row['load_price_eur_mwh'] += 25
    after = reconcile_vppa(case)
    for name in case['mixes']:
        assert after['alternatives'][name]['buyer_receipt_eur'] == before['alternatives'][name]['buyer_receipt_eur']
        assert after['alternatives'][name]['net_cost_eur'] - before['alternatives'][name]['net_cost_eur'] == 10000


def test_receipt_sign_and_break_even():
    case = reference_case()
    for row in case['intervals']:
        row['reference_price_eur_mwh'] += 60
    report = reconcile_vppa(case)
    assert report['alternatives']['solar']['buyer_receipt_eur'] == 4000
    assert report['alternatives']['solar']['net_cost_eur'] == 28800
    case['strike_eur_mwh'] = report['alternatives']['solar']['break_even_strike_eur_mwh']
    assert reconcile_vppa(case)['alternatives']['solar']['change_vs_unhedged_eur'] == pytest.approx(0)


@pytest.mark.parametrize('key,value', [('load_mwh', -1), ('solar_mwh', float('nan')),
    ('hours', 0), ('load_price_eur_mwh', True), ('start_utc', '2026-11-05T01:00:00Z')])
def test_invalid_intervals(key, value):
    case = reference_case()
    case['intervals'][1][key] = value
    with pytest.raises(ValueError):
        reconcile_vppa(case)


def test_duplicate_timestamps_rejected():
    case = reference_case()
    case['intervals'][1]['start_utc'] = case['intervals'][0]['start_utc']
    with pytest.raises(ValueError):
        reconcile_vppa(case)


def test_unequal_contract_energy_rejected():
    case = reference_case()
    case['intervals'][0]['wind_mwh'] = 0
    with pytest.raises(ValueError, match='equal positive'):
        reconcile_vppa(case)


def test_workflow_parity_immutability_and_missing_evidence():
    case = reference_case()
    before = deepcopy(case)
    run = run_vppa_workflow(case)
    assert run['success'] and run['results']['finance']['report'] == reconcile_vppa(case)
    assert case == before
    case['source']['url'] = ''
    assert run_vppa_workflow(case)['states'] == {'evidence': 'failed', 'finance': 'blocked'}


@pytest.mark.parametrize('action', [{'tool': 'trade', 'arguments': {}},
    {'tool': 'delegate', 'arguments': {'task_id': 'finance'}}])
def test_forbidden_and_premature_handoffs(action):
    class BadPlanner:
        def next_action(self, context):
            return action
    run = run_vppa_workflow(reference_case(), BadPlanner())
    assert not run['success'] and len(run['trace']) == 4
    assert all(t['status'] == 'rejected' for t in run['trace'])


def test_edi_adapter_propagates_validation_failure(tmp_path, monkeypatch):
    import sys
    from types import ModuleType

    from energy_agents.business.vppa import inspect_edi_wind

    mod = ModuleType('energy_data_retrieval.wind_catalogue.catalogue')
    mod.load_records = lambda root: [{'country_code': 'ROU'}]
    seen = []
    mod.validate_record = lambda row, sources: seen.append(row)
    monkeypatch.setitem(sys.modules, mod.__name__, mod)
    (tmp_path / 'records').mkdir()
    (tmp_path / 'sources.json').write_text('{}')
    assert inspect_edi_wind(tmp_path)['records'] == 1 and len(seen) == 1
    def invalid(row, sources):
        raise ValueError('Invalid evidence')
    mod.validate_record = invalid
    with pytest.raises(ValueError, match='Invalid evidence'):
        inspect_edi_wind(tmp_path)
