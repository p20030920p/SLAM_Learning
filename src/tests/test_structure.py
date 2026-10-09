import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from slam_learning.core.provenance import source_hashes

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("script", [
    "experiments/run_paired_cell.py",
    "experiments/run_delayed_correction.py",
    "evidence/snapshot_cell_sources.py",
])
def test_grouped_script_entrypoints_work_outside_checkout(script, tmp_path):
    result = subprocess.run([sys.executable, str(ROOT / "src/scripts" / script), "--help"],
                            cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "usage:" in result.stdout.lower()


def test_cli_finds_checkout_from_nested_working_directory():
    result = subprocess.run(
        [sys.executable, "-m", "slam_learning.cli", "doctor"],
        cwd=ROOT / "src/slam_learning/core", capture_output=True, text=True, check=True,
    )
    assert Path(json.loads(result.stdout)["root"]) == ROOT


def test_cli_verifies_evidence_from_outside_checkout(tmp_path):
    checkout = tmp_path / "checkout"
    (checkout / "src/configs").mkdir(parents=True)
    (checkout / "src/configs/methods.json").write_text("{}", encoding="utf-8")
    artifact = checkout / "run.log"
    artifact.write_bytes(b"preserved measurement\n")
    record = checkout / "record.json"
    record.write_text(json.dumps({
        "schema_version": 1, "kind": "mechanism", "status": "executed",
        "artifacts": {"run.log": {
            "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(), "availability": "portable",
        }},
    }), encoding="utf-8")
    command = [sys.executable, "-m", "slam_learning.cli", "verify", "record.json", "--root", str(checkout)]
    valid = subprocess.run(command, cwd=tmp_path, capture_output=True, text=True)
    assert valid.returncode == 0, valid.stderr
    artifact.write_bytes(b"changed measurement\n")
    invalid = subprocess.run(command, cwd=tmp_path, capture_output=True, text=True)
    assert invalid.returncode == 1
    assert "Artifact modified: run.log" in invalid.stdout


def test_source_hashes_exclude_installed_environments(tmp_path):
    for name in ("slam_learning/core.py", "scripts/task.py", ".venv/Lib/site-packages/external.py",
                 "build/lib/stale.py"):
        path = tmp_path / "src" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# fixture\n", encoding="utf-8")
    assert set(source_hashes(tmp_path)) == {"src/slam_learning/core.py", "src/scripts/task.py"}


def test_preflight_failure_still_records_moved_configuration(tmp_path, monkeypatch):
    from slam_learning.runtime import runner
    config = tmp_path / "src/configs/methods.json"
    config.parent.mkdir(parents=True)
    config.write_text(json.dumps({"fixture": {}}), encoding="utf-8")

    def unavailable(root, method):
        raise runner.MissingRequirement("fixture inputs unavailable")

    monkeypatch.setattr(runner, "validate_inputs", unavailable)
    monkeypatch.setattr(runner, "git_state", lambda root: {"commit": None, "dirty": None})
    record = json.loads(runner.run_method(tmp_path, "fixture").read_text(encoding="utf-8"))
    assert record["status"] == "blocked"
    assert record["config_sha256"] == {"methods.json": hashlib.sha256(config.read_bytes()).hexdigest()}
