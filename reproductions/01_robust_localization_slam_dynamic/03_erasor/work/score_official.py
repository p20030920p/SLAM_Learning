#!/usr/bin/env python3
"""Score one PCD with ERASOR's own PR/RR metric, as JSON.

Upstream ships `scripts/analysis_runner.py`, which prints an orgtbl and nothing
machine-readable. This wrapper imports that file (no copy, no re-implementation)
and dumps the same numbers as JSON so the reproduction driver can backtest them.

Usage:
    work/score_official.py --runner <ERASOR>/scripts/analysis_runner.py \
                           --gt <gt.pcd> --est <est.pcd> --out <score.json>
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys


def load(path):
    spec = importlib.util.spec_from_file_location("erasor_analysis_runner", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runner", required=True, help="upstream scripts/analysis_runner.py")
    ap.add_argument("--gt", required=True)
    ap.add_argument("--est", required=True)
    ap.add_argument("--voxelsize", type=float, default=0.2)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    for p in (args.runner, args.gt, args.est):
        if not os.path.isfile(p):
            print(f"missing: {p}", file=sys.stderr)
            return 2

    runner = load(args.runner)
    gt_xyz, gt_int = runner.read_pcd_ascii(args.gt)
    est_xyz, est_int = runner.read_pcd_ascii(args.est)
    r = runner.evaluate(gt_xyz, runner.labels(gt_int),
                        est_xyz, runner.labels(est_int),
                        voxelsize=args.voxelsize)

    payload = {
        "gt": os.path.abspath(args.gt),
        "est": os.path.abspath(args.est),
        "voxelsize_m": args.voxelsize,
        **{k: (round(v, 6) if isinstance(v, float) else v) for k, v in r.items()},
        "metric_source": "ERASOR scripts/analysis_runner.py (the authors' own PR/RR evaluator)",
    }
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
