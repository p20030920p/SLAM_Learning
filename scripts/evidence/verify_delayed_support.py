"""Verify the separate post-hoc support control against its primary parent."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from slam_learning.core.provenance import digest
from slam_learning.runtime.runner import verify_record


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--record", type=Path,
                        default=Path("results/reference/delayed-support-control/record.json"))
    parser.add_argument("--primary", type=Path, default=Path("results/reference/delayed-pose"))
    parser.add_argument("--raw-followup", type=Path)
    args = parser.parse_args()
    root = args.record.parent
    errors = verify_record(args.record) + verify_record(args.primary / "record.json")
    public = json.loads(args.record.read_text())
    raw = json.loads((root / "inputs/record.json").read_text())
    parent = json.loads((args.primary / "inputs/record.json").read_text())
    cfg = parent["configuration"]
    if raw["configuration"] != cfg or raw["freeze_sha256"] != parent["freeze_sha256"]:
        errors.append("Frozen primary configuration or input seal differs")
    for name in ("protocol.json", "annotations.json", "source-manifest.json", "frontend-record.json",
                 "executed-metrics.py"):
        if raw["artifacts"][name]["sha256"] != digest(args.primary / "inputs" / name):
            errors.append(f"Post-hoc source differs from primary: {name}")
    if public["primary_analysis_sha256"] != digest(args.primary / "record.json") or (
        raw["primary_parent_sha256"] != digest(args.primary / "inputs/record.json")
    ):
        errors.append("Post-hoc parent differs")
    if raw["status"] != "executed" or raw["kind"] != "posthoc_support_control" or raw["execution_subset"] != {
        "arms": ["fixed_association"], "obj_min_detections": 1, "declared_after_primary_inspection": True
    } or raw["inherited_parent_gates"] != parent["gates"]:
        errors.append("Post-hoc scope or inherited gates changed")
    expected = {f"fixed_association-{r:.2f}-{s}" for r in cfg["translation_rms_m"] for s in cfg["seeds"]}
    if {c["name"] for c in raw["cells"]} != expected or len(raw["cells"]) != 6:
        errors.append("Expected all six post-hoc cells")
    ann = json.loads((args.primary / "inputs/annotations.json").read_text())
    prefix_ids = {i["id"] for i in ann["instances"] if i["first_reference_frame"] <= cfg["mapping_frames"][7]}
    lookup = {}
    for info in raw["cells"]:
        directory = root / "cells" / info["name"]
        cell = json.loads((directory / "record.json").read_text())
        if digest(directory / "record.json") != info["record_sha256"] or cell["status"] != "executed":
            errors.append(f"Incomplete or changed cell: {info['name']}")
        original = json.loads((args.primary / "cells" / info["name"] / "decision-trace.json").read_text())[:8]
        followup = json.loads((directory / "decision-trace.json").read_text())[:8]
        if original != followup:
            errors.append(f"Historical associations differ: {info['name']}")
        if [s["observation"] for s in cell["stages"]] != cfg["evaluation_observations"]:
            errors.append(f"Incomplete stages: {info['name']}")
        for stage in cell["stages"]:
            if json.loads((directory / f"stage-{stage['observation']:02d}.json").read_text()) != stage:
                errors.append(f"Stage differs: {info['name']}")
            lookup[(cell["rms_m"], cell["seed"], stage["observation"])] = stage
        manifest = json.loads((directory / "artifact-manifest.json").read_text())
        for name, artifact in manifest.items():
            path = directory / name if artifact["availability"] == "portable" else (
                args.raw_followup / "cells" / info["name"] / name if args.raw_followup else None)
            if path is not None and (not path.is_file() or digest(path) != artifact["sha256"]):
                errors.append(f"Artifact differs: {info['name']}/{name}")
    with (root / "measurements.csv").open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) != 18:
        errors.append("Expected 18 stage rows")
    for row in rows:
        stage = lookup[(float(row["rms_m"]), int(row["seed"]), int(row["observation"]))]
        targets = [t for t in stage["targets"] if t["target"] in prefix_ids]
        for key, field in (("prefix_coverage", "best_coverage"), ("prefix_recovery", "recovered"),
                           ("prefix_query_hit", "restricted_top1_hit")):
            if not np.isclose(float(row[key]), np.mean([t[field] for t in targets]), rtol=0, atol=1e-12):
                errors.append(f"CSV differs: {key}")
        for key in ("map_objects", "fragment_count"):
            if int(row[key]) != stage[key]:
                errors.append(f"CSV differs: {key}")
    print("\n".join(errors) if errors else "Six post-hoc controls verified: parent, scope, fixed histories and CSV" +
          ("; local maps verified" if args.raw_followup else ""))
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
