import json
from copy import deepcopy
from io import BytesIO
from unittest.mock import patch

import pytest

from energy_agents.business import reference_case, run_bess_agent, stress_revenues
from energy_agents.business.analysis import export
from energy_agents.business.bess import review_screen
from energy_agents.connectors import BESSChatCompletionsPlanner


def test_one_year_hand_calculated_cash_flow():
    c = reference_case()
    c["source"].update(gross_eur_per_mw_year=100, ancillary_eur_per_mw_year=60)
    c["assumptions"].update(
        power_mw=2,
        years=1,
        availability=0.5,
        annual_fixed_cost_eur_per_mw=5,
        capex_eur=50,
        discount_rate=0.1,
    )
    c["scenarios"] = {
        "flat_index": {"ancillary_retention": [1], "other_retention": [1]},
        "downside": {"ancillary_retention": [0], "other_retention": [1]},
    }
    s = stress_revenues(c)["scenarios"]
    assert s["flat_index"]["npv_eur"] == pytest.approx(90 / 1.1 - 50)
    assert s["downside"]["npv_eur"] == pytest.approx(30 / 1.1 - 50)
    assert s["flat_index"]["cash_flows_eur"] == [-50, 90]


def test_no_efficiency_double_count_and_year_end_discounting():
    c = reference_case()
    s = stress_revenues(c)["scenarios"]["flat_index"]
    first = s["annual"][0]
    assert first["ancillary_eur"] + first["other_eur"] == 587000 * 10 * 0.95
    assert first["discounted_cash_eur"] == pytest.approx(first["cash_flow_eur"] / 1.1)
    assert s["zero_npv_upfront_budget_eur"] - c["assumptions"]["capex_eur"] == s["npv_eur"]


def test_downside_monotonic_and_parity():
    c = reference_case()
    before = deepcopy(c)
    result = run_bess_agent(c)
    s = result["reports"]["screen"]
    assert result["success"] and s == stress_revenues(c)
    assert c == before
    assert (
        s["scenarios"]["flat_index"]["npv_eur"]
        > s["scenarios"]["saturation"]["npv_eur"]
        > s["scenarios"]["severe"]["npv_eur"]
    )
    assert s["realised_revenue"] is None
    assert result["decision"] == "human_review_required"


@pytest.mark.parametrize(
    "key,value",
    [
        ("power_mw", 0),
        ("years", True),
        ("discount_rate", float("nan")),
        ("availability", 1.1),
        ("capex_eur", -1),
        ("duration_hours", 4),
    ],
)
def test_invalid_assumptions(key, value):
    c = reference_case()
    c["assumptions"][key] = value
    with pytest.raises(ValueError):
        run_bess_agent(c)


def test_revenue_reconciliation_and_horizon_validation():
    c = reference_case()
    c["source"]["ancillary_eur_per_mw_year"] = 1e9
    with pytest.raises(ValueError):
        stress_revenues(c)
    c = reference_case()
    c["scenarios"]["saturation"]["other_retention"] = [1]
    with pytest.raises(ValueError):
        stress_revenues(c)


class WrongPlanner:
    def __init__(self, tool):
        self.tool = tool

    def next_action(self, context):
        context["case"]["assumptions"]["capex_eur"] = 0
        return {"tool": self.tool, "arguments": {}}


@pytest.mark.parametrize("tool", ["finish", "review_screen", "execute_trade", "stress_revenues"])
def test_forbidden_early_or_repeated_tools(tool):
    c = reference_case()
    result = run_bess_agent(c, WrongPlanner(tool))
    assert not result["success"]
    assert result["trace"][-1]["status"] == "rejected"
    assert result["case"] == c


def test_budget_and_tamper():
    c = reference_case()
    assert not run_bess_agent(c, max_calls=1)["success"]
    s = stress_revenues(c)
    s["scenarios"]["severe"]["npv_eur"] = 1e12
    assert not review_screen(c, s)["passed"]


def test_reproducible_exports_and_sensitivity(tmp_path):
    result = export(tmp_path)
    first = (tmp_path / "manifest.json").read_bytes()
    export(tmp_path)
    assert (tmp_path / "manifest.json").read_bytes() == first
    assert result["deterministic_parity"]
    assert (
        result["sensitivity"][0]["npv_eur"]["flat_index"]
        > result["sensitivity"][-1]["npv_eur"]["flat_index"]
    )


def test_optional_live_prompt_uses_finance_contract(monkeypatch):
    monkeypatch.setenv("ENERGY_AGENTS_API_KEY", "test-key")
    p = BESSChatCompletionsPlanner("https://example.test/chat/completions", "test-model")
    payload = {"choices": [{"message": {"content": '{"tool":"stress_revenues","arguments":{}}'}}]}
    with patch(
        "energy_agents.connectors.urlopen", return_value=BytesIO(json.dumps(payload).encode())
    ) as call:
        assert p.next_action({})["tool"] == "stress_revenues"
    instruction = json.loads(call.call_args.args[0].data)["messages"][0]["content"]
    assert "Project Finance Analyst" in instruction
    assert "windows" not in instruction


def test_edi_adapter_uses_loader_and_validator_without_capacity_inference(tmp_path, monkeypatch):
    import sys
    from types import ModuleType

    from energy_agents.business.edi import inspect_bess_inventory

    module = ModuleType("energy_data_retrieval.bess_catalogue.catalogue")
    rows = [
        {"record_id": "pol-1", "country_code": "POL", "status": "announced"},
        {"record_id": "fin-1", "country_code": "FIN", "status": "operational"},
    ]
    calls = []
    module.load_records = lambda root: rows
    module.validate_record = lambda row, sources: calls.append(row["record_id"])
    monkeypatch.setitem(sys.modules, module.__name__, module)
    (tmp_path / "records").mkdir()
    (tmp_path / "sources.json").write_text("{}")
    result = inspect_bess_inventory(tmp_path)
    assert calls == ["pol-1"]
    assert result["records"] == 1
    assert result["status_counts"] == {"announced": 1}
    assert "capacity_mw" not in result

    def reject(row, sources):
        raise ValueError("invalid source evidence")

    module.validate_record = reject
    with pytest.raises(ValueError, match="source evidence"):
        inspect_bess_inventory(tmp_path)
