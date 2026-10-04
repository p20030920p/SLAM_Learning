#!/usr/bin/env python3
"""Generate Removert's rosparams from upstream's own template.

Upstream ships `config/params_kitti.yaml` with the author's absolute paths
(`/media/user/GS1TB/KITTI/...`) and a target region tuned for KITTI 09. This
script loads that file, changes **only** the fields that are machine-specific
(paths) or sequence-specific (index range, LiDAR-frame extrinsic), and writes
the result. Every algorithm parameter - resolutions, voxel size, static
sensitivity, FOV - is left exactly as upstream ships it, so the run is
upstream's configuration, not ours.

The one judgement call is documented in the folder README: our scans are
reconstructed in the **LiDAR frame** (not KITTI's camera frame), so
`ExtrinsicLiDARtoPoseBase` becomes the identity - the option upstream's own
comment block recommends for "lidar-itself odometry".
"""

from __future__ import annotations

import argparse
import os

import yaml

IDENTITY = [1.0, 0.0, 0.0, 0.0,
            0.0, 1.0, 0.0, 0.0,
            0.0, 0.0, 1.0, 0.0,
            0.0, 0.0, 0.0, 1.0]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--upstream", required=True, help="upstream config/params_kitti.yaml")
    ap.add_argument("--scan-dir", required=True)
    ap.add_argument("--pose-file", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--end", type=int, required=True)
    ap.add_argument("--gap", type=int, default=1)
    ap.add_argument("--cores", type=int, default=min(16, os.cpu_count() or 4))
    ap.add_argument("--out", required=True, help="where to write the generated yaml")
    args = ap.parse_args()

    with open(args.upstream) as fh:
        params = yaml.safe_load(fh)
    rmv = params["removert"]

    changed = {
        # machine-specific paths
        "save_pcd_directory": os.path.abspath(args.out_dir).rstrip("/") + "/",
        "sequence_scan_dir": os.path.abspath(args.scan_dir).rstrip("/") + "/",
        "sequence_pose_path": os.path.abspath(args.pose_file),
        # sequence-specific region and sampling
        "start_idx": args.start,
        "end_idx": args.end,
        "use_keyframe_gap": True,
        "keyframe_gap": args.gap,
        # our scans are LiDAR-frame, so no camera->LiDAR extrinsic applies
        "ExtrinsicLiDARtoPoseBase": IDENTITY,
        "num_omp_cores": args.cores,
    }
    for k, v in changed.items():
        rmv[k] = v

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w") as fh:
        yaml.safe_dump(params, fh, sort_keys=True)

    print(f"wrote {args.out}")
    for k in sorted(changed):
        print(f"  {k}: {changed[k]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
