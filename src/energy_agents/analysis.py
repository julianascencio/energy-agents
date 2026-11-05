"""Reproducible analysis exports separating local replay from published results."""

import argparse
import hashlib
import json
from importlib.resources import files
from pathlib import Path

from .agents import run_agent
from .inputs import synthetic_model


def published_windows():
    """Load manually transcribed Table 8A observations; these are not our measurements."""
    return json.loads(files("energy_agents").joinpath("data/window_results.json").read_text())


def run_comparison():
    """Execute both successful scripted policies on fresh synthetic input models."""
    records = []
    for task in ("windows", "lighting"):
        for surface in ("domain", "primitive"):
            result = run_agent(synthetic_model(), task, surface)
            records.append(
                {
                    "task": task,
                    "surface": surface,
                    **result,
                    "edit_calls": sum(e["status"] == "applied" for e in result["trace"]),
                    "planner": "scripted replay; no LLM",
                    "energy_savings": None,
                    "necb_compliance": "not evaluated",
                    "simulation": "not run",
                }
            )
    return records


def export(output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    records = run_comparison()
    for name, content in {
        "replay.json": records,
        "published_windows.json": published_windows(),
        "synthetic_input.epJSON": synthetic_model(),
    }.items():
        (output / name).write_text(json.dumps(content, indent=2) + "\n")
    manifest = {
        "source_doi": "10.1016/j.egyai.2026.100896",
        "input_status": "synthetic",
        "simulation": "not run",
        "files": {},
    }
    for name in ("replay.json", "published_windows.json", "synthetic_input.epJSON"):
        manifest["files"][name] = hashlib.sha256((output / name).read_bytes()).hexdigest()
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="outputs/building_edits")
    args = parser.parse_args()
    records = export(args.output)
    print(f"{sum(r['success'] for r in records)}/4 offline workflows passed; {args.output}")


if __name__ == "__main__":
    main()
