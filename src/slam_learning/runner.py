from __future__ import annotations

import importlib.util
import json
import subprocess
import shutil
import sys
import traceback
import uuid
import tempfile
from pathlib import Path

from .metrics import compare_paper, score_map
from .pcd import read_pcd
from .provenance import digest, environment, git_state, source_hashes, utc_now, write_json


class MissingRequirement(RuntimeError):
    pass


def execute(command: list[str], cwd: Path, log: Path, timeout: float) -> int:
    with log.open("w", encoding="utf-8") as f:
        result = subprocess.run(command, cwd=cwd, stdout=f, stderr=subprocess.STDOUT, timeout=timeout)
    if result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, command)
    return result.returncode


def validate_inputs(root: Path, method: str) -> dict:
    sequence = root / ".cache/datasets/00"
    provenance = sequence / "provenance.json"
    if not provenance.is_file():
        raise MissingRequirement("Verified dataset missing. Run: slam-study fetch")
    metadata = json.loads(provenance.read_text(encoding="utf-8"))
    spec = json.loads((root / "configs/dataset.json").read_text(encoding="utf-8"))
    if metadata["source"] != spec:
        raise ValueError("Dataset manifest differs from current configuration; refetch required")
    files = sorted(sequence.rglob("*.pcd"))
    if set(p.relative_to(sequence).as_posix() for p in files) != set(metadata["files"]):
        raise ValueError("Dataset file inventory changed")
    for p in files:
        if digest(p) != metadata["files"][p.relative_to(sequence).as_posix()]:
            raise ValueError(f"Dataset file changed: {p.name}")
    if len(list((sequence / "pcd").glob("*.pcd"))) != spec["frames"]:
        raise ValueError("Wrong frame count")
    if len(read_pcd(sequence / "gt_cloud.pcd").records) != spec["gt_points"]:
        raise ValueError("Wrong GT point count")
    upstreams = json.loads((root / "configs/upstreams.json").read_text(encoding="utf-8"))
    states = {}
    for name in {"dynamicmap", method}:
        checkout = root / ".cache/upstream" / name
        if not checkout.is_dir():
            raise MissingRequirement(f"Missing pinned upstream {name}. Run: slam-study fetch")
        state = git_state(checkout)
        if state["commit"] != upstreams[name]["commit"] or state["dirty"]:
            raise ValueError(f"Upstream {name} is not at clean pinned commit")
        states[name] = {**upstreams[name], **state}
    deps = ("dufomap",) if method == "dufomap" else ("open3d", "fire", "dztimer", "tqdm")
    for name in deps:
        if importlib.util.find_spec(name) is None:
            raise MissingRequirement(f"Missing dependency {name}. Install .[methods]")
    expected = {"dufomap": "1.1.1"} if method == "dufomap" else {"open3d": "0.18.0", "dztimer": "1.1.1"}
    env = environment()
    if any(env["packages"][k] != v for k, v in expected.items()):
        raise ValueError(f"Method package versions differ from pinned environment: {expected}")
    return {"dataset": {"manifest_sha256": digest(provenance), "archive_sha256": metadata["archive_sha256"],
                        "configuration": spec}, "upstreams": states}


