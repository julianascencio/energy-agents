import json
from copy import deepcopy

import pytest

from energy_agents.career_roles import (
    CareerReplayPlanner,
    CareerRolePlanner,
    career_catalogue,
    career_instruction,
    career_role_context,
    career_roles,
    career_runners,
    inspect_role_inputs,
    main,
    run_career_agent,
    synthetic_career_case,
)
from energy_agents.orchestrator import AgentTask, run_orchestrator

ROLE = "career_forward_deployed_engineer"


def test_complete_dated_listing_mapping_and_deliberate_deduplication():
    cat = career_catalogue()
    assert set(cat) == {
        "schema_version", "snapshot_date", "listing_count", "role_count",
        "extraction_note", "normalization_notes", "listings", "roles",
    }
    assert cat["schema_version"] == 2
    assert cat["snapshot_date"] == "2026-11-10"
    assert len(cat["roles"]) == cat["role_count"] == 53
    assert len(cat["listings"]) == cat["listing_count"] == 57
    roles = {r["id"]: r for r in cat["roles"]}
    listings = {s["id"]: s for s in cat["listings"]}
    assert set(listings) == {f"role_source_{i:03d}" for i in range(1, 58)}
    assert all(set(s) == {"id", "title", "agent_id"} for s in listings.values())
    assert all(s["title"] == roles[s["agent_id"]]["title"] for s in listings.values())
    assert "https://" not in json.dumps(cat) and "http://" not in json.dumps(cat)
    assert len(roles) == 53 and len(listings) == 57
    assert len({r["mandate"] for r in roles.values()}) == 53
    mapped = [sid for r in roles.values() for sid in r["listing_ids"]]
    assert len(mapped) == len(set(mapped)) == 57
    assert set(mapped) == set(listings)
    for role in roles.values():
        for key in ("required_inputs", "deliverables", "responsibilities", "review_checks", "kpis"):
            assert len(role[key]) >= 2 and len(set(role[key])) == len(role[key])
        assert set(role["handoffs"]) <= set(roles) - {role["id"]}
        assert role["authority"] == "advisory_only"
        assert all(listings[s]["agent_id"] == role["id"] for s in role["listing_ids"])
    assert roles["career_procurement_assistant"]["listing_ids"] == [
        "role_source_034", "role_source_035", "role_source_036"
    ]
    assert roles[ROLE]["listing_ids"] == ["role_source_017", "role_source_018"]
    assert roles["career_customer_support_specialist"]["listing_ids"] == [
        "role_source_052", "role_source_055"
    ]


@pytest.mark.parametrize("role", career_roles(), ids=lambda role: role.id)
def test_every_agent_runs_and_keeps_missing_inputs_visible(role):
    case = synthetic_career_case()
    original = deepcopy(case)
    result = run_career_agent(role.id, case)
    assert result["success"] and result["mode"] == "scripted_work_plan"
    assert result["requires_human_review"] and not result["execution_authorized"]
    assert len(result["trace"]) == 2
    assert set(result["inspection"]["missing_inputs"]) == set(role.inputs) - set(case["inputs"])
    card = career_role_context(role.id)["role"]
    assert {d["name"] for d in result["proposal"]["deliverables"]} == set(card["deliverables"])
    assert case == original
    assert role.title in career_instruction(role.id)
    assert card["responsibilities"][0] in career_instruction(role.id)


def test_catalogue_and_context_are_isolated():
    career_catalogue()["roles"].clear()
    career_role_context(ROLE)["role"]["deliverables"].clear()
    assert len(career_roles()) == 53
    assert career_role_context(ROLE)["role"]["deliverables"]
    with pytest.raises(ValueError, match="Unknown career role"):
        career_role_context("invented_role")


