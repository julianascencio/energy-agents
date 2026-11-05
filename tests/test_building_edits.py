import json
from copy import deepcopy
from unittest.mock import patch

import pytest

from energy_agents import edit_lighting, edit_windows, run_agent
from energy_agents.analysis import export, published_windows
from energy_agents.connectors import ChatCompletionsPlanner
from energy_agents.inputs import synthetic_model
from energy_agents.methods import GLAZING


def test_lighting_all_methods_and_preservation():
    original = synthetic_model()
    original["Lights"]["Office"]["lighting_level"] = 999  # inactive field
    saved = deepcopy(original)
    result = edit_lighting(original)
    assert result["Lights"]["Office"]["watts_per_floor_area"] == 7
    assert result["Lights"]["Lobby"]["lighting_level"] == 350
    assert result["Lights"]["Meeting"]["watts_per_person"] == pytest.approx(8.4)
    assert result["Lights"]["Office"]["lighting_level"] == 999
    for name in original["Lights"]:
        assert result["Lights"][name]["schedule_name"] == original["Lights"][name]["schedule_name"]
    assert original == saved
    assert result[GLAZING] == original[GLAZING]


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -1, True, "1.5", 0])
def test_invalid_windows(value):
    with pytest.raises(ValueError):
        edit_windows(synthetic_model(), value)


@pytest.mark.parametrize("value", [float("nan"), -0.1, 1.1, True])
def test_invalid_reduction(value):
    with pytest.raises(ValueError):
        edit_lighting(synthetic_model(), value)


def test_atomic_failure():
    model = synthetic_model()
    model["Lights"]["Meeting"]["design_level_calculation_method"] = "unknown"
    saved = deepcopy(model)
    with pytest.raises(ValueError):
        edit_lighting(model)
    assert model == saved


@pytest.mark.parametrize("task", ["windows", "lighting"])
def test_replay_surfaces_equal(task):
    model = synthetic_model()
    domain = run_agent(model, task, "domain")
    primitive = run_agent(model, task, "primitive")
    assert domain["success"] and primitive["success"]
    assert domain["model"] == primitive["model"]
    assert model == synthetic_model()


class FinishOnly:
    def next_action(self, context):
        return {"tool": "finish", "arguments": {}}


def test_false_success_rejected_and_retries_bounded():
    result = run_agent(synthetic_model(), "lighting", "domain", FinishOnly())
    assert not result["success"]
    assert len(result["trace"]) == 3
    assert result["model"] == synthetic_model()


class RepeatReduction:
    def next_action(self, context):
        if context["attempt"] == 1 and context["step"] < 2:
            return {"tool": "edit_lighting", "arguments": {}}
        if context["step"] == 0:
            return {"tool": "edit_lighting", "arguments": {}}
        return {"tool": "finish", "arguments": {}}


def test_retry_restarts_original_not_compounded_reduction():
    result = run_agent(synthetic_model(), "lighting", "domain", RepeatReduction())
    assert result["success"]
    assert result["trace"][-1]["attempt"] == 2
    assert result["model"]["Lights"]["Lobby"]["lighting_level"] == 350


class WrongTool:
    def next_action(self, context):
        return {"tool": "edit_windows", "arguments": {}}


def test_surface_isolation():
    result = run_agent(synthetic_model(), "windows", "primitive", WrongTool())
    assert not result["success"]
    assert "not available" in result["trace"][0]["error"]


def test_budget_exhaustion_rolls_back():
    result = run_agent(synthetic_model(), "windows", "domain", max_calls=1)
    assert not result["success"]
    assert result["model"] == synthetic_model()


def test_missing_target_is_failure():
    with pytest.raises(ValueError):
        edit_windows({})


def test_exports_reproducible_and_evidence_separate(tmp_path):
    export(tmp_path)
    initial = (tmp_path / "manifest.json").read_bytes()
    export(tmp_path)
    assert initial == (tmp_path / "manifest.json").read_bytes()
    records = json.loads((tmp_path / "replay.json").read_text())
    assert all(r["energy_savings"] is None for r in records)
    assert len(published_windows()) == 14
    assert published_windows()[0]["calls"] == 1  # Table 8A, not conflicting narrative


def test_http_adapter_request_and_usage(monkeypatch):
    monkeypatch.setenv("ENERGY_AGENTS_API_KEY", "test-key")
    planner = ChatCompletionsPlanner("https://example.test/v1/chat/completions", "test-model")
    payload = {
        "choices": [{"message": {"content": '{"tool":"finish","arguments":{}}'}}],
        "usage": {"total_tokens": 20},
    }
    from io import BytesIO

    with patch(
        "energy_agents.connectors.urlopen", return_value=BytesIO(json.dumps(payload).encode())
    ) as call:
        assert planner.next_action({"task": "windows"})["tool"] == "finish"
    request = call.call_args.args[0]
    assert json.loads(request.data)["model"] == "test-model"
    assert planner.usage == [{"total_tokens": 20}]
