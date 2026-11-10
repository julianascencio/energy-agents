"""Bounded Quantum Machine Learning Engineer with executable research tools."""

import json
from copy import deepcopy
from datetime import date, datetime, timezone
from importlib.resources import files

from ..connectors import ChatCompletionsPlanner
from ..roles import RoleSpec
from .benchmark import benchmark_forecasts
from .inputs import prepare_dataset, validate_case
from .literature import fetch_arxiv_literature
from .optimization import benchmark_schedule

ROLE = RoleSpec(
    id="career_quantum_ml_engineer", title="Quantum Machine Learning Engineer",
    mandate="Design and evaluate classical, quantum-inspired and hybrid energy research workflows.",
    inputs=("load_case", "experiment_budget", "research_context"),
    tool="prepare_data", output="quantum_ml_research_handoff",
    acceptance="Chronological held-out benchmarks, feasible schedules, provenance and limitations.",
    technology="cross_technology", authority="local_bounded_research_only",
)

TOOLS = ("prepare_data", "benchmark_models", "optimize_schedule", "research_handoff", "finish")


def quantum_context() -> dict:
    """Versioned role skills, neutral responsibility coverage and primary references."""
    return json.loads(files("energy_agents").joinpath(
        "data/quantum_ml/skills.json").read_text(encoding="utf-8"))


class QuantumMLPlanner(ChatCompletionsPlanner):
    """Optional live planner; receives metadata and summaries, never raw hourly loads."""

    @property
    def instruction_override(self):
        return quantum_context()["system_prompt"]


class QuantumMLReplayPlanner:
    """Deterministic tool scheduling for offline reproducibility; not an LLM."""

    def next_action(self, context):
        return {"tool": context["allowed_tools"][0], "arguments": {}}


def research_handoff(forecasts: dict, schedule: dict, *, as_of: str,
                     literature: dict | None = None) -> dict:
    """Build a measured-result handoff plus explicit research and transfer work items."""
    current = date.fromisoformat(as_of)
    context = quantum_context()
    reviewed = date.fromisoformat(context["references_reviewed_on"])
    return {
        "selected_model": forecasts["selected_model"],
        "recommendation": "Retain the validation-selected baseline for a prospective pilot; "
                          "this experiment does not establish quantum advantage.",
        "quantum_advantage_demonstrated": False,
        "literature": {"reviewed_on": reviewed.isoformat(), "as_of": current.isoformat(),
                       "refresh_due": (current - reviewed).days > 90,
                       "references": context["references"],
                       "live_search_performed_by_agent": literature is not None,
                       "recent_metadata": deepcopy(literature)},
        "coverage": context["responsibility_coverage"],
        "handoffs": [
            {"role": "python_ml_engineer", "task": "Review reproducibility, tests, data contracts "
             "and deployment packaging; inspect the current Energy Data Insights capability "
             "manifest before choosing a provider connector. No EDI integration is assumed."},
            {"role": "commercial_asset_manager", "task": "Replace synthetic tariffs and load "
             "stress weights with approved economics; measure value prospectively."},
            {"role": "maintenance_planner", "task": "Review production constraints, scheduling "
             "windows and telemetry availability with the plant engineer."},
        ],
        "pilot_gates": ["Obtain licensed multi-season real load, prices and telemetry latency.",
                        "Use rolling-origin validation and separate sites; preserve a final holdout.",
                        "Add strong boosted-tree, physical and deep-learning baselines.",
                        "Measure training/inference resources, shot noise, device noise and drift.",
                        "Require feasible schedules, documented uncertainty and business review."],
        "business_result": {"scenario_objective_reduction_eur":
                            schedule["scenario_objective_reduction_eur"],
                            "realized_savings": False},
        "limitations": ["Synthetic default data and assumed zero telemetry delay.",
                        "Small simulators, single temporal holdout and limited hyperparameter grid.",
                        "No hardware speedup, peer review, scientific novelty or professional credential.",
                        "Literature metadata is not full-text review, replication or evidence of novelty.",
                        "No autonomous technology transfer or plant deployment.",
                        "Optional live LLM quality is not evaluated by deterministic replay."],
    }


