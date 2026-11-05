import json
from copy import deepcopy

import pytest

from energy_agents.flexibility import (
    export,
    optimise_batches,
    reference_case,
    run_flexibility_agent,
)


def test_reference_reconciles():
    c = reference_case()
    original = deepcopy(c)
    r = optimise_batches(c)
    assert c == original
    assert r["baseline"]["production_mwh"] == r["proposed"]["production_mwh"] == 8
    assert r["net_savings_eur"] == 1080
    assert r["baseline"]["total_cost_eur"] == 3320
    assert r["proposed"]["total_cost_eur"] == 2240
    for name in ("baseline", "proposed"):
        v = r[name]
        assert v["total_cost_eur"] == pytest.approx(
            v["purchase_eur"] - v["export_revenue_eur"] + v["shift_cost_eur"]
        )
        assert v["peak_import_mw"] <= c["import_limit_mw"]
        for h in range(24):
            assert v["load_mw"][h] - c["solar_mw"][h] == pytest.approx(
                v["import_mwh"][h] - v["export_mwh"][h]
            )


def test_no_action_when_cost_exceeds_savings():
    c = reference_case()
    for j in c["jobs"]:
        j["shift_cost_eur"] = 100000
    r = optimise_batches(c)
    assert r["net_savings_eur"] == 0
    assert r["baseline"] == r["proposed"]


def test_export_opportunity_cost_and_negative_prices():
    c = reference_case()
    c["buy_eur_mwh"] = [-10] * 24
    c["sell_eur_mwh"] = [300] * 24
    r = optimise_batches(c)
    assert r["net_savings_eur"] == 0


def test_joint_import_constraint():
    c = reference_case()
    c["solar_mw"] = [0] * 24
    c["buy_eur_mwh"] = [200] * 24
    c["buy_eur_mwh"][10:12] = [0, 0]
    for j in c["jobs"]:
        j["starts"] = [10, j["baseline_start"]]
    r = optimise_batches(c)
    assert list(r["proposed"]["starts"].values()).count(10) == 1
    assert r["feasible_schedules"] == 3


@pytest.mark.parametrize(
    "mutation",
    [
        lambda c: c.update(base_mw=[1]),
        lambda c: c["solar_mw"].__setitem__(0, -1),
        lambda c: c["buy_eur_mwh"].__setitem__(0, float("nan")),
        lambda c: c.update(import_limit_mw=2),
        lambda c: c["jobs"][0].update(hours=True),
        lambda c: c["jobs"][0].update(starts=[23]),
        lambda c: c["jobs"][0].update(starts=[9, 9]),
        lambda c: c["jobs"][0].update(baseline_start=0),
        lambda c: c["jobs"][1].update(id="batch_a"),
    ],
)
def test_bad_inputs(mutation):
    c = reference_case()
    mutation(c)
    with pytest.raises(ValueError):
        optimise_batches(c)


@pytest.mark.parametrize("tool", ["dispatch", "finish"])
def test_forbidden_actions(tool):
    class Bad:
        def next_action(self, context):
            return {"tool": tool, "arguments": {}}

    with pytest.raises(ValueError):
        run_flexibility_agent(reference_case(), Bad())


def test_budget_and_isolation():
    with pytest.raises(ValueError):
        run_flexibility_agent(reference_case(), max_calls=1)

    class Mutating:
        def next_action(self, c):
            c["case"]["base_mw"][0] = 9999
            return {"tool": "finish" if c["result"] else "optimise_batches", "arguments": {}}

    c = reference_case()
    r = run_flexibility_agent(c, Mutating())
    assert r["result"] == optimise_batches(c)
    assert c["base_mw"][0] == 1
    assert r["live_llm"] == "unverified_custom_planner"


def test_exports_reproducible(tmp_path):
    export(tmp_path / "a")
    export(tmp_path / "b")
    for p in (tmp_path / "a").iterdir():
        assert p.read_bytes() == (tmp_path / "b" / p.name).read_bytes()
    rows = json.loads((tmp_path / "a" / "sensitivity.json").read_text())
    assert rows[-1]["net_savings_eur"] == 0


def test_repeated_tool_rejected():
    class Repeating:
        def next_action(self, context):
            return {"tool": "optimise_batches", "arguments": {}}

    with pytest.raises(ValueError, match="repeated"):
        run_flexibility_agent(reference_case(), Repeating())


def test_search_bound():
    c = reference_case()
    c["jobs"] = [dict(c["jobs"][0], id=str(i), hours=1, starts=list(range(24))) for i in range(8)]
    with pytest.raises(ValueError, match="Search limit"):
        optimise_batches(c)


def test_optional_provider_prompt(monkeypatch):
    from energy_agents import connectors
    from energy_agents.flexibility import FlexibilityChatPlanner

    captured = {}

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def read(self):
            return json.dumps(
                {
                    "choices": [
                        {"message": {"content": '{"tool":"optimise_batches","arguments":{}}'}}
                    ]
                }
            ).encode()

    def fake(request, timeout):
        captured.update(json.loads(request.data))
        return Response()

    monkeypatch.setenv("ENERGY_AGENTS_API_KEY", "test-only")
    monkeypatch.setattr(connectors, "urlopen", fake)
    action = FlexibilityChatPlanner("https://example.invalid/chat/completions", "test").next_action(
        {}
    )
    assert action["tool"] == "optimise_batches"
    assert "optimise_batches" in captured["messages"][0]["content"]
    assert "windows" not in captured["messages"][0]["content"]
