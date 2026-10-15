"""Score native 2D map coverage and independently timestamped mapper events.

SA: unique observed static 10cm support covered within 15cm. DA: historical
dynamic support that later real scan rays verify free, excluding static support
and currently occupied dynamic support. Fused points are not exact deletion
masks. Truth never enters the online mapper.
"""

import argparse
import json
from pathlib import Path
import numpy as np
import xml.etree.ElementTree as ET
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation


def matrix(xyz, q):
    m = np.eye(4)
    m[:3, :3] = Rotation.from_quat(q).as_matrix()
    m[:3, 3] = xyz
    return m


def nearest(rows, t, limit=0.05):
    times = np.array([r["stamp_s"] for r in rows])
    i = int(np.argmin(abs(times - t)))
    if abs(times[i] - t) > limit:
        raise ValueError(f"Unsynchronized truth {t} delta {abs(times[i]-t)}")
    return rows[i]


def read_rows(p):
    result = []
    for i, line in enumerate(p.read_text().splitlines()):
        if not line:
            continue
        try:
            result.append(json.loads(line))
        except json.JSONDecodeError:
            if i != len(p.read_text().splitlines()) - 1:
                raise
    return result


def unique(points, resolution=0.1):
    if not len(points):
        return np.empty((0, 2))
    _, idx = np.unique(np.floor(points / resolution).astype(int), axis=0, return_index=True)
    return points[idx]


