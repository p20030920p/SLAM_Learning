#!/usr/bin/env python3
"""Rebuild a KITTI-odometry-format sequence from the DynamicMap_Benchmark release.

Why this exists
---------------
KISS-ICP's paper evaluates on KITTI, MulRan, Newer College and Boreas, and every
one of those needs registration, a form, or (for Newer College) has a download
that is currently broken. What we *do* have free is the benchmark's Zenodo
release of KITTI 00: 141 frames shipped as **world-frame** clouds with the sensor
pose in each PCD's VIEWPOINT field.

Those clouds were built by transforming raw Velodyne scans with exactly those
poses, so the transform is invertible and the original sensor-frame scans come
back out. This script does that inversion and writes a KITTI-odometry layout, so
the official `--dataloader kitti` path can be used unmodified.

    p_sensor = R(q)^T · (p_world − t)

What this does and does not give you is recorded in the folder README. Briefly:
141 of KITTI 00's 4541 frames, 108.3 m of travel, and ground truth that is
SuMa-derived (SemanticKITTI's convention) rather than KITTI's official poses.

Usage:
    python3 work/make_kitti_seq.py --seq-dir <benchmark>/data/raw/00 \
                                   --out <02_kiss_icp>/data/raw/kitti00_sub
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import sys

import numpy as np

MARK = b"DATA binary\n"


def read_pcd(path: str):
    """Binary `x y z [intensity]` PCD plus its VIEWPOINT (tx ty tz qw qx qy qz)."""
    with open(path, "rb") as fh:
        raw = fh.read()
    i = raw.find(MARK)
    if i < 0:
        raise ValueError(f"{path}: not a binary PCD")
    header = raw[:i].decode("ascii", errors="replace")
    body = raw[i + len(MARK):]
    n = int(re.search(r"POINTS (\d+)", header).group(1))
    fields = re.search(r"FIELDS (.*)", header).group(1).split()
    vp = [float(x) for x in re.search(r"VIEWPOINT (.*)", header).group(1).split()]
    pts = np.frombuffer(body[: n * 4 * len(fields)], dtype=np.float32).reshape(-1, len(fields))
    if len(pts) != n:
        raise ValueError(f"{path}: header says {n}, file holds {len(pts)}")
    return pts, vp


def quat_to_R(qw: float, qx: float, qy: float, qz: float) -> np.ndarray:
    n = np.sqrt(qw * qw + qx * qx + qy * qy + qz * qz)
    qw, qx, qy, qz = qw / n, qx / n, qy / n, qz / n
    return np.array([
        [1 - 2 * (qy * qy + qz * qz), 2 * (qx * qy - qz * qw),     2 * (qx * qz + qy * qw)],
        [2 * (qx * qy + qz * qw),     1 - 2 * (qx * qx + qz * qz), 2 * (qy * qz - qx * qw)],
        [2 * (qx * qz - qy * qw),     2 * (qy * qz + qx * qw),     1 - 2 * (qx * qx + qy * qy)],
    ])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seq-dir", required=True, help="benchmark sequence folder holding pcd/")
    ap.add_argument("--out", required=True, help="KITTI root to create")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    src = os.path.join(args.seq_dir, "pcd")
    files = sorted(f for f in os.listdir(src) if f.endswith(".pcd"))
    if not files:
        print(f"no .pcd under {src}", file=sys.stderr)
        return 2

    seq = os.path.join(args.out, "sequences", "00")
    velo = os.path.join(seq, "velodyne")
    poses_dir = os.path.join(args.out, "poses")
    if os.path.isdir(args.out) and args.force:
        shutil.rmtree(args.out)
    for d in (velo, poses_dir):
        os.makedirs(d, exist_ok=True)

    # Tr = identity: with it, KISS-ICP's KITTI loader keeps poses and clouds in
    # the LiDAR frame instead of rotating them into the camera frame. The metric
    # is relative, so the convention cancels - but both sides must agree.
    with open(os.path.join(seq, "calib.txt"), "w") as fh:
        fh.write("Tr: " + " ".join(["1", "0", "0", "0", "0", "1", "0", "0",
                                    "0", "0", "1", "0"]) + "\n")

    pose_rows = []
    moved = []
    for k, name in enumerate(files):
        pts, vp = read_pcd(os.path.join(src, name))
        t = np.array(vp[:3], dtype=np.float64)
        R = quat_to_R(*vp[3:7])
        local = (pts[:, :3].astype(np.float64) - t) @ R          # R^T (p - t)
        out = np.empty((len(local), 4), dtype=np.float32)
        out[:, :3] = local
        out[:, 3] = pts[:, 3] if pts.shape[1] > 3 else 0.0       # intensity passthrough
        out.tofile(os.path.join(velo, f"{k:06d}.bin"))
        pose_rows.append(np.hstack([R, t.reshape(3, 1)]).reshape(-1))
        moved.append(np.linalg.norm(t))
        if (k + 1) % 40 == 0 or k + 1 == len(files):
            print(f"  [{k + 1}/{len(files)}] {name} -> {k:06d}.bin  ({len(local)} pts)")

    np.savetxt(os.path.join(poses_dir, "00.txt"), np.array(pose_rows), fmt="%.9e")

    # KISS-ICP's KITTI loader reads sequences/00/times.txt, but only to stamp the
    # TUM-format trajectory it writes out - the metric does not use it. The
    # benchmark package carries no timestamps, so they are reconstructed from the
    # frame numbers at KITTI's 10 Hz (frames are contiguous, 4390..4530).
    np.savetxt(os.path.join(seq, "times.txt"),
               (np.arange(len(files)) * 0.1).reshape(-1, 1), fmt="%.6f")

    print(f"\nwrote {len(files)} scans to {velo}")
    print(f"wrote {len(files)} poses to {os.path.join(poses_dir, '00.txt')}")
    print("note: poses are in the LiDAR frame (calib Tr = identity)")

    # Sanity: a spinning-LiDAR scan in its own frame has the sensor at the origin,
    # so the body-centred distance must collapse compared with the world frame.
    probe = np.fromfile(os.path.join(velo, "000000.bin"), dtype=np.float32).reshape(-1, 4)
    with open(os.path.join(src, files[0]), "rb") as fh:
        head = fh.read(4096)
    vp0 = [float(x) for x in re.search(r"VIEWPOINT (.*)",
            head[:head.find(b"DATA binary")].decode("ascii", "replace")).group(1).split()]
    world = np.frombuffer(open(os.path.join(src, files[0]), "rb").read()[
        open(os.path.join(src, files[0]), "rb").read().find(MARK) + len(MARK):], dtype=np.float32)
    print(f"frame 0 sensor-frame: |p| mean {np.linalg.norm(probe[:, :3], axis=1).mean():.2f} m, "
          f"xyz range x[{probe[:, 0].min():.1f},{probe[:, 0].max():.1f}] "
          f"y[{probe[:, 1].min():.1f},{probe[:, 1].max():.1f}] "
          f"z[{probe[:, 2].min():.1f},{probe[:, 2].max():.1f}]")
    print(f"frame 0 viewpoint was ({vp0[0]:.1f}, {vp0[1]:.1f}, {vp0[2]:.1f}) in the world frame")
    return 0


if __name__ == "__main__":
    sys.exit(main())
