"""Joint own-method H1: supported scan alignment followed by temporal cleaning."""
import json
from pathlib import Path
import shutil
import sys

import numpy as np
from scipy.spatial import cKDTree

from h1_revision import ROOT, OLD, read, write, sha
sys.path.insert(0, str(ROOT / "src"))
from slam_learning.runtime.own_mapping import RayEvidence, transform
from slam_learning.runtime.own_refinement import refine_scan_pose

SUITE = ROOT / "results/reference/h1-refined-20261016"
METHODS = ("raw", "filter_only", "align_only", "temporal")


def process(scans, archive):
    base, aligned = RayEvidence(), RayEvidence()
    previous_wheel = previous_estimate = None
    for i, scan in enumerate(scans):
        wheel = np.asarray(scan["sensor_pose"])
        local = archive[scan["key"]]
        predicted = wheel if previous_wheel is None else previous_estimate @ np.linalg.inv(previous_wheel) @ wheel
        support = aligned.mask("temporal") & (aligned.support_hits >= 3)
        reference = aligned.origin + (np.argwhere(support)[:, ::-1] + .5) * aligned.resolution
        estimate = refine_scan_pose(local, predicted, reference)
        base.add(transform(local, wheel), wheel[:2, 2], scan["stamp_s"])
        aligned.add(transform(local, estimate), estimate[:2, 2], scan["stamp_s"])
        previous_wheel, previous_estimate = wheel, estimate
        yield i, base, aligned, estimate


def build(scene):
    source, out = OLD / (scene + "-A"), SUITE / (scene + "-A")
    assert not (out / "record.json").exists()
    out.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source / "runtime.json", out / "runtime.json")
    scans = read(source / "own-scans.json")
    archive = np.load(source / "own-inputs.npz")
    estimates = []
    for i, base, aligned, estimate in process(scans, archive):
        estimates.append(estimate.copy())
        if i % 50 == 0:
            print(f"REFINED A {scene}: {i}/{len(scans)}", flush=True)
    base.save(out / "maps/raw", "raw")
    base.save(out / "maps/filter_only", "temporal")
    aligned.save(out / "maps/align_only", "raw")
    aligned.save(out / "maps/temporal", "temporal")
    np.save(out / "estimated-sensor-poses.npy", estimates)
    frozen = {p.relative_to(out).as_posix(): sha(p) for p in (out / "maps").rglob("*") if p.is_file()}
    write(out / "frozen-before-scoring.json", {"maps": frozen, "algorithm_sources": {
        name: sha(ROOT / "src/slam_learning/runtime" / name) for name in ("own_mapping.py", "own_refinement.py")},
        "truth_used_in_builder": False, "parameters": {"time_bin_s": .5, "neighborhood_m": .10,
        "free_bins": 3, "free_support_ratio": 1.5, "match_distance_m": .30, "trim_fraction": .70,
        "Huber_distance_m": .05, "max_correction_m": .15, "max_correction_rad": .05, "iterations": 12}})
    # Only now load evaluation references and truth.
    refs = np.load(source / "own-score-inputs.npz")
    static, ghosts = refs["static_support"], refs["ghost_support"]
    quality = {}
    for method in METHODS:
        points = np.load(out / "maps" / method / "points.npy")
        tree = cKDTree(points)
        quality[method] = {"points": len(points), "static_retention": float((tree.query(static)[0] <= .15).mean()),
                           "dynamic_removal": float((tree.query(ghosts)[0] > .15).mean()) if len(ghosts) else None}
    truth = [json.loads(row) for row in (source / "truth.jsonl").read_text().splitlines()]
    times = np.array([r["stamp_s"] for r in truth])
    truth_sensor = []
    from scipy.spatial.transform import Rotation
    for scan in scans:
        row = truth[np.argmin(abs(times - scan["stamp_s"]))]
        rotation = Rotation.from_quat(row["xyzw"]).as_matrix()[:2, :2]
        truth_sensor.append(np.asarray(row["xyz"][:2]) + rotation @ np.asarray(scan["extrinsic"])[:2, 2])
    truth_sensor = np.asarray(truth_sensor)
    pose_score = {"wheel_rmse_m": float(np.sqrt(np.mean(np.sum((np.array([r["sensor_pose"] for r in scans])[:, :2, 2] - truth_sensor)**2, axis=1)))),
                  "aligned_rmse_m": float(np.sqrt(np.mean(np.sum((np.asarray(estimates)[:, :2, 2] - truth_sensor)**2, axis=1))))}
    write(out / "own-finished.json", {"methods": ("raw", "temporal"), "diagnostic_methods": METHODS, "truth_used": False})
    write(out / "record.json", {"status": "executed", "kind": "own_static_support_alignment_and_cleaning",
          "A_source": source.relative_to(ROOT).as_posix(), "methods": quality, "pose_diagnostic": pose_score,
          "frozen_map_sha256": frozen, "truth_used_by_algorithm": False,
          "scope": "Same recorded A. Raw uses wheel poses; filter_only adds cleaning; align_only adds own robust SE(2) alignment; temporal combines both. Truth only enters post-run scoring. This is a joint mapping intervention, not a pure-deletion claim."})
    print(json.dumps({"scene": scene, "quality": quality, "pose_diagnostic": pose_score}), flush=True)


if __name__ == "__main__":
    build(sys.argv[1])
