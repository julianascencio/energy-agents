"""Run a portfolio review and export a portable report, evidence and work-order drafts."""

import argparse
import hashlib
import json
from pathlib import Path

from .report import render_report
from .service import OperationsService, synthetic_portfolio


def export_review(portfolio, output):
    service = OperationsService(portfolio)
    result = service.review_portfolio()
    drafts = [
        service.draft_work_order(a["asset_id"], action["action_id"])
        for a in result["assets"]
        for action in a["actions"]
    ]
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    files = {"input.json": portfolio, "portfolio.json": result, "work_orders.json": drafts}
    for name, data in files.items():
        (output / name).write_text(
            json.dumps(data, indent=2, allow_nan=False) + "\n", encoding="utf-8"
        )
    (output / "report.html").write_text(render_report(result), encoding="utf-8")
    manifest = {
        name: hashlib.sha256((output / name).read_bytes()).hexdigest()
        for name in [*files, "report.html"]
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input", type=Path, help="Portfolio JSON; default: four synthetic PV sites"
    )
    parser.add_argument("--output", type=Path, default=Path("outputs/operations"))
    args = parser.parse_args()
    portfolio = json.loads(args.input.read_text()) if args.input else synthetic_portfolio()
    result = export_review(portfolio, args.output)
    print(f"Reviewed {len(result['assets'])} assets. Report: {args.output / 'report.html'}")


if __name__ == "__main__":
    main()
