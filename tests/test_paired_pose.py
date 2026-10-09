import numpy as np
import pytest

from slam_learning.core.paired_pose import paired_translations, error_description


def test_pairs_preserve_marginal_and_gauge():
    pair = paired_translations(141, 0.10, 104)
    for values in pair.values():
        assert np.array_equal(values[0], [0, 0, 0])
        assert error_description(values)["rms_m"] == pytest.approx(0.10)
        assert abs(values[:, 0].mean()) < 1e-15
    assert np.array_equal(np.sort(pair["independent"][:, 0]), np.sort(pair["correlated"][:, 0]))
    assert error_description(pair["correlated"])["lag1_correlation"] > 0.9


def test_zero_and_invalid_pose_errors():
    assert not np.any(paired_translations(8, 0, 205)["correlated"])
    with pytest.raises(ValueError):
        paired_translations(3, 0.1, 104)
    with pytest.raises(ValueError):
        paired_translations(8, -0.1, 104)
