"""Cross-runtime control: same B arrays must reproduce the saved coarse estimates."""
import argparse
import json
import platform
import sys
from pathlib import Path

import numpy as np
import scipy

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from slam_learning.core.provenance import digest
from slam_learning.runtime.recovery_probe import Probe, SurfaceMap, wrap


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("parent", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    folder = args.parent.parent
    config = json.loads((folder / "probe-config.json").read_text())
    initial = json.loads((folder / "cases.json").read_text())["plain"]["initial_pose"]
    lidar = np.load(folder / "probe-maps/lidar.npy", allow_pickle=False).astype(float, copy=True)
    depth = np.load(folder / "probe-maps/depth.npy", allow_pickle=False).astype(float, copy=True)
    lidar[:, 2] -= config.get("ground_z_m", 0.)
    depth[:, 2] -= config.get("ground_z_m", 0.)
    maps = [SurfaceMap(lidar, 2 if config["dimension"] == "2d" else 3), SurfaceMap(depth, 3)]
    estimators = {name: Probe([initial["x"], initial["y"], initial["yaw"]], guarded=True, depth=(name == "recover"), recovery=True) for name in ("search", "recover")}
    expected = {(row["case"], row["frame"]): row for row in (json.loads(line) for line in (folder / "probe-updates.jsonl").read_text().splitlines())}
    inputs = np.load(folder / "probe-B-inputs.npz", allow_pickle=False)
    frames = json.loads((folder / "probe-B-inputs.json").read_text())["frames"]
    errors = {name: [] for name in estimators}
    for frame in frames:
        key = f"frame_{frame['frame']:05d}"
        cloud, camera, odom = (inputs[key + suffix] for suffix in ("_lidar", "_depth", "_odom"))
        for name, estimator in estimators.items():
            pose, _ = estimator.update(frame["stamp_s"], odom, (maps[0], cloud), (maps[1], camera) if len(camera) >= 12 else None)
            target = np.array(expected[name, frame["frame"]]["pose"])
            errors[name].append([float(np.linalg.norm(pose[:2] - target[:2])), float(abs(wrap(pose[2] - target[2])))])
    maximum = {name: {"position_delta_m": max(row[0] for row in values), "yaw_delta_rad": max(row[1] for row in values)} for name, values in errors.items()}
    passed = all(value < 1e-5 for row in maximum.values() for value in row.values())
    result = {"parent_sha256": digest(args.parent), "frames_per_case": len(frames), "maximum_deltas": maximum,
              "passed_1e_minus_5_m_rad": passed, "truth_read": False,
              "offline_environment": {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__}}
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2), flush=True)
    if not passed:
        raise ValueError("Cross-runtime coarse replay differs; do not attribute the difference solely to refinement")


if __name__ == "__main__":
    main()
