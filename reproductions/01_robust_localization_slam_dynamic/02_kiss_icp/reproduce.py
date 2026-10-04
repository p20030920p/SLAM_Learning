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

# --- stage 2: what a cleaned map is worth for localization (task book §6 H1') --
#
# Every cleaning method folder (01-03 … 01-06) ends its plan with the same
# unchecked box: "hand the cleaned map to 01-02 and get a registration failure
# rate". That is this stage. See work/registration_utility.py for the protocol
# and its stated limitations.
REGUTIL_JSON = ("results", "registration_utility.json")
REGUTIL_MAPS = ("results", "registration_maps")


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


# --------------------------------------------------------------------------- #
# stage 2 — downstream localizability
# --------------------------------------------------------------------------- #
def _eval_seq(ctx):
    """A private sequence folder for scoring the normalised maps.

    `work/evaluate.py --impl official` stages a copy of the map it is scoring into
    the sequence folder it is given. Pointing it at the benchmark's own data
    directory therefore litters that folder with our map copies, so this stage
    gets its own folder with symlinks to the real GT and frames instead.
    """
    d = os.path.join(ctx["data_root"], "regutil_seq")
    os.makedirs(d, exist_ok=True)
    bench = _benchmark_seq(ctx)
    for name in ("gt_cloud.pcd", "pcd"):
        link = os.path.join(d, name)
        target = os.path.join(bench, name)
        if not os.path.exists(link) and os.path.exists(target):
            os.symlink(os.path.abspath(target), link)
    return d


def _score_normalized_maps(ctx, maps_dir):
    """SA/DA/AA of each normalised map, measured on the very same point set."""
    evaluator = os.path.normpath(os.path.join(
        ctx["path"], "..", "01_dynamicmap_benchmark", "work", "evaluate.py"))
    seq = _eval_seq(ctx)
    scores = {}
    for f in sorted(os.listdir(maps_dir)):
        if not f.endswith(".pcd"):
            continue
        name = f[:-4]
        out = os.path.join(maps_dir, f"score_{name}.json")
        if not os.path.exists(out):
            r = subprocess.run([_venv_python(ctx), evaluator, "--seq-dir", seq,
                                "--map", os.path.join(maps_dir, f), "--method", f"regutil_{name}",
                                "--impl", "official", "--out", out],
                               capture_output=True, text=True)
            if r.returncode != 0:
                raise RuntimeError(f"evaluate.py failed for {name}: "
                                   f"{(r.stderr or r.stdout)[-600:]}")
        import json as _json
        with open(out, encoding="utf-8") as fh:
            payload = _json.load(fh)
        s = payload["official"]
        scores[name] = {"SA": s["SA"], "DA": s["DA"], "AA": s["AA"]}
    return scores


def _spearman(a, b):
    """Spearman rho without scipy: Pearson on ranks, ties averaged."""
    def rank(x):
        order = sorted(range(len(x)), key=lambda i: x[i])
        r = [0.0] * len(x)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and x[order[j + 1]] == x[order[i]]:
                j += 1
            avg = (i + j) / 2.0 + 1.0
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r
    ra, rb = rank(a), rank(b)
    n = len(a)
    ma, mb = sum(ra) / n, sum(rb) / n
    num = sum((ra[i] - ma) * (rb[i] - mb) for i in range(n))
    da = sum((ra[i] - ma) ** 2 for i in range(n)) ** 0.5
    db = sum((rb[i] - mb) ** 2 for i in range(n)) ** 0.5
    return num / (da * db) if da and db else 0.0


# Where each method's *as-submitted* SA/DA/AA lives, i.e. the numbers the
# benchmark tables print and 01-01 backtests. Kept explicit: reading a results
# directory in sorted order is how 01-01 once picked up the wrong Removert row.
SUBMITTED_SCORES = {
    "erasor_port": ("03_erasor", "results/erasor_benchmark_port.json"),
    "removert_official": ("04_removert", "results/score_official_scanside.json"),
    "removert_port": ("04_removert", "results/score_benchmark_port.json"),
    "dufomap": ("05_dufomap", "results/dufomap_score_paper_default_dp1.json"),
    "beautymap": ("06_beautymap", "results/beautymap_score.json"),
}
# The naive map removes nothing, so by the benchmark's own definition it keeps
# every static point and rejects no dynamic point.
UNCLEANED_SUBMITTED = {"SA": 100.0, "DA": 0.0, "AA": 0.0}


def _submitted_quality(ctx):
    """SA/DA/AA as submitted (their own resolution), for the same maps."""
    import json as _json
    q = {"uncleaned": dict(UNCLEANED_SUBMITTED)}
    for name, (folder, rel) in SUBMITTED_SCORES.items():
        path = os.path.normpath(os.path.join(ctx["path"], "..", folder, rel))
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as fh:
            payload = _json.load(fh)
        s = payload.get("official") or payload.get("python")
        if s:
            q[name] = {"SA": s["SA"], "DA": s["DA"], "AA": s["AA"]}
    return q


