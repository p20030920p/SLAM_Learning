"""Validate native SE(3) poses against independent timestamped simulator truth."""
import csv
import math
from pathlib import Path

import numpy as np


def score_poses3d(path: Path, truth: list[dict]) -> dict:
    keys = ("x", "y", "z", "qx", "qy", "qz", "qw")
    names = ["stamp_s", *["truth_"+key for key in keys], *["estimate_"+key for key in keys], "nearest_truth_delta_s"]
    with path.open(newline="", encoding="utf-8") as stream:
        values = np.asarray([[float(row[name]) for name in names] for row in csv.DictReader(stream)])
    if values.ndim != 2 or len(values) < 2 or not np.isfinite(values).all() or np.any(np.diff(values[:, 0]) < 0):
        raise ValueError("3D poses must contain finite ordered native updates")
    stamps = np.asarray([row["stamp_s"] for row in truth])
    if len(stamps) < 2 or not np.isfinite(stamps).all() or np.any(np.diff(stamps) < 0):
        raise ValueError("3D simulator truth timestamps are invalid")
    for row in values:
        index = int(np.argmin(abs(stamps-row[0])))
        measured = truth[index]
        delta = abs(stamps[index]-row[0])
        if (measured.get("model") != "omni_car" or delta > .05 or abs(delta-row[-1]) > 1e-10
                or not np.allclose(row[1:8], [*measured["xyz"], *measured["xyzw"]], atol=1e-10, rtol=0)):
            raise ValueError("3D poses do not match independent synchronized robot truth")
    expected, estimated = values[:, 4:8], values[:, 11:15]
    if np.any(np.linalg.norm(expected, axis=1) < .99) or np.any(np.linalg.norm(estimated, axis=1) < .99):
        raise ValueError("3D quaternion is invalid")
    expected = expected / np.linalg.norm(expected, axis=1)[:, None]
    estimated = estimated / np.linalg.norm(estimated, axis=1)[:, None]
    angles = 2*np.arccos(np.clip(np.abs(np.sum(expected*estimated, axis=1)), 0, 1))
    error = values[:, 8:11]-values[:, 1:4]
    distance = np.linalg.norm(error, axis=1)
    warm = values[:, 0] >= values[0, 0]+5
    return {"samples": len(values), "xyz_rmse_m": float(np.sqrt(np.mean(distance**2))),
            "z_rmse_m": float(np.sqrt(np.mean(error[:, 2]**2))),
            "rotation_rmse_deg": float(np.sqrt(np.mean(angles**2))*180/math.pi),
            "xyz_p95_m": float(np.percentile(distance, 95)),
            "post_warmup_5s_xyz_rmse_m": float(np.sqrt(np.mean(distance[warm]**2))) if warm.any() else None}
