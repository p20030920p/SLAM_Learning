import numpy as np
import pytest

from slam_learning.evaluation_check import check_point_order
from slam_learning.pcd import Cloud


def cloud(points):
    records = np.zeros(len(points), dtype=[("x", "f4"), ("y", "f4"), ("z", "f4")])
    for i, axis in enumerate(("x", "y", "z")):
        records[axis] = np.array(points)[:, i]
    return Cloud(records, [0, 0, 0, 1, 0, 0, 0])


def test_evaluator_reordering_cannot_preserve_label_identity():
    gt = cloud([[0, 0, 0], [1, 2, 3]])
    check_point_order(gt, cloud([[0, 0, 0], [1, 2, 3]]))
    with pytest.raises(ValueError, match="identity/order"):
        check_point_order(gt, cloud([[1, 2, 3], [0, 0, 0]]))
    with pytest.raises(ValueError, match="point count"):
        check_point_order(gt, cloud([[0, 0, 0]]))
