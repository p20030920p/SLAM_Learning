"""Run a frozen ConceptGraphs frontend once, after the annotation seal."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--annotations", type=Path, required=True)
    parser.add_argument("--freeze", type=Path, required=True)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--native-source", type=Path, required=True)
    parser.add_argument("--weights", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    cfg = json.loads(args.protocol.read_text())
    seal = json.loads(args.freeze.read_text())
    for key, path in (("protocol_sha256", args.protocol), ("annotations_sha256", args.annotations),
                      ("source_manifest_sha256", args.data / "manifest.json")):
        if seal[key] != sha(path):
            raise ValueError(f"Frozen input changed: {path}")
    args.output.mkdir(parents=True, exist_ok=False)
    record = {"kind": "sealed_new_scene_frontend", "status": "running", "started_at": now(),
              "freeze_sha256": sha(args.freeze), "protocol_sha256": sha(args.protocol),
              "scene": cfg["scene"], "frames": cfg["mapping_frames"], "artifacts": {}}
    record_path = args.output / "record.json"

    def save():
        record_path.write_text(json.dumps(record, indent=2) + "\n")

    save()
    try:
        data_root = args.output / "input/Replica"
        target = data_root / cfg["scene"]
        (target / "results").mkdir(parents=True)
        for index in cfg["mapping_frames"]:
            for stem, suffix in (("frame", "jpg"), ("depth", "png")):
                name = f"{stem}{index:06d}.{suffix}"
                (target / "results" / name).symlink_to(args.data / cfg["scene"] / "results" / name)
        shutil.copy2(args.data / cfg["scene"] / "traj.txt", target / "traj.txt")
        work = args.output / "author-code"
        shutil.copytree(args.native_source / "author-code", work,
                        ignore=shutil.ignore_patterns("__pycache__", "assets", ".git"))
        script = work / "conceptgraph/scripts/generate_gsa_results.py"
        record["native_source_script_sha256"] = sha(args.native_source / "author-code" /
                                                   "conceptgraph/scripts/generate_gsa_results.py")
        record["runtime_script_sha256"] = sha(script)
        env = dict(os.environ, PYTHONPATH=str(work), MPLBACKEND="Agg", OMP_NUM_THREADS="4",
                   OPENBLAS_NUM_THREADS="4", PYTHONHASHSEED="7",
                   GSA_PATH=str(args.weights / "sam/checkpoints"), SLAM_STUDY_SAM_BATCH="36",
                   SLAM_STUDY_CLIP_CHECKPOINT=str(args.weights / "clip/open_clip_pytorch_model.bin"))
        command = [sys.executable, str(script), "--dataset_root", str(data_root),
                   "--dataset_config", str(work / "conceptgraph/dataset/dataconfigs/replica/replica.yaml"),
                   "--scene_id", cfg["scene"], "--class_set", "none", "--stride", "1"]
        record["command"] = command
        save()
        start = time.monotonic()
        print("New-scene SAM/CLIP begins only after independent-reference seal", flush=True)
        with (args.output / "frontend.log").open("w") as log:
            subprocess.run(command, cwd=work / "conceptgraph", env=env, stdout=log,
                           stderr=subprocess.STDOUT, check=True, timeout=3600)
        record["elapsed_seconds"] = time.monotonic() - start
        detections = sorted((target / "gsa_detections_none").glob("*.pkl.gz"))
        if len(detections) != len(cfg["mapping_frames"]):
            raise ValueError("Incomplete frozen frontend")
        for path in detections:
            record["artifacts"][path.relative_to(args.output).as_posix()] = {
                "sha256": sha(path), "bytes": path.stat().st_size, "availability": "local_only"}
        record.update(status="executed", exit_code=0)
    except Exception as error:
        record.update(status="failed", error=str(error), traceback=traceback.format_exc())
    finally:
        record["finished_at"] = now()
        save()
    print(f"Frontend {record['status']}: {record_path}", flush=True)
    return int(record["status"] != "executed")


if __name__ == "__main__":
    raise SystemExit(main())
