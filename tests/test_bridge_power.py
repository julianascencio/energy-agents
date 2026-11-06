import json
from copy import deepcopy
from importlib.resources import files

import pytest

from energy_agents.business.bridge_power import (
    reference_case,
    run_bridge_workflow,
    screen_bridge_power,
)


def test_hand_calculation_and_energy_boundary():
    case = reference_case()
    case['assumptions'].update(grid_month=1, bridge_month=0, annual_discount_rate=0,
                               it_mw=1, hours_per_month=100, pue=2, utilization=1,
                               availability=1, margin_eur_per_it_mwh=10,
                               power_eur_per_facility_mwh=2, monthly_fixed_eur=50,
                               upfront_eur=100)
    result = screen_bridge_power(case)
    row = result['monthly'][0]
    assert row['it_mwh'] == 100
    assert row['facility_mwh'] == 200
    assert row['net_cash_eur'] == 550
    assert result['bridge_incremental_npv_eur'] == 450
    assert result['break_even_margin_eur_per_it_mwh'] == 5.5


def test_discount_timing_and_break_even():
    case = reference_case()
    result = screen_bridge_power(case)
    expected = -2_000_000 + sum(554664 / 1.1 ** (m / 12) for m in range(4, 13))
    assert result['bridge_incremental_npv_eur'] == pytest.approx(expected)
    case['assumptions']['margin_eur_per_it_mwh'] = result['break_even_margin_eur_per_it_mwh']
    assert screen_bridge_power(case)['bridge_incremental_npv_eur'] == pytest.approx(0, abs=1e-8)


@pytest.mark.parametrize('key,value', [('pue', .9), ('it_mw', float('nan')),
    ('availability', 1.1), ('grid_month', True), ('bridge_month', 1.5),
    ('power_eur_per_facility_mwh', -1), ('upfront_eur', float('inf'))])
def test_invalid_inputs(key, value):
    case = reference_case()
    case['assumptions'][key] = value
    with pytest.raises(ValueError):
        screen_bridge_power(case)


@pytest.mark.parametrize('update', [{'grid_month': 2}, {'availability': 0},
                                  {'margin_eur_per_it_mwh': 0}])
def test_no_false_positive_when_no_benefit(update):
    case = reference_case()
    case['assumptions'].update(update)
    result = screen_bridge_power(case)
    assert result['screened_choice'] == 'wait_for_grid'
    assert result['best_incremental_npv_eur'] == 0


def test_parity_handoff_and_immutability():
    case = reference_case()
    before = deepcopy(case)
    run = run_bridge_workflow(case)
    assert run['success']
    assert [t['task_id'] for t in run['trace']] == ['evidence', 'finance']
    assert run['results']['finance']['screen'] == screen_bridge_power(case)
    assert case == before


def test_missing_evidence_blocks_finance():
    case = reference_case()
    case['source']['url'] = ''
    run = run_bridge_workflow(case)
    assert run['states'] == {'evidence': 'failed', 'finance': 'blocked'}
    assert not run['success']


@pytest.mark.parametrize('action', [
    {'tool': 'purchase', 'arguments': {}},
    {'tool': 'delegate', 'arguments': {'task_id': 'finance'}},
])
def test_forbidden_action_and_premature_handoff(action):
    class BadPlanner:
        def next_action(self, context):
            context['tasks'][0]['payload']['case']['assumptions']['upfront_eur'] = 0
            return action
    run = run_bridge_workflow(reference_case(), BadPlanner())
    assert not run['success']
    assert len(run['trace']) == 4
    assert all(t['status'] == 'rejected' for t in run['trace'])


def test_packaged_evidence_and_prompt_contract():
    root = files('energy_agents').joinpath('data/bridge_power')
    skill = json.loads(root.joinpath('skill.json').read_text())
    catalogue = json.loads(root.joinpath('edi_capabilities.json').read_text())
    assert skill['authority'] == 'advisory_only'
    assert skill['role'] == 'project_finance_analyst'
    assert len(catalogue['commit']) == 40
    assert catalogue['coverage']['errors'] == []
    assert catalogue['entries']


def test_edi_adapter_executes_validation_and_propagates_failure(tmp_path, monkeypatch):
    import sys
    from types import ModuleType

    from energy_agents.business.bridge_power import inspect_edi_inventory

    module = ModuleType('energy_data_retrieval.data_center_catalogue.catalogue')
    seen = []
    module.load_records = lambda root: [{'record_id': 'test'}]
    module.validate_record = lambda row, sources: seen.append((row, sources))
    monkeypatch.setitem(sys.modules, module.__name__, module)
    (tmp_path / 'records').mkdir()
    (tmp_path / 'sources.json').write_text('{}')
    result = inspect_edi_inventory(tmp_path)
    assert result['records'] == 1
    assert len(seen) == 1
    assert result['use'] == 'inventory_context_only_not_financial_calibration'

    def reject(row, sources):
        raise ValueError('Invalid evidence')
    module.validate_record = reject
    with pytest.raises(ValueError, match='Invalid evidence'):
        inspect_edi_inventory(tmp_path)
