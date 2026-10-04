#!/usr/bin/env python3
"""01-05 · DUFOMap — automated reproduction.

The paper (RA-L 2024) reports, on KITTI sequence 00, SA / DA / AA =
97.96 / 98.72 / 98.34 for DUFOMap in its default configuration, and its
ablation table states that default as voxel 0.1 m, d_s = 0.2 m, **d_p = 1**.

The benchmark repository this reproduction borrows its data from ships
`methods/dufomap/main.py`, which constructs `dufomap(0.1, 0.2, 2)` and labels
those arguments "same with paper". They are not: `d_p` is 1 in the paper.
Rather than pick one, this runs both, because the size of the discrepancy is
itself the result - it tells us how much of a reproduction hinges on a single
integer that the upstream example gets wrong.

    d_p = 1   the paper's default and the configuration whose numbers we
              claim to reproduce -> the acceptance criterion
    d_p = 2   what the benchmark's example actually passes -> recorded so the
              difference is documented with numbers instead of an assertion

`checks` are the invariants. `findings` are measurements about the data and
the tooling, and never gate the run.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

# The paper's headline row: Table I, p.5, "KITTI small town (00)", DUFOMap.
PAPER = {"SA": 97.96, "DA": 98.72, "AA": 98.34}
# Tolerance in percentage points. The paper prints two decimals, so anything
# looser than a few tenths would stop being a reproduction claim.
TOL_PP = 0.5


def _venv_python(ctx):
    """The interpreter that can import dufomap.

    dufomap is a compiled extension installed in the shared venv (see
    reproductions/README.md); the driver itself runs under the system python.
    """
    cand = os.path.join(ctx["repo_root"], "reproductions", ".venvs", "dmb", "bin", "python")
    return cand if os.path.exists(cand) else sys.executable


def _seq_dir(ctx):
    """Where sequence 00 lives.

    It belongs to 01-01 - the benchmark owns the data, the methods borrow it -
    so a local copy wins, then the sibling folder, then $DMB_SEQ_DIR.
    """
    env = os.environ.get("DMB_SEQ_DIR")
    if env and os.path.isdir(os.path.join(env, "pcd")):
        return env
    local = os.path.join(ctx["data_root"], "00")
    if os.path.isdir(os.path.join(local, "pcd")):
        return local
    sibling = os.path.normpath(os.path.join(
        ctx["path"], "..", "01_dynamicmap_benchmark", "data", "raw", "00"))
    if os.path.isdir(os.path.join(sibling, "pcd")):
        return sibling
    return None


def require(ctx):
    seq = _seq_dir(ctx)
    if seq is None:
        return ("sequence 00 not found - download the benchmark's teaser data: "
                "wget https://zenodo.org/records/10886629/files/00.zip and unzip it "
                "into 01_dynamicmap_benchmark/data/raw/ (no KITTI registration needed)")
    py = _venv_python(ctx)
    probe = subprocess.run([py, "-c", "import dufomap"], capture_output=True, text=True)
    if probe.returncode != 0:
        return (f"dufomap not importable under {py} - "
                "python3 -m venv --without-pip reproductions/.venvs/dmb && "
                "reproductions/.venvs/dmb/bin/python /tmp/get-pip.py -r requirements, "
                "see reproductions/README.md")
    return None


def _run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        raise RuntimeError(f"{' '.join(map(str, cmd))} failed ({r.returncode}): "
                           f"{(r.stderr or r.stdout)[-1200:]}")
    return r


def run(ctx):
    seq = _seq_dir(ctx)
    py = _venv_python(ctx)
    out_dir = os.path.join(ctx["path"], "data", "output")
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(ctx["results_dir"], exist_ok=True)

    runner = os.path.join(ctx["work_dir"], "run_dufomap.py")
    evaluator = os.path.normpath(os.path.join(
        ctx["path"], "..", "01_dynamicmap_benchmark", "work", "evaluate.py"))

    scores = {}
    for label, dp in (("paper_default_dp1", 1), ("benchmark_example_dp2", 2)):
        mp = os.path.join(out_dir, f"dufomap_output_{label}.pcd")
        if not os.path.exists(mp):
            _run([py, runner, "--seq-dir", seq, "--out", mp, "--d-p", str(dp)])
        sj = os.path.join(ctx["results_dir"], f"dufomap_score_{label}.json")
        _run([sys.executable, evaluator, "--seq-dir", seq, "--map", mp,
              "--method", f"dufomap_{label}", "--impl", "official", "--out", sj])
        with open(sj, encoding="utf-8") as fh:
            scores[label] = json.load(fh)

    main = scores["paper_default_dp1"]["official"]
    alt = scores["benchmark_example_dp2"]["official"]

    metrics = {
        "SA": main["SA"], "DA": main["DA"], "AA": main["AA"], "HA": main["HA"],
        "gt_static": main["gt_static"], "gt_dynamic": main["gt_dynamic"],
        "map_points": scores["paper_default_dp1"]["map_points"],
        "SA_dp2": alt["SA"], "DA_dp2": alt["DA"], "AA_dp2": alt["AA"],
        "map_points_dp2": scores["benchmark_example_dp2"]["map_points"],
    }

    checks = [
        {
            "name": "reproduces_paper_headline",
            "ok": all(abs(metrics[k] - PAPER[k]) <= TOL_PP for k in ("SA", "DA", "AA")),
            "detail": (f"d_p=1 gives SA/DA/AA = {metrics['SA']:.2f}/{metrics['DA']:.2f}/"
                       f"{metrics['AA']:.2f} vs paper {PAPER['SA']}/{PAPER['DA']}/"
                       f"{PAPER['AA']} (Table I p.5), within {TOL_PP} pp"),
        },
        {
            "name": "gt_is_binary_and_rare_dynamic",
            "ok": (main["gt_static"] + main["gt_dynamic"] > 0
                   and metrics["gt_dynamic"] / (metrics["gt_static"] + metrics["gt_dynamic"]) < 0.02),
            "detail": (f"GT = {main['gt_static']} static + {main['gt_dynamic']} dynamic points "
                       f"({100.0 * metrics['gt_dynamic'] / (main['gt_static'] + metrics['gt_dynamic']):.2f}% dynamic) "
                       "- a rare-positive problem, so AA is dominated by SA"),
        },
        {
            # The two configurations must actually differ, otherwise the d_p
            # comparison below is measuring nothing.
            "name": "dp_is_load_bearing",
            "ok": abs(metrics["SA_dp2"] - metrics["SA"]) > 0.5,
            "detail": (f"d_p=2 keeps {metrics['SA_dp2'] - metrics['SA']:+.2f} pp more static and "
                       f"removes {metrics['DA_dp2'] - metrics['DA']:+.2f} pp fewer dynamic points "
                       "than the paper's d_p=1"),
        },
    ]

    findings = [
        {
            "name": "upstream_example_contradicts_the_paper",
            "detail": ("DynamicMap_Benchmark's methods/dufomap/main.py passes d_p=2 with the "
                       "comment 'same with paper', but the DUFOMap paper's default - the one "
                       "whose Table I row we reproduce - is d_p=1 (Table IV, p.7). Using the "
                       "example's value reproduces AA only by coincidence; SA and DA are each "
                       "off by about 2 pp."),
        },
        {
            "name": "geometric_mean_hides_the_sa_da_tradeoff",
            "detail": (f"d_p=1 -> SA {metrics['SA']:.2f} / DA {metrics['DA']:.2f} / AA {metrics['AA']:.2f}; "
                       f"d_p=2 -> SA {metrics['SA_dp2']:.2f} / DA {metrics['DA_dp2']:.2f} / "
                       f"AA {metrics['AA_dp2']:.2f}. The two AA values are "
                       f"{abs(metrics['AA_dp2'] - metrics['AA']):.2f} pp apart while SA and DA each "
                       "move ~2 pp in opposite directions - the geometric mean of a "
                       "rare-positive problem is almost entirely SA, so it cannot tell a "
                       "conservative cleaner from an aggressive one."),
            "AA_dp1": metrics["AA"], "AA_dp2": metrics["AA_dp2"],
        },
        {
            "name": "dynamic_points_are_0_55_percent_of_the_map",
            "detail": (f"{metrics['gt_dynamic']} of {metrics['gt_static'] + metrics['gt_dynamic']} "
                       "GT points are dynamic; any metric averaged over points is therefore "
                       "a static-preservation metric in disguise."),
        },
    ]

    return {
        "metrics": metrics,
        "checks": checks,
        "findings": findings,
        "artifacts": [
            os.path.relpath(os.path.join(ctx["results_dir"], f"dufomap_score_{k}.json"), ctx["path"])
            for k in ("paper_default_dp1", "benchmark_example_dp2")
        ],
        "note": (f"DUFOMap on KITTI 00: SA/DA/AA = {metrics['SA']:.2f}/{metrics['DA']:.2f}/"
                 f"{metrics['AA']:.2f} vs paper {PAPER['SA']}/{PAPER['DA']}/{PAPER['AA']}"),
    }
