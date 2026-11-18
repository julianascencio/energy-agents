"""Synthetic non-firm load economics, not tariff eligibility or dispatch advice."""

import argparse
import json
import math
from datetime import date
from importlib.resources import files
from pathlib import Path
from urllib.parse import urlsplit

from ..orchestrator import AgentTask, run_orchestrator
from .bess import ROLE, _number
from .tandem import digest


def data_file(name):
    return json.loads(files("energy_agents").joinpath(f"data/nonfirm/{name}.json").read_text())


def reference_case():
    return data_file("case")


def validate_case(c):
    if (c["version"], c["classification"], c["currency"], c["source"]["status"]) != (
        "1.0",
        "synthetic",
        "USD",
        "proposal_not_effective_rule",
    ):
        raise ValueError("Require synthetic USD and explicitly proposed rule")
    s = c["source"]
    url = urlsplit(s["url"])
    if (
        url.scheme != "https"
        or url.netloc != "isonewswire.com"
        or s["publisher"] != "ISO New England"
    ):
        raise ValueError("Primary ISO announcement required")
    if not date.fromisoformat(s["publication_date"]) <= date.fromisoformat(c["as_of"]):
        raise ValueError("Future source")
    if not c["limitations"] or not c["evidence_gaps"]:
        raise ValueError("Explicit limitations and evidence gaps required")
    a = c["assumptions"]
    if a["cash_basis"] != "constant_real_year_end_incremental_before_tax":
        raise ValueError("Real incremental year-end cash required")
    for key in (
        "load_mw",
        "nonfirm_mw",
        "flexible_mw",
        "threshold_usd_mwh",
        "lost_contribution_usd_mwh",
        "restart_usd_event",
        "annual_avoided_firm_cost_usd",
        "annual_flex_opex_usd",
        "flex_capex_usd",
    ):
        _number(a[key], key, upper=1e12)
    if not 0 <= a["nonfirm_mw"] <= a["flexible_mw"] <= a["load_mw"]:
        raise ValueError("Non-firm tranche must be fully curtailable within total load")
    if a["nonfirm_mw"] == 0 and a["annual_avoided_firm_cost_usd"] != 0:
        raise ValueError("No avoided firm-service cost without a non-firm tranche")
    _number(a["discount_rate"], "discount_rate", upper=1)
    if type(a["years"]) is not int or not 1 <= a["years"] <= 50:
        raise ValueError("Horizon must be 1..50 whole years")
    periods = c["periods"]
    if not isinstance(periods, list) or not 1 <= len(periods) <= 8760:
        raise ValueError("Require chronological periods")
    for p in periods:
        _number(p["hours"], "hours", lower=1, upper=8760)
        _number(p["price_usd_mwh"], "price", lower=-10000, upper=100000)
    if not math.isclose(math.fsum(p["hours"] for p in periods), 8760, abs_tol=1e-8, rel_tol=0):
        raise ValueError("Period hours must total 8760")


def screen_nonfirm(c):
    """Fully curtail the non-firm tranche at >= threshold; no make-up work or generator.

    Same energization date and constant load in both options. Consecutive high-price
    periods form one event. A year is a standalone window, initially not curtailed.
    Marginal business contribution excludes electricity. Avoided firm costs are an
    operator-supplied annual equivalent, not an inferred ISO tariff or exemption.
    """
    validate_case(c)
    a = c["assumptions"]
    rows = []
    previous = False
    for i, p in enumerate(c["periods"]):
        active = p["price_usd_mwh"] >= a["threshold_usd_mwh"] and a["nonfirm_mw"] > 0
        energy = a["nonfirm_mw"] * p["hours"] if active else 0
        start = active and not previous
        rows.append(
            {
                "period": i,
                "triggered": active,
                "curtailed_mwh": energy,
                "lost_contribution_usd": energy * a["lost_contribution_usd_mwh"],
                "avoided_energy_cost_usd": energy * p["price_usd_mwh"],
                "restart_cost_usd": a["restart_usd_event"] if start else 0,
                "event_start": start,
            }
        )
        previous = active
    totals = {
        k: math.fsum(r[k] for r in rows)
        for k in (
            "curtailed_mwh",
            "lost_contribution_usd",
            "avoided_energy_cost_usd",
            "restart_cost_usd",
        )
    }
    penalty = (
        totals["lost_contribution_usd"]
        - totals["avoided_energy_cost_usd"]
        + totals["restart_cost_usd"]
    )
    annual = a["annual_avoided_firm_cost_usd"] - a["annual_flex_opex_usd"] - penalty
    factor = math.fsum((1 + a["discount_rate"]) ** (-y) for y in range(1, a["years"] + 1))
    return {
        "classification": "modelled_synthetic",
        "currency": "USD",
        "input_sha256": digest(c),
        "source": c["source"].copy(),
        "periods": rows,
        "annual": totals,
        "events": sum(r["event_start"] for r in rows),
        "baseline_incremental_npv_usd": 0,
        "annual_net_benefit_usd": annual,
        "incremental_npv_usd": annual * factor - a["flex_capex_usd"],
        "break_even_annual_avoided_firm_cost_usd": (
            penalty + a["annual_flex_opex_usd"] + a["flex_capex_usd"] / factor
        ),
        "evidence_gaps": list(c["evidence_gaps"]),
        "limitations": list(c["limitations"]),
        "eligible_for_service": None,
        "dispatch_authorized": False,
        "human_review_required": True,
        "llm": {"executed": False, "cost": None, "latency": None, "tokens": None},
    }


def run_workflow(c, planner=None):
    def evidence(context):
        case = context["payload"]["case"]
        validate_case(case)
        return {
            "success": True,
            "case": case,
            "validation": "schema_not_legal_or_source_validation",
        }

    def finance(context):
        return {"success": True, "report": screen_nonfirm(context["upstream"]["evidence"]["case"])}

    return run_orchestrator(
        [
            AgentTask("evidence", "evidence_contract", payload={"case": c}),
            AgentTask("finance", ROLE.id, dependencies=("evidence",)),
        ],
        {"evidence_contract": evidence, ROLE.id: finance},
        planner,
        max_calls=4,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", type=Path)
    parser.add_argument("--output", type=Path, default=Path("outputs/nonfirm"))
    args = parser.parse_args()
    c = json.loads(args.case.read_text()) if args.case else reference_case()
    run = run_workflow(c)
    if not run["success"] or run["results"]["finance"]["report"] != screen_nonfirm(c):
        raise RuntimeError("Workflow/direct baseline parity failed")
    args.output.mkdir(parents=True, exist_ok=True)
    for name, value in [
        ("inputs", c),
        ("workflow", run),
        ("edi_context", data_file("edi_context")),
    ]:
        (args.output / (name + ".json")).write_text(
            json.dumps(value, indent=2, allow_nan=False) + "\n"
        )
    print(json.dumps(run["results"]["finance"]["report"], indent=2))


if __name__ == "__main__":
    main()
