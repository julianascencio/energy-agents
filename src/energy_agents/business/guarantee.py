"""Advisory bank-guarantee liquidity and cost screen; no banking actions."""

import argparse
import json
from datetime import date
from importlib.resources import files
from pathlib import Path

from ..orchestrator import AgentTask, run_orchestrator
from .bess import ROLE, _number
from .tandem import digest


def data(name):
    return json.loads(files("energy_agents").joinpath(f"data/guarantee/{name}.json").read_text())


def reference_case():
    return data("case")


def validate_case(c):
    if (c["version"], c["currency"], c["classification"]) != ("1.0", "NIS", "synthetic_terms"):
        raise ValueError("Require version 1.0 and explicitly synthetic NIS terms")
    s = c["source"]
    if s["status"] != "announced_estimate_subject_to_approvals" or not s["url"].startswith(
        "https://www.globenewswire.com/"
    ):
        raise ValueError("Require announcement provenance and conditional estimate status")
    if date.fromisoformat(s["publication_date"]) > date.fromisoformat(c["as_of"]):
        raise ValueError("Future source")
    if not c["evidence_gaps"] or not c["limitations"]:
        raise ValueError("Evidence gaps and limitations required")
    a = c["assumptions"]
    _number(s["aggregate_guarantee_nis"], "guarantee", lower=1, upper=1e12)
    for k in (
        "sponsor_share",
        "annual_opportunity_spread",
        "call_probability",
        "net_loss_fraction",
    ):
        _number(a[k], k, upper=1)
    _number(a["years"], "years", lower=1 / 12, upper=10)
    _number(a["initial_liquidity_budget_nis"], "budget", upper=1e12)
    if set(c["offers"]) != {"baseline", "alternative"}:
        raise ValueError("Exactly baseline and alternative required")
    for offer in c["offers"].values():
        for k in ("collateral_fraction", "annual_fee_rate"):
            _number(offer[k], k, upper=1)
        _number(offer["setup_fee_nis"], "setup fee", upper=1e12)


def screen_guarantee(c):
    """Simple undiscounted horizon costs, equal liability and call risk across offers.

    All fees paid upfront; collateral released at expiry unless applied to a call.
    Opportunity spread is net of collateral interest. Expected net call loss is
    separate from peak cash demand: recoveries are assumed later, not immediate.
    """
    validate_case(c)
    a = c["assumptions"]
    g = c["source"]["aggregate_guarantee_nis"] * a["sponsor_share"]
    rows = {}
    for name, o in c["offers"].items():
        collateral = g * o["collateral_fraction"]
        fees = g * o["annual_fee_rate"] * a["years"] + o["setup_fee_nis"]
        opportunity = collateral * a["annual_opportunity_spread"] * a["years"]
        loss = g * a["call_probability"] * a["net_loss_fraction"]
        rows[name] = {
            "guarantee_face_nis": g,
            "restricted_cash_nis": collateral,
            "upfront_fees_nis": fees,
            "opportunity_cost_nis": opportunity,
            "expected_net_call_loss_nis": loss,
            "total_economic_cost_nis": fees + opportunity + loss,
            "initial_cash_required_nis": collateral + fees,
            "initial_budget_feasible": collateral + fees <= a["initial_liquidity_budget_nis"],
            "additional_cash_on_full_call_nis": g - collateral,
            "full_call_cash_including_initial_nis": g + fees,
        }
    b, z = rows["baseline"], rows["alternative"]
    return {
        "classification": "modelled_synthetic_terms",
        "currency": "NIS",
        "input_sha256": digest(c),
        "offers": rows,
        "economic_cost_reduction_nis": b["total_economic_cost_nis"] - z["total_economic_cost_nis"],
        "restricted_cash_released_nis": b["restricted_cash_nis"] - z["restricted_cash_nis"],
        "alternative_break_even_annual_fee_rate": (
            (
                b["upfront_fees_nis"]
                + b["opportunity_cost_nis"]
                - z["opportunity_cost_nis"]
                - c["offers"]["alternative"]["setup_fee_nis"]
            )
            / (g * a["years"])
            if g
            else None
        ),
        "source": c["source"],
        "evidence_gaps": c["evidence_gaps"],
        "limitations": c["limitations"],
        "bank_offer_available": None,
        "connection_approved": False,
        "banking_authorized": False,
        "human_review_required": True,
        "llm": {"executed": False, "cost": None, "tokens": None, "latency": None},
    }


def run_workflow(c, planner=None):
    def evidence(context):
        value = context["payload"]["case"]
        validate_case(value)
        return {"success": True, "case": value, "validation": "schema_not_legal_or_source_truth"}

    def finance(context):
        return {
            "success": True,
            "report": screen_guarantee(context["upstream"]["evidence"]["case"]),
        }

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
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--case", type=Path)
    p.add_argument("--output", type=Path, default=Path("outputs/guarantee"))
    args = p.parse_args()
    c = json.loads(args.case.read_text()) if args.case else reference_case()
    run = run_workflow(c)
    if not run["success"] or run["results"]["finance"]["report"] != screen_guarantee(c):
        raise RuntimeError("Workflow/direct baseline parity failed")
    args.output.mkdir(parents=True, exist_ok=True)
    for name, value in [("inputs", c), ("workflow", run), ("edi_context", data("edi_context"))]:
        (args.output / (name + ".json")).write_text(
            json.dumps(value, indent=2, allow_nan=False) + "\n"
        )
    print(json.dumps(run["results"]["finance"]["report"], indent=2))


if __name__ == "__main__":
    main()
