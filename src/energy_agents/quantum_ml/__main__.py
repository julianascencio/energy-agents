"""Run and export the bounded quantum ML research workflow."""

import argparse
import hashlib
import importlib.metadata
import json
import platform
from pathlib import Path

from .agent import quantum_context, run_quantum_ml_agent
from .inputs import load_csv, synthetic_load_case


def export_result(case: dict, result: dict, output: Path) -> None:
    """Preserve inputs, reports, context, versions and SHA256 checksums."""
    output.mkdir(parents=True, exist_ok=True)
    versions = {"python": platform.python_version()}
    for name in ("energy-agents", "numpy", "pennylane", "torch", "qiskit"):
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = "not_installed"
    payloads = {"input.json": case, "result.json": result,
                "research_context.json": quantum_context(), "environment.json": versions}
    checksums = {}
    for name, payload in payloads.items():
        raw = (json.dumps(payload, indent=2, allow_nan=False) + "\n").encode()
        (output / name).write_bytes(raw)
        checksums[name] = hashlib.sha256(raw).hexdigest()
    (output / "manifest.json").write_text(json.dumps(checksums, indent=2) + "\n", encoding="utf-8")


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("outputs/quantum_ml"))
    parser.add_argument("--hybrid", action="store_true", help="Also train PennyLane/Torch models")
    parser.add_argument("--input-csv", type=Path, help="Observed hourly UTC timestamp,load_mw")
    parser.add_argument("--source")
    parser.add_argument("--license")
    parser.add_argument("--description")
    parser.add_argument("--as-of", help="Literature-review date YYYY-MM-DD; default today UTC")
    parser.add_argument("--refresh-literature", action="store_true",
                        help="Opt in to one bounded live arXiv metadata request")
    args = parser.parse_args(argv)
    if args.input_csv:
        if not all((args.source, args.license, args.description)):
            parser.error("Observed data requires --source, --license and --description")
        case = load_csv(args.input_csv, source=args.source, license=args.license,
                        description=args.description)
    else:
        case = synthetic_load_case()
    result = run_quantum_ml_agent(case, include_hybrid=args.hybrid, as_of=args.as_of,
                                 refresh_literature=args.refresh_literature)
    export_result(case, result, args.output)
    if not result["success"]:
        raise SystemExit(f"Research workflow failed; inspect {args.output / 'result.json'}")
    for row in result["reports"]["forecast"]["rows"]:
        print(f"{row['model']:28s} test MAE {row['test']['mae_mw']:.5f} MW")
    print(f"Exported {case['classification']} research case to {args.output}")


if __name__ == "__main__":
    main()
