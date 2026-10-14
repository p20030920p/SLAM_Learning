import csv
import math

import numpy as np
import pytest

from slam_learning.runtime.presentation_evidence import read_samples, restoration, score, validate_truth


def series():
    data = np.zeros((101, 10))
    data[:, 0] = np.linspace(0, 10, 101)
    data[:, 4] = .03
    data[:, 6] = math.radians(1)
    data[:, 7] = .03
    data[:, 8] = math.radians(1)
    return data


def test_native_update_rmse_and_sustained_restore():
    values = series()
    assert score(values)["position_rmse_m"] == pytest.approx(.03)
    assert score(values)["post_warmup_5s_samples"] == 51
    assert restoration(values, 4)["converged"]
    values[-40:, 7] = .2
    assert not restoration(values, 4)["converged"]


def test_low_error_last_frame_does_not_establish_recovery():
    values = series()
    values[:-1, 7] = 1
    assert not restoration(values, 4)["converged"]


def test_missing_pose_updates_after_restore_are_unmeasured():
    assert restoration(series(), 9)["converged"] is None
    assert restoration(series(), 11)["status"] == "insufficient_post_restore_pose_updates"


def test_recomputed_errors_reject_rehashed_false_score(tmp_path):
    names = ["stamp_s", "truth_x", "truth_y", "truth_yaw", "estimate_x", "estimate_y",
             "estimate_yaw", "position_error_m", "yaw_error_rad", "nearest_truth_delta_s"]
    path = tmp_path / "samples.csv"
    values = series()
    values[0, 7] = 0
    with path.open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(names)
        writer.writerows(values)
    with pytest.raises(ValueError, match="differ from retained poses"):
        read_samples(path)


def test_independent_truth_rejects_wrong_model_or_coordinates():
    values = series()
    truth = [{"model": "omni_car", "stamp_s": row[0], "xyz": [0, 0, 0], "xyzw": [0, 0, 0, 1]} for row in values]
    validate_truth(values, truth)
    truth[50]["xyz"][0] = .5
    with pytest.raises(ValueError, match="independent simulator"):
        validate_truth(values, truth)
