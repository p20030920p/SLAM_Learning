import numpy as np
import pytest

from slam_learning.core.metrics import compare_paper, confusion_metrics, score_map
from slam_learning.core.pcd import read_pcd, write_pcd


def test_keep_everything_and_delete_everything_are_not_good_maps():
    gt = np.array([0, 0, 0, 1])
    kept = confusion_metrics(gt, np.zeros(4))
    removed = confusion_metrics(gt, np.ones(4))
    assert kept["SA"] == 100 and kept["DA"] == 0 and kept["AA"] == 0
    assert removed["SA"] == 0 and removed["DA"] == 100 and removed["HA"] == 0


def test_geometric_mean_is_not_harmonic_mean():
    score = confusion_metrics(np.array([0, 0, 1, 1]), np.array([0, 0, 1, 0]))
    assert score["AA"] == pytest.approx(70.710678)
    assert score["HA"] == pytest.approx(66.666667)


@pytest.mark.parametrize("gt,removed", [([0, 2], [0, 1]), ([0, 1], [0]), ([0, 0], [0, 1]), ([], [])])
def test_invalid_and_one_class_labels_are_rejected(gt, removed):
    with pytest.raises(ValueError):
        confusion_metrics(np.array(gt), np.array(removed))


def test_map_nearest_neighbor_and_empty_output(tmp_path):
    gt, output = tmp_path / "gt.pcd", tmp_path / "output.pcd"
    write_pcd(gt, np.array([[0, 0, 0], [1, 0, 0], [2, 0, 0]]), np.array([0, 0, 1]))
    write_pcd(output, np.array([[0.04, 0, 0], [1, 0, 0]]))
    assert score_map(gt, output)["AA"] == 100
    write_pcd(output, np.empty((0, 3)))
    assert score_map(gt, output)["SA"] == 0
    assert score_map(gt, output)["DA"] == 100


def test_corrupt_binary_payload_is_rejected(tmp_path):
    path = tmp_path / "cloud.pcd"
    write_pcd(path, np.array([[0, 0, 0]]))
    path.write_bytes(path.read_bytes()[:-1])
    with pytest.raises(ValueError, match="payload"):
        read_pcd(path)


def test_unlabeled_scan_preserves_geometry_and_sensor_pose(tmp_path):
    source, staged = tmp_path / "source.pcd", tmp_path / "staged.pcd"
    pose = [3.5, -2, 0.4, 1, 0, 0, 0]
    write_pcd(source, np.array([[1, 2, 3]]), np.array([252]), viewpoint=pose)
    cloud = read_pcd(source)
    write_pcd(staged, cloud.xyz(), viewpoint=cloud.viewpoint)
    result = read_pcd(staged)
    assert result.records.dtype.names == ("x", "y", "z")
    assert result.viewpoint == pose
    np.testing.assert_array_equal(result.xyz(), cloud.xyz())


def test_crlf_and_mixed_integer_fields(tmp_path):
    path = tmp_path / "cloud.pcd"
    header = "FIELDS x y z intensity\r\nSIZE 4 4 4 4\r\nTYPE F F F U\r\nCOUNT 1 1 1 1\r\nWIDTH 1\r\nHEIGHT 1\r\nPOINTS 1\r\nDATA binary\r\n"
    data = np.array([(1, 2, 3, 1)], dtype=[("x", "<f4"), ("y", "<f4"), ("z", "<f4"), ("intensity", "<u4")])
    path.write_bytes(header.encode() + data.tobytes())
    cloud = read_pcd(path)
    assert cloud.xyz().tolist() == [[1, 2, 3]]
    assert cloud.records["intensity"].tolist() == [1]


def test_paper_values_do_not_become_self_baselines():
    target = {"source": "paper", "table": "I", "values": {"SA": 96.76}, "absolute_tolerance_pp": 0.01}
    assert not compare_paper({"SA": 96.95}, target)["matched"]


@pytest.mark.parametrize("values,measured,tolerance", [({}, {}, 0.01),
    ({"SA": 97}, {"SA": float("nan")}, 0.01), ({"SA": 101}, {"SA": 97}, 0.01),
    ({"SA": 97}, {"SA": 97}, -1)])
def test_vacuous_or_invalid_paper_agreement_is_rejected(values, measured, tolerance):
    with pytest.raises(ValueError):
        compare_paper(measured, {"values": values, "absolute_tolerance_pp": tolerance})
