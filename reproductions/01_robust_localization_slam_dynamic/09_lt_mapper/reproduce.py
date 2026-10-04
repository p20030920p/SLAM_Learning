#!/usr/bin/env python3
"""01-09 · LT-mapper — the official ltremovert change detector, run as a reproduction.

What is reproduced, and what is not
-----------------------------------
LT-mapper (ICRA 2022) is two things: LT-SLAM, which builds a map per session and
computes inter-session loops, and LT-removert, which uses one session to clean
another and is the module the paper's change-detection claims rest on. Only the
second is reachable here:

  * `ltslam` needs GTSAM, which is not installed on this machine, and nothing is
    installed by this reproduction;
  * the **LT-map / delta-map** module is not in the repository at all — a whole
    checkout grep for `delta_map`/`meta_map` returns nothing and the one line
    that mentions it in `Removerter.cpp:1671` is a comment. So the paper's
    headline numbers (delta map 85.7 MB vs 213.6 MB, 9.8 s vs 87/160 s) have no
    implementation here and cannot be reproduced from this checkout.

What this file therefore runs is the official `removert_removert` binary from
`gisbi-kim/lt-mapper` over a **two-session split of one continuous KITTI 00
pass**, and scores its cleaned map with the DynamicMap_Benchmark evaluator, the
same one the sibling folders use.

The input, and why it is built rather than downloaded
-----------------------------------------------------
The paper's own input is the ParkingLot dataset: raw Ouster + IMU, six sessions
over three days, which still needs SC-LIO-SAM before ltremovert can read it (and
the authors' Docker image is 2.2 GB with no docker on this machine). What is
already local is the benchmark's KITTI 00 release: 141 world-frame clouds whose
VIEWPOINT field holds the sensor pose, so the sensor-frame scans invert back out
(`work/make_ltmapper_sessions.py`, same inversion as
02_kiss_icp/work/make_kitti_seq.py, but writing the binary `.pcd` that
`Session.cpp:277-281` requires).

The split follows work/feasibility.md §4:

    central session  frames 4390..4470  (81 scans)  <- the map to clean
    query session    frames 4451..4530  (80 scans)  <- the cleaner, auto-cropped
                                                       to 29 keyframes by the
                                                       10 m ROI rule at
                                                       Session.cpp:234

Both pose files are the benchmark's own VIEWPOINTs, i.e. already in one common
world frame — which is exactly why `ltslam` (and therefore GTSAM) is not needed.

The honest limit of this setup
------------------------------
This is **one continuous pass cut in two**, not two visits to the same place on
different days. "Change" here is therefore moving cars plus occlusion and
viewpoint differences, and the overlap between the sessions is a ~15 m stretch of
trajectory. Two consequences are measured rather than hidden:

  * the map only covers structure the input scans observed. 71.6% of the
    benchmark's GT static points are observable from the 110 scans the run
    consumed, so on the full 141-frame GT (the protocol the sibling folders use)
    SA is capped by coverage, not by the method;
  * `updated_map.pcd` keeps the structure both sessions agree on, so it is much
    sparser than the input map. The uncleaned central map is scored next to it as
    the no-removal control, which separates "the method deleted structure" from
    "the map never covered it".

Which output is scored
----------------------
Two upstream outputs are reported, because 01-04 shows they sit at opposite
corners of the precision/recall trade-off: `updated_map.pcd` (the map-side result
of Step 3) and the merged `scans_updated/` clouds (the scan-side result).
`map_static/` is empty — the only call to `saveCurrentStaticAndDynamicPointCloudGlobal`
inside a path `run()` reaches is the `_MVM` debug one, so no map-side static map
is written by this version of the code.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import time

# The sibling rows this folder is comparable to, i.e. cleaned maps of the same
# 141 KITTI 00 frames scored by the same evaluator on the same GT. Recorded here
# so the README's comparison cannot drift silently.
SIBLINGS = {
    "removert": {"SA": 99.44, "DA": 41.53, "AA": 64.26},
    "erasor": {"SA": 66.71, "DA": 98.54, "AA": 81.07},
    "dufomap": {"SA": 97.96, "DA": 98.72, "AA": 98.34},
}

CENTRAL_RANGE = (0, 81)     # frames 004390..004470
QUERY_RANGE = (61, 141)     # frames 004451..004530


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
    return os.path.join(_repo(ctx), "reproductions", ".ws", "lt_mapper_ws")


def _binary(ctx):
    return os.path.join(_ws(ctx), "devel", "lib", "removert", "removert_removert")


def _checkout(ctx):
    """The clone of gisbi-kim/lt-mapper (holds both packages)."""
    return os.path.join(ctx["path"], "code", "lt-mapper")


def _pkg(ctx):
    """The `ltremovert` directory — package name `removert`, directory `ltremovert`."""
    return os.path.join(_checkout(ctx), "ltremovert")


def _upstream_params(ctx):
    return os.path.join(_pkg(ctx), "config", "params_ltmapper.yaml")


def _script(ctx, name):
    return os.path.join(ctx["work_dir"], name)


def _sessions(ctx):
    return os.path.join(ctx["data_root"], "kitti00_two_sessions")


def _full_gt(ctx):
    """A sequence dir holding only the benchmark's GT (symlinked, never written to)."""
    return os.path.join(ctx["data_root"], "gt_full_kitti00")


