"""Real MCP initialization, discovery and calls over a stdio subprocess."""

import asyncio
import json
import sys

import pytest

pytest.importorskip("mcp")
pytest.importorskip("energy_methods.operations")

from mcp import ClientSession, StdioServerParameters  # noqa: E402
from mcp.client.stdio import stdio_client  # noqa: E402


def test_stdio_roundtrip():
    async def run():
        params = StdioServerParameters(
            command=sys.executable, args=["-m", "energy_agents.operations.mcp_server"]
        )
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await session.list_tools()
                assert {t.name for t in tools.tools} == {
                    "list_assets",
                    "review_asset",
                    "review_portfolio",
                    "get_evidence",
                    "draft_work_order",
                }
                assert all(t.annotations.readOnlyHint for t in tools.tools)
                response = await session.call_tool("review_portfolio", {})
                assert not response.isError
                result = json.loads(response.content[0].text)
                action = result["summaries"][0]["ranked_actions"][0]
                response = await session.call_tool(
                    "draft_work_order",
                    {"asset_id": action["asset_id"], "action_id": action["action_id"]},
                )
                assert not response.isError
                assert json.loads(response.content[0].text)["status"] == "draft"
                rejected = await session.call_tool("review_asset", {"asset_id": "unknown"})
                assert rejected.isError

    asyncio.run(asyncio.wait_for(run(), timeout=30))
