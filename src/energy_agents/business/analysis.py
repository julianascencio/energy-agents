"""Reproducible BESS stress-case exports and sensitivity analysis."""

import argparse
import hashlib
import json
from copy import deepcopy
from pathlib import Path

from .bess import reference_case, run_bess_agent, stress_revenues


def export(output, case=None):
    case = reference_case() if case is None else case
    result = run_bess_agent(case)
    baseline = stress_revenues(case)
    parity = result["reports"].get("screen") == baseline
    sensitivity = []
    for discount in (0.06, 0.10, 0.14):
        altered = deepcopy(case)
        altered["assumptions"]["discount_rate"] = discount
        values = stress_revenues(altered)
        sensitivity.append(
            {
                "discount_rate": discount,
                "npv_eur": {k: v["npv_eur"] for k, v in values["scenarios"].items()},
            }
        )
    report = {
        "run": result,
        "deterministic_parity": parity,
        "sensitivity": sensitivity,
        "llm_tokens": None,
        "llm_cost": None,
        "live_llm": "not_run",
    }
    target = Path(output)
    target.mkdir(parents=True, exist_ok=True)
    checksums = {}
    for name, data in {"case.json": case, "results.json": report}.items():
        raw = (json.dumps(data, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
        (target / name).write_bytes(raw)
        checksums[name] = hashlib.sha256(raw).hexdigest()
    (target / "manifest.json").write_text(json.dumps(checksums, sort_keys=True, indent=2) + "\n")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="outputs/bess_saturation")
    parser.add_argument("--input")
    parser.add_argument("--edi-catalogue", help="Optional local EDI catalogues/bess path")
    args = parser.parse_args()
    case = json.loads(Path(args.input).read_text()) if args.input else None
    report = export(args.output, case)
    if args.edi_catalogue:
        from .edi import inspect_bess_inventory

        inventory = inspect_bess_inventory(args.edi_catalogue)
        Path(args.output, "edi_inventory.json").write_text(json.dumps(inventory, indent=2) + "\n")
    if not report["run"]["success"] or not report["deterministic_parity"]:
        raise SystemExit("Workflow failed")
    for name, values in report["run"]["reports"]["screen"]["scenarios"].items():
        print(
            f"{name}: NPV EUR {values['npv_eur']:,.0f}; upfront budget EUR {values['zero_npv_upfront_budget_eur']:,.0f}"
        )


if __name__ == "__main__":
    main()
