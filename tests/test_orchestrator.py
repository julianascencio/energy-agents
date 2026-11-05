from copy import deepcopy

import pytest

from energy_agents.orchestrator import AgentTask, run_orchestrator


def ok(context):
    return {"success": True, "data": [context["task_id"]]}


def test_handoff_and_input_isolation():
    tasks = [AgentTask("a", "role", payload={"items": [1]}), AgentTask("b", "role", ("a",))]
    original = deepcopy(tasks)

    def runner(context):
        if context["task_id"] == "b":
            assert context["upstream"]["a"]["data"] == ["a"]
            context["upstream"]["a"]["data"].clear()
        context["payload"].clear()
        return ok(context)

    result = run_orchestrator(tasks, {"role": runner})
    assert result["success"] and result["results"]["a"]["data"] == ["a"]
    assert tasks == original


def test_failure_blocks_descendants_but_not_independent_work():
    tasks = [
        AgentTask("a", "fail"),
        AgentTask("c", "ok", ("b",)),
        AgentTask("b", "ok", ("a",)),
        AgentTask("d", "ok"),
    ]
    result = run_orchestrator(tasks, {"ok": ok, "fail": lambda c: {"success": False}})
    assert result["states"] == {"a": "failed", "b": "blocked", "c": "blocked", "d": "completed"}
    assert not result["success"] and not result["budget_exhausted"]


@pytest.mark.parametrize("response", [None, {}, {"success": "yes"}])
def test_malformed_specialist_response(response):
    result = run_orchestrator([AgentTask("a", "r")], {"r": lambda c: response})
    assert result["states"]["a"] == "failed"


def test_runner_exception_does_not_leak_message():
    def fail(context):
        raise OSError("secret token")

    result = run_orchestrator([AgentTask("a", "r")], {"r": fail})
    assert result["results"]["a"]["error_type"] == "OSError"
    assert "secret token" not in str(result)


def test_out_of_order_and_duplicate_delegation_rejected():
    class Planner:
        def __init__(self):
            self.ids = iter(["b", "a", "a", "b"])

        def next_action(self, context):
            return {"tool": "delegate", "arguments": {"task_id": next(self.ids)}}

    result = run_orchestrator(
        [AgentTask("a", "r"), AgentTask("b", "r", ("a",))], {"r": ok}, Planner()
    )
    assert result["success"]
    assert [e["status"] for e in result["trace"]] == [
        "rejected",
        "completed",
        "rejected",
        "completed",
    ]


def test_exhaustion_leaves_pending_work_visible():
    result = run_orchestrator(
        [AgentTask("a", "r"), AgentTask("b", "r", ("a",))], {"r": ok}, max_calls=1
    )
    assert result["budget_exhausted"] and result["states"]["b"] == "pending"


@pytest.mark.parametrize(
    "tasks",
    [
        [],
        [AgentTask("a", "missing")],
        [AgentTask("a", "r"), AgentTask("a", "r")],
        [AgentTask("a", "r", ("missing",))],
        [AgentTask("a", "r", ("b",)), AgentTask("b", "r", ("a",))],
    ],
)
def test_invalid_graph_fails_before_running(tasks):
    with pytest.raises(ValueError):
        run_orchestrator(tasks, {"r": ok})


@pytest.mark.parametrize("budget", [0, 101, True, 1.5])
def test_invalid_budget(budget):
    with pytest.raises(ValueError):
        run_orchestrator([AgentTask("a", "r")], {"r": ok}, max_calls=budget)


def test_planner_cannot_mutate_ready_allowlist():
    class MutatingPlanner:
        def next_action(self, context):
            context["ready_tasks"].append("b")
            return {"tool": "delegate", "arguments": {"task_id": "b"}}

    result = run_orchestrator(
        [AgentTask("a", "r"), AgentTask("b", "r", ("a",))],
        {"r": ok},
        MutatingPlanner(),
        max_calls=1,
    )
    assert result["states"] == {"a": "pending", "b": "pending"}
    assert result["trace"][0]["status"] == "rejected"
