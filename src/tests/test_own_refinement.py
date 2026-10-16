import numpy as np

from slam_learning.runtime.own_mapping import pose2, transform
from slam_learning.runtime.own_refinement import refine_scan_pose


def test_local_alignment_recovers_pose_with_unmatched_moving_returns():
    rng = np.random.default_rng(42)
    # Irregular static corners avoid a repeated-line correspondence ambiguity.
    reference = rng.uniform([-3, -2], [3, 2], size=(450, 2))
    truth = pose2(.4, -.2, .1)
    scan = transform(reference, np.linalg.inv(truth))
    scan = np.vstack((scan, rng.uniform([7, 7], [9, 9], size=(60, 2))))
    initial = truth @ pose2(.06, -.04, .015)
    result = refine_scan_pose(scan, initial, reference)
    np.testing.assert_allclose(result, truth, atol=2e-3)


def test_insufficient_supported_map_keeps_odometry_prediction():
    initial = pose2(1., 2., .1)
    result = refine_scan_pose(np.ones((50, 2)), initial, np.ones((20, 2)))
    np.testing.assert_array_equal(result, initial)
