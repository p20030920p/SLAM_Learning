"""Predeclared late-correction interventions and held-out partial-surface references."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from matplotlib.path import Path as PolygonPath
from scipy.ndimage import binary_erosion
from scipy.spatial import cKDTree


def prefix_errors(count: int, rms: float, seed: int) -> np.ndarray:
    if count < 2 or rms < 0:
        raise ValueError("At least two poses and a nonnegative RMS are required")
    values = np.r_[0.0, np.cumsum(np.random.default_rng(seed).normal(size=count - 1))]
    if rms:
        values *= rms / np.sqrt(np.mean(values**2))
    else:
        values[:] = 0
    result = np.zeros((count, 3))
    result[:, 0] = values
    return result


def reference_instances(annotation_path: Path, data: Path):
    from PIL import Image

    annotation = json.loads(annotation_path.read_text())
    scene = data / annotation["scene"]
    poses = np.loadtxt(scene / "traj.full.txt").reshape(-1, 4, 4)
    k = np.array([[600., 0., 599.5], [0., 600., 339.5], [0., 0., 1.]])
    canvas = annotation["coordinate_canvas"]
    output = []
    for instance in annotation["instances"]:
        views, surfaces = [], []
        for view in instance["views"]:
            frame = view["frame"]
            depth = np.asarray(Image.open(scene / "results" / f"depth{frame:06d}.png"), float) / 6553.5
            h, w = depth.shape
            u, v = np.meshgrid(np.arange(w), np.arange(h))
            polygon = np.asarray(view["polygon"]) * [w / canvas[0], h / canvas[1]]
            mask = PolygonPath(polygon).contains_points(np.c_[u.ravel(), v.ravel()]).reshape(h, w)
            mask = binary_erosion(mask, iterations=max(1, round(2 * w / canvas[0])))
            mask &= (depth > 0) & np.isfinite(depth) & (u % 3 == 0) & (v % 3 == 0)
            xyz = np.c_[(u[mask] - k[0, 2]) * depth[mask] / k[0, 0],
                        (v[mask] - k[1, 2]) * depth[mask] / k[1, 1], depth[mask]]
            xyz = xyz @ poses[frame, :3, :3].T + poses[frame, :3, 3]
            if not len(xyz):
                raise ValueError(f"Empty eroded reference: {instance['id']} frame {frame}")
            surfaces.append(xyz)
            views.append({"frame": frame, "pose": poses[frame], "polygon": polygon, "depth": depth, "k": k})
        output.append({**instance, "points": np.concatenate(surfaces), "reference_views": views})
    return output


def visible_precision(points, instance, tolerance):
    hits, total = 0, 0
    for view in instance["reference_views"]:
        pose, k, depth = view["pose"], view["k"], view["depth"]
        camera = (points - pose[:3, 3]) @ pose[:3, :3]
        camera = camera[camera[:, 2] > .01]
        uv = np.rint(camera[:, :2] / camera[:, 2, None] * [k[0, 0], k[1, 1]] +
                     [k[0, 2], k[1, 2]]).astype(int)
        valid = (uv[:, 0] >= 0) & (uv[:, 0] < depth.shape[1]) & (uv[:, 1] >= 0) & (uv[:, 1] < depth.shape[0])
        uv, camera = uv[valid], camera[valid]
        uv = np.unique(uv[np.abs(camera[:, 2] - depth[uv[:, 1], uv[:, 0]]) <= tolerance], axis=0)
        hits += int(PolygonPath(view["polygon"]).contains_points(uv).sum())
        total += len(uv)
    return hits / total if total else 0.


def measure_map(clouds, features, text_features, instances, config, latest_source_frame):
    eligible = [i for i in instances if i["first_reference_frame"] <= latest_source_frame]
    d = config["reference_distance_m"]
    cover = np.zeros((len(clouds), len(eligible)))
    precision = np.zeros_like(cover)
    for j, points in enumerate(clouds):
        tree = cKDTree(points)
        for k, instance in enumerate(eligible):
            cover[j, k] = np.mean(tree.query(instance["points"], workers=2)[0] <= d)
            precision[j, k] = visible_precision(points, instance, d)
    qualifying = (cover >= config["reference_coverage_min"]) & (precision >= config["reference_precision_min"])
    rows = []
    normalized = features / np.maximum(np.linalg.norm(features, axis=1, keepdims=True), 1e-12)
    queries = [i["query"] for i in instances]
    scores = text_features @ normalized.T
    for k, instance in enumerate(eligible):
        selected = int(np.argmax(scores[queries.index(instance["query"])])) if clouds else None
        rows.append({"target": instance["id"], "query": instance["query"],
                     "reference_points": len(instance["points"]),
                     "best_coverage": float(cover[:, k].max()) if clouds else 0.,
                     "recovered": bool(qualifying[:, k].any()),
                     "qualifying_fragments": int(qualifying[:, k].sum()),
                     "top1_object": selected,
                     "restricted_top1_hit": bool(qualifying[selected, k]) if clouds else False,
                     "top1_coverage": float(cover[selected, k]) if clouds else 0.,
                     "top1_visible_precision": float(precision[selected, k]) if clouds else 0.,
                     "top1_surface_distance_m": float(np.median(cKDTree(clouds[selected]).query(
                         instance["points"], workers=2)[0])) if clouds else None})
    # Multiple independently labelled instances substantially supported by one map object.
    mixing = int(np.sum(((cover >= config["reference_coverage_min"]) & (precision >= .20)).sum(axis=1) > 1))
    return {"eligible_targets": len(eligible), "map_objects": len(clouds), "targets": rows,
            "mean_coverage": float(np.mean([r["best_coverage"] for r in rows])),
            "recovery": float(np.mean([r["recovered"] for r in rows])),
            "restricted_query_hit": float(np.mean([r["restricted_top1_hit"] for r in rows])),
            "annotated_mixed_objects": mixing,
            "fragment_count": sum(r["qualifying_fragments"] for r in rows)}
