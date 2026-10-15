"""Package actual own-method recordings; scoring truth is read only here."""

import argparse
import hashlib
import json
from pathlib import Path
import shutil

import numpy as np
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation

from package_direction_run import package
from package_session import gif
from score_direction_time_grid import score

ROOT = Path(__file__).resolve().parents[3]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def matrix(xyz, q):
    result = np.eye(4)
    result[:3, :3] = Rotation.from_quat(q).as_matrix()
    result[:3, 3] = xyz
    return result


def unique(points):
    if not len(points):
        return np.empty((0, 2))
    _, ids = np.unique(np.floor(points / .1).astype(int), axis=0, return_index=True)
    return points[ids]


def map_score(run):
    scans = json.loads((run / "own-scans.json").read_text())
    archive = np.load(run / "own-inputs.npz")
    truth = rows(run / "truth.jsonl")
    times = np.array([item["stamp_s"] for item in truth])
    objects = rows(run / "object-truth.jsonl") if (run / "object-truth.jsonl").exists() else []
    geometry = json.loads((run / "object-geometry.json").read_text()) if objects else []
    object_rows = {key: [r for r in objects if r["entity_id"] == key] for g in geometry for key in (g["model_id"], g["link_id"])}
    static, dynamic, sensor_rows, dynamic_times = [], [], [], []
    for scan in scans:
        t = scan["stamp_s"]
        i = np.argmin(np.abs(times - t))
        if abs(times[i] - t) > .05:
            continue
        local = archive[scan["key"]]
        sensor = matrix(truth[i]["xyz"], truth[i]["xyzw"])
        ext = np.asarray(scan["extrinsic"])
        offset = np.eye(4)
        offset[:2, :2], offset[:2, 3], offset[2, 3] = ext[:2, :2], ext[:2, 2], scan["sensor_z"]
        sensor = sensor @ offset
        p = np.column_stack((local, np.zeros(len(local)))) @ sensor[:3, :3].T + sensor[:3, 3]
        labels = np.zeros(len(p), int)
        for g in geometry:
            selected = []
            for key in (g["model_id"], g["link_id"]):
                candidates = object_rows[key]
                if not candidates:
                    break
                selected.append(min(candidates, key=lambda r: abs(r["stamp_s"] - t)))
            if len(selected) != 2 or any(abs(r["stamp_s"] - t) > .05 for r in selected):
                continue
            pose = matrix(selected[0]["xyz"], selected[0]["xyzw"]) @ matrix(selected[1]["xyz"], selected[1]["xyzw"])
            d = np.abs((p - pose[:3, 3]) @ pose[:3, :3]) - np.asarray(g["size_xyz"]) / 2
            positive = (d.max(axis=1) <= .02) & (np.abs(d).min(axis=1) <= .02)
            labels[(d.max(axis=1) <= .05) & ~positive] = -1
            labels[positive] = 1
        static.append(p[labels == 0, :2])
        dynamic.append(p[labels == 1, :2])
        dynamic_times.extend([t] * int((labels == 1).sum()))
        sensor_rows.append((t, sensor, local))
    static = unique(np.concatenate(static))
    dynamic = np.concatenate(dynamic)
    dynamic_times = np.asarray(dynamic_times)
    static_tree = cKDTree(static)
    targets = []
    # A ghost is scored only after a later measured return verifies free space.
    current = dynamic[dynamic_times >= scans[-1]["stamp_s"] - 1] if len(dynamic) else dynamic
    current_tree = cKDTree(current) if len(current) else None
    for point in unique(dynamic):
        if static_tree.query(point)[0] <= .15 or (current_tree and current_tree.query(point)[0] <= .15):
            continue
        appearances = dynamic_times[np.linalg.norm(dynamic - point, axis=1) <= .1]
        first = appearances.min()
        for t, sensor, local in sensor_rows:
            if t < first + 1 or not len(local):
                continue
            q = sensor[:2, :2].T @ (point - sensor[:2, 3])
            angle, distance = np.arctan2(q[1], q[0]), np.linalg.norm(q)
            a = np.arctan2(local[:, 1], local[:, 0])
            diff = np.abs(np.arctan2(np.sin(a - angle), np.cos(a - angle)))
            j = np.argmin(diff)
            if diff[j] * distance < .08 and np.linalg.norm(local[j]) > distance + .2:
                targets.append(point)
                break
    targets = np.asarray(targets).reshape(-1, 2)
    scores = {}
    for folder in sorted((run / "maps").iterdir()):
        points = np.load(folder / "points.npy")
        tree = cKDTree(points)
        scores[folder.name] = {
            "points": len(points),
            "map_rmse_m": float(np.sqrt(np.mean(static_tree.query(points)[0] ** 2))) if len(points) else None,
            "static_retention": float((tree.query(static)[0] <= .15).mean()),
            "dynamic_removal": float((tree.query(targets)[0] > .15).mean()) if len(targets) else None,
        }
    np.savez_compressed(run / "own-score-inputs.npz", static_support=static, ghost_support=targets)
    return {"methods": scores, "static_support_cells": len(static), "verified_ghost_cells": len(targets),
        "scope": "10cm unique observed static support; 15cm coverage; geometry is support-distance RMSE, not exact wall-surface error; truth used only in this post-run scorer"}


def mapping(run, out):
    assert json.loads((run / "session-stopped.json").read_text())["exit_code"] == 0
    assert (run / "own-finished.json").is_file()
    assert not out.exists(), out
    quality = map_score(run)
    out.mkdir(parents=True)
    for name in ("session.json", "runtime.json", "metrics.json", "session-stopped.json", "own-finished.json", "own-scans.json", "own-odom.json", "own-inputs.npz", "own-score-inputs.npz", "truth.jsonl", "object-truth.jsonl", "object-geometry.json", "capture-filter.txt", "capture-progress.txt", "video-probe.json", "execution.mp4"):
        if (run / name).is_file():
            shutil.copyfile(run / name, out / name)
    shutil.copytree(run / "maps", out / "maps")
    shutil.copytree(run / "logs", out / "logs")
    (out / "map-score.json").write_text(json.dumps(quality, indent=2) + "\n")
    timing = gif(out / "execution.mp4", out / "execution.gif")
    (out / "source").mkdir()
    for name in ("src/slam_learning/runtime/own_mapping.py", "src/scripts/presentation/own_live.py", "src/scripts/presentation/package_own_hypotheses.py"):
        shutil.copyfile(ROOT / name, out / "source" / Path(name).name)
    record = {"schema_version": 1, "kind": "project_written_mapping_A", "status": "executed", "exit_code": 0,
        "source_run": str(run), "scope": "Own geometric prototype, native Gazebo rays and wheel odometry, fixed known start; evaluation truth excluded from mapping", "timing": timing, **quality,
        "input_bags": {p.name: {"sha256": sha(p), "bytes": p.stat().st_size, "availability": "local_only"} for p in (run / "input-bag").glob("*.mcap")},
        "artifacts": {p.relative_to(out).as_posix(): {"sha256": sha(p), "bytes": p.stat().st_size, "availability": "portable"} for p in out.rglob("*") if p.is_file()}}
    (out / "record.json").write_text(json.dumps(record, indent=2) + "\n")
    print(out.name, json.dumps(quality))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("run", type=Path)
    parser.add_argument("out", type=Path)
    parser.add_argument("role", choices=("A", "B"))
    args = parser.parse_args()
    if args.role == "A":
        mapping(args.run, args.out)
    else:
        package(args.run, args.out)
        score(args.out)
