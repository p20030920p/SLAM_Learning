"""Recompute geometric moving-box labels and point retention scores."""
import json

import numpy as np


def geometric_labels(data):
    points, ids = data["points"], data["scan_ids"]
    result = np.zeros(len(points), dtype=np.int8)
    for index, poses in enumerate(data["box_poses"]):
        chosen = ids == index
        frame = points[chosen]
        dynamic, ambiguous = np.zeros(len(frame), bool), np.zeros(len(frame), bool)
        for pose, size in zip(poses, data["box_sizes"]):
            local = (frame-pose[:3, 3]) @ pose[:3, :3]
            distances = np.abs(local)-size/2
            positive = (distances.max(axis=1) <= .02) & (np.abs(distances).min(axis=1) <= .02)
            dynamic |= positive
            ambiguous |= (distances.max(axis=1) <= .05) & ~positive
        ambiguous |= np.linalg.norm(frame-data["sensor_origins"][index], axis=1) < .45
        labels = np.zeros(len(frame), dtype=np.int8)
        labels[dynamic] = 1
        labels[ambiguous] = -1
        result[chosen] = labels
    return result


def retention_score(labels, retained):
    if retained.dtype != bool or retained.shape != labels.shape:
        raise ValueError("Point decisions do not index the exact scored input")
    static, dynamic = labels == 0, labels == 1
    if not static.any() or not dynamic.any():
        raise ValueError("Both confident static and moving-object returns are required")
    return {"static_retention": float(retained[static].mean()),
            "dynamic_removal": float((~retained[dynamic]).mean()),
            "removed_static_points": int((~retained & static).sum()),
            "retained_dynamic_points": int((retained & dynamic).sum())}


def verify_map_point_audit(path, record):
    try:
        with np.load(path.parent / "point-label-inputs.npz", allow_pickle=False) as data:
            labels = geometric_labels(data)
            if not np.array_equal(labels, data["labels"]):
                raise ValueError("Saved moving-box labels differ from synchronized geometry")
        for name, expected in record["configurations"].items():
            with np.load(path.parent / name / "retention-masks.npz", allow_pickle=False) as masks:
                actual = {method: retention_score(labels, masks[method]) for method in ("raw", "dufomap", "beautymap")}
            if actual != expected["metrics"]:
                raise ValueError("Map-cleaning scores differ from retained point decisions")
            processing = json.loads((path.parent / name / "processing.json").read_text(encoding="utf-8"))
            if processing["parameters"] != expected["parameters"]:
                raise ValueError("Map-cleaning configuration changed")
    except (OSError, ValueError, KeyError, TypeError) as error:
        return [str(error)]
    return []
