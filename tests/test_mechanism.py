import numpy as np

from slam_learning.synthetic import classify_change, normalize_residual


def test_occlusion_is_unknown_not_deletion():
    prediction, _ = classify_change(np.zeros((2, 2)), np.array([True, False]), 0.1, True, True)
    assert prediction.tolist() == [0, -1]


def test_common_pose_error_and_single_object_motion_are_separated():
    residual = np.array([[0.3, 0], [0.3, 0], [1.3, 0]])
    prediction, correction = classify_change(residual, np.ones(3, dtype=bool), 0.1, True, True)
    assert prediction.tolist() == [0, 0, 1]
    assert correction.tolist() == [0.3, 0]


def test_majority_coherent_movers_are_an_explicit_counterexample():
    residual = np.array([[0.3, 0], [1.3, 0], [1.3, 0]])
    _, correction = normalize_residual(residual, np.ones(3, dtype=bool))
    # Median estimates pose+object motion; it cannot discover the real pose by itself.
    assert correction[0] == 1.3


def test_no_visible_anchor_produces_no_pose_information():
    _, correction = normalize_residual(np.ones((3, 2)), np.zeros(3, dtype=bool))
    assert np.array_equal(correction, [0, 0])