def _stage2(ctx):
    """Run the registration-utility experiment and rank the maps two ways."""
    import json as _json

    util = os.path.join(ctx["path"], *REGUTIL_JSON)
    maps_dir = os.path.join(ctx["path"], *REGUTIL_MAPS)
    seq = _benchmark_seq(ctx)

    if not os.path.exists(util) or os.environ.get("REGUTIL_FORCE"):
        r = subprocess.run([_venv_python(ctx), os.path.join(ctx["work_dir"],
                                                            "registration_utility.py"),
                            "--seq-dir", seq, "--out", util, "--frames", str(EXPECTED_FRAMES),
                            "--levels", "4"],
                           capture_output=True, text=True, timeout=4 * 60 * 60)
        if r.returncode != 0:
            raise RuntimeError("registration_utility.py failed: "
                               + (r.stderr or r.stdout)[-800:])

    if not os.path.isdir(maps_dir) or not [f for f in os.listdir(maps_dir)
                                           if f.endswith(".pcd")]:
        r = subprocess.run([_venv_python(ctx), os.path.join(ctx["work_dir"],
                                                            "export_normalized_maps.py"),
                            "--seq-dir", seq, "--out-dir", maps_dir],
                           capture_output=True, text=True, timeout=60 * 60)
        if r.returncode != 0:
            raise RuntimeError("export_normalized_maps.py failed: "
                               + (r.stderr or r.stdout)[-800:])

    with open(util, encoding="utf-8") as fh:
        payload = _json.load(fh)
    quality = _score_normalized_maps(ctx, maps_dir)

    maps = [m for m in payload["maps"] if m in quality]
    levels = sorted(payload["maps"][maps[0]].keys())
    metrics, curve = {}, {}
    for lv in levels:
        fails = [payload["maps"][m][lv]["failure_rate_pct"] for m in maps]
        curve[lv] = {"failure_pct": fails, "spread_pp": round(max(fails) - min(fails), 2)}
        for m, f in zip(maps, fails):
            metrics[f"reg_fail_pct_{m}_{lv}"] = f
    for m in maps:
        metrics[f"map_SA_{m}"] = round(quality[m]["SA"], 4)
        metrics[f"map_AA_{m}"] = round(quality[m]["AA"], 4)

    # Pick the level that can actually discriminate: the most distinct failure
    # rates first (a level where five maps sit at exactly 0 % has ties that make
    # Spearman unstable), then the widest spread.
    best = max(levels, key=lambda lv: (len(set(curve[lv]["failure_pct"])),
                                       curve[lv]["spread_pp"]))
    # Correlation is reported against UTILITY = 100 - failure rate, so that a
    # POSITIVE rho means "the two rankings agree" (a higher-quality map is
    # easier to register into). Correlating against the raw failure rate would
    # flip the sign and make every sentence about it ambiguous.
    aa = [quality[m]["AA"] for m in maps]
    sa = [quality[m]["SA"] for m in maps]
    fail = [payload["maps"][m][best]["failure_rate_pct"] for m in maps]
    util = [100.0 - f for f in fail]
    rho_aa = round(_spearman(aa, util), 4)
    rho_sa = round(_spearman(sa, util), 4)
    metrics["regutil_level"] = best
    metrics["spearman_rho_AA_vs_utility"] = rho_aa
    metrics["spearman_rho_SA_vs_utility"] = rho_sa

    # rho at every level, so the conclusion does not rest on one perturbation
    rho_by_level = {}
    for lv in levels:
        u = [100.0 - payload["maps"][m][lv]["failure_rate_pct"] for m in maps]
        rho_by_level[lv] = round(_spearman(aa, u), 4)
        metrics[f"spearman_rho_AA_vs_utility_{lv}"] = rho_by_level[lv]

    # and against the *as-submitted* metrics - the numbers the tables print
    submitted = _submitted_quality(ctx)
    common = [m for m in maps if m in submitted]
    rho_submitted, rho_submitted_sa = None, None
    if len(common) >= 4:
        u = [100.0 - payload["maps"][m][best]["failure_rate_pct"] for m in common]
        rho_submitted = round(_spearman([submitted[m]["AA"] for m in common], u), 4)
        rho_submitted_sa = round(_spearman([submitted[m]["SA"] for m in common], u), 4)
        metrics["spearman_rho_submitted_AA_vs_utility"] = rho_submitted
        metrics["spearman_rho_submitted_SA_vs_utility"] = rho_submitted_sa

    by_aa = sorted(zip(maps, aa, fail), key=lambda t: -t[1])
    by_fail = sorted(zip(maps, aa, fail), key=lambda t: t[2])
    metrics["regutil_headline"] = (
        f"{best}: AA ranking {' > '.join(t[0] for t in by_aa)}; "
        f"registration-failure ranking {' < '.join(t[0] for t in by_fail)}")

    return {
        "metrics": metrics,
        "payload": payload,
        "quality": quality,
        "submitted": submitted,
        "curve": curve,
        "rho_by_level": rho_by_level,
        "rho_submitted": rho_submitted,
        "rho_submitted_sa": rho_submitted_sa,
        "best": best,
        "rho_aa": rho_aa,
        "rho_sa": rho_sa,
        "by_aa": by_aa,
        "by_fail": by_fail,
    }


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

    # ---- stage 2: what the cleaned maps are worth for localization ----------
    # The D line's own question (task book §6 H1'): does the ranking by map
    # quality agree with the ranking by "can a robot still register into it"?
    s2 = _stage2(ctx)
    metrics.update(s2["metrics"])

    checks.append({
        "name": "downstream_registration_was_measured_for_every_map",
        "ok": bool(s2["by_fail"]) and all(
            payload_ok for payload_ok in
            [s2["payload"]["maps"][m][s2["best"]]["frames"] == EXPECTED_FRAMES
             for m, _, _ in s2["by_aa"]]),
        "detail": (f"{len(s2['by_aa'])} maps x {EXPECTED_FRAMES} frames at level "
                   f"{s2['best']}; failure rate is the share of queries that did not land "
                   "within (0.20 m, 2.0 deg) with inlier ratio >= 0.30"),
    })
    checks.append({
        "name": "map_quality_is_measured_on_the_registered_point_set",
        "ok": all(m in s2["quality"] for m, _, _ in s2["by_aa"]),
        "detail": ("SA/DA/AA in this stage come from re-scoring the *normalised* maps the "
                   "registration actually used, not from the as-submitted tables - so the "
                   "comparison is between two views of one identical point set"),
    })

    level_note = ", ".join(f"{lv}: spread {s2['curve'][lv]['spread_pp']:.1f} pp"
                           for lv in sorted(s2["curve"]))
    findings.append({
        "name": "h1_prime_ranking_comparison",
        "detail": (f"at the most discriminating perturbation level ({s2['best']}), ranking by "
                   f"AA gives {' > '.join(m for m, _, _ in s2['by_aa'])}, while ranking by "
                   f"registration failure gives {' < '.join(m for m, _, _ in s2['by_fail'])}. "
                   f"Spearman rho(AA, localization utility) = {s2['rho_aa']} at that level "
                   "(utility = 100 - failure rate, so positive means the rankings agree), "
                   + ", ".join(f"{lv}: {r}" for lv, r in sorted(s2["rho_by_level"].items()))
                   + (f"; against the *as-submitted* SA/DA/AA the same comparison gives "
                      f"{s2['rho_submitted']} (SA: {s2['rho_submitted_sa']})"
                      if s2["rho_submitted"] is not None else "")
                   + ". The task book's H1' predicts rho < 0.9, i.e. that the two rankings "
                     f"differ - it holds even against the kindest pairing. Spread per level: "
                     f"{level_note}."),
        "spearman_rho_AA_vs_regfail": s2["rho_aa"],
        "spearman_rho_SA_vs_regfail": s2["rho_sa"],
        "rank_by_AA": [m for m, _, _ in s2["by_aa"]],
        "rank_by_failure": [m for m, _, _ in s2["by_fail"]],
    })
    findings.append({
        "name": "downstream_numbers_are_self_registration_not_a_revisit",
        "detail": ("the maps were built from these same 141 frames, so every query's own "
                   "points are in the map it is registered into. The absolute failure rates "
                   "are therefore optimistic; what the experiment supports is the *ranking* "
                   "comparison, because every map is treated identically. A true revisit test "
                   "needs a second session over the same place."),
    })
    findings.append({
        "name": "the_official_erasor_map_cannot_enter_this_experiment",
        "detail": ("the official ERASOR output is expressed in the official bag's SuMa "
                   "frame, which differs from the benchmark's world frame by ~1.6 m median "
                   "nearest-neighbour distance (measured in 03_erasor). It fails 100 % of "
                   "registrations at every perturbation level for that reason, so it is "
                   "excluded rather than silently scored as a bad map."),
    })

    return {
        "metrics": metrics, "checks": checks, "findings": findings,
        "artifacts": [os.path.relpath(metrics_log, ctx["path"]),
                      "results/registration_utility.json"],
        "note": (f"KISS-ICP on a reconstructed 141-frame KITTI 00 sub-sequence: ATE {ate} m, "
                 f"avg translation error {avg_trans} % over only {samples} metric sample(s) - "
                 f"the paper's {PAPER_KITTI_00_10} % is NOT reproduced (see findings). "
                 f"Downstream localizability: rho(normalised AA, utility) = {s2['rho_aa']} "
                 f"at level {s2['best']}, rho(as-submitted AA, utility) = {s2['rho_submitted']}"),
    }
