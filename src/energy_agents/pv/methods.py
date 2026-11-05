"""Deterministic, advisory-only tools shared by all execution modes."""

from math import fsum, isclose


def envelope(case, data, refs, limitations):
    return {
        "data": data,
        "evidence_ids": sorted(set(refs)),
        "evidence_kinds": sorted({case["evidence"][ref]["kind"] for ref in refs}),
        "verification": "not_independently_verified",
        "limitations": limitations,
    }


def assess_performance(case, reports):
    rows, excluded, refs = [], [], []
    for row in case["days"]:
        refs.extend(row["evidence_ids"].values())
        if row["actual_mwh"] is None:
            excluded.append(row["date"])
            continue
        delta = row["expected_mwh"] - row["actual_mwh"]
        rows.append(
            {"date": row["date"], "deficit_mwh": max(0.0, delta), "surplus_mwh": max(0.0, -delta)}
        )
    valid = [row for row in case["days"] if row["actual_mwh"] is not None]
    return envelope(
        case,
        {
            "daily": rows,
            "excluded_dates": excluded,
            "coverage_fraction": len(valid) / len(case["days"]),
            "expected_mwh": fsum(r["expected_mwh"] for r in valid),
            "actual_mwh": fsum(r["actual_mwh"] for r in valid),
            "deficit_mwh": fsum(r["deficit_mwh"] for r in rows),
            "surplus_mwh": fsum(r["surplus_mwh"] for r in rows),
        },
        refs,
        [
            "Expected energy is an input baseline, not ground truth.",
            "Missing actual energy is excluded from both sides of the comparison.",
        ],
    )


def assess_reliability(case, reports):
    losses = {r["date"]: r["deficit_mwh"] for r in reports["performance"]["data"]["daily"]}
    groups = {"equipment_fault": [], "curtailment": [], "unresolved": []}
    refs = []
    for row in case["days"]:
        if row["date"] not in losses:
            continue
        category = row["event"] if row["event"] != "none" else "unresolved"
        groups[category].append(losses[row["date"]])
        refs.extend(row["evidence_ids"].values())
    return envelope(
        case,
        {f"{key}_mwh": fsum(values) for key, values in groups.items()},
        refs,
        [
            "Daily event association does not establish root cause or causal loss.",
            "Overlapping events require interval-level reconciliation before ingestion.",
        ],
    )


def assess_commercial(case, reports):
    losses = {r["date"]: r["deficit_mwh"] for r in reports["performance"]["data"]["daily"]}
    assumptions = case["assumptions"]
    total, fault = [], []
    refs = [assumptions["evidence_id"]]
    for row in case["days"]:
        if row["date"] not in losses:
            continue
        value = losses[row["date"]] * row["price_per_mwh"]
        total.append(value)
        if row["event"] == "equipment_fault":
            fault.append(value)
        refs.extend(row["evidence_ids"].values())
    gross = fsum(fault) * assumptions["recovery_fraction"]
    return envelope(
        case,
        {
            "currency": case["currency"],
            "historical_deficit_value": fsum(total),
            "conditional_recovery_mwh": reports["reliability"]["data"]["equipment_fault_mwh"]
            * assumptions["recovery_fraction"],
            "conditional_gross_value": gross,
            "intervention_cost": assumptions["intervention_cost"],
            "conditional_net_value": gross - assumptions["intervention_cost"],
            "scenario_description": assumptions["scenario_description"],
        },
        refs,
        [
            "Signed energy value only; negative prices are preserved.",
            "No imbalance, compensation, availability guarantee, tax or PPA settlement model.",
            "Recovery is conditional on recurrence and repair effectiveness, not a forecast.",
        ],
    )