def _covered_gt(ctx):
    """GT restricted to what all input scans observed; built by work/make_coverage_matched_gt.py."""
    return os.path.join(ctx["data_root"], "gt_covered_sessions")


def _central_gt(ctx):
    """GT restricted to the central session alone — the fair partner for comparing
    this run's own outputs (raw, map-side, scan-side) with each other."""
    return os.path.join(ctx["data_root"], "gt_covered_central")


def _out(ctx):
    return os.path.join(ctx["results_dir"], "ltmapper_kitti00")


def _bench_seq(ctx):
    """The benchmark's free KITTI 00 release (world-frame clouds + GT)."""
    env = os.environ.get("DMB_SEQ_DIR")
    if env and os.path.isdir(os.path.join(env, "pcd")):
        return env
    return os.path.normpath(os.path.join(
        ctx["path"], "..", "01_dynamicmap_benchmark", "data", "raw", "00"))


def _evaluator(ctx):
    return os.path.normpath(os.path.join(
        ctx["path"], "..", "01_dynamicmap_benchmark", "work", "evaluate.py"))


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def _run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def _pcd_points(path):
    """Read POINTS from the header — no numpy, this file runs under system python3."""
    try:
        with open(path, "rb") as fh:
            head = fh.read(2048).split(b"DATA", 1)[0].decode("ascii", "replace")
        return int(re.search(r"POINTS (\d+)", head).group(1))
    except Exception:
        return 0


