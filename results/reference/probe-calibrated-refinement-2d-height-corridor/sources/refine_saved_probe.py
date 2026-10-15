"""New offline inference on exactly the retained B inputs; video is a result replay."""
import argparse
import csv
import datetime
import hashlib
import json
import math
import shutil
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from slam_learning.core.provenance import digest
from slam_learning.runtime.poses3d import score_poses3d
from slam_learning.runtime.presentation_evidence import read_samples, restoration, score, validate_truth
from slam_learning.runtime.recovery_probe import SurfaceMap
from slam_learning.runtime.refined_probe import FineProbe, REFINEMENT
from slam_learning.runtime.runner import verify_record
from package_session import gif, probe, replay

ROOT = Path(__file__).resolve().parents[3]
PROTOCOL = ROOT / "results/analysis/hypotheses/refinement-protocol.json"
SOURCE = Path(__file__).resolve()


def freeze():
    if PROTOCOL.exists():
        raise ValueError("The refinement protocol is already frozen")
    sources = [ROOT / "src/slam_learning/runtime/refined_probe.py", ROOT / "src/slam_learning/runtime/recovery_probe.py"]
    data = {"frozen_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "parent_protocol_sha256": digest(PROTOCOL.with_name("calibrated-protocol.json" if PROTOCOL.name.startswith("calibrated-") else "protocol.json")),
            "hypothesis": "A 0.4m coarse grid plus weak-direction projection can leave a 0.2m offset. A 0.1m local candidate grid and checks against evaluated spatially distinct alternatives may remove it when visible height structure distinguishes position; a plain parallel corridor should remain ambiguous.",
            "settings": REFINEMENT,
            "conditions": [{"dimension": dimension, "scene": scene} for dimension in ("2d", "3d") for scene in ("corridor", "height-corridor")],
            "input_scope": "exact same saved lidar/depth/odometry arrays as the completed native B trial; no new Gazebo simulation",
            "truth_input": False, "video_scope": "measured output replay after new offline inference; no live-Gazebo or real-time claim",
            "controls": "retained coarse LiDAR Search and Depth + Search; new fine LiDAR and fine Depth, same H1/H2 and initial beliefs",
            "source_sha256": {path.name: digest(path) for path in sources}}
    PROTOCOL.write_text(json.dumps(data, indent=2) + "\n")
    print(f"Frozen: {PROTOCOL}")


def compute(parent, folder):
    # This phase has no truth/metrics/old-estimate reads. Only sensor inputs,
    # measured maps and the same supplied initial belief enter FineProbe.
    config = json.loads((parent / "probe-config.json").read_text())
    cases = json.loads((parent / "cases.json").read_text())
    frames = json.loads((parent / "probe-B-inputs.json").read_text())["frames"]
    inputs = np.load(parent / "probe-B-inputs.npz", allow_pickle=False)
    lidar_points = np.load(parent / "probe-maps/lidar.npy", allow_pickle=False).astype(float, copy=True)
    depth_points = np.load(parent / "probe-maps/depth.npy", allow_pickle=False).astype(float, copy=True)
    lidar_points[:, 2] -= config.get("ground_z_m", 0.)
    depth_points[:, 2] -= config.get("ground_z_m", 0.)
    lidar_map = SurfaceMap(lidar_points, 2 if config["dimension"] == "2d" else 3)
    depth_map = SurfaceMap(depth_points, 3)
    initial = cases["plain"]["initial_pose"]
    belief = [initial["x"], initial["y"], initial["yaw"]]
    methods = {"fine_lidar": FineProbe(belief, depth=False), "fine_depth": FineProbe(belief, depth=True)}
    estimates = {name: [] for name in methods}
    started = time.monotonic()
    with (folder / "inference.jsonl").open("w") as log:
        for frame in frames:
            key, stamp = f"frame_{frame['frame']:05d}", frame["stamp_s"]
            lidar, depth, odom = (inputs[key + suffix] for suffix in ("_lidar", "_depth", "_odom"))
            input_hash = hashlib.sha256(lidar.tobytes() + depth.tobytes() + odom.tobytes()).hexdigest()
            for name, estimator in methods.items():
                pose, info = estimator.update(stamp, odom, (lidar_map, lidar), (depth_map, depth) if len(depth) >= 12 else None)
                estimates[name].append([stamp, *pose.tolist()])
                log.write(json.dumps({"case": name, "frame": frame["frame"], "stamp_s": stamp,
                                      "input_sha256": input_hash, "pose": pose.tolist(), **info}) + "\n")
            if frame["frame"] % 60 == 0:
                print(f"OFFLINE NEW INFERENCE frame={frame['frame']} t={stamp:.1f}; truth is not an input", flush=True)
    np.savez_compressed(folder / "new-estimates.npz", **{name: np.array(rows) for name, rows in estimates.items()})
    return estimates, time.monotonic() - started


