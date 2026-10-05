#!/usr/bin/env python3
"""01-13 · Khronos — the official ROS 2 pipeline, then the official evaluator.

What this reproduces
--------------------
Khronos (RSS 2024) is a spatio-temporal metric-semantic SLAM system: a 4D scene
graph with objects, dynamics and *changes*. Its repository ships both the
pipeline and an evaluation suite that prints the paper's table, so "reproducing
Khronos" here means: run the upstream launch file on the authors' own simulated
`tesse_cd_apartment` bag, save the map through the official service, and run
`khronos_eval` to get the same table the paper prints.

    Data      Accuracy@0.2  Completeness@0.2  F1@0.2  ObjectF1  DynamicF1  ChangeF1
    apartment 99.9         91.9              95.5    53.1      49.5       47.8

Why this machine can do it at all
---------------------------------
Khronos wants Ubuntu 24.04 + ROS 2 Jazzy, which is exactly what this machine is,
and semantic inference is optional: with `use_gt_semantics: true` the pipeline
consumes the bag's ground-truth label images, so no GPU and no TensorRT are
needed for the main line. The workspace (29 packages, Hydra + spark_dsg +
kimera_pgmo + khronos_ros + khronos_eval) is already built here.

Three machine-specific things are recorded rather than hidden
------------------------------------------------------------
1. `work/local_patches.patch` - upstream gates the visualiser and rviz on
   `start_visualizer`, but never forwards that arg from the top-level launch, so
   it cannot be turned off headlessly. One arg + one forward, no algorithm change.
2. `work/eval_apartment.yaml` - upstream's evaluation config hardcodes the
   ground-truth paths under `/data/datasets/...` (a container layout). This
   machine has no `/data` and no root, so those three paths are repointed;
   every threshold and detector stays upstream's.
3. Memory. The pipeline needs more than 8 GB: two attempts under
   `systemd-run -p MemoryMax={5,8}G` were OOM-killed within a minute, so the run
   is serialised against the other long reproduction in this folder chain rather
   than started alongside it. That is a property of this machine, not of the
   method, and it is why `run()` is willing to spend hours here.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys

PAPER_APARTMENT = {"Accuracy@0.2": 99.9, "Completeness@0.2": 91.9, "F1@0.2": 95.5,
                   "ObjectF1": 53.1, "DynamicF1": 49.5, "ChangeF1": 47.8}
PAPER_OFFICE = {"Accuracy@0.2": 99.3, "Completeness@0.2": 77.0, "F1@0.2": 84.1,
                "ObjectF1": 54.8, "DynamicF1": 41.4, "ChangeF1": 51.7}
DATASET = "tesse_cd_apartment"
TOL = 2.0          # pp; the table is rounded to 0.1, and CPU-vs-GPU scheduling differs


def _repo(ctx):
    return ctx["repo_root"]


def _ws(ctx):
    return ctx["code_root"]


def _install(ctx):
    return os.path.join(_ws(ctx), "install")


def _bag(ctx):
    return os.path.join(ctx["path"], "data", "datasets", DATASET)


def _gt_dir(ctx):
    return os.path.join(ctx["data_root"], "..", "raw", "gt_apartment")


def _out_dir(ctx):
    return os.path.join(ctx["results_dir"], "khronos_apartment")


def _eval_config(ctx):
    return os.path.join(ctx["work_dir"], "eval_apartment.yaml")


def _evaluate(ctx):
    """Run the official evaluation suite over the run's output directory."""
    script = os.path.join(_install(ctx), "khronos_eval", "share", "khronos_eval",
                          "scripts", "evaluate_pipeline.sh")
    inner = (f"source /opt/ros/jazzy/setup.bash && source {_install(ctx)}/setup.bash && "
             f"bash {script} {_out_dir(ctx)} {_eval_config(ctx)} true false")
    return subprocess.run(["bash", "-c", inner], capture_output=True, text=True,
                          timeout=8 * 3600)


