import csv
import math

import pytest

from slam_learning.runtime.poses3d import score_poses3d


def poses(tmp_path, *, sign=1):
    path = tmp_path / "pose.csv"
    names = ["stamp_s", *[prefix+key for prefix in ("truth_", "estimate_")
                          for key in ("x", "y", "z", "qx", "qy", "qz", "qw")], "nearest_truth_delta_s"]
    truth = [{"stamp_s": float(i), "model": "omni_car", "xyz": [0, 0, .1], "xyzw": [0, 0, 0, 1]}
             for i in range(11)]
    with path.open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(names)
        for row in truth:
            writer.writerow([row["stamp_s"], *row["xyz"], *row["xyzw"], .03, .04, .22,
                             0, 0, sign*math.sin(.1), sign*math.cos(.1), 0])
    return path, truth


@pytest.mark.parametrize("sign", [1, -1])
def test_full_position_and_quaternion_rotation_not_only_xy_yaw(tmp_path, sign):
    result = score_poses3d(*poses(tmp_path, sign=sign))
    assert result["xyz_rmse_m"] == pytest.approx(.13)
    assert result["z_rmse_m"] == pytest.approx(.12)
    assert result["rotation_rmse_deg"] == pytest.approx(math.degrees(.2))


@pytest.mark.parametrize("field", ["xyz", "xyzw", "model", "stamp_s"])
def test_reject_wrong_reference_pose_or_timestamp(tmp_path, field):
    path, truth = poses(tmp_path)
    truth[5][field] = {"xyz": [1, 0, .1], "xyzw": [0, 0, 1, 0], "model": "obstacle", "stamp_s": 5.1}[field]
    with pytest.raises(ValueError, match="independent synchronized"):
        score_poses3d(path, truth)
