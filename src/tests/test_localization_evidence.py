
import numpy as np
import pytest

from slam_learning.core.provenance import digest, write_json
from slam_learning.runtime.localization_evidence import trajectory_metrics
from slam_learning.runtime.runner import verify_record


@pytest.fixture
def localization_record(tmp_path):
    truth = np.zeros((3, 8))
    truth[:, 0] = [21, 22, 23]
    truth[:, 7] = 1
    estimate = truth.copy()
    estimate[:, 1] = [0.03, 0.04, 0.06]
    np.savetxt(tmp_path / "IRMCL.txt", estimate)
    np.savetxt(tmp_path / "seq_1_gt_pose.txt", truth)
    measured, count = trajectory_metrics(tmp_path / "IRMCL.txt", tmp_path / "seq_1_gt_pose.txt", 20, 0.01)
    write_json(tmp_path / "metrics.json", {"measured": measured})
    (tmp_path / "run.log").write_text("Measured localization run")
    (tmp_path / "loc_config.yml").write_text("native config")
    record = {
        "schema_version": 1, "kind": "author_localization", "status": "executed",
        "command": ["localize"], "exit_code": 0,
        "dataset": {"inputs_sha256": {"truth": digest(tmp_path / "seq_1_gt_pose.txt")}},
        "scoring": {"start_time_s": 20, "max_timestamp_difference_s": 0.01,
                    "scored_samples": count, "alignment": "none", "rotation_metric": "rotation_angle_deg"},
        "metrics": measured,
        "paper_comparison": {key: {"paper": value, "reproduced": value} for key, value in measured.items()},
        "artifacts": {path.name: {"sha256": digest(path), "availability": "portable"}
                      for path in tmp_path.iterdir()},
    }
    path = tmp_path / "record.json"
    write_json(path, record)
    return path, record


def test_valid_localization_has_pose_evidence_instead_of_cleaned_cloud(localization_record):
    path, _ = localization_record
    assert verify_record(path) == []


def test_rehashed_wrong_pose_cannot_reuse_old_localization_scores(localization_record):
    path, record = localization_record
    trajectory = path.parent / "IRMCL.txt"
    values = np.loadtxt(trajectory)
    values[0, 1] += 1
    np.savetxt(trajectory, values)
    record["artifacts"][trajectory.name]["sha256"] = digest(trajectory)
    write_json(path, record)
    assert any("differ from retained trajectories" in issue for issue in verify_record(path))


def test_forged_localization_table_cannot_pass_by_rehashing_metrics(localization_record):
    path, record = localization_record
    record["metrics"]["location_rmse_cm"] = 0.0
    metrics = path.parent / "metrics.json"
    write_json(metrics, {"measured": record["metrics"]})
    record["artifacts"][metrics.name]["sha256"] = digest(metrics)
    write_json(path, record)
    assert any("differ from retained trajectories" in issue for issue in verify_record(path))


def test_unreported_alignment_is_rejected(localization_record):
    path, record = localization_record
    record["scoring"]["alignment"] = "SE2 fitted to test truth"
    write_json(path, record)
    assert "Unsupported localization scoring protocol" in verify_record(path)


def test_missing_dataset_evidence_is_rejected(localization_record):
    path, record = localization_record
    record["dataset"]["inputs_sha256"] = {}
    write_json(path, record)
    assert "Localization dataset hashes missing or invalid" in verify_record(path)
