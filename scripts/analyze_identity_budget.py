"""Recompute v2 readouts from complete immutable snapshots; never run a mapper."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from slam_learning.delayed_pose import reference_instances
from slam_learning.identity_budget import (
    ARMS, digest, hypothesis_decision, load_snapshot, metric_cache, scan_readouts, validate_freeze,
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    record = json.loads((args.run / "record.json").read_text())
    cfg = json.loads((args.run / "protocol.json").read_text())
    exploratory = record.get("analysis_type") == "ai_only_exploratory"
    validate_freeze(args.run / "protocol.json", args.run / "annotations.json", args.data,
                    json.loads((args.run / "freeze.json").read_text()), exploratory=exploratory)
    if (record["status"] != "executed" or len(record["cells"]) != 28 or not record["gates"] or
            not all(g["passed"] for g in record["gates"].values())):
        raise ValueError("Complete successful suite and zero/native parity gates required")
    root = Path(__file__).resolve().parents[1]
    if digest(args.run / "executed-budget-metrics.py") != digest(root / "src/slam_learning/identity_budget.py"):
        raise ValueError("Changed metrics code: declare a separately versioned post-hoc analysis")
    if digest(args.run / "executed-metrics.py") != digest(root / "src/slam_learning/delayed_pose.py"):
        raise ValueError("Changed reference-surface code")
    for name, info in record["artifacts"].items():
        if digest(args.run / name) != info["sha256"]:
            raise ValueError(f"Changed run artifact: {name}")
    instances = reference_instances(args.run / "annotations.json", args.data)
    text = np.load(args.run / "text_features.npy", allow_pickle=False)
    rows, input_hashes, seen = [], {}, set()
    for entry in record["cells"]:
        folder = args.run / "cells" / entry["name"]
        if digest(folder / "record.json") != entry["record_sha256"]:
            raise ValueError("Changed cell record")
        cell = json.loads((folder / "record.json").read_text())
        key = (cell["arm"], cell["rms_m"], cell["seed"])
        if key in seen or cell["status"] != "executed":
            raise ValueError("Repeated or failed cell")
        seen.add(key)
        for name, info in cell["artifacts"].items():
            if digest(folder / name) != info["sha256"]:
                raise ValueError(f"Changed cell artifact: {name}")
        if cell["arm"] != "oracle_replay" and not cell["fixed_members_and_features_preserved"]:
            raise ValueError("Fixed-membership gate missing")
        for stage in cell["stages"]:
            obs = stage["observation"]
            path = folder / f"stage-{obs:02d}-complete.npz"
            if digest(path) != stage["snapshot_sha256"]:
                raise ValueError("Changed complete snapshot")
            state = load_snapshot(path)
            if state["metadata"]["freeze_sha256"] != record["freeze_sha256"]:
                raise ValueError("Snapshot belongs to another freeze")
            cache = metric_cache(state, text, instances, cfg, cfg["mapping_frames"][obs - 1])
            readouts = scan_readouts(state, cache, cfg)
            if readouts != stage["readouts"]:
                raise ValueError("Recomputed metrics differ from executed readouts")
            for metric in readouts:
                rows.append({**metric, "arm": cell["arm"], "rms_m": cell["rms_m"], "seed": cell["seed"],
                             "observation": obs, "snapshot_bytes": path.stat().st_size,
                             "correction_compute_seconds": cell["correction_compute_seconds"]})
            input_hashes[path.relative_to(args.run).as_posix()] = digest(path)
    expected = {(arm, rms, seed) for arm in ARMS for rms, seed in
                [(0., 0)] + [(r, s) for r in cfg["translation_rms_m"] for s in cfg["seeds"]]}
    if seen != expected or len(rows) != 28 * 3 * 12:
        raise ValueError("Incomplete cell/stage/readout matrix")
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "readouts.json").write_text(json.dumps(rows, indent=2, allow_nan=False) + "\n")
    scalars = [k for k in rows[0] if k not in ("instances", "category_queries", "selected_object_ids")]
    with (args.output / "readouts.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=scalars)
        writer.writeheader()
        writer.writerows({k: row[k] for k in scalars} for row in rows)
    decision = hypothesis_decision(rows, cfg)
    decision.update(analysis_type=record.get("analysis_type"), human_reviewed=not exploratory,
                    interpretation="Exploratory screening only; AI-only identity labels do not verify H1."
                    if exploratory else "Protocol screen only; passing does not verify H1.")
    (args.output / "decision.json").write_text(json.dumps(decision, indent=2) + "\n")
    (args.output / "inputs.json").write_text(json.dumps({"run_record_sha256": digest(args.run / "record.json"),
        "complete_states": input_hashes, "budget_claim": cfg["budget_claim"], "mapping_cells": 28,
        "readout_rows": len(rows), "analysis_type": record.get("analysis_type")}, indent=2) + "\n")
    print(f"Recomputed {len(rows)} readouts; {decision['status']}; H1 remains unverified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
