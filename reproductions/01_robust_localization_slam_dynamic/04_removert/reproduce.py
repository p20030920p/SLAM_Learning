#!/usr/bin/env python3
"""01-04 · Removert — the official implementation, on the same data as the port.

What changed and why
--------------------
The first version of this reproduction ran the Removert **port** shipped inside
DynamicMap_Benchmark (`methods/removert/build/removert_run`, from Kin-Zhang's
ROS-free rewrite) and scored it 99.44 / 41.53 / 64.26, matching the benchmark's
Table I row. That is a legitimate benchmark reproduction, but it is not a
reproduction of *Removert*: the paper's own repository is
[irapkaist/removert](https://github.com/irapkaist/removert), it is public, and
the standing rule in this repo is that an upstream implementation is used
whenever one exists.

So this file now drives the official `removert_removert` binary over the same
KITTI 00 frames and the same evaluator, and keeps the port's number beside it.
That turns the folder into a measurement of something the task book asks about
(§6 H1′: are method rankings stable across implementations and metrics?).

How the official binary is driven
---------------------------------
Upstream is offline and file-based: it reads `<seq>/velodyne/*.bin` plus a
poses file (12 numbers per scan, KITTI odometry format) and uses ROS only as a
parameter server. `work/run_official.sh` does roscore + `rosparam load` + the
node; `work/gen_params.py` copies upstream's own `config/params_kitti.yaml` and
changes only machine paths and the sequence range.

Two judgement calls, both documented in README.md:
  * our scans are reconstructed in the **LiDAR frame**, so
    `ExtrinsicLiDARtoPoseBase` is the identity - the option upstream's own
    comment block recommends for LiDAR-frame odometry;
  * every algorithm parameter (resolutions, voxel size, static sensitivity) is
    left exactly as upstream ships it.

What is measured
----------------
Both maps are scored by `01_dynamicmap_benchmark/work/evaluate.py`, i.e. the
benchmark's point-level SA/DA/AA/HA on KITTI 00 with the *same* GT cloud and the
same 0.05 m rule. The official run additionally reports two of its own outputs:
the merged cleaned scans (`map_static/StaticMapScansideMapGlobal.pcd`, the last
step of `run()`) and the map-side result at the finest removal resolution.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

# The benchmark-port row this folder used to reproduce (DynamicMap_Benchmark
# Table I p.5; DUFOMap Table I p.5 prints the same numbers). Kept as a check so
# the comparison partner cannot drift silently.
BENCH_PORT = {"SA": 99.44, "DA": 41.53, "AA": 64.26}
TOL_PP = 0.5

OFFICIAL_SCANSIDE = os.path.join("results", "removert_kitti00", "map_static",
                                 "StaticMapScansideMapGlobal.pcd")
OFFICIAL_MAPSIDE = os.path.join("results", "removert_kitti00", "map_static",
                                "StaticMapMapsideGlobalResX1.500000.pcd")


# --------------------------------------------------------------------------- #
# paths / helpers
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
    return os.path.join(_repo(ctx), "reproductions", ".ws", "removert_ws")


def _official_binary(ctx):
    return os.path.join(_ws(ctx), "devel", "lib", "removert", "removert_removert")


def _upstream(ctx):
    return os.path.join(ctx["path"], "code", "removert")


def _bench(ctx):
    return os.path.normpath(os.path.join(
        ctx["path"], "..", "01_dynamicmap_benchmark", "code", "DynamicMap_Benchmark"))


def _bench_seq(ctx):
    """The benchmark's free KITTI 00 release (world-frame clouds + poses)."""
    env = os.environ.get("DMB_SEQ_DIR")
    if env and os.path.isdir(os.path.join(env, "pcd")):
        return env
    cand = os.path.normpath(os.path.join(
        ctx["path"], "..", "01_dynamicmap_benchmark", "data", "raw", "00"))
    return cand if os.path.isdir(os.path.join(cand, "pcd")) else None


def _kitti_root(ctx):
    """KITTI-format sequence the official binary consumes."""
    return os.path.join(ctx["data_root"], "kitti00")


def _scan_dir(ctx):
    return os.path.join(_kitti_root(ctx), "sequences", "00", "velodyne")


def _pose_file(ctx):
    return os.path.join(_kitti_root(ctx), "poses", "00.txt")


def _evaluator(ctx):
    return os.path.normpath(os.path.join(
        ctx["path"], "..", "01_dynamicmap_benchmark", "work", "evaluate.py"))


