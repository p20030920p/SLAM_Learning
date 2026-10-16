"""Rebuild H1 maps from the recorded A inputs; freeze before inspecting B."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from slam_learning.runtime.own_mapping import RayEvidence, transform

OLD = ROOT / "results/reference/own-hypotheses-20261016"
SUITE = ROOT / "results/reference/h1-conservative-20261016"
METHODS = ("raw", "legacy", "temporal")


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(scene):
    source, out = OLD / (scene + "-A"), SUITE / (scene + "-A")
    assert not (out / "record.json").exists(), "Keep sealed map evidence"
    scans = read(source / "own-scans.json")
    archive = np.load(source / "own-inputs.npz")
    grid = RayEvidence()
    for i, scan in enumerate(scans):
        pose = np.asarray(scan["sensor_pose"])
        grid.add(transform(archive[scan["key"]], pose), pose[:2, 2], scan["stamp_s"])
        if i % 50 == 0:
            print(f"H1 {scene}: replayed A scan {i}/{len(scans)}", flush=True)
    for method in METHODS:
        grid.save(out / "maps" / method, method)
    np.savez_compressed(out / "evidence.npz", hits=grid.hits, free=grid.free,
                        last_support_bin=grid.last_support_bin, clear_bins=grid.clear_bins)
    # Maps and parameters exist before any evaluation references are loaded.
    frozen = {p.relative_to(out).as_posix(): sha(p) for p in (out / "maps").rglob("*") if p.is_file()}
    write(out / "frozen-before-scoring.json", {"maps": frozen, "parameters": {
        "bin_seconds": .5, "support_radius_m": .10, "guard_bins": 1, "required_later_free_bins": 3},
        "source_sha256": sha(ROOT / "src/slam_learning/runtime/own_mapping.py"), "truth_used_in_builder": False})
    refs = np.load(source / "own-score-inputs.npz")
    static, ghosts = refs["static_support"], refs["ghost_support"]
    scores = {}
    for method in METHODS:
        points = np.load(out / "maps" / method / "points.npy")
        tree = cKDTree(points)
        scores[method] = {"points": len(points), "static_retention": float((tree.query(static)[0] <= .15).mean()),
                          "dynamic_removal": float((tree.query(ghosts)[0] > .15).mean()) if len(ghosts) else None}
    write(out / "own-finished.json", {"methods": METHODS, "scans": len(scans), "truth_used": False})
    write(out / "record.json", {"kind": "project_written_mapping_A_input_replay", "status": "executed",
          "A_source": source.relative_to(ROOT).as_posix(), "source_inputs": {
              name: sha(source / name) for name in ("own-inputs.npz", "own-scans.json", "own-odom.json")},
          "scope": "Same recorded A laser endpoints and wheel-derived sensor poses, no truth in builder. Raw/legacy/new maps rebuilt from identical float32 archive. Evaluation uses the original shared A references.",
          "methods": scores, "frozen_map_sha256": frozen,
          "cleaning_criterion_satisfied": scores["temporal"]["static_retention"] >= scores["raw"]["static_retention"] - .01
              and (not len(ghosts) or scores["temporal"]["dynamic_removal"] > scores["raw"]["dynamic_removal"])})
    print(json.dumps({"scene": scene, "scores": scores}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scene", choices=("static", "dynamic"))
    build(parser.parse_args().scene)
