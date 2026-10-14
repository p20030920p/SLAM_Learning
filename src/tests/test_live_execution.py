"""Reject reused Raw views and old-result playback labelled as live execution."""
import csv
import json

import numpy as np
import pytest

from slam_learning.core.provenance import digest
from slam_learning.runtime.author_demo_evidence import verify_author_demo
from slam_learning.runtime.presentation_evidence import score, verify_presentation


@pytest.fixture
def live_scene(tmp_path):
    values = np.zeros((20, 10))
    values[:, 0] = np.arange(20)
    values[:, 4] = values[:, 7] = .03
    names = ["stamp_s", "truth_x", "truth_y", "truth_yaw", "estimate_x", "estimate_y",
             "estimate_yaw", "position_error_m", "yaw_error_rad", "nearest_truth_delta_s"]
    with (tmp_path / "raw-samples.csv").open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(names)
        writer.writerows(values)
    truth = [{"model": "omni_car", "stamp_s": float(row[0]), "xyz": [0, 0, 0], "xyzw": [0, 0, 0, 1]} for row in values]
    (tmp_path / "truth.jsonl").write_text("\n".join(json.dumps(row) for row in truth))
    config = {"title": "Raw live RViz", "config": "view-raw.rviz", "map_topic": "/raw/map",
              "pose_topic": "/raw/amcl_pose", "tf_topic": "/raw/view/tf"}
    (tmp_path / "views.json").write_text(json.dumps({"raw": config}))
    (tmp_path / "view-raw.rviz").write_text("Value: /raw/map\nValue: /raw/amcl_pose\n")
    updates = [{"case": "raw", "stamp_s": float(row[0])} for row in values]
    (tmp_path / "view-updates.jsonl").write_text("\n".join(json.dumps(row) for row in updates))
    (tmp_path / "raw.mp4").write_bytes(b"test capture identity")
    view = {"case": "raw", "window_title": config["title"], "map_topic": config["map_topic"],
            "pose_topic": config["pose_topic"], "tf_topic": config["tf_topic"], "video": "raw.mp4",
            "sha256": digest(tmp_path / "raw.mp4")}
    record = {"truth_input_to_localizers": False, "metrics": {"cases": {"raw": score(values)}},
              "native_views": [view]}
    return tmp_path / "record.json", record


def test_each_live_view_is_bound_to_its_method(live_scene):
    path, record = live_scene
    assert verify_presentation(path, record) == []


@pytest.mark.parametrize("change", ["another_method", "raw_reused_config", "stopped_updates"])
def test_reject_wrong_or_stale_live_rviz(live_scene, change):
    path, record = live_scene
    if change == "another_method":
        record["native_views"][0]["pose_topic"] = "/dufomap/amcl_pose"
    elif change == "raw_reused_config":
        (path.parent / "view-raw.rviz").write_text("Value: /dufomap/map\nValue: /dufomap/amcl_pose\n")
    else:
        (path.parent / "view-updates.jsonl").write_text(json.dumps({"case": "raw", "stamp_s": 0}))
    assert verify_presentation(path, record)


@pytest.fixture
def author_states(tmp_path):
    events = [{"method": "dufomap", "serial": i, "frame": i, "wall_unix": i+1,
               "sha256": f"state-{i}"} for i in range(10)]
    shown = [{**row, "published_unix": row["wall_unix"]+.1} for row in events]
    (tmp_path / "execution.json").write_text(json.dumps({"started_unix": 0, "finished_unix": 20}))
    return tmp_path / "record.json", events, shown


def check_states(fixture):
    path, events, shown = fixture
    for name, rows in (("live-events.jsonl", events), ("live-published.jsonl", shown)):
        (path.parent / name).write_text("\n".join(json.dumps(row) for row in rows))
    return verify_author_demo(path, {"method": "dufomap", "live_state": {"enabled": True}})


def test_current_author_computation_is_live(author_states):
    assert check_states(author_states) == []


@pytest.mark.parametrize("change", ["old_results", "other_method", "wrong_state", "backward_frame"])
def test_reject_old_or_mislabelled_author_states(author_states, change):
    path, events, shown = author_states
    if change == "old_results":
        (path.parent / "execution.json").write_text(json.dumps({"started_unix": 100, "finished_unix": 120}))
    elif change == "other_method":
        shown[0]["method"] = "beautymap"
    elif change == "wrong_state":
        shown[0]["sha256"] = "different-recording"
    else:
        events[4]["frame"] = 0
    assert check_states(author_states)


def test_wall_clock_adjustment_does_not_reorder_native_frames(author_states):
    _, events, shown = author_states
    events[5]["wall_unix"] = 4.5
    shown[5]["wall_unix"] = 4.5
    assert check_states(author_states) == []
