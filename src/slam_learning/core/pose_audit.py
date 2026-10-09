"""Verify the coordinate convention saved by an executed mapper."""
from __future__ import annotations

import gzip
import pickle
from pathlib import Path

import numpy as np

from slam_learning.core.provenance import digest


def audit_camera_snapshots(snapshots: list[Path], poses: np.ndarray,
                           expected_indices: list[int], tolerance: float = 1e-6) -> dict:
    indices = [int(path.name.split(".")[0]) for path in snapshots]
    if not indices or indices != expected_indices or any(i < 0 or i >= len(poses) for i in indices):
        raise ValueError("Native snapshot observation indices are incomplete or invalid")
    errors, hashes = [], {}
    for path, index in zip(snapshots, indices):
        # Call only on fully verified, locally generated native snapshots.
        with gzip.open(path, "rb") as stream:
            saved = np.asarray(pickle.load(stream)["camera_pose"])
        if saved.shape != (4, 4) or not np.isfinite(saved).all():
            raise ValueError("Invalid native camera matrix")
        errors.append(float(np.max(np.abs(saved-poses[index]))))
        hashes[str(path)] = digest(path)
    if max(errors) > tolerance:
        raise ValueError("Native camera poses differ from supplied absolute poses")
    return {"checked_native_camera_poses": len(errors), "maximum_absolute_matrix_error": max(errors),
            "source_hashes": hashes}
