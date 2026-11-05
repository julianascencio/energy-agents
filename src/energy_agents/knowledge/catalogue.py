"""Build a source-derived capability catalogue without importing repository code."""

import ast
import gzip
import hashlib
import json
import re
import subprocess
from collections import Counter
from importlib.resources import files
from pathlib import Path, PurePosixPath

REPOSITORY = "julianascencio/energy-data-insights"
SOURCE_ROOTS = {
    "data-retrieval/src/": "connector",
    "methods/src/": "method",
    "analysis/src/": "analysis",
    "examples/": "example",
    "docs/": "documentation",
    "scripts/": "script",
    "benchmarks/": "benchmark",
}
TEXT_SUFFIXES = {".py", ".md", ".rst", ".toml", ".txt"}


def category(path):
    """Classify supported capability content; exclude data, tests and vendored assets."""
    p = PurePosixPath(path)
    if p.suffix not in TEXT_SUFFIXES:
        return None
    if any(
        part in {"data", "_static", "_build", "_generated", "reports", "tests"} for part in p.parts
    ):
        return None
    if p.name == "pyproject.toml":
        return "package"
    if path in {"README.md", "CONTRIBUTING.md"}:
        return "documentation"
    if path.startswith("catalogues/") and p.name == "README.md":
        return "documentation"
    for prefix, kind in SOURCE_ROOTS.items():
        if path.startswith(prefix):
            return kind
    if path in {"data-retrieval/README.md", "methods/README.md", "analysis/README.md"}:
        return "documentation"
    return None


def _symbols(tree):
    result = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.name.startswith("_"):
                continue
            entries = [(node.name, node)]
            if isinstance(node, ast.ClassDef):
                entries += [
                    (f"{node.name}.{child.name}", child)
                    for child in node.body
                    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and not child.name.startswith("_")
                ]
            for name, child in entries:
                signature = ast.unparse(child.args) if hasattr(child, "args") else ""
                result.append(
                    {
                        "name": name,
                        "line": child.lineno,
                        "signature": signature,
                        "summary": (ast.get_docstring(child) or "")[:600],
                    }
                )
    return result


def describe(path, raw, commit):
    """Extract documentation and public symbol signatures with immutable citations."""
    text = raw.decode("utf-8")
    tree = ast.parse(text) if path.endswith(".py") else None
    doc = ast.get_docstring(tree) or "" if tree is not None else text
    title = next((line.strip("# ") for line in doc.splitlines() if line.strip()), path)
    symbols = _symbols(tree) if tree is not None else []
    imports = []
    if tree is not None:
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
            elif isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
    module = None
    if "/src/" in path and path.endswith(".py"):
        module = path.split("/src/", 1)[1][:-3].replace("/", ".").removesuffix(".__init__")
    return {
        "path": path,
        "category": category(path),
        "title": title[:200],
        "summary": doc[:2400],
        "summary_truncated": len(doc) > 2400,
        "symbols": symbols,
        "imports": sorted(set(imports)),
        "module": module,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "source_url": f"https://github.com/{REPOSITORY}/blob/{commit}/{path}",
        "runnable_example": path.startswith("examples/")
        and path.endswith(".py")
        and PurePosixPath(path).name.startswith("plot_"),
        "execution_status": "not_executed_by_catalogue",
    }


def build_catalogue(checkout, ref="HEAD"):
    """Index committed Git blobs, ignoring dirty/untracked working-tree changes.

    All files in scope are accounted for; decode/parse errors appear in the
    manifest and prevent a claim of complete coverage. No source is imported.
    """
    root = Path(checkout).resolve()

    def git(*args):
        return subprocess.check_output(["git", "-C", str(root), *args])

    commit = git("rev-parse", "--verify", f"{ref}^{{commit}}").decode().strip()
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("Expected full Git commit SHA")
    paths = git("ls-tree", "-r", "--name-only", "-z", commit).decode().split("\0")
    selected = sorted(path for path in paths if path and category(path))
    entries, errors = [], []
    for path in selected:
        try:
            entries.append(describe(path, git("show", f"{commit}:{path}"), commit))
        except (UnicodeError, SyntaxError, ValueError) as exc:
            errors.append({"path": path, "error": str(exc)})
    snapshot = {
        "schema_version": "1.0",
        "repository": REPOSITORY,
        "commit": commit,
        "commit_date": git("show", "-s", "--format=%cI", commit).decode().strip(),
        "coverage": {
            "selected_files": len(selected),
            "indexed_files": len(entries),
            "categories": dict(sorted(Counter(e["category"] for e in entries).items())),
            "gallery_examples": sum(e["runnable_example"] for e in entries),
            "public_symbols": sum(len(e["symbols"]) for e in entries),
            "errors": errors,
            "complete_within_scope": not errors,
        },
        "scope": "Committed Python and text documentation in packages, examples, docs, scripts and benchmarks; data, tests, reports and vendored assets excluded",
        "entries": entries,
    }
    return snapshot


def save_catalogue(catalogue, output):
    """Write byte-reproducible compressed JSON (no generation timestamp)."""
    raw = json.dumps(catalogue, sort_keys=True, separators=(",", ":")).encode()
    Path(output).write_bytes(gzip.compress(raw, mtime=0))


def load_catalogue(path=None):
    """Read the shipped pinned snapshot or an explicitly refreshed one."""
    raw = (
        Path(path).read_bytes()
        if path
        else files("energy_agents").joinpath("data/energy_data_insights.json.gz").read_bytes()
    )
    catalogue = json.loads(gzip.decompress(raw))
    if catalogue.get("schema_version") != "1.0" or catalogue.get("repository") != REPOSITORY:
        raise ValueError("Unsupported repository catalogue")
    return catalogue
