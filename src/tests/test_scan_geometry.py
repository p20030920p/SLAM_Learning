import numpy as np

from slam_learning.core.scan_geometry import normal_coverage


def test_parallel_walls_have_one_weak_normal_direction():
    angles = np.linspace(-2*np.pi/3, 2*np.pi/3, 72)
    with np.errstate(divide="ignore"):
        ranges = 1.5/np.abs(np.sin(angles))
    ranges[ranges > 3.5] = np.inf
    result = normal_coverage(ranges, angles[0], angles[1]-angles[0], .08, 3.5)
    assert result["ratio"] < 1e-10


def test_visible_perpendicular_end_adds_normal_direction():
    angles = np.linspace(-np.pi, np.pi, 720)
    with np.errstate(divide="ignore"):
        sides = 1.5/np.abs(np.sin(angles))
        ends = 3/np.abs(np.cos(angles))
    result = normal_coverage(np.minimum(sides, ends), angles[0], angles[1]-angles[0], .08, 12)
    assert result["ratio"] > .1
