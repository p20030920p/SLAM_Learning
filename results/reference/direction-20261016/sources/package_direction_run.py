"""Package completed native recordings and score the same 10Hz truth grid."""

import argparse
import csv
import hashlib
import json
from pathlib import Path
import shutil

import numpy as np

from package_session import gif

ROOT = Path(__file__).resolve().parents[3]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def package(run, output):
    report = json.loads((run / "metrics.json").read_text())
    assert report["status"] == "completed"
    assert json.loads((run / "session-stopped.json").read_text())["exit_code"] == 0
    assert not (output / "record.json").exists(), "Refuse to replace sealed evidence"
    output.mkdir(parents=True, exist_ok=True)
    names = [
        "session.json",
        "runtime.json",
        "cases.json",
        "metrics.json",
        "truth.jsonl",
        "scan-stress.jsonl",
        "native-views.json",
        "fastlio.yaml",
        "rolling-scans.jsonl",
        "imu.jsonl",
        "fastlio-transport-finished.json",
        "fastlio-deskew.jsonl",
        "fastlio-no_deskew.jsonl",
        "fastlio-deskew-clouds.npz",
        "fastlio-no_deskew-clouds.npz",
        "fastlio-imu.urdf",
        "fastlio-bridge.yaml",
        "fastlio-world.sdf",
        "landmark-corridor.world",
        "timing.json",
    ]
    for name in names:
        p = run / name
        if p.is_file():
            shutil.copyfile(p, output / name)
    for p in run.glob("*-samples.csv"):
        shutil.copyfile(p, output / p.name)
    for p in run.glob("*-poses3d.csv"):
        shutil.copyfile(p, output / p.name)
    for p in run.glob("*views.json"):
        shutil.copyfile(p, output / p.name)
    (output / "logs").mkdir(exist_ok=True)
    for p in (run / "logs").glob("*.log"):
        if p.stat().st_size < 8_000_000:
            shutil.copyfile(p, output / "logs" / p.name)
    metrics = {}
    cases = json.loads((run / "cases.json").read_text())
    start, end = report["recording_interval_sim_s"]
    grid = np.arange(start + 5, end, 0.1)
    for name, case in cases.items():
        text = case["map_yaml"].replace("\\", "/")
        source = Path(text[5].upper() + ":/" + text[7:]) if text.startswith("/mnt/") else Path(text)
        dest = output / "maps" / name
        dest.mkdir(parents=True, exist_ok=True)
        for item in ("map.pgm", "map.yaml"):
            shutil.copyfile(source.parent / item, dest / item)
        with (run / f"{name}-samples.csv").open() as f:
            rows = list(csv.DictReader(f))
        a = np.array([[float(v) for v in row.values()] for row in rows])
        ids = np.searchsorted(a[:, 0], grid, side="right") - 1
        valid = (ids >= 0) & (grid - a[np.maximum(ids, 0), 0] <= 0.15)
        selected = a[ids[valid]]
        e = selected[:, 7]
        angle = np.abs(selected[:, 8])
        metrics[name] = {
            "position_rmse_m": float(np.sqrt(np.mean(e**2))),
            "position_p95_m": float(np.percentile(e, 95)),
            "yaw_rmse_deg": float(np.rad2deg(np.sqrt(np.mean(angle**2)))),
            "grid_coverage": float(np.mean(valid)),
            "success_fraction": float(np.sum((e < 0.25) & (angle < np.deg2rad(10))) / len(grid)),
            "grid_samples": int(valid.sum()),
            "grid_expected": len(grid),
            "native_samples": len(rows),
        }
        for phase, mask in (("limited", grid[valid] < start + 50), ("restored", grid[valid] >= start + 50)):
            part = selected[mask]
            if len(part):
                metrics[name][phase] = {
                    "rmse_m": float(np.sqrt(np.mean(part[:, 7] ** 2))),
                    "samples": len(part),
                }
    media = run / "executions"
    if media.exists():
        (output / "executions").mkdir(exist_ok=True)
        for p in media.glob("*.mp4"):
            shutil.copyfile(p, output / "executions" / p.name)
    else:
        shutil.copyfile(run / "execution.mp4", output / "execution.mp4")
    timing = {}
    for p in output.rglob("*.mp4"):
        timing[p.relative_to(output).as_posix()] = gif(p, p.with_suffix(".gif"))
    record = {
        "schema_version": 1,
        "kind": "native_direction_experiment",
        "status": "executed",
        "exit_code": 0,
        "scope": "Native run and real application capture; pose metrics use evaluation-only truth, 10Hz grid, max pose age 0.15s, 5s warmup; no truth to localizers",
        "source_run": str(run),
        "source_session_sha256": sha(run / "session.json"),
        "metrics": metrics,
        "timing": timing,
        "input_bags": {
            p.name: {"sha256": sha(p), "bytes": p.stat().st_size, "availability": "local_only"}
            for p in (run / "input-bag").glob("*.mcap")
        },
        "artifacts": {
            p.relative_to(output).as_posix(): {
                "sha256": sha(p),
                "bytes": p.stat().st_size,
                "availability": "portable",
            }
            for p in output.rglob("*")
            if p.is_file()
        },
    }
    (output / "record.json").write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps({"output": str(output), "metrics": metrics}, indent=2))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("run", type=Path)
    p.add_argument("output", type=Path)
    a = p.parse_args()
    package(a.run, a.output)
