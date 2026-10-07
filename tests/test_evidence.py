import subprocess
import sys
import zipfile

import pytest

from slam_learning.fetch import safe_extract
from slam_learning.provenance import digest, write_json
from slam_learning.runner import execute, export_record, verify_record


def test_failed_process_cannot_reuse_a_stale_score(tmp_path):
    (tmp_path / "metrics.json").write_text('{"SA": 100}')
    with pytest.raises(subprocess.CalledProcessError):
        execute([sys.executable, "-c", "raise SystemExit(17)"], tmp_path, tmp_path / "run.log", 10)


def test_timeout_is_not_a_success(tmp_path):
    with pytest.raises(subprocess.TimeoutExpired):
        execute([sys.executable, "-c", "import time; time.sleep(10)"], tmp_path, tmp_path / "run.log", 0.2)


def test_changed_artifact_invalidates_evidence(tmp_path):
    artifact = tmp_path / "metrics.json"
    artifact.write_text("original")
    record = tmp_path / "record.json"
    write_json(record, {"schema_version": 1, "kind": "mechanism", "status": "executed", "artifacts": {
        "metrics.json": {"sha256": digest(artifact), "availability": "portable"}}})
    assert verify_record(record) == []
    artifact.write_text("modified")
    assert verify_record(record) == ["Artifact modified: metrics.json"]


def test_no_prefilled_done_status_without_evidence(tmp_path):
    record = tmp_path / "record.json"
    write_json(record, {"schema_version": 1, "kind": "author_method", "status": "smoke_passed", "artifacts": {}})
    assert verify_record(record)


def test_strict_json_rejects_nan(tmp_path):
    with pytest.raises(ValueError):
        write_json(tmp_path / "a.json", {"metric": float("nan")})


@pytest.mark.parametrize("name", ["../escape.txt", "/absolute.txt", "..\\escape.txt", "C:/escape.txt"])
def test_zip_cannot_escape_dataset_directory(tmp_path, name):
    archive = tmp_path / "test.zip"
    with zipfile.ZipFile(archive, "w") as z:
        z.writestr(name, "bad")
    with pytest.raises(ValueError):
        safe_extract(archive, tmp_path / "data")


def test_portable_export_keeps_hashes_and_does_not_overwrite(tmp_path):
    run = tmp_path / "run"
    run.mkdir()
    log = run / "run.log"
    log.write_text("measured")
    record = run / "record.json"
    write_json(record, {"schema_version": 1, "kind": "mechanism", "status": "executed", "artifacts": {
        "run.log": {"sha256": digest(log), "availability": "portable"}}})
    destination = tmp_path / "reference"
    export_record(record, destination)
    assert verify_record(destination / "record.json") == []
    with pytest.raises(ValueError, match="exists"):
        export_record(record, destination)
