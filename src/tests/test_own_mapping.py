import numpy as np
import pytest

from slam_learning.runtime.own_mapping import RayEvidence, deskew, interpolate_pose, transform


def test_motion_deskew_restores_a_fixed_world_point_across_yaw_wrap():
    times = [0., 1.]
    poses = np.array([[0., 0., np.deg2rad(179)], [1., 0., np.deg2rad(-179)]])
    target = np.array([[4., 2.]])
    local = np.concatenate([transform(target, np.linalg.inv(interpolate_pose(times, poses, t))) for t in times])
    corrected = deskew(local, np.array(times), times, poses, 1.)
    restored = transform(corrected, interpolate_pose(times, poses, 1.))
    np.testing.assert_allclose(restored, np.repeat(target, 2, axis=0), atol=1e-10)
    with pytest.raises(ValueError, match="bracket"):
        interpolate_pose(times, poses, 1.1)


def test_later_free_rays_remove_ghost_but_an_occluder_does_not_erase_wall():
    grid = RayEvidence()
    sensor = np.array([0., 0.])
    # First a ghost at 2m, later the stable wall at 4m.
    for t in range(3):
        grid.add(np.array([[2.02, .02]]), sensor, t)
    for t in range(3, 10):
        grid.add(np.array([[4.02, .02]]), sensor, t)
    assert len(grid.points("raw")) == 2
    assert len(grid.points("temporal")) == 1
    assert grid.points("temporal")[0, 0] > 3.9
    before = grid.free.copy()
    grid.add(np.array([[1.02, .02]]), sensor, 12.)
    wall = grid.cells(np.array([[4.02, .02]]))[0]
    assert grid.free[wall[1], wall[0]] == before[wall[1], wall[0]]


def test_same_time_bin_cannot_inflate_static_support():
    grid = RayEvidence()
    for t in (.01, .02, .03, .04):
        grid.add(np.array([[2.02, .02]]), np.array([0., 0.]), t)
    assert grid.hits.max() == 1
    assert grid.support_hits.max() == 1
    # Being observed rarely is not evidence of motion.
    assert len(grid.points("temporal")) == 1


def test_sparse_static_cell_survives_without_later_free_space_evidence():
    grid = RayEvidence()
    grid.add(np.array([[2.02, .02]]), np.array([0., 0.]), 0.)
    for t in range(1, 8):
        # The obstacle at 1m occludes the old 2m endpoint.
        grid.add(np.array([[1.02, .02]]), np.array([0., 0.]), t)
    cell = grid.cells(np.array([[2.02, .02]]))[0]
    assert grid.mask("temporal")[cell[1], cell[0]]
    assert grid.mask("after_free")[cell[1], cell[0]]


def test_clearing_needs_three_later_bins_and_a_new_hit_resets_it():
    grid = RayEvidence()
    sensor = np.array([0., 0.])
    near, far = np.array([[2.02, .02]]), np.array([[4.02, .02]])
    grid.add(near, sensor, 0.)
    for t in (1.01, 1.02, 1.03, 1.04):
        grid.add(far, sensor, t)
    cell = grid.cells(near)[0]
    assert grid.clear_bins[cell[1], cell[0]] == 1
    assert grid.mask("temporal")[cell[1], cell[0]]
    grid.add(far, sensor, 1.6)
    assert grid.mask("after_free")[cell[1], cell[0]]
    assert grid.mask("temporal")[cell[1], cell[0]]
    grid.add(far, sensor, 2.1)
    assert not grid.mask("after_free")[cell[1], cell[0]]
    assert not grid.mask("temporal")[cell[1], cell[0]]
    grid.add(near, sensor, 2.6)
    assert grid.mask("after_free")[cell[1], cell[0]]


def test_nearby_hit_protects_a_wall_against_small_registration_jitter():
    grid = RayEvidence()
    near = np.array([[2.02, .02]])
    grid.add(near, np.array([0., 0.]), 0.)
    cell = grid.cells(near)[0]
    for t in range(1, 7):
        grid.add(np.array([[2.10, .02], [4.02, .02]]), np.array([0., 0.]), t)
    assert grid.mask("temporal")[cell[1], cell[0]]


def test_weak_axis_protection_retains_rare_perpendicular_structure():
    grid = RayEvidence()
    long_wall = np.column_stack((np.arange(1., 9., .05), np.ones(160)))
    short_wall = np.column_stack((np.full(12, 3.), np.arange(2., 2.6, .05)[:12]))
    for points, count in [(long_wall, 6), (short_wall, 2)]:
        cells = grid.cells(points)
        grid.hits[cells[:, 1], cells[:, 0]] = count
    strict = grid.points("strict")
    protected = grid.points("protected")
    assert len(protected) > len(strict)
    assert np.any(protected[:, 1] > 1.9)
