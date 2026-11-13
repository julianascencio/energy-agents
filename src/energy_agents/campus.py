"""Six-function campus team, reusing the bounded data center design agents."""

import argparse
import json
from pathlib import Path

from .data_center import (
    design_catalogue,
    reference_case,
    run_design_agent,
    screen_campus_layout,
    screen_design,
)
from .orchestrator import AgentTask, run_orchestrator


def campus_catalogue() -> dict:
    """Return the screenshot group mapping and three generic role additions."""
    return design_catalogue(include_campus=True)['campus_team']


def campus_reference_case() -> dict:
    """Synthetic 20 MW campus: 200 required racks but only 180 planned slots."""
    case = reference_case()
    case['id'] = 'synthetic-campus-design-to-delivery'
    case['layout'] = dict(hall_count=2, rack_slots_per_hall=90,
                          hall_white_space_m2=600, planning_m2_per_rack=6)
    return case


def campus_tasks() -> list[AgentTask]:
    """Explicit dependencies; do not infer task order from catalogue position."""
    disciplines = ('electrical_engineer', 'controls_engineer', 'mechanical_engineer',
                   'liquid_cooling_engineer', 'civil_engineer', 'structural_engineer',
                   'architect', 'telecom_engineer', 'sustainability_engineer')
    tasks = [AgentTask('design_director', 'design_director'),
             AgentTask('campus_design_engineer', 'campus_design_engineer', ('design_director',))]
    tasks.extend(AgentTask(r, r, ('campus_design_engineer',)) for r in disciplines)
    tasks.append(AgentTask('data_hall_site_planner', 'data_hall_site_planner',
                           ('campus_design_engineer', *disciplines)))
    tasks.append(AgentTask('design_manager', 'design_manager',
                           (*disciplines, 'data_hall_site_planner', 'campus_design_engineer')))
    tasks.append(AgentTask('facilities_development_manager', 'facilities_development_manager',
                           ('design_manager', 'data_hall_site_planner')))
    tasks.append(AgentTask('commissioning_engineer', 'commissioning_engineer',
                           ('facilities_development_manager',)))
    # Governance and delivery see every preceding report, not merely a summary.
    tasks.append(AgentTask('technical_governance', 'technical_governance',
                           tuple(t.id for t in tasks)))
    tasks.append(AgentTask('delivery_manager', 'delivery_manager', tuple(t.id for t in tasks)))
    return tasks


def _readiness_register(result: dict) -> dict:
    """Keep failed protocols, capacity gaps and unverified evidence independently visible."""
    issues = []
    for role_id, state in result['states'].items():
        if state != 'completed':
            issues.append(dict(owner=role_id, kind='protocol_incomplete', item=state))
        review = result['results'].get(role_id, {}).get('review')
        if review is None:
            continue
        for metric in review['capacity_shortfalls']:
            issues.append(dict(owner=role_id, kind='capacity_shortfall', item=metric,
                               value=review['metrics'][metric]))
        for document in review['missing_documents']:
            issues.append(dict(owner=role_id, kind='missing_document_reference', item=document))
        for document in review['supplied_document_references']:
            issues.append(dict(owner=role_id, kind='unverified_document_reference', item=document))
    return dict(issues=issues, requires_human_review=True, ready_for_service=False,
                status='advisory_review_only',
                note='Rows are role-owned findings, not unique project risks. '
                     'No automatic engineering acceptance, even with zero arithmetic shortfalls.')


def run_campus_team(case: dict, planners: dict | None = None) -> dict:
    """Run seventeen specialists; success records protocol completion, not readiness.

    The default is deterministic replay. Pass DataCenterDesignPlanner instances by
    role ID for optional live planning under the existing two-step tool contract.
    """
    screen_campus_layout(case)
    tasks = campus_tasks()
    roles = {t.role for t in tasks}
    planners = planners or {}
    if set(planners) - roles:
        raise ValueError('Unknown planner role')

    def runner(role_id):
        def run(context):
            return run_design_agent(role_id, case, planners.get(role_id),
                                    upstream=context['upstream'])
        return run

    result = run_orchestrator(tasks, {r: runner(r) for r in roles}, max_calls=len(tasks))
    result.update(readiness=_readiness_register(result), design_approved=False,
                  requires_human_review=True, evidence=case['evidence'],
                  mode='supplied_planners' if planners else 'offline_replay',
                  groups=campus_catalogue()['groups'])
    return result


def main() -> None:
    """Export the synthetic case or a user JSON case, catalogue, screens and role traces."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, help='JSON case using the documented schema')
    parser.add_argument('--output', type=Path, default=Path('outputs/campus_team'))
    args = parser.parse_args()
    case = json.loads(args.input.read_text()) if args.input else campus_reference_case()
    result = run_campus_team(case)
    args.output.mkdir(parents=True, exist_ok=True)
    exports = dict(case=case, catalogue=design_catalogue(include_campus=True),
                   screen=screen_design(case), layout=screen_campus_layout(case), team=result)
    for name, data in exports.items():
        (args.output / f'{name}.json').write_text(json.dumps(data, indent=2) + '\n')
    if not result['success']:
        raise SystemExit('Campus review protocol incomplete; inspect team.json')


if __name__ == '__main__':
    main()
