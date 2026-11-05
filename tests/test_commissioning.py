from copy import deepcopy

import pytest

from energy_agents.commissioning import (
    export,
    rank_acceleration,
    reference_case,
    run_commissioning_agent,
)


def test_reference_package_and_economics():
    c = reference_case()
    saved = deepcopy(c)
    r = run_commissioning_agent(c)
    assert r["success"]
    s = r["reports"]["screen"]
    assert s == rank_acceleration(c)
    assert s["baseline"]["completion_day"] == 25
    p = s["recommended_package"]
    assert p["options"] == ["extra_substation_crew", "reserved_witness_slot"]
    assert p["schedule"]["completion_day"] == 20
    assert p["days_saved"] == 5
    assert p["additional_energy_mwh"] == 4800
    assert p["gross_contribution_eur"] == 336000
    assert p["cost_eur"] == 140000
    assert p["net_benefit_eur"] == 196000
    assert c == saved


def test_noncritical_acceleration_does_not_earn_revenue():
    s = rank_acceleration(reference_case())
    p = next(p for p in s["packages"] if p["options"] == ["extra_turbine_crew"])
    assert p["days_saved"] == p["gross_contribution_eur"] == 0
    assert p["net_benefit_eur"] == -40000


def test_parallel_paths_recompute_bottleneck():
    c = reference_case()
    c["tasks"] = [
        {"id": "a", "duration_days": 10, "minimum_days": 5, "dependencies": []},
        {"id": "b", "duration_days": 9, "minimum_days": 5, "dependencies": []},
        {"id": "c", "duration_days": 1, "minimum_days": 1, "dependencies": ["a", "b"]},
    ]
    c["options"] = [
        {"id": "a5", "task": "a", "new_duration_days": 5, "cost_eur": 1},
        {"id": "b5", "task": "b", "new_duration_days": 5, "cost_eur": 1},
    ]
    r = rank_acceleration(c)
    assert next(p for p in r["packages"] if p["options"] == ["a5"])["days_saved"] == 1
    assert r["recommended_package"]["days_saved"] == 5
    assert r["recommended_package"]["options"] == ["a5", "b5"]


@pytest.mark.parametrize("budget", [0, 1])
def test_budget_keeps_no_action(budget):
    c = reference_case()
    c["economics"]["budget_eur"] = budget
    assert rank_acceleration(c)["recommended_package"]["options"] == []


def test_negative_prices_and_zero_resource_do_not_force_action():
    c = reference_case()
    c["economics"]["price_eur_per_mwh"] = -10
    assert rank_acceleration(c)["recommended_package"]["options"] == []
    c["economics"]["capacity_factor"] = 0
    assert rank_acceleration(c)["recommended_package"]["options"] == []


@pytest.mark.parametrize(
    "fault", ["cycle", "missing", "duplicate", "below_minimum", "nan", "bool", "too_many"]
)
def test_invalid_cases(fault):
    c = reference_case()
    if fault == "cycle":
        c["tasks"][0]["dependencies"] = ["handover"]
    elif fault == "missing":
        c["tasks"][0]["dependencies"] = ["unknown"]
    elif fault == "duplicate":
        c["tasks"][1]["id"] = c["tasks"][0]["id"]
    elif fault == "below_minimum":
        c["options"][0]["new_duration_days"] = 0
    elif fault == "nan":
        c["economics"]["price_eur_per_mwh"] = float("nan")
    elif fault == "bool":
        c["economics"]["power_mw"] = True
    elif fault == "too_many":
        c["options"] = c["options"] * 4
    with pytest.raises(ValueError):
        rank_acceleration(c)


def test_competing_options_same_task_are_exclusive():
    c = reference_case()
    c["options"].append(
        {"id": "other_crew", "task": "substation_tests", "new_duration_days": 6, "cost_eur": 30000}
    )
    for p in rank_acceleration(c)["packages"]:
        assert not {"other_crew", "extra_substation_crew"} <= set(p["options"])


class WrongPlanner:
    def __init__(self, tool):
        self.tool = tool

    def next_action(self, context):
        context["case"]["economics"]["budget_eur"] = 1e12
        return {"tool": self.tool, "arguments": {}}


@pytest.mark.parametrize(
    "tool", ["finish", "waive_safety_test", "place_order", "rank_acceleration"]
)
def test_forbidden_early_repeated_and_context_isolation(tool):
    c = reference_case()
    r = run_commissioning_agent(c, WrongPlanner(tool))
    assert not r["success"]
    assert r["case"] == c
    assert r["trace"][-1]["status"] == "rejected"


def test_budget_and_exports(tmp_path):
    assert not run_commissioning_agent(reference_case(), max_calls=1)["success"]
    r = export(tmp_path)
    raw = (tmp_path / "manifest.json").read_bytes()
    export(tmp_path)
    assert (tmp_path / "manifest.json").read_bytes() == raw
    assert r["baseline_parity"] and r["realised_savings"] is None
    assert (
        r["sensitivity"][0]["best"]["net_benefit_eur"]
        < r["sensitivity"][-1]["best"]["net_benefit_eur"]
    )


def test_optional_provider_prompt_and_action(monkeypatch):
    import json
    from io import BytesIO
    from unittest.mock import patch

    from energy_agents.connectors import CommissioningChatCompletionsPlanner

    monkeypatch.setenv("ENERGY_AGENTS_API_KEY", "test-key")
    planner = CommissioningChatCompletionsPlanner(
        "https://example.test/chat/completions", "test-model"
    )
    payload = {"choices": [{"message": {"content": '{"tool":"rank_acceleration","arguments":{}}'}}]}
    with patch(
        "energy_agents.connectors.urlopen", return_value=BytesIO(json.dumps(payload).encode())
    ) as call:
        assert planner.next_action({})["tool"] == "rank_acceleration"
    prompt = json.loads(call.call_args.args[0].data)["messages"][0]["content"]
    assert "Project Controls Engineer" in prompt
    assert "windows" not in prompt
