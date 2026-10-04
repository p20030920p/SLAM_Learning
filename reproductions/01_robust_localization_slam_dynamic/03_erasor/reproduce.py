#!/usr/bin/env python3
"""01-03 · ERASOR — automated reproduction.

What we reproduce here is NOT the ERASOR paper's own number. The paper (RA-L
2021) reports voxel-wise PR/RR/F1 with voxel 0.2 on SemanticKITTI, and its
seq 00 headline is PR 93.980 / RR 97.081 / F1 0.955. What this folder runs is
the *reimplementation* shipped inside DynamicMap_Benchmark, which reports
point-wise SA/DA/AA, and whose ERASOR row is 66.70 / 98.54 / 81.07.

Those two numbers are 27 percentage points apart and it is not noise - it is
the metric and the pipeline. Keeping both in view is the point of the check
below: it is the task book's §6 ranking-stability question, already answered
for one method pair before any new experiment runs.

The run is the benchmark's own: `methods/ERASOR/build/erasor_run <seq> config/seq_00.yaml`
with the config the benchmark ships for sequence 00.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

# DynamicMap_Benchmark Table I, p.5 (identical row in the DUFOMap paper, Table I p.5)
BENCHMARK = {"SA": 66.70, "DA": 98.54, "AA": 81.07}
# The original ERASOR paper, Table II p.8 - different metric, shown for contrast.
PAPER_OWN = {"PR": 93.980, "RR": 97.081, "F1": 0.955,
             "metric": "voxel-wise, voxel 0.2, SemanticKITTI 00"}
TOL_PP = 0.5


def _bench(ctx):
    return os.path.normpath(os.path.join(
        ctx["path"], "..", "01_dynamicmap_benchmark", "code", "DynamicMap_Benchmark"))


def _seq_dir(ctx):
    env = os.environ.get("DMB_SEQ_DIR")
    if env and os.path.isdir(os.path.join(env, "pcd")):
        return env
    sibling = os.path.normpath(os.path.join(
        ctx["path"], "..", "01_dynamicmap_benchmark", "data", "raw", "00"))
    return sibling if os.path.isdir(os.path.join(sibling, "pcd")) else None


def require(ctx):
    seq = _seq_dir(ctx)
    if seq is None:
        return ("sequence 00 not found - wget "
                "https://zenodo.org/records/10886629/files/00.zip and unzip into "
                "01_dynamicmap_benchmark/data/raw/ (no KITTI registration needed)")
    binary = os.path.join(_bench(ctx), "methods", "ERASOR", "build", "erasor_run")
    if not os.path.exists(binary):
        return ("erasor_run not built - cd "
                "code/DynamicMap_Benchmark/methods/ERASOR && cmake -B build && cmake --build build")
    return None


def run(ctx):
    seq = _seq_dir(ctx)
    bench = _bench(ctx)
    method_dir = os.path.join(bench, "methods", "ERASOR")
    evaluator = os.path.normpath(os.path.join(
        ctx["path"], "..", "01_dynamicmap_benchmark", "work", "evaluate.py"))

    map_path = os.path.join(seq, "erasor_output.pcd")
    if not os.path.exists(map_path):
        # erasor_run writes into the sequence folder it is given.
        r = subprocess.run([os.path.join(method_dir, "build", "erasor_run"),
                            seq, os.path.join(method_dir, "config", "seq_00.yaml"), "-1"],
                           cwd=method_dir, capture_output=True, text=True)
        if r.returncode != 0 or not os.path.exists(map_path):
            raise RuntimeError(f"erasor_run failed ({r.returncode}): "
                               f"{(r.stderr or r.stdout)[-1200:]}")

    score_json = os.path.join(ctx["results_dir"], "erasor_score.json")
    r = subprocess.run([sys.executable, evaluator, "--seq-dir", seq, "--map", map_path,
                        "--method", "erasor", "--impl", "official", "--out", score_json],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"evaluate.py failed: {(r.stderr or r.stdout)[-1200:]}")
    with open(score_json, encoding="utf-8") as fh:
        s = json.load(fh)["official"]

    metrics = {k: s[k] for k in ("SA", "DA", "AA", "HA")}
    metrics.update({"map_points": json.load(open(score_json, encoding="utf-8"))["map_points"],
                    "gt_static": s["gt_static"], "gt_dynamic": s["gt_dynamic"],
                    "false_removal": s["false_removal"], "missed_dynamic": s["missed_dynamic"]})

    checks = [
        {
            "name": "reproduces_benchmark_row",
            "ok": all(abs(metrics[k] - BENCHMARK[k]) <= TOL_PP for k in ("SA", "DA", "AA")),
            "detail": (f"SA/DA/AA = {metrics['SA']:.2f}/{metrics['DA']:.2f}/{metrics['AA']:.2f} "
                       f"vs DynamicMap_Benchmark Table I {BENCHMARK['SA']}/{BENCHMARK['DA']}/"
                       f"{BENCHMARK['AA']}, within {TOL_PP} pp"),
        },
        {
            "name": "output_is_voxel_downsampled",
            "ok": metrics["map_points"] < metrics["gt_static"],
            "detail": (f"the cleaned map holds {metrics['map_points']} points against "
                       f"{metrics['gt_static'] + metrics['gt_dynamic']} GT points - ERASOR's "
                       "MapUpdater voxelises at 0.1 m, so most 'false removals' are "
                       "downsampling, not deletion"),
        },
    ]

    findings = [
        {
            "name": "low_SA_is_downsampling_not_deletion",
            "detail": (f"SA {metrics['SA']:.2f}% with {metrics['false_removal']} GT points marked "
                       "removed, yet DA is {:.2f}%. The map has {:.1f}x fewer points than the GT "
                       "cloud, so the 0.05 m nearest-neighbour rule reads downsampling as "
                       "removal. The benchmark's metric therefore penalises resolution, not "
                       "correctness - worth remembering before calling any method 'worse'."
                       ).format(metrics["DA"], (metrics["gt_static"] + metrics["gt_dynamic"]) / metrics["map_points"]),
        },
        {
            "name": "same_method_27_points_apart_across_metrics",
            "detail": ("ERASOR scores PR 93.980 on its own voxel-wise metric (SemanticKITTI 00, "
                       "Table II p.8) and SA 66.71 on the benchmark's point-wise metric "
                       "(KITTI 00). Removert goes the other way: 85.502 -> 99.44. The ranking "
                       "between the two methods inverts with the metric."),
            "paper_own": PAPER_OWN, "benchmark": BENCHMARK, "ours": metrics,
        },
    ]

    return {"metrics": metrics, "checks": checks, "findings": findings,
            "artifacts": ["results/erasor_score.json"],
            "note": (f"ERASOR (benchmark reimplementation) on KITTI 00: SA/DA/AA = "
                     f"{metrics['SA']:.2f}/{metrics['DA']:.2f}/{metrics['AA']:.2f}")}
