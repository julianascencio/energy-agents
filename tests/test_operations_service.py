"""Cross-repository service checks, using the actual EDI implementation."""

import hashlib
import json
from copy import deepcopy
from dataclasses import replace

import pytest

pytest.importorskip(
    "energy_methods.operations", reason="Install requirements/operations.txt on 3.12+"
)

from energy_agents.operations import OperationsService, synthetic_portfolio  # noqa: E402
from energy_agents.operations.__main__ import export_review  # noqa: E402
from energy_agents.operations.report import render_report  # noqa: E402


def test_demo_has_real_backend_and_economic_data_quality_gates():
    service = OperationsService(synthetic_portfolio())
    report = service.review_portfolio()
    states = {a["asset_id"]: a["state"] for a in report["assets"]}
    assert states == {
        "solar-north": "investigate",
        "solar-south": "review_economics",
        "solar-west": "held_data_quality",
        "solar-grid": "monitor",
    }
    group = report["summaries"][0]
    assert group["ranked_conditional_net_value"] == 1500
    assert [a["asset_id"] for a in group["ranked_actions"]] == ["solar-north"]
    assert group["observed_deficit_mwh"] == 280
    assert report["backend"]["execution"] == "executed_locally"
    assert report["backend"]["callable"].startswith("energy_methods.")
    assert len(report["backend"]["module_sha256"]) == 64
    assert all(a["role_execution"] == "deterministic_or_scripted" for a in report["assets"])


def test_no_cross_currency_period_or_timezone_ranking():
    data = synthetic_portfolio()
    data["assets"][1]["currency"] = "USD"
    data["assets"][2]["days"] = data["assets"][2]["days"][:-1]
    data["assets"][3]["timezone"] = "UTC"
    groups = OperationsService(data).review_portfolio()["summaries"]
    assert len(groups) == 4
    assert all(g["assets"] == 1 for g in groups)


def test_missing_calendar_day_and_negative_prices_block_rank():
    data = synthetic_portfolio()
    del data["assets"][0]["days"][2]
    for row in data["assets"][1]["days"]:
        row["price_per_mwh"] = -50
    service = OperationsService(data)
    north = service.review_asset("solar-north")
    assert north["state"] == "held_data_quality"
    assert north["ledger"]["missing_calendar_dates"] == ("2026-10-03",)
    assert service.review_asset("solar-south")["ledger"]["conditional_net_value"] == -3600
    assert service.review_portfolio()["summaries"][0]["ranked_actions"] == []


def test_work_order_is_draft_and_rejects_foreign_action():
    service = OperationsService(synthetic_portfolio())
    action = service.review_portfolio()["summaries"][0]["ranked_actions"][0]
    draft = service.draft_work_order("solar-north", action["action_id"])
    assert draft["status"] == "draft" and draft["requires_human_approval"]
    assert draft["external_work_order_id"] is None
    assert draft["evidence"] and draft["closure_evidence_required"]
    with pytest.raises(ValueError, match="Unknown action"):
        service.draft_work_order("solar-south", action["action_id"])
    with pytest.raises(ValueError, match="Unknown asset"):
        service.review_asset("not-in-snapshot")


def test_snapshot_and_results_are_isolated():
    data = synthetic_portfolio()
    original = deepcopy(data)
    service = OperationsService(data)
    before = service.review_portfolio()
    data["assets"][0]["days"][0]["actual_mwh"] = 9999
    assert service.review_portfolio() == before
    service.get_evidence("solar-north")["meter"]["source"] = "mutated"
    service.review_asset("solar-north")["scenario"]["intervention_cost"] = -1
    assert service.review_portfolio() == before
    assert OperationsService(original).review_portfolio() == before


def test_duplicate_assets_and_invalid_energy_rejected():
    data = synthetic_portfolio()
    data["assets"].append(data["assets"][0])
    with pytest.raises(ValueError, match="Duplicate"):
        OperationsService(data)
    data = synthetic_portfolio()
    data["assets"][0]["days"][0]["expected_mwh"] = float("nan")
    with pytest.raises(ValueError, match="finite"):
        OperationsService(data)


def test_backend_disagreement_fails_closed(monkeypatch):
    from energy_methods import operations

    service = OperationsService(synthetic_portfolio())
    actual = operations.analyze_daily_operations
    monkeypatch.setattr(
        operations,
        "analyze_daily_operations",
        lambda *a, **kw: replace(actual(*a, **kw), deficit_mwh=999999),
    )
    with pytest.raises(ValueError, match="accounting disagree"):
        service.review_asset("solar-north")


def test_export_replays_and_html_escapes_source_content(tmp_path):
    data = synthetic_portfolio()
    attack = '<script>alert("source")</script>'
    data["assets"][0]["plant_id"] = attack
    data["assets"][0]["evidence"]["meter"]["source"] = attack
    report = export_review(data, tmp_path)
    html = render_report(report)
    assert attack not in html and "&lt;script&gt;" in html
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    for name, digest in manifest.items():
        assert hashlib.sha256((tmp_path / name).read_bytes()).hexdigest() == digest
    assert (
        json.loads((tmp_path / "portfolio.json").read_text())["input_sha256"]
        == report["input_sha256"]
    )
