import copy
import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from slam_learning.identity_budget import (
    ARMS, check_resources, digest, hypothesis_decision, load_snapshot, object_id, readout, restore_fixed_semantics,
    save_snapshot, scan_readouts, select_candidates, validate_annotations, validate_freeze, validate_protocol,
)


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def cfg():
    return json.loads((ROOT / "configs/identity_budget_v2.json").read_text())


@pytest.fixture
def ann():
    return json.loads((ROOT / "annotations/room2/targets.ai-v2.1.json").read_text())


def state(tmp_path):
    members = [[[i, 0], [i, 1]] if i % 2 else [[i, 0]] for i in range(110)]
    clouds = [np.full((i % 3 + 1, 3), i, dtype=float) for i in range(110)]
    path = tmp_path / "complete.npz"
    save_snapshot(path, clouds, np.ones((110, 2)), members, [len(m) for m in members])
    return path, load_snapshot(path)


def test_snapshot_keeps_support_one_and_provenance_and_refuses_overwrite(tmp_path):
    path, saved = state(tmp_path)
    assert len(saved["ids"]) == 110
    assert sum(saved["supports"] == 1) == 55
    assert saved["members"][0] == [[0, 0]]
    with pytest.raises(ValueError):
        saved["clouds"][0][0, 0] = 99
    with pytest.raises(FileExistsError):
        save_snapshot(path, saved["clouds"], saved["features"], saved["members"], saved["supports"])


def test_snapshot_rejects_false_support(tmp_path):
    with pytest.raises(ValueError, match="supports"):
        save_snapshot(tmp_path / "bad.npz", [np.ones((1, 3))], np.ones((1, 2)), [[[0, 0]]], [3])


def test_id_depends_on_contributors_not_container_order():
    assert object_id([[4, 1], [2, 0]]) == object_id([[2, 0], [4, 1]])
    assert object_id([[4, 1]]) != object_id([[4, 2]])


def test_budget_order_is_label_free_and_invariant_to_map_permutation(tmp_path):
    _, saved = state(tmp_path)
    chosen = select_candidates(saved, 1, 25)
    reverse = np.arange(109, -1, -1)
    permuted = {"ids": saved["ids"][reverse], "supports": saved["supports"][reverse],
                "clouds": [saved["clouds"][i] for i in reverse]}
    assert saved["ids"][chosen].tolist() == permuted["ids"][select_candidates(permuted, 1, 25)].tolist()
    assert all(saved["supports"][i] == 2 for i in chosen)


def test_scans_do_not_change_state_or_snapshot_and_empty_candidates_are_valid(tmp_path, cfg):
    path, saved = state(tmp_path)
    before = path.read_bytes()
    matrix = np.ones((110, 1), dtype=bool)
    cache = {"qualifying": matrix, "mix_support": matrix, "coverage": matrix.astype(float),
             "scores": np.ones((1, 110)), "eligible": [(0, {"id": "vase", "query": "vase"})]}
    values = scan_readouts(saved, cache, cfg)
    assert len(values) == 12
    assert values[0]["actual_candidates"] == 25
    assert values[3]["actual_candidates"] == 110
    assert values[8]["actual_candidates"] == 0
    assert values[8]["instance_recovery"] == 0
    assert path.read_bytes() == before
    assert len(saved["ids"]) == 110
    assert readout(saved, cache, 1, 25) == values[0]


def test_category_query_accepts_any_annotated_same_class_but_identity_stays_separate(tmp_path):
    _, saved = state(tmp_path)
    qualifying = np.zeros((110, 2), dtype=bool)
    selected = select_candidates(saved, 1, 25)
    qualifying[selected[0], 1] = True
    cache = {"qualifying": qualifying, "mix_support": qualifying,
             "coverage": qualifying.astype(float), "scores": np.ones((2, 110)),
             "eligible": [(0, {"id": "vase-A", "query": "vase"}), (1, {"id": "vase-B", "query": "vase"})]}
    result = readout(saved, cache, 1, 25)
    assert result["instance_recovery"] == .5
    assert result["category_query_hit"] == 1
    assert result["category_queries"][0]["matched_physical_ids"] == ["vase-B"]
    assert result["unknown_candidates_are_false_positives"] is False


