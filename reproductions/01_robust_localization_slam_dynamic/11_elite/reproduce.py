#!/usr/bin/env python3
"""01-11 · ELite — the official pipeline, on the authors' own ParkingLot data.

What this reproduces
--------------------
ELite (ICRA 2025) keeps a per-voxel *ephemerality* label across sessions, so a new
session's points are either merged into the permanent map, kept local, or treated
as temporary. The paper's main experiment is run on the authors' own LT-ParkingLot
sequence (sessions 01 and 02), and Table I reports map-alignment quality against
two baselines:

    LT-ParkingLot   ICP           AC 0.962   RMSE 0.117   CD 0.194
                    LT-mapper     AC 0.968   RMSE 0.121   CD 0.175
                    ELite         AC 0.969   RMSE 0.090   CD 0.133

So "reproducing ELite" here means: run the two upstream configs (build session 01's
map, then align + update with session 02), then compute AC/RMSE/CD with the
paper's own definition (§IV-A p.5) via work/evaluate_alignment.py.

What is manual, and is recorded
-------------------------------
Upstream's multi-session step needs one ICP initial guess between sessions; the
authors' current workflow does that by hand in CloudCompare (their README says a
Scan Context-based global localiser is planned). That initial transform is in
`work/parkinglot_headless.yaml` and is copied from the upstream config - it is the
authors' number, not something this driver invented, but the step is still manual
and is stated as a finding rather than glossed over.

Environment, and why it is not the system python
------------------------------------------------
`requirements.txt` pins `open3d==0.18.0`, which has no wheel for python 3.12; and
0.18.0 segfaults under NumPy 2 (PointCloud.transform). So this folder uses its own
env: python 3.10 + open3d 0.18.0 + numpy 1.26.4 + loguru, created with micromamba
(no sudo). Two upstream code paths needed a compatibility patch, both recorded in
work/local_patches.patch: an unconditional import of the optional pygicp matcher,
and per-frame `combined += pcd` accumulation that segfaults on Open3D 0.18.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

PAPER_TABLE_I = {"AC": 0.969, "RMSE": 0.090, "CD": 0.133,
                 "sequence": "LT-ParkingLot (sessions 01 and 02)"}
BASELINES = {"ICP": {"AC": 0.962, "RMSE": 0.117, "CD": 0.194},
             "LT-mapper": {"AC": 0.968, "RMSE": 0.121, "CD": 0.175}}

SESSIONS = ("01", "02")


def _elite_python(ctx):
    cand = os.path.join(ctx["repo_root"], "reproductions", ".venvs", "elite", "bin", "python")
    return cand if os.path.exists(cand) else None


def _upstream(ctx):
    return os.path.join(ctx["code_root"], "ELite")


def _session_dir(ctx, session):
    return os.path.join(_upstream(ctx), "data", "parkinglot", session)


def _outputs(ctx, session):
    return os.path.join(_session_dir(ctx, session), "outputs")


def _config(ctx, first):
    name = "parkinglot_first_headless.yaml" if first else "parkinglot_headless.yaml"
    return os.path.join(ctx["work_dir"], name)


def require(ctx):
    if not os.path.isdir(_upstream(ctx)):
        return ("official repo not cloned - git clone https://github.com/dongjae0107/ELite "
                + os.path.relpath(_upstream(ctx), ctx["path"]))
    for session in SESSIONS:
        scans = os.path.join(_session_dir(ctx, session), "Scans")
        if not os.path.isdir(scans):
            return (f"ParkingLot session {session} missing - the authors' zips come from Google "
                    "Drive and are quota-limited; reproductions/tools/gdrive_range_fetch.py pulls "
                    f"ranged chunks into {os.path.relpath(_session_dir(ctx, session), ctx['path'])}"
                    ".zip, then unzip Scans/ and poses.txt")
    py = _elite_python(ctx)
    if py is None:
        return ("the ELite env is missing - requirements pin open3d==0.18.0 (no py3.12 wheel) and "
                "0.18.0 segfaults under NumPy 2, so this folder needs its own python 3.10 env at "
                "reproductions/.venvs/elite with open3d==0.18.0, numpy<2, loguru (see README)")
    probe = subprocess.run([py, "-c", "import open3d, numpy, loguru; "
                                      "print(open3d.__version__, numpy.__version__)"],
                           capture_output=True, text=True)
    if probe.returncode != 0:
        return ("reproductions/.venvs/elite is broken - "
                f"{(probe.stderr or probe.stdout)[-300:]}")
    for first in (True, False):
        if not os.path.exists(_config(ctx, first)):
            return f"headless config missing: {_config(ctx, first)}"
    return None


def _run_stage(ctx, first, timeout_h):
    """Run one upstream config. cwd must be the upstream root (relative paths)."""
    py = _elite_python(ctx)
    r = subprocess.run([py, "run_elite.py", _config(ctx, first)],
                       cwd=_upstream(ctx), capture_output=True, text=True,
                       timeout=timeout_h * 3600)
    if r.returncode != 0:
        raise RuntimeError(f"ELite stage {'first' if first else 'update'} failed: "
                           + (r.stderr or r.stdout)[-1200:])


def run(ctx):
    # ------------------------------------------------------------- the pipeline
    # Both stages are cached: the first one takes ~75 min and the second ~45 min
    # on this CPU, and a re-run would just reproduce the same maps.
    s1_map = os.path.join(_outputs(ctx, "01"), "cleaned_session_map.pcd")
    s2_map = os.path.join(_outputs(ctx, "02"), "cleaned_session_map.pcd")
    if not os.path.exists(s1_map):
        _run_stage(ctx, first=True, timeout_h=4)
    if not os.path.exists(s2_map):
        _run_stage(ctx, first=False, timeout_h=4)

    lifelong = os.path.join(_outputs(ctx, "02"), "lifelong_map.pcd")

    # ----------------------------------------------------------- the metric
    py = _elite_python(ctx)
    pairs = [("session01_vs_session02", s1_map, s2_map)]
    if os.path.exists(lifelong):
        pairs.append(("session01_vs_lifelong02", s1_map, lifelong))

    scores = {}
    for tag, a, b in pairs:
        out = os.path.join(ctx["results_dir"], f"alignment_{tag}.json")
        r = subprocess.run([py, os.path.join(ctx["work_dir"], "evaluate_alignment.py"),
                            "--a", a, "--b", b, "--sigma", "0.5", "--label-a", "session 01",
                            "--label-b", "session 02 (ELite-aligned)", "--out", out],
                           capture_output=True, text=True, timeout=6 * 3600)
        if r.returncode != 0:
            raise RuntimeError(f"evaluate_alignment.py failed for {tag}: "
                               + (r.stderr or r.stdout)[-800:])
        with open(out, encoding="utf-8") as fh:
            scores[tag] = json.load(fh)

    primary = scores["session01_vs_session02"]
    metrics = {
        "AC": primary["AC"], "RMSE_m": primary["RMSE_m"], "CD_m": primary["CD_m"],
        "points_session01": primary["points_a"], "points_session02": primary["points_b"],
        "paper_AC": PAPER_TABLE_I["AC"], "paper_RMSE": PAPER_TABLE_I["RMSE"],
        "paper_CD": PAPER_TABLE_I["CD"],
        "AC_diff": round(primary["AC"] - PAPER_TABLE_I["AC"], 4),
        "RMSE_ratio": round(primary["RMSE_m"] / PAPER_TABLE_I["RMSE"], 4) if primary["RMSE_m"] else None,
        "CD_ratio": round(primary["CD_m"] / PAPER_TABLE_I["CD"], 4) if primary["CD_m"] else None,
    }

    checks = [
        {
            "name": "both_sessions_produced_maps",
            "ok": os.path.exists(s1_map) and os.path.exists(s2_map),
            "detail": (f"session 01 {primary['points_a']:,} points, "
                       f"session 02 {primary['points_b']:,} points, after the upstream "
                       "two-config pipeline (build, then align + update)"),
        },
        {
            "name": "metrics_computed_with_the_papers_definition",
            "ok": all(metrics[k] is not None for k in ("AC", "RMSE_m", "CD_m")),
            "detail": (f"sigma_inlier = {primary['sigma_inlier_m']} m, NN correspondences, "
                       f"AC = inlier ratio, RMSE = RMS inlier distance, CD = bidirectional sum "
                       f"of average inlier distance (work/evaluate_alignment.py)"),
        },
        {
            "name": "alignment_quality_is_in_the_papers_range",
            "ok": metrics["AC"] >= 0.90 and (metrics["RMSE_m"] or 1e9) <= 0.30,
            "detail": (f"AC {metrics['AC']:.3f} (paper {PAPER_TABLE_I['AC']}), "
                       f"RMSE {metrics['RMSE_m']:.3f} m (paper {PAPER_TABLE_I['RMSE']}), "
                       f"CD {metrics['CD_m']:.3f} m (paper {PAPER_TABLE_I['CD']}). A collapse "
                       "here would mean the two sessions were not aligned at all"),
        },
    ]

    findings = [
        {
            "name": "paper_table_i_row",
            "detail": (f"LT-ParkingLot (sessions 01+02), AC/RMSE/CD = "
                       f"{metrics['AC']:.3f} / {metrics['RMSE_m']:.3f} / {metrics['CD_m']:.3f} "
                       f"against the paper's ELite row {PAPER_TABLE_I['AC']} / "
                       f"{PAPER_TABLE_I['RMSE']} / {PAPER_TABLE_I['CD']}; the same table's "
                       f"baselines are ICP {BASELINES['ICP']} and LT-mapper "
                       f"{BASELINES['LT-mapper']}. The paper does not say which two clouds it "
                       "measures, so the choice is on the command line and echoed into the "
                       "result JSON - see the finding below."),
        },
        {
            "name": "the_multi_session_step_needs_a_manual_icp_guess",
            "detail": ("upstream's alignment needs one initial transform between sessions. The "
                       "authors currently obtain it by hand in CloudCompare (their README says a "
                       "Scan Context global localiser is planned), and this reproduction feeds the "
                       "transform from their own config unchanged. So the pipeline is not "
                       "end-to-end automatic, and the number below inherits that initial guess."),
        },
        {
            "name": "the_dataset_itself_was_quota_limited",
            "detail": ("ParkingLot comes from Google Drive with a per-file download quota: plain "
                       "downloads return a 2009-byte 'Quota exceeded' page, while 1 MB ranged "
                       "requests keep working (observed: fine up to ~224 MB, then nothing). "
                       "reproductions/tools/gdrive_range_fetch.py pulls both zips in ranged chunks "
                       "which is why this folder has data at all."),
        },
        {
            "name": "open3d_0_18_needs_numpy_1_x_and_two_source_patches",
            "detail": ("recorded in work/local_patches.patch: (1) map_zipper.py imports the "
                       "optional pygicp matcher unconditionally, but that matcher is not on PyPI "
                       "(needs fast_gicp built from source) - wrapped in try/except, and the "
                       "config uses Open3DScanMatcher anyway; (2) per-frame `combined += pcd` "
                       "accumulation segfaults on Open3D 0.18 - replaced by one np.vstack, same "
                       "points, no algorithm change. Neither patch touches the ephemerality "
                       "logic that the paper is about."),
        },
    ]
    if len(scores) > 1:
        alt = scores["session01_vs_lifelong02"]
        findings.append({
            "name": "the_choice_of_second_cloud_moves_the_metric",
            "detail": (f"measuring session 01 against session 02's own cleaned map gives "
                       f"AC {primary['AC']:.3f} / RMSE {primary['RMSE_m']:.3f} / "
                       f"CD {primary['CD_m']:.3f}, and against the merged lifelong map "
                       f"{alt['AC']:.3f} / {alt['RMSE_m']:.3f} / {alt['CD_m']:.3f}. The paper "
                       "does not specify which one Table I uses, so both are recorded rather "
                       "than one being presented as 'the' number."),
        })

    return {
        "metrics": metrics,
        "checks": checks,
        "findings": findings,
        "artifacts": [f"results/alignment_{tag}.json" for tag, _, _ in pairs],
        "note": (f"ELite on LT-ParkingLot sessions 01+02 (official two-config pipeline): "
                 f"AC {metrics['AC']:.3f} / RMSE {metrics['RMSE_m']:.3f} m / "
                 f"CD {metrics['CD_m']:.3f} m vs paper {PAPER_TABLE_I['AC']} / "
                 f"{PAPER_TABLE_I['RMSE']} / {PAPER_TABLE_I['CD']}"),
    }
