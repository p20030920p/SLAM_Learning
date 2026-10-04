#!/usr/bin/env python3
"""Write the resolution-normalised maps that the registration experiment uses.

Why these exist
---------------
`registration_utility.py` registers into every map **after** normalising all of
them to one resolution (0.2 m), because otherwise it would rank maps by density
rather than by structure - ERASOR submits a 0.1–0.2 m voxelised map while
DUFOMap submits a dense one.

But the map-quality metrics everyone quotes (SA/DA/AA) are measured on the maps
**as submitted**, at their own resolutions - and 01-03 already showed that the
benchmark's 0.05 m nearest-neighbour rule reads downsampling as deletion. So the
same map can be "bad" by SA and perfectly registrable, or vice versa.

This script materialises the normalised maps as PCDs so both numbers can be
reported for *the identical point set*:

    as-submitted SA/DA/AA   (what the benchmark tables print)
    normalised  SA/DA/AA   (the object the registration experiment registers into)

Usage:
    work/export_normalized_maps.py --seq-dir <bench>/data/raw/00 --out-dir results/registration_maps
"""

from __future__ import annotations

import argparse
import os
import sys

import open3d as o3d

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from registration_utility import EXCLUDED, MAP_SOURCES, load_maps  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seq-dir", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--voxel", type=float, default=0.2)
    args = ap.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    repro_dir = os.path.normpath(os.path.join(here, "..", ".."))
    os.makedirs(args.out_dir, exist_ok=True)

    maps = load_maps(repro_dir, args.seq_dir, args.voxel,
                     os.path.join(here, "generated"))
    for name, pcd in maps.items():
        # strip normals: the benchmark evaluator reads binary `x y z [intensity]`
        # and would otherwise take normal_x as a semantic label
        out = o3d.geometry.PointCloud()
        out.points = pcd.points
        path = os.path.join(args.out_dir, f"{name}.pcd")
        o3d.io.write_point_cloud(path, out, write_ascii=False)
        print(f"  {name:20s} {len(out.points):>9,} pts -> {path} "
              f"({os.path.getsize(path) / 1e6:.1f} MB)")
    print(f"skipped (not usable here): {', '.join(EXCLUDED) or 'none'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
