"""Post-run evaluation only: did depth add observable geometry at the true pose?"""
import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
from scipy.spatial.transform import Rotation

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from slam_learning.core.provenance import digest
from slam_learning.runtime.recovery_probe import SurfaceMap


def information(surface, scan, pose):
    if len(scan) < 12:
        return np.zeros((3, 3)), None
    jacobian, residual, _ = surface.correspondences(scan, pose, .5)
    if len(residual) < 12:
        return np.zeros((3, 3)), None
    weights = np.minimum(1., .08 / np.maximum(np.abs(residual), 1e-9))
    return (jacobian.T * weights) @ jacobian / len(residual), float(np.median(np.abs(residual)))


def rank(matrix):
    values = np.linalg.eigvalsh(matrix)
    return int((values > max(values[-1] * .02, 1e-8)).sum())


def diagnose(path):
    folder = path.parent
    record = json.loads(path.read_text())
    config = record["hypothesis_probes"]
    frames = json.loads((folder / "probe-B-inputs.json").read_text())["frames"]
    points = np.load(folder / "probe-B-inputs.npz", allow_pickle=False)
    lidar = np.load(folder / "probe-maps/lidar.npy", allow_pickle=False).astype(float, copy=True)
    depth = np.load(folder / "probe-maps/depth.npy", allow_pickle=False).astype(float, copy=True)
    lidar[:, 2] -= config.get("ground_z_m", 0.)
    depth[:, 2] -= config.get("ground_z_m", 0.)
    lidar_map = SurfaceMap(lidar, 2 if config["dimension"] == "2d" else 3)
    depth_map = SurfaceMap(depth, 3)
    truth = [json.loads(line) for line in (folder / "truth.jsonl").read_text().splitlines()]
    stamps = np.asarray([row["stamp_s"] for row in truth])
    runtime = json.loads((folder / "runtime.json").read_text())
    restore = record["restoration"]["plain"]["restore_stamp_s"]
    boxes = []
    if (folder / "height-control.world").exists():
        for model in ET.parse(folder / "height-control.world").findall(".//model"):
            if model.get("name", "").startswith("probe_high_block_"):
                centre = np.fromstring(model.findtext("pose"), sep=" ")[:3]
                size = np.fromstring(model.findtext("link/collision/geometry/box/size"), sep=" ")
                boxes.append((centre, size))
    rows = []
    for frame in frames:
        stamp, index = frame["stamp_s"], frame["frame"]
        nearest = int(np.argmin(abs(stamps - stamp)))
        measured = truth[nearest]
        if abs(stamps[nearest] - stamp) > .05:
            continue
        rotation = Rotation.from_quat(measured["xyzw"])
        yaw = rotation.as_euler("xyz")[2]
        pose = np.array([*measured["xyz"][:2], yaw])
        lidar, depth = (points[f"frame_{index:05d}_{kind}"] for kind in ("lidar", "depth"))
        first, lidar_residual = information(lidar_map, lidar, pose)
        extra, depth_residual = information(depth_map, depth, pose)
        row = {"frame": index, "stamp_s": stamp, "phase": "limited" if stamp < restore else "restored",
               "lidar_rank": rank(first), "with_depth_rank": rank(first + extra),
               "lidar_plane_median_residual_at_truth_m": lidar_residual,
               "depth_plane_median_residual_at_truth_m": depth_residual,
               "depth_points": len(depth), "high_fixture_points": {}}
        for kind, cloud in (("lidar", lidar), ("depth", depth)):
            world = rotation.apply(cloud) + np.asarray(measured["xyz"])
            hit = np.zeros(len(world), dtype=bool)
            for centre, size in boxes:
                hit |= np.all(np.abs(world - centre) <= size / 2 + .05, axis=1)
            row["high_fixture_points"][kind] = int(hit.sum())
        rows.append(row)
    stages = {}
    for phase in ("limited", "restored"):
        stage = [row for row in rows if row["phase"] == phase]
        if stage:
            stages[phase] = {"frames": len(stage), "frames_with_depth": sum(row["depth_points"] >= 12 for row in stage),
                             "lidar_full_rank_frames": sum(row["lidar_rank"] == 3 for row in stage),
                             "with_depth_full_rank_frames": sum(row["with_depth_rank"] == 3 for row in stage),
                             "high_fixture_lidar_points": sum(row["high_fixture_points"]["lidar"] for row in stage),
                             "high_fixture_depth_points": sum(row["high_fixture_points"]["depth"] for row in stage)}
    return {"scope": "post-run evaluation at independent truth, never input to B estimators; local rank is not proof of unique global position",
            "record_sha256": digest(path), "scene": runtime["scene"], "dimension": config["dimension"],
            "stages": stages, "frames": rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = diagnose(args.record)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result["stages"], indent=2))


if __name__ == "__main__":
    main()