def test_fixed_geometry_rebuild_retains_original_members_support_and_semantics():
    original = [{"members": [[0, 2]], "num_detections": 1, "clip_ft": np.array([1., 2.]),
                 "text_ft": np.array([3., 4.]), "xyz": np.array([.3, 0, 0])}]
    rebuilt = copy.deepcopy(original)
    rebuilt[0].update(clip_ft=np.zeros(2), text_ft=np.zeros(2), xyz=np.zeros(3))
    restore_fixed_semantics(rebuilt, original, lambda o: o["members"])
    np.testing.assert_array_equal(rebuilt[0]["clip_ft"], original[0]["clip_ft"])
    np.testing.assert_array_equal(rebuilt[0]["text_ft"], original[0]["text_ft"])
    assert rebuilt[0]["xyz"][0] == 0 and original[0]["xyz"][0] == .3
    rebuilt[0]["members"] = [[1, 2]]
    with pytest.raises(ValueError, match="memberships"):
        restore_fixed_semantics(rebuilt, original, lambda o: o["members"])


def test_zero_geometry_control_is_exact_and_changed_support_is_rejected():
    original = [{"members": [[0, 2]], "num_detections": 1, "clip_ft": np.array([1., 2.]),
                 "text_ft": np.array([3., 4.]), "xyz": np.zeros(3)}]
    rebuilt = restore_fixed_semantics(copy.deepcopy(original), original, lambda o: o["members"])
    for key in ("xyz", "clip_ft", "text_ft"):
        np.testing.assert_array_equal(original[0][key], rebuilt[0][key])
    rebuilt[0]["num_detections"] = 2
    with pytest.raises(ValueError, match="support"):
        restore_fixed_semantics(rebuilt, original, lambda o: o["members"])


def test_review_and_exploratory_modes_cannot_silently_substitute(cfg, ann):
    validate_annotations(cfg, ann, require_review=False)
    with pytest.raises(ValueError, match="human annotation review pending"):
        validate_annotations(cfg, ann)
    exploratory = json.loads((ROOT / "configs/identity_budget_v2_exploratory.json").read_text())
    validate_annotations(exploratory, ann, require_review=False, exploratory=True)
    with pytest.raises(ValueError, match="requires_human_review"):
        validate_protocol(exploratory)
    ann["human_reviewed"] = True
    with pytest.raises(ValueError, match="must not claim"):
        validate_annotations(exploratory, ann, require_review=False, exploratory=True)


@pytest.mark.parametrize("change", ["duplicate_id", "out_of_bounds", "missing_visibility", "fewer_than_four"])
def test_annotation_inconsistencies_rejected(cfg, ann, change):
    if change == "duplicate_id":
        ann["instances"][1]["id"] = ann["instances"][0]["id"]
    elif change == "out_of_bounds":
        ann["instances"][0]["views"][0]["polygon"][0] = [1200, 0]
    elif change == "missing_visibility":
        ann["instances"][0]["visibility"].pop("62")
    else:
        ann["instances"] = ann["instances"][:3]
    with pytest.raises(ValueError):
        validate_annotations(cfg, ann, require_review=False)


def test_mismatched_freeze_rejected_before_native_import(tmp_path, cfg, ann):
    config = tmp_path / "protocol.json"
    annotation = tmp_path / "annotations.json"
    freeze = tmp_path / "freeze.json"
    config.write_text(json.dumps(cfg))
    annotation.write_text(json.dumps(ann))
    freeze.write_text("{}")
    with pytest.raises(ValueError):
        validate_freeze(config, annotation, tmp_path, {})
    output = tmp_path / "attempt"
    process = subprocess.run([sys.executable, str(ROOT / "scripts/run_identity_budget.py"),
                              "--protocol", str(config), "--annotations", str(annotation),
                              "--freeze", str(freeze), "--data", str(tmp_path), "--frontend", str(tmp_path),
                              "--weights", str(tmp_path), "--output", str(output)], capture_output=True, text=True)
    assert process.returncode == 1
    record = json.loads((output / "record.json").read_text())
    assert record["status"] == "rejected_before_native_import" and record["cells"] == []
    assert "human annotation review pending" in record["error"]


def decision_rows(cfg, delta=.2):
    rows = []
    for rms in cfg["translation_rms_m"]:
        for support in cfg["support_minima"]:
            for cap in cfg["candidate_caps"]:
                for seed in cfg["seeds"]:
                    for arm in ARMS:
                        rows.append({"observation": 8, "rms_m": rms, "min_support": support,
                                     "candidate_cap": cap, "seed": seed, "arm": arm,
                                     "instance_recovery": .5 + (delta if arm == "oracle_replay" else 0),
                                     "category_query_hit": .5, "annotated_duplicate_excess": 0,
                                     "annotated_mixed_objects": 0})
    return rows


