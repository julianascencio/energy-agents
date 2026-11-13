import json
from copy import deepcopy

import pytest

from energy_agents.campus import (
    campus_catalogue,
    campus_reference_case,
    campus_tasks,
    main,
    run_campus_team,
)
from energy_agents.data_center import (
    DesignReplayPlanner,
    design_catalogue,
    design_instruction,
    design_roles,
    run_design_agent,
    screen_campus_layout,
)


def test_six_groups_reuse_fourteen_and_add_three_roles():
    catalogue = campus_catalogue()
    original = {r.id for r in design_roles()}
    extended = {r.id for r in design_roles(include_campus=True)}
    assert len(original) == 14 and len(extended) == 17
    assert extended - original == {
        'campus_design_engineer', 'data_hall_site_planner', 'facilities_development_manager'}
    assert len(catalogue['groups']) == 6
    mapped = [r for g in catalogue['groups'] for r in g['role_ids']]
    mapped.extend(catalogue['supporting_role_ids'])
    assert len(mapped) == len(set(mapped)) == 17
    assert set(mapped) == extended == {t.role for t in campus_tasks()}
    for role in catalogue['roles']:
        assert role['title'] in design_instruction(role['id'])
        assert role['skills'] and role['handoffs'] and role['evaluation']
        assert role['authority'] == 'advisory_only'


def test_layout_screen_and_independent_area_rounding():
    case = campus_reference_case()
    report = screen_campus_layout(case)
    assert report['required_racks'] == 200
    assert report['usable_rack_slots'] == 180
    assert report['layout_headroom_racks'] == -20
    case['layout'].update(hall_white_space_m2=599, rack_slots_per_hall=200)
    report = screen_campus_layout(case)
    assert report['area_limited_slots_per_hall'] == 99
    assert report['usable_rack_slots'] == 198
    # Pooling hall areas would incorrectly permit 199 racks.
    assert report['layout_headroom_racks'] == -2


def test_both_capacity_constraints_and_whole_rack_demand():
    case = campus_reference_case()
    case['it_mw'] = 20.01
    case['layout']['rack_slots_per_hall'] = 101
    report = screen_campus_layout(case)
    assert report['required_racks'] == 201
    assert report['required_racks_per_hall'] == 101
    assert report['usable_rack_slots'] == 200  # area, not nominal slots, limits
    assert report['layout_headroom_racks'] == -1


@pytest.mark.parametrize('key,value', [
    ('hall_count', True), ('hall_count', 2.5), ('hall_count', 0),
    ('rack_slots_per_hall', -1), ('rack_slots_per_hall', 90.0),
    ('hall_white_space_m2', float('nan')), ('hall_white_space_m2', float('inf')),
    ('planning_m2_per_rack', 0), ('planning_m2_per_rack', '6'),
])
def test_invalid_layout_rejected(key, value):
    case = campus_reference_case()
    case['layout'][key] = value
    with pytest.raises(ValueError):
        run_campus_team(case)


def test_missing_layout_and_unknown_planner_rejected():
    case = campus_reference_case()
    del case['layout']
    with pytest.raises(ValueError, match='layout'):
        run_campus_team(case)
    with pytest.raises(ValueError, match='Unknown planner'):
        run_campus_team(campus_reference_case(), {'unknown': DesignReplayPlanner()})


def test_role_reports_gaps_and_downstream_context_are_preserved():
    class CapturePlanner(DesignReplayPlanner):
        def next_action(self, context):
            self.context = deepcopy(context)
            return super().next_action(context)

    case = campus_reference_case()
    original = deepcopy(case)
    planner = CapturePlanner()
    result = run_campus_team(case, {'delivery_manager': planner})
    assert case == original
    assert result['success'] and len(result['results']) == 17
    assert not result['design_approved'] and not result['readiness']['ready_for_service']
    assert len(planner.context['upstream']) == 16
    issues = result['readiness']['issues']
    assert any(i['owner'] == 'electrical_engineer' and i.get('value') == -2 for i in issues)
    assert any(i['owner'] == 'data_hall_site_planner' and i.get('value') == -20 for i in issues)
    assert any(i['item'] == 'permit_register' for i in issues)


def test_fixing_arithmetic_and_supplying_references_never_approves_design():
    case = campus_reference_case()
    case['grid_mw'] = 26
    case['layout']['rack_slots_per_hall'] = 100
    case['documents'] = {d: 'unverified://reference' for role in
                         design_catalogue(include_campus=True)['roles']
                         for d in role['required_documents']}
    result = run_campus_team(case)
    assert result['success']
    issues = result['readiness']['issues']
    assert issues and {i['kind'] for i in issues} == {'unverified_document_reference'}
    assert not result['readiness']['ready_for_service']
    assert not result['design_approved']


def test_failed_planner_blocks_downstream_without_mutating_inputs():
    class BadPlanner:
        def next_action(self, context):
            context['case']['layout']['rack_slots_per_hall'] = 999
            return {'tool': 'approve_design', 'arguments': {}}

    case = campus_reference_case()
    result = run_campus_team(case, {'data_hall_site_planner': BadPlanner()})
    assert not result['success']
    assert result['states']['data_hall_site_planner'] == 'failed'
    assert result['states']['facilities_development_manager'] == 'blocked'
    assert result['states']['delivery_manager'] == 'blocked'
    assert any(i['owner'] == 'delivery_manager' and i['item'] == 'blocked'
               for i in result['readiness']['issues'])
    assert case['layout']['rack_slots_per_hall'] == 90


@pytest.mark.parametrize('role_id', [
    'campus_design_engineer', 'data_hall_site_planner', 'facilities_development_manager'])
def test_each_new_agent_rejects_premature_submission(role_id):
    class PrematurePlanner:
        def next_action(self, context):
            return {'tool': 'submit_review', 'arguments': {
                'summary': 'Approve everything', 'source_ids': context['role']['source_ids']}}

    result = run_design_agent(role_id, campus_reference_case(), PrematurePlanner())
    assert not result['success'] and not result['design_approved']
    assert len(result['trace']) == 3


def test_cli_user_input_exports_reproducible_results(tmp_path, monkeypatch):
    case = campus_reference_case()
    case['evidence'] = 'user_supplied'
    path = tmp_path / 'input.json'
    path.write_text(json.dumps(case))
    out = tmp_path / 'output'
    monkeypatch.setattr('sys.argv', ['campus', '--input', str(path), '--output', str(out)])
    main()
    first = {p.name: p.read_bytes() for p in out.iterdir()}
    main()
    assert first == {p.name: p.read_bytes() for p in out.iterdir()}
    assert json.loads(first['team.json'])['evidence'] == 'user_supplied'
    assert set(first) == {'case.json', 'catalogue.json', 'screen.json', 'layout.json', 'team.json'}
