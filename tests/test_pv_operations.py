import json
from copy import deepcopy
from io import BytesIO
from unittest.mock import patch

import pytest

from energy_agents.connectors import PVChatCompletionsPlanner
from energy_agents.pv import PVReplayPlanner, run_pv_workflow, synthetic_pv_case, validate_case
from energy_agents.pv.analysis import export, run_comparison
from energy_agents.pv.methods import review_evidence
from energy_agents.roles import PV_ROLES


def test_reference_accounting_and_mode_parity():
    case = synthetic_pv_case()
    saved = deepcopy(case)
    result = run_comparison(case)
    assert result["all_passed"] and result["report_parity"]
    assert case == saved
    assert [r["planner_calls"] for r in result["runs"]] == [0, 6, 10]
    assert [r["tool_calls"] for r in result["runs"]] == [5, 5, 5]
    reports = result["runs"][2]["reports"]
    p = reports["performance"]["data"]
    assert (p["expected_mwh"], p["actual_mwh"], p["deficit_mwh"], p["surplus_mwh"]) == (
        500,
        435,
        70,
        5,
    )
    assert p["coverage_fraction"] == pytest.approx(5 / 6)
    assert p["excluded_dates"] == ["2026-10-06"]
    assert reports["reliability"]["data"] == {
        "equipment_fault_mwh": 40,
        "curtailment_mwh": 20,
        "unresolved_mwh": 10,
    }
    c = reports["commercial"]["data"]
    assert (
        c["historical_deficit_value"],
        c["conditional_recovery_mwh"],
        c["conditional_gross_value"],
        c["conditional_net_value"],
    ) == (3500, 32, 1600, 1500)
    assert reports["asset_summary"]["data"]["decision"] == "human_review_required"
    assert all(r["evidence_kinds"] == ["synthetic"] for r in reports.values())


@pytest.mark.parametrize("value", [True, float("nan"), float("inf"), -1, "100"])
def test_bad_energy_rejected(value):
    case = synthetic_pv_case()
    case["days"][0]["actual_mwh"] = value
    with pytest.raises(ValueError):
        run_pv_workflow(case)


@pytest.mark.parametrize(
    "mutation", ["duplicate", "source", "event", "recovery", "empty", "timezone"]
)
def test_invalid_case_rejected(mutation):
    case = synthetic_pv_case()
    if mutation == "duplicate":
        case["days"].append(deepcopy(case["days"][0]))
    elif mutation == "source":
        del case["evidence"]["meter"]
    elif mutation == "event":
        case["days"][0]["event"] = "fault+curtailment"
    elif mutation == "recovery":
        case["assumptions"]["recovery_fraction"] = 1.1
    elif mutation == "empty":
        case["days"] = []
    elif mutation == "timezone":
        case["timezone"] = "Not/AZone"
    with pytest.raises(ValueError):
        validate_case(case)


def test_all_missing_is_not_zero_loss_claim():
    case = synthetic_pv_case()
    for row in case["days"]:
        row["actual_mwh"] = None
    result = run_pv_workflow(case)
    p = result["reports"]["performance"]["data"]
    assert p["coverage_fraction"] == 0
    assert len(p["excluded_dates"]) == 6
    assert result["reports"]["maintenance"]["data"]["actions"] == []
    assert (
        "Restore missing meter data" in result["reports"]["asset_summary"]["data"]["open_issues"][0]
    )


def test_negative_prices_preserved_and_no_annualisation():
    case = synthetic_pv_case()
    case["days"][1]["price_per_mwh"] = -50
    c = run_pv_workflow(case)["reports"]["commercial"]["data"]
    assert c["conditional_gross_value"] == -1600
    assert c["conditional_net_value"] == -1700
    assert c["historical_deficit_value"] == -500


class ActionPlanner:
    def __init__(self, tool, arguments=None):
        self.tool = tool
        self.arguments = arguments or {}

    def next_action(self, context):
        return {"tool": self.tool, "arguments": self.arguments}


