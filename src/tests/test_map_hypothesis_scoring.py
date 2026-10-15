import csv
import importlib.util
import math
from pathlib import Path

import numpy as np
import pytest

_source = Path(__file__).resolve().parents[1] / "scripts/presentation/summarize_map_hypotheses.py"
_spec = importlib.util.spec_from_file_location("map_hypothesis_scoring", _source)
scoring = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(scoring)


def test_missing_method_cannot_win_with_zero_error():
    rows = np.array([[0, .1, 0], [.1, .1, 0]])
    result = scoring.grid_scores({"raw": rows, "clean": np.empty((0, 3))}, 0, .2)
    assert result["common_grid_samples"] == 0
    assert result["methods"]["clean"]["output_coverage"] == 0
    assert result["methods"]["clean"]["success_fraction_all_grid"] == 0
    assert result["methods"]["clean"]["common_xyz_rmse_m"] is None


def test_future_and_stale_poses_are_not_scored_as_current():
    rows = np.array([[.1, .01, 0]])
    result = scoring.grid_scores({"raw": rows}, 0, .5)
    # t=0 precedes the output; t=.3,.4 have stale output. Only t=.1,.2 count.
    assert result["methods"]["raw"]["output_coverage"] == pytest.approx(.4)
    assert result["methods"]["raw"]["success_fraction_all_grid"] == pytest.approx(.4)


def test_comparison_uses_common_grid_and_signed_gain():
    raw = np.array([[0, .1, 0], [.1, .2, 0], [.2, .3, 0]])
    clean = np.array([[.2, .1, 0]])
    result = scoring.grid_scores({"raw": raw, "clean": clean}, 0, .3)
    assert result["common_grid_samples"] == 1
    assert result["methods"]["raw"]["common_xyz_rmse_m"] == pytest.approx(.3)
    assert result["methods"]["clean"]["paired_rmse_gain_m"] == pytest.approx(.2)


@pytest.mark.parametrize("sign", [1, -1])
def test_xyz_error_and_quaternion_sign_are_respected(tmp_path, sign):
    path = tmp_path / "poses.csv"
    keys = ["stamp_s", *[prefix + key for prefix in ("truth_", "estimate_")
                        for key in ("x", "y", "z", "qx", "qy", "qz", "qw")]]
    with path.open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(keys)
        writer.writerow([0, 0, 0, 0, 0, 0, 0, 1, .03, .04, .12,
                         0, 0, sign * math.sin(.1), sign * math.cos(.1)])
    values = scoring.pose_errors(path)
    assert values[0, 1] == pytest.approx(.13)
    assert values[0, 2] == pytest.approx(math.degrees(.2))