def evaluate(run):
    frames = read_rows(run / "srrg-frames.jsonl")
    scans = read_rows(run / "srrg-inputs.jsonl")
    truth = read_rows(run / "truth.jsonl")
    runtime = json.loads((run / "runtime.json").read_text())
    objects = read_rows(run / "object-truth.jsonl") if (run / "object-truth.jsonl").exists() else []
    geometry = json.loads((run / "object-geometry.json").read_text()) if objects else []
    entities = {
        k: [r for r in objects if r["entity_id"] == k]
        for b in geometry
        for k in (b["model_id"], b["link_id"])
    }
    static = []
    dynamic = []
    dynamic_times = []
    sensors = []
    pairs = []
    point_labels = []
    errors = []
    deltas = []
    changed = []
    changed_boxes = []
    if runtime["scene"] == "large-change":
        world = ET.parse(runtime["world"]).getroot().find("world")
        for m in world.findall("model"):
            if not m.get("name", "").startswith("s3_"):
                continue
            pose = list(map(float, m.findtext("pose").split()))
            size = list(map(float, m.findtext("link/collision/geometry/box/size").split()))
            changed_boxes.append(
                (matrix(pose[:3], Rotation.from_euler("xyz", pose[3:]).as_quat()), np.array(size))
            )
    for f, s in zip(frames, scans):
        assert f["stamp_s"] == s["stamp_s"]
        t = s["stamp_s"]
        tr = nearest(truth, t)
        sensor = matrix(tr["xyz"], tr["xyzw"]) @ matrix(s["laser_tf_xyz"], s["laser_tf_xyzw"])
        ranges = np.array(s["ranges"])
        angles = s["angle_min"] + np.arange(len(ranges)) * s["angle_increment"]
        valid = (ranges > 0.45) & (ranges < 12) & np.isfinite(ranges)
        local = np.column_stack(
            (
                ranges[valid] * np.cos(angles[valid]),
                ranges[valid] * np.sin(angles[valid]),
                np.zeros(valid.sum()),
            )
        )
        p = local @ sensor[:3, :3].T + sensor[:3, 3]
        labels = np.zeros(len(p), np.int8)
        for b in geometry:
            model = nearest(entities[b["model_id"]], t)
            link = nearest(entities[b["link_id"]], t)
            pose = matrix(model["xyz"], model["xyzw"]) @ matrix(link["xyz"], link["xyzw"])
            distance = np.abs((p - pose[:3, 3]) @ pose[:3, :3]) - np.array(b["size_xyz"]) / 2
            positive = (distance.max(axis=1) <= 0.02) & (np.abs(distance).min(axis=1) <= 0.02)
            ambiguous = (distance.max(axis=1) <= 0.05) & ~positive
            labels[positive] = 1
            labels[ambiguous] = -1
        static.append(p[labels == 0, :2])
        dynamic.append(p[labels == 1, :2])
        dynamic_times.extend([t] * int((labels == 1).sum()))
        for pose, size in changed_boxes:
            d = np.abs((p - pose[:3, 3]) @ pose[:3, :3]) - size / 2
            changed.append(p[(d.max(axis=1) <= 0.02) & (np.abs(d).min(axis=1) <= 0.02), :2])
        sensors.append(sensor)
        pairs.append((ranges, angles))
        point_labels.append(labels)
        errors.append(np.linalg.norm(np.array(f["base_pose"][:2]) - np.array(tr["xyz"][:2])))
        deltas.append(abs(tr["stamp_s"] - t))
    static = unique(np.concatenate(static))
    dyn = np.concatenate(dynamic)
    dyn_times = np.array(dynamic_times)
    targets = []
    if len(dyn):
        _, idx = np.unique(np.floor(dyn / 0.1).astype(int), axis=0, return_index=True)
        # Exclude static-support overlap and current returns from the final 1s.
        current = dyn[dyn_times >= scans[-1]["stamp_s"] - 1]
        for i in idx:
            p = dyn[i]
            t = dyn_times[i]
            if cKDTree(static).query(p)[0] <= 0.15:
                continue
            if len(current) and cKDTree(current).query(p)[0] <= 0.15:
                continue
            for s, sensor, (ranges, angles) in zip(scans, sensors, pairs):
                if s["stamp_s"] < t + 1:
                    continue
                delta = p - sensor[:2, 3]
                d = np.linalg.norm(delta)
                local = sensor[:2, :2].T @ delta
                a = np.arctan2(local[1], local[0])
                j = int(np.rint((a - angles[0]) / s["angle_increment"]))
                if 0 <= j < len(ranges) and abs(angles[j] - a) * d <= 0.1 and ranges[j] > d + 0.15:
                    targets.append(p)
                    break
    targets = np.array(targets).reshape(-1, 2)
    maps = {"raw": np.load(run / "srrg-raw.npy"), "srrg": np.load(run / "srrg-final.npy")}
    result = {}
    for method, points in maps.items():
        tree = cKDTree(points)
        result[method] = {
            "static_retention": float((tree.query(static, workers=2)[0] <= 0.15).mean()),
            "dynamic_removal": float((tree.query(targets, workers=2)[0] > 0.15).mean())
            if len(targets)
            else None,
            "points": len(points),
        }
        if changed:
            support = unique(np.concatenate(changed))
            result[method]["new_structure_retention"] = (
                float((tree.query(support, workers=2)[0] <= 0.15).mean()) if len(support) else None
            )
    events = []
    for status, label in [
        (3, "BadCorrespondences: native tracker map reset"),
        (5, "BadBPR: native tracker map reset"),
        (6, "SolverNAN"),
    ]:
        candidates = [f for f in frames if f["status"] == status and f["elapsed_s"] is not None]
        if candidates:
            f = candidates[0]
            events.append(
                {
                    "kind": "native_mapper_reset",
                    "criterion": label,
                    "stamp_s": f["stamp_s"],
                    "recording_sim_elapsed_s": f["elapsed_s"],
                }
            )
    # Independently flag a measured map-geometry problem, not just a pose error.
    # Reference is all measured, confidently static support; GT is scoring only.
    snapshots = np.load(run / "srrg-snapshots.npz")
    static_tree = cKDTree(static)
    history = []
    for i, t in enumerate(snapshots["stamps"]):
        points = snapshots[f"clean_{i:04d}"]
        bad = float((static_tree.query(points, workers=2)[0] > 0.2).mean()) if len(points) else 1.0
        history.append({"stamp_s": float(t), "map_points_over_20cm_from_observed_static_fraction": bad})
    # This warning can also include residual moving objects in a dynamic scene;
    # only the no-moving-target corridor has an unambiguous geometry meaning.
    if runtime["scene"] == "corridor":
        for i in range(len(history) - 2):
            window = history[i : i + 3]
            if all(r["map_points_over_20cm_from_observed_static_fraction"] > 0.2 for r in window):
                t = window[0]["stamp_s"]
                f = min(frames, key=lambda f: abs(f["stamp_s"] - t))
                if f["elapsed_s"] is not None:
                    events.append(
                        {
                            "kind": "map_geometry_warning",
                            "criterion": ">20% map points farther than 0.2m from observed static support in 3 consecutive ~1s snapshots",
                            "stamp_s": t,
                            "recording_sim_elapsed_s": f["elapsed_s"],
                        }
                    )
                    break
    if runtime["scene"] == "corridor":
        for phase in ("limited", "full"):
            f = next((f for f in frames if f["phase"] == phase and f["elapsed_s"] is not None), None)
            if f:
                events.append(
                    {
                        "kind": "observation_change",
                        "criterion": phase,
                        "stamp_s": f["stamp_s"],
                        "recording_sim_elapsed_s": f["elapsed_s"],
                    }
                )
    # A separate trajectory warning, never labelled a map-geometry failure.
    for i, f in enumerate(frames):
        if f["elapsed_s"] is not None and errors[i] > 0.2:
            ids = [j for j in range(i, len(frames)) if frames[j]["stamp_s"] <= f["stamp_s"] + 3]
            if frames[ids[-1]]["stamp_s"] >= f["stamp_s"] + 2.8 and all(errors[j] > 0.2 for j in ids):
                events.append(
                    {
                        "kind": "pose_error_warning",
                        "criterion": "XY error >0.2m sustained >=2.8s, independent truth, not a map-failure label",
                        "stamp_s": f["stamp_s"],
                        "recording_sim_elapsed_s": f["elapsed_s"],
                    }
                )
                break
    report = {
        "kind": "srrg_observed_support_coverage",
        "resolution_m": 0.1,
        "coverage_tolerance_m": 0.15,
        "static_cells": len(static),
        "dynamic_return_points": len(dyn),
        "dynamic_ghost_opportunities": len(targets),
        "new_structure_cells": len(unique(np.concatenate(changed))) if changed else 0,
        "static_label_scope": "Observed scene support excluding self and moving-box boundary shell; unique 10cm cells",
        "dynamic_label_scope": "Historical moving-box support later crossed by a real free ray; current occupancy and static overlap excluded",
        "methods": result,
        "events": events,
        "map_geometry_timeline": history,
        "mapping_pose_xy_rmse_m": float(np.sqrt(np.mean(np.array(errors) ** 2))),
        "truth_sync_max_s": max(deltas),
        "frames": len(frames),
        "scope": "Single session native author map. Coverage after registration and fusion, not exact source-point deletion; cannot numerically rank against 3D subset metrics.",
    }
    for event in events:
        f = min(frames, key=lambda f: abs(f["stamp_s"] - event["stamp_s"]))
        if "recording_wall_elapsed_s" in f:
            event["approx_mp4_s"] = f["recording_wall_elapsed_s"] + 2
    np.savez_compressed(
        run / "srrg-quality-inputs.npz",
        static_support=static,
        dynamic_ghost_support=targets,
        raw=maps["raw"],
        srrg=maps["srrg"],
    )
    (run / "srrg-quality.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("run", type=Path)
    evaluate(p.parse_args().run)
