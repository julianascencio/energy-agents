"""External numerical ownership without planner-controlled code execution."""

import json
from copy import deepcopy

import pytest

pytest.importorskip("numpy")

from energy_agents.quantum_ml.agent import QuantumMLReplayPlanner  # noqa: E402
from energy_agents.quantum_ml.studies import STUDY_STAGES, run_quantum_research_study  # noqa: E402


def study():
    case = {"objective": "Test a trusted external numerical study", "classification": "synthetic",
            "measurements": [1, 2, 3]}

    def callback(context):
        output = {"total": sum(context["case"]["measurements"]),
                  "upstream": list(context["reports"])}
        context["case"]["measurements"].clear()
        context["reports"].clear()
        return output

    return case, {stage: callback for stage in STUDY_STAGES}


def test_isolated_inputs_dependency_order_and_same_role():
    case, callbacks = study()
    original = deepcopy(case)
    run = run_quantum_research_study(case, callbacks)
    assert run["success"] and run["role"]["id"] == "career_quantum_ml_engineer"
    assert not run["execution_authorized"] and run["human_review_required"]
    assert case == original and len(run["trace"]) == 5
    for i, stage in enumerate(STUDY_STAGES):
        assert run["reports"][stage] == {"total": 6, "upstream": list(STUDY_STAGES[:i])}


def test_planner_cannot_skip_stages_inject_arguments_or_read_measurements():
    case, callbacks = study()

    class Repair:
        def next_action(self, context):
            assert "measurements" not in json.dumps(context)
            if not context["history"]:
                return {"tool": "benchmark_methods", "arguments": {"code": "not allowed"}}
            action = QuantumMLReplayPlanner().next_action(context)
            context["completed_reports"].clear()
            return action

    run = run_quantum_research_study(case, callbacks, Repair())
    assert run["success"] and run["trace"][0]["status"] == "rejected"
    assert not run_quantum_research_study(case, callbacks, max_calls=1)["success"]


@pytest.mark.parametrize("output", [{}, [], {"success": False}, {"success": "yes"},
                                     {"score": float("nan")}, {"data": object()}])
def test_bad_or_failed_external_results_never_complete(output):
    case, callbacks = study()
    callbacks["benchmark_methods"] = lambda context: output
    run = run_quantum_research_study(case, callbacks)
    assert not run["success"] and set(run["reports"]) == {"inspect_evidence"}
    assert run["trace"][-1]["status"] == "tool_failed"


def test_failure_does_not_leak_exception_secrets():
    case, callbacks = study()

    def broken(context):
        raise RuntimeError("secret")

    callbacks["benchmark_methods"] = broken
    run = run_quantum_research_study(case, callbacks)
    assert not run["success"] and "secret" not in json.dumps(run)


def test_invalid_registration_and_budget():
    case, callbacks = study()
    for bad in ({}, {**callbacks, "shell": lambda c: {}}, {**callbacks, "inspect_evidence": "code"}):
        with pytest.raises(ValueError):
            run_quantum_research_study(case, bad)
    with pytest.raises(ValueError):
        run_quantum_research_study(case, callbacks, max_calls=True)
