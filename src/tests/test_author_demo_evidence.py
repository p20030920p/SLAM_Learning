import numpy as np
import pytest

from slam_learning.runtime.author_demo_evidence import distance_summary, verify_author_demo


def test_distance_log_is_not_square_rooted_twice(tmp_path):
    path = tmp_path / "error_position.txt"
    np.savetxt(path, [3, 4])
    assert distance_summary(path)["position_rmse_cells"] == pytest.approx(np.sqrt(12.5))
    assert distance_summary(path)["final_error_cells"] == 4
    record = {"method": "adam-mcl", "metrics": {"position_rmse_cells": np.sqrt(3.5), "final_error_cells": 2, "updates": 2, "paper_comparison": False}}
    assert len(verify_author_demo(tmp_path / "record.json", record)) == 2
