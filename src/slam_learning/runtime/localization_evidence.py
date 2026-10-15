"""Check localization evidence against retained, unaligned TUM trajectories."""
from __future__ import annotations

import json
import math
import re
from pathlib import Path

import numpy as np
from scipy.spatial.transform import Rotation


def trajectory_metrics(estimate: Path, truth: Path, start_time: float, max_difference: float) -> tuple[dict, int]:
    est, gt = np.loadtxt(estimate, ndmin=2), np.loadtxt(truth, ndmin=2)
    for values in (est, gt):
        if values.shape[1] != 8 or not np.isfinite(values).all() or not (np.diff(values[:, 0]) > 0).all():
            raise ValueError("Invalid TUM trajectory")
    est, gt = est[est[:, 0] >= start_time], gt[gt[:, 0] >= start_time]
    if not len(est) or not len(gt):
        raise ValueError("Empty scoring window")
    index = np.searchsorted(est[:, 0], gt[:, 0])
    before, after = np.clip(index - 1, 0, len(est) - 1), np.clip(index, 0, len(est) - 1)
    index = np.where(abs(est[before, 0] - gt[:, 0]) < abs(est[after, 0] - gt[:, 0]), before, after)
    valid = abs(est[index, 0] - gt[:, 0]) <= max_difference
    gt, index = gt[valid], index[valid]
    if not len(gt) or len(np.unique(index)) != len(index):
        raise ValueError("Empty or ambiguous timestamp association")
    est = est[index]
    position = np.linalg.norm(est[:, 1:4] - gt[:, 1:4], axis=1)
    angle = np.degrees((Rotation.from_quat(gt[:, 4:8]).inv() * Rotation.from_quat(est[:, 4:8])).magnitude())
    values = {
        "location_rmse_cm": np.sqrt(np.mean(position ** 2)) * 100,
        "yaw_rmse_deg": np.sqrt(np.mean(angle ** 2)),
    }
    for threshold in (5, 10, 20):
        values[f"location_lt{threshold}_pct"] = np.mean(position < threshold / 100) * 100
    for label, threshold in (("0_5", 0.5), ("1", 1.0), ("2", 2.0)):
        values[f"yaw_lt{label}_pct"] = np.mean(angle < threshold) * 100
    return {key: round(float(value), 2) for key, value in values.items()}, len(gt)


def verify_localization(path: Path, record: dict) -> list[str]:
    errors = []
    try:
        required = {"run.log", "metrics.json", "IRMCL.txt", "seq_1_gt_pose.txt", "loc_config.yml"}
        if record.get("exit_code") != 0 or not record.get("command") or not required.issubset(record["artifacts"]):
            errors.append("Localization run lacks command, successful exit or trajectory evidence")
        inputs = record["dataset"]["inputs_sha256"]
        if not inputs or not all(re.fullmatch(r"[0-9a-f]{64}", value) for value in inputs.values()):
            errors.append("Localization dataset hashes missing or invalid")
        scoring = record["scoring"]
        if scoring["alignment"] != "none" or scoring["rotation_metric"] != "rotation_angle_deg":
            errors.append("Unsupported localization scoring protocol")
        measured, count = trajectory_metrics(path.parent / "IRMCL.txt", path.parent / "seq_1_gt_pose.txt",
                                             scoring["start_time_s"], scoring["max_timestamp_difference_s"])
        saved = json.loads((path.parent / "metrics.json").read_text(encoding="utf-8"))
        if measured != record["metrics"] or saved["measured"] != measured or count != scoring["scored_samples"]:
            errors.append("Localization metrics or sample count differ from retained trajectories")
        for key, value in measured.items():
            pair = record["paper_comparison"][key]
            if pair["reproduced"] != value or not math.isfinite(pair["paper"]):
                errors.append("Localization paper comparison is inconsistent")
    except (KeyError, TypeError, ValueError, OSError) as exc:
        errors.append(f"Invalid localization evidence: {exc}")
    return errors
