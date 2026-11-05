"""Contract tests for the coding agent, not a benchmark of LLM competence."""

from copy import deepcopy

import pytest

from energy_agents.python_engineer import run_python_engineer, validate_bundle


@pytest.fixture
def bundle():
    return {
        "files": {
            "src/metric.py": "def value(): return 1\n",
            "tests/test_metric.py": "def test_value(): assert 1 == 1\n",
            "examples/demo.py": "print('synthetic example')\n",
        },
        "explanation": "Synthetic contract fixture",
        "validation_commands": ["pytest"],
    }


class Planner:
    def __init__(self, actions):
        self.actions = iter(actions)
        self.contexts = []

    def next_action(self, context):
        self.contexts.append(deepcopy(context))
        context["repository_context"].clear()
        return next(self.actions)


def test_repairs_invalid_python_and_preserves_context(bundle):
    bad = deepcopy(bundle)
    bad["files"]["src/metric.py"] = "def broken("
    planner = Planner([{"tool": "propose_files", "arguments": b} for b in [bad, bundle]])
    context = {"README.md": "Energy science"}
    result = run_python_engineer("Implement a metric", context, planner)
    assert result["success"] and not result["tests_run"]
    assert result["trace"][0]["status"] == "rejected"
    assert context == planner.contexts[1]["repository_context"]
    result["bundle"]["files"].clear()
    assert len(bundle["files"]) == 3


@pytest.mark.parametrize(
    "path",
    ["../x.py", "/tmp/x.py", "a/../x.py", ".github/x.py", "a\\x.py", "C:/x.py", "a//x.py", "a.sh"],
)
def test_rejects_paths(bundle, path):
    bundle["files"][path] = "pass"
    with pytest.raises(ValueError):
        validate_bundle(bundle)


def test_budget_and_unavailable_tools():
    planner = Planner([{"tool": "shell"}] * 2)
    result = run_python_engineer("Fit forecast", {"README": "context"}, planner, max_calls=2)
    assert not result["success"] and result["bundle"] is None
    assert len(result["trace"]) == 2


def test_does_not_execute_source(bundle, tmp_path):
    marker = tmp_path / "executed"
    bundle["files"]["src/metric.py"] = f"open({str(marker)!r}, 'w').write('bad')"
    assert validate_bundle(bundle)
    assert not marker.exists()


@pytest.mark.parametrize(
    "field,value", [("files", {}), ("explanation", ""), ("validation_commands", [None])]
)
def test_missing_contract(bundle, field, value):
    bundle[field] = value
    with pytest.raises(ValueError):
        validate_bundle(bundle)


def test_requires_test_and_example(bundle):
    bundle["files"]["demo.py"] = bundle["files"].pop("examples/demo.py")
    with pytest.raises(ValueError, match="Include source"):
        validate_bundle(bundle)


def test_catalogue_is_opt_in_and_independent():
    from energy_agents.roles import role_catalogue

    assert len(role_catalogue()) == 5
    roles = role_catalogue(include_engineering=True)
    assert roles[-1]["id"] == "python_ml_engineer"
    roles[-1]["title"] = "changed"
    assert role_catalogue(include_engineering=True)[-1]["title"] != "changed"