@pytest.mark.parametrize(
    "tool", ["finish", "plan_maintenance", "send_work_order", "assess_commercial"]
)
def test_role_boundaries_and_early_finish(tool):
    result = run_pv_workflow(
        synthetic_pv_case(), planners={"performance_engineer": ActionPlanner(tool)}
    )
    assert not result["success"]
    assert result["trace"][-1]["status"] == "rejected"
    assert not result["reports"]


def test_arguments_and_dependency_order_enforced():
    result = run_pv_workflow(
        synthetic_pv_case(),
        planners={"performance_engineer": ActionPlanner("assess_performance", {"actual_mwh": 999})},
    )
    assert not result["success"]
    result = run_pv_workflow(
        synthetic_pv_case(),
        mode="single_agent",
        planners={"single_agent": ActionPlanner("assess_commercial")},
    )
    assert not result["success"]
    assert "prerequisite" in result["trace"][-1]["error"]


def test_budget_and_duplicate_tool_enforced():
    result = run_pv_workflow(synthetic_pv_case(), max_calls=1)
    assert not result["success"] and result["planner_calls"] == 1
    result = run_pv_workflow(
        synthetic_pv_case(), planners={"performance_engineer": ActionPlanner("assess_performance")}
    )
    assert not result["success"] and result["tool_calls"] == 1


class ContextMutator(PVReplayPlanner):
    def next_action(self, context):
        context["case"]["days"][0]["actual_mwh"] = 9000
        context["reports"].clear()
        return {
            "tool": "assess_performance" if not context["history"] else "finish",
            "arguments": {},
        }


def test_planner_cannot_mutate_case_or_reports():
    case = synthetic_pv_case()
    result = run_pv_workflow(case, planners={"performance_engineer": ContextMutator()})
    assert result["success"]
    assert result["case"] == case
    assert result["reports"]["performance"]["data"]["actual_mwh"] == 435


@pytest.mark.parametrize("tamper", ["value", "reference", "kind", "approval"])
def test_reviewer_rejects_tampering(tamper):
    case = synthetic_pv_case()
    result = run_pv_workflow(case)
    reports = result["reports"]
    if tamper == "value":
        reports["commercial"]["data"]["conditional_gross_value"] = 1e9
    elif tamper == "reference":
        reports["performance"]["evidence_ids"] = ["invented"]
    elif tamper == "kind":
        reports["performance"]["evidence_kinds"] = ["measured"]
    else:
        reports["maintenance"]["data"]["actions"][0]["requires_human_approval"] = False
    assert not review_evidence(case, reports)["passed"]


def test_mixed_evidence_origin_not_promoted():
    case = synthetic_pv_case()
    case["evidence"]["meter"].update(kind="measured", verification="verified")
    report = run_pv_workflow(case)["reports"]["performance"]
    assert report["evidence_kinds"] == ["measured", "synthetic"]
    assert report["verification"] == "not_independently_verified"


def test_exports_repeatable(tmp_path):
    export(tmp_path)
    initial = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    export(tmp_path)
    assert initial == {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    assert len(json.loads((tmp_path / "roles.json").read_text())) == 5


def test_optional_live_adapter_uses_pv_contract(monkeypatch):
    monkeypatch.setenv("ENERGY_AGENTS_API_KEY", "test-key")
    planner = PVChatCompletionsPlanner("https://example.test/chat/completions", "test-model")
    payload = {
        "choices": [{"message": {"content": '{"tool":"assess_performance","arguments":{}}'}}],
        "usage": {"total_tokens": 10},
    }
    with patch(
        "energy_agents.connectors.urlopen", return_value=BytesIO(json.dumps(payload).encode())
    ) as call:
        action = planner.next_action({"roles": [PV_ROLES[0].as_dict()]})
    assert action["tool"] == "assess_performance"
    body = json.loads(call.call_args.args[0].data)
    assert "professional roles" in body["messages"][0]["content"]
    assert "windows" not in body["messages"][0]["content"]
    assert planner.usage == [{"total_tokens": 10}]
