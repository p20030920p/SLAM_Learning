#!/usr/bin/env python3
"""01-04 · Removert — automated reproduction.

We do not have Removert's own paper. Its IROS 2020 original is closed access -
OpenAlex reports is_oa false, oa_status closed, no repository fulltext - and the
only mirror the authors link (irap.kaist.ac.kr) no longer resolves. So what this
folder reproduces is the *reimplementation* shipped inside DynamicMap_Benchmark,
whose Removert row is 99.44 / 41.53 / 64.26. That row is also what the DUFOMap
paper prints for Removert, so it is at least doubly attested.

If the original PDF is ever obtained, its numbers go in paper_baseline.md and
this target has to be revisited - Removert's own paper reports voxel-wise
PR/RR, which is a different metric entirely (see 01-03 for how far apart the
two can be for the same method).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

# DynamicMap_Benchmark Table I, p.5; identical row in DUFOMap Table I, p.5
BENCHMARK = {"SA": 99.44, "DA": 41.53, "AA": 64.26}
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
    binary = os.path.join(_bench(ctx), "methods", "removert", "build", "removert_run")
    if not os.path.exists(binary):
        return ("removert_run not built - cd "
                "code/DynamicMap_Benchmark/methods/removert && cmake -B build && cmake --build build")
    return None


def run(ctx):
    seq = _seq_dir(ctx)
    method_dir = os.path.join(_bench(ctx), "methods", "removert")
    evaluator = os.path.normpath(os.path.join(
        ctx["path"], "..", "01_dynamicmap_benchmark", "work", "evaluate.py"))

    map_path = os.path.join(seq, "removert_output.pcd")
    if not os.path.exists(map_path):
        r = subprocess.run([os.path.join(method_dir, "build", "removert_run"),
                            seq, os.path.join(method_dir, "config", "params_kitti.yaml"), "-1"],
                           cwd=method_dir, capture_output=True, text=True)
        if r.returncode != 0 or not os.path.exists(map_path):
            raise RuntimeError(f"removert_run failed ({r.returncode}): "
                               f"{(r.stderr or r.stdout)[-1200:]}")

    score_json = os.path.join(ctx["results_dir"], "removert_score.json")
    r = subprocess.run([sys.executable, evaluator, "--seq-dir", seq, "--map", map_path,
                        "--method", "removert", "--impl", "official", "--out", score_json],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"evaluate.py failed: {(r.stderr or r.stdout)[-1200:]}")
    with open(score_json, encoding="utf-8") as fh:
        payload = json.load(fh)
    s = payload["official"]

    metrics = {k: s[k] for k in ("SA", "DA", "AA", "HA")}
    metrics.update({"map_points": payload["map_points"],
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
            # Both papers report Removert as the extreme case on this axis; if it
            # ever stops being one, the reproduction target itself has moved.
            "name": "removert_is_the_conservative_extreme",
            "ok": metrics["SA"] > 99.0 and metrics["DA"] < 50.0,
            "detail": (f"SA {metrics['SA']:.2f}% with only DA {metrics['DA']:.2f}% - it keeps "
                       f"essentially the whole map ({metrics['missed_dynamic']} dynamic GT points "
                       "left in) rather than risk deleting static structure"),
        },
    ]

    findings = [
        {
            "name": "original_paper_is_unobtainable",
            "detail": ("Removert's IROS 2020 paper is closed access: OpenAlex returns "
                       "is_oa=false, oa_status=closed, any_repository_has_fulltext=false, and "
                       "the authors' own link (irap.kaist.ac.kr) fails DNS. So the target here "
                       "is the benchmark's reimplementation, not Removert's self-reported "
                       "numbers - the only folder in this repo where that is true."),
        },
        {
            "name": "the_two_extremes_disagree_about_what_good_means",
            "detail": (f"Removert SA {metrics['SA']:.2f} / DA {metrics['DA']:.2f} against ERASOR's "
                       "66.71 / 98.54 on the same data and the same metric. They are opposite "
                       "corners: one refuses to delete, the other deletes too much. AA ranks "
                       "them DUFOMap > ERASOR > Removert, SA ranks them Removert > DUFOMap > "
                       "ERASOR - the task book's ranking-stability question, answered on real "
                       "numbers."),
        },
    ]

    return {"metrics": metrics, "checks": checks, "findings": findings,
            "artifacts": ["results/removert_score.json"],
            "note": (f"Removert (benchmark reimplementation) on KITTI 00: SA/DA/AA = "
                     f"{metrics['SA']:.2f}/{metrics['DA']:.2f}/{metrics['AA']:.2f}")}
