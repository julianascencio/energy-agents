"""Shared service for Python, CLI and MCP; all outputs are reviewable proposals."""

from copy import deepcopy
from dataclasses import asdict
from hashlib import sha256
from importlib.metadata import version
from inspect import getsource
from math import fsum, isclose

from ..pv import run_pv_workflow, synthetic_pv_case, validate_case
from ..pv.workflow import case_digest


def synthetic_portfolio():
    """Four invented PV sites illustrating economic, grid and evidence decisions."""
    cases = []
    for plant, cost, complete, grid_only in (
        ("solar-north", 100, True, False),
        ("solar-south", 2000, True, False),
        ("solar-west", 100, False, False),
        ("solar-grid", 100, True, True),
    ):
        case = synthetic_pv_case()
        case.update(case_id=f"demo-{plant}", plant_id=plant)
        case["assumptions"]["intervention_cost"] = cost
        case["assumptions"]["scenario_description"] = (
            f"Assume recurrence over the same six-day window at identical prices; "
            f"80% of fault-associated energy recovered at a one-off cost of {cost} EUR."
        )
        case["evidence"]["scenario"]["source"] = case["assumptions"]["scenario_description"]
        if complete:
            case["days"][-1]["actual_mwh"] = 100
        if grid_only:
            case["days"][1]["event"] = "curtailment"
        cases.append(case)
    return {"schema_version": "1.0", "portfolio_id": "synthetic-solar-portfolio", "assets": cases}


