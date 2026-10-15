"""Matched real sensor maps for the lightweight recovery hypotheses."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

from build_maps import project

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from slam_learning.runtime.recovery_probe import voxel


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    args = parser.parse_args()
    run = args.run
    extra = np.load(run / "probe-mapping-inputs.npz", allow_pickle=False)
    metadata = json.loads((run / "probe-mapping-inputs.json").read_text())
    points, origins = {"lidar2d": [], "depth": [], "lidar3d": []}, {"lidar2d": [], "lidar3d": []}
    for row in metadata["records"]:
        key = row["key"]
        kind = key.split("_")[0]
        pose = extra[key + "_pose"]
        moved = extra[key] @ pose[:3, :3].T + pose[:3, 3]
        points[kind].append(moved)
        if kind in origins:
            origins[kind].append(np.broadcast_to(pose[:3, 3], moved.shape))
    lidar = np.load(run / "mapping-clouds.npz", allow_pickle=False)
    for index, pose in enumerate(lidar["poses"]):
        moved = lidar[f"scan_{index:04d}"] @ pose[:3, :3].T + pose[:3, 3]
        points["lidar3d"].append(moved)
        origins["lidar3d"].append(np.broadcast_to(pose[:3, 3], moved.shape))
    output = run / "probe-maps"
    output.mkdir(exist_ok=False)
    manifest = {"kind": "probe_mapping_A", "source_recording": str(run),
                "world_sha256": json.loads((run / "runtime.json").read_text())["world_sha256"],
                "provided_mapping_poses": True, "truth_to_localization_B": False,
                "inputs": {name: hashlib.sha256((run / name).read_bytes()).hexdigest() for name in
                           ("mapping-clouds.npz", "probe-mapping-inputs.npz", "probe-mapping-inputs.json")}, "maps": {}}
    for kind in points:
        raw = np.concatenate(points[kind])
        if kind == "depth":
            selected = raw[(raw[:, 2] > .12) & (raw[:, 2] < 2.4)]
            selected = voxel(selected, .06)
            np.save(output / "depth.npy", selected.astype(np.float32))
        else:
            selected = voxel(raw, .06)
            bounds = [np.floor(raw[:, :2].min(axis=0) - .5), np.ceil(raw[:, :2].max(axis=0) + .5)]
            project(selected, raw, np.concatenate(origins[kind]), output / kind, bounds)
        manifest["maps"][kind] = {"raw_points": len(raw), "voxel_points": len(selected)}
    (output / "record.json").write_text(json.dumps(manifest, indent=2) + "\n")
    runtime = json.loads((run / "runtime.json").read_text())
    marker = Path(__file__).resolve().parents[3] / f".cache/presentation/probe-maps-{runtime['scene']}-latest.json"
    marker.write_text(json.dumps({"path": str(output)}, indent=2) + "\n")
    print(json.dumps(manifest, indent=2), flush=True)


if __name__ == "__main__":
    main()
