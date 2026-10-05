#!/usr/bin/env python3
"""H1' part 3: are the false removals concentrated where observability is low?

The task book's parallel experiment (§6) has three parts. Two are done in 01-02
(the ranking table and the scatter). This is the third:

    "if rho < 0.9, show that the false positives come from low-observability
     regions"

Two things make this measurable without any new data.

1. **Every GT point can be scored for how often it *could* have been seen.**
   For each of the 141 frames we know the sensor pose (the PCD VIEWPOINT field,
   the same source make_kitti_seq.py inverts). A GT point was geometrically
   observable from frame k when it was inside the scan's range *and* inside the
   rotating lidar's vertical field of view. Counting those frames gives an
   integer observability score per GT point.

   The count is an **upper bound**: occlusion is not modelled, so a point behind
   a wall scores as observable if it was in range and in the vertical band. That
   is stated rather than hidden, and it is the honest direction for this test -
   an upper-bound observability makes the "low observability" stratum
   conservative, not generous.

2. **The benchmark's own evaluator already labels every GT point.** For a given
   cleaned map it writes a relabelled GT cloud where label 1 means "no point of
   the cleaned map lies within 0.05 m, i.e. this method dropped it". Those files
   exist for every map this workspace has scored.

So: bin the GT static points by observability, and per bin report how many the
method dropped. The benchmark's `uncleaned` map (voxelised to 0.2 m, dropping
*no* structure on purpose) is the control: its dropped labels are pure
downsampling. Any method whose curve sits above that control, especially in the
low-observability bins, is misclassifying rather than merely coarsening.

Usage:
    work/observability_strata.py --seq-dir <bench>/data/raw/00 \
        --maps maps.json --out results/observability_strata.json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

import numpy as np

MARK = b"DATA binary\n"
# KITTI's HDL-64E: +2 deg to -24.8 deg. Points outside that band cannot have
# been hit by any scan, whatever the method does afterwards.
FOV_TOP_DEG = 2.0
FOV_BOTTOM_DEG = -24.8
RANGE_M = 50.0

BINS = [(0, 0), (1, 4), (5, 19), (20, 49), (50, 99), (100, 10 ** 9)]
BIN_LABELS = ["0", "1-4", "5-19", "20-49", "50-99", "100+"]


def read_pcd(path, cols=None):
    """Binary PCD as float32 (x y z [intensity]); `cols` selects a subset."""
    with open(path, "rb") as fh:
        raw = fh.read()
    i = raw.find(MARK)
    if i < 0:
        raise ValueError(f"{path}: not a binary PCD")
    head = raw[:i].decode("ascii", "replace")
    n = int(re.search(r"POINTS (\d+)", head).group(1))
    fields = re.search(r"FIELDS (.*)", head).group(1).split()
    arr = np.frombuffer(raw[i + len(MARK): i + len(MARK) + n * 4 * len(fields)],
                        dtype=np.float32).reshape(-1, len(fields))
    if cols is not None:
        idx = [fields.index(c) for c in cols]
        arr = arr[:, idx]
    return arr


def read_viewpoints(seq_dir):
    """Sensor position per frame, from each PCD's VIEWPOINT field."""
    pcd_dir = os.path.join(seq_dir, "pcd")
    poses = []
    for f in sorted(os.listdir(pcd_dir)):
        if not f.endswith(".pcd"):
            continue
        with open(os.path.join(pcd_dir, f), "rb") as fh:
            head = fh.read(4096)
        head = head[: head.find(b"DATA")].decode("ascii", "replace")
        vp = [float(x) for x in re.search(r"VIEWPOINT (.*)", head).group(1).split()]
        poses.append(vp[:3])
    return np.asarray(poses, dtype=np.float64)


