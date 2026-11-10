"""Hourly UTC load data with explicit provenance and forecast availability."""

import csv
import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np


def synthetic_load_case(*, days: int = 18, seed: int = 17) -> dict:
    """Generate a fictional industrial load in MW, never a measured plant record."""
    if type(days) is not int or not 12 <= days <= 32:
        raise ValueError("days must be an integer in 12..32")
    if type(seed) is not int or not 0 <= seed <= 2**32 - 1:
        raise ValueError("seed must be an integer in 0..2**32-1")
    rng = np.random.default_rng(seed)
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    records = []
    weather = 0.0
    for t in range(days * 24):
        weather = 0.85 * weather + rng.normal(0, 0.025)
        hour, day = t % 24, t // 24
        load = (1.2 + 0.22 * np.sin(2 * np.pi * (hour - 7) / 24)
                + 0.12 * (8 <= hour < 18) + 0.07 * np.sin(2 * np.pi * day / 7)
                + weather + rng.normal(0, 0.015))
        records.append({"timestamp": (start + timedelta(hours=t)).isoformat(),
                        "load_mw": round(float(load), 6)})
    return {"schema_version": 1, "classification": "synthetic", "unit": "MW",
            "provenance": {"source": "synthetic_load_case/v1", "license": "MIT",
                           "seed": seed, "description": "Fictional industrial hourly demand"},
            "records": records}


def validate_case(case: dict) -> None:
    """Reject gaps, NaNs, negative loads, non-UTC timestamps and incomplete days.

    The deliberately small research budget is 12..32 complete days. This connector
    is for nonnegative demand, not signed net export or arbitrary SCADA channels.
    """
    if not isinstance(case, dict) or case.get("schema_version") != 1:
        raise ValueError("Expected load case schema_version 1")
    if case.get("unit") != "MW" or case.get("classification") not in {"synthetic", "observed"}:
        raise ValueError("Declare MW and synthetic or observed classification")
    provenance = case.get("provenance")
    if not isinstance(provenance, dict) or any(
        not isinstance(provenance.get(k), str) or not provenance[k].strip()
        for k in ("source", "license", "description")
    ):
        raise ValueError("Provide source, license and description; provenance is user-declared")
    records = case.get("records")
    if not isinstance(records, list) or not 288 <= len(records) <= 768 or len(records) % 24:
        raise ValueError("Supply 12..32 complete hourly days")
    previous = None
    for record in records:
        if not isinstance(record, dict) or set(record) != {"timestamp", "load_mw"}:
            raise ValueError("Records require exactly timestamp and load_mw")
        if not isinstance(record["timestamp"], str):
            raise ValueError("timestamp must be an ISO string")
        stamp = datetime.fromisoformat(record["timestamp"])
        if stamp.utcoffset() != timedelta(0) or stamp.minute or stamp.second or stamp.microsecond:
            raise ValueError("Timestamps must be hourly and explicitly UTC")
        if previous is None and stamp.hour != 0:
            raise ValueError("The first complete day must start at midnight UTC")
        if previous is not None and stamp - previous != timedelta(hours=1):
            raise ValueError("Timestamps must be unique, ordered and contiguous hourly UTC")
        value = record["load_mw"]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not np.isfinite(value):
            raise ValueError("load_mw must be finite numeric data; missing is not zero")
        if not 0 <= value <= 1e6:
            raise ValueError("load_mw must be in 0..1e6")
        previous = stamp


def load_csv(path: str | Path, *, source: str, license: str, description: str) -> dict:
    """Read caller-owned observed data; never silently download or relabel a fixture."""
    path = Path(path)
    if path.stat().st_size > 1_000_000:
        raise ValueError("CSV exceeds the 1 MB research budget")
    raw = path.read_bytes()
    rows = list(csv.DictReader(raw.decode("utf-8-sig").splitlines()))
    if not rows or any(set(r) != {"timestamp", "load_mw"} for r in rows):
        raise ValueError("CSV header must be timestamp,load_mw")
    case = {"schema_version": 1, "classification": "observed", "unit": "MW",
            "provenance": {"source": source, "license": license, "description": description,
                           "source_sha256": hashlib.sha256(raw).hexdigest()},
            "records": [{"timestamp": r["timestamp"], "load_mw": float(r["load_mw"])}
                        for r in rows]}
    validate_case(case)
    return case


def prepare_dataset(case: dict) -> dict:
    """Build daily forecasts using only previous-day measurements and calendar time.

    Every day's 24 forecasts are issued together at 00:00 UTC. Lag-24 and lag-48
    measurements are already available then. This assumes no telemetry delay.
    Training and validation boundaries are whole days; no random time splitting.
    """
    validate_case(case)
    records = case["records"]
    load = np.array([r["load_mw"] for r in records])
    target = np.arange(48, len(load))
    hour = target % 24
    features = np.column_stack((load[target - 24], load[target - 48],
                                np.sin(2 * np.pi * hour / 24),
                                np.cos(2 * np.pi * hour / 24)))
    usable_days = len(target) // 24
    train_end = (usable_days // 2) * 24
    validation_end = train_end + (usable_days // 4) * 24
    return {"x": features, "y": load[target], "persistence": load[target - 24],
            "timestamps": [records[i]["timestamp"] for i in target],
            "forecast_origins": [records[i - i % 24]["timestamp"] for i in target],
            "latest_feature_timestamps": [records[i - 24]["timestamp"] for i in target],
            "train_end": train_end, "validation_end": validation_end,
            "input_sha256": hashlib.sha256(json.dumps(case, sort_keys=True,
                                                       allow_nan=False).encode()).hexdigest()}
