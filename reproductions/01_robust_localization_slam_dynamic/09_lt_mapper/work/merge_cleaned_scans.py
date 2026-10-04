#!/usr/bin/env python3
"""Merge ltremovert's cleaned per-scan output into one global map.

`Removerter::saveAllTypeOfScans()` writes the central session's cleaned scans
into `scans_updated/` (and `scans_updated_strong/`) as **sensor-frame** clouds,
named after the input scans. Upstream merges scans the same way in
`Removerter::mergeScansWithinGlobalCoord` (`Removerter.cpp:158-177`): apply the
LiDAR->base extrinsic, then the scan's pose. With the identity extrinsic that is
one matrix multiply per scan.

Why it is worth having both this and `updated_map.pcd`: they are the two ends of
the same run. `updated_map.pcd` is the map-level result of Step 3 - it keeps only
the structure both sessions agree on - while the merged cleaned scans are the
scan-side result, which is what the sibling reproduction 01-04 scores as
Removert's headline map (`map_static/StaticMapScansideMapGlobal.pcd`). Reporting
one number without saying which output it belongs to is the mistake 01-04
documents; here both are scored.

Usage:
    python3 work/merge_cleaned_scans.py --scans results/ltmapper_kitti00/scans_updated \
        --poses data/raw/kitti00_two_sessions/central/poses.txt \
        --out results/ltmapper_kitti00/scans_updated_merged.pcd
"""

from __future__ import annotations

import argparse
import os
import re
import sys

import numpy as np

MARK = b"DATA binary\n"


def read_pcd(path: str) -> np.ndarray:
    with open(path, "rb") as fh:
        raw = fh.read()
    i = raw.find(MARK)
    if i < 0:
        raise ValueError(f"{path}: not a binary PCD")
    header = raw[:i].decode("ascii", errors="replace")
    n = int(re.search(r"POINTS (\d+)", header).group(1))
    fields = re.search(r"FIELDS (.*)", header).group(1).split()
    return np.frombuffer(raw[i + len(MARK): i + len(MARK) + n * 4 * len(fields)],
                         dtype=np.float32).reshape(-1, len(fields))


def write_binary_pcd(path: str, pts: np.ndarray) -> None:
    n = len(pts)
    header = ("# .PCD v0.7 - Point Cloud Data file format\nVERSION 0.7\n"
              "FIELDS x y z intensity\nSIZE 4 4 4 4\nTYPE F F F F\nCOUNT 1 1 1 1\n"
              f"WIDTH {n}\nHEIGHT 1\nVIEWPOINT 0 0 0 1 0 0 0\nPOINTS {n}\nDATA binary\n")
    with open(path, "wb") as fh:
        fh.write(header.encode("ascii"))
        fh.write(pts.astype(np.float32).tobytes())


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scans", required=True, help="a scans_* directory")
    ap.add_argument("--poses", required=True, help="the central session's poses.txt")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    names = sorted(f for f in os.listdir(args.scans) if f.endswith(".pcd"))
    poses = np.loadtxt(args.poses).reshape(-1, 3, 4)
    if len(names) != len(poses):
        print(f"{len(names)} scans vs {len(poses)} poses", file=sys.stderr)
        return 2

    chunks, total = [], 0
    for k, nm in enumerate(names):
        p = read_pcd(os.path.join(args.scans, nm))
        R, t = poses[k, :, :3], poses[k, :, 3]
        world = np.empty_like(p)
        world[:, :3] = (p[:, :3].astype(np.float64) @ R.T + t).astype(np.float32)
        world[:, 3] = p[:, 3] if p.shape[1] > 3 else 0.0
        chunks.append(world)
        total += len(world)
    merged = np.concatenate(chunks)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    write_binary_pcd(args.out, merged)
    print(f"merged {len(names)} scans ({total} points) -> {args.out} ({len(merged)} points)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
