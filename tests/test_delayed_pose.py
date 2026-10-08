import numpy as np
import pytest

from slam_learning.delayed_pose import prefix_errors


def test_late_intervention_is_reproducible_and_fixes_first_pose():
    values = prefix_errors(8, .30, 417)
    assert np.array_equal(values, prefix_errors(8, .30, 417))
    assert np.all(values[0] == 0)
    assert np.all(values[:, 1:] == 0)
    assert np.sqrt(np.mean(values[:, 0] ** 2)) == pytest.approx(.30)


def test_zero_error_gate_has_no_hidden_random_translation():
    assert np.array_equal(prefix_errors(8, 0, 518), np.zeros((8, 3)))


def test_invalid_prefix_intervention_rejected():
    with pytest.raises(ValueError):
        prefix_errors(1, .30, 417)
    with pytest.raises(ValueError):
        prefix_errors(8, -.30, 417)
