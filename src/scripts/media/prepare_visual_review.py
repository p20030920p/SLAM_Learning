"""Prepare traceable, thinned measured outputs for an actual RViz inspection.

No mapper or front end is executed here. Pickles must be trusted local author outputs.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from slam_learning.core.pcd import read_pcd
from slam_learning.core.provenance import digest
from slam_learning.runtime.runner import verify_record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("method", choices=("dufomap", "beautymap"))
    parser.add_argument("record", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--dataset", type=Path)
    args = parser.parse_args()
    issues = verify_record(args.record, full=True)
    record = json.loads(args.record.read_text())
    if issues or record.get("status") != "executed":
        raise ValueError(f"Completed full local evidence required: {issues}")
    run = args.record.parent
    args.output.mkdir(parents=True, exist_ok=False)
    sources = {str(args.record.resolve()): digest(args.record)}
    steps = []

    def bound(path):
        sources[str(path.resolve())] = digest(path)
        return path

    def save(xyz, colors, label):
        xyz = np.asarray(xyz, dtype=np.float32)
        colors = np.broadcast_to(np.asarray(colors, dtype=np.uint8), xyz.shape).copy()
        selection = np.linspace(0, len(xyz)-1, min(len(xyz), 120000), dtype=int)
        path = args.output / f"{len(steps):03d}.npz"
        np.savez_compressed(path, xyz=xyz[selection], rgb=colors[selection])
        steps.append({"file": path.name, "sha256": digest(path), "label": label,
                      "source_index": None, "input_points": len(xyz),
                      "display_points": len(selection)})

    if args.dataset is None or record.get("kind") != "map_evaluator_cross_check":
        raise ValueError("LiDAR review requires the native evaluator record and --dataset")
    if record.get("total_disagreement_points") != 0:
        raise ValueError("Resolve evaluator disagreements before visual publication")
    gt_path = bound(args.dataset / "gt_cloud.pcd")
    gt = read_pcd(gt_path)
    manifest_path = bound(args.dataset / "provenance.json")
    manifest = json.loads(manifest_path.read_text())
    if digest(gt_path) != manifest["files"]["gt_cloud.pcd"]:
        raise ValueError("Dataset hash mismatch")
    predicted = read_pcd(bound(run / args.method / "eval/cleaned_exportGT.pcd"))
    if len(predicted.records) != len(gt.records):
        raise ValueError("Evaluator point count mismatch")
    # First 21 source scans, same point sample in all stages. Scoring used all 141.
    paths = sorted((args.dataset / "pcd").glob("*.pcd"))[:21]
    n = sum(len(read_pcd(p).records) for p in paths)
    idx = np.arange(0, n, 12)
    idx = idx[np.linspace(0, len(idx)-1, min(len(idx), 120000), dtype=int)]
    xyz = gt.xyz(idx)
    if not np.array_equal(xyz, predicted.xyz(idx)):
        raise ValueError("Evaluator identities differ")
    dynamic = np.asarray(gt.records["intensity"][idx]) == 1
    removed = np.asarray(predicted.records["intensity"][idx]) == 1
    colors = np.full(xyz.shape, [160, 176, 190], dtype=np.uint8)
    colors[dynamic & removed] = [70, 220, 130]
    colors[~dynamic & removed] = [255, 80, 80]
    colors[dynamic & ~removed] = [70, 145, 255]
    save(xyz, colors, "INPUT | GT colors for inspection only | 21 selected scans")
    save(xyz[removed], colors[removed], "REMOVED | green dynamic / red static loss")
    save(xyz[~removed], colors[~removed], "RETAINED | gray static / blue dynamic leakage")
    save(xyz, colors, "INPUT again | final-map decisions, not online growth")
    combined = np.concatenate([np.load(args.output / s["file"])["xyz"] for s in steps])
    lower, upper = np.quantile(combined, [.01, .99], axis=0)
    manifest = {"schema_version": 1, "method": args.method, "kind": "measured_output_rviz_review",
                "scope": "Recorded graphical inspection of saved measured outputs; no new inference or FPS claim",
                "generator_sha256": digest(Path(__file__)), "sources": sources, "steps": steps,
                "display_transform": "none; stored maps unchanged",
                "focal_point": ((lower+upper)/2).tolist(), "distance": float(np.linalg.norm(upper-lower)*1.15)}
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2)+"\n")
    print(args.output / "manifest.json", flush=True)


if __name__ == "__main__":
    main()
