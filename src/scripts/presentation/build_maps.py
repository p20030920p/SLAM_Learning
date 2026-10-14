"""Run native author mappers on measured 3D mapping A; project a common AMCL map."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
from scipy.ndimage import binary_dilation


def project(points, raw, origins, folder, bounds):
    resolution = 0.05
    origin = np.asarray(bounds[0])
    width, height = np.ceil((np.asarray(bounds[1]) - origin) / resolution).astype(int) + 1
    image = np.full((height, width), 205, dtype=np.uint8)
    # Common observed free rays; no SDF geometry is supplied to the maps.
    valid = (raw[:, 2] >= 0.12) & (raw[:, 2] <= 1.20)
    for endpoint, start in zip(raw[valid, :2][::4], origins[valid, :2][::4]):
        count = max(2, int(np.linalg.norm(endpoint - start) / resolution) + 1)
        ray = start + np.linspace(0, 1, count)[:, None] * (endpoint - start)
        cells = np.floor((ray - origin) / resolution).astype(int)
        inside = (cells[:, 0] >= 0) & (cells[:, 0] < width) & (cells[:, 1] >= 0) & (cells[:, 1] < height)
        cells = cells[inside]
        image[cells[:, 1], cells[:, 0]] = 254
    selected = points[(points[:, 2] >= 0.12) & (points[:, 2] <= 1.20)]
    cells = np.floor((selected[:, :2] - origin) / resolution).astype(int)
    inside = (cells[:, 0] >= 0) & (cells[:, 0] < width) & (cells[:, 1] >= 0) & (cells[:, 1] < height)
    cells = cells[inside]
    occupied = np.zeros(image.shape, dtype=bool)
    occupied[cells[:, 1], cells[:, 0]] = True
    occupied = binary_dilation(occupied, iterations=1)
    image[occupied] = 0
    folder.mkdir(parents=True, exist_ok=False)
    with (folder / "map.pgm").open("wb") as stream:
        stream.write(f"P5\n{width} {height}\n255\n".encode())
        stream.write(np.flipud(image).tobytes())
    (folder / "map.yaml").write_text(
        f"image: map.pgm\nmode: trinary\nresolution: {resolution}\n"
        f"origin: [{origin[0]}, {origin[1]}, 0.0]\nnegate: 0\noccupied_thresh: 0.65\nfree_thresh: 0.196\n"
    )
    np.save(folder / "points.npy", points.astype(np.float32))
    return {
        "resolution_m": resolution,
        "height_band_m": [0.12, 1.20],
        "origin_xy_m": origin.tolist(),
        "width": int(width),
        "height": int(height),
        "points": len(points),
        "projection": "common raw observed rays every fourth point; one-cell occupied dilation; no world geometry",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--recording", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--runtime", type=Path, default=Path("/home/qzl/projects/SLAM_Author_Originals"))
    parser.add_argument("--physical-root", type=Path, default=Path("/mnt/d/workspace/be2/SLAM-Physical"))
    args = parser.parse_args()
    sys.path.insert(0, str(args.physical_root / "src"))
    from native_beautymap import run_beautymap
    from slam_physical.storage import read_pcd, write_pcd

    archive = np.load(args.recording / "mapping-clouds.npz", allow_pickle=False)
    poses = archive["poses"]
    ids = np.linspace(0, len(poses) - 1, min(60, len(poses)), dtype=int)
    scans = [archive[f"scan_{i:04d}"] for i in ids]
    poses = poses[ids]
    clouds = [scan @ pose[:3, :3].T + pose[:3, 3] for scan, pose in zip(scans, poses)]
    raw = np.concatenate(clouds)
    origins = np.concatenate(
        [np.broadcast_to(pose[:3, 3], cloud.shape) for cloud, pose in zip(clouds, poses)]
    )
    bounds = [np.floor(raw[:, :2].min(axis=0) - 0.5), np.ceil(raw[:, :2].max(axis=0) + 0.5)]
    args.output.mkdir(parents=True, exist_ok=False)
    write_pcd(args.output / "raw-map.pcd", raw)
    records = {}
    for method in ("raw", "dufomap", "beautymap"):
        started = time.perf_counter()
        print(f"NATIVE MAP PROCESSING: {method}; same {len(scans)} measured 3D scans", flush=True)
        points = raw
        if method == "dufomap":
            from dufomap import dufomap

            native = args.output / "dufomap-native"
            native.mkdir()
            mapper = dufomap(0.1, 0.2, 1, num_threads=2)
            for i, (cloud, pose) in enumerate(zip(clouds, poses)):
                mapper.run(cloud, [*map(float, pose[:3, 3]), 1.0, 0.0, 0.0, 0.0], cloud_transform=False)
                print(f"DUFOMap {i+1}/{len(scans)}", flush=True)
            mapper.oncePropagateCluster(if_propagate=True, if_cluster=False)
            previous = Path.cwd()
            try:
                os.chdir(native)
                mapper.outputMap(raw, voxel_map=False)
            finally:
                os.chdir(previous)
            points = read_pcd(native / "dufomap_output.pcd")
        if method == "beautymap":
            mask, native_record = run_beautymap(
                scans,
                poses,
                args.output / "beautymap-native",
                args.runtime / "upstream/beautymap",
                {"dis_range": 8, "xy_resolution": 0.5, "h_res": 0.2},
            )
            points = raw[mask]
        records[method] = {
            **project(points, raw, origins, args.output / method, bounds),
            "seconds": time.perf_counter() - started,
            "raw_points": len(raw),
        }
    report = {
        "kind": "author_map_platform_adaptation",
        "world_sha256": json.loads((args.recording / "runtime.json").read_text()).get("world_sha256"),
        "source_recording": str(args.recording),
        "input_sha256": hashlib.sha256((args.recording / "mapping-clouds.npz").read_bytes()).hexdigest(),
        "selected_scan_ids": ids.tolist(),
        "methods": records,
        "scope": "measured Sim2Real 3D point clouds with evaluation-provided mapping poses; not original-paper metrics",
        "truth_to_held_out_localization": False,
    }
    (args.output / "record.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    main()
