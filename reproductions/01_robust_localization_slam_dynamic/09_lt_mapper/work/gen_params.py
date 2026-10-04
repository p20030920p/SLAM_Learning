#!/usr/bin/env python3
"""Generate ltremovert's rosparams from upstream's own template.

Upstream ships `ltremovert/config/params_ltmapper.yaml` with the author's
absolute paths (`/home/user/Desktop/ltslam-tutorial-kitti/...`), a MulRan
Riverside session pair and `start_idx/end_idx` for that sequence. This script
loads that file and changes **only** the machine-specific paths and the
sequence-specific index range. Every algorithm parameter - the range-image
magnifier ratios, the downsample voxel size, the static-sensitivity pair
(`num_nn_points_within` / `dist_nn_points_within`), the FOVs, the OpenMP core
count - is left exactly as upstream ships it, so the run is upstream's
configuration, not ours.

`ExtrinsicLiDARtoPoseBase` is left at upstream's own value, which is already the
identity: our poses come from the benchmark's VIEWPOINT fields, i.e. they are
LiDAR-itself poses, and upstream's comment block says to use the identity for
exactly that case.

The one judgement call is the index range: `parseKeyframes` includes `end_idx`
(`Removerter.cpp:92` -> `Session.cpp:149` tests `curr_idx > end_idx`), so
`end_idx = <number of central scans>` means "all of them".

Usage:
    python3 work/gen_params.py --upstream <checkout>/ltremovert/config/params_ltmapper.yaml \
        --central-scans <...>/central/Scans --central-poses <...>/central/poses.txt \
        --query-scans <...>/query/Scans --query-poses <...>/query/poses.txt \
        --out-dir results/ltmapper_kitti00 --start 0 --end 81 --out work/generated/params.yaml
"""

from __future__ import annotations

import argparse
import os

import yaml


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--upstream", required=True, help="upstream config/params_ltmapper.yaml")
    ap.add_argument("--central-scans", required=True)
    ap.add_argument("--central-poses", required=True)
    ap.add_argument("--query-scans", required=True)
    ap.add_argument("--query-poses", required=True)
    ap.add_argument("--out-dir", required=True, help="where the node writes its pcd outputs")
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--end", type=int, required=True)
    ap.add_argument("--out", required=True, help="where to write the generated yaml")
    args = ap.parse_args()

    with open(args.upstream) as fh:
        params = yaml.safe_load(fh)
    rmv = params["removert"]

    def d(p):  # upstream's own template ends every directory with a slash
        return os.path.abspath(p).rstrip("/") + "/"

    changed = {
        # machine-specific paths
        "save_pcd_directory": d(args.out_dir),
        "central_sess_scan_dir": d(args.central_scans),
        "central_sess_pose_path": os.path.abspath(args.central_poses),
        "query_sess_scan_dir": d(args.query_scans),
        "query_sess_pose_path": os.path.abspath(args.query_poses),
        # sequence-specific index range (inclusive end, see module docstring)
        "start_idx": args.start,
        "end_idx": args.end,
    }
    for k, v in changed.items():
        rmv[k] = v

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    # sort_keys=False: the generated file keeps upstream's own ordering, so a
    # diff against the template shows only the seven fields above.
    with open(args.out, "w") as fh:
        yaml.safe_dump(params, fh, sort_keys=False)

    print(f"wrote {args.out}")
    for k in changed:
        print(f"  {k}: {changed[k]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