def run_quantum_ml_agent(case: dict, planner=None, *, include_hybrid: bool = False,
                         refresh_literature: bool = False, max_calls: int = 7,
                         as_of: str | None = None) -> dict:
    """Execute trusted local tools in dependency order; reject unauthorized actions.

    Planners can request the next stage, but cannot modify data, budgets, models or
    results. Only the caller enables heavy hybrid training. Outputs are advisory.
    """
    validate_case(case)
    if type(max_calls) is not int or not 1 <= max_calls <= 12:
        raise ValueError("max_calls must be an integer in 1..12")
    if type(include_hybrid) is not bool:
        raise ValueError("include_hybrid must be boolean")
    if type(refresh_literature) is not bool:
        raise ValueError("refresh_literature must be boolean")
    as_of = as_of if as_of is not None else datetime.now(timezone.utc).date().isoformat()
    date.fromisoformat(as_of)
    case = deepcopy(case)
    mode = "scripted_tool_workflow" if planner is None else "caller_supplied_planner"
    planner = planner or QuantumMLReplayPlanner()
    result = {"success": False, "role": ROLE.as_dict(), "mode": mode,
              "classification": case["classification"], "trace": [], "reports": {},
              "execution_authorized": False, "human_review_required": True,
              "include_hybrid": include_hybrid, "refresh_literature": refresh_literature}
    stages = (*TOOLS[:3], "refresh_literature", *TOOLS[3:]) if refresh_literature else TOOLS
    stage, dataset = 0, None
    for step in range(max_calls):
        expected = stages[stage]
        context = {"role": ROLE.as_dict(), "skills": quantum_context()["skills"],
                   "allowed_tools": [expected], "history": deepcopy(result["trace"]),
                   "input_summary": {"classification": case["classification"],
                                     "samples": len(case["records"]), "unit": case["unit"]},
                   "completed_reports": list(result["reports"]),
                   "include_hybrid": include_hybrid}
        try:
            action = planner.next_action(context)
        except Exception as exc:
            result["trace"].append({"step": step, "status": "provider_failed",
                                    "error_type": type(exc).__name__})
            return result
        if (not isinstance(action, dict) or set(action) != {"tool", "arguments"}
                or action.get("tool") != expected or action.get("arguments") != {}):
            result["trace"].append({"step": step, "status": "rejected",
                                    "error": f"Only {expected} with empty arguments is available"})
            continue
        try:
            if expected == "prepare_data":
                dataset = prepare_dataset(case)
                result["reports"]["data"] = {
                    "input_sha256": dataset["input_sha256"],
                    "classification": case["classification"],
                    "provenance": deepcopy(case["provenance"]),
                    "samples": len(case["records"]), "features": ["lag_24h_mw", "lag_48h_mw",
                                                                   "hour_sin", "hour_cos"],
                    "forecast_policy": "24 hourly forecasts at each midnight UTC; zero data delay",
                    "missing_data_policy": "reject; never impute zero"}
            elif expected == "benchmark_models":
                result["reports"]["forecast"] = benchmark_forecasts(
                    dataset, include_hybrid=include_hybrid)
            elif expected == "optimize_schedule":
                result["reports"]["optimization"] = benchmark_schedule(result["reports"]["forecast"])
            elif expected == "refresh_literature":
                result["reports"]["literature"] = fetch_arxiv_literature()
            elif expected == "research_handoff":
                result["reports"]["handoff"] = research_handoff(
                    result["reports"]["forecast"], result["reports"]["optimization"], as_of=as_of,
                    literature=result["reports"].get("literature"))
            else:
                result["success"] = True
        except Exception as exc:
            # Partial output is retained, but never marked as successful.
            result["trace"].append({"step": step, "tool": expected, "status": "tool_failed",
                                    "error_type": type(exc).__name__})
            return result
        result["trace"].append({"step": step, "tool": expected, "status": "completed"})
        if result["success"]:
            return result
        stage += 1
    return result


def quantum_ml_runners(planner=None, *, include_hybrid: bool = False) -> dict:
    """Explicit executable registration for the existing dependency-aware orchestrator."""
    def runner(context):
        return run_quantum_ml_agent(context["payload"], planner, include_hybrid=include_hybrid)
    return {ROLE.id: runner}
