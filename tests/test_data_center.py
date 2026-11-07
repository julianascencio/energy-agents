from copy import deepcopy

import pytest

from energy_agents.data_center import (
    design_catalogue,
    design_roles,
    reference_case,
    review_design,
    run_design_agent,
    run_design_team,
    screen_design,
)


def test_independent_energy_and_capacity_balance():
    report = screen_design(reference_case())
    assert report['facility_peak_mw'] == 26
    assert report['grid_headroom_mw'] == -2
    assert report['rack_count'] == 200
    assert report['annual_it_mwh'] == 140160
    assert report['annual_facility_mwh'] == 175200
    assert report['annual_electricity_cost_eur'] == 17520000
    assert report['annual_site_water_m3'] == 28032
    assert report['air_heat_mw'] + report['liquid_heat_mw'] == 20
    assert report['liquid_flow_kg_s'] == pytest.approx(382.22646918)
    assert report['ups_headroom_mw'] == report['air_headroom_mw'] == 0


@pytest.mark.parametrize('key,value', [
    ('it_mw', float('nan')), ('grid_mw', float('inf')), ('annual_pue', .9),
    ('rack_kw', 0), ('liquid_fraction', 1.1), ('ups_units', True),
    ('ups_spare_units', 5), ('annual_load_factor', -1), ('hours_per_year', 9000),
    ('documents', {'utility_offer': ''}),
])
def test_bad_input_rejected(key, value):
    case = reference_case()
    case[key] = value
    with pytest.raises(ValueError):
        screen_design(case)


def test_heat_partition_extremes_and_zero_load_energy():
    case = reference_case()
    case.update(liquid_fraction=0, annual_load_factor=0)
    a = screen_design(case)
    assert a['liquid_flow_kg_s'] == a['annual_facility_mwh'] == 0
    assert a['air_heat_mw'] == 20
    case['liquid_fraction'] = 1
    assert screen_design(case)['air_heat_mw'] == 0


def test_team_covers_every_role_and_preserves_gaps():
    case = reference_case()
    original = deepcopy(case)
    result = run_design_team(case)
    assert result['success'] and not result['design_approved']
    assert len(result['results']) == 14
    assert set(result['results']) == {r.id for r in design_roles()}
    electrical = result['results']['electrical_engineer']['review']
    assert electrical['capacity_shortfalls'] == ['grid_headroom_mw']
    assert 'utility_offer' in electrical['missing_documents']
    assert result['results']['delivery_manager']['review']['upstream_requiring_review']
    assert original == case
    assert len(design_catalogue()['post']['groups']) == 6


def test_documents_are_references_not_acceptance():
    case = reference_case()
    case['documents'] = {k: 'unverified://document' for k in
                         ('single_line_diagram', 'utility_offer', 'protection_study')}
    review = review_design('electrical_engineer', case)
    assert not review['missing_documents']
    assert review['requires_human_review'] and not review['design_approved']


class BadPlanner:
    def next_action(self, context):
        context['case']['grid_mw'] = 999
        return {'tool': 'energize', 'arguments': {}}


def test_unauthorized_tools_and_dependency_failure():
    case = reference_case()
    result = run_design_team(case, {'design_director': BadPlanner()})
    assert not result['success']
    assert result['states']['design_director'] == 'failed'
    assert result['states']['delivery_manager'] == 'blocked'
    assert case['grid_mw'] == 24


class CitationPlanner:
    def next_action(self, context):
        if context['review'] is None:
            return {'tool': 'review_design', 'arguments': {}}
        return {'tool': 'submit_review', 'arguments': {
            'summary': 'Fabricated source', 'source_ids': ['nonexistent']}}


def test_invalid_citations_and_budget_rejected():
    result = run_design_agent('architect', reference_case(), CitationPlanner())
    assert not result['success']
    assert result['review'] is not None
    assert result['trace'][-1]['status'] == 'rejected'
    with pytest.raises(ValueError):
        run_design_agent('architect', reference_case(), max_calls=True)