def test_empty_case_and_unverified_references_never_become_validated_facts():
    case = dict(id="empty", objective="Prepare a plan", inputs={}, evidence={})
    result = run_career_agent(ROLE, case)
    assert result["success"] and len(result["inspection"]["missing_inputs"]) == 4
    case["inputs"]["customer_brief"] = dict(text="Unverified brief", evidence_ids=[])
    inspection = inspect_role_inputs(ROLE, case)
    assert inspection["inputs_without_evidence"] == ["customer_brief"]
    case["evidence"]["link"] = dict(kind="reference_only", summary="Unretrieved document URL")
    case["inputs"]["customer_brief"]["evidence_ids"] = ["link"]
    result = run_career_agent(ROLE, case)
    assert result["inspection"]["evidence_kinds"] == {"link": "reference_only"}
    assert "not_factual_verification" in result["inspection"]["evidence_validation"]


class InvalidPlanner:
    def __init__(self, mutation):
        self.mutation = mutation

    def next_action(self, context):
        action = CareerReplayPlanner().next_action(context)
        if context["inspection"] is not None:
            self.mutation(action)
        return action


@pytest.mark.parametrize("mutation", [
    lambda a: a.update(tool="execute_shell"),
    lambda a: a["arguments"].update(execution_authorized=True),
    lambda a: a["arguments"]["deliverables"].pop(),
    lambda a: a["arguments"]["deliverables"][1].update(
        name=a["arguments"]["deliverables"][0]["name"]),
    lambda a: a["arguments"]["deliverables"][0].update(evidence_ids=["invented_evidence"]),
    lambda a: a["arguments"]["deliverables"][0].update(evidence_ids=["role_source_017"]),
    lambda a: a["arguments"]["deliverables"][0].update(content=" "),
    lambda a: a["arguments"]["deliverables"][0].update(evidence_ids=[], assumptions=[]),
    lambda a: a["arguments"].update(open_questions="none"),
])
def test_invalid_proposals_fail_closed_with_bounded_trace(mutation):
    result = run_career_agent(ROLE, synthetic_career_case(), InvalidPlanner(mutation), max_calls=3)
    assert not result["success"] and result["proposal"] is None
    assert len(result["trace"]) == 3
    assert result["trace"][-1]["status"] == "rejected"
    assert not result["execution_authorized"]


def test_out_of_order_calls_can_be_repaired_and_unauthorized_tools_never_dispatch():
    class RepairPlanner:
        def next_action(self, context):
            if not context["history"]:
                return {"tool": "submit_proposal", "arguments": {}}
            return CareerReplayPlanner().next_action(context)

    result = run_career_agent(ROLE, synthetic_career_case(), RepairPlanner())
    assert result["success"] and len(result["trace"]) == 3
    assert result["trace"][0]["status"] == "rejected"


def test_unrelated_inputs_are_not_shared_and_planner_cannot_erase_gaps():
    case = synthetic_career_case()
    case["evidence"]["private_hr"] = dict(kind="user_supplied", summary="Unrelated HR data")
    case["inputs"]["hr_workflow"] = dict(text="Unrelated HR workflow", evidence_ids=["private_hr"])
    original = deepcopy(case)

    class MutatingPlanner:
        def next_action(self, context):
            assert "hr_workflow" not in context["case"]["inputs"]
            assert "private_hr" not in context["case"]["evidence"]
            action = CareerReplayPlanner().next_action(context)
            context["case"]["inputs"].clear()
            context["role"]["required_inputs"].clear()
            if context["inspection"]:
                context["inspection"]["missing_inputs"].clear()
            return action

    # The business analyst deliberately lacks product_boundaries in this case.
    result = run_career_agent("career_business_analyst", case, MutatingPlanner())
    assert result["success"] and result["inspection"]["missing_inputs"] == ["product_boundaries"]
    assert original == case


@pytest.mark.parametrize("budget", [0, 9, True, 1.5])
def test_invalid_call_budget(budget):
    with pytest.raises(ValueError, match="max_calls"):
        run_career_agent(ROLE, synthetic_career_case(), max_calls=budget)


