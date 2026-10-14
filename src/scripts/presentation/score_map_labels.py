"""Score measured map points using synchronized Gazebo moving-box geometry."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation


def matrix(row):
    result = np.eye(4)
    result[:3, :3] = Rotation.from_quat(row["xyzw"]).as_matrix()
    result[:3, 3] = row["xyz"]
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("maps", type=Path)
    args = parser.parse_args()
    archive = np.load(args.run / "mapping-clouds.npz", allow_pickle=False)
    processing = json.loads((args.maps / "record.json").read_text())
    geometry = json.loads((args.run / "object-geometry.json").read_text())
    needed = {item[key] for item in geometry for key in ("model_id", "link_id")}
    entities = {key: [] for key in needed}
    lines = (args.run / "object-truth.jsonl").read_bytes().split(b"\n")
    discarded_tail_bytes = 0
    for number, line in enumerate(lines):
        if not line:
            continue
        try:
            row = json.loads(line)
        except (UnicodeDecodeError, json.JSONDecodeError):
            if any(part for part in lines[number+1:]):
                raise ValueError("Corrupt object truth inside the scoring interval") from None
            discarded_tail_bytes = len(line)
            continue
        if row["entity_id"] in entities:
            entities[row["entity_id"]].append(row)
    times = {key: np.asarray([row["stamp_s"] for row in rows]) for key, rows in entities.items()}
    labels, surface_distances, box_poses, scan_ids, sensor_origins = [], [], [], [], []
    for index in processing["selected_scan_ids"]:
        stamp = archive["stamps"][index]
        sensor = archive["poses"][index]
        scan = archive[f"scan_{index:04d}"]
        points = (scan @ sensor[:3, :3].T + sensor[:3, 3]).astype(np.float32)
        frame_boxes = []
        dynamic, ambiguous = np.zeros(len(points), bool), np.zeros(len(points), bool)
        for box in geometry:
            parts = []
            for key in ("model_id", "link_id"):
                entity = box[key]
                near = int(np.argmin(abs(times[entity]-stamp)))
                if abs(times[entity][near]-stamp) > .05:
                    raise ValueError("Moving object truth is not synchronized with the measured scan")
                parts.append(matrix(entities[entity][near]))
            pose = parts[0] @ parts[1]
            frame_boxes.append(pose)
            local = (points-pose[:3, 3]) @ pose[:3, :3]
            distance = np.abs(local)-np.asarray(box["size_xyz"])/2
            surface = np.abs(distance).min(axis=1)
            positive = (distance.max(axis=1) <= .02) & (surface <= .02)
            dynamic |= positive
            ambiguous |= (distance.max(axis=1) <= .05) & ~positive
            surface_distances.extend(surface[positive].tolist())
        # Self returns and the 2–5 cm box boundary shell have no confident label.
        ambiguous |= np.linalg.norm(points-sensor[:3, 3], axis=1) < .45
        own = np.zeros(len(points), dtype=np.int8)
        own[dynamic] = 1
        own[ambiguous] = -1
        labels.append(own)
        scan_ids.append(np.full(len(points), len(box_poses), dtype=np.int16))
        box_poses.append(frame_boxes)
        sensor_origins.append(sensor[:3, 3])
    labels = np.concatenate(labels)
    raw = np.load(args.maps / "raw/points.npy", allow_pickle=False)
    if len(raw) != len(labels):
        raise ValueError("Labels do not index the exact Raw input points")
    np.save(args.maps / "point-labels.npy", labels)
    np.savez_compressed(args.maps / "point-label-inputs.npz", points=raw, labels=labels,
                        scan_ids=np.concatenate(scan_ids), box_poses=np.asarray(box_poses),
                        sensor_origins=np.asarray(sensor_origins),
                        box_sizes=np.asarray([box["size_xyz"] for box in geometry]))
    static, dynamic = labels == 0, labels == 1
    if not dynamic.any():
        raise ValueError("No validated moving-box returns in these measured scans")
    result = {}
    for method in ("raw", "dufomap", "beautymap"):
        points = np.load(args.maps / method / "points.npy", allow_pickle=False)
        retained = cKDTree(points).query(raw, workers=2)[0] < 2e-5
        if retained.sum() != len(points):
            raise ValueError("Coordinate retention does not preserve exact point multiplicity")
        sa = float(retained[static].mean())
        da = float((~retained[dynamic]).mean())
        result[method] = {"static_retention": sa, "dynamic_removal": da,
                          "static_false_removal": 1-sa, "dynamic_residual": 1-da,
                          "retained_dynamic_points": int((retained & dynamic).sum()),
                          "removed_static_points": int((~retained & static).sum())}
    paths = [args.run / name for name in ("mapping-clouds.npz", "object-truth.jsonl", "object-geometry.json", "object-scene.pbtxt")]
    report = {"kind": "gazebo_geometry_point_classification", "methods": result,
              "static_points": int(static.sum()), "dynamic_points": int(dynamic.sum()),
              "unscored_ambiguous_points": int((labels < 0).sum()),
              "discarded_incomplete_shutdown_tail_bytes": discarded_tail_bytes,
              "positive_surface_distance_p95_m": float(np.percentile(surface_distances, 95)),
              "label_tolerance_m": .02, "ambiguous_shell_m": .05,
              "inputs": {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths},
              "scope": "three actual moving-box surface labels on selected mapping-A points; not hand-labelled paper data; truth never enters held-out localization"}
    (args.maps / "point-label-scores.json").write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