def observability(points, poses, chunk=2_000_000):
    """How many frames could have seen each point (range + vertical FOV)."""
    sin_top = np.sin(np.deg2rad(FOV_TOP_DEG))
    sin_bot = np.sin(np.deg2rad(FOV_BOTTOM_DEG))
    out = np.empty(len(points), dtype=np.int16)
    for start in range(0, len(points), chunk):
        stop = min(start + chunk, len(points))
        P = points[start:stop]
        count = np.zeros(len(P), dtype=np.int16)
        for t in poses:
            d = P - t
            r2 = np.einsum("ij,ij->i", d, d)
            ok = r2 <= RANGE_M * RANGE_M
            if not ok.any():
                continue
            r = np.sqrt(r2, where=ok, out=np.full_like(r2, np.inf))
            dz = d[:, 2]
            ok &= (dz <= r * sin_top) & (dz >= r * sin_bot)
            count += ok
        out[start:stop] = count
        print(f"    observability: {stop:,}/{len(points):,}", flush=True)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seq-dir", required=True)
    ap.add_argument("--maps", required=True,
                    help="JSON: {display name: path to the evaluator's *_exportGT.pcd}")
    ap.add_argument("--out", required=True)
    ap.add_argument("--gt", default=None, help="default: <seq-dir>/gt_cloud.pcd")
    ap.add_argument("--control", default=None,
                    help="map name to use as the density baseline; per-bin excess is then "
                         "reported for every other map (excess isolates deletions that are "
                         "NOT explained by voxel downsampling)")
    ap.add_argument("--figure", default=None, help="write a PNG of the strata")
    args = ap.parse_args()

    gt_path = args.gt or os.path.join(args.seq_dir, "gt_cloud.pcd")
    print(f"[strata] GT: {gt_path}")
    gt = read_pcd(gt_path, cols=["x", "y", "z", "intensity"])
    pts = gt[:, :3].astype(np.float64)
    gt_label = gt[:, 3].astype(np.int32)
    static = gt_label == 0
    print(f"[strata] {len(gt):,} GT points, {int(static.sum()):,} static")

    poses = read_viewpoints(args.seq_dir)
    print(f"[strata] {len(poses)} frame poses, "
          f"FOV {FOV_TOP_DEG}..{FOV_BOTTOM_DEG} deg, range {RANGE_M} m")

    obs = observability(pts, poses)
    np.save(os.path.join(os.path.dirname(os.path.abspath(args.out)),
                         "observability_counts.npy"), obs)
    hist = [int(np.count_nonzero((obs >= lo) & (obs <= hi))) for lo, hi in BINS]
    print("[strata] observability histogram (all GT points): "
          + ", ".join(f"{lab}: {h:,}" for lab, h in zip(BIN_LABELS, hist)))

    static_idx = np.flatnonzero(static)
    obs_static = obs[static_idx]
    static_bins = [(obs_static >= lo) & (obs_static <= hi) for lo, hi in BINS]
    n_static_per_bin = [int(m.sum()) for m in static_bins]

    with open(args.maps, encoding="utf-8") as fh:
        maps = json.load(fh)

    out = {
        "protocol": {
            "gt": os.path.abspath(gt_path),
            "frames": len(poses),
            "observability": "number of frames whose range (<= %.0f m) and vertical FOV "
                             "(%.1f..%.1f deg) contain the point; occlusion NOT modelled, so "
                             "this is an upper bound" % (RANGE_M, FOV_TOP_DEG, FOV_BOTTOM_DEG),
            "dropped_label": "the benchmark evaluator's exportGT output: 1 = no map point "
                             "within 0.05 m, i.e. the method dropped that GT point",
            "bin_edges": [b[0] for b in BINS] + ["inf"],
            "bin_labels": BIN_LABELS,
        },
        "observability_histogram_all_gt": dict(zip(BIN_LABELS, hist)),
        "static_points_per_bin": dict(zip(BIN_LABELS, n_static_per_bin)),
        "maps": {},
    }

    for name, path in maps.items():
        if not os.path.exists(path):
            print(f"[strata] skip {name}: {path} missing")
            continue
        lab = read_pcd(path, cols=["intensity"])[:, 0].astype(np.int32)
        if len(lab) != len(gt):
            print(f"[strata] skip {name}: {len(lab)} labels vs {len(gt)} GT points")
            continue
        dropped = lab[static_idx] == 1
        row = {}
        for bin_lab, m in zip(BIN_LABELS, static_bins):
            n = int(m.sum())
            d = int(dropped[m].sum())
            row[bin_lab] = {
                "static_points": n,
                "dropped": d,
                "false_removal_pct": round(100.0 * d / n, 4) if n else None,
            }
        row["_total"] = {
            "static_points": int(static.sum()),
            "dropped": int(dropped.sum()),
            "false_removal_pct": round(100.0 * dropped.sum() / static.sum(), 4),
        }
        out["maps"][name] = row
        print(f"[strata] {name:20s} overall {row['_total']['false_removal_pct']:6.2f}%  "
              + "  ".join(f"{b}:{row[b]['false_removal_pct']:.1f}%" for b in BIN_LABELS
                          if row[b]["false_removal_pct"] is not None))

    # ---------------------------------------------------------------- excess
    # The dropped-label rate rises with observability for EVERY map, control
    # included, because observability correlates with point density and the
    # evaluator's 0.05 m rule reads downsampling as deletion. Subtracting the
    # control per bin leaves the deletions that downsampling cannot explain -
    # which is the quantity H1' part 3 is actually about.
    if args.control and args.control in out["maps"]:
        ctrl = out["maps"][args.control]
        for name, row in out["maps"].items():
            excess = {}
            for b in BIN_LABELS:
                a, c = row[b]["false_removal_pct"], ctrl[b]["false_removal_pct"]
                excess[b] = None if (a is None or c is None) else round(a - c, 4)
            row["excess_vs_control_pp"] = excess
        out["protocol"]["control"] = args.control

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, ensure_ascii=False)
    print(f"[strata] wrote {args.out}")

    if args.figure:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        # Two regimes, so two panels. The maps as submitted keep their own
        # resolutions and most of them lose almost no static points, so what is
        # left there is genuine misclassification. The 0.2 m group has been
        # voxelised by us, so its curve is dominated by density - that is what
        # the control line is for. Grouping is by the caller's own naming
        # convention ("as submitted" in the map label).
        groups = [
            ("normalised to 0.2 m (density regime)", [n for n in out["maps"] if "as submitted" not in n]),
            ("as submitted (their own resolutions)", [n for n in out["maps"] if "as submitted" in n]),
        ]
        fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.4))
        x = range(len(BIN_LABELS))
        for ax, (title, names) in zip(axes, groups):
            for name in names:
                row = out["maps"][name]
                ys = [row[b]["false_removal_pct"] for b in BIN_LABELS]
                style = dict(marker="o", lw=2.6, ls="--", color="0.35", zorder=3) \
                    if name == args.control else dict(marker="o", lw=1.8)
                ax.plot(x, ys, label=name.replace(" (as submitted)", ""), **style)
            ax.set_xticks(list(x))
            ax.set_xticklabels(BIN_LABELS)
            ax.set_xlabel("observability  [frames that could have seen the point]")
            ax.set_ylabel("static GT points dropped  [%]")
            ax.set_title(title)
            ax.grid(alpha=0.3)
            ax.legend(fontsize=8)
        fig.suptitle("H1' part 3: where do the false removals come from? "
                     "(dashed grey = the density control)", fontsize=11)
        fig.tight_layout()
        fig.savefig(args.figure, dpi=140)
        print(f"[strata] wrote {args.figure}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
