import pytest

from slam_learning.experiments.evidence_stress import change_probability


def test_single_reading_independent_and_shared_models_agree():
    p1 = change_probability(0.2, 1, 0.02, 0.15, 0.5, 0.1, "independent_pose_noise")
    p2 = change_probability(0.2, 1, 0.02, 0.15, 0.5, 0.1, "shared_pose_latent")
    assert p1 == p2


def test_shared_pose_uncertainty_does_not_vanish_with_more_readings():
    independent = change_probability(0.2, 100, 0.02, 0.15, 0.5, 0.1, "independent_pose_noise")
    shared = change_probability(0.2, 100, 0.02, 0.15, 0.5, 0.1, "shared_pose_latent")
    assert independent > 0.99
    assert shared < 0.1


def test_no_pose_uncertainty_reduces_to_the_conditional_model():
    assert change_probability(0.05, 10, 0.02, 0, 0.5, 0.1, "shared_pose_latent") == pytest.approx(
        change_probability(0.05, 10, 0.02, 0, 0.5, 0.1, "condition_on_pose"))
