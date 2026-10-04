#!/usr/bin/env python3
"""DUFOMap (RA-L 2024) over one DynamicMap_Benchmark sequence.

Writes the cleaned map that the benchmark's own evaluator consumes.

The call sequence mirrors `methods/dufomap/main.py` from
KTH-RPL/DynamicMap_Benchmark, so that our run is the run the benchmark
describes rather than a re-invention of it:

    dufomap(0.1, 0.2, 2)                    resolution, d_s, d_p - "same with paper"
    run(pc, pose, cloud_transform=False)    the released clouds are already world-frame
    oncePropagateCluster(if_propagate=True, if_cluster=False)
    outputMap(cloud_acc, voxel_map=False)   unvoxelised, so GT stays point-level

The one deliberate difference: DUFOMap's own demo hard-codes 12 threads; we
default to the machine's core count and let --threads override, because the
thread count is not part of the method.

Usage:
    python3 work/run_dufomap.py --seq-dir <...>/data/raw/00 --out results/dufomap_output.pcd
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import time

import numpy as np


def read_pcd(path: str) -> np.ndarray:
    """Minimal reader for the binary `x y z [intensity]` PCDs this benchmark ships.

    Deliberately dependency-free: the benchmark's own reader drags in a PCL
    wrapper, and the only files we read are the ones it wrote.
    """
    with open(path, "rb") as fh:
        raw = fh.read()
    marker = raw.find(b"DATA binary\n")
    if marker < 0:
        raise ValueError(f"{path}: not a binary PCD (only DATA binary is supported)")
    header = raw[:marker].decode("ascii", errors="replace")
    body = raw[marker + len(b"DATA binary\n"):]
    n = int(re.search(r"POINTS (\d+)", header).group(1))
    fields = re.search(r"FIELDS (.*)", header).group(1).split()
    a = np.frombuffer(body[: n * 4 * len(fields)], dtype=np.float32).reshape(-1, len(fields))
    if len(a) != n:
        raise ValueError(f"{path}: header says {n} points, file holds {len(a)}")
    return a


def read_viewpoint(path: str) -> list:
    """The sensor pose the benchmark stores in the PCD VIEWPOINT field.

    Order is [tx, ty, tz, qw, qx, qy, qz], which is what DUFOMap's pose_check
    accepts directly - so it is passed straight through, untransformed.
    """
    with open(path, "rb") as fh:
        head = fh.read(2048)
    marker = head.find(b"DATA binary")
    header = head[: marker if marker > 0 else len(head)].decode("ascii", errors="replace")
    m = re.search(r"VIEWPOINT (.*)", header)
    if not m:
        raise ValueError(f"{path}: no VIEWPOINT - cannot recover the sensor pose")
    return [float(v) for v in m.group(1).split()]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seq-dir", required=True,
                    help="sequence folder holding pcd/ (e.g. .../data/raw/00)")
    ap.add_argument("--out", required=True, help="where to write the cleaned map")
    ap.add_argument("--threads", type=int, default=0, help="0 = all cores")
    ap.add_argument("--max-frames", type=int, default=0, help="0 = all frames (smoke tests)")
    ap.add_argument("--resolution", type=float, default=0.1)
    ap.add_argument("--d-s", type=float, default=0.2)
    # d_p is an int in DUFOMap's pybind signature even though the paper writes it
    # in metres as 2; passing 2.0 raises a TypeError from the binding, so this
    # one is deliberately typed int.
    ap.add_argument("--d-p", type=int, default=2)
    args = ap.parse_args()

    from dufomap import dufomap

    pcd_dir = os.path.join(args.seq_dir, "pcd")
    if not os.path.isdir(pcd_dir):
        print(f"no pcd/ under {args.seq_dir}", file=sys.stderr)
        return 2
    files = sorted(f for f in os.listdir(pcd_dir) if f.endswith(".pcd"))
    if args.max_frames:
        files = files[: args.max_frames]
    if not files:
        print(f"no .pcd frames in {pcd_dir}", file=sys.stderr)
        return 2

    print(f"DUFOMap: {len(files)} frames from {pcd_dir}")
    print(f"  resolution={args.resolution} d_s={args.d_s} d_p={args.d_p} threads={args.threads}")

    mapper = dufomap(args.resolution, args.d_s, args.d_p, num_threads=args.threads)
    t0 = time.time()
    acc = []
    for i, name in enumerate(files):
        path = os.path.join(pcd_dir, name)
        pts = read_pcd(path)[:, :3]
        mapper.run(pts, read_viewpoint(path), cloud_transform=False)
        acc.append(pts)
        if (i + 1) % 25 == 0 or i + 1 == len(files):
            print(f"  [{i + 1}/{len(files)}] {time.time() - t0:.1f}s", flush=True)

    cloud = np.concatenate(acc, axis=0)
    print(f"accumulated {len(cloud)} points in {time.time() - t0:.1f}s")

    mapper.oncePropagateCluster(if_propagate=True, if_cluster=False)
    mapper.outputMap(cloud, voxel_map=False)

    # outputMap writes next to the process CWD; move it where the caller asked.
    produced = "dufomap_output.pcd"
    if not os.path.exists(produced):
        cands = [f for f in os.listdir(".") if f.endswith(".pcd")]
        print(f"outputMap did not write {produced}; found {cands}", file=sys.stderr)
        return 3
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    os.replace(produced, args.out)
    print(f"cleaned map -> {args.out}")
    mapper.printDetailTiming()
    print(f"total {time.time() - t0:.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
