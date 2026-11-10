"""CEN Chile: real dispatch reconciliation through the operations tool interface.

Default execution is a deterministic five-role review. The same existing MCP
surface lets an LLM host choose asset reviews, inspect evidence and request drafts.
"""

import argparse
import hashlib
import json
import re
from copy import deepcopy
from dataclasses import asdict
from datetime import date
from importlib.resources import files
from inspect import getsource
from math import fsum, isclose
from pathlib import Path
from urllib.parse import urlsplit

from ..pv.workflow import case_digest


def load_cen_snapshot():
    return json.loads(files("energy_agents").joinpath("data/cen_chile/snapshot.json").read_text())


class CENOperationsService:
    """Review source PFV identities without inventing prices, causes or recovery."""

    def __init__(self, snapshot):
        from energy_methods import dispatch_review

        data = deepcopy(snapshot)
        if (
            data.get("review_type") != "cen_dispatch_schedule"
            or data.get("schema_version") != "1.0"
        ):
            raise ValueError("Expected CEN dispatch snapshot schema 1.0")
        if data.get("energy_unit") != "MWh" or data.get("timezone") != "America/Santiago":
            raise ValueError("Expected daily MWh and America/Santiago report dates")
        start, end = date.fromisoformat(data["start_date"]), date.fromisoformat(data["end_date"])
        if not 0 <= (end - start).days <= 30:
            raise ValueError("CEN snapshot must span 1..31 days")
        reports = {}
        assets = set()
        for report in data["reports"]:
            day = date.fromisoformat(report["report_date"])
            if day in reports or day < start or day > end:
                raise ValueError("Duplicate or out-of-window report")
            if (
                urlsplit(report["source_url"]).hostname != "www.coordinador.cl"
                or not report["source_url"].startswith(
                    "https://www.coordinador.cl/wp-content/uploads/"
                )
                or not re.fullmatch(r"[a-f0-9]{64}", report["source_sha256"])
            ):
                raise ValueError("Missing CEN source URL or SHA-256")
            names = [row["plant_name"] for row in report["generation"]]
            if len(set(names)) != len(names) or any(not n.startswith("PFV ") for n in names):
                raise ValueError("Duplicate or unsupported source plant identity")
            for row in report["generation"]:
                dispatch_review.DailyScheduleRecord(
                    str(day), row["scheduled_mwh"], row["actual_mwh"]
                )
            for notice in report["availability_notices"]:
                value = notice["reported_availability_percent"]
                if (
                    isinstance(value, bool)
                    or not isinstance(value, (int, float))
                    or not 0 <= value <= 100
                ):
                    raise ValueError("Invalid availability percentage")
            assets.update(names)
            reports[day] = report
        if not assets:
            raise ValueError("No PV generation rows in snapshot")
        self._data, self._reports, self._assets = data, reports, sorted(assets)
        self._start, self._end, self._backend = start, end, dispatch_review
        self._digest = case_digest(data)
        self._backend_info = {
            "callable": "energy_methods.dispatch_review.review_dispatch_schedule",
            "repository": "https://github.com/julianascencio/energy-data-insights",
            "module_sha256": hashlib.sha256(getsource(dispatch_review).encode()).hexdigest(),
            "execution": "executed_locally",
        }

    def list_assets(self):
        return [
            {
                "asset_id": name,
                "technology": "solar_pv",
                "evidence_kinds": ["imported"],
                "period_start": str(self._start),
                "period_end": str(self._end),
                "identity_basis": "CEN report label; InfoTecnica ID mapping not established",
            }
            for name in self._assets
        ]

    def get_evidence(self, asset_id):
        if asset_id not in self._assets:
            raise ValueError(f"Unknown asset_id: {asset_id}")
        evidence = []
        for day, report in sorted(self._reports.items()):
            rows = [r for r in report["generation"] if r["plant_name"] == asset_id]
            notices = [n for n in report["availability_notices"] if n["plant_name"] == asset_id]
            evidence.append(
                {
                    "evidence_id": str(day),
                    "kind": "imported",
                    "verification": "source_report_only",
                    "source_url": report["source_url"],
                    "source_sha256": report["source_sha256"],
                    "report_date": str(day),
                    "generation_row": deepcopy(rows[0]) if rows else None,
                    "availability_notices": deepcopy(notices),
                }
            )
        return evidence

    def review_asset(self, asset_id):
        evidence = self.get_evidence(asset_id)
        rows = tuple(
            self._backend.DailyScheduleRecord(
                e["report_date"],
                e["generation_row"]["scheduled_mwh"],
                e["generation_row"]["actual_mwh"],
            )
            for e in evidence
            if e["generation_row"] is not None
        )
        ledger = asdict(
            self._backend.review_dispatch_schedule(rows, start=self._start, end=self._end)
        )
        if not isclose(
            ledger["actual_mwh"] - ledger["scheduled_mwh"],
            ledger["above_schedule_mwh"] - ledger["shortfall_mwh"],
            abs_tol=1e-7,
        ):
            raise ValueError("Schedule review failed energy reconciliation")
        notices = [
            {**n, "report_date": e["report_date"], "source_url": e["source_url"]}
            for e in evidence
            for n in e["availability_notices"]
        ]
        latest = [n for n in notices if n["report_date"] == str(self._end)]
        # The source report's instantaneous/declared availability is not a time-weighted KPI.
        unavailable = any(n["reported_availability_percent"] == 0 for n in latest)
        limited = any(n["reported_availability_percent"] < 100 for n in latest)
        state = (
            "reported_unavailable"
            if unavailable
            else "reported_limitation"
            if limited
            else "held_data_quality"
            if ledger["missing_dates"]
            else "review_schedule"
            if ledger["shortfall_mwh"] > 0
            else "monitor"
        )
        proposals = []
        if ledger["missing_dates"]:
            proposals.append(
                (
                    "data",
                    "Restore missing plant-days before comparing the full window",
                    "performance_engineer",
                )
            )
        if notices:
            proposals.append(
                (
                    "notice",
                    "Confirm current status and closure of reported availability notices",
                    "reliability_engineer",
                )
            )
        if ledger["shortfall_mwh"] > 0:
            proposals.append(
                (
                    "schedule",
                    "Reconcile schedule deviations with weather, grid instructions and SCADA",
                    "performance_engineer",
                )
            )
        digest = case_digest({"asset_id": asset_id, "snapshot": self._digest})
        actions = [
            {
                "action_id": f"{digest[:16]}-{kind}",
                "asset_id": asset_id,
                "kind": kind,
                "title": title,
                "owner": owner,
                "status": "draft",
                "requires_human_approval": True,
                "evidence_ids": [e["evidence_id"] for e in evidence],
                "case_sha256": digest,
            }
            for kind, title, owner in proposals
        ]
        role_reports = {
            "performance_engineer": {"method": self._backend_info["callable"], "data": ledger},
            "reliability_engineer": {
                "data": notices,
                "fault_loss_mwh": None,
                "interpretation": "Reported availability; no loss attribution",
            },
            "commercial_asset_manager": {
                "revenue_impact": None,
                "repair_value": None,
                "missing_inputs": [
                    "plant nodal/PPA price series",
                    "technical baseline",
                    "causal attribution",
                    "repair scope and cost",
                ],
            },
            "maintenance_planner": {"actions": actions, "dispatch_status": "not_sent"},
            "technical_asset_manager": {
                "state": state,
                "review": "human_review_required",
                "zero_schedule_does_not_prove_health": True,
            },
        }
        return {
            "asset_id": asset_id,
            "case_sha256": digest,
            "state": state,
            "ledger": ledger,
            "reported_notices": notices,
            "latest_notices": latest,
            "actions": actions,
            "evidence": evidence,
            "role_reports": role_reports,
            "role_trace": [{"role": role, "status": "completed"} for role in role_reports],
            "role_execution": "deterministic",
            "authority": "advisory_only",
        }

    def review_portfolio(self):
        assets = [self.review_asset(name) for name in self._assets]
        ranked = sorted(
            [
                a
                for a in assets
                if not a["ledger"]["missing_dates"] and a["ledger"]["shortfall_mwh"] > 0
            ],
            key=lambda a: (-a["ledger"]["shortfall_mwh"], a["asset_id"]),
        )
        availability_queue = [
            a for a in assets if a["state"] in {"reported_unavailable", "reported_limitation"}
        ]
        summary = {
            key: fsum(a["ledger"][key] for a in assets)
            for key in (
                "scheduled_mwh",
                "actual_mwh",
                "shortfall_mwh",
                "above_schedule_mwh",
                "net_deviation_mwh",
            )
        }
        summary.update(
            assets=len(assets),
            reports=len(self._reports),
            comparable_plant_days=sum(a["ledger"]["comparable_days"] for a in assets),
            held_assets=sum(bool(a["ledger"]["missing_dates"]) for a in assets),
            revenue_impact=None,
            recoverable_revenue=None,
        )
        return {
            "schema_version": "1.0",
            "review_type": "cen_dispatch_schedule",
            "period_start": str(self._start),
            "period_end": str(self._end),
            "timezone": "America/Santiago",
            "input_sha256": self._digest,
            "backend": deepcopy(self._backend_info),
            "summary": summary,
            "assets": assets,
            "investigation_queue": [
                {
                    "rank": i + 1,
                    "asset_id": a["asset_id"],
                    "shortfall_mwh": a["ledger"]["shortfall_mwh"],
                }
                for i, a in enumerate(ranked)
            ],
            "availability_queue": [
                {
                    "asset_id": a["asset_id"],
                    "state": a["state"],
                    "latest_notices": a["latest_notices"],
                }
                for a in availability_queue
            ],
            "limitations": [
                "Dispatch schedule is not unconstrained technical production.",
                "Daily report data may be revised; source publication is not independent field verification.",
                "Source PFV rows are a selected fleet, not all solar plants in Chile.",
                "Availability notices are reported states, not time-weighted availability or causal loss.",
                "No revenue, fault loss, repair return or avoided curtailment is estimated.",
            ],
            "authority": "advisory_only",
        }

    def draft_work_order(self, asset_id, action_id):
        review = self.review_asset(asset_id)
        action = next((a for a in review["actions"] if a["action_id"] == action_id), None)
        if action is None:
            raise ValueError("Unknown action_id for this asset snapshot")
        return {
            **action,
            "external_work_order_id": None,
            "evidence": review["evidence"],
            "scope": "Evidence collection and operational investigation; repair not authorized",
            "preconditions": [
                "Confirm data and current operational status",
                "Site authorization before access",
            ],
            "closure_evidence_required": [
                "Reconciled interval records",
                "Reviewed source notice closure status",
            ],
        }


def export_cen_review(snapshot, output):
    from .cen_report import render_cen_report

    service = CENOperationsService(snapshot)
    result = service.review_portfolio()
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    drafts = [
        service.draft_work_order(a["asset_id"], action["action_id"])
        for a in result["assets"]
        for action in a["actions"]
    ]
    for name, value in {
        "input.json": snapshot,
        "portfolio.json": result,
        "work_orders.json": drafts,
    }.items():
        (output / name).write_text(
            json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
        )
    (output / "report.html").write_text(render_cen_report(result), encoding="utf-8")
    names = ["input.json", "portfolio.json", "work_orders.json", "report.html"]
    manifest = {n: hashlib.sha256((output / n).read_bytes()).hexdigest() for n in names}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input", type=Path, help="Downloaded CEN snapshot; default: preserved real example"
    )
    parser.add_argument("--output", type=Path, default=Path("outputs/cen_chile"))
    args = parser.parse_args()
    data = json.loads(args.input.read_text()) if args.input else load_cen_snapshot()
    result = export_cen_review(data, args.output)
    print(json.dumps(result["summary"], indent=2))
    print(f"Report: {args.output / 'report.html'}")


if __name__ == "__main__":
    main()