def evaluate(parent, folder, estimates, original, wall_seconds):
    truth = [json.loads(line) for line in (parent / "truth.jsonl").read_text().splitlines()]
    stamps = np.array([row["stamp_s"] for row in truth])
    dimension = original["hypothesis_probes"]["dimension"]
    ground_z = original["hypothesis_probes"].get("ground_z_m", 0.)
    shutil.copyfile(parent / "truth.jsonl", folder / "truth.jsonl")
    values, metrics3d, cases = {}, {}, {}
    parent_cases = json.loads((parent / "cases.json").read_text())
    fieldnames = ["stamp_s", "truth_x", "truth_y", "truth_yaw", "estimate_x", "estimate_y", "estimate_yaw",
                  "position_error_m", "yaw_error_rad", "nearest_truth_delta_s"]
    keys = ("x", "y", "z", "qx", "qy", "qz", "qw")
    for name, source_case in (("coarse_lidar", "search"), ("coarse_depth", "recover"),
                              ("fine_lidar", "search"), ("fine_depth", "recover")):
        cases[name] = {**parent_cases[source_case], "localizer": name.replace("_", " ") + " SE2 probe"}
        target_map = folder / "maps" / name
        target_map.mkdir(parents=True)
        for part in ("map.yaml", "map.pgm"):
            shutil.copyfile(parent / "maps" / source_case / part, target_map / part)
        sample_path = folder / f"{name}-samples.csv"
        pose_path = folder / f"{name}-poses3d.csv"
        if name.startswith("coarse"):
            shutil.copyfile(parent / f"{source_case}-samples.csv", sample_path)
            if dimension == "3d":
                shutil.copyfile(parent / f"{source_case}-poses3d.csv", pose_path)
        else:
            with sample_path.open("w", newline="") as stream, pose_path.open("w", newline="") as poses:
                writer, full = csv.writer(stream), csv.writer(poses)
                writer.writerow(fieldnames)
                full.writerow(["stamp_s", *["truth_" + key for key in keys], *["estimate_" + key for key in keys], "nearest_truth_delta_s"])
                for stamp, x, y, heading in estimates[name]:
                    index = int(np.argmin(abs(stamps - stamp)))
                    near, delta = truth[index], abs(stamps[index] - stamp)
                    if delta > .05:
                        continue
                    qx, qy, qz, qw = near["xyzw"]
                    actual_yaw = math.atan2(2 * (qw * qz + qx * qy), 1 - 2 * (qy * qy + qz * qz))
                    angle = math.atan2(math.sin(heading - actual_yaw), math.cos(heading - actual_yaw))
                    writer.writerow([stamp, *near["xyz"][:2], actual_yaw, x, y, heading,
                                     math.hypot(x - near["xyz"][0], y - near["xyz"][1]), angle, delta])
                    full.writerow([stamp, *near["xyz"], *near["xyzw"], x, y, ground_z, 0., 0., math.sin(heading / 2), math.cos(heading / 2), delta])
        values[name] = read_samples(sample_path)
        validate_truth(values[name], truth)
        if dimension == "3d":
            metrics3d[name] = score_poses3d(pose_path, truth)
    (folder / "cases.json").write_text(json.dumps(cases, indent=2) + "\n")
    metrics = {name: score(array) for name, array in values.items()}
    (folder / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    restore = original["restoration"]["plain"]["restore_stamp_s"]
    first = min(array[0, 0] for array in values.values())
    record = {"schema_version": 1, "kind": "offline_hypothesis_refinement", "status": "executed", "exit_code": 0,
              "scope": "new offline inference on the exact retained B arrays; video replays saved coarse/fine outputs with evaluation truth; no live simulation or hardware claim",
              "dimension": dimension, "scene": json.loads((parent / "runtime.json").read_text())["scene"],
              "parent_repository_path": (parent / "record.json").relative_to(ROOT).as_posix(),
              "parent_sha256": digest(parent / "record.json"), "truth_input_to_estimators": False,
              "protocol_sha256": digest(PROTOCOL), "inference_wall_s": wall_seconds,
              "protocol_repository_path": PROTOCOL.relative_to(ROOT).as_posix(), "ground_z_m": ground_z,
              "metrics": metrics, "metrics_3d": metrics3d,
              "restoration": {name: restoration(array, restore) for name, array in values.items()},
              "initial_sustained_delay_s": {name: restoration(array, first)["sustained_convergence_delay_s"] for name, array in values.items()},
              "source_inputs": {name: digest(parent / name) for name in ("cases.json", "probe-config.json", "probe-B-inputs.npz", "probe-B-inputs.json", "probe-maps/lidar.npy", "probe-maps/depth.npy", "truth.jsonl", "search-samples.csv", "recover-samples.csv")}}
    replay_meta = replay(folder, values, restore, heading_label=f"{dimension.upper()} {record['scene']} | same-input coarse-to-fine test",
                         provenance_label="RESULT REPLAY | retained baselines + new offline inference | same B inputs | no inference during playback")
    replay_meta["frame_sampling"] = "latest retained coarse/fine estimate at each 8fps simulation timestamp; no new inference during replay"
    record["result_replay"] = replay_meta
    record["timing"] = gif(folder / "result.mp4", folder / "result.gif")
    import subprocess
    subprocess.run(["ffmpeg", "-v", "error", "-i", str(folder / "result.mp4"), "-f", "null", "-"], check=True)
    duration = float(probe(folder / "result.mp4")["format"]["duration"])
    subprocess.run(["ffmpeg", "-v", "error", "-ss", str(duration / 2), "-i", str(folder / "result.mp4"), "-frames:v", "1", "-y", str(folder / "frame-mid.png")], check=True)
    record["artifacts"] = {path.relative_to(folder).as_posix(): {"sha256": digest(path), "bytes": path.stat().st_size, "availability": "portable"} for path in folder.rglob("*") if path.is_file()}
    (folder / "record.json").write_text(json.dumps(record, indent=2) + "\n")
    issues = verify_record(folder / "record.json")
    if issues:
        raise ValueError(issues)
    print(json.dumps({"output": str(folder), "metrics": metrics, "initial_sustained_delay_s": record["initial_sustained_delay_s"]}, indent=2), flush=True)


def main():
    global PROTOCOL
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("parent_record", nargs="?", type=Path)
    parser.add_argument("output", nargs="?", type=Path)
    parser.add_argument("--freeze", action="store_true")
    parser.add_argument("--calibrated", action="store_true")
    args = parser.parse_args()
    if args.calibrated:
        PROTOCOL = PROTOCOL.with_name("calibrated-refinement-protocol.json")
    if args.freeze:
        freeze()
        return
    parent = args.parent_record.resolve().parent
    original = json.loads((parent / "record.json").read_text())
    if verify_record(parent / "record.json"):
        raise ValueError("Parent evidence is invalid")
    protocol = json.loads(PROTOCOL.read_text())
    for name, sha in protocol["source_sha256"].items():
        if digest(ROOT / "src/slam_learning/runtime" / name) != sha:
            raise ValueError("Refinement algorithm differs from frozen protocol")
    if digest(ROOT / "src/slam_learning/runtime/recovery_probe.py") != original["hypothesis_probes"]["source_sha256"]["recovery_probe.py"]:
        raise ValueError("H1/H2 implementation changed since parent B")
    folder = args.output.resolve()
    folder.mkdir(parents=True, exist_ok=False)
    (folder / "sources").mkdir()
    for source in (SOURCE, ROOT / "src/slam_learning/runtime/refined_probe.py", ROOT / "src/slam_learning/runtime/recovery_probe.py"):
        shutil.copyfile(source, folder / "sources" / source.name)
    estimates, wall = compute(parent, folder)
    evaluate(parent, folder, estimates, original, wall)


if __name__ == "__main__":
    main()
