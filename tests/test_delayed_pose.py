import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from slam_learning.core.delayed_pose import prefix_errors


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


def test_mismatched_followup_fails_before_cuda_and_archives_failure(tmp_path):
    root = tmp_path / "root"
    inputs = {"configs/delayed_pose.json": {"id": "fixture"}, "configs/semantic.json": {},
              "annotations/room1/targets.json": {}, "data/manifest.json": {}}
    for name, data in inputs.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data))
    metrics = root / "src/slam_learning/core/delayed_pose.py"
    metrics.parent.mkdir(parents=True)
    metrics.write_text("# This failure must not execute any mapper or CUDA code\n")
    seal = {key: hashlib.sha256((root / name).read_bytes()).hexdigest() for key, name in (
        ("protocol_sha256", "configs/delayed_pose.json"), ("annotations_sha256", "annotations/room1/targets.json"),
        ("source_manifest_sha256", "data/manifest.json"))}
    freeze = root / "freeze.json"
    freeze.write_text(json.dumps(seal))
    frontend = root / "frontend"
    frontend.mkdir()
    (frontend / "record.json").write_text(json.dumps({"status": "executed", "artifacts": {},
        "freeze_sha256": hashlib.sha256(freeze.read_bytes()).hexdigest()}))
    parent = root / "primary"
    parent.mkdir()
    parent_record = parent / "record.json"
    parent_record.write_text(json.dumps({"status": "executed", "gates": {
        str(i): {"passed": True} for i in range(7)}, "configuration": inputs["configs/delayed_pose.json"],
        "freeze_sha256": "a different study"}))
    before = parent_record.read_bytes()
    output = root / "followup"
    script = Path(__file__).resolve().parents[1] / "scripts/run_delayed_correction.py"
    result = subprocess.run([sys.executable, str(script), "--root", str(root), "--data", str(root / "data"),
        "--freeze", str(freeze), "--frontend", str(frontend), "--weights", str(root / "weights"),
        "--output", str(output), "--support-control-from", str(parent)], capture_output=True, text=True)
    record = json.loads((output / "record.json").read_text())
    assert result.returncode == 1
    assert record["status"] == "failed"
    assert record["kind"] == "posthoc_support_control"
    assert record["error"] == "Post-hoc control changed frozen primary inputs"
    assert record["cells"] == []
    assert parent_record.read_bytes() == before
