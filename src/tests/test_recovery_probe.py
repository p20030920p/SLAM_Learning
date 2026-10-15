"""Behavioral checks for sensor-only planar recovery prototypes."""
import numpy as np

from slam_learning.runtime.recovery_probe import Probe, SurfaceMap, compose, fit, inverse, transform


def test_se2_odometry_composition_preserves_sensor_extrinsic():
    pose = np.array([4., -2., .8])
    displacement = np.array([.3, -.1, -.2])
    sensor = np.array([[.18, 0., .22], [1.2, .4, .6]])
    assert np.allclose(transform(transform(sensor, displacement), pose), transform(sensor, compose(pose, displacement)))
    assert np.allclose(compose(inverse(pose), pose), 0., atol=1e-12)


def test_guard_does_not_invent_translation_along_parallel_walls():
    x = np.linspace(-8, 8, 401)
    walls = np.concatenate([np.column_stack((x, np.full(len(x), y), np.full(len(x), .4))) for y in (-1.5, 1.5)])
    surface = SurfaceMap(walls, 2)
    scan = walls[np.abs(walls[:, 0]) < 2.8]
    result, info = fit([(surface, scan)], np.array([1., .18, .03]), guarded=True)
    assert info["rank"] < 3
    assert abs(result[0] - 1.) < .03
    assert abs(result[1]) < .02
    assert abs(result[2]) < .01


def test_guard_aligns_asymmetric_observable_geometry():
    axis = np.linspace(-3, 3, 180)
    points = np.concatenate([np.column_stack((axis, np.full(len(axis), y), np.full(len(axis), .4))) for y in (-2, 2)] +
                            [np.column_stack((np.full(len(axis), 3.), axis, np.full(len(axis), .4)))])
    surface = SurfaceMap(points, 2)
    fitted, info = fit([(surface, points)], np.array([.2, -.15, .06]), guarded=True)
    assert info["rank"] == 3
    assert np.linalg.norm(fitted[:2]) < .015
    assert abs(fitted[2]) < .005


def test_no_correspondences_preserves_odometry_prediction():
    axis = np.linspace(-2, 2, 100)
    points = np.column_stack((axis, np.zeros(100), np.zeros(100)))
    predicted = np.array([20., 20., 1.])
    result, info = fit([(SurfaceMap(points, 2), points)], predicted, guarded=True)
    assert np.array_equal(result, predicted)
    assert info["fallback"] is True


def test_recovery_requires_consecutive_motion_consistent_proposals(monkeypatch):
    from slam_learning.runtime import recovery_probe
    sequence = iter((np.array([.8, 0., 0.]), np.array([-.8, 0., 0.]), np.array([-.8, 0., 0.])))
    monkeypatch.setattr(recovery_probe, "search_candidates", lambda groups, centre:
                        (next(sequence), {"accepted_geometry": True, "best_score": .9, "margin": .1}))
    points = np.column_stack((np.linspace(-2, 2, 100), np.zeros(100), np.zeros(100)))
    surface = SurfaceMap(points, 2)
    probe = Probe([0., 0., 0.], guarded=True, depth=False, recovery=True)
    group = (surface, np.empty((0, 3)))
    for stamp in (0., 3.):
        pose, info = probe.update(stamp, np.zeros(3), group)
        assert np.allclose(pose, 0.)
        assert info["relocalized"] is False
    pose, info = probe.update(6., np.zeros(3), group)
    assert np.allclose(pose, [-.8, 0., 0.])
    assert info["relocalized"] is True


def test_finer_grid_still_rejects_an_ambiguous_parallel_corridor():
    from slam_learning.runtime.refined_probe import candidates
    x = np.linspace(-12, 12, 801)
    walls = np.concatenate([np.column_stack((x, np.full(len(x), y), np.full(len(x), .4))) for y in (-1.5, 1.5)])
    scan = walls[np.abs(walls[:, 0]) < 2.8]
    _, info = candidates([(SurfaceMap(walls, 2), scan)], np.array([1., 0., 0.]))
    assert info["best_score"] > .9
    assert info["accepted_geometry"] is False


def test_height_reference_uses_provided_A_poses_and_actual_extrinsic_without_truth(tmp_path):
    from scipy.spatial.transform import Rotation
    from slam_learning.runtime.frame_prior import height_from_mapping
    (tmp_path / "probe-robot.urdf").write_text('<robot name="test"><link name="base_footprint"/><link name="lidar_3d_link"/><joint name="sensor" type="fixed"><parent link="base_footprint"/><child link="lidar_3d_link"/><origin xyz="0.1 0 0.3" rpy="0.05 0.02 0.1"/></joint></robot>')
    mount = np.eye(4)
    mount[:3, :3] = Rotation.from_euler("xyz", [.05, .02, .1]).as_matrix()
    mount[:3, 3] = [.1, 0., .3]
    poses = []
    for index in range(12):
        body = np.eye(4)
        body[:3, :3] = Rotation.from_euler("xyz", [.04 * np.sin(index), .03, .1 * index]).as_matrix()
        body[:3, 3] = [index * .1, 0., .094]
        poses.append(body @ mount)
    np.savez_compressed(tmp_path / "mapping-clouds.npz", poses=np.array(poses))
    prior = height_from_mapping(tmp_path)
    assert abs(prior["ground_z_m"] - .094) < 1e-12
    assert prior["localization_B_truth_used"] is False
    assert not (tmp_path / "truth.jsonl").exists()


def test_nested_mapping_manifest_requires_parent_binding_and_unchanged_maps(tmp_path):
    import json
    from slam_learning.core.provenance import digest
    from slam_learning.runtime.runner import verify_record
    maps = tmp_path / "probe-maps"
    maps.mkdir()
    sources = []
    for kind in ("lidar2d", "lidar3d", "depth"):
        source = maps / ("depth.npy" if kind == "depth" else f"{kind}/points.npy")
        source.parent.mkdir(exist_ok=True)
        np.save(source, np.zeros((12, 3)))
        sources.append(source)
    names = ("mapping-clouds.npz", "probe-mapping-inputs.npz", "probe-mapping-inputs.json")
    for name in names:
        (tmp_path / name).write_bytes(b"retained mapping input")
    manifest = {"kind": "probe_mapping_A", "provided_mapping_poses": True, "truth_to_localization_B": False,
                "world_sha256": "world", "inputs": {name: digest(tmp_path / name) for name in names},
                "maps": {kind: {"voxel_points": 12, "raw_points": 24} for kind in ("lidar2d", "lidar3d", "depth")}}
    path = maps / "record.json"
    path.write_text(json.dumps(manifest))
    (tmp_path / "runtime.json").write_text(json.dumps({"world_sha256": "world"}))
    assert verify_record(path)
    parent = {"schema_version": 1, "kind": "native_desktop_mapping", "probe_mapping_A": {"checked": True},
              "artifacts": {source.relative_to(tmp_path).as_posix(): {"sha256": digest(source)} for source in [path, *sources]}}
    (tmp_path / "record.json").write_text(json.dumps(parent))
    assert not verify_record(path)
    np.save(sources[0], np.ones((12, 3)))
    assert verify_record(path)
