#!/usr/bin/env python3
"""Build ltremovert's two-session input from the benchmark's world-frame clouds.

Why this exists
---------------
LT-mapper's change detector (`ltremovert`) wants what SC-LIO-SAM's saver writes:
two session directories of **sensor-frame** `.pcd` scans plus one pose file per
session holding 12 numbers per line (KITTI odometry `[R|t]`, row-major). The
paper's own input is the ParkingLot dataset, which is raw Ouster+IMU and still
needs SC-LIO-SAM to become this format; the Docker image is 2.2 GB and there is
no docker on this machine.

What we do have is the DynamicMap_Benchmark release of KITTI 00: 141 frames
shipped as **world-frame** clouds whose per-scene `VIEWPOINT` field holds the
sensor pose `(t, q)`. Those clouds were built by transforming raw Velodyne scans
with exactly those poses, so the transform inverts:

    p_sensor = R(q)^T · (p_world − t)

which is the same inversion 02_kiss_icp/work/make_kitti_seq.py already uses to
write `.bin` scans for KISS-ICP. Here it writes **binary .pcd** instead, because
`ltremovert`'s `.bin` branch is commented out at `Session.cpp:277-281`.

Why sensor frame matters
------------------------
`precleaningKeyframes(2.5)` (`Session.cpp:506-533`) deletes every point with
range < 2.5 m **and** |z| < 0.5 in the *scan* frame. Feeding world-frame clouds
with identity poses would carve a 2.5 m ball out of the map at the world origin
instead of under the sensor. So the inversion is not cosmetic.

Two sessions, one world frame
-----------------------------
Both pose files are the benchmark's own VIEWPOINTs, i.e. already expressed in a
single common world frame — which is the whole reason `ltslam` (and therefore
GTSAM, which is not installed) is not needed here. The central session is the
early part of the pass and the query session the later part, with an overlap;
`Removerter::parseKeyframes` (`Removerter.cpp:92-93`) then crops the central
session to `[start_idx, end_idx)` and auto-crops the query session to scans
within 10 m of a central keyframe (`Session.cpp:234`).

Split order, file names and pose lines are kept 1:1: `loadSessionInfo` sorts the
directory listing and reads the pose file line by line, and asserts the two
counts match (`Session.cpp:87-117`) — so `000000.pcd` must go with line 1.

Usage:
    python3 work/make_ltmapper_sessions.py \
        --seq-dir ../01_dynamicmap_benchmark/data/raw/00 \
        --out data/raw/kitti00_two_sessions [--force]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys

import numpy as np

NAN_MARK = b"DATA binary\n"

# index ranges into the 141 benchmark frames (004390..004530), as recommended by
# work/feasibility.md §4 after simulating Session.cpp:234's 10 m ROI rule
DEFAULT_CENTRAL = (0, 81)   # frames 004390..004470  (81 scans)
DEFAULT_QUERY = (61, 141)   # frames 004451..004530  (80 scans)


def read_pcd(path: str):
    """Binary `x y z intensity` PCD plus its VIEWPOINT (tx ty tz qw qx qy qz)."""
    with open(path, "rb") as fh:
        raw = fh.read()
    i = raw.find(NAN_MARK)
    if i < 0:
        raise ValueError(f"{path}: not a binary PCD")
    header = raw[:i].decode("ascii", errors="replace")
    n = int(re.search(r"POINTS (\d+)", header).group(1))
    fields = re.search(r"FIELDS (.*)", header).group(1).split()
    vp = [float(x) for x in re.search(r"VIEWPOINT (.*)", header).group(1).split()]
    pts = np.frombuffer(raw[i + len(NAN_MARK): i + len(NAN_MARK) + n * 4 * len(fields)],
                        dtype=np.float32).reshape(-1, len(fields))
    if len(pts) != n:
        raise ValueError(f"{path}: header says {n} points, file holds {len(pts)}")
    return pts, vp, fields


def quat_to_R(qw: float, qx: float, qy: float, qz: float) -> np.ndarray:
    n = np.sqrt(qw * qw + qx * qx + qy * qy + qz * qz)
    qw, qx, qy, qz = qw / n, qx / n, qy / n, qz / n
    return np.array([
        [1 - 2 * (qy * qy + qz * qz), 2 * (qx * qy - qz * qw),     2 * (qx * qz + qy * qw)],
        [2 * (qx * qy + qz * qw),     1 - 2 * (qx * qx + qz * qz), 2 * (qy * qz - qx * qw)],
        [2 * (qx * qz - qy * qw),     2 * (qy * qz + qx * qw),     1 - 2 * (qx * qx + qy * qy)],
    ])


def write_binary_pcd(path: str, xyz: np.ndarray, intensity: np.ndarray) -> None:
    """The `x y z intensity` binary PCD that `pcl::io::loadPCDFile<PointXYZI>` reads.

    The sensor's own frame puts the origin at the sensor, so the VIEWPOINT is the
    identity — no pose is baked into the cloud any more (that is what the pose
    file is for).
    """
    n = len(xyz)
    rec = np.empty((n, 2, 4), dtype=np.float32)
    rec[:, 0, :3] = xyz
    rec[:, 0, 3] = intensity
    header = (
        "# .PCD v0.7 - Point Cloud Data file format\n"
        "VERSION 0.7\n"
        "FIELDS x y z intensity\n"
        "SIZE 4 4 4 4\n"
        "TYPE F F F F\n"
        "COUNT 1 1 1 1\n"
        f"WIDTH {n}\n"
        "HEIGHT 1\n"
        "VIEWPOINT 0 0 0 1 0 0 0\n"
        f"POINTS {n}\n"
        "DATA binary\n"
    ).encode("ascii")
    # rec[:,0] is the point, rec[:,1] is unused padding -- write only the first
    # half of every 32-byte record
    body = rec[:, 0, :].tobytes()
    with open(path, "wb") as fh:
        fh.write(header)
        fh.write(body)


def build_session(files, src_dir, out_dir, lo, hi, force, kind):
    scans_dir = os.path.join(out_dir, "Scans")
    os.makedirs(scans_dir, exist_ok=True)
    pose_rows = []
    sensor_ranges = []
    for k, fi in enumerate(range(lo, hi)):
        name = files[fi]
        pts, vp, fields = read_pcd(os.path.join(src_dir, name))
        if fields[:3] != ["x", "y", "z"]:
            raise ValueError(f"{name}: unexpected FIELDS {fields}")
        t = np.array(vp[:3], dtype=np.float64)
        R = quat_to_R(*vp[3:7])
        local = (pts[:, :3].astype(np.float64) - t) @ R          # R^T (p - t)
        inten = pts[:, 3] if pts.shape[1] > 3 else np.zeros(len(pts), dtype=np.float32)
        write_binary_pcd(os.path.join(scans_dir, f"{k:06d}.pcd"), local, inten)
        pose_rows.append(np.hstack([R, t.reshape(3, 1)]).reshape(-1))
        sensor_ranges.append(float(np.linalg.norm(local, axis=1).mean()))
        if (k + 1) % 20 == 0 or k + 1 == hi - lo:
            print(f"  [{kind} {k + 1}/{hi - lo}] {name} -> {k:06d}.pcd "
                  f"({len(local)} pts, |p| mean {sensor_ranges[-1]:.2f} m)")

    # 12 numbers per line: R row-major, then t. Session.cpp:104-107 appends the
    # missing [0,0,0,1] row itself.
    np.savetxt(os.path.join(out_dir, "poses.txt"), np.array(pose_rows), fmt="%.9e")
    return {"kind": kind, "src_frames": [files[i] for i in range(lo, hi)],
            "num_scans": hi - lo, "idx_range": [lo, hi],
            "mean_sensor_range_m": float(np.mean(sensor_ranges))}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seq-dir", required=True, help="benchmark sequence folder holding pcd/")
    ap.add_argument("--out", required=True, help="session root to create")
    ap.add_argument("--central", nargs=2, type=int, default=list(DEFAULT_CENTRAL),
                    metavar=("LO", "HI"), help="central session slice [lo, hi)")
    ap.add_argument("--query", nargs=2, type=int, default=list(DEFAULT_QUERY),
                    metavar=("LO", "HI"), help="query session slice [lo, hi)")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    src = os.path.join(args.seq_dir, "pcd")
    if not os.path.isdir(src):
        print(f"no pcd/ under {args.seq_dir}", file=sys.stderr)
        return 2
    files = sorted(f for f in os.listdir(src) if f.endswith(".pcd"))
    if not files:
        print(f"no .pcd under {src}", file=sys.stderr)
        return 2
    if max(args.central[1], args.query[1]) > len(files):
        print(f"slice exceeds the {len(files)} available frames", file=sys.stderr)
        return 2

    if os.path.isdir(args.out) and args.force:
        shutil.rmtree(args.out)
    os.makedirs(args.out, exist_ok=True)

    meta = {"source_seq_dir": os.path.abspath(args.seq_dir),
            "source_frames": [files[0], files[-1]], "num_source_frames": len(files),
            "frame_convention": "p_sensor = R(q)^T (p_world - t); pose line = R row-major then t",
            "viewpoint_role": "benchmark VIEWPOINT = sensor pose in the common world frame"}
    meta["central"] = build_session(files, src, os.path.join(args.out, "central"),
                                    *args.central, force=args.force, kind="central")
    meta["query"] = build_session(files, src, os.path.join(args.out, "query"),
                                  *args.query, force=args.force, kind="query")
    meta["central"]["pose_path"] = "central/poses.txt"
    meta["query"]["pose_path"] = "query/poses.txt"

    with open(os.path.join(args.out, "sessions.json"), "w") as fh:
        json.dump(meta, fh, indent=2)

    print(f"\nwrote {args.out}")
    print(f"  central: {meta['central']['num_scans']} scans "
          f"({meta['central']['src_frames'][0]}..{meta['central']['src_frames'][-1]}) "
          f"+ central/poses.txt")
    print(f"  query:   {meta['query']['num_scans']} scans "
          f"({meta['query']['src_frames'][0]}..{meta['query']['src_frames'][-1]}) "
          f"+ query/poses.txt")
    print("  note: both pose files are in the same world frame (the benchmark VIEWPOINTs)")

    # Sanity: a sensor-frame scan must have the sensor at its own origin, so the
    # mean range collapses relative to the world-frame cloud; and the 2.5 m ball
    # precleaningKeyframes carves must be a small shell, not the whole cloud.
    probe, vp, _ = read_pcd(os.path.join(args.out, "central", "Scans", "000000.pcd"))
    r = np.linalg.norm(probe[:, :3], axis=1)
    world, wvp, _ = read_pcd(os.path.join(src, files[args.central[0]]))
    print(f"\nframe 0 sensor-frame: mean range {r.mean():.2f} m, "
          f"r<2.5 m with |z|<0.5 m: {int(((r < 2.5) & (np.abs(probe[:, 2]) < 0.5)).sum())} pts "
          f"of {len(r)}")
    print(f"same frame in world frame was at ({wvp[0]:.1f}, {wvp[1]:.1f}, {wvp[2]:.1f}), "
          f"mean range {np.linalg.norm(world[:, :3], axis=1).mean():.2f} m")
    return 0


if __name__ == "__main__":
    sys.exit(main())
