"""Bounded Project Controls Engineer skill for commissioning acceleration screens."""

import argparse
import hashlib
import itertools
import json
import math
from copy import deepcopy
from importlib.resources import files
from pathlib import Path

from .roles import RoleSpec

ROLE = RoleSpec(
    "project_controls_engineer",
    "Project Controls Engineer",
    "Identify dependency-aware commissioning options with positive expected net benefit.",
    ("case",),
    "rank_acceleration",
    "schedule_screen",
    "Respect minimum durations and budget; compare complete packages, retaining no-action baseline.",
    technology="wind",
    authority="advisory_only",
)


def reference_case():
    return json.loads(files("energy_agents").joinpath("data/commissioning/case.json").read_text())


def number(value, name, *, minimum=None, maximum=None):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{name} must be finite numeric input")
    if minimum is not None and value < minimum or maximum is not None and value > maximum:
        raise ValueError(f"{name} outside permitted range")


def validate(case):
    if not case.get("case_id") or not case.get("evidence_kind") or not case.get("limitations"):
        raise ValueError("Identity, evidence classification and limitations required")
    if not case["news"]["url"].startswith("https://"):
        raise ValueError("Cited news context required")
    tasks = case["tasks"]
    if not 1 <= len(tasks) <= 50 or len(case["options"]) > 12:
        raise ValueError("Screen limited to 1..50 tasks and at most 12 options")
    ids = [t["id"] for t in tasks]
    if any(not isinstance(i, str) or not i for i in ids) or len(set(ids)) != len(ids):
        raise ValueError("Task IDs must be unique nonempty strings")
    for task in tasks:
        number(task["minimum_days"], "minimum_days", minimum=0)
        number(task["duration_days"], "duration_days", minimum=task["minimum_days"])
        if len(set(task["dependencies"])) != len(task["dependencies"]) or any(
            d not in ids for d in task["dependencies"]
        ):
            raise ValueError("Unknown or duplicate dependency")
    seen = set()
    lookup = {t["id"]: t for t in tasks}
    for option in case["options"]:
        if not option["id"] or option["id"] in seen or option["task"] not in lookup:
            raise ValueError("Invalid option identity or target")
        seen.add(option["id"])
        task = lookup[option["task"]]
        number(option["cost_eur"], "cost_eur", minimum=0)
        number(
            option["new_duration_days"],
            "new_duration_days",
            minimum=task["minimum_days"],
            maximum=task["duration_days"],
        )
    e = case["economics"]
    for key in ("power_mw", "variable_cost_eur_per_mwh", "budget_eur"):
        number(e[key], key, minimum=0)
    for key in ("capacity_factor", "availability"):
        number(e[key], key, minimum=0, maximum=1)
    number(e["price_eur_per_mwh"], "price")  # negative prices remain valid
    schedule(tasks)  # reject cycles before running any package


def schedule(tasks, durations=None):
    """Earliest start/finish of a dependency DAG, allowing parallel independent tasks."""
    durations = durations or {}
    pending = {t["id"]: t for t in tasks}
    result = {}
    while pending:
        ready = sorted(
            key for key, t in pending.items() if all(d in result for d in t["dependencies"])
        )
        if not ready:
            raise ValueError("Cyclic or unresolved task dependencies")
        for key in ready:
            task = pending.pop(key)
            start = max((result[d]["finish_day"] for d in task["dependencies"]), default=0.0)
            result[key] = {
                "start_day": start,
                "finish_day": start + durations.get(key, task["duration_days"]),
            }
    return {"tasks": result, "completion_day": max(r["finish_day"] for r in result.values())}