def run_method(root: Path, method: str, frames: int = 0, timeout: float = 3600) -> Path:
    if frames < 0 or timeout <= 0:
        raise ValueError("Frames must be nonnegative and timeout positive")
    specifications = json.loads((root / "configs/methods.json").read_text(encoding="utf-8"))
    if method not in specifications:
        raise ValueError(f"Unknown method {method}")
    spec = specifications[method]
    output = root / "results/runs" / f"{method}-{uuid.uuid4().hex[:12]}"
    output.mkdir(parents=True)
    record = {"schema_version": 1, "kind": "author_method", "method": method, "status": "running",
              "started_at": utc_now(), "scope": "smoke" if frames else "full_teaser",
              "requested_frames": frames, "specification": spec, "environment": environment(),
              "repository": git_state(root), "source_sha256": source_hashes(root),
              "config_sha256": {p.name: digest(p) for p in sorted((root / "configs").glob("*.json"))},
              "artifacts": {}, "command": [], "exit_code": None}
    write_json(output / "record.json", record)
    try:
        record.update(validate_inputs(root, method))
        command = [sys.executable, "-m", "slam_learning.cli", "_worker", "--root", str(root),
                   "--method", method, "--output", str(output), "--frames", str(frames)]
        record["command"] = command
        print(f"Running {method}; log: {output / 'run.log'}", flush=True)
        record["exit_code"] = execute(command, output, output / "run.log", timeout)
        worker = json.loads((output / "worker.json").read_text(encoding="utf-8"))
        if worker["frames"] != (min(frames, 141) if frames else 141):
            raise ValueError("Worker did not process the requested frames")
        record["worker"] = worker
        if frames:
            record["status"] = "smoke_passed"
            record["paper_comparison"] = None
        else:
            metrics = score_map(root / ".cache/datasets/00/gt_cloud.pcd", output / "cleaned.pcd")
            write_json(output / "metrics.json", metrics)
            record["metrics"] = metrics
            record["paper_comparison"] = compare_paper(metrics, spec["paper_target"])
            # Execution success and table agreement are independent facts.
            record["status"] = "executed"
    except MissingRequirement as e:
        record.update(status="blocked", error=str(e))
    except Exception as e:
        if isinstance(e, subprocess.CalledProcessError):
            record["exit_code"] = e.returncode
        record.update(status="failed", error=f"{type(e).__name__}: {e}", traceback=traceback.format_exc())
    finally:
        record["finished_at"] = utc_now()
        for name in ("cleaned.pcd", "run.log", "worker.json", "metrics.json", "compatibility.patch"):
            path = output / name
            if path.is_file():
                record["artifacts"][name] = {"sha256": digest(path), "bytes": path.stat().st_size,
                                            "availability": "local_only" if name == "cleaned.pcd" else "portable"}
        write_json(output / "record.json", record)
    print(f"{method}: {record['status']}; record: {output / 'record.json'}", flush=True)
    return output / "record.json"


def verify_record(path: Path, full: bool = False) -> list[str]:
    record = json.loads(path.read_text(encoding="utf-8"))
    errors = []
    if record.get("schema_version") != 1:
        errors.append("Unsupported schema")
    if record.get("status") in ("executed", "smoke_passed") and record.get("kind") == "author_method":
        if record.get("exit_code") != 0 or not record.get("command") or not record.get("dataset"):
            errors.append("Successful author run lacks command, zero exit code, or dataset evidence")
        if not {"cleaned.pcd", "run.log", "worker.json"}.issubset(record.get("artifacts", {})):
            errors.append("Successful author run lacks output/log hashes")
        if record["status"] == "executed":
            try:
                comparison = compare_paper(record["metrics"], record["specification"]["paper_target"])
                if record.get("paper_comparison") != comparison or record.get("scope") != "full_teaser":
                    errors.append("Paper comparison or full-run scope inconsistent")
                saved = path.parent / "metrics.json"
                if saved.is_file() and json.loads(saved.read_text(encoding="utf-8")) != record["metrics"]:
                    errors.append("Record metrics differ from the measured metrics artifact")
            except (KeyError, TypeError, ValueError):
                errors.append("Invalid author metrics/comparison")
        worker = path.parent / "worker.json"
        if worker.is_file() and json.loads(worker.read_text(encoding="utf-8")) != record.get("worker"):
            errors.append("Worker artifact differs from the run record")
    for name, artifact in record.get("artifacts", {}).items():
        target = (path.parent / name).resolve()
        if not target.is_relative_to(path.parent.resolve()):
            errors.append(f"Artifact escapes run directory: {name}")
        elif target.is_file():
            if digest(target) != artifact["sha256"]:
                errors.append(f"Artifact modified: {name}")
        elif full or artifact["availability"] != "local_only":
            errors.append(f"Artifact missing: {name}")
    return errors


def export_record(path: Path, destination: Path) -> None:
    errors = verify_record(path, full=True)
    if errors:
        raise ValueError("Cannot export invalid run: " + "; ".join(errors))
    if destination.exists():
        raise ValueError("Reference destination exists; choose a new name to preserve earlier evidence")
    destination.parent.mkdir(parents=True, exist_ok=True)
    record = json.loads(path.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory(prefix=".export-", dir=destination.parent) as temporary:
        staged = Path(temporary) / "record"
        staged.mkdir()
        shutil.copy2(path, staged / "record.json")
        for name, artifact in record["artifacts"].items():
            if artifact["availability"] == "portable":
                target = staged / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path.parent / name, target)
        staged.rename(destination)
