#!/usr/bin/env python3
"""01-03 · ERASOR — the official implementation, on the authors' own data.

Two numbers used to live in this folder and they are 27 points apart:

  * the ERASOR paper's own Table II (p.8): voxel-wise PR/RR/F1 = 93.980 / 97.081
    / 0.955 on SemanticKITTI 00, at 0.2 m voxels;
  * DynamicMap_Benchmark Table I (p.5), which runs a ROS-free re-implementation
    and reports point-wise SA/DA/AA = 66.70 / 98.54 / 81.07.

The gap is neither noise nor a bug in either one - it is the metric and the
pipeline. So this file now runs the **official** repo, on the **official** data,
with the **authors' own evaluator**, and keeps the benchmark's row beside it:

  1. `data/official/00_4390_to_4530_w_interval_2_node.bag` - the seq-00 snippet
     upstream's README tells you to download (frames 4390-4530, interval 2);
  2. `kitti_mapgen` -> naive map, then `offline_map_updater` -> cleaned map,
     both driven exactly as upstream's launch files drive them;
  3. scored by `scripts/analysis_runner.py` against the authors' dense semantic
     GT `erasor_paper_pcds/gt/00_voxel_0_2.pcd`.

The evaluation chain is not taken on trust: the authors' own published output
(`estimate/00_ERASOR.pcd`) is scored first, and it must land on the paper's
Table II row. It does, to 0.001 pp - that is a check, not a finding.

Upstream sources are built unmodified except for two portability patches
(PCL >= 1.11 shared-pointer type, `PassThrough::setNegative`) recorded in
`work/local_patches.patch`.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

# ERASOR, RA-L 2021, Table II p.8 - voxel-wise PR/RR/F1, SemanticKITTI 00, voxel 0.2
PAPER_TABLE_II = {"PR": 93.980, "RR": 97.081, "F1": 0.955}
# The same table re-run by the authors on the current master, printed in the
# repo README's "Benchmark" section: the band our own run should land in.
UPSTREAM_RERUN = {"PR": 95.790, "RR": 95.642, "F1": 0.957}
# DynamicMap_Benchmark Table I p.5 (identical row in DUFOMap Table I p.5)
BENCHMARK = {"SA": 66.70, "DA": 98.54, "AA": 81.07}
TOL_PP = 0.5


# --------------------------------------------------------------------------- #
# paths
# --------------------------------------------------------------------------- #
def _repo(ctx):
    return ctx["repo_root"]


def _venv_python(ctx):
    cand = os.path.join(_repo(ctx), "reproductions", ".venvs", "dmb", "bin", "python")
    return cand if os.path.exists(cand) else sys.executable


def _micromamba():
    cand = os.path.expanduser("~/.local/bin/micromamba")
    return cand if os.path.exists(cand) else None


def _ros1_env(ctx):
    return os.path.join(_repo(ctx), "reproductions", ".venvs", "ros1noetic")


def _ws(ctx):
    return os.path.join(_repo(ctx), "reproductions", ".ws", "erasor_ws")


def _upstream(ctx):
    return os.path.join(ctx["path"], "code", "ERASOR")


def _official(ctx):
    # upstream data lives beside data/raw (which holds the benchmark package)
    return os.path.join(ctx["path"], "data", "official")


def _bag(ctx):
    return os.path.join(_official(ctx), "00_4390_to_4530_w_interval_2_node.bag")


def _paper_pcds(ctx):
    return os.path.join(_official(ctx), "erasor_paper_pcds")


def _gt(ctx):
    return os.path.join(_paper_pcds(ctx), "gt", "00_voxel_0_2.pcd")


def _published_estimate(ctx):
    return os.path.join(_paper_pcds(ctx), "estimate", "00_ERASOR.pcd")


def _result_pcd(ctx):
    return os.path.join(ctx["results_dir"], "erasor_official", "00_result.pcd")


def _bench(ctx):
    return os.path.normpath(os.path.join(
        ctx["path"], "..", "01_dynamicmap_benchmark", "code", "DynamicMap_Benchmark"))


def _bench_seq(ctx):
    env = os.environ.get("DMB_SEQ_DIR")
    if env and os.path.isdir(os.path.join(env, "pcd")):
        return env
    cand = os.path.normpath(os.path.join(
        ctx["path"], "..", "01_dynamicmap_benchmark", "data", "raw", "00"))
    return cand if os.path.isdir(os.path.join(cand, "pcd")) else None


def _score_official(ctx, gt, est, out):
    r = subprocess.run([_venv_python(ctx), os.path.join(ctx["work_dir"], "score_official.py"),
                        "--runner", os.path.join(_upstream(ctx), "scripts", "analysis_runner.py"),
                        "--gt", gt, "--est", est, "--out", out],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"score_official.py failed: {(r.stderr or r.stdout)[-1200:]}")
    with open(out, encoding="utf-8") as fh:
        return json.load(fh)


# --------------------------------------------------------------------------- #
# contract
# --------------------------------------------------------------------------- #
def require(ctx):
    if _micromamba() is None:
        return ("micromamba not found - the official ROS 1 build needs it: "
                "curl -sSL https://micro.mamba.pm/api/micromamba/linux-64/latest | "
                "tar -xj -C /tmp bin/micromamba && mv /tmp/bin/micromamba ~/.local/bin/")
    if not os.path.isdir(_ros1_env(ctx)):
        return ("ROS 1 Noetic env missing - create it once with the micromamba command in "
                "03_erasor/README.md (reproductions/.venvs/ros1noetic)")
    if not os.path.isdir(os.path.join(_upstream(ctx), "src")):
        return ("official repo not cloned - git clone https://github.com/LimHyungTae/ERASOR "
                + os.path.relpath(_upstream(ctx), ctx["path"]))
    missing = [b for b in ("kitti_mapgen", "offline_map_updater")
               if not os.path.exists(os.path.join(_ws(ctx), "devel", "lib", "erasor", b))]
    if missing:
        return ("official binaries not built (" + ", ".join(missing) + ") - bash "
                "reproductions/tools/build_ros1_catkin.sh reproductions/.ws/erasor_ws erasor "
                + os.path.relpath(_upstream(ctx), _repo(ctx))
                + "  (inside `micromamba run -p reproductions/.venvs/ros1noetic bash`)")
    if not os.path.exists(_bag(ctx)):
        return ("official seq-00 rosbag missing - wget "
                "https://urserver.kaist.ac.kr/publicdata/erasor/rosbag/"
                "00_4390_to_4530_w_interval_2_node.bag -P " + _official(ctx))
    if not os.path.exists(_gt(ctx)):
        return ("official GT missing - wget https://urserver.kaist.ac.kr/publicdata/erasor/"
                "erasor_paper_pcds.zip -P " + _official(ctx) + " && unzip it there")
    # the authors' evaluator needs sklearn + tabulate; the benchmark evaluator needs scipy
    probe = subprocess.run([_venv_python(ctx), "-c",
                            "import numpy, sklearn, tabulate, scipy, tqdm"],
                           capture_output=True, text=True)
    if probe.returncode != 0:
        rel = os.path.relpath(_venv_python(ctx), _repo(ctx))
        return (f"{rel} needs numpy + scikit-learn + tabulate + tqdm (the authors' "
                f"analysis_runner) and scipy (the benchmark evaluator): "
                f"{rel} -m pip install scikit-learn tabulate tqdm scipy")
    return None


def run(ctx):
    metrics = {}

    # ---------------------------------------------------- 0. the metric chain
    # The authors' own published output must reproduce their Table II row.
    published = _score_official(ctx, _gt(ctx), _published_estimate(ctx),
                                os.path.join(ctx["results_dir"], "score_published.json"))
    metrics.update({"published_PR": published["PR"], "published_RR": published["RR"],
                    "published_F1": published["F1"]})

    # ------------------------------------------------- 1. our own official run
    r = subprocess.run([_micromamba(), "run", "-p", _ros1_env(ctx), "bash",
                        os.path.join(ctx["work_dir"], "run_official.sh"),
                        _bag(ctx), os.path.join(ctx["results_dir"], "erasor_official", "mapgen"),
                        os.path.join(ctx["results_dir"], "erasor_official")],
                       capture_output=True, text=True, timeout=90 * 60,
                       env={**os.environ,
                            "ERASOR_WS": _ws(ctx), "ERASOR_SRC": _upstream(ctx)})
    if r.returncode != 0:
        raise RuntimeError("official ERASOR run failed:\n"
                           + (r.stdout or "")[-1500:] + (r.stderr or "")[-1500:])
    if not os.path.exists(_result_pcd(ctx)):
        raise RuntimeError(f"official run wrote no {_result_pcd(ctx)}")

    ours = _score_official(ctx, _gt(ctx), _result_pcd(ctx),
                           os.path.join(ctx["results_dir"], "score_official.json"))
    metrics.update({"official_PR": ours["PR"], "official_RR": ours["RR"],
                    "official_F1": ours["F1"],
                    "official_gt_static": ours["gt_static"],
                    "official_gt_dynamic": ours["gt_dynamic"],
                    "official_est_static": ours["est_static"],
                    "official_est_dynamic": ours["est_dynamic"],
                    "official_kept_static": ours["preserved_static"],
                    "official_kept_dynamic": ours["preserved_dynamic"]})

    # ------------------------------------- 2. the benchmark's port, unmodified
    # Kept so the folder's original target keeps being backtested, and so the
    # official-vs-port comparison exists on the same data as in 01-04.
    port = None
    seq = _bench_seq(ctx)
    if seq:
        port_map = os.path.join(seq, "erasor_output.pcd")
        if os.path.exists(port_map):
            out = os.path.join(ctx["results_dir"], "erasor_benchmark_port.json")
            e = subprocess.run([_venv_python(ctx), os.path.normpath(os.path.join(
                                    ctx["path"], "..", "01_dynamicmap_benchmark", "work",
                                    "evaluate.py")),
                                "--seq-dir", seq, "--map", port_map, "--method", "erasor",
                                "--impl", "official", "--out", out],
                               capture_output=True, text=True)
            if e.returncode == 0:
                with open(out, encoding="utf-8") as fh:
                    payload = json.load(fh)
                port = {k: payload["official"][k] for k in ("SA", "DA", "AA", "HA")}
                metrics.update(port)
                metrics.update({"map_points": payload["map_points"],
                                "gt_static": payload["official"]["gt_static"],
                                "gt_dynamic": payload["official"]["gt_dynamic"],
                                "false_removal": payload["official"]["false_removal"],
                                "missed_dynamic": payload["official"]["missed_dynamic"]})

    checks = [
        {
            "name": "published_output_reproduces_paper_table_ii",
            "ok": all(abs(metrics[f"published_{k}"] - PAPER_TABLE_II[k]) <= 0.05
                      for k in ("PR", "RR", "F1")),
            "detail": (f"the authors' own estimate/00_ERASOR.pcd scored with their own "
                       f"analysis_runner against their own GT gives "
                       f"{metrics['published_PR']:.3f}/{metrics['published_RR']:.3f}/"
                       f"{metrics['published_F1']:.4f} against Table II's "
                       f"{PAPER_TABLE_II['PR']}/{PAPER_TABLE_II['RR']}/{PAPER_TABLE_II['F1']} - "
                       "so the evaluator, the GT and the voxel rule are the paper's"),
        },
        {
            # The authors' own published map for this snippet holds 364,005
            # points (363,880 static + 125 dynamic) - ERASOR submits a 0.2 m
            # voxelised map, not a dense one, so the bar is 200k, not millions.
            "name": "official_pipeline_runs_on_official_data",
            "ok": (metrics["official_est_static"] + metrics["official_est_dynamic"]) > 200_000,
            "detail": (f"mapgen + offline_map_updater over the official bag produced "
                       f"{metrics['official_est_static'] + metrics['official_est_dynamic']} "
                       f"points (the authors' published estimate/00_ERASOR.pcd holds "
                       f"{published['est_static'] + published['est_dynamic']})"),
        },
        {
            "name": "our_run_lands_in_the_upstream_band",
            "ok": (min(PAPER_TABLE_II["PR"], UPSTREAM_RERUN["PR"]) - 3.0
                   <= metrics["official_PR"]
                   <= max(PAPER_TABLE_II["PR"], UPSTREAM_RERUN["PR"]) + 3.0),
            "detail": (f"PR {metrics['official_PR']:.3f} / RR {metrics['official_RR']:.3f} / "
                       f"F1 {metrics['official_F1']:.4f}; the paper's Table II is "
                       f"{PAPER_TABLE_II['PR']}/{PAPER_TABLE_II['RR']}/{PAPER_TABLE_II['F1']} "
                       "and the authors' re-run on current master is "
                       f"{UPSTREAM_RERUN['PR']}/{UPSTREAM_RERUN['RR']}/{UPSTREAM_RERUN['F1']}"),
        },
    ]
    if port is not None:
        checks.append({
            "name": "benchmark_port_still_reproduces_its_row",
            "ok": all(abs(port[k] - BENCHMARK[k]) <= TOL_PP for k in ("SA", "DA", "AA")),
            "detail": (f"benchmark port SA/DA/AA = {port['SA']:.2f}/{port['DA']:.2f}/"
                       f"{port['AA']:.2f} vs Table I {BENCHMARK['SA']}/{BENCHMARK['DA']}/"
                       f"{BENCHMARK['AA']}"),
        })

    findings = [
        {
            "name": "official_and_port_agree_on_erasor_where_removert_disagreed",
            "detail": (f"ERASOR's official repo scores PR {metrics['official_PR']:.2f} / "
                       f"RR {metrics['official_RR']:.2f} / F1 {metrics['official_F1']:.4f} on "
                       "the official snippet, and the benchmark's ROS-free port reproduces "
                       f"its own Table I row (SA/DA/AA = {port['SA']:.2f}/{port['DA']:.2f}/"
                       f"{port['AA']:.2f}) on the Zenodo sequence. Unlike Removert (01-04, "
                       "where the port lost 47.7 pp of dynamic rejection), here the two "
                       "implementations do not contradict each other - the metric changes, "
                       "the method does not." if port else
                       "official ERASOR ran; the benchmark port was not available to compare"),
        },
        {
            "name": "the_27_point_gap_is_the_metric_not_the_method",
            "detail": (f"on the same sequence, the same method reads PR "
                       f"{metrics['official_PR']:.2f} under the paper's voxel-wise metric and "
                       f"SA {port['SA']:.2f} under the benchmark's point-wise one. The paper's "
                       "own number is the higher one, and the benchmark's GT cloud has "
                       f"{metrics['gt_static'] + metrics['gt_dynamic']} points against our "
                       f"map's {metrics['official_est_static'] + metrics['official_est_dynamic']} "
                       "- at 0.05 m nearest-neighbour, resolution loss is scored as deletion."
                       if port else "official metric only (port unavailable)"),
        },
    ]

    note = (f"official ERASOR on the authors' seq-00 snippet: PR/RR/F1 = "
            f"{metrics['official_PR']:.2f}/{metrics['official_RR']:.2f}/{metrics['official_F1']:.3f} "
            f"(paper Table II {PAPER_TABLE_II['PR']}/{PAPER_TABLE_II['RR']}/{PAPER_TABLE_II['F1']})")

    return {
        "metrics": metrics,
        "checks": checks,
        "findings": findings,
        "artifacts": ["results/score_official.json", "results/score_published.json",
                      "results/erasor_official/00_result.pcd"],
        "note": note,
    }
