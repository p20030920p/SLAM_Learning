import csv
import json
import math

import numpy as np
import pytest

from slam_learning.core.provenance import digest
from slam_learning.runtime.presentation_evidence import read_samples, restoration, score, validate_truth, verify_case_replay


def series():
    data = np.zeros((101, 10))
    data[:, 0] = np.linspace(0, 10, 101)
    data[:, 4] = .03
    data[:, 6] = math.radians(1)
    data[:, 7] = .03
    data[:, 8] = math.radians(1)
    return data


def test_native_update_rmse_and_sustained_restore():
    values = series()
    assert score(values)["position_rmse_m"] == pytest.approx(.03)
    assert score(values)["post_warmup_5s_samples"] == 51
    assert restoration(values, 4)["converged"]
    values[-40:, 7] = .2
    assert not restoration(values, 4)["converged"]


def test_low_error_last_frame_does_not_establish_recovery():
    values = series()
    values[:-1, 7] = 1
    assert not restoration(values, 4)["converged"]


def test_missing_pose_updates_after_restore_are_unmeasured():
    assert restoration(series(), 9)["converged"] is None
    assert restoration(series(), 11)["status"] == "insufficient_post_restore_pose_updates"


def test_recomputed_errors_reject_rehashed_false_score(tmp_path):
    names = ["stamp_s", "truth_x", "truth_y", "truth_yaw", "estimate_x", "estimate_y",
             "estimate_yaw", "position_error_m", "yaw_error_rad", "nearest_truth_delta_s"]
    path = tmp_path / "samples.csv"
    values = series()
    values[0, 7] = 0
    with path.open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(names)
        writer.writerows(values)
    with pytest.raises(ValueError, match="differ from retained poses"):
        read_samples(path)


def test_independent_truth_rejects_wrong_model_or_coordinates():
    values = series()
    truth = [{"model": "omni_car", "stamp_s": row[0], "xyz": [0, 0, 0], "xyzw": [0, 0, 0, 1]} for row in values]
    validate_truth(values, truth)
    truth[50]["xyz"][0] = .5
    with pytest.raises(ValueError, match="independent simulator"):
        validate_truth(values, truth)


@pytest.fixture
def case_replay(tmp_path):
    scene = tmp_path / "scene"
    output = scene / "methods" / "raw"
    output.mkdir(parents=True)
    values = series()
    names = ["stamp_s", "truth_x", "truth_y", "truth_yaw", "estimate_x", "estimate_y",
             "estimate_yaw", "position_error_m", "yaw_error_rad", "nearest_truth_delta_s"]
    with (scene / "raw-samples.csv").open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(names)
        writer.writerows(values)
    config = {"method": "raw", "mapping_scene": "static", "map_yaml": "original/raw/map.yaml"}
    (scene / "cases.json").write_text(json.dumps({"raw": config}))
    for name in ("truth.jsonl", "metrics.json", "maps/raw/map.pgm", "maps/raw/map.yaml"):
        target = scene / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("fixture")
    inputs = {name: digest(scene / name) for name in
              ("raw-samples.csv", "truth.jsonl", "metrics.json", "cases.json", "maps/raw/map.pgm", "maps/raw/map.yaml")}
    replay = {"common_start_s": 0, "common_end_s": 10, "frames": 81}
    parent = {"kind": "native_desktop_localization", "status": "executed", "source_run": "native-run",
              "result_replay": replay, "artifacts": {name: {"sha256": sha} for name, sha in inputs.items()}}
    (scene / "record.json").write_text(json.dumps(parent))
    child = {"parent_record": "../../record.json", "parent_sha256": digest(scene / "record.json"),
             "case": "raw", "case_configuration": config, "source_run": "native-run", "source_inputs": inputs,
             "metrics": score(values), "result_replay": replay.copy(), "restoration": None,
             "artifacts": {name: {} for name in ("result.mp4", "result.gif", "frame-mid.png")}}
    return output / "record.json", child


def test_case_replay_binds_native_case_sources(case_replay):
    path, record = case_replay
    assert verify_case_replay(path, record) == []


@pytest.mark.parametrize("change", ["algorithm", "score", "interval", "source", "case"])
def test_case_replay_rejects_misassigned_or_changed_evidence(case_replay, change):
    path, record = case_replay
    if change == "algorithm":
        record["case_configuration"] = {**record["case_configuration"], "method": "dufomap"}
    elif change == "score":
        record["metrics"]["position_rmse_m"] = 0
    elif change == "interval":
        record["result_replay"]["common_end_s"] = 5
    elif change == "source":
        record["source_inputs"]["maps/raw/map.pgm"] = "0"*64
    else:
        record["case"] = "beautymap"
    assert verify_case_replay(path, record)
