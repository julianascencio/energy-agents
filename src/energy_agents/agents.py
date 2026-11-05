"""Provider-independent agent loop with bounded calls and complete local traces.

The offline replay is a scripted policy, not an LLM or a measured agent benchmark.
"""

from copy import deepcopy
from dataclasses import dataclass
from typing import Protocol

from .methods import GLAZING, active_field, edit_lighting, edit_windows, number, verify_task


class Planner(Protocol):
    def next_action(self, context: dict) -> dict:
        """Return {tool: name, arguments: mapping}; use finish to request validation."""
        ...


@dataclass
class ReplayPlanner:
    """Successful deterministic reference policy for CI and offline demonstrations."""

    def next_action(self, context):
        model, task, surface = context["model"], context["task"], context["surface"]
        if surface == "domain":
            if context["step"] == 0:
                return {
                    "tool": "edit_windows" if task == "windows" else "edit_lighting",
                    "arguments": {},
                }
            return {"tool": "finish", "arguments": {}}
        kind = GLAZING if task == "windows" else "Lights"
        names = list(model[kind])
        step = context["step"]
        if step >= len(names):
            return {"tool": "finish", "arguments": {}}
        name = names[step]
        field = "u_factor" if task == "windows" else active_field(model[kind][name])
        value = 1.5 if task == "windows" else context["original"][kind][name][field] * 0.7
        return {
            "tool": "set_field",
            "arguments": {"object_type": kind, "name": name, "field": field, "value": value},
        }


def run_agent(model, task, surface, planner=None, *, max_attempts=3, max_calls=20):
    """Run edits on isolated copies, committing only after task validation.

    Failed attempts restart from the original, preventing repeated 30% reductions.
    max_calls includes finish, applies per attempt; errors remain in the trace.
    """
    if task not in {"windows", "lighting"} or surface not in {"domain", "primitive"}:
        raise ValueError("Supported tasks: windows/lighting; surfaces: domain/primitive")
    if not 1 <= max_attempts <= 3 or not 1 <= max_calls <= 100:
        raise ValueError("Budgets must be 1..3 attempts and 1..100 calls")
    planner = planner or ReplayPlanner()
    original, trace = deepcopy(model), []
    for attempt in range(max_attempts):
        candidate = deepcopy(original)
        for step in range(max_calls):
            event = {"attempt": attempt + 1, "step": step, "status": "started"}
            trace.append(event)
            try:
                action = planner.next_action(
                    {
                        "model": deepcopy(candidate),
                        "original": deepcopy(original),
                        "task": task,
                        "surface": surface,
                        "attempt": attempt + 1,
                        "step": step,
                        "history": deepcopy(trace[:-1]),
                    }
                )
                event["action"] = deepcopy(action)
                tool, args = action["tool"], action.get("arguments", {})
                if tool == "finish":
                    verify_task(original, candidate, task)
                    event["status"] = "accepted"
                    return {
                        "success": True,
                        "model": candidate,
                        "trace": trace,
                        "evidence": "local task postconditions; no energy simulation",
                    }
                if surface == "domain" and tool == "edit_windows" and task == "windows":
                    candidate = edit_windows(candidate, **args)
                elif surface == "domain" and tool == "edit_lighting" and task == "lighting":
                    candidate = edit_lighting(candidate, **args)
                elif surface == "primitive" and tool == "set_field":
                    kind, name, field = args["object_type"], args["name"], args["field"]
                    if kind not in {GLAZING, "Lights"}:
                        raise ValueError("Object type is outside the edit allowlist")
                    obj = candidate[kind][name]
                    allowed = {"u_factor"} if kind == GLAZING else {active_field(obj)}
                    if field not in allowed:
                        raise ValueError("Field is outside the edit allowlist")
                    obj[field] = number(args["value"], positive=kind == GLAZING)
                else:
                    raise ValueError("Tool is not available for this task and surface")
                event["status"] = "applied"
            except (ValueError, KeyError, TypeError, AttributeError) as exc:
                event.update(status="rejected", error=str(exc))
                break
        else:
            trace.append(
                {"attempt": attempt + 1, "status": "rejected", "error": "Call budget exhausted"}
            )
    return {
        "success": False,
        "model": original,
        "trace": trace,
        "evidence": "rejected; original model preserved",
    }
