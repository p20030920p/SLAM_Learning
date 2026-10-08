"""Execute isolated, recorded v2 phases after other-window resources become idle.

This is one bounded experiment process, not a recurring job. It never changes Git,
installs packages, stops other jobs, or writes to shared caches/environments.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from slam_learning.identity_budget import check_resources, digest


def git_read_command(repo):
    metadata = repo / ".git"
    if sys.platform == "linux" and metadata.is_file():
        match = re.fullmatch(r"gitdir: ([A-Za-z]):[/\\](.+)\s*", metadata.read_text().strip())
        if match:
            drive, suffix = match.groups()
            gitdir = f"/mnt/{drive.lower()}/{suffix.replace(chr(92), '/')}"
            return ["git", f"--git-dir={gitdir}", f"--work-tree={repo}"]
    return ["git", "-C", str(repo)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("repo", "semantic-python", "protocol", "annotations", "data", "freeze", "native-source",
                 "weights", "output", "recordings"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    parser.add_argument("--wait-idle-seconds", type=int, default=5400)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    args.recordings.mkdir(parents=True, exist_ok=False)
    original_repo = args.repo
    source_snapshot = args.output / "source"
    source_snapshot.mkdir()
    for folder in ("src", "scripts", "configs", "annotations/room2"):
        shutil.copytree(args.repo / folder, source_snapshot / folder,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    git = git_read_command(args.repo)
    revision = subprocess.check_output([*git, "rev-parse", "HEAD"], text=True).strip()
    dirty = bool(subprocess.check_output([*git, "status", "--porcelain"], text=True).strip())
    args.repo = source_snapshot
    record = {"kind": "identity_budget_v2_pipeline", "analysis_type": "ai_only_exploratory",
              "status": "waiting_for_resources", "started_at": datetime.now(timezone.utc).isoformat(),
              "repo": str(original_repo), "executed_source": str(source_snapshot), "source_revision": revision,
              "source_was_dirty": dirty,
              "source_hashes": {p.relative_to(source_snapshot).as_posix(): digest(p)
                                for p in source_snapshot.rglob("*") if p.is_file()},
              "freeze_sha256": digest(args.freeze), "phases": [], "resource_checks": []}
    path = args.output / "pipeline.json"

    def save():
        path.write_text(json.dumps(record, indent=2) + "\n")

    def wait_idle():
        deadline = time.monotonic() + args.wait_idle_seconds
        while True:
            try:
                check = {"status": "idle", **check_resources()}
            except (OSError, RuntimeError, subprocess.SubprocessError) as error:
                check = {"status": "defer", "reason": str(error)}
            check["checked_at"] = datetime.now(timezone.utc).isoformat()
            record["resource_checks"].append(check)
            save()
            if check["status"] == "idle":
                return
            if time.monotonic() >= deadline:
                raise TimeoutError("Resource wait expired; other window left untouched")
            if len(record["resource_checks"]) == 1:
                print("Other window is busy; this experiment is waiting without GPU use", flush=True)
            time.sleep(min(30, max(0, deadline - time.monotonic())))

    def execute(name, command, recorded=False):
        wait_idle()
        phase = {"name": name, "command": command, "status": "running",
                 "started_at": datetime.now(timezone.utc).isoformat()}
        record["phases"].append(phase)
        record["status"] = "running"
        save()
        if recorded:
            command = [sys.executable, str(args.repo / "scripts/record_session.py"),
                       "--output", str(args.recordings / name), "--cwd", str(args.repo),
                       "--watch-root", str(args.output / name), "--", *command]
        started = time.monotonic()
        with (args.output / f"{name}.log").open("w") as log:
            result = subprocess.run(command, cwd=args.repo, stdout=log, stderr=subprocess.STDOUT)
        phase.update(status="executed" if result.returncode == 0 else "failed", exit_code=result.returncode,
                     elapsed_seconds=time.monotonic() - started,
                     finished_at=datetime.now(timezone.utc).isoformat())
        save()
        print(f"{name}: {phase['status']}; log {args.output / (name + '.log')}", flush=True)
        if result.returncode:
            raise RuntimeError(f"Phase failed; retained evidence: {name}")

    try:
        protocol = args.repo / args.protocol.relative_to(original_repo)
        annotations = args.repo / args.annotations.relative_to(original_repo)
        common = ["--protocol", str(protocol), "--annotations", str(annotations), "--data", str(args.data),
                  "--freeze", str(args.freeze), "--weights", str(args.weights), "--exploratory"]
        execute("frontend", [str(args.semantic_python), str(args.repo / "scripts/prepare_delayed_frontend.py"),
                             *common, "--native-source", str(args.native_source),
                             "--output", str(args.output / "frontend")], recorded=True)
        execute("mapping", [str(args.semantic_python), str(args.repo / "scripts/run_identity_budget.py"),
                            *common, "--frontend", str(args.output / "frontend"),
                            "--output", str(args.output / "mapping")], recorded=True)
        execute("analysis", [sys.executable, str(args.repo / "scripts/analyze_identity_budget.py"),
                             "--run", str(args.output / "mapping"), "--data", str(args.data),
                             "--output", str(args.output / "analysis")])
        execute("report", [sys.executable, str(args.repo / "scripts/summarize_identity_budget.py"),
                           "--analysis", str(args.output / "analysis"), "--output", str(args.output / "report")])
        execute("prepare-3d", [sys.executable, str(args.repo / "scripts/prepare_identity_3d.py"),
                               "--run", str(args.output / "mapping"), "--data", str(args.data),
                               "--output", str(args.output / "view-3d")])
        execute("saved-map-rviz", ["bash", str(args.repo / "scripts/record_visual_review.sh"),
                                   str(args.output / "view-3d/manifest.json")], recorded=True)
        record["status"] = "executed"
    except Exception as error:
        record.update(status="failed", error=str(error))
    finally:
        record["finished_at"] = datetime.now(timezone.utc).isoformat()
        save()
    return int(record["status"] != "executed")


if __name__ == "__main__":
    raise SystemExit(main())
