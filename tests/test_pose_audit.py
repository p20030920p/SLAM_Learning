import gzip
import pickle

import numpy as np
import pytest

from slam_learning.pose_audit import audit_camera_snapshots


def test_absolute_mapper_poses_reject_loader_normalization(tmp_path):
    poses = np.repeat(np.eye(4)[None], 3, axis=0)
    poses[:, 0, 3] = [10, 11, 12]
    snapshots = [tmp_path / f"{i:06d}.pkl.gz" for i in (1, 2)]
    for path, pose in zip(snapshots, poses[1:]):
        with gzip.open(path, "wb") as stream:
            pickle.dump({"camera_pose": pose}, stream)
    assert audit_camera_snapshots(snapshots, poses, [1, 2])["maximum_absolute_matrix_error"] == 0
    relative = np.linalg.inv(poses[0])[None] @ poses
    with pytest.raises(ValueError, match="absolute poses"):
        audit_camera_snapshots(snapshots, relative, [1, 2])


def test_missing_initialization_is_explicit_not_a_shifted_frame(tmp_path):
    snapshots = [tmp_path / "000001.pkl.gz", tmp_path / "000003.pkl.gz"]
    with pytest.raises(ValueError, match="indices"):
        audit_camera_snapshots(snapshots, np.repeat(np.eye(4)[None], 4, axis=0), [1, 2, 3])
