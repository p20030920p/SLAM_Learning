"""Freeze Practice inputs and package genuine held-out localization recordings."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

import numpy as np
from scipy.spatial.transform import Rotation, Slerp

from package_session import gif, probe, windows_path

ROOT = Path(__file__).resolve().parents[3]
SUITE = ROOT / "results/reference/practice-frozen-20261016"
PLANS = {
    "3d-static": ("robot-3d-static", "static", "3D"),
    "3d-dynamic": ("robot-3d-dynamic", "dynamic", "3D"),
    "3d-corridor": ("robot-3d-corridor", "degradation", "3D"),
    "3d-change": ("robot-3d-large-change", "large-change", "3D"),
    "srrg-change": ("srrg-2d-large-change", "large-change", "2D"),
}


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def prepare(key):
    original, scene, dimension = PLANS[key]
    source = ROOT / "results/reference" / original
    record = read(source / "record.json")
    if dimension == "3D":
        cases = read(source / "cases.json")
        maps = windows_path(cases["raw"]["map_yaml"]).parent.parent
        files = [maps / method / name for method in ("raw", "dufomap", "beautymap")
                 for name in ("map.yaml", "map.pgm", "map-3d.pcd", "points.npy")]
        for method in ("raw", "dufomap", "beautymap"):
            assert sha(maps / method / "map-3d.pcd") == record["case_maps"][method]["pcd_sha256"]
        marker_scene = "static" if scene == "large-change" else "corridor" if scene == "degradation" else scene
        marker = "maps-" + marker_scene + "-latest.json"
        selected = ("raw", "dufomap", "beautymap")
        map_source = maps
    else:
        maps = source / "maps"
        files = [maps / method / name for method in ("raw", "srrg") for name in ("map.yaml", "map.pgm")]
        marker = "mapping-srrg-static-latest.json"
        selected = ("raw", "srrg")
        map_source = source
    output = SUITE / key
    output.mkdir(parents=True, exist_ok=True)
    snapshot = {str(path): sha(path) for path in files}
    frozen = output / "frozen-inputs.json"
    if frozen.exists():
        assert read(frozen)["map_sha256"] == snapshot, "Previously frozen maps changed"
    else:
        write(frozen, {"source_A_or_prior_record": source.relative_to(ROOT).as_posix() + "/record.json",
                       "source_record_sha256": sha(source / "record.json"),
                       "dimension": dimension, "scene": scene, "methods": selected,
                       "scope": "Use the existing mapping A/prior; acquire fresh B; do not update maps in B",
                       "map_sha256": snapshot})
    linux_maps = "/mnt/" + map_source.drive[0].lower() + "/" + map_source.as_posix()[3:]
    write(ROOT / ".cache/presentation" / marker, {"path": linux_maps})
    print(json.dumps({"key": key, "scene": scene, "dimension": dimension, "frozen": str(frozen)}, ensure_ascii=False))


def score(run, names, dimension):
    metrics = read(run / "metrics.json")
    begin, end = metrics["recording_interval_sim_s"]
    grid = np.arange(begin + 5.0, end, 0.1)
    truth = [json.loads(line) for line in (run / "truth.jsonl").read_text().splitlines()]
    times = np.array([row["stamp_s"] for row in truth])
    times, unique = np.unique(times, return_index=True)
    xyz = np.array([row["xyz"] for row in truth])[unique]
    rotations = Rotation.from_quat(np.array([row["xyzw"] for row in truth])[unique])
    assert len(grid) and grid[0] >= times[0] and grid[-1] <= times[-1]
    target = np.column_stack([np.interp(grid, times, xyz[:, i]) for i in range(3)])
    target_rotation = Slerp(times, rotations)(grid)
    validity, errors, counts = {}, {}, {}
    for name in names:
        suffix = "-poses3d.csv" if dimension == "3D" else "-samples.csv"
        columns = ["stamp_s", "estimate_x", "estimate_y"]
        columns += ["estimate_z", "estimate_qx", "estimate_qy", "estimate_qz", "estimate_qw"] if dimension == "3D" else ["estimate_yaw"]
        with (run / (name + suffix)).open() as stream:
            rows = list(csv.DictReader(stream))
        a = np.array([[float(row[column]) for column in columns] for row in rows])
        if not len(a):
            validity[name] = np.zeros(len(grid), dtype=bool)
            errors[name] = (np.full(len(grid), np.nan), np.full(len(grid), np.nan))
            counts[name] = {"native_rows": 0, "invalid_rows": 0}
            continue
        finite = np.isfinite(a).all(axis=1)
        if dimension == "3D":
            finite &= np.linalg.norm(a[:, 4:], axis=1) > .5
        counts[name] = {"native_rows": len(a), "invalid_rows": int((~finite).sum())}
        a = a[finite]
        a = a[np.argsort(a[:, 0], kind="stable")]
        assert len(a), name + " has no finite native poses"
        ids = np.searchsorted(a[:, 0], grid, side="right") - 1
        selected = a[np.maximum(ids, 0)]
        validity[name] = (ids >= 0) & (grid - selected[:, 0] <= .15)
        dimensions = 3 if dimension == "3D" else 2
        distance = np.linalg.norm(selected[:, 1:1 + dimensions] - target[:, :dimensions], axis=1)
        if dimension == "3D":
            angle = np.rad2deg((target_rotation.inv() * Rotation.from_quat(selected[:, 4:])).magnitude())
        else:
            target_yaw = target_rotation.as_euler("xyz")[:, 2]
            angle = np.rad2deg(np.arctan2(np.sin(selected[:, 3] - target_yaw), np.cos(selected[:, 3] - target_yaw)))
        errors[name] = distance, angle
    common = np.logical_and.reduce(list(validity.values()))
    methods = {}
    for name, (distance, angle) in errors.items():
        def rmse(value, mask):
            return float(np.sqrt(np.mean(value[mask] ** 2))) if mask.any() else None
        methods[name] = {**counts[name], "common_samples": int(common.sum()),
                         "position_rmse_m": rmse(distance, common), "rotation_rmse_deg": rmse(angle, common),
                         "fresh_grid_coverage": float(validity[name].mean()),
                         "own_valid_position_rmse_m": rmse(distance, validity[name])}
    return {"kind": "held_out_frozen_map_localization", "dimension": dimension,
            "scope": "Fresh B; native estimates; truth only for scoring; no trajectory alignment; 10 Hz after 5 s; latest pose age <= 0.15 s; common times across displayed controls",
            "expected_grid_samples": len(grid), "common_grid_samples": int(common.sum()),
            "recording_interval_sim_s": [begin, end], "methods": methods}


def finish(key, run):
    output = SUITE / key
    assert not (output / "record.json").exists(), "Evidence already sealed"
    frozen = read(output / "frozen-inputs.json")
    assert read(run / "session-stopped.json")["exit_code"] == 0
    assert read(run / "metrics.json")["status"] == "completed"
    assert read(run / "session.json")["flow"].startswith("localization-")
    for path, expected in frozen["map_sha256"].items():
        assert sha(Path(path)) == expected, "Frozen map changed in B: " + path
    cases = read(run / "cases.json")
    names = frozen["methods"]
    for name in names:
        for field in ("map_yaml", "map_pcd"):
            if field in cases[name]:
                path = windows_path(cases[name][field])
                assert str(path) in frozen["map_sha256"]
    for filename in ("session.json", "runtime.json", "cases.json", "metrics.json", "truth.jsonl",
                     "recording.started", "recording.stopped", "native-views.json", "views.json",
                     "scan-stress.jsonl", "cloud-stress.jsonl", "window-capture-heartbeat.jsonl", "view-updates.jsonl"):
        path = run / filename
        if path.exists():
            shutil.copyfile(path, output / filename)
    for pattern in ("*-samples.csv", "*-poses3d.csv", "view-*.rviz"):
        for path in run.glob(pattern):
            shutil.copyfile(path, output / path.name)
    shutil.copytree(run / "logs", output / "logs", dirs_exist_ok=True)
    scores = score(run, names, frozen["dimension"])
    write(output / "score.json", scores)
    (output / "executions").mkdir(exist_ok=True)
    timing = {}
    for name in names:
        video = run / "executions" / (name + ".mp4")
        target = output / "executions" / video.name
        shutil.copyfile(video, target)
        for extension in ("-filter.txt", "-capture.log", "-probe.json"):
            path = video.with_name(name + extension)
            if path.exists():
                shutil.copyfile(path, target.with_name(path.name))
        subprocess.run(["ffmpeg", "-v", "error", "-i", str(target), "-f", "null", "-"], check=True)
        timing[name] = gif(target, target.with_suffix(".gif"))
        duration = float(probe(target)["format"]["duration"])
        for label, fraction in (("first", .05), ("mid", .5), ("last", .95)):
            subprocess.run(["ffmpeg", "-v", "error", "-ss", str(duration * fraction), "-i", str(target),
                            "-frames:v", "1", "-y", str(target.with_name(name + "-" + label + ".png"))], check=True)
    map_processing = windows_path(cases[names[0]]["map_yaml"]).parent.parent / "record.json"
    shutil.copyfile(map_processing, output / "mapping-A-processing.json")
    record = {"schema_version": 1, "kind": "native_frozen_map_practice", "status": "executed", "exit_code": 0,
              "source_run": str(run), "frozen_maps_unchanged": True, "truth_input_to_localizers": False,
              "source_A_or_prior_record": frozen["source_A_or_prior_record"],
              "mapping_A_processing_record": str(map_processing), "mapping_A_processing_sha256": sha(map_processing),
              "score": scores, "timing": timing,
              "recorded_inputs": {str(path): {"sha256": sha(path), "bytes": path.stat().st_size, "availability": "local_only"}
                                  for path in (run / "input-bag").glob("*.mcap")},
              "artifacts": {path.relative_to(output).as_posix(): {"sha256": sha(path), "bytes": path.stat().st_size}
                            for path in output.rglob("*") if path.is_file() and path.name != "record.json"}}
    write(output / "record.json", record)
    print(json.dumps({"output": str(output), "score": scores}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "finish"))
    parser.add_argument("key", choices=PLANS)
    parser.add_argument("run", nargs="?", type=Path)
    args = parser.parse_args()
    prepare(args.key) if args.action == "prepare" else finish(args.key, args.run)