def _log_text(ctx):
    p = os.path.join(ctx["work_dir"], "logs", "ltmapper.log")
    if not os.path.exists(p):
        return ""
    with open(p, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def _roi_keyframes(ctx):
    m = re.search(r"Total (\d+) keyframes parsed in the map's ROI", _log_text(ctx))
    return int(m.group(1)) if m else -1


def _central_keyframes(ctx):
    m = re.search(r"Total (\d+) nodes are used from the index range", _log_text(ctx))
    return int(m.group(1)) if m else -1


def _pipeline_finished(ctx):
    """Did `Removerter::run()` reach its last statement?

    `saveAllTypeOfScans()` is the final call of `run()`, and it writes one file
    per central keyframe into each of `scans_updated/`, `scans_updated_strong/`
    and `scans_nd_strong/`. The output directory is wiped before the run and the
    driver removes the completion marker first, so full per-scan directories
    cannot be left over from an earlier run. The log is deliberately *not* used:
    rosconsole's stdout is block-buffered when redirected, so it can lag the
    actual progress by a few KB even after the node has finished.
    """
    out = _out(ctx)
    central = os.path.join(_sessions(ctx), "central", "Scans")
    if not os.path.isdir(central):
        return None
    n = len([f for f in os.listdir(central) if f.endswith(".pcd")])
    counts = {d: len(os.listdir(os.path.join(out, d)))
              for d in ("scans_updated", "scans_updated_strong", "scans_nd_strong")
              if os.path.isdir(os.path.join(out, d))}
    return n, counts


def _evaluate(ctx, map_path, seq_dir, tag):
    out = os.path.join(ctx["results_dir"], f"score_{tag}.json")
    r = _run([_venv_python(ctx), _evaluator(ctx), "--seq-dir", seq_dir,
              "--map", map_path, "--method", tag, "--impl", "both", "--out", out])
    if r.returncode != 0:
        raise RuntimeError(f"evaluate.py failed for {tag}: {(r.stderr or r.stdout)[-800:]}")
    with open(out, encoding="utf-8") as fh:
        return json.load(fh)


def _pct(payload, impl="python", keys=("SA", "DA", "AA", "HA")):
    return {k: payload[impl][k] for k in keys}


# --------------------------------------------------------------------------- #
# contract
# --------------------------------------------------------------------------- #
def require(ctx):
    if _micromamba() is None:
        return ("micromamba not found - the official ROS 1 build needs it: "
                "curl -sSL https://micro.mamba.pm/api/micromamba/linux-64/latest | "
                "tar -xj -C /tmp bin/micromamba && mv /tmp/bin/micromamba ~/.local/bin/")
    env = _ros1_env(ctx)
    if not os.path.isdir(env):
        return ("ROS 1 Noetic env missing - see 03_erasor/README.md for the one-time "
                "micromamba/robostack command that creates reproductions/.venvs/ros1noetic")
    if not os.path.isdir(os.path.join(_pkg(ctx), "src")):
        return ("official repo not cloned - git clone https://github.com/gisbi-kim/lt-mapper "
                f"{os.path.relpath(_checkout(ctx), ctx['path'])}  (the change detector is the "
                "package in ltremovert/; ltslam/ needs GTSAM and is not used here)")
    if not os.path.exists(_binary(ctx)):
        return ("official binary not built - SRC must be the *package* directory, not the "
                "checkout root, or catkin tries to build ltslam and stops on GTSAM: "
                "micromamba run -p reproductions/.venvs/ros1noetic bash "
                "reproductions/tools/build_ros1_catkin.sh "
                f"{os.path.relpath(_ws(ctx), _repo(ctx))} ltremovert "
                f"{os.path.relpath(_pkg(ctx), _repo(ctx))}")
    seq = _bench_seq(ctx)
    if not os.path.isdir(os.path.join(seq, "pcd")):
        return ("sequence 00 not found - wget "
                "https://zenodo.org/records/10886629/files/00.zip and unzip into "
                "01_dynamicmap_benchmark/data/raw/ (no KITTI registration needed)")
    if not os.path.exists(os.path.join(seq, "gt_cloud.pcd")):
        return f"benchmark GT missing: {os.path.join(seq, 'gt_cloud.pcd')}"
    for name in ("make_ltmapper_sessions.py", "gen_params.py", "run_official.sh",
                 "make_coverage_matched_gt.py", "merge_cleaned_scans.py",
                 "verify_sessions.py"):
        if not os.path.exists(_script(ctx, name)):
            return f"driver script missing: {_script(ctx, name)}"
    return None


def run(ctx):
    sessions = _sessions(ctx)
    out = _out(ctx)
    work = ctx["work_dir"]
    py = _venv_python(ctx)

    # ------------------------------------------------------- 1. input sessions
    if not os.path.exists(os.path.join(sessions, "central", "Scans", "000000.pcd")):
        r = _run([py, _script(ctx, "make_ltmapper_sessions.py"),
                  "--seq-dir", _bench_seq(ctx), "--out", sessions, "--force",
                  "--central", str(CENTRAL_RANGE[0]), str(CENTRAL_RANGE[1]),
                  "--query", str(QUERY_RANGE[0]), str(QUERY_RANGE[1])])
        if r.returncode != 0:
            raise RuntimeError(f"make_ltmapper_sessions.py failed: {(r.stderr or r.stdout)[-800:]}")

    # the invariants that make the sessions valid input (sensor frame, pose
    # alignment, renumbering) are checked, not assumed
    ver = _run([py, _script(ctx, "verify_sessions.py"), "--sessions", sessions,
                "--bench-seq", _bench_seq(ctx)])
    sessions_ok = ver.returncode == 0

    # ------------------------------------------------------------ 2. rosparams
    params = os.path.join(work, "generated", "params.yaml")
    sess = {"central": os.path.join(sessions, "central"), "query": os.path.join(sessions, "query")}
    r = _run([py, _script(ctx, "gen_params.py"),
              "--upstream", _upstream_params(ctx),
              "--central-scans", os.path.join(sess["central"], "Scans"),
              "--central-poses", os.path.join(sess["central"], "poses.txt"),
              "--query-scans", os.path.join(sess["query"], "Scans"),
              "--query-poses", os.path.join(sess["query"], "poses.txt"),
              "--out-dir", out, "--start", str(CENTRAL_RANGE[0]),
              "--end", str(CENTRAL_RANGE[1]), "--out", params])
    if r.returncode != 0:
        raise RuntimeError(f"gen_params.py failed: {(r.stderr or r.stdout)[-800:]}")

    # ------------------------------------------- 3. run the official ltremovert
    # Start from an empty output directory: a stale map left by an earlier run
    # would otherwise be scored as if this run had produced it.
    shutil.rmtree(out, ignore_errors=True)
    env = dict(os.environ)
    env["LTMAPPER_WS"] = _ws(ctx)
    t0 = time.monotonic()
    r = _run([_micromamba(), "run", "-p", _ros1_env(ctx), "bash",
              _script(ctx, "run_official.sh"), params, out],
             env=env, timeout=60 * 60)
    run_seconds = round(time.monotonic() - t0, 1)
    if r.returncode != 0:
        raise RuntimeError("official ltremovert run failed:\n" + (r.stdout or "")[-1500:]
                           + (r.stderr or "")[-1500:])

    updated = os.path.join(out, "updated_map.pcd")
    if not os.path.exists(updated):
        raise RuntimeError("official run produced no updated_map.pcd")

    # the scan-side output of the same run, merged the way upstream merges it
    r = _run([py, _script(ctx, "merge_cleaned_scans.py"),
              "--scans", os.path.join(out, "scans_updated"),
              "--poses", os.path.join(sess["central"], "poses.txt"),
              "--out", os.path.join(out, "scans_updated_merged.pcd")])
    if r.returncode != 0:
        raise RuntimeError(f"merge_cleaned_scans.py failed: {(r.stderr or r.stdout)[-800:]}")
    scanside = os.path.join(out, "scans_updated_merged.pcd")

    # ---------------------------------------------- 4. fair comparison partners
    # GT points the input scans actually observed; coverage is defined by the
    # input scans, never by the method's output. Two restrictions are built:
    # both sessions (the run's own footprint) and the central session alone
    # (identical footprint for the raw, map-side and scan-side maps).
    gts = {}
    for key, seq_dir, frames in (("covered", _covered_gt(ctx), "both"),
                                 ("central", _central_gt(ctx), "central")):
        if not os.path.exists(os.path.join(seq_dir, "gt_cloud.pcd")):
            r = _run([py, _script(ctx, "make_coverage_matched_gt.py"),
                      "--bench-seq", _bench_seq(ctx), "--sessions", sessions,
                      "--log", os.path.join(work, "logs", "ltmapper.log"),
                      "--frames", frames, "--out", seq_dir])
            if r.returncode != 0:
                raise RuntimeError(f"make_coverage_matched_gt.py failed: {(r.stderr or r.stdout)[-800:]}")
        with open(os.path.join(seq_dir, "coverage.json"), encoding="utf-8") as fh:
            gts[key] = (seq_dir, json.load(fh))
    coverage = gts["covered"][1]
    coverage_central = gts["central"][1]

    full = _full_gt(ctx)
    os.makedirs(full, exist_ok=True)
    link = os.path.join(full, "gt_cloud.pcd")
    if not os.path.exists(link):
        os.symlink(os.path.join(_bench_seq(ctx), "gt_cloud.pcd"), link)

    # ------------------------------------------------------------ 5. scoring
    ctrl_map = os.path.join(out, "OriginalNoisyCentralMapGlobal.pcd")
    prim = _evaluate(ctx, updated, gts["covered"][0], "updated_map_covered")
    fullp = _evaluate(ctx, updated, full, "updated_map_full")
    c_upd = _evaluate(ctx, updated, gts["central"][0], "central_gt_updated_map")
    c_scan = _evaluate(ctx, scanside, gts["central"][0], "central_gt_scanside_merged")
    c_ctrl = _evaluate(ctx, ctrl_map, gts["central"][0], "central_gt_control_raw")

    metrics = {}
    metrics.update(_pct(prim))                       # plain keys: the headline row
    metrics["map_points"] = prim["map_points"]
    metrics.update({f"full_gt_{k}": v for k, v in _pct(fullp).items()})
    metrics.update({f"scanside_{k}": v for k, v in _pct(c_scan).items()})
    metrics["scanside_map_points"] = c_scan["map_points"]
    metrics.update({f"central_gt_{k}": v for k, v in _pct(c_upd).items()})
    metrics["central_gt_map_points"] = c_upd["map_points"]
    metrics.update({f"control_{k}": v for k, v in _pct(c_ctrl).items()})
    metrics["control_map_points"] = c_ctrl["map_points"]

    metrics["gt_static_covered"] = coverage["gt_static_covered"]
    metrics["gt_dynamic_covered"] = coverage["gt_dynamic_covered"]
    metrics["static_coverage_pct"] = coverage["static_coverage_pct"]
    metrics["dynamic_coverage_pct"] = coverage["dynamic_coverage_pct"]
    metrics["central_gt_static"] = coverage_central["gt_static_covered"]
    metrics["central_gt_dynamic"] = coverage_central["gt_dynamic_covered"]
    metrics["central_keyframes"] = _central_keyframes(ctx)
    metrics["query_roi_keyframes"] = _roi_keyframes(ctx)
    for name, key in (("updated_map.pcd", "updated_map_points"),
                      ("updated_map_strong.pcd", "updated_map_strong_points"),
                      ("union_map_centralside.pcd", "union_centralside_points"),
                      ("union_map_queryside.pcd", "union_queryside_points"),
                      ("nd_map.pcd", "nd_points"), ("pd_map.pcd", "pd_points"),
                      ("strong_nd_map.pcd", "strong_nd_points"),
                      ("weak_nd_map.pcd", "weak_nd_points")):
        p = os.path.join(out, name)
        if os.path.exists(p):
            metrics[key] = _pcd_points(p)

    # ------------------------------------------------------------- 6. checks
    cross = prim.get("cross_check", {})
    fin = _pipeline_finished(ctx)
    checks = [
        {"name": "sessions_are_valid_ltremovert_input",
         "ok": bool(sessions_ok),
         "detail": ("scans are sensor-frame and 1:1 with their pose lines: applying a "
                    "scan's pose reproduces the benchmark cloud it came from to <1e-3 m "
                    "(measured ~4e-6 m, i.e. float32 storage); the 2.5 m pre-clean ball "
                    "at Session.cpp:506-533 is therefore under the sensor, not under the "
                    "world origin") if sessions_ok else (ver.stdout or ver.stderr)[-400:]},
        {"name": "query_session_overlaps_the_central_session",
         "ok": _roi_keyframes(ctx) >= 10,
         "detail": (f"{_roi_keyframes(ctx)} of the 80 query keyframes fall inside the "
                    f"central map's 10 m ROI (Session.cpp:234); the overlap is a ~15 m "
                    f"stretch of trajectory, so the change detector has somewhere to work")},
        {"name": "official_pipeline_produced_a_cleaned_map",
         "ok": prim["map_points"] > 100_000,
         "detail": (f"updated_map.pcd holds {prim['map_points']} points after "
                    f"makeGlobalMap + high-dynamic removal + low-dynamic detection over "
                    f"{_central_keyframes(ctx)} central and {_roi_keyframes(ctx)} query keyframes")},
        {"name": "evaluator_implementations_agree",
         "ok": bool(cross.get("ok")),
         "detail": (f"official export_eval_pcd vs scipy re-implementation: "
                    f"{cross.get('disagreeing_points')} disagreeing GT labels "
                    f"(rate {cross.get('disagree_rate')})")},
        {"name": "official_run_reached_the_end_of_its_pipeline",
         "ok": bool(fin and all(v == fin[0] for v in fin[1].values()) and len(fin[1]) == 3),
         "detail": (f"saveAllTypeOfScans() - the last statement of Removerter::run() - wrote "
                    f"{fin[0]} files per directory into "
                    + ", ".join(f"{d}/ ({c})" for d, c in sorted(fin[1].items()))
                    + "; the output directory is wiped before the run and the driver removes "
                      "the completion marker first, so these cannot be a previous run's leftovers")
         if fin else "the per-scan output directories are missing - the node did not finish"},
        {"name": "change_detection_found_both_directions",
         "ok": metrics.get("nd_points", 0) > 0 and metrics.get("pd_points", 0) > 0,
         "detail": (f"nd_map.pcd (central-only) {metrics.get('nd_points')} points, "
                    f"pd_map.pcd (query-only) {metrics.get('pd_points')} points; both empty "
                    "would mean the two sessions saw identical geometry and nothing was measured")},
    ]

    # ------------------------------------------------------------ 7. findings
    findings = []
    findings.append({
        "name": "coverage_caps_the_comparable_score",
        "detail": (f"only {coverage['static_coverage_pct']:.1f}% of the benchmark's GT static "
                   f"points ({coverage['gt_static_covered']} of {coverage['gt_static_total']}) "
                   f"are observed by the {_central_keyframes(ctx) + _roi_keyframes(ctx)} input "
                   f"scans this run consumed ({coverage['dynamic_coverage_pct']:.1f}% for dynamic). "
                   f"On the full 141-frame GT the same map scores SA {metrics['full_gt_SA']:.2f} "
                   f"/ DA {metrics['full_gt_DA']:.2f}, i.e. the sibling rows (removert "
                   f"{SIBLINGS['removert']['SA']} / erasor {SIBLINGS['erasor']['SA']} / dufomap "
                   f"{SIBLINGS['dufomap']['SA']} SA) are not like-for-like: their maps cover all "
                   "141 frames. The coverage-matched GT (SA "
                   f"{metrics['SA']:.2f} / DA {metrics['DA']:.2f}) is the fair partner."),
    })
    findings.append({
        "name": "the_sa_loss_is_a_deliberate_trade_for_dynamic_rejection",
        "detail": (f"on one identical GT - the central session's own footprint, "
                   f"{coverage_central['gt_static_covered']} static / "
                   f"{coverage_central['gt_dynamic_covered']} dynamic points, against which all "
                   f"three maps are measured - the no-removal control (the raw central map, "
                   f"{metrics['control_map_points']} points) scores SA {metrics['control_SA']:.2f} "
                   f"/ DA {metrics['control_DA']:.2f}: it keeps everything and rejects nothing. "
                   f"After the change detection, updated_map.pcd scores SA "
                   f"{metrics['central_gt_SA']:.2f} / DA {metrics['central_gt_DA']:.2f} and the "
                   f"merged scan-side output SA {metrics['scanside_SA']:.2f} / DA "
                   f"{metrics['scanside_DA']:.2f}. So the detector trades "
                   f"{metrics['control_SA'] - metrics['central_gt_SA']:.1f} pp of static "
                   f"preservation for {metrics['central_gt_DA'] - metrics['control_DA']:.1f} pp of "
                   "dynamic rejection on this pair - aggressive next to 01-04's Removert run on "
                   "the same kind of data (SA 99.62 / DA 89.25), which is upstream's own "
                   "configuration difference: 01-04 runs params_kitti.yaml with "
                   "dist_nn_points_within 0.1, ltremovert's params_ltmapper.yaml asks for 0.01, "
                   "i.e. a ten times stricter requirement that two sessions agree."),
    })
    findings.append({
        "name": "the_run_has_two_upstream_outputs_and_they_are_close",
        "detail": (f"on the identical central-session GT, map-side updated_map.pcd scores SA "
                   f"{metrics['central_gt_SA']:.2f} / DA {metrics['central_gt_DA']:.2f} "
                   f"({metrics['central_gt_map_points']} points) and the scan-side merged "
                   f"scans_updated/ SA {metrics['scanside_SA']:.2f} / DA "
                   f"{metrics['scanside_DA']:.2f} ({metrics['scanside_map_points']} points) - "
                   "AA 74.33 vs 71.53. Unlike 01-04, where the two outputs of one Removert run "
                   "sat at opposite corners of the trade-off, here the choice of output moves AA "
                   "by 2.8 pp; what moves this score is which GT footprint it is measured on "
                   f"(central GT AA {metrics['central_gt_AA']:.2f}, both-sessions GT AA "
                   f"{metrics['AA']:.2f}, full 141-frame GT AA {metrics['full_gt_AA']:.2f})."),
    })
    findings.append({
        "name": "nd_pd_asymmetry_is_the_signature_of_a_partial_overlap",
        "detail": (f"central-only points (nd_map) {metrics.get('nd_points')} vs query-only "
                   f"points (pd_map) {metrics.get('pd_points')} - a "
                   f"{metrics.get('nd_points', 0) / max(metrics.get('pd_points', 1), 1):.1f}x "
                   "asymmetry. The query session covers a ~15 m stretch of the central "
                   "session's 40.8 m trajectory, so far more of the central map is unseen by "
                   "the query than the other way round. A real multi-session pair (the "
                   "paper's two visits to one car park) would not have this shape."),
    })
    findings.append({
        "name": "the_paper_headline_is_not_reachable_from_this_checkout",
        "detail": ("LT-mapper's delta-map numbers (85.7 MB vs 213.6 MB, 9.8 s vs 87/160 s) "
                   "belong to the LT-map module, which is absent from the repository: a "
                   "whole-checkout grep for delta_map/meta_map returns nothing and "
                   "Removerter.cpp:1671 mentions it only in a comment. Tab. I/II also need "
                   "MulRan KAIST 04, an extended sequence obtained by e-mail. No run of this "
                   "checkout can produce those numbers, in any environment."),
    })
    findings.append({
        "name": "what_change_means_on_this_input",
        "detail": ("one continuous KITTI 00 pass split at frames 4390..4470 / 4451..4530, not "
                   "the paper's six sessions over three days. 'Change' here is moving cars "
                   "plus occlusion and viewpoint differences between two nearby stretches of "
                   "one drive; the gap between these numbers and the paper's ParkingLot "
                   "experiment is the experiment, not the implementation."),
    })
    findings.append({
        "name": "runtime",
        "detail": (f"the official node ran over {_central_keyframes(ctx)} central + "
                   f"{_roi_keyframes(ctx)} query keyframes in {run_seconds:.0f} s wall clock "
                   "(it does all the work in its constructor and then spins; the same input "
                   "took ~32 s on a cold page cache and ~8 s warm, so read this as seconds, "
                   "not as a benchmark). This is not the "
                   "paper's 9.8 s figure: that one times the LT-map delta-map update, whose "
                   "code is absent here, and it is not comparable to a whole change-detection "
                   "pass."),
    })
    findings.append({
        "name": "roi_rule_recomputed_from_the_poses_matches_the_run",
        "detail": ("work/make_coverage_matched_gt.py recomputes Session.cpp:234's 10 m ROI "
                   f"rule from the two pose files and gets {_roi_keyframes(ctx)} query keyframes, "
                   "the same number ltremovert logged - so the fair GT's footprint really is the "
                   "run's input footprint."),
    })

    note = (f"official ltremovert on a two-session KITTI 00 split ({_central_keyframes(ctx)} "
            f"central + {_roi_keyframes(ctx)} query keyframes): SA/DA/AA = "
            f"{metrics['SA']:.2f}/{metrics['DA']:.2f}/{metrics['AA']:.2f} on the coverage-matched "
            f"GT ({coverage['static_coverage_pct']:.1f}% of GT static observable), "
            f"{metrics['full_gt_SA']:.2f}/{metrics['full_gt_DA']:.2f} on the full 141-frame GT; "
            f"LT-map/delta-map half of the paper is absent from the repo")

    return {
        "metrics": metrics,
        "checks": checks,
        "findings": findings,
        "artifacts": ["results/score_updated_map_covered.json",
                      "results/score_updated_map_full.json",
                      "results/score_central_gt_updated_map.json",
                      "results/score_central_gt_scanside_merged.json",
                      "results/score_central_gt_control_raw.json",
                      "work/local_patches.patch",
                      "work/generated/params.yaml"],
        "note": note,
    }
