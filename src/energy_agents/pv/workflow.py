"""Bounded professional-role orchestration over a shared versioned case."""

import hashlib
import json
from copy import deepcopy
from dataclasses import dataclass

from ..knowledge import EnergyDataInsightsAgent
from ..roles import PV_ROLES
from .inputs import validate_case
from .methods import TOOLS, review_evidence


def case_digest(case):
    return hashlib.sha256(json.dumps(case, sort_keys=True, allow_nan=False).encode()).hexdigest()


@dataclass
class PVReplayPlanner:
    """Offline reference policy, not an LLM or an autonomous diagnosis system."""

    def next_action(self, context):
        for role in context["roles"]:
            if role["output"] not in context["reports"]:
                return {"tool": role["tool"], "arguments": {}}
        return {"tool": "finish", "arguments": {}}


def run_pv_workflow(
    case,
    *,
    mode="role_team",
    planners=None,
    max_calls=12,
    repository_query="PV performance degradation maintenance examples",
    knowledge_agent=None,
):
    """Run a deterministic baseline, one planner, or five bounded role planners.

    ``planners`` maps role IDs (or ``single_agent``) to Planner-compatible objects.
    A missing mapping uses the labelled scripted replay. Planner contexts are copies;
    only allowlisted deterministic tools can produce reports. The total call budget
    includes finish and is shared by the team. Any rejected action stops the run.
    The Technical Asset Manager receives source-backed repository context from a
    pinned offline catalogue. Set repository_query=None to disable retrieval.
    Repository suggestions are separate from the plant's numerical evidence.
    """
    if mode not in {"deterministic", "single_agent", "role_team"}:
        raise ValueError("Unknown execution mode")
    if isinstance(max_calls, bool) or not isinstance(max_calls, int) or not 1 <= max_calls <= 100:
        raise ValueError("max_calls must be an integer in 1..100")
    original = deepcopy(case)
    validate_case(original)
    planners = dict(planners or {})
    allowed_ids = {r.id for r in PV_ROLES} if mode == "role_team" else {"single_agent"}
    if (mode == "deterministic" and planners) or set(planners) - allowed_ids:
        raise ValueError("Planner keys do not match the execution mode")
    state = {
        "schema_version": "1.0",
        "case": original,
        "case_sha256": case_digest(original),
        "mode": mode,
        "reports": {},
        "trace": [],
        "success": False,
        "authority": "advisory_only",
        "planner_calls": 0,
        "tool_calls": 0,
        "execution": "external_planner" if planners else "deterministic_or_scripted",
    }
    state["repository_knowledge"] = (
        (knowledge_agent or EnergyDataInsightsAgent()).context(repository_query)
        if repository_query is not None
        else None
    )
    reports = state["reports"]
    if mode == "deterministic":
        for role in PV_ROLES:
            reports[role.output] = TOOLS[role.tool](original, reports)
            state["tool_calls"] += 1
            state["trace"].append({"role": role.id, "tool": role.tool, "status": "applied"})
    else:
        groups = (
            [(r.id, (r,)) for r in PV_ROLES]
            if mode == "role_team"
            else [("single_agent", PV_ROLES)]
        )
        for owner, roles in groups:
            planner = planners.get(owner, PVReplayPlanner())
            completed = False
            while state["planner_calls"] < max_calls:
                event = {"role": owner, "status": "started"}
                state["trace"].append(event)
                state["planner_calls"] += 1
                try:
                    action = planner.next_action(
                        deepcopy(
                            {
                                "case": original,
                                "reports": reports,
                                "roles": [r.as_dict() for r in roles],
                                "allowed_tools": [r.tool for r in roles] + ["finish"],
                                "history": state["trace"][:-1],
                                "authority": "advisory_only",
                                "repository_knowledge": state["repository_knowledge"]
                                if owner in {"technical_asset_manager", "single_agent"}
                                else None,
                            }
                        )
                    )
                    if not isinstance(action, dict) or set(action) != {"tool", "arguments"}:
                        raise ValueError("Expected exactly tool and arguments")
                    if action["arguments"] != {}:
                        raise ValueError("PV tools accept no planner-supplied arguments")
                    tool = action["tool"]
                    event["tool"] = tool
                    if tool == "finish":
                        if any(r.output not in reports for r in roles):
                            raise ValueError("Cannot finish before role deliverables exist")
                        event["status"] = "accepted"
                        completed = True
                        break
                    role = next((r for r in roles if r.tool == tool), None)
                    if role is None:
                        raise ValueError("Tool outside role authority")
                    if role.output in reports:
                        raise ValueError("Role deliverable already exists")
                    if any(key != "case" and key not in reports for key in role.inputs):
                        raise ValueError("Missing prerequisite reports")
                    reports[role.output] = TOOLS[tool](original, reports)
                    state["tool_calls"] += 1
                    event["status"] = "applied"
                except (ValueError, KeyError, TypeError, AttributeError, OSError) as exc:
                    event.update(status="rejected", error=str(exc))
                    state["review"] = {"passed": False, "issues": [str(exc)]}
                    return state
            if not completed:
                state["review"] = {"passed": False, "issues": ["Planner call budget exhausted"]}
                return state
    state["review"] = review_evidence(original, reports)
    state["success"] = state["review"]["passed"]
    return state
