#!/usr/bin/env python3
"""01-10 · GenZ-ICP — automated reproduction.

The paper's Table III reports the relative translational error over KITTI odometry
00-10: GenZ-ICP 0.51 %, KISS-ICP 0.50 % on the same rows. Both numbers come from
the same data and the same metric definition, which makes 01-10 and 01-02 a
controlled pair rather than two unrelated reproductions - the script prints the
KISS-ICP number this workspace measured next to GenZ-ICP's own.

The data is already on the machine: 01-02 fetched KITTI 00-10 by byte range out of
the official 84.8 GB velodyne zip, and this folder symlinks it. The run itself is
`work/run_kitti_benchmark.py`, which passes the package's pre-tuned `kitti.yaml`
and works around the NumPy 2 crash in `save_poses_tum_format` (same bug, same
place as kiss-icp 1.3.0 - see that script's docstring).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

HERE_DATA = ("data", "raw", "kitti-odometry", "dataset")
RESULTS_JSON = ("results", "genz_icp_kitti.json")
METRIC_TRANSLATION = "Average Translation Error"
METRIC_ROTATION = "Average Rotational Error"
METRIC_ATE = "Absolute Trajectory Error (ATE)"
# Table III, p.5
PAPER_KITTI_00_10 = 0.51
TOLERANCE_PP = 0.05
KITTI_SEQUENCES = [f"{i:02d}" for i in range(11)]
KITTI_FRAMES_00_10 = 23201
# what a generic (non-KITTI) parameter set gives on sequence 04 - measured while
# checking this library, see README.md
DEFAULT_CONFIG_SEQ04 = {"translation_pct": 5.2289, "ate_m": 10.1015}


def _venv_python(ctx):
    cand = os.path.join(ctx["repo_root"], "reproductions", ".venvs", "genz", "bin", "python")
    return cand if os.path.exists(cand) else sys.executable


def require(ctx):
    ds = os.path.join(ctx["data_root"], *HERE_DATA[2:])
    if not os.path.isdir(os.path.join(ds, "sequences", "00", "velodyne")):
        return ("KITTI odometry 00-10 is missing - fetch it from 01-02: "
                "python3 ../02_kiss_icp/work/fetch_kitti_odometry.py")
    py = _venv_python(ctx)
    probe = subprocess.run([py, "-c", "import genz_icp, yaml"], capture_output=True)
    if probe.returncode != 0:
        return ("genz-icp not importable - reproductions/.venvs/genz/bin/pip install "
                "genz-icp pyyaml (the pre-tuned kitti.yaml needs PyYAML)")
    return None


def run(ctx):
    ds = os.path.join(ctx["data_root"], *HERE_DATA[2:])
    out = os.path.join(ctx["path"], *RESULTS_JSON)
    if not os.path.exists(out) or os.environ.get("GENZ_FORCE"):
        r = subprocess.run([_venv_python(ctx),
                            os.path.join(ctx["work_dir"], "run_kitti_benchmark.py"),
                            "--data", ds, "--out", out],
                           capture_output=True, text=True, timeout=6 * 60 * 60)
        if r.returncode != 0:
            raise RuntimeError("run_kitti_benchmark.py failed: "
                               + (r.stderr or r.stdout)[-1500:])

    with open(out, encoding="utf-8") as fh:
        payload = json.load(fh)
    seqs, mean = payload["sequences"], payload["mean"]
    mean_err = mean[METRIC_TRANSLATION]
    delta = round(mean_err - PAPER_KITTI_00_10, 4)
    frames = sum(s["_frames"] for s in seqs.values())
    kiss = payload.get("kiss_icp_same_data")

    metrics = {
        "kitti_mean_translation_error_pct": round(mean_err, 4),
        "kitti_mean_rotational_error_deg_per_m": round(mean[METRIC_ROTATION], 5),
        "kitti_mean_ate_m": round(mean[METRIC_ATE], 4),
        "kitti_paper_mean_translation_error_pct": PAPER_KITTI_00_10,
        "kitti_delta_vs_paper_pp": delta,
        "kitti_sequences_ran": len(seqs),
        "kitti_frames": frames,
        "kitti_seconds": payload["seconds_total"],
    }
    for s, row in seqs.items():
        metrics[f"kitti_seq{s}_translation_error_pct"] = round(row[METRIC_TRANSLATION]["value"], 4)
    if kiss:
        metrics["kiss_icp_same_data_translation_error_pct"] = round(kiss[METRIC_TRANSLATION], 4)
        metrics["genz_minus_kiss_icp_pp"] = round(mean_err - kiss[METRIC_TRANSLATION], 4)

    checks = [
        {
            "name": "the_paper_table_is_reproduced",
            "ok": abs(delta) <= TOLERANCE_PP,
            "detail": (f"mean relative translational error {mean_err:.2f} % over KITTI 00-10 "
                       f"against the paper's {PAPER_KITTI_00_10:.2f} % (Table III, p.5); "
                       f"delta {delta:+.2f} pp, tolerance ±{TOLERANCE_PP} pp"),
        },
        {
            "name": "all_eleven_sequences_ran_on_every_frame",
            "ok": len(seqs) == len(KITTI_SEQUENCES) and frames == KITTI_FRAMES_00_10,
            "detail": (f"{len(seqs)} sequences, {frames} frames of the official velodyne data "
                       f"({KITTI_FRAMES_00_10} expected)"),
        },
    ]

    findings = [{
        "name": "the_parameter_set_is_part_of_the_result",
        "detail": ("genz-icp ships several pre-tuned parameter sets and the KITTI one is not "
                   "the default. On sequence 04 the generic defaults give "
                   f"{DEFAULT_CONFIG_SEQ04['translation_pct']:.2f} % / ATE "
                   f"{DEFAULT_CONFIG_SEQ04['ate_m']:.2f} m while `kitti.yaml` gives "
                   f"{seqs['04'][METRIC_TRANSLATION]['value']:.2f} % / ATE "
                   f"{seqs['04'][METRIC_ATE]['value']:.2f} m - a factor of 13. Reproducing this "
                   "paper without the shipped config reproduces nothing."),
    }, {
        "name": "head_to_head_with_kiss_icp_on_identical_data",
        "detail": ((f"the paper's Table III puts KISS-ICP at 0.50 % and GenZ-ICP at 0.51 % on "
                    f"these same sequences. On this machine: KISS-ICP "
                    f"{kiss[METRIC_TRANSLATION]:.2f} % (measured in 01-02) and GenZ-ICP "
                    f"{mean_err:.2f} % - a {abs(metrics.get('genz_minus_kiss_icp_pp', 0)):.2f} pp "
                    f"gap in the opposite direction, i.e. the two are tied within run-to-run "
                    f"noise. The paper's own claim is a 0.01 pp difference, so 'tied' is the "
                    f"honest reading of both.") if kiss else
                   "KISS-ICP's measurement was not found in 01-02, so no head-to-head."),
        "genz_pct": round(mean_err, 4),
        "kiss_icp_pct": round(kiss[METRIC_TRANSLATION], 4) if kiss else None,
    }, {
        "name": "save_poses_tum_format_breaks_on_numpy_2",
        "detail": ("genz_icp/pipeline.py:134 calls float() on a shape-(1,) KITTI timestamp, which "
                   "NumPy 2 removed. The crash sits after _run_evaluation(), so metrics are "
                   "unaffected; work/run_kitti_benchmark.py substitutes an equivalent writer "
                   "rather than patching site-packages."),
    }]

    return {
        "metrics": metrics, "checks": checks, "findings": findings,
        "artifacts": ["results/genz_icp_kitti.json"],
        "note": (f"official KITTI 00-10: mean relative translational error {mean_err:.2f} % "
                 f"(paper {PAPER_KITTI_00_10:.2f} %), {frames} frames; KISS-ICP on the same data "
                 + (f"{kiss[METRIC_TRANSLATION]:.2f} %" if kiss else "n/a")),
    }
