"""Export repeatable PV role-team results and architecture parity checks."""

import argparse
import hashlib
import json
from pathlib import Path

from ..roles import role_catalogue
from .inputs import synthetic_pv_case
from .workflow import run_pv_workflow


def run_comparison(case=None):
    """Same tools/input in all modes; parity is not evidence of LLM superiority."""
    case = synthetic_pv_case() if case is None else case
    runs = [
        run_pv_workflow(case, mode=mode) for mode in ("deterministic", "single_agent", "role_team")
    ]
    return {
        "runs": runs,
        "report_parity": all(r["reports"] == runs[0]["reports"] for r in runs),
        "all_passed": all(r["success"] for r in runs),
        "evidence": "Offline deterministic/scripted policies; zero LLM calls",
        "live_benchmark": "not_run",
        "model_cost": None,
    }


def export(output, case=None):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    case = synthetic_pv_case() if case is None else case
    result = run_comparison(case)
    artifacts = {"case.json": case, "comparison.json": result, "roles.json": role_catalogue()}
    checksums = {}
    for name, data in artifacts.items():
        content = (json.dumps(data, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()
        (output / name).write_bytes(content)
        checksums[name] = hashlib.sha256(content).hexdigest()
    (output / "manifest.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "files": checksums,
                "case_sha256": result["runs"][0]["case_sha256"],
                "live_benchmark": "not_run",
                "authority": "advisory_only",
            },
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="outputs/pv_operations")
    parser.add_argument("--input", help="Versioned case JSON; default is explicitly synthetic")
    args = parser.parse_args()
    case = json.loads(Path(args.input).read_text()) if args.input else None
    result = export(args.output, case)
    print(f"3 offline modes: passed={result['all_passed']}, parity={result['report_parity']}")
    if not result["all_passed"] or not result["report_parity"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