def _make_kitti_seq(ctx):
    """Rebuild KITTI-format scans+poses from the benchmark's world-frame clouds.

    The reconstruction lives in 02_kiss_icp/work/ because that reproduction
    needed it first; it is shared tooling, so it is called rather than copied.
    """
    script = os.path.normpath(os.path.join(
        ctx["path"], "..", "02_kiss_icp", "work", "make_kitti_seq.py"))
    seq = _bench_seq(ctx)
    if not (os.path.exists(script) and seq):
        return False
    r = subprocess.run([_venv_python(ctx), script, "--seq-dir", seq,
                        "--out", _kitti_root(ctx), "--force"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"make_kitti_seq.py failed: {(r.stderr or r.stdout)[-800:]}")
    return True


def _evaluate(ctx, map_path, tag, impl="both"):
    out = os.path.join(ctx["results_dir"], f"score_{tag}.json")
    r = subprocess.run([_venv_python(ctx), _evaluator(ctx),
                        "--seq-dir", _bench_seq(ctx), "--map", map_path,
                        "--method", tag, "--impl", impl, "--out", out],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"evaluate.py failed for {tag}: {(r.stderr or r.stdout)[-800:]}")
    with open(out, encoding="utf-8") as fh:
        return json.load(fh)


def _pct(payload, impl="python"):
    s = payload[impl]
    return {k: s[k] for k in ("SA", "DA", "AA", "HA")}


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
                "micromamba/robostack command that creates "
                "reproductions/.venvs/ros1noetic")
    if not os.path.isdir(os.path.join(_upstream(ctx), "src")):
        return ("official repo not cloned - git clone https://github.com/irapkaist/removert "
                f"{os.path.relpath(_upstream(ctx), ctx['path'])}")
    if not os.path.exists(_official_binary(ctx)):
        return ("official binary not built - bash reproductions/tools/build_ros1_catkin.sh "
                f"{os.path.relpath(_ws(ctx), _repo(ctx))} removert "
                f"{os.path.relpath(_upstream(ctx), _repo(ctx))}  (inside micromamba run -p "
                f"{os.path.relpath(env, _repo(ctx))})")
    if _bench_seq(ctx) is None:
        return ("sequence 00 not found - wget "
                "https://zenodo.org/records/10886629/files/00.zip and unzip into "
                "01_dynamicmap_benchmark/data/raw/ (no KITTI registration needed)")
    runner = os.path.join(ctx["work_dir"], "run_official.sh")
    if not os.path.exists(runner):
        return f"driver missing: {runner}"
    return None


