"""Build, inspect and search the Energy Data Insights capability catalogue."""

import argparse
import json

from .agent import EnergyDataInsightsAgent
from .catalogue import build_catalogue, load_catalogue, save_catalogue


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    refresh = commands.add_parser(
        "refresh", help="Index a local Git checkout without running its code"
    )
    refresh.add_argument("checkout")
    refresh.add_argument("--ref", default="HEAD")
    refresh.add_argument("--output", required=True)
    for name in ("search", "inventory"):
        command = commands.add_parser(name)
        command.add_argument("--catalogue")
        if name == "search":
            command.add_argument("query")
            command.add_argument("--category")
            command.add_argument("--limit", type=int, default=8)
    args = parser.parse_args()
    if args.command == "refresh":
        catalogue = build_catalogue(args.checkout, args.ref)
        if catalogue["coverage"]["errors"]:
            raise SystemExit(json.dumps(catalogue["coverage"], indent=2))
        save_catalogue(catalogue, args.output)
        result = {k: catalogue[k] for k in ("repository", "commit", "coverage")}
    else:
        agent = EnergyDataInsightsAgent(load_catalogue(args.catalogue))
        result = (
            agent.inventory()
            if args.command == "inventory"
            else agent.search(args.query, limit=args.limit, category=args.category)
        )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
