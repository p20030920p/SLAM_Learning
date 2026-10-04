#!/usr/bin/env python3
"""Restrict the benchmark GT to the region the two ltremovert sessions observe.

Why this exists
---------------
`updated_map.pcd` is built from the **central** session (81 frames) plus the
**query** keyframes that survive `Session.cpp:234`'s 10 m ROI crop (29 frames of
80). The benchmark's `gt_cloud.pcd` instead labels the whole 141-frame KITTI 00
pass, and the evaluator turns every GT static point with no neighbour within
0.05 m of the map into a false removal. GT structure that lies beyond the last
frame either session contains therefore *cannot* be in the map, and scoring the
map against the full GT charges the method for ground it never drove over.

This script builds the fair comparison partner: the GT points that at least one
of the **input scans actually fed to ltremovert** observed. Coverage is defined
by the input scans and their poses, never by the method's output, so the
restricted score is not circular — it is the standard "evaluate where the sensor
looked" restriction.

Two details that make it exact:
  * the ROI rule is recomputed from the two pose files with `Session.cpp:217-247`
    (nearest central keyframe within 10.0 m, `keyframe_gap = 1`), and the count
    is checked against the ltremovert log;
  * the benchmark's world-frame clouds *are* the sensor returns transformed by
    those poses, so a GT point is observable iff it has a neighbour in the union
    of the covered frames' clouds (0.05 m, the evaluator's own tolerance).

Usage:
    python3 work/make_coverage_matched_gt.py \
        --bench-seq ../01_dynamicmap_benchmark/data/raw/00 \
        --sessions data/raw/kitti00_two_sessions \
        --log work/logs/ltmapper.log \
        --out data/raw/gt_covered_sessions
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

import numpy as np
from scipy.spatial import cKDTree

MARK = b"DATA binary\n"
INPLACE_THRES = 10.0  # Session.cpp:234


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


def poses_by_t(path: str) -> np.ndarray:
    return np.loadtxt(path).reshape(-1, 3, 4)[:, :, 3]


def roi_indices(central_poses: np.ndarray, query_poses: np.ndarray,
                thres: float = INPLACE_THRES) -> np.ndarray:
    """Session::parseKeyframesInROI with keyframe_gap = 1: keep the query scans
    whose nearest central keyframe is within `thres` metres."""
    keep = []
    for i, p in enumerate(query_poses):
        if np.min(np.linalg.norm(central_poses - p, axis=1)) <= thres:
            keep.append(i)
    return np.array(keep, dtype=int)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bench-seq", required=True, help="benchmark seq dir holding gt_cloud.pcd")
    ap.add_argument("--sessions", required=True, help="the generated two-session root")
    ap.add_argument("--log", help="ltmapper.log, to cross-check the ROI keyframe count")
    ap.add_argument("--out", required=True, help="seq dir to write (gt_cloud.pcd inside)")
    ap.add_argument("--tol", type=float, default=0.05)
    ap.add_argument("--frames", choices=("both", "central"), default="both",
                    help="which input scans define coverage: both sessions (default) or the "
                         "central session alone. The central-only GT is the fair partner for "
                         "comparing one run's outputs with each other, since the raw map, the "
                         "map-side result and the scan-side result are all built from the "
                         "central session's scans.")
    args = ap.parse_args()

    meta = json.load(open(os.path.join(args.sessions, "sessions.json")))
    central_poses = poses_by_t(os.path.join(args.sessions, "central", "poses.txt"))
    query_poses = poses_by_t(os.path.join(args.sessions, "query", "poses.txt"))
    roi = roi_indices(central_poses, query_poses)

    if args.log and os.path.exists(args.log):
        txt = open(args.log, errors="replace").read()
        m = re.search(r"Total (\d+) keyframes parsed in the map's ROI", txt)
        got = int(m.group(1)) if m else None
        print(f"ROI recomputed from poses: {len(roi)} query keyframes; "
              f"ltremovert log reports {got} -> match={got == len(roi)}")
        if got is not None and got != len(roi):
            print("WARNING: ROI recomputation disagrees with the run", file=sys.stderr)

    # The union of the input scans the run actually consumed, in the world frame.
    # make_ltmapper_sessions.py renumbers the scans per session, so the source
    # benchmark frame names come from sessions.json (which records them in order).
    # The benchmark's world-frame clouds are used directly: a session-frame scan
    # plus its pose maps back to exactly this cloud (verified to 4e-6 m).
    src = os.path.join(args.bench_seq, "pcd")
    sessions_used = [("central", [meta["central"]["src_frames"][i]
                                  for i in range(meta["central"]["num_scans"])])]
    if args.frames == "both":
        sessions_used.append(("query", [meta["query"]["src_frames"][i] for i in roi]))
    chunks, n_used = [], 0
    for _name, names in sessions_used:
        for nm in names:
            chunks.append(read_pcd(os.path.join(src, nm))[:, :3])
            n_used += 1
    covered = np.concatenate(chunks)
    del chunks
    print(f"union of the {n_used} input scans: {len(covered)} points")

    gt = read_pcd(os.path.join(args.bench_seq, "gt_cloud.pcd"))
    labels = gt[:, 3].astype(np.int8)
    tree = cKDTree(covered.astype(np.float32))
    keep = np.zeros(len(gt), dtype=bool)
    step = 2_000_000
    for i in range(0, len(gt), step):
        d, _ = tree.query(gt[i:i + step, :3].astype(np.float32), k=1, workers=-1)
        keep[i:i + step] = d <= args.tol

    stat = labels == 0
    dyn = labels == 1
    cov = {"gt_total": int(len(gt)),
           "gt_static_total": int(stat.sum()), "gt_dynamic_total": int(dyn.sum()),
           "gt_static_covered": int((keep & stat).sum()),
           "gt_dynamic_covered": int((keep & dyn).sum()),
           "static_coverage_pct": round(100.0 * (keep & stat).sum() / max(stat.sum(), 1), 4),
           "dynamic_coverage_pct": round(100.0 * (keep & dyn).sum() / max(dyn.sum(), 1), 4)}

    os.makedirs(args.out, exist_ok=True)
    write_binary_pcd(os.path.join(args.out, "gt_cloud.pcd"), gt[keep])
    with open(os.path.join(args.out, "coverage.json"), "w") as fh:
        json.dump({"note": "GT restricted to points observed by the input scans ltremovert "
                           "actually consumed (coverage defined by input, not by output)",
                   "frames_used": args.frames,
                   "central_frames": meta["central"]["num_scans"],
                   "query_roi_frames": int(len(roi)) if args.frames == "both" else 0,
                   "tol_m": args.tol, **cov}, fh, indent=2)
    print(json.dumps(cov, indent=2))
    print(f"\nwrote {args.out}/gt_cloud.pcd with {int(keep.sum())} points")
    return 0


if __name__ == "__main__":
    sys.exit(main())