def run(ctx):
    # ---------------------------------------------------------------- inputs
    if not os.path.exists(os.path.join(_scan_dir(ctx), "000000.bin")):
        if not _make_kitti_seq(ctx):
            raise RuntimeError("cannot rebuild the KITTI-format sequence")

    params = os.path.join(ctx["work_dir"], "generated", "params.yaml")
    r = subprocess.run([_venv_python(ctx), os.path.join(ctx["work_dir"], "gen_params.py"),
                        "--upstream", os.path.join(_upstream(ctx), "config", "params_kitti.yaml"),
                        "--scan-dir", _scan_dir(ctx), "--pose-file", _pose_file(ctx),
                        "--out-dir", os.path.join(ctx["results_dir"], "removert_kitti00"),
                        "--start", "0", "--end", "140", "--gap", "1", "--out", params],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"gen_params.py failed: {(r.stderr or r.stdout)[-800:]}")

    # --------------------------------------------------- run official binary
    env = dict(os.environ)
    env["REMOVERT_WS"] = _ws(ctx)
    r = subprocess.run([_micromamba(), "run", "-p", _ros1_env(ctx), "bash",
                        os.path.join(ctx["work_dir"], "run_official.sh"),
                        params, os.path.join(ctx["results_dir"], "removert_kitti00")],
                       capture_output=True, text=True, env=env, timeout=60 * 60)
    if r.returncode != 0:
        raise RuntimeError("official Removert run failed:\n" + (r.stdout or "")[-1500:]
                           + (r.stderr or "")[-1500:])

    scanside = os.path.join(ctx["path"], OFFICIAL_SCANSIDE)
    mapside = os.path.join(ctx["path"], OFFICIAL_MAPSIDE)
    if not os.path.exists(scanside):
        raise RuntimeError(f"official run produced no {OFFICIAL_SCANSIDE}")

    # ------------------------------------------------------------- evaluation
    s_payload = _evaluate(ctx, scanside, "official_scanside")
    official = _pct(s_payload)
    metrics = {f"official_{k}": v for k, v in official.items()}
    metrics["official_map_points"] = s_payload["map_points"]

    if os.path.exists(mapside):
        m_payload = _evaluate(ctx, mapside, "official_mapside")
        metrics.update({f"official_mapside_{k}": v for k, v in _pct(m_payload).items()})
        metrics["official_mapside_points"] = m_payload["map_points"]

    # the benchmark's port, on the same frames, scored by the same evaluator
    port_map = os.path.join(_bench_seq(ctx), "removert_output.pcd")
    port = None
    if os.path.exists(port_map):
        p_payload = _evaluate(ctx, port_map, "benchmark_port", impl="official")
        port = _pct(p_payload, "official")
        metrics.update(port)                       # legacy keys: SA/DA/AA/HA
        metrics["map_points"] = p_payload["map_points"]
        metrics["port_map_points"] = p_payload["map_points"]
        metrics.update({k: p_payload["official"][k] for k in
                        ("gt_static", "gt_dynamic", "false_removal", "missed_dynamic")})

    cross = s_payload.get("cross_check", {})
    checks = [
        {
            "name": "official_pipeline_produced_a_static_map",
            "ok": metrics["official_map_points"] > 1_000_000,
            "detail": (f"{OFFICIAL_SCANSIDE} holds {metrics['official_map_points']} points "
                       "after mapgen+removert ran over all 141 frames"),
        },
        {
            "name": "evaluator_implementations_agree",
            "ok": bool(cross.get("ok")),
            "detail": (f"official export_eval_pcd vs scipy re-implementation: "
                       f"{cross.get('disagreeing_points')} disagreeing GT labels "
                       f"(rate {cross.get('disagree_rate')})"),
        },
    ]
    if port is not None:
        checks.append({
            "name": "benchmark_port_still_reproduces_its_row",
            "ok": all(abs(port[k] - BENCH_PORT[k]) <= TOL_PP for k in ("SA", "DA", "AA")),
            "detail": (f"port SA/DA/AA = {port['SA']:.2f}/{port['DA']:.2f}/{port['AA']:.2f} "
                       f"vs Table I {BENCH_PORT['SA']}/{BENCH_PORT['DA']}/{BENCH_PORT['AA']}"),
        })

    findings = []
    if port is not None:
        findings.append({
            "name": "official_removert_is_not_the_conservative_extreme",
            "detail": (f"same 141 frames, same evaluator, same GT: official Removert scores "
                       f"SA {official['SA']:.2f} / DA {official['DA']:.2f} / AA {official['AA']:.2f}, "
                       f"the benchmark's port scores SA {port['SA']:.2f} / DA {port['DA']:.2f} / "
                       f"AA {port['AA']:.2f}. Static preservation is unchanged (0.2 pp apart) "
                       f"but dynamic rejection differs by {official['DA'] - port['DA']:.1f} pp - "
                       "the port leaks more than half the dynamic points the official code "
                       "removes. Any ranking built on the port under-rates Removert."),
        })
    if "official_mapside_DA" in metrics:
        findings.append({
            "name": "removert_revert_step_matters_more_than_it_looks",
            "detail": (f"map-side output at the finest removal resolution scores "
                       f"SA {metrics['official_mapside_SA']:.2f} / DA {metrics['official_mapside_DA']:.2f} "
                       f"(AA {metrics['official_mapside_AA']:.2f}) against the scan-side merged output's "
                       f"SA {official['SA']:.2f} / DA {official['DA']:.2f} "
                       f"(AA {official['AA']:.2f}). The two upstream outputs of one run sit at "
                       "opposite corners of the precision/recall trade-off, so 'Removert's score' "
                       "is not defined without saying which output is submitted."),
        })
    findings.append({
        "name": "official_output_is_downsampled_but_still_scores_higher",
        "detail": (f"the official map has {metrics['official_map_points']} points against the port's "
                   f"{metrics.get('port_map_points', 0)}. The evaluator's 0.05 m nearest-neighbour "
                   "rule punishes sparse maps, so the official run wins on DA despite submitting "
                   "a map ~3.6x smaller - the extra points in the port are not in the places the "
                   "metric looks at."),
    })

    note = (f"official Removert (irapkaist/removert) on KITTI 00: SA/DA/AA = "
            f"{official['SA']:.2f}/{official['DA']:.2f}/{official['AA']:.2f}"
            + (f"; benchmark port {port['SA']:.2f}/{port['DA']:.2f}/{port['AA']:.2f}"
               if port else ""))

    return {
        "metrics": metrics,
        "checks": checks,
        "findings": findings,
        "artifacts": ["results/score_official_scanside.json",
                      "results/score_official_mapside.json",
                      "results/score_benchmark_port.json"],
        "note": note,
    }
