"""Verify sealed new-scene cells, CSV measurements and fixed-history controls."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from slam_learning.core.provenance import digest
from slam_learning.runtime.runner import verify_record


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--record", type=Path, default=Path("results/reference/delayed-pose/record.json"))
    parser.add_argument("--raw-suite", type=Path)
    args = parser.parse_args()
    root = args.record.parent
    errors = verify_record(args.record)
    source = json.loads((root / "inputs/record.json").read_text())
    cfg = json.loads((root / "inputs/protocol.json").read_text())
    ann = json.loads((root / "inputs/annotations.json").read_text())
    seal = json.loads((root / "inputs/freeze.json").read_text())
    manifest = json.loads((root / "inputs/source-manifest.json").read_text())
    frontend = json.loads((root / "inputs/frontend-record.json").read_text())
    for key, name in (("protocol_sha256", "protocol.json"), ("annotations_sha256", "annotations.json"),
                      ("source_manifest_sha256", "source-manifest.json")):
        if digest(root / "inputs" / name) != seal[key]:
            errors.append(f"Frozen input differs: {name}")
    if frontend["freeze_sha256"] != digest(root / "inputs/freeze.json"):
        errors.append("Frontend did not bind annotation freeze")
    times = [cfg["design_frozen_at_utc"], manifest["fetched_at"], seal["frozen_at_utc"],
             frontend["started_at"], source["started_at"]]
    parsed_times = [datetime.fromisoformat(t.replace("Z", "+00:00")) for t in times]
    if sorted(parsed_times) != parsed_times:
        errors.append("Design/source/annotation/frontend/mapping freeze order differs")
    if set(cfg["mapping_frames"]) & set(cfg["reference_frames"]):
        errors.append("Reference images enter mapping")
    if frontend["frames"] != cfg["mapping_frames"]:
        errors.append("Frontend frame selection changed")
    if len(source["gates"]) != 7 or not all(g["passed"] for g in source["gates"].values()):
        errors.append("Native or zero-error gate failed")
    settings = [(0., 0)] + [(r, s) for r in cfg["translation_rms_m"] for s in cfg["seeds"]]
    expected = {f"{a}-{r:.2f}-{s}" for a in cfg["arms"] for r, s in settings}
    if {c["name"] for c in source["cells"]} != expected:
        errors.append("Missing/extra experimental cells")
    lookup = {}
    for info in source["cells"]:
        cell_dir = root / "cells" / info["name"]
        path = cell_dir / "record.json"
        if digest(path) != info["record_sha256"]:
            errors.append(f"Changed original cell record: {info['name']}")
        cell = json.loads(path.read_text())
        if cell["status"] != "executed" or [s["observation"] for s in cell["stages"]] != cfg["evaluation_observations"]:
            errors.append(f"Incomplete cell: {info['name']}")
        for stage in cell["stages"]:
            saved = json.loads((cell_dir / f"stage-{stage['observation']:02d}.json").read_text())
            if saved != stage:
                errors.append(f"Stage/record metrics differ: {info['name']}")
            lookup[(cell["arm"], cell["rms_m"], cell["seed"], stage["observation"])] = stage
        artifacts = json.loads((cell_dir / "artifact-manifest.json").read_text())
        for name, artifact in artifacts.items():
            path = cell_dir / name if artifact["availability"] == "portable" else (
                args.raw_suite / "cells" / info["name"] / name if args.raw_suite else None)
            if path is not None and (not path.is_file() or digest(path) != artifact["sha256"]):
                errors.append(f"Cell artifact differs: {info['name']}/{name}")
    prefix_ids = {i["id"] for i in ann["instances"] if i["first_reference_frame"] <=
                  cfg["mapping_frames"][cfg["correction_after_observations"] - 1]}
    with (root / "measurements.csv").open(newline="") as stream:
        measurements = list(csv.DictReader(stream))
    if len(measurements) != len(expected) * len(cfg["evaluation_observations"]):
        errors.append("Measurement row count differs")
    for row in measurements:
        stage = lookup[(row["arm"], float(row["rms_m"]), int(row["seed"]), int(row["observation"]))]
        targets = [t for t in stage["targets"] if t["target"] in prefix_ids]
        for key, field in (("prefix_coverage", "best_coverage"), ("prefix_recovery", "recovered"),
                           ("prefix_query_hit", "restricted_top1_hit")):
            if not np.isclose(float(row[key]), np.mean([t[field] for t in targets]), rtol=0, atol=1e-12):
                errors.append(f"CSV differs: {key}")
    for rms, seed in settings:
        base = root / "cells" / f"native-{rms:.2f}-{seed}"
        fixed = root / "cells" / f"fixed_association-{rms:.2f}-{seed}"
        a = json.loads((base / "decision-trace.json").read_text())[:cfg["correction_after_observations"]]
        b = json.loads((fixed / "decision-trace.json").read_text())[:cfg["correction_after_observations"]]
        if a != b:
            errors.append(f"Fixed-geometry arm did not share native prefix decisions: {rms}/{seed}")
        if args.raw_suite:
            for stage in cfg["evaluation_observations"]:
                zero = args.raw_suite / "cells/native-0.00-0" / f"stage-{stage:02d}.npz"
                oracle = args.raw_suite / "cells" / f"oracle_replay-{rms:.2f}-{seed}" / f"stage-{stage:02d}.npz"
                with np.load(zero) as z, np.load(oracle) as o:
                    if set(z.files) != set(o.files) or any(not np.array_equal(z[k], o[k]) for k in z.files):
                        errors.append(f"Oracle correction did not recover exact zero-error map: {rms}/{seed}/{stage}")
            with np.load(args.raw_suite / "cells" / base.name / "stage-08.npz") as a, np.load(
                args.raw_suite / "cells" / fixed.name / "stage-08.npz"
            ) as b:
                if not np.array_equal(a["features"], b["features"]) or not np.array_equal(
                    a["members_json"], b["members_json"]
                ):
                    errors.append(f"Coordinate control changed semantic membership/features: {rms}/{seed}")
    if errors:
        print("\n".join(errors))
        return 1
    print(f"{len(expected)} delayed-correction cells verified: freeze order, native gates, CSV and fixed histories" +
          ("; local map hashes and oracle/coordinate controls verified" if args.raw_suite else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