def test_budget_exhaustion_and_provider_exception_do_not_claim_success():
    assert not run_career_agent(ROLE, synthetic_career_case(), max_calls=1)["success"]

    class BrokenPlanner:
        def next_action(self, context):
            raise RuntimeError("secret provider detail")

    result = run_career_agent(ROLE, synthetic_career_case(), BrokenPlanner())
    assert not result["success"] and "secret" not in json.dumps(result)
    assert result["trace"][0]["error_type"] == "RuntimeError"


@pytest.mark.parametrize("mutation", [
    lambda c: c.update(objective=""),
    lambda c: c.update(inputs=[]),
    lambda c: c.update(evidence=[]),
    lambda c: c["evidence"]["synthetic_brief"].update(kind="verified"),
    lambda c: c["inputs"]["customer_brief"].update(evidence_ids=["missing"]),
    lambda c: c["inputs"]["customer_brief"].update(text=""),
    lambda c: c.update(execute=True),
])
def test_malformed_case_rejected(mutation):
    case = synthetic_career_case()
    mutation(case)
    with pytest.raises(ValueError):
        run_career_agent(ROLE, case)


def test_registered_roles_work_with_existing_orchestrator_and_block_failed_handoffs():
    runners = career_runners()
    assert set(runners) == {r.id for r in career_roles()}
    case = synthetic_career_case()
    tasks = [AgentTask("discovery", ROLE, payload=case),
             AgentTask("implementation", "career_full_stack_ai_engineer", ("discovery",), case)]
    result = run_orchestrator(tasks, runners)
    assert result["success"]
    assert result["results"]["implementation"]["upstream_task_ids"] == ["discovery"]
    bad = career_runners({ROLE: InvalidPlanner(lambda a: a.update(tool="deploy"))})
    failed = run_orchestrator(tasks, bad)
    assert failed["states"] == {"discovery": "failed", "implementation": "blocked"}
    with pytest.raises(ValueError, match="known career"):
        career_runners({"invented": CareerReplayPlanner()})


def test_live_adapter_uses_role_instruction_with_mocked_transport(monkeypatch):
    calls = []

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            payload = json.loads(calls[-1].data)
            context = json.loads(payload["messages"][1]["content"])
            action = CareerReplayPlanner().next_action(context)
            return json.dumps({"choices": [{"message": {"content": json.dumps(action)}}]})

    def urlopen(request, timeout):
        calls.append(request)
        return Response()

    monkeypatch.setenv("ENERGY_AGENTS_TEST_KEY", "test-only-key")
    monkeypatch.setattr("energy_agents.connectors.urlopen", urlopen)
    planner = CareerRolePlanner(ROLE, endpoint="https://example.test/chat/completions",
                                model="test-model", api_key_env="ENERGY_AGENTS_TEST_KEY")
    result = run_career_agent(ROLE, synthetic_career_case(), planner)
    assert result["success"] and result["mode"] == "planner_proposal"
    assert len(calls) == 2
    payload = json.loads(calls[0].data)
    assert payload["messages"][0]["content"] == career_instruction(ROLE)
    assert "test-only-key" not in json.dumps(result)
    with pytest.raises(ValueError, match="match"):
        run_career_agent("career_ai_production_engineer", synthetic_career_case(), planner)


def test_cli_exports_every_role_and_lists_ids(tmp_path, capsys):
    main(["--output", str(tmp_path)])
    export = json.loads((tmp_path / "work_plans.json").read_text())
    assert len(export["results"]) == 53
    assert export["snapshot_listing_count"] == export["selected_listing_count"] == 57
    assert all(r["success"] for r in export["results"])
    main(["--role", ROLE, "--output", str(tmp_path)])
    selected = json.loads((tmp_path / "work_plans.json").read_text())
    assert len(selected["results"]) == 1 and selected["selected_listing_count"] == 2
    main(["--list"])
    assert "career_powergrid_expert" in capsys.readouterr().out
