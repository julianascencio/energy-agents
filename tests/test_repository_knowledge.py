import hashlib
import json
import subprocess
from io import BytesIO
from unittest.mock import patch

import pytest

from energy_agents.knowledge import (
    EnergyDataInsightsAgent,
    build_catalogue,
    load_catalogue,
    save_catalogue,
)
from energy_agents.knowledge.catalogue import REPOSITORY
from energy_agents.pv import PVReplayPlanner, run_pv_workflow, synthetic_pv_case


@pytest.fixture
def repository(tmp_path):
    def git(*args):
        return subprocess.check_output(["git", "-C", str(tmp_path), *args]).decode().strip()

    git("init", "-q")
    git("config", "user.name", "Test")
    git("config", "user.email", "test@example.invalid")
    files = {
        "methods/src/energy_methods/solar.py": '''"""Solar performance assessment."""
from math import sqrt

def energy_loss(expected: float, actual: float) -> float:
    """Compute PV energy loss."""
    raise RuntimeError("Catalogue must never execute this code")

class Assessor:
    def assess(self, value=1):
        """Assess PV energy."""
        return value
''',
        "examples/methods/plot_solar.py": '''"""Solar loss example."""
from energy_methods.solar import energy_loss
raise RuntimeError("Do not execute during indexing")
''',
        "docs/solar.md": "# Solar methods\nSolar performance guide.",
        "pyproject.toml": '[project]\nname = "energy-data-insights"\nrequires-python = ">=3.12"',
        "methods/tests/test_solar.py": "raise RuntimeError()",
        "examples/data/huge.csv": "a,b\n1,2",
    }
    for name, content in files.items():
        p = tmp_path / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
    git("add", ".")
    git("commit", "-qm", "Fixture")
    return tmp_path, git


def test_index_committed_sources_without_execution(repository):
    root, git = repository
    sha = git("rev-parse", "HEAD")
    (root / "docs/solar.md").write_text("Uncommitted contamination")
    snapshot = build_catalogue(root)
    assert snapshot["commit"] == sha
    assert snapshot["coverage"]["indexed_files"] == 4
    assert snapshot["coverage"]["gallery_examples"] == 1
    assert snapshot["coverage"]["public_symbols"] == 3
    assert snapshot["coverage"]["complete_within_scope"]
    agent = EnergyDataInsightsAgent(snapshot)
    entry = agent.read("methods/src/energy_methods/solar.py")
    assert entry["module"] == "energy_methods.solar"
    assert [s["name"] for s in entry["symbols"]] == ["energy_loss", "Assessor", "Assessor.assess"]
    assert "expected: float" in entry["symbols"][0]["signature"]
    assert "Uncommitted" not in agent.read("docs/solar.md")["summary"]
    assert f"/blob/{sha}/" in entry["source_url"]


def test_parse_failures_are_not_silently_omitted(repository):
    root, git = repository
    (root / "methods/src/energy_methods/broken.py").write_text("def bad(")
    git("add", ".")
    git("commit", "-qm", "Malformed source")
    snapshot = build_catalogue(root)
    assert not snapshot["coverage"]["complete_within_scope"]
    assert len(snapshot["coverage"]["errors"]) == 1
    assert snapshot["coverage"]["selected_files"] == snapshot["coverage"]["indexed_files"] + 1


def test_snapshot_roundtrip_reproducible(repository, tmp_path):
    snapshot = build_catalogue(repository[0])
    target = tmp_path / "catalogue.json.gz"
    save_catalogue(snapshot, target)
    first = target.read_bytes()
    save_catalogue(snapshot, target)
    assert target.read_bytes() == first
    assert load_catalogue(target) == snapshot


@pytest.mark.parametrize(
    "query,fragment",
    [
        ("PVGIS terrain weather", "pvgis"),
        ("PV degradation lifetime", "degradation"),
        ("KGPV climate classification", "kgpv"),
        ("Timestral solar wind forecast", "timestral"),
        ("BESS database", "bess"),
        ("satellite module counting Rengo", "rengo"),
    ],
)
def test_shipped_catalogue_retrieves_real_examples(query, fragment):
    result = EnergyDataInsightsAgent().search(query, category="example", limit=5)
    assert any(fragment in r["path"] for r in result["results"])
    assert all("/blob/" + result["commit"] + "/" in r["source_url"] for r in result["results"])
    assert all(r["execution_status"] == "not_executed_by_catalogue" for r in result["results"])


def test_inventory_coverage_and_unknown_query():
    agent = EnergyDataInsightsAgent()
    coverage = agent.catalogue["coverage"]
    assert len(agent.inventory()) == coverage["indexed_files"] == coverage["selected_files"]
    assert sum(e["runnable_example"] for e in agent.inventory()) == coverage["gallery_examples"]
    assert coverage["gallery_examples"] >= 65
    assert coverage["errors"] == []
    assert agent.search("zzzzunsupportedcapability")["results"] == []
    with pytest.raises(ValueError):
        agent.read("../../outside")
    with pytest.raises(ValueError):
        agent.search("solar", limit=0)


def test_read_source_pins_and_verifies_content(repository):
    agent = EnergyDataInsightsAgent(build_catalogue(repository[0]))
    raw = (repository[0] / "examples/methods/plot_solar.py").read_bytes()
    with patch("urllib.request.urlopen", return_value=BytesIO(raw)) as call:
        result = agent.read_source("examples/methods/plot_solar.py")
    assert agent.catalogue["commit"] in call.call_args.args[0]
    assert result["sha256"] == hashlib.sha256(raw).hexdigest()
    assert result["trust"] == "untrusted_reference_data"
    with patch("urllib.request.urlopen", return_value=BytesIO(b"tampered")):
        with pytest.raises(ValueError, match="hash"):
            agent.read_source("examples/methods/plot_solar.py")
    with patch("urllib.request.urlopen", return_value=BytesIO(raw)):
        with pytest.raises(ValueError, match="size limit"):
            agent.read_source("examples/methods/plot_solar.py", max_bytes=1)


class RecordingPlanner(PVReplayPlanner):
    def __init__(self):
        self.contexts = []

    def next_action(self, context):
        self.contexts.append(context)
        return super().next_action(context)


def test_asset_manager_receives_context_without_changing_plant_evidence():
    case = synthetic_pv_case()
    manager = RecordingPlanner()
    result = run_pv_workflow(
        case,
        planners={"technical_asset_manager": manager},
        repository_query="PV degradation lifetime",
    )
    assert result["success"] and result["case"] == case
    knowledge = manager.contexts[0]["repository_knowledge"]
    assert knowledge["repository"] == REPOSITORY
    assert knowledge["results"]
    assert knowledge["commit"] == load_catalogue()["commit"]
    without = run_pv_workflow(case, repository_query=None)
    assert without["repository_knowledge"] is None
    assert result["reports"] == without["reports"]
    assert result["case_sha256"] == without["case_sha256"]
    # Planner context mutation must not change the saved retrieval record.
    manager.contexts[0]["repository_knowledge"]["results"].clear()
    assert result["repository_knowledge"]["results"]


def test_search_context_is_serialisable_and_bounded():
    agent = EnergyDataInsightsAgent()
    context = agent.context("PVGIS", limit=2)
    assert len(context["results"]) == 2
    assert all("symbols" not in e for e in context["results"])
    assert json.loads(json.dumps(context)) == context
