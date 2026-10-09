"""Paired errors with identical marginal samples, and evaluation-only targets."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from matplotlib.path import Path as PolygonPath
from scipy.ndimage import binary_erosion
from scipy.spatial import cKDTree


def paired_translations(count: int, rms: float, seed: int):
    if count < 4 or rms < 0:
        raise ValueError("At least four poses and nonnegative RMS required")
    iid = np.random.default_rng(seed).normal(size=count - 1)
    iid -= iid.mean()
    iid *= rms / np.sqrt(np.sum(iid * iid) / count)
    result = {}
    for name, values in (("independent", iid), ("correlated", np.sort(iid))):
        translation = np.zeros((count, 3))
        translation[1:, 0] = values
        result[name] = translation
    if not np.array_equal(np.sort(result["independent"][:, 0]), np.sort(result["correlated"][:, 0])):
        raise AssertionError("Paired marginal distributions differ")
    return result


def error_description(values):
    x = np.asarray(values)[:, 0]
    return {
        "rms_m": float(np.sqrt(np.mean(x * x))),
        "mean_m": float(x.mean()),
        "lag1_correlation": float(np.corrcoef(x[:-1], x[1:])[0, 1]) if np.any(x) else None,
        "first_pose_fixed": bool(np.all(values[0] == 0)),
    }


def reference_targets(root: Path):
    """Reference is visible RGB-D geometry, never predicted SAM masks."""
    from PIL import Image

    annotation = json.loads((root / "configs/annotations/room0/targets.json").read_text())
    data = root / ".cache/semantic-data/Replica/room0"
    poses = np.loadtxt(data / "traj.full.txt").reshape(-1, 4, 4)
    # Pinned rendered Replica calibration, matching the existing two adapters.
    original_k = np.array([[600.0, 0, 599.5], [0, 600.0, 339.5], [0, 0, 1.0]])
    width, height = annotation["coordinate_canvas"]
    targets = []
    for target in annotation["targets"]:
        frame = target["source_frame"]
        depth = np.asarray(Image.open(data / "results" / f"depth{frame:06d}.png"), dtype=float) / 6553.5
        h, w = depth.shape
        u, v = np.meshgrid(np.arange(w), np.arange(h))
        polygon = np.asarray(target["polygon"], dtype=float) * [w / width, h / height]
        mask = PolygonPath(polygon).contains_points(np.c_[u.ravel(), v.ravel()]).reshape(h, w)
        # Remove a two-canvas-pixel boundary band to reduce mixed-depth edge samples.
        mask = binary_erosion(mask, iterations=max(1, int(round(2 * w / width))))
        mask &= (depth > 0) & np.isfinite(depth)
        # Every third pixel bounds runtime; no frontend predictions select reference points.
        mask &= (u % 3 == 0) & (v % 3 == 0)
        xyz = np.c_[
            (u[mask] - original_k[0, 2]) * depth[mask] / original_k[0, 0],
            (v[mask] - original_k[1, 2]) * depth[mask] / original_k[1, 1],
            depth[mask],
        ]
        pose = poses[frame]
        xyz = xyz @ pose[:3, :3].T + pose[:3, 3]
        ax, ay = np.asarray(target["anchor_pixel"]) * [w / width, h / height]
        ax, ay = int(round(ax)), int(round(ay))
        z = float(np.median(depth[max(0, ay - 2) : ay + 3, max(0, ax - 2) : ax + 3]))
        anchor = (
            np.array(
                [
                    (ax - original_k[0, 2]) * z / original_k[0, 0],
                    (ay - original_k[1, 2]) * z / original_k[1, 1],
                    z,
                ]
            )
            @ pose[:3, :3].T
            + pose[:3, 3]
        )
        targets.append(
            {
                **target,
                "points": xyz,
                "anchor_world_m": anchor,
                "pose": pose,
                "depth": depth,
                "polygon_original": polygon,
                "camera_k": original_k,
                "points_count": len(xyz),
            }
        )
    return targets


def target_metrics(
    clouds, features, text_features, queries, targets, distance=0.1, coverage_min=0.20, precision_min=0.50
):
    """Partial-surface recovery and query hit; not full-object 3D segmentation IoU."""
    rows = []
    normalized = features / np.maximum(np.linalg.norm(features, axis=1, keepdims=True), 1e-12)
    scores = text_features @ normalized.T
    all_distances = []
    for points in clouds:
        tree = cKDTree(points)
        all_distances.append([tree.query(t["points"], workers=2)[0] for t in targets])
    for t_index, target in enumerate(targets):
        coverage = np.array([np.mean(d[t_index] <= distance) for d in all_distances])
        # Visible projected support in the independently annotated source image.
        precisions = []
        k, pose, depth = target["camera_k"], target["pose"], target["depth"]
        for points in clouds:
            camera = (points - pose[:3, 3]) @ pose[:3, :3]
            valid = camera[:, 2] > 0.01
            camera = camera[valid]
            uv = np.rint(camera[:, :2] / camera[:, 2, None] * [k[0, 0], k[1, 1]] + [k[0, 2], k[1, 2]]).astype(
                int
            )
            valid = (
                (uv[:, 0] >= 0) & (uv[:, 0] < depth.shape[1]) & (uv[:, 1] >= 0) & (uv[:, 1] < depth.shape[0])
            )
            uv, camera = uv[valid], camera[valid]
            visible = np.abs(camera[:, 2] - depth[uv[:, 1], uv[:, 0]]) <= distance
            uv = np.unique(uv[visible], axis=0)
            precision = (
                np.mean(PolygonPath(target["polygon_original"]).contains_points(uv)) if len(uv) else 0.0
            )
            precisions.append(float(precision))
        qualifying = (coverage >= coverage_min) & (np.asarray(precisions) >= precision_min)
        query_index = queries.index(target["query"])
        selected = int(np.argmax(scores[query_index]))
        closest = int(np.argmax(coverage))
        rows.append(
            {
                "target": target["id"],
                "query": target["query"],
                "reference_surface_points": len(target["points"]),
                "best_surface_coverage": float(coverage[closest]),
                "recoverable": bool(qualifying.any()),
                "qualifying_segments": int(qualifying.sum()),
                "top1_segment": selected,
                "top1_surface_coverage": float(coverage[selected]),
                "top1_visible_precision": precisions[selected],
                "top1_target_hit": bool(qualifying[selected]),
                "top1_anchor_distance_m": float(cKDTree(clouds[selected]).query(target["anchor_world_m"])[0]),
                "reference_anchor_world_m": target["anchor_world_m"].tolist(),
                "cosine_similarity": float(scores[query_index, selected]),
            }
        )
    # A category query can legitimately retrieve either of the two ottomans.
    category_hits = {
        query: any(r["top1_target_hit"] for r in rows if r["query"] == query) for query in queries
    }
    return {
        "targets": rows,
        "category_hits": category_hits,
        "query_hit_fraction": float(np.mean(list(category_hits.values()))),
        "target_recovery_fraction": float(np.mean([r["recoverable"] for r in rows])),
        "mean_best_surface_coverage": float(np.mean([r["best_surface_coverage"] for r in rows])),
    }
