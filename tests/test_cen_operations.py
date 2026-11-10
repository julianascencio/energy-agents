"""Real CEN snapshot replay with conservative operational and monetary claims."""

import asyncio
import json
import sys
from copy import deepcopy

import pytest

pytest.importorskip("energy_methods.dispatch_review")

from energy_agents.operations.cen import (  # noqa: E402
    CENOperationsService,
    export_cen_review,
    load_cen_snapshot,
)


def test_preserved_real_snapshot_and_independent_accounting():
    source = load_cen_snapshot()
    result = CENOperationsService(source).review_portfolio()
    rows = [row for report in source["reports"] for row in report["generation"]]
    assert len(rows) == 583
    assert result["summary"]["assets"] == 84
    assert result["summary"]["actual_mwh"] == pytest.approx(sum(r["actual_mwh"] for r in rows))
    assert result["summary"]["scheduled_mwh"] == pytest.approx(322685.04)
    assert result["summary"]["actual_mwh"] == pytest.approx(296344.82)
    assert result["summary"]["shortfall_mwh"] == pytest.approx(82148.40)
    assert result["summary"]["above_schedule_mwh"] == pytest.approx(55808.18)
    assert result["summary"]["recoverable_revenue"] is None
    assert result["investigation_queue"][0]["asset_id"] == "PFV Atacama Solar II"


def test_zero_schedule_outage_is_not_healthy_or_zero_financial_impact():
    asset = CENOperationsService(load_cen_snapshot()).review_asset("PFV Huatacondo")
    assert asset["ledger"]["shortfall_mwh"] == 0
    assert asset["state"] == "reported_unavailable"
    assert asset["latest_notices"][0]["notice_ids"] == ["SDCF 2026100475"]
    assert asset["role_reports"]["commercial_asset_manager"]["revenue_impact"] is None
    assert asset["actions"][0]["kind"] == "notice"


def test_absent_plant_days_stay_missing_and_out_of_ranking():
    service = CENOperationsService(load_cen_snapshot())
    asset = service.review_asset("PFV Tirana Solar")
    assert asset["ledger"]["comparable_days"] == 2
    assert asset["state"] == "held_data_quality"
    assert all(
        a["asset_id"] != "PFV Tirana Solar"
        for a in service.review_portfolio()["investigation_queue"]
    )


def test_mutation_duplicate_source_and_draft_boundaries():
    data = load_cen_snapshot()
    before = deepcopy(data)
    service = CENOperationsService(data)
    asset = service.review_asset("PFV Gran Teno")
    draft = service.draft_work_order("PFV Gran Teno", asset["actions"][0]["action_id"])
    assert draft["status"] == "draft" and draft["external_work_order_id"] is None
    assert data == before
    with pytest.raises(ValueError):
        service.draft_work_order("PFV Huatacondo", asset["actions"][0]["action_id"])
    data["reports"].append(data["reports"][0])
    with pytest.raises(ValueError, match="Duplicate"):
        CENOperationsService(data)


def test_export_has_source_links_and_no_currency_valuation(tmp_path):
    export_cen_review(load_cen_snapshot(), tmp_path)
    html = (tmp_path / "report.html").read_text()
    assert "Not valued" in html and "#page=3" in html
    assert "synthetic" not in html.lower()
    assert set(json.loads((tmp_path / "manifest.json").read_text())) == {
        "input.json",
        "portfolio.json",
        "work_orders.json",
        "report.html",
    }


def test_cen_snapshot_through_real_mcp_stdio():
    pytest.importorskip("mcp")
    from importlib.resources import files

    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    async def run():
        path = files("energy_agents").joinpath("data/cen_chile/snapshot.json")
        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "energy_agents.operations.mcp_server", "--input", str(path)],
        )
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                response = await session.call_tool("review_asset", {"asset_id": "PFV Huatacondo"})
                assert not response.isError
                result = json.loads(response.content[0].text)
                assert result["state"] == "reported_unavailable"
                draft = await session.call_tool(
                    "draft_work_order",
                    {
                        "asset_id": result["asset_id"],
                        "action_id": result["actions"][0]["action_id"],
                    },
                )
                assert not draft.isError and json.loads(draft.content[0].text)["status"] == "draft"

    asyncio.run(asyncio.wait_for(run(), timeout=30))