def plan_maintenance(case, reports):
    reliability = reports["reliability"]["data"]
    actions = []
    if reliability["equipment_fault_mwh"] > 0:
        actions.append(
            {
                "action": "Inspect equipment and verify fault logs before proposing repair",
                "priority": "investigate",
                "owner": "maintenance_planner",
                "requires_human_approval": True,
                "status": "proposed",
                "preconditions": [
                    "Confirm diagnosis",
                    "Obtain site safety clearance",
                    "Confirm scope, cost and expected recovery",
                ],
            }
        )
    if reliability["unresolved_mwh"] > 0:
        actions.append(
            {
                "action": "Investigate baseline, sensors and unclassified losses",
                "priority": "investigate",
                "owner": "performance_engineer",
                "requires_human_approval": True,
                "status": "proposed",
                "preconditions": ["Acquire interval data and independent baseline evidence"],
            }
        )
    return envelope(
        case,
        {"actions": actions},
        reports["reliability"]["evidence_ids"] + reports["commercial"]["evidence_ids"],
        ["No work order, spending commitment or physical command is issued."],
    )


def summarise_asset(case, reports):
    performance = reports["performance"]["data"]
    issues = []
    if performance["excluded_dates"]:
        issues.append("Restore missing meter data before making whole-period claims")
    if reports["reliability"]["data"]["unresolved_mwh"] > 0:
        issues.append("Resolve unclassified deficits")
    if any(e["kind"] == "synthetic" for e in case["evidence"].values()):
        issues.append("Synthetic evidence: demonstration only")
    if any(e["verification"] == "unverified" for e in case["evidence"].values()):
        issues.append("Source evidence has not all been verified")
    refs = [ref for report in reports.values() for ref in report["evidence_ids"]]
    return envelope(
        case,
        {
            "decision": "human_review_required",
            "open_issues": issues,
            "next_action": "Review evidence and proposed inspections with the asset owner",
            "proposed_actions": len(reports["maintenance"]["data"]["actions"]),
        },
        refs,
        ["Numerical reconciliation is not engineering sign-off."],
    )


TOOLS = {
    f.__name__: f
    for f in (
        assess_performance,
        assess_reliability,
        assess_commercial,
        plan_maintenance,
        summarise_asset,
    )
}


def _review_evidence(case, reports):
    """Independently reconcile raw energy and revenue; audit all report contracts.

    A pass establishes accounting consistency, not correctness of the baseline,
    event attribution or the supplied evidence. No LLM judges its own calculations.
    """
    from ..roles import PV_ROLES

    issues = []
    if set(reports) != {r.output for r in PV_ROLES}:
        return {"passed": False, "issues": ["Incomplete or unexpected report set"]}
    expected_reports = {}
    for role in PV_ROLES:
        report = reports[role.output]
        refs = report.get("evidence_ids", [])
        if not refs or any(ref not in case["evidence"] for ref in refs):
            issues.append(f"{role.output}: missing evidence")
        if not report.get("limitations"):
            issues.append(f"{role.output}: missing limitations")
        # Replay checks enforce the deterministic contract including evidence labels,
        # assumptions and human approval. Raw accounting below is a separate check.
        expected = TOOLS[role.tool](case, expected_reports)
        expected_reports[role.output] = expected
        if report != expected:
            issues.append(f"{role.output}: output differs from validated tool contract")
    valid = [r for r in case["days"] if r["actual_mwh"] is not None]
    deficit = fsum(max(0, r["expected_mwh"] - r["actual_mwh"]) for r in valid)
    revenue = fsum(max(0, r["expected_mwh"] - r["actual_mwh"]) * r["price_per_mwh"] for r in valid)
    p, r, c = (reports[k]["data"] for k in ("performance", "reliability", "commercial"))
    checks = [
        (p["deficit_mwh"], deficit),
        (p["expected_mwh"] - p["actual_mwh"], deficit - p["surplus_mwh"]),
        (fsum(r.values()), deficit),
        (c["historical_deficit_value"], revenue),
    ]
    if any(not isclose(a, b, rel_tol=1e-9, abs_tol=1e-9) for a, b in checks):
        issues.append("Energy or revenue does not reconcile")
    return {
        "passed": not issues,
        "issues": issues,
        "scope": "Contract and arithmetic checks only; source truth not verified",
    }


def review_evidence(case, reports):
    """Return a failed review for malformed, unsupported or unreconciled reports."""
    try:
        return _review_evidence(case, reports)
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        return {"passed": False, "issues": [f"Malformed evidence or report: {exc}"]}