def test_decision_needs_two_finite_caps_and_rejects_incomplete_cells(cfg):
    rows = decision_rows(cfg)
    assert hypothesis_decision(rows, cfg)["status"] == "prototype_plan_eligible"
    assert hypothesis_decision(rows, cfg)["H1_validated"] is False
    for row in rows:
        if row["arm"] == "oracle_replay" and row["candidate_cap"] in (50, 100):
            row["instance_recovery"] = .5
    assert hypothesis_decision(rows, cfg)["status"] == "narrow_or_stop_H1"
    with pytest.raises(ValueError, match="Missing/duplicate"):
        hypothesis_decision(rows[:-5], cfg)


def test_simple_control_match_or_identity_error_blocks_hypothesis(cfg):
    rows = decision_rows(cfg, delta=.099)
    assert hypothesis_decision(rows, cfg)["status"] == "narrow_or_stop_H1"
    rows = decision_rows(cfg)
    for row in rows:
        if row["arm"] == "visibility_fixed":
            row["instance_recovery"] = .7
    assert hypothesis_decision(rows, cfg)["status"] == "narrow_or_stop_H1"
    rows = decision_rows(cfg)
    for row in rows:
        if row["arm"] == "oracle_replay":
            row["annotated_mixed_objects"] = 1
    assert hypothesis_decision(rows, cfg)["status"] == "narrow_or_stop_H1"


def test_foreign_gpu_process_blocks_before_other_work(monkeypatch):
    calls = []

    def run(command, **kwargs):
        calls.append(command)
        return SimpleNamespace(stdout="999999, another-window-python, 8000 MiB\n")
    monkeypatch.setattr(subprocess, "run", run)
    with pytest.raises(RuntimeError, match="Another GPU process"):
        check_resources()
    assert len(calls) == 1


def test_author_jobs_block_even_when_wsl_gpu_inventory_is_empty(monkeypatch):
    def run(command, **kwargs):
        return SimpleNamespace(stdout="" if command[0] == "nvidia-smi" else
                               " 632 /home/qzl/projects/SLAM_Author_Originals/envs/python generate_gsa_results.py\n")
    monkeypatch.setattr(subprocess, "run", run)
    with pytest.raises(RuntimeError, match="Other window"):
        check_resources()


def test_idle_resource_gate_is_read_only(monkeypatch):
    commands = []

    def run(command, **kwargs):
        commands.append(command)
        return SimpleNamespace(stdout=f"{os.getpid()}, self, 0 MiB\n" if command[0] == "nvidia-smi" else " PID ARGS\n")
    monkeypatch.setattr(subprocess, "run", run)
    assert check_resources()["no_other_compute_processes"]
    assert [c[0] for c in commands] == ["nvidia-smi", "ps"]


def test_exploratory_freeze_binds_every_raw_file_and_cannot_pose_as_human_review(tmp_path, ann):
    cfg = json.loads((ROOT / "configs/identity_budget_v2_exploratory.json").read_text())
    config, annotation = tmp_path / "protocol.json", tmp_path / "annotations.json"
    config.write_text(json.dumps(cfg))
    annotation.write_text(json.dumps(ann))
    names = [f"room2/results/{stem}{f:06d}.{ext}" for f in cfg["mapping_frames"] + cfg["reference_frames"]
             for stem, ext in (("frame", "jpg"), ("depth", "png"))] + ["room2/traj.full.txt", "room2/traj.txt"]
    files = []
    for name in names:
        p = tmp_path / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"fixture raw bytes")
        files.append({"path": name, "sha256": digest(p)})
    manifest = {"scene": "room2", "protocol_sha256": digest(config), "mapping_frames": cfg["mapping_frames"],
                "reference_frames": cfg["reference_frames"], "files": files}
    (tmp_path / "manifest.json").write_text(json.dumps(manifest))
    freeze = {"analysis_type": "ai_only_exploratory", "protocol_sha256": digest(config),
              "annotations_sha256": digest(annotation), "source_manifest_sha256": digest(tmp_path / "manifest.json")}
    validate_freeze(config, annotation, tmp_path, freeze, exploratory=True)
    with pytest.raises(ValueError):
        validate_freeze(config, annotation, tmp_path, freeze)
    (tmp_path / names[0]).write_bytes(b"changed")
    with pytest.raises(ValueError, match="source hash mismatch"):
        validate_freeze(config, annotation, tmp_path, freeze, exploratory=True)