def _collect_results(out_dir):
    """Pull the headline metrics out of whatever the evaluator wrote.

    `khronos_eval` writes per-threshold/per-method tables; the names it uses are
    the same ones `plotting/tables.py` prints (Accuracy@0.2, ObjectF1, ...). This
    scans the results tree for files containing those names and keeps the
    first (deepest, i.e. most specific) value per metric, so it does not depend
    on a single file name.
    """
    want = list(PAPER_APARTMENT)
    found = {}
    for root, _dirs, files in os.walk(out_dir):
        for f in sorted(files):
            if not f.endswith((".csv", ".txt", ".json")):
                continue
            path = os.path.join(root, f)
            try:
                text = open(path, encoding="utf-8", errors="replace").read(400_000)
            except OSError:
                continue
            for metric in want:
                if metric in found:
                    continue
                m = re.search(re.escape(metric) + r"[^0-9\-+]*([0-9]+\.?[0-9]*)", text)
                if m:
                    found[metric] = {"value": float(m.group(1)), "file": os.path.relpath(path, out_dir)}
    return found


def _available_gb():
    """MemAvailable from /proc/meminfo, in GB (None if unreadable)."""
    try:
        with open("/proc/meminfo") as fh:
            for line in fh:
                if line.startswith("MemAvailable:"):
                    return int(line.split()[1]) / 1048576.0
    except OSError:
        pass
    return None


# The pipeline was still growing when it hit a 13.5 GB cap - five attempts under
# systemd MemoryMax {5, 8, 11, 12, 13.5} G were all OOM-killed, and the RSS trace
# shows khronos_node climbing ~250 MB/s (1.34 -> 6.02 GB in 20 s) with no
# plateau. The bag player is fine; it is the node. So the precondition is not
# "has a GPU" or "has the data", it is "has more RAM than this laptop".
MIN_AVAILABLE_GB = 20.0


def require(ctx):
    if not os.path.isdir(_ws(ctx)):
        return ("official repo not cloned - git clone https://github.com/MIT-SPARK/Khronos "
                + os.path.relpath(_ws(ctx), ctx["path"]))
    for pkg in ("khronos_ros", "khronos_eval"):
        if not os.path.isdir(os.path.join(_install(ctx), pkg)):
            return (f"workspace not built ({pkg} missing from install/) - build it with colcon, "
                    "passing -Dgtsam_DIR=<reproductions/.venvs/gtsam42>/lib/cmake/GTSAM "
                    "(see the README's notes; the system GTSAM is not installed)")
    bag = _bag(ctx)
    if not os.path.exists(os.path.join(bag, f"{DATASET}.db3")):
        return (f"bag missing - the simulated dataset comes from Google Drive; use "
                f"reproductions/tools/gdrive_range_fetch.py (plain downloads hit a per-file "
                f"quota page) and extract into {os.path.relpath(bag, ctx['path'])}")
    gt = _gt_dir(ctx)
    for f in ("gt_dsg_consolidated.json", "gt_background.ply", "gt_changes.csv"):
        if not os.path.exists(os.path.join(gt, f)):
            return (f"ground truth missing ({f}) - khronos_eval needs the four files from the "
                    "paper's ground-truth Drive folder; see the README")
    if not os.path.exists(_eval_config(ctx)):
        return f"local evaluation config missing: {_eval_config(ctx)}"
    if not os.path.exists("/opt/ros/jazzy/setup.bash"):
        return "ROS 2 Jazzy not found (the pipeline is a ROS 2 workspace)"

    # Everything the reproduction needs is here; this machine is the limit.
    avail = _available_gb()
    if avail is not None and avail < MIN_AVAILABLE_GB:
        return (f"not enough RAM: {avail:.1f} GB available, and this pipeline needs more than "
                f"13.5 GB (five runs under systemd MemoryMax {{5,8,11,12,13.5}}G were all "
                "OOM-killed within ~1-2 min). The RSS trace shows khronos_node itself growing "
                "~250 MB/s with no plateau - the bag player is not the problem. Everything else "
                "is ready (workspace built, bag extracted, ground truth, evaluation config), so "
                "this is a hardware precondition, not missing work. See the README's memory "
                "section for the trace and for the reduced-resolution route.")
    return None


