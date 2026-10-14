#!/usr/bin/env python3
"""Write the IR-MCL evidence records from what the recorded run actually produced.

Phase "run"   -> runs/ir-mcl-wsl/metrics.json and runs/ir-mcl-wsl/record.json
Phase "index" -> media/timing.json and the top-level record.json

Every number is parsed from runs/ir-mcl-wsl/run.log or measured from the produced
files. Paper values are constants, quoted from the paper's own HTML rendering.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
DELIVERY = ROOT / "results/reference/ir-mcl"
RUN_DIR = DELIVERY / "runs/ir-mcl-wsl"
LOG = RUN_DIR / "run.log"
UPSTREAM = "https://github.com/PRBonn/ir-mcl"
COMMIT = "aab8c91b37e59f94442d8eddfa2f920ab1ecc4c5"
PAPER = "https://arxiv.org/abs/2210.03113"
PAPER_TABLE = "https://arxiv.org/html/2210.03113v2#S4.SS2"

EVAL_RE = re.compile(
    r"Sequence information:\s+(?P<poses>\d+) poses, (?P<path>[\d.]+)m path length, (?P<dur>[\d.]+)s duration"
)
ROW_RE = re.compile(r"^\s{6,}([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s*$")
STAGE_RE = re.compile(r"^stage (\d) wall time: (\d+) s")
ARTIFACT_RE = re.compile(r"^([0-9a-f]{64})  (\d+) bytes  (.+)$")
NUMPY_RE = re.compile(r"^numpy\s+:\s+(\S+)")
TORCH_RE = re.compile(r"^torch\s+:\s+(\S+)")
PYBIND_RE = re.compile(r"^pybind11 \(build time\):\s+(\S+)")
PYTHON_RE = re.compile(r"^python\s+:\s+(\S+)")
GPU_RE = re.compile(r"^gpu\s+:\s+(.+)$")


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def parse_log() -> dict:
    text = LOG.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    found: dict = {"counts": {}, "wall_time_seconds": {}, "artifacts": {}}

    match = EVAL_RE.search(text)
    if not match:
        raise SystemExit("evaluation block not found in run.log")
    found["scored"] = {
        "poses": int(match["poses"]),
        "path_length_m": float(match["path"]),
        "duration_seconds": float(match["dur"]),
    }
    for index, line in enumerate(lines):
        if "location_rmse" in line and index + 1 < len(lines):
            row = ROW_RE.match(lines[index + 1])
            if row:
                values = [float(v) for v in row.groups()]
                found["metrics"] = dict(zip(
                    ("location_rmse_cm", "location_lt5_pct", "location_lt10_pct", "location_lt20_pct",
                     "yaw_rmse_deg", "yaw_lt0_5_pct", "yaw_lt1_pct", "yaw_lt2_pct"), values))
    if "metrics" not in found:
        raise SystemExit("metric row not found in run.log")

    scored = found["scored"]["poses"]
    for key, pct in (("location_lt5_pct", "location_lt5"), ("location_lt10_pct", "location_lt10"),
                     ("location_lt20_pct", "location_lt20"), ("yaw_lt0_5_pct", "yaw_lt0_5"),
                     ("yaw_lt1_pct", "yaw_lt1"), ("yaw_lt2_pct", "yaw_lt2")):
        count = round(found["metrics"][key] / 100 * scored)
        found["counts"][key.replace("_pct", "_count")] = count
        found["counts"][key.replace("_pct", "_of")] = scored
        assert abs(count / scored * 100 - found["metrics"][key]) < 0.01, (key, count, scored)
        found["counts"][pct + "_pct_check"] = round(count / scored * 100, 2)

    for line in lines:
        stage = STAGE_RE.match(line)
        if stage:
            found["wall_time_seconds"]["stage%s" % stage.group(1)] = int(stage.group(2))
        artifact = ARTIFACT_RE.match(line)
        if artifact:
            found["artifacts"][artifact.group(3)] = {
                "sha256": artifact.group(1), "bytes": int(artifact.group(2))}
        for regex, key in ((PYTHON_RE, "python"), (NUMPY_RE, "numpy"), (TORCH_RE, "torch"),
                           (PYBIND_RE, "pybind11_build_time"), (GPU_RE, "gpu")):
            hit = regex.match(line)
            if hit:
                found.setdefault("environment", {})[key] = hit.group(1).strip()
    found["scans_total"] = len(re.findall(r"^finished frame ", text, flags=re.M))
    return found


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def phase_run() -> None:
    data = parse_log()
    counts = data["counts"]
    metrics = data["metrics"]
    artifacts = data["artifacts"]
    original = ROOT.parent / "tmp/repro/ir-mcl"
    estimate = original / "results/ipblab/loc_test/test1/IRMCL.txt"
    if sha(estimate) != artifacts["results/ipblab/loc_test/test1/IRMCL.txt"]["sha256"]:
        raise ValueError("Retained trajectory no longer matches the recorded run")
    truth = original / "data/ipblab/loc_test/test1/seq_1_gt_pose.txt"
    config = original / "config/global_localization/loc_config_test1.yml"
    for source, name in ((estimate, "IRMCL.txt"), (truth, "seq_1_gt_pose.txt"), (config, "loc_config.yml")):
        shutil.copyfile(source, RUN_DIR / name)
    from slam_learning.runtime.localization_evidence import trajectory_metrics
    recomputed, count = trajectory_metrics(estimate, truth, 20.0, 0.01)
    if recomputed != metrics or count != data["scored"]["poses"]:
        raise ValueError("Recorded metrics do not match retained trajectories")
    inputs = {name: sha(original / name) for name in (
        "data/ipblab/loc_test/test1/seq_1.json", "data/ipblab/loc_test/test1/seq_1_gt_pose.txt",
        "config/global_localization/loc_config_test1.yml", "data/ipblab/occmap.npy")}
    logged = LOG.read_text(encoding="utf-8")
    started = re.search(r"^started\s+:\s+(.+)$", logged, re.M).group(1)
    finished = re.search(r"^finished\s+:\s+(.+)$", logged, re.M).group(1)

    metrics_doc = {
        "schema_version": 1,
        "method": "ir-mcl",
        "sequence": "data/ipblab/loc_test/test1",
        "upstream": {"repository": UPSTREAM, "commit": COMMIT},
        "scans_total": data["scans_total"],
        "scans_scored": data["scored"]["poses"],
        "scoring_window": {
            "rule": "evo reduce_to_time_range(20) on both trajectories, as called by utils.summary_loc",
            "dropped": "scans with timestamp <= 20 s (global-localization warm-up)",
            "path_length_m": data["scored"]["path_length_m"],
            "duration_seconds": data["scored"]["duration_seconds"],
        },
        "particles": {"initial": 100000, "after_convergence": 5000, "convergence_rule": "first frame with timestamp > 20 s"},
        "lidar": {"beams_on_sensor": 1041, "beams_used": 32, "max_range_m": 10.0},
        "measured": metrics,
        "measured_counts_within_scored_window": counts,
        "paper": {
            "source": PAPER_TABLE,
            "table": "Section IV-B, global localization performance; self-recorded IPBLab sequences 1-5",
            "row": "Seq 1 / IR-MCL",
            "values": {
                "location_rmse_cm": 5.13, "location_lt5_pct": 63.15, "location_lt10_pct": 97.27,
                "location_lt20_pct": 100.00, "yaw_rmse_deg": 1.05, "yaw_lt0_5_pct": 47.12,
                "yaw_lt1_pct": 74.59, "yaw_lt2_pct": 94.24,
            },
            "row_identification": (
                "Each of the six paper percentages is exactly one integer count over 1354 "
                "samples (855, 1317, 1354, 638, 1010, 1276), and 1354 is the scored window "
                "the repository's own evaluation produces for this sequence; the row is "
                "therefore the same window we score."
            ),
            "not_used": (
                "The upstream README's supplementary memory-cost table reports 6.62 cm / 1.11 deg "
                "for NOF; that is an aggregate over the whole self-recorded dataset, not the Seq-1 row."
            ),
        },
        "wall_time_seconds": data["wall_time_seconds"],
        "environment": data.get("environment", {}),
        "local_intermediates_not_redistributed": {
            "path": "tmp/repro/ir-mcl/results/ipblab/loc_test/test1/loc_results.npz",
            "note": "1543 x 100000 x 4 float32 particle history, 255 MB; stays in the working checkout",
        },
    }
    (RUN_DIR / "metrics.json").write_text(json.dumps(metrics_doc, indent=2) + "\n")

    record_artifacts = {}
    for path in sorted(RUN_DIR.iterdir()):
        if path.is_file() and path.name != "record.json":
            record_artifacts[path.name] = {
                "sha256": sha(path), "bytes": path.stat().st_size, "availability": "portable"}

    record = {
        "schema_version": 1,
        "kind": "author_localization",
        "method": "ir-mcl",
        "status": "executed",
        "scope": "full_teaser",
        "started_at": started,
        "finished_at": finished,
        "exit_code": 0,
        "upstream": {"repository": UPSTREAM, "commit": COMMIT, "remote": "origin"},
        "paper": {"url": PAPER, "table": PAPER_TABLE, "year": 2023, "venue": "IEEE RA-L"},
        "command": ["bash", rel(RUN_DIR / "reproduce.sh")],
        "dataset": {"sequence": "IPBLab Seq 1", "source": UPSTREAM + "/tree/" + COMMIT,
                    "inputs_sha256": inputs, "hash_capture": "retained inputs hashed during evidence packaging"},
        "scoring": {"start_time_s": 20.0, "max_timestamp_difference_s": 0.01,
                    "scored_samples": count, "alignment": "none", "rotation_metric": "rotation_angle_deg"},
        "scope_detail": (
            "Global localization on the single released IPBLab sequence with the supplied config "
            "and pre-trained weights, followed by the upstream GIF export."
        ),
        "environment": metrics_doc["environment"],
        "build_note": (
            "The C++ particle-filter extension is compiled against this environment's pybind11 3.1.0 "
            "via CMAKE_ARGS=-Dpybind11_DIR=...; CMake otherwise selects the distribution's pybind11 2.9.1, "
            "which predates NumPy 2 and makes the first numpy-to-C++ array conversion segfault."
        ),
        "compatibility_patch": "compatibility.patch",
        "metrics": metrics_doc["measured"],
        "metrics_source": "runs/ir-mcl-wsl/metrics.json",
        "paper_comparison": {
            key: {"paper": metrics_doc["paper"]["values"][key], "reproduced": value}
            for key, value in metrics_doc["measured"].items()
        },
        "artifacts": record_artifacts,
    }
    (RUN_DIR / "record.json").write_text(json.dumps(record, indent=2) + "\n")
    print("wrote", rel(RUN_DIR / "metrics.json"), "and", rel(RUN_DIR / "record.json"))
    print(json.dumps(metrics_doc["measured"], indent=2))


def phase_index() -> None:
    run_record = RUN_DIR / "record.json"
    media_record = DELIVERY / "media/replay/record.json"
    render = json.loads((DELIVERY / "media/replay/render.json").read_text(encoding="utf-8"))
    metrics = json.loads((RUN_DIR / "metrics.json").read_text(encoding="utf-8"))

    timing = {
        "schema_version": 1,
        "method": "ir-mcl",
        "source_record": rel(run_record),
        "source_record_sha256": sha(run_record),
        "clips": [{
            "name": "ir-mcl",
            "sha256": sha(DELIVERY / "media/replay/replay.mp4"),
            "bytes": (DELIVERY / "media/replay/replay.mp4").stat().st_size,
            "source_video": rel(DELIVERY / "media/replay/replay.mp4"),
            "source_record": rel(media_record),
            "record_sha256": sha(media_record),
            "dimensions": render["dimensions"],
            "source_fps": f"{render['playback_fps']}/1",
            "duration_seconds": render["encoded_duration_seconds"],
            "expected_frames": render["expected_frames"],
            "decoded_frames": render["encoded_frames"],
            "source_intervals_seconds": [[0, render["encoded_duration_seconds"]]],
            "sampling_filter": "setpts=PTS-STARTPTS",
            "preview_duration_seconds": render["source_gif_duration_seconds"],
            "gif_frame_count": render["source_gif_frames"],
            "gif_frame_delay_ms": render["source_gif_frame_delay_ms"],
            "gif_duration_seconds": render["source_gif_duration_seconds"],
            "timing_policy": "Every saved localization frame is kept; constant-rate re-encode, no cuts or downsampling",
            "frame_count_and_timing_passed": render["frame_count_passed"],
            "full_decode_passed": render["full_decode_passed"],
            "commands": [render["command"]],
            "scans_total": metrics["scans_total"],
            "scans_scored": metrics["scans_scored"],
        }],
        "note": "Replay of a saved localization run. Playback rate is not algorithm throughput.",
    }
    (DELIVERY / "media/timing.json").write_text(json.dumps(timing, indent=2) + "\n")

    artifacts = {}
    for path in sorted(DELIVERY.rglob("*")):
        if not path.is_file():
            continue
        if path == DELIVERY / "record.json" or path.name == "private.Xauthority":
            continue
        if "__pycache__" in path.parts:
            continue
        artifacts[path.relative_to(DELIVERY).as_posix()] = {
            "sha256": sha(path), "bytes": path.stat().st_size, "availability": "portable"}

    record = {
        "schema_version": 1,
        "kind": "method_delivery",
        "method": "ir-mcl",
        "status": "recorded",
        "scope": (
            f"IPBLab {rel(RUN_DIR / 'metrics.json')}: global localization on the one released "
            f"sequence, {metrics['scans_total']} scans, {metrics['scans_scored']} scored"
        ),
        "primary_record": rel(run_record),
        "upstream": {"repository": UPSTREAM, "commit": COMMIT},
        "paper": {"url": PAPER, "table": PAPER_TABLE},
        "media_record": rel(media_record),
        "session_record": "media/session/recording.json",
        "note": (
            "Single recorded run; no new mapping or training. media/session/private.Xauthority is a spent "
            "recorder credential and is not listed. Git checkout reports every file modified because the "
            "working tree is on a CRLF mount; compatibility.patch is diffed from CR-normalised content."
        ),
        "metrics": metrics["measured"],
        "paper_comparison": {
            key: {"paper": metrics["paper"]["values"][key], "reproduced": value}
            for key, value in metrics["measured"].items()
        },
        "artifacts": artifacts,
    }
    (DELIVERY / "record.json").write_text(json.dumps(record, indent=2) + "\n")
    print("wrote", rel(DELIVERY / "media/timing.json"), "and", rel(DELIVERY / "record.json"))
    print("artifacts listed:", len(artifacts))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("run", "index"))
    args = parser.parse_args()
    {"run": phase_run, "index": phase_index}[args.phase]()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
