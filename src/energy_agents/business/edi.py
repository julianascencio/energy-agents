"""Optional read-only adapter to Energy Data Insights' existing BESS loader."""

import hashlib
import json
from collections import Counter
from pathlib import Path


def inspect_bess_inventory(catalogue_root, country_code="POL"):
    """Use EDI's real loader and schema validator, without inferring commissioned MW.

    Install energy-data-retrieval from the documented pinned checkout first.
    This inventory is context only and is never used to calibrate revenue paths.
    """
    from energy_data_retrieval.bess_catalogue.catalogue import load_records, validate_record

    root = Path(catalogue_root)
    if not (root / "records").is_dir() or not (root / "sources.json").is_file():
        raise ValueError("Expected a BESS catalogue with records and sources.json")
    sources = json.loads((root / "sources.json").read_text())
    rows = [r for r in load_records(root) if r.get("country_code") == country_code]
    for row in rows:
        validate_record(row, sources)
    return {
        "country_code": country_code,
        "records": len(rows),
        "status_counts": dict(sorted(Counter(r.get("status", "unknown") for r in rows).items())),
        "record_ids": [r["record_id"] for r in rows],
        "input_sha256": hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest(),
        "adapter": "energy_data_retrieval.bess_catalogue.catalogue.load_records + validate_record",
        "limitation": "Incomplete inventory; phases/groups may overlap; no market capacity sum or saturation inference",
    }
