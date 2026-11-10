"""Quantum ML Engineer orchestration for explicitly registered scientific study tools.

Numerical methods stay in their owning library. Callbacks are trusted host Python
code, not a sandbox for model-generated code or commands.
"""

import json
from collections.abc import Callable, Mapping
from copy import deepcopy

from .agent import ROLE, QuantumMLReplayPlanner, quantum_context

STUDY_STAGES = ("inspect_evidence", "benchmark_methods", "assess_sensitivity", "prepare_handoff")


def run_quantum_research_study(
    case: dict,
    study_tools: Mapping[str, Callable[[dict], dict]],
    planner=None,
    *,
    max_calls: int = 7,
) -> dict:
    """Execute four registered callbacks in dependency order, then finish.

    ``case`` must be JSON-serializable with a nonempty objective and classification
    (synthetic, observed or mixed). ``study_tools`` maps exactly STUDY_STAGES to
    trusted callables. Each receives isolated case/reports copies and must return
    a nonempty JSON object; an explicit boolean success=False fails the stage.

    The planner gets only objective, classification, role, stage names and history,
    not raw measurements or numerical reports. It cannot supply tool arguments,
    code, imports or URLs. The host alone chooses callbacks. Successful execution
    is not scientific validation, model superiority or deployment authorization.
    """
    if not isinstance(case, dict) or not isinstance(case.get("objective"), str):
        raise ValueError("A study case with an objective is required")
    if not case["objective"].strip() or case.get("classification") not in {
        "synthetic", "observed", "mixed"
    }:
        raise ValueError("Declare a nonempty objective and evidence classification")
    json.dumps(case, allow_nan=False)
    if not isinstance(study_tools, Mapping) or set(study_tools) != set(STUDY_STAGES):
        raise ValueError("Register exactly the four declared study stages")
    if not all(callable(callback) for callback in study_tools.values()):
        raise ValueError("Study tools must be trusted callables")
    if type(max_calls) is not int or not 1 <= max_calls <= 12:
        raise ValueError("max_calls must be an integer in 1..12")
    case, callbacks = deepcopy(case), dict(study_tools)
    mode = "scripted_tool_workflow" if planner is None else "caller_supplied_planner"
    planner = planner or QuantumMLReplayPlanner()
    result = {"success": False, "role": ROLE.as_dict(), "mode": mode,
              "classification": case["classification"], "reports": {}, "trace": [],
              "human_review_required": True, "execution_authorized": False,
              "validation": "registered_tool_execution_and_protocol_only"}
    stages = (*STUDY_STAGES, "finish")
    stage = 0
    for step in range(max_calls):
        expected = stages[stage]
        context = {"role": ROLE.as_dict(), "skills": quantum_context()["skills"],
                   "objective": case["objective"], "classification": case["classification"],
                   "allowed_tools": [expected], "completed_reports": list(result["reports"]),
                   "history": deepcopy(result["trace"])}
        try:
            action = planner.next_action(context)
        except Exception as exc:
            result["trace"].append({"step": step, "status": "provider_failed",
                                    "error_type": type(exc).__name__})
            return result
        if (not isinstance(action, dict) or set(action) != {"tool", "arguments"}
                or action["tool"] != expected or action["arguments"] != {}):
            result["trace"].append({"step": step, "status": "rejected",
                                    "error": f"Only {expected} with empty arguments is available"})
            continue
        if expected == "finish":
            result["trace"].append({"step": step, "tool": expected, "status": "completed"})
            result["success"] = True
            return result
        try:
            output = callbacks[expected]({"case": deepcopy(case),
                                          "reports": deepcopy(result["reports"])})
            if not isinstance(output, dict) or not output:
                raise ValueError("A nonempty JSON report is required")
            if "success" in output and type(output["success"]) is not bool:
                raise ValueError("success must be boolean when present")
            if output.get("success") is False:
                raise ValueError("Study tool reported failure")
            json.dumps(output, allow_nan=False)
            result["reports"][expected] = deepcopy(output)
        except Exception as exc:
            result["trace"].append({"step": step, "tool": expected, "status": "tool_failed",
                                    "error_type": type(exc).__name__})
            return result
        result["trace"].append({"step": step, "tool": expected, "status": "completed"})
        stage += 1
    return result
