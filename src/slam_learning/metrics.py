from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

from .pcd import read_pcd


def confusion_metrics(gt: np.ndarray, removed: np.ndarray) -> dict:
    gt, removed = np.asarray(gt), np.asarray(removed)
    if gt.shape != removed.shape or gt.ndim != 1 or not len(gt):
        raise ValueError("Nonempty one-dimensional labels of equal length required")
    if not np.isin(gt, [0, 1]).all() or not np.isin(removed, [0, 1]).all():
        raise ValueError("Labels must be binary (0=static/kept, 1=dynamic/removed)")
    return from_counts(int(np.count_nonzero((gt == 0) & (removed == 0))),
                       int(np.count_nonzero((gt == 0) & (removed == 1))),
                       int(np.count_nonzero((gt == 1) & (removed == 1))),
                       int(np.count_nonzero((gt == 1) & (removed == 0))))


def from_counts(kept_static: int, removed_static: int, removed_dynamic: int, kept_dynamic: int) -> dict:
    s, d = kept_static + removed_static, removed_dynamic + kept_dynamic
    if s <= 0 or d <= 0:
        raise ValueError("SA/DA comparison requires both GT classes")
    sa, da = 100 * kept_static / s, 100 * removed_dynamic / d
    return {"counts": {"kept_static": kept_static, "removed_static": removed_static,
                       "removed_dynamic": removed_dynamic, "kept_dynamic": kept_dynamic},
            "SA": sa, "DA": da, "AA": float(np.sqrt(sa * da)),
            "HA": 2 * sa * da / (sa + da) if sa + da else 0.0}


def score_map(gt_path: Path, map_path: Path, threshold: float = 0.05) -> dict:
    if not np.isfinite(threshold) or threshold <= 0:
        raise ValueError("Threshold must be positive")
    gt, output = read_pcd(gt_path), read_pcd(map_path)
    if "intensity" not in gt.records.dtype.names:
        raise ValueError("GT has no intensity labels")
    xyz = output.xyz()
    if not np.isfinite(xyz).all():
        raise ValueError("Map has nonfinite coordinates")
    tree = cKDTree(xyz) if len(xyz) else None
    counts = np.zeros(4, dtype=np.int64)
    for start in range(0, len(gt.records), 250_000):
        selection = slice(start, start + 250_000)
        points = gt.xyz(selection)
        labels = gt.records["intensity"][selection]
        if not np.isfinite(points).all() or not np.isin(labels, [0, 1]).all():
            raise ValueError("GT has nonfinite coordinates or nonbinary labels")
        distances = tree.query(points, workers=2)[0] if tree is not None else np.full(len(points), np.inf)
        removed = distances > threshold
        counts += [np.count_nonzero((labels == 0) & ~removed), np.count_nonzero((labels == 0) & removed),
                   np.count_nonzero((labels == 1) & removed), np.count_nonzero((labels == 1) & ~removed)]
    return {**from_counts(*map(int, counts)), "gt_points": len(gt.records), "map_points": len(xyz),
            "threshold_m": threshold,
            "evaluator": "independent scipy nearest-neighbor implementation of benchmark rule; no PCL cross-check claimed"}


def compare_paper(metrics: dict, target: dict) -> dict:
    tolerance = target["absolute_tolerance_pp"]
    rows = {k: {"measured": metrics[k], "reported": value, "difference_pp": metrics[k] - value,
                "within_tolerance": abs(metrics[k] - value) <= tolerance}
            for k, value in target["values"].items()}
    return {"source": target["source"], "table": target["table"], "absolute_tolerance_pp": tolerance,
            "matched": all(r["within_tolerance"] for r in rows.values()), "metrics": rows}
