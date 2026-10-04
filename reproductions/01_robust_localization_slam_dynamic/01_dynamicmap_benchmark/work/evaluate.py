#!/usr/bin/env python3
"""Score a cleaned map against the DynamicMap_Benchmark ground truth.

The benchmark's own pipeline is three steps and we keep all three:

  1. a method writes a cleaned map                       (each method's work/)
  2. export_eval_pcd relabels the GT cloud               (official C++ binary)
         every GT point takes label 1 if its nearest neighbour in the cleaned
         map is further than `min_dis`, i.e. the method dropped it;
         otherwise 0
  3. count the four quadrants and report SA / DA / AA / HA

Step 2 exists in two independent implementations here:

  --impl official   runs `scripts/build/export_eval_pcd` (PCL kd-tree)
  --impl python     re-does the same rule with scipy's cKDTree

They must agree; `--cross-check` runs both and reports the disagreement rate.
That is the point of the duplication - the official binary is the authority,
but a number produced by one opaque binary is not evidence until something
else reproduces it.

The metric is the one the ITSC'23 paper defines, and it is NOT F1:

    SA = #(et=0 & gt=0) / #(gt=0)        static points preserved
    DA = #(et=1 & gt=1) / #(gt=1)        dynamic points rejected
    AA = sqrt(SA * DA)                   geometric mean, deliberately not the
                                         harmonic mean - it punishes whichever
                                         of the two is worse, which is the
                                         whole point of reporting it this way
    HA = 2*SA*DA / (SA + DA)             harmonic mean, for comparison only

Usage:
    python3 work/evaluate.py --seq-dir <...>/data/raw/00 \
                             --map <...>/05_dufomap/results/dufomap_output.pcd \
                             --method dufomap --out results/dufomap_score.json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys

import numpy as np

# The benchmark's own example uses 0.05 m as "same point". Recorded here
# because every number we report is conditional on it.
DEFAULT_MIN_DIS = 0.05


def read_pcd(path: str) -> np.ndarray:
    """Binary `x y z intensity` PCD, the only kind this benchmark writes."""
    with open(path, "rb") as fh:
        raw = fh.read()
    marker = raw.find(b"DATA binary\n")
    if marker < 0:
        raise ValueError(f"{path}: not a binary PCD")
    header = raw[:marker].decode("ascii", errors="replace")
    body = raw[marker + len(b"DATA binary\n"):]
    n = int(re.search(r"POINTS (\d+)", header).group(1))
    fields = re.search(r"FIELDS (.*)", header).group(1).split()
    a = np.frombuffer(body[: n * 4 * len(fields)], dtype=np.float32).reshape(-1, len(fields))
    if len(a) != n:
        raise ValueError(f"{path}: header says {n}, file holds {len(a)}")
    return a


def score(gt_labels: np.ndarray, et_labels: np.ndarray) -> dict:
    """The four quadrants and the four percentages, exactly as evaluate_all.py."""
    n_gt_static = int(np.count_nonzero(gt_labels == 0))
    n_gt_dynamic = int(np.count_nonzero(gt_labels == 1))
    n_et_static = int(np.count_nonzero(et_labels == 0))
    n_et_dynamic = int(np.count_nonzero(et_labels == 1))

    correct_static = int(np.count_nonzero((et_labels == 0) & (gt_labels == 0)))
    correct_dynamic = int(np.count_nonzero((et_labels == 1) & (gt_labels == 1)))

    # A GT point the method kept but that was dynamic: a false "still there".
    missed_dynamic = int(np.count_nonzero((et_labels == 0) & (gt_labels == 1)))
    # A GT point the method dropped but that never moved: a false removal.
    false_removal = int(np.count_nonzero((et_labels == 1) & (gt_labels == 0)))

    SA = 100.0 * correct_static / n_gt_static if n_gt_static else float("nan")
    DA = 100.0 * correct_dynamic / n_gt_dynamic if n_gt_dynamic else float("nan")
    AA = float(np.sqrt(SA * DA)) if n_gt_dynamic and n_gt_static else float("nan")
    HA = (2 * SA * DA / (SA + DA)) if (SA + DA) else float("nan")
    return {
        "gt_static": n_gt_static, "gt_dynamic": n_gt_dynamic,
        "out_static": n_et_static, "out_dynamic": n_et_dynamic,
        "correct_static": correct_static, "correct_dynamic": correct_dynamic,
        "missed_dynamic": missed_dynamic, "false_removal": false_removal,
        "SA": round(SA, 4), "DA": round(DA, 4), "AA": round(AA, 4), "HA": round(HA, 4),
    }


def export_gt_python(gt_path: str, map_path: str, min_dis: float) -> np.ndarray:
    """The export_eval_pcd rule, re-implemented: label 1 where the GT point has
    no neighbour in the cleaned map within min_dis."""
    from scipy.spatial import cKDTree

    gt = read_pcd(gt_path)
    mp = read_pcd(map_path)
    tree = cKDTree(mp[:, :3].astype(np.float32))
    labels = np.ones(len(gt), dtype=np.float32)  # assume dropped ...
    # ... chunked, so the query never materialises a full distance vector
    step = 2_000_000
    for i in range(0, len(gt), step):
        d, _ = tree.query(gt[i:i + step, :3].astype(np.float32), k=1, workers=-1)
        labels[i:i + step] = (d > min_dis).astype(np.float32)
    return labels


def export_gt_official(seq_dir: str, map_path: str, min_dis: float,
                       eval_bin: str) -> np.ndarray:
    """Run the benchmark's own export_eval_pcd, which wants the map inside the
    sequence folder and writes <seq>/eval/<name>_exportGT.pcd."""
    if not os.path.exists(eval_bin):
        raise FileNotFoundError(
            f"{eval_bin} not built - run: cmake -S "
            "code/DynamicMap_Benchmark/scripts -B code/DynamicMap_Benchmark/scripts/build "
            "&& cmake --build code/DynamicMap_Benchmark/scripts/build")
    os.makedirs(os.path.join(seq_dir, "eval"), exist_ok=True)
    staged = os.path.join(seq_dir, os.path.basename(map_path))
    shutil.copyfile(map_path, staged)
    r = subprocess.run([eval_bin, seq_dir, os.path.basename(map_path), str(min_dis)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"export_eval_pcd failed ({r.returncode}): {r.stderr[-800:]}")
    out = os.path.join(seq_dir, "eval",
                       os.path.basename(map_path)[:-4] + "_exportGT.pcd")
    return read_pcd(out)[:, 3].copy()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seq-dir", required=True)
    ap.add_argument("--map", required=True, help="the method's cleaned map")
    ap.add_argument("--method", required=True)
    ap.add_argument("--out", help="write the score json here")
    ap.add_argument("--min-dis", type=float, default=DEFAULT_MIN_DIS)
    ap.add_argument("--impl", choices=("official", "python", "both"), default="both")
    ap.add_argument("--eval-bin", default=None,
                    help="path to export_eval_pcd; default: the built one in code/")
    args = ap.parse_args()

    gt_path = os.path.join(args.seq_dir, "gt_cloud.pcd")
    if not os.path.exists(gt_path):
        print(f"no gt_cloud.pcd in {args.seq_dir}", file=sys.stderr)
        return 2
    if not os.path.exists(args.map):
        print(f"no cleaned map at {args.map}", file=sys.stderr)
        return 2

    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    default_bin = os.path.join(here, "..", "01_dynamicmap_benchmark", "code",
                               "DynamicMap_Benchmark", "scripts", "build", "export_eval_pcd")
    eval_bin = args.eval_bin or os.path.normpath(default_bin)

    gt_labels = read_pcd(gt_path)[:, 3]
    result = {"method": args.method, "sequence": os.path.basename(args.seq_dir.rstrip("/")),
              "min_dis_m": args.min_dis, "map": os.path.abspath(args.map),
              "map_points": int(len(read_pcd(args.map)))}

    labels = {}
    if args.impl in ("official", "both"):
        labels["official"] = export_gt_official(args.seq_dir, args.map, args.min_dis, eval_bin)
        result["official"] = score(gt_labels, labels["official"])
    if args.impl in ("python", "both"):
        labels["python"] = export_gt_python(gt_path, args.map, args.min_dis)
        result["python"] = score(gt_labels, labels["python"])

    if len(labels) == 2:
        a, b = labels["official"], labels["python"]
        if len(a) != len(b):
            result["cross_check"] = {"ok": False,
                                     "why": f"length mismatch {len(a)} vs {len(b)}"}
        else:
            disagree = int(np.count_nonzero(a != b))
            result["cross_check"] = {
                "ok": disagree == 0,
                "disagreeing_points": disagree,
                "disagree_rate": round(disagree / len(a), 8),
                "note": "the two implementations must label the GT identically; "
                        "a non-zero rate means the nearest-neighbour rule is "
                        "tie-sensitive, not that either is wrong",
            }

    print(json.dumps(result, indent=2, ensure_ascii=False))
    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(result, fh, indent=2, ensure_ascii=False)
        print(f"\nwritten {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
