"""Versioned PV case input with explicit units, evidence and scenario assumptions."""

from datetime import date
from math import isfinite

KINDS = {"measured", "imported", "modelled", "synthetic"}
VERIFICATION = {"unverified", "verified"}


def numeric(value, name, *, minimum=None, maximum=None):
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not isfinite(value):
        raise ValueError(f"{name} must be a finite number")
    if minimum is not None and value < minimum:
        raise ValueError(f"{name} must be >= {minimum}")
    if maximum is not None and value > maximum:
        raise ValueError(f"{name} must be <= {maximum}")
    return value


def validate_case(case):
    """Reject ambiguous daily energy, duplicate days and missing provenance.

    Inputs are daily MWh, not instantaneous MW. Missing actual energy remains
    None and is excluded, never silently treated as zero. Evidence records may
    have different origins; verification is independent of origin.
    """
    if case.get("schema_version") != "1.0" or case.get("technology") != "solar_pv":
        raise ValueError("Expected schema 1.0 and technology solar_pv")
    for key in ("case_id", "plant_id", "timezone", "currency"):
        if not isinstance(case.get(key), str) or not case[key].strip():
            raise ValueError(f"Missing {key}")
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

    try:
        ZoneInfo(case["timezone"])
    except ZoneInfoNotFoundError as exc:
        raise ValueError("Unknown timezone") from exc
    if len(case["currency"]) != 3 or not case["currency"].isupper():
        raise ValueError("Use a three-letter currency code")
    numeric(case["revision"], "revision", minimum=1)
    if not isinstance(case["revision"], int):
        raise ValueError("revision must be an integer")
    sources = case["evidence"]
    if not isinstance(sources, dict) or not sources:
        raise ValueError("Evidence registry is required")
    for source in sources.values():
        if source["kind"] not in KINDS or source["verification"] not in VERIFICATION:
            raise ValueError("Unknown evidence origin or verification status")
        if not isinstance(source["source"], str) or not source["source"].strip():
            raise ValueError("Evidence source is required")
    assumptions = case["assumptions"]
    numeric(assumptions["recovery_fraction"], "recovery_fraction", minimum=0, maximum=1)
    numeric(assumptions["intervention_cost"], "intervention_cost", minimum=0)
    if not assumptions["scenario_description"].strip():
        raise ValueError("Recovery scenario must be described")
    if assumptions["evidence_id"] not in sources:
        raise ValueError("Missing assumption evidence")
    if not case["days"]:
        raise ValueError("At least one daily record is required")
    seen = set()
    for row in case["days"]:
        day = date.fromisoformat(row["date"])
        if day in seen:
            raise ValueError("Duplicate daily record")
        seen.add(day)
        numeric(row["expected_mwh"], "expected_mwh", minimum=0)
        if row["actual_mwh"] is not None:
            numeric(row["actual_mwh"], "actual_mwh", minimum=0)
        numeric(row["price_per_mwh"], "price_per_mwh")
        if row["event"] not in {"none", "equipment_fault", "curtailment"}:
            raise ValueError("Unknown event; reconcile overlapping events upstream")
        required = {"expected", "actual", "price"}
        if row["event"] != "none":
            required.add("event")
        refs = row["evidence_ids"]
        if not required <= refs.keys() or any(ref not in sources for ref in refs.values()):
            raise ValueError("Missing or dangling daily evidence reference")


def synthetic_pv_case():
    """Six illustrative days, including one missing actual-energy value."""
    evidence = {
        key: {"kind": "synthetic", "verification": "unverified", "source": description}
        for key, description in {
            "expected": "Illustrative daily baseline; not a calibrated production model",
            "meter": "Invented daily export-energy values",
            "events": "Invented mutually exclusive daily equipment/grid event labels",
            "prices": "Illustrative flat energy value; no PPA or settlement data",
            "scenario": "Assume recurrence over a comparable six-day period, 80% recovery, cost 100",
        }.items()
    }
    days = []
    for i, (actual, event) in enumerate(
        [
            (100, "none"),
            (60, "equipment_fault"),
            (80, "curtailment"),
            (90, "none"),
            (105, "none"),
            (None, "none"),
        ],
        1,
    ):
        refs = {"expected": "expected", "actual": "meter", "price": "prices"}
        if event != "none":
            refs["event"] = "events"
        days.append(
            {
                "date": f"2026-10-{i:02d}",
                "expected_mwh": 100.0,
                "actual_mwh": actual,
                "price_per_mwh": 50.0,
                "event": event,
                "evidence_ids": refs,
            }
        )
    return {
        "schema_version": "1.0",
        "case_id": "synthetic-pv-operations",
        "revision": 1,
        "plant_id": "illustrative-pv-plant",
        "technology": "solar_pv",
        "timezone": "Atlantic/Canary",
        "currency": "EUR",
        "evidence": evidence,
        "assumptions": {
            "recovery_fraction": 0.8,
            "intervention_cost": 100.0,
            "evidence_id": "scenario",
            "scenario_description": "Recurrence over a comparable six-day period at the same prices; not a forecast",
        },
        "days": days,
    }
