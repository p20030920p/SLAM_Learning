import json

import numpy as np
import pytest

from slam_learning.runtime.map_point_audit import geometric_labels, retention_score, verify_map_point_audit


def geometry():
    pose = np.eye(4)
    pose[:3, :3] = [[0, -1, 0], [1, 0, 0], [0, 0, 1]]
    pose[0, 3] = 2
    return {"points": np.asarray([[3, 0, 0], [3.03, 0, 0], [5, 5, 0], [.1, 0, 0]]),
            "scan_ids": np.zeros(4, dtype=int), "box_poses": pose[None, None],
            "sensor_origins": np.zeros((1, 3)), "box_sizes": np.asarray([[1, 2, 1]])}


def test_rotated_moving_box_surface_shell_and_self_return():
    assert geometric_labels(geometry()).tolist() == [1, -1, 0, -1]


def test_ambiguous_returns_do_not_enter_static_or_dynamic_scores():
    result = retention_score(np.asarray([1, -1, 0, -1]), np.asarray([False, True, True, False]))
    assert result == {"static_retention": 1, "dynamic_removal": 1,
                      "removed_static_points": 0, "retained_dynamic_points": 0}
    with pytest.raises(ValueError, match="exact scored input"):
        retention_score(np.asarray([1, 0]), np.asarray([True]))


def test_rehashed_false_labels_are_rejected_by_geometry(tmp_path):
    data = geometry()
    data["labels"] = np.zeros(4, dtype=np.int8)
    np.savez(tmp_path / "point-label-inputs.npz", **data)
    record = {"configurations": {}}
    (tmp_path / "record.json").write_text(json.dumps(record))
    assert "geometry" in verify_map_point_audit(tmp_path / "record.json", record)[0]