class OperationsService:
    """Validated portfolio snapshot with deterministic, evidence-linked tool calls.

    The host LLM can select tools through MCP. Python callers can also supply the
    existing role planners to review_asset. No tool changes source data, sends a
    work order, commits spending, or controls equipment. Ranking is economic only.
    """

    def __init__(self, portfolio):
        try:
            from energy_methods import operations
        except ImportError as exc:
            raise RuntimeError(
                "Install the Energy Data Insights backend from requirements/operations.txt "
                "using Python 3.12+. No local fallback calculations are substituted."
            ) from exc
        snapshot = deepcopy(portfolio)
        if snapshot.get("schema_version") != "1.0":
            raise ValueError("Expected portfolio schema_version 1.0")
        if (
            not isinstance(snapshot.get("portfolio_id"), str)
            or not snapshot["portfolio_id"].strip()
        ):
            raise ValueError("portfolio_id is required")
        if not isinstance(snapshot.get("assets"), list) or not snapshot["assets"]:
            raise ValueError("At least one asset is required")
        assets = {}
        for case in snapshot["assets"]:
            validate_case(case)
            if case["plant_id"] in assets:
                raise ValueError("Duplicate plant_id")
            assets[case["plant_id"]] = case
        self._assets = assets
        self._portfolio_id = snapshot["portfolio_id"]
        self._digest = case_digest(snapshot)
        self._backend = operations
        self._backend_info = {
            "repository": "https://github.com/julianascencio/energy-data-insights",
            "callable": "energy_methods.operations.analyze_daily_operations",
            "package_version": version("energy-methods"),
            "module_sha256": sha256(getsource(operations).encode()).hexdigest(),
            "execution": "executed_locally",
        }

    def list_assets(self):
        return [
            {
                "asset_id": key,
                "technology": case["technology"],
                "currency": case["currency"],
                "period_start": min(d["date"] for d in case["days"]),
                "period_end": max(d["date"] for d in case["days"]),
                "evidence_kinds": sorted({e["kind"] for e in case["evidence"].values()}),
            }
            for key, case in sorted(self._assets.items())
        ]

    def get_evidence(self, asset_id):
        """Retrieve source descriptions, origin and verification from the loaded snapshot."""
        return deepcopy(self._case(asset_id)["evidence"])

    def _case(self, asset_id):
        if asset_id not in self._assets:
            raise ValueError(f"Unknown asset_id: {asset_id}")
        return self._assets[asset_id]

    def review_asset(self, asset_id, *, planners=None):
        case = self._case(asset_id)
        backend = self._backend
        ledger = asdict(
            backend.analyze_daily_operations(
                tuple(
                    backend.DailyEnergyRecord(
                        day=r["date"],
                        expected_mwh=r["expected_mwh"],
                        actual_mwh=r["actual_mwh"],
                        price_per_mwh=r["price_per_mwh"],
                        event=r["event"],
                    )
                    for r in case["days"]
                ),
                recovery_fraction=case["assumptions"]["recovery_fraction"],
                intervention_cost=case["assumptions"]["intervention_cost"],
            )
        )
        team = run_pv_workflow(case, planners=planners)
        if not team["success"]:
            raise ValueError(f"Role review failed: {team['review']['issues']}")
        reports = team["reports"]
        comparisons = {
            "performance": ("expected_mwh", "actual_mwh", "deficit_mwh", "surplus_mwh"),
            "commercial": (
                "historical_deficit_value",
                "conditional_recovery_mwh",
                "conditional_gross_value",
                "conditional_net_value",
            ),
        }
        for report, keys in comparisons.items():
            if any(not isclose(ledger[k], reports[report]["data"][k], abs_tol=1e-8) for k in keys):
                raise ValueError("Energy Data Insights and role review accounting disagree")
        held = bool(ledger["excluded_dates"] or ledger["missing_calendar_dates"])
        faults = ledger["deficit_by_event_mwh"]["equipment_fault"] > 0
        state = (
            "held_data_quality"
            if held
            else "investigate"
            if faults and ledger["conditional_net_value"] > 0
            else "review_economics"
            if faults
            else "monitor"
        )
        actions = []
        if held:
            actions.append(
                (
                    "data",
                    "Recover missing meter data and reconcile daily coverage",
                    "performance_engineer",
                )
            )
        if faults:
            actions.append(
                (
                    "fault",
                    "Inspect fault evidence and validate repair scope and cost",
                    "maintenance_planner",
                )
            )
        if ledger["deficit_by_event_mwh"]["curtailment"] > 0:
            actions.append(
                (
                    "grid",
                    "Review curtailment events and applicable compensation terms",
                    "commercial_asset_manager",
                )
            )
        if ledger["deficit_by_event_mwh"]["unresolved"] > 0:
            actions.append(
                (
                    "baseline",
                    "Investigate baseline, sensors and unclassified deficits",
                    "performance_engineer",
                )
            )
        digest = team["case_sha256"]
        proposals = [
            {
                "action_id": f"{digest[:16]}-{kind}",
                "asset_id": asset_id,
                "kind": kind,
                "title": title,
                "owner": owner,
                "status": "draft",
                "requires_human_approval": True,
                "evidence_ids": sorted(case["evidence"]),
                "case_sha256": digest,
                "economic_rank_eligible": kind == "fault" and state == "investigate",
                "conditional_net_value": ledger["conditional_net_value"]
                if kind == "fault"
                else None,
                "currency": case["currency"],
            }
            for kind, title, owner in actions
        ]
        return {
            "asset_id": asset_id,
            "case_sha256": digest,
            "currency": case["currency"],
            "period_start": min(d["date"] for d in case["days"]),
            "period_end": max(d["date"] for d in case["days"]),
            "timezone": case["timezone"],
            "state": state,
            "ledger": ledger,
            "scenario": deepcopy(case["assumptions"]),
            "actions": proposals,
            "backend": deepcopy(self._backend_info),
            "role_execution": team["execution"],
            "role_trace": team["trace"],
            "role_reports": reports,
            "evidence": deepcopy(case["evidence"]),
            "authority": "advisory_only",
            "limitations": [
                "Event association is not root-cause diagnosis.",
                "Conditional recovery assumes recurrence and is not a revenue forecast.",
                "Data gaps block economic ranking; observed-period values remain visible.",
                "Economic ranking does not assess safety criticality or dispatch feasibility.",
                "No warranty, PPA settlement or compensation calculation is performed.",
                "Evidence provenance and arithmetic checks do not independently verify source truth.",
            ],
        }

    def review_portfolio(self):
        assets = [self.review_asset(key) for key in sorted(self._assets)]
        # Different currencies, windows and timezones are deliberately not aggregated or ranked.
        groups = {}
        for asset in assets:
            key = (asset["currency"], asset["period_start"], asset["period_end"], asset["timezone"])
            groups.setdefault(key, []).append(asset)
        summaries = []
        for (currency, start, end, timezone), members in sorted(groups.items()):
            ranked = sorted(
                [a for m in members for a in m["actions"] if a["economic_rank_eligible"]],
                key=lambda a: (-a["conditional_net_value"], a["asset_id"]),
            )
            summaries.append(
                {
                    "currency": currency,
                    "period_start": start,
                    "period_end": end,
                    "timezone": timezone,
                    "assets": len(members),
                    "held_assets": sum(m["state"] == "held_data_quality" for m in members),
                    "observed_deficit_mwh": fsum(m["ledger"]["deficit_mwh"] for m in members),
                    "historical_deficit_value": fsum(
                        m["ledger"]["historical_deficit_value"] for m in members
                    ),
                    "ranked_conditional_net_value": fsum(
                        a["conditional_net_value"] for a in ranked
                    ),
                    "ranked_actions": [dict(a, rank=i + 1) for i, a in enumerate(ranked)],
                }
            )
        return {
            "schema_version": "1.0",
            "portfolio_id": self._portfolio_id,
            "input_sha256": self._digest,
            "backend": deepcopy(self._backend_info),
            "authority": "advisory_only",
            "summaries": summaries,
            "assets": assets,
        }

    def draft_work_order(self, asset_id, action_id):
        """Return a draft object only; no CMMS, notification or file write is invoked."""
        review = self.review_asset(asset_id)
        action = next((a for a in review["actions"] if a["action_id"] == action_id), None)
        if action is None:
            raise ValueError("Unknown action_id for this asset snapshot")
        return {
            **action,
            "external_work_order_id": None,
            "case_sha256": review["case_sha256"],
            "evidence": review["evidence"],
            "scenario": review["scenario"],
            "review_state": review["state"],
            "preconditions": [
                "Confirm source data and diagnosis",
                "Confirm site safety clearance",
                "Approve scope, contractor, cost and outage window",
            ],
            "closure_evidence_required": [
                "As-found and as-left inspection records",
                "Post-work meter data against a reviewed baseline",
            ],
        }
