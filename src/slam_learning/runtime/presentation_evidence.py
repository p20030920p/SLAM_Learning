"""Recompute native desktop localization scores from retained poses and simulator truth."""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import numpy as np


def read_samples(path: Path) -> np.ndarray:
    with path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    names = ["stamp_s", "truth_x", "truth_y", "truth_yaw", "estimate_x", "estimate_y",
             "estimate_yaw", "position_error_m", "yaw_error_rad", "nearest_truth_delta_s"]
    values = np.asarray([[float(row[name]) for name in names] for row in rows])
    if values.ndim != 2 or len(values) < 2 or not np.isfinite(values).all():
        raise ValueError("Scored poses must contain at least two finite samples")
    if np.any(np.diff(values[:, 0]) < 0):
        raise ValueError("Scored pose timestamps moved backwards")
    position = np.linalg.norm(values[:, 4:6]-values[:, 1:3], axis=1)
    delta = values[:, 6]-values[:, 3]
    angle = np.arctan2(np.sin(delta), np.cos(delta))
    if not np.allclose(position, values[:, 7], atol=1e-10, rtol=0):
        raise ValueError("Saved position errors differ from retained poses")
    if not np.allclose(angle, values[:, 8], atol=1e-10, rtol=0):
        raise ValueError("Saved yaw errors differ from retained poses")
    if np.any((values[:, 9] < 0) | (values[:, 9] > .05)):
        raise ValueError("Unsynchronized truth was scored")
    return values


def score(values: np.ndarray) -> dict:
    after = values[values[:, 0] >= values[0, 0]+5]
    return {"samples": len(values), "position_rmse_m": float(np.sqrt(np.mean(values[:, 7]**2))),
            "yaw_rmse_deg": float(np.sqrt(np.mean(values[:, 8]**2))*180/math.pi),
            "post_warmup_5s_samples": len(after),
            "post_warmup_5s_position_rmse_m": float(np.sqrt(np.mean(after[:, 7]**2))) if len(after) else None,
            "position_p95_m": float(np.percentile(values[:, 7], 95))}


def validate_truth(values: np.ndarray, truth: list[dict]) -> None:
    stamps = np.asarray([row["stamp_s"] for row in truth])
    if len(stamps) < 2 or np.any(np.diff(stamps) < 0) or not np.isfinite(stamps).all():
        raise ValueError("Simulator truth timestamps are invalid")
    for row in values:
        near = int(np.argmin(np.abs(stamps-row[0])))
        measured = truth[near]
        qx, qy, qz, qw = measured["xyzw"]
        heading = math.atan2(2*(qw*qz+qx*qy), 1-2*(qy*qy+qz*qz))
        if measured.get("model") != "omni_car":
            raise ValueError("Wrong simulator model was used as truth")
        if not np.allclose(row[1:4], [*measured["xyz"][:2], heading], atol=1e-10, rtol=0):
            raise ValueError("CSV truth does not match the independent simulator stream")
        if abs(abs(stamps[near]-row[0])-row[9]) > 1e-10:
            raise ValueError("Truth synchronization deltas were changed")


def restoration(values: np.ndarray, stamp: float) -> dict:
    after = values[values[:, 0] >= stamp]
    if len(after) < 8 or after[-1, 0]-after[0, 0] < 5:
        return {"restore_stamp_s": stamp, "converged": None, "status": "insufficient_post_restore_pose_updates",
                "sustained_convergence_delay_s": None}
    first = None
    for idx, row in enumerate(after):
        end = int(np.searchsorted(after[:, 0], row[0]+5, side="left"))
        if end >= len(after):
            continue
        window = after[idx:end+1]
        if len(window) >= 8 and window[-1, 0]-row[0] >= 5-1e-9:
            if np.all((window[:, 7] < .1) & (np.abs(window[:, 8]) < math.radians(5))):
                first = float(after[idx, 0]-stamp)
                break
    return {"restore_stamp_s": stamp, "criterion": "position <0.1m and absolute yaw <5deg for 5 simulation seconds, >=8 native updates",
            "sustained_convergence_delay_s": first, "converged": first is not None,
            "scope": "recovery of an offset initial belief when full observations return; no physical kidnapping"}


def verify_presentation(path: Path, record: dict) -> list[str]:
    errors = []
    try:
        truth = [json.loads(line) for line in (path.parent / "truth.jsonl").read_text().splitlines()]
        for name, expected in record["metrics"]["cases"].items():
            values = read_samples(path.parent / f"{name}-samples.csv")
            validate_truth(values, truth)
            actual = score(values)
            for key, value in actual.items():
                if value is None:
                    if expected.get(key) is not None:
                        raise ValueError(f"{name}: {key} differs")
                elif not math.isclose(value, expected[key], abs_tol=1e-10, rel_tol=0):
                    raise ValueError(f"{name}: {key} differs from retained poses")
        if record.get("truth_input_to_localizers") is not False:
            errors.append("Truth was not reserved for evaluation")
        if record.get("restoration"):
            events = [json.loads(line) for line in (path.parent / "scan-stress.jsonl").read_text().splitlines()]
            stamp = min(event["stamp_s"] for event in events if event["phase"] == "restored")
            for name, expected in record["restoration"].items():
                actual = restoration(read_samples(path.parent / f"{name}-samples.csv"), stamp)
                if actual != expected:
                    errors.append(f"{name}: restoration claim differs from retained poses and observation event")
    except (OSError, ValueError, KeyError, TypeError) as error:
        errors.append(f"Native desktop localization: {error}")
    return errors
