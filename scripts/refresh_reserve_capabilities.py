"""Refresh a focused source-derived EDI capability catalogue from committed Git blobs."""
import argparse
import ast
import hashlib
import json
import subprocess
from pathlib import Path

PATHS = [
    'methods/src/energy_methods/storage_peak_shift.py',
    'methods/src/energy_methods/hybrid_dispatch.py',
    'examples/analysis/plot_india_storage_mandate.py',
    'methods/pyproject.toml', 'LICENSE',
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('checkout')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()

    def git(*parts):
        return subprocess.check_output(['git', '-C', args.checkout, *parts])

    commit = git('rev-parse', 'HEAD').decode().strip()
    entries = []
    for path in PATHS:
        raw = git('show', f'{commit}:{path}')
        symbols = []
        if path.endswith('.py'):
            tree = ast.parse(raw)
            symbols = [{'name': n.name, 'line': n.lineno,
                        'signature': ast.unparse(n.args) if hasattr(n, 'args') else ''}
                       for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))]
        entries.append({'path': path, 'sha256': hashlib.sha256(raw).hexdigest(),
                        'symbols': symbols,
                        'url': f'https://github.com/julianascencio/energy-data-insights/blob/{commit}/{path}'})
    args.output.write_text(json.dumps({
        'repository': 'julianascencio/energy-data-insights', 'commit': commit,
        'scope': 'Focused five-file source catalogue, not full inventory',
        'entries': entries, 'discovery_is_execution': False}, indent=2) + '\n')


if __name__ == '__main__':
    main()
