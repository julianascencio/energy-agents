"""Advisory BESS revenue concentration screening; no dispatch or trade execution."""

import json
import math
from copy import deepcopy
from importlib.resources import files

from ..roles import RoleSpec

ROLE = RoleSpec(
    "project_finance_analyst",
    "Project Finance Analyst",
    "Challenge flat battery revenue extrapolation with explicit downside scenarios.",
    ("case",),
    "stress_revenues",
    "investment_screen",
    "Preserve source/model distinctions, reconcile cash flows and require human review.",
    technology="bess",
)


def reference_case():
    return json.loads(
        files("energy_agents").joinpath("data/business/bess_saturation.json").read_text()
    )


def _number(value, name, lower=0, upper=None):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{name} must be finite numeric input")
    if value < lower or (upper is not None and value > upper):
        raise ValueError(f"{name} outside supported range")


def validate_case(case):
    if case["currency"] != "EUR" or not case["case_id"]:
        raise ValueError("This screen requires an identified EUR case")
    source, a = case["source"], case["assumptions"]
    if not source["url"].startswith("https://") or not source["classification"]:
        raise ValueError("Source provenance is required")
    for key in ("gross_eur_per_mw_year", "ancillary_eur_per_mw_year"):
        _number(source[key], key)
    if source["ancillary_eur_per_mw_year"] > source["gross_eur_per_mw_year"]:
        raise ValueError("Ancillary revenue exceeds total index")
    for key in ("power_mw", "capex_eur", "annual_fixed_cost_eur_per_mw"):
        _number(a[key], key)
    if a["power_mw"] <= 0 or a["duration_hours"] != 2:
        raise ValueError("Positive MW and two-hour duration required for this source index")
    if isinstance(a["years"], bool) or not isinstance(a["years"], int) or not 1 <= a["years"] <= 50:
        raise ValueError("years must be an integer in 1..50")
    for key in ("availability", "annual_revenue_derating", "discount_rate"):
        _number(a[key], key, upper=1)
    if not a["classification"] or not a["cash_flow_basis"] or not a["cost_scope"]:
        raise ValueError("Scenario classification, cash-flow and cost basis are required")
    if "flat_index" not in case["scenarios"] or len(case["scenarios"]) < 2:
        raise ValueError("Supply flat_index and at least one stress scenario")
    for name, scenario in case["scenarios"].items():
        for key in ("ancillary_retention", "other_retention"):
            if len(scenario[key]) != a["years"]:
                raise ValueError("Retention vectors must match the horizon")
            for value in scenario[key]:
                _number(value, key, upper=1)
            if name == "flat_index" and any(value != 1 for value in scenario[key]):
                raise ValueError("flat_index requires all market retention factors equal to one")


def stress_revenues(case):
    """Value each explicit annual revenue path in constant-real EUR.

    Published gross index already embeds charging economics and efficiency.
    Residual non-ancillary income is derived as total minus ancillary; it is not
    relabelled as pure arbitrage. Uniform availability/derating is a simplification.
    """
    validate_case(case)
    source, a = case["source"], case["assumptions"]
    ancillary = source["ancillary_eur_per_mw_year"]
    other = source["gross_eur_per_mw_year"] - ancillary
    scenarios = {}
    for name, path in case["scenarios"].items():
        rows = []
        for i in range(a["years"]):
            scale = a["power_mw"] * a["availability"] * (1 - a["annual_revenue_derating"]) ** i
            anc = ancillary * path["ancillary_retention"][i] * scale
            nonanc = other * path["other_retention"][i] * scale
            costs = a["annual_fixed_cost_eur_per_mw"] * a["power_mw"]
            cash = anc + nonanc - costs
            rows.append(
                {
                    "year": i + 1,
                    "ancillary_eur": anc,
                    "other_eur": nonanc,
                    "fixed_cost_eur": costs,
                    "cash_flow_eur": cash,
                    "discounted_cash_eur": cash / (1 + a["discount_rate"]) ** (i + 1),
                }
            )
        pv = math.fsum(row["discounted_cash_eur"] for row in rows)
        scenarios[name] = {
            "annual": rows,
            "npv_eur": pv - a["capex_eur"],
            "zero_npv_upfront_budget_eur": pv,
            "cash_flows_eur": [-a["capex_eur"]] + [r["cash_flow_eur"] for r in rows],
        }
    baseline = scenarios["flat_index"]["npv_eur"]
    for row in scenarios.values():
        row["npv_reduction_vs_flat_eur"] = baseline - row["npv_eur"]
    return {
        "scenarios": scenarios,
        "ancillary_share": ancillary / source["gross_eur_per_mw_year"]
        if source["gross_eur_per_mw_year"]
        else 0.0,
        "source_url": source["url"],
        "source_classification": source["classification"],
        "scenario_classification": a["classification"],
        "currency": "EUR",
        "realised_revenue": None,
        "limitations": [
            "Screening scenarios, not project forecasts or investment advice",
            "No causal saturation model or new dispatch optimisation",
            "No independently measured agent advantage",
        ],
    }


def review_screen(case, screen):
    """Recompute accounting and reject altered findings or provenance labels."""
    expected = stress_revenues(case)
    return {
        "passed": screen == expected,
        "scope": "Deterministic contract replay; source truth not independently verified",
    }


class BESSReplayPlanner:
    """Offline reference policy; not an LLM."""

    def next_action(self, context):
        if "screen" not in context["reports"]:
            return {"tool": "stress_revenues", "arguments": {}}
        if "review" not in context["reports"]:
            return {"tool": "review_screen", "arguments": {}}
        return {"tool": "finish", "arguments": {}}


def run_bess_agent(case, planner=None, *, max_calls=3):
    """Run a bounded finance-role skill with no execution or mutation tools."""
    validate_case(case)
    if isinstance(max_calls, bool) or not isinstance(max_calls, int) or not 1 <= max_calls <= 20:
        raise ValueError("max_calls must be 1..20")
    original = deepcopy(case)
    result = {
        "success": False,
        "case": original,
        "role": ROLE.as_dict(),
        "reports": {},
        "trace": [],
        "authority": "advisory_only",
        "decision": "human_review_required",
        "planner": "external" if planner else "scripted_reference",
        "live_llm_verified": False,
    }
    planner = planner or BESSReplayPlanner()
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
                        "allowed_tools": ["stress_revenues", "review_screen", "finish"],
                    }
                )
            )
            if (
                not isinstance(action, dict)
                or set(action) != {"tool", "arguments"}
                or action["arguments"] != {}
            ):
                raise ValueError("Expected tool and empty arguments; case edits are not allowed")
            tool = action["tool"]
            event["tool"] = tool
            reports = result["reports"]
            if tool == "stress_revenues" and not reports:
                reports["screen"] = stress_revenues(original)
            elif tool == "review_screen" and set(reports) == {"screen"}:
                reports["review"] = review_screen(original, reports["screen"])
            elif tool == "finish" and "review" in reports and reports["review"]["passed"]:
                result["success"] = True
                event["status"] = "accepted"
                return result
            else:
                raise ValueError("Tool forbidden, repeated, or prerequisite missing")
            event["status"] = "applied"
        except (ValueError, TypeError, KeyError, AttributeError, OSError) as exc:
            event.update(status="rejected", error=str(exc))
            return result
    result["trace"].append({"status": "rejected", "error": "Call budget exhausted"})
    return result
