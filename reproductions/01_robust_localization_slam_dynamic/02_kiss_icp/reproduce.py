#!/usr/bin/env python3
"""01-02 · KISS-ICP — automated reproduction.

What this can and cannot claim is the whole point of the file, so it is worth
stating up front.

KISS-ICP's paper evaluates on KITTI odometry, MulRan, Newer College and Boreas,
and every one of them is gated behind a registration form, an email, or - for
Newer College - a download that is currently broken. So the published 0.50 %
average translation error on KITTI 00-10 cannot be reproduced here.

What can be done is a sanity run on data we do have. The benchmark's free Zenodo
release of KITTI 00 ships 141 frames as world-frame clouds with the sensor pose
in each PCD's VIEWPOINT field; those were built by transforming the original
Velodyne scans with exactly those poses, so inverting the transform recovers the
raw sensor-frame scans (work/make_kitti_seq.py). The official `--dataloader
kitti` path then runs unmodified.

That run reports an average translation error, and the number is real, but it is
NOT the paper's number, for three measured reasons:

  - KISS-ICP's metric is the KITTI devkit one: segments of {100..800} m starting
    every 10 frames. This trajectory is 108.3 m long, so it yields exactly
    **2** error samples. The paper averages hundreds, over full sequences.
  - 141 of KITTI 00's 4541 frames.
  - the ground truth here is SuMa-derived (SemanticKITTI's convention), not
    KITTI's official poses.

So `checks` cover only what is genuinely invariant - the official pipeline runs,
it consumes every frame, and the trajectory is the length the source data says
it is. The comparability gap is a measurement about the data and is reported as
a finding, which by this repo's convention never gates the run.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys

# The metric below is reported for information; it is deliberately NOT compared
# against the paper's 0.50 %, because the evaluation set is not the paper's.
PAPER_KITTI_00_10 = 0.50  # % average translation error, Table II p.6
# KITTI devkit segment lengths; the shortest one bounds what a trajectory can measure.
MIN_SEGMENT_M = 100.0
EXPECTED_FRAMES = 141
EXPECTED_LENGTH_M = 108.3


def _venv_python(ctx):
    cand = os.path.join(ctx["repo_root"], "reproductions", ".venvs", "dmb", "bin", "python")
    return cand if os.path.exists(cand) else sys.executable


def _seq_root(ctx):
    return os.path.join(ctx["data_root"], "kitti00_sub")


def _benchmark_seq(ctx):
    """The DynamicMap_Benchmark KITTI 00 folder the raw scans are rebuilt from."""
    for cand in (os.path.join(ctx["data_root"], "00"),
                 os.path.normpath(os.path.join(ctx["path"], "..", "01_dynamicmap_benchmark",
                                               "data", "raw", "00"))):
        if os.path.isdir(os.path.join(cand, "pcd")):
            return cand
    return None


def require(ctx):
    root = _seq_root(ctx)
    if not os.path.isdir(os.path.join(root, "sequences", "00", "velodyne")):
        if _benchmark_seq(ctx) is None:
            return ("the source sequence is missing - fetch the benchmark's free KITTI 00 "
                    "package (wget https://zenodo.org/records/10886629/files/00.zip, 385 MB, "
                    "no KITTI registration) into 01_dynamicmap_benchmark/data/raw/, then run "
                    "work/make_kitti_seq.py. The paper's own datasets (KITTI odometry, "
                    "MulRan, NCD, Boreas) are all registration-gated and cannot be used here.")
        return ("reconstructed sequence not built yet - run: work/make_kitti_seq.py "
                "--seq-dir <benchmark>/data/raw/00 --out data/raw/kitti00_sub")
    py = _venv_python(ctx)
    if subprocess.run([py, "-c", "import kiss_icp"], capture_output=True).returncode != 0:
        return ("kiss-icp not importable - reproductions/.venvs/dmb/bin/pip install kiss-icp "
                "(see reproductions/README.md for bootstrapping the venv without sudo)")
    return None


def run(ctx):
    root = _seq_root(ctx)
    py = _venv_python(ctx)
    seq = os.path.join(root, "sequences", "00")

    # Rebuild the KITTI-format sequence if the source changed underneath us.
    velo = os.path.join(seq, "velodyne")
    if len([f for f in os.listdir(velo) if f.endswith(".bin")]) != EXPECTED_FRAMES:
        src = _benchmark_seq(ctx)
        r = subprocess.run([py, os.path.join(ctx["work_dir"], "make_kitti_seq.py"),
                            "--seq-dir", src, "--out", root, "--force"],
                           capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(f"make_kitti_seq failed: {(r.stderr or r.stdout)[-1200:]}")

    out_dir = os.path.join(ctx["results_dir"], "kiss_icp_logs")
    os.makedirs(out_dir, exist_ok=True)
    env = dict(os.environ, kiss_icp_out_dir=out_dir)
    proc = subprocess.run([py, "-m", "kiss_icp.pipeline", "--dataloader", "kitti",
                           "--sequence", "00", root],
                          capture_output=True, text=True, env=env)
    if proc.returncode != 0:
        raise RuntimeError(f"kiss_icp_pipeline failed ({proc.returncode}): "
                           f"{(proc.stderr or proc.stdout)[-1500:]}")

    metrics_log = os.path.join(out_dir, "latest", "result_metrics.log")
    if not os.path.exists(metrics_log):
        raise RuntimeError("the pipeline produced no result_metrics.log")
    text = open(metrics_log, encoding="utf-8").read()

    def _metric(label):
        # rows read like "| Absolute Trajectory Error (ATE) | 0.112 | m |"
        m = re.search(re.escape(label) + r"(?:\s*\([^)]*\))?\s*\|\s*([0-9.]+)", text)
        return float(m.group(1)) if m else None

    ate = _metric("Absolute Trajectory Error")
    avg_trans = _metric("Average Translation Error")
    avg_rot = _metric("Average Rotational Error")
    fps = _metric("Average Frequency")
    ms = _metric("Average Runtime")

    poses_file = os.path.join(out_dir, "latest", "00_poses_kitti.txt")
    frames = sum(1 for line in open(poses_file, encoding="utf-8") if line.strip()) \
        if os.path.exists(poses_file) else 0

    # Recompute trajectory length from the ground truth the loader used, so the
    # comparability finding is derived rather than asserted.
    import numpy as np
    gt = np.loadtxt(os.path.join(out_dir, "latest", "00_gt_kitti.txt")).reshape(-1, 3, 4)
    dist = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(gt[:, :3, 3], axis=0), axis=1))]
    length = float(dist[-1])
    samples = sum(1 for f in range(0, len(gt), 10) for L in (100, 200, 300, 400, 500, 600, 700, 800)
                  if np.any(dist > dist[f] + L))

    metrics = {
        "avg_translation_error_pct": avg_trans,
        "avg_rotational_error_deg_per_m": avg_rot,
        "ATE_m": ate,
        "frames": frames,
        "trajectory_length_m": round(length, 1),
        "metric_samples": samples,
        "avg_frequency_hz": fps,
        "avg_runtime_ms": ms,
    }

    checks = [
        {
            "name": "official_pipeline_reports_all_metrics",
            "ok": all(v is not None for v in (ate, avg_trans, avg_rot, fps, ms)),
            "detail": (f"ATE {ate} m, avg translation {avg_trans} %, avg rotation {avg_rot} deg/m, "
                       f"{fps} Hz, {ms} ms/frame"),
        },
        {
            "name": "every_frame_processed",
            "ok": frames == EXPECTED_FRAMES,
            "detail": f"{frames} poses written for {EXPECTED_FRAMES} input scans",
        },
        {
            "name": "trajectory_matches_the_source_data",
            "ok": abs(length - EXPECTED_LENGTH_M) < 2.0,
            "detail": (f"ground-truth path length {length:.1f} m against the "
                       f"{EXPECTED_LENGTH_M} m measured on the benchmark release - a mismatch "
                       "would mean the pose inversion in make_kitti_seq.py is wrong"),
        },
    ]

    findings = [
        {
            "name": "cannot_reproduce_the_published_number_on_free_data",
            "detail": (f"KISS-ICP's metric is the KITTI devkit one: segments of "
                       f"{{{MIN_SEGMENT_M:.0f}..800}} m starting every 10 frames. This trajectory is "
                       f"{length:.1f} m, so it yields exactly {samples} error sample(s). The paper's "
                       f"{PAPER_KITTI_00_10} % averages hundreds of samples over the full KITTI "
                       f"sequences (thousands of metres each). {samples} samples is a sanity run, "
                       "not a reproduction."),
            "metric_samples": samples, "paper_value_pct": PAPER_KITTI_00_10,
        },
        {
            "name": "all_four_paper_datasets_are_gated",
            "detail": ("KITTI odometry needs registration (~80 GB), MulRan needs registration, "
                       "Boreas needs a form, and Newer College's download page carries no direct "
                       "links (its download is reported broken upstream). Reproducing the "
                       "published numbers requires registering for KITTI."),
        },
        {
            "name": "kiss_icp_1_3_0_breaks_on_numpy_2",
            "detail": ("pipeline.py:130 calls float() on a shape-(1,) timestamp array, which "
                       "NumPy 2 no longer allows. The crash is in the TUM-format writer, which "
                       "runs after _run_evaluation() - so no metric is affected, but without the "
                       "one-line patch in work/local_patches.patch the run dies before returning "
                       "them."),
        },
        {
            "name": "no_loop_closure_by_design",
            "detail": ("there is no loop closure, no pose graph and no keyframe selection - "
                       f"{frames} frames, {fps:.0f} Hz, {ms:.0f} ms/frame on CPU. Drift is bounded "
                       "only by ICP itself, which matters for the H1' experiment in 01-01: a "
                       "'cleaned map hurts localization' result could be drift rather than map "
                       "quality."),
        },
    ]

    return {
        "metrics": metrics, "checks": checks, "findings": findings,
        "artifacts": [os.path.relpath(metrics_log, ctx["path"])],
        "note": (f"KISS-ICP on a reconstructed 141-frame KITTI 00 sub-sequence: ATE {ate} m, "
                 f"avg translation error {avg_trans} % over only {samples} metric sample(s) - "
                 f"the paper's {PAPER_KITTI_00_10} % is NOT reproduced (see findings)"),
    }