def rank_acceleration(case):
    """Enumerate feasible option packages, including no action; no greedy double counting."""
    validate(case)
    baseline = schedule(case["tasks"])
    e = case["economics"]
    daily_energy = e["power_mw"] * e["capacity_factor"] * e["availability"] * 24
    daily_margin = daily_energy * (e["price_eur_per_mwh"] - e["variable_cost_eur_per_mwh"])
    packages = []
    for n in range(len(case["options"]) + 1):
        for options in itertools.combinations(case["options"], n):
            # Competing alternatives on the same task cannot be purchased together.
            if len({o["task"] for o in options}) != len(options):
                continue
            cost = math.fsum(o["cost_eur"] for o in options)
            if cost > e["budget_eur"]:
                continue
            plan = schedule(case["tasks"], {o["task"]: o["new_duration_days"] for o in options})
            days = baseline["completion_day"] - plan["completion_day"]
            packages.append(
                {
                    "options": sorted(o["id"] for o in options),
                    "schedule": plan,
                    "days_saved": days,
                    "cost_eur": cost,
                    "additional_energy_mwh": days * daily_energy,
                    "gross_contribution_eur": days * daily_margin,
                    "net_benefit_eur": days * daily_margin - cost,
                }
            )
    packages.sort(key=lambda p: (-p["net_benefit_eur"], p["cost_eur"], p["options"]))
    return {
        "baseline": baseline,
        "packages": packages,
        "recommended_package": packages[0],
        "daily_energy_mwh": daily_energy,
        "daily_contribution_eur": daily_margin,
        "evidence_kind": case["evidence_kind"],
        "news_url": case["news"]["url"],
        "limitations": deepcopy(case["limitations"]),
        "decision": "human_review_required",
    }


class CommissioningReplayPlanner:
    """Scripted reference policy, not an LLM benchmark."""

    def next_action(self, context):
        tool = "finish" if context["reports"] else "rank_acceleration"
        return {"tool": tool, "arguments": {}}


def run_commissioning_agent(case, planner=None, *, max_calls=2):
    """Planner chooses allowlisted tool; acceptance rechecks all findings locally."""
    validate(case)
    if isinstance(max_calls, bool) or not isinstance(max_calls, int) or not 1 <= max_calls <= 10:
        raise ValueError("max_calls must be an integer in 1..10")
    original = deepcopy(case)
    result = {
        "success": False,
        "case": original,
        "role": ROLE.as_dict(),
        "reports": {},
        "trace": [],
        "authority": "advisory_only",
        "planner": "external" if planner else "scripted_reference",
    }
    planner = planner or CommissioningReplayPlanner()
    for step in range(max_calls):
        event = {"step": step, "status": "started"}
        result["trace"].append(event)
        try:
            action = planner.next_action(
                deepcopy(
                    {
                        "case": original,
                        "role": ROLE.as_dict(),
                        "reports": result["reports"],
                        "allowed_tools": ["rank_acceleration", "finish"],
                    }
                )
            )
            if (
                not isinstance(action, dict)
                or set(action) != {"tool", "arguments"}
                or action["arguments"] != {}
            ):
                raise ValueError("Expected a tool and empty arguments")
            event["tool"] = action["tool"]
            if action["tool"] == "rank_acceleration" and not result["reports"]:
                result["reports"]["screen"] = rank_acceleration(original)
                event["status"] = "applied"
            elif action["tool"] == "finish" and result["reports"]:
                result["success"] = result["reports"]["screen"] == rank_acceleration(original)
                event["status"] = "accepted" if result["success"] else "rejected"
                return result
            else:
                raise ValueError("Forbidden/repeated tool or missing prerequisite")
        except (ValueError, KeyError, TypeError, AttributeError, OSError) as exc:
            event.update(status="rejected", error=str(exc))
            return result
    result["trace"].append({"status": "rejected", "error": "Call budget exhausted"})
    return result


def export(output):
    case = reference_case()
    run = run_commissioning_agent(case)
    sensitivity = []
    for price in (50, 75, 100):
        changed = deepcopy(case)
        changed["economics"]["price_eur_per_mwh"] = price
        sensitivity.append(
            {"price_eur_per_mwh": price, "best": rank_acceleration(changed)["recommended_package"]}
        )
    report = {
        "run": run,
        "sensitivity": sensitivity,
        "baseline_parity": run["reports"]["screen"] == rank_acceleration(case),
        "live_llm": "not_run",
        "llm_cost": None,
        "realised_savings": None,
    }
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for name, value in {"case.json": case, "results.json": report}.items():
        raw = (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
        (output / name).write_bytes(raw)
        manifest[name] = hashlib.sha256(raw).hexdigest()
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="outputs/wind_commissioning")
    args = parser.parse_args()
    report = export(args.output)
    if not report["run"]["success"] or not report["baseline_parity"]:
        raise SystemExit("Validation failed")
    print(json.dumps(report["run"]["reports"]["screen"]["recommended_package"], indent=2))


if __name__ == "__main__":
    main()
