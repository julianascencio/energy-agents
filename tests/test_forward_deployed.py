"""Workflow gates and handoff isolation, independent of model provider."""

from copy import deepcopy

import pytest

from energy_agents.forward_deployed import STAGES, run_forward_deployed_engineer

BRIEF = dict(problem="Triage", users="Analyst", evidence="Synthetic", constraints="Read-only")


class Planner:
    def __init__(self, invalid=None):
        self.invalid = invalid
        self.contexts = []

    def next_action(self, context):
        self.contexts.append(deepcopy(context))
        context["customer_brief"].clear()
        if self.invalid is not None:
            action, self.invalid = self.invalid, None
            return action
        tool = context["allowed_tools"][0]
        return {"tool": tool, "arguments": {k: "Proposed " + k for k in context["required_fields"]}}


def test_ordered_handoff_and_copies():
    planner = Planner()
    context = {"README": "Original"}
    result = run_forward_deployed_engineer(BRIEF, context, planner)
    assert result["success"] and len(result["trace"]) == 5
    assert list(result["reports"]) == list(STAGES)
    assert result["python_handoff"]["target_role"] == "python_ml_engineer"
    assert "acceptance_criteria" in result["python_handoff"]["task"]
    assert not result["deployment_authorized"]
    assert planner.contexts[-1]["customer_brief"] == BRIEF
    result["python_handoff"]["repository_context"]["README"] = "Changed"
    assert context["README"] == "Original"


@pytest.mark.parametrize(
    "action",
    [
        None,
        {},
        {"tool": "finish", "arguments": {}},
        {"tool": "submit_rollout", "arguments": {}},
        {"tool": "submit_discovery", "arguments": {}},
        {"tool": "submit_discovery", "arguments": {k: "" for k in STAGES["discovery"]}},
    ],
)
def test_rejection_and_repair(action):
    # None is also an invalid response (rather than the planner's default sentinel).
    class RepairPlanner(Planner):
        def next_action(self, context):
            if not self.contexts:
                self.contexts.append(deepcopy(context))
                return action
            return super().next_action(context)

    result = run_forward_deployed_engineer(BRIEF, {}, RepairPlanner())
    assert result["success"]
    assert result["trace"][0]["status"] == "rejected"


def test_explicit_finish_required():
    result = run_forward_deployed_engineer(BRIEF, {}, Planner(), max_calls=4)
    assert not result["success"]
    assert result["python_handoff"] is None
    assert len(result["reports"]) == 4


@pytest.mark.parametrize("budget", [0, 21, True, 1.5])
def test_invalid_budget(budget):
    with pytest.raises(ValueError):
        run_forward_deployed_engineer(BRIEF, {}, Planner(), max_calls=budget)


def test_brief_required():
    with pytest.raises(ValueError):
        run_forward_deployed_engineer({"problem": "Missing evidence"}, {}, Planner())


def test_provider_error_propagates():
    class Offline:
        def next_action(self, context):
            raise OSError("Unavailable")

    with pytest.raises(OSError):
        run_forward_deployed_engineer(BRIEF, {}, Offline())