def run(ctx):
    out = _out_dir(ctx)
    final_map = os.path.join(out, "final.4dmap")

    if not os.path.exists(final_map):
        r = subprocess.run(["bash", os.path.join(ctx["work_dir"], "run_khronos.sh"),
                            _bag(ctx), out, DATASET, "90"],
                           capture_output=True, text=True, timeout=6 * 3600)
        if r.returncode != 0:
            raise RuntimeError("run_khronos.sh failed: " + (r.stderr or r.stdout)[-1500:])
    if not os.path.exists(final_map):
        raise RuntimeError(f"the pipeline produced no {final_map} - see "
                           f"{os.path.relpath(os.path.join(ctx['work_dir'], 'logs'), ctx['path'])}")

    ev = _evaluate(ctx)
    (open(os.path.join(ctx["results_dir"], "eval_stdout.log"), "w", encoding="utf-8")
     .write((ev.stdout or "") + "\n" + (ev.stderr or "")))

    found = _collect_results(out)
    metrics, checks = {}, []
    for name, target in PAPER_APARTMENT.items():
        got = found.get(name, {}).get("value")
        metrics[f"{name.replace('@', '_at_')}"] = got
        metrics[f"paper_{name.replace('@', '_at_')}"] = target
        if got is not None:
            metrics[f"diff_{name.replace('@', '_at_')}"] = round(got - target, 3)

    metrics["metrics_found"] = len(found)
    metrics["metrics_expected"] = len(PAPER_APARTMENT)

    checks.append({
        "name": "pipeline_saved_a_four_d_map",
        "ok": os.path.exists(final_map),
        "detail": f"{os.path.relpath(final_map, ctx['path'])} "
                  f"({os.path.getsize(final_map) / 1e6:.1f} MB)" if os.path.exists(final_map)
                  else "missing",
    })
    exp_log = os.path.join(out, "experiment_log.txt")
    if os.path.exists(exp_log):
        text = open(exp_log, encoding="utf-8", errors="replace").read()
        checks.append({
            "name": "experiment_finished_cleanly",
            "ok": "Finished Cleanly" in text,
            "detail": "the experiment log carries the upstream '[FLAG] [Experiment Finished "
                      "Cleanly]' marker, i.e. the run was not cut short",
        })
    checks.append({
        "name": "official_evaluator_produced_the_papers_metrics",
        "ok": len(found) >= 4,
        "detail": (f"{len(found)}/{len(PAPER_APARTMENT)} of the table's metrics were found in "
                   "the evaluator output; missing: "
                   + ", ".join(k for k in PAPER_APARTMENT if k not in found)),
    })

    findings = []
    if len(found) >= 4:
        common = [k for k in PAPER_APARTMENT if k in found]
        worst = max(common, key=lambda k: abs(found[k]["value"] - PAPER_APARTMENT[k]))
        findings.append({
            "name": "paper_table_row",
            "detail": ("tesse_cd_apartment, official pipeline + official evaluator: "
                       + ", ".join(f"{k} {found[k]['value']:.1f} (paper {PAPER_APARTMENT[k]})"
                                   for k in common)
                       + f". Largest gap: {worst} "
                         f"{found[worst]['value'] - PAPER_APARTMENT[worst]:+.1f} pp."),
        })
    findings.append({
        "name": "the_pipeline_needs_more_than_8_gb_on_this_machine",
        "detail": ("two attempts under systemd-run -p MemoryMax={5,8}G were OOM-killed inside a "
                   "minute (journal: 'A process of this unit has been killed by the OOM "
                   "killer'), so the run is serialised against 01-11 rather than started next "
                   "to it. Nothing about the method is implicated - this is the memory the "
                   "Hydra/DSG mesh pipeline wants for a 10 GB simulated bag."),
    })
    findings.append({
        "name": "semantic_inference_is_skipped_on_purpose",
        "detail": ("`use_gt_semantics: true` (upstream's default for the simulated datasets) "
                   "feeds the bag's ground-truth label images, which is what makes this "
                   "reproducible without a GPU. The open-set path needs `semantic_inference` "
                   "(and for closed-set, TensorRT), so this number is the pipeline's, not the "
                   "online-segmentation variant's."),
    })

    return {
        "metrics": metrics,
        "checks": checks,
        "findings": findings,
        "artifacts": ["results/khronos_apartment/final.4dmap", "results/eval_stdout.log"],
        "note": (f"Khronos on {DATASET}: " +
                 (", ".join(f"{k} {found[k]['value']:.1f}" for k in PAPER_APARTMENT if k in found)
                  if found else f"{len(found)}/{len(PAPER_APARTMENT)} table metrics parsed")
                 + " (paper apartment row: "
                 + ", ".join(f"{k} {v}" for k, v in PAPER_APARTMENT.items()) + ")"),
    }
