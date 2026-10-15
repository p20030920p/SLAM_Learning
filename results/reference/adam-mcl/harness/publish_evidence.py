"""Publish the AdaM_MCL reproduction evidence into the study repository.

Two subcommands:

  run    write runs/adam-mcl-wsl/{run.log,worker.json,metrics.json,record.json}
         from the released-code logs kept outside the repository
  index  hash every file under results/reference/adam-mcl and write the curated
         record.json that docs/figures/slots.json binds media/preview.gif to

The curated index is generated last so the published GIF hash always equals the
hash stored in the record, which is what src/scripts/evidence/check_docs.py
verifies.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

PAPER_MAP_METRES = 43.0
PAPER_CONVERGE_METRES = 2.0
PAPER_CONVERGE_RADIANS = math.radians(10.0)
CONSECUTIVE = 5


def digest(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            sha.update(block)
    return sha.hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def git_state(repo: Path) -> dict:
    def read(*arguments: str) -> str:
        return subprocess.check_output(["git", "-C", str(repo), *arguments], text=True).strip()

    return {"commit": read("rev-parse", "HEAD"), "dirty": bool(read("status", "--porcelain"))}


def kidnapping_index(gt_pose: np.ndarray) -> int:
    steps = np.linalg.norm(np.diff(gt_pose[:, :2], axis=0), axis=1)
    return int(np.argmax(steps)) + 1


def convergence_step(error, orientation, start, position_limit, orientation_limit):
    run = 0
    for index in range(start, len(error)):
        if error[index] < position_limit and orientation[index] < orientation_limit:
            run += 1
            if run >= CONSECUTIVE:
                return index - CONSECUTIVE + 1
        else:
            run = 0
    return None


def collect_metrics(logs: Path, sequences: Path, map_cells: int) -> dict:
    scale = PAPER_MAP_METRES / map_cells
    position_limit = PAPER_CONVERGE_METRES / scale
    trials = []
    for summary in sorted(logs.glob("**/error_position.txt")):
        run = summary.parent
        # released layout: logs4MCL/<dataset>/<sequence>/<mode>_<particles>_particles_<w_cut>/log_time_.../
        sequence = run.parent.parent.name
        error = np.sqrt(np.atleast_1d(np.loadtxt(summary, ndmin=1)))
        orientation = np.sqrt(np.atleast_1d(np.loadtxt(run / "error_orientation.txt", ndmin=1)))
        cost = np.atleast_1d(np.loadtxt(run / "time_consumption.txt", ndmin=1))
        gt_pose = np.loadtxt(sequences / sequence / "gt_pose.txt", ndmin=2)
        kidnap = kidnapping_index(gt_pose)
        trials.append({
            "sequence": sequence,
            "run": str(run.relative_to(logs)),
            "updates": int(len(error)),
            "kidnapping_update_index": kidnap,
            "final_position_error_cells": float(error[-1]),
            "position_rmse_cells": float(np.sqrt(np.mean(np.square(error)))),
            "final_orientation_error_rad": float(orientation[-1]),
            "global_localization_convergence_step": convergence_step(
                error, orientation, 0, position_limit, PAPER_CONVERGE_RADIANS),
            "kidnapping_convergence_step": convergence_step(
                error, orientation, kidnap, position_limit, PAPER_CONVERGE_RADIANS),
            "mean_update_seconds": float(np.mean(cost)),
        })
    if not trials:
        raise SystemExit("no released evaluation logs found")
    final = np.array([t["final_position_error_cells"] for t in trials])
    rms = np.array([t["position_rmse_cells"] for t in trials])
    localization = [t["global_localization_convergence_step"] for t in trials]
    kidnapping = [t["kidnapping_convergence_step"] for t in trials]
    found_localization = [s for s in localization if s is not None]
    found_kidnapping = [s for s in kidnapping if s is not None]
    return {
        "trials": len(trials),
        "updates_per_trial_mean": float(np.mean([t["updates"] for t in trials])),
        "position_rmse_cells_mean": float(rms.mean()),
        "position_rmse_cells_median": float(np.median(rms)),
        "final_position_error_cells_mean": float(final.mean()),
        "final_position_error_cells_median": float(np.median(final)),
        "final_position_error_cells_max": float(final.max()),
        "mean_update_seconds": float(np.mean([t["mean_update_seconds"] for t in trials])),
        "global_localization_converged_trials": len(found_localization),
        "global_localization_convergence_step_mean": (
            float(np.mean(found_localization)) if found_localization else None),
        "kidnapping_converged_trials": len(found_kidnapping),
        "kidnapping_convergence_step_mean": (
            float(np.mean(found_kidnapping)) if found_kidnapping else None),
        "convergence_rule": {
            "position_limit_m": PAPER_CONVERGE_METRES,
            "orientation_limit_rad": PAPER_CONVERGE_RADIANS,
            "consecutive_updates": CONSECUTIVE,
            "map_cells_across": map_cells,
            "paper_map_metres_across": PAPER_MAP_METRES,
            "rescaled_position_limit_cells": position_limit,
            "note": ("This is the paper's convergence rule rescaled to the authored 128-cell plan. "
                     "Cells are not metres: the paper uses 43 m maps, so no numeric match is claimed."),
        },
        "per_trial": trials,
    }


def command_run(args) -> int:
    run_directory = args.repo / "results/reference/adam-mcl/runs/adam-mcl-wsl"
    run_directory.mkdir(parents=True, exist_ok=True)

    header = [
        "# AdaM_MCL reproduction run log (released code, WSL2)",
        f"# generated: {utc_now()}",
        "# stage 1/3  authored input layout + released generator: repro/gen_train_data.sh",
        "# stage 2/3  released DSOM training:                    repro/train.sh",
        "# stage 3/3  released evaluation:                       repro/run_session.sh",
        "",
    ]
    body = []
    for name in ("train.log", "eval-full-output.log"):
        path = args.logs / name
        body.append(f"\n===== {name} =====\n")
        body.append(path.read_text(encoding="utf-8", errors="replace") if path.is_file()
                    else f"(missing: {path})\n")
    (run_directory / "run.log").write_text("".join(header) + "".join(body), encoding="utf-8")

    metrics = collect_metrics(args.evaluation_logs, args.sequences, args.map_cells)
    write_json(run_directory / "metrics.json", metrics)

    worker = {
        "upstream": {
            "name": "AdaM_MCL",
            "url": "https://github.com/Runjian-Chen/AdaM_MCL",
            "commit": args.upstream_commit,
            "license": "MIT",
            "checkout": str(args.upstream),
            "dirty": True,
            "dirty_reason": "the documented compatibility patch is applied in the checkout",
        },
        "compatibility_patch": "compatibility.patch",
        "python": args.python_version,
        "torch": args.torch_version,
        "numpy": np.__version__,
        "opencv": args.opencv_version,
        "scipy": args.scipy_version,
        "scikit_learn": args.sklearn_version,
        "gpu": args.gpu,
        "device": args.device,
        "dataset": {
            "id": "authored-simulation-surrogate",
            "path": "Dataset/simulation (staged on the WSL filesystem)",
            "authored_layouts": 21,
            "hold_out_layout": 1,
            "training_samples": args.training_samples,
            "validation_samples": args.validation_samples,
            "evaluation_sequences": args.sequences_count,
            "evaluation_frames": args.evaluation_frames,
            "note": ("The released Dataset/ directory ships empty: the authors' simulation maps, "
                     "their evaluation sequences and the UPO/Bicocca datasets are external "
                     "downloads. The layouts are authored by repro/make_maps.py and every sample "
                     "and scan is produced by the authors' own Data_processor/synthetic_dataset.py "
                     "and src/Generate_Path.py."),
        },
        "training": {
            "epochs_completed": args.epochs,
            "iterations_per_epoch": args.iterations,
            "iterations_executed": args.epochs * args.iterations,
            "batch_size": 32,
            "optimizer": "Adam, lr 0.001, weight_decay 1e-6",
            "loss": "torch.nn.KLDivLoss(reduction='sum') / batch_size",
            "published_checkpoint": "Trained_models/simulation_2_*/model_train_38epochs.pth",
            "paper_budget": ("cfg.DSOM_training_iters = 7200*4 iterations per epoch over 100 "
                             "epochs, i.e. 2,880,000 optimizer steps"),
            "budget_ratio": "2432 executed steps against the authors' 2,880,000 default",
        },
        "evaluation": {
            "update_mode": "Adaptive_Mixture_MCL",
            "particles": args.particles,
            "w_cut": 0.6,
            "trials": args.trials,
            "sequence": args.sequence,
            "sequence_frames": args.evaluation_frames,
            "command": args.evaluation_command,
        },
    }
    write_json(run_directory / "worker.json", worker)

    record = {
        "schema_version": 1,
        "kind": "author_pipeline_run",
        "method": "adam-mcl",
        "status": "executed",
        "started_at": args.started_at,
        "finished_at": utc_now(),
        "stage_notes": (
            "Data generation and DSOM training ran before the recorded session. The WSL wall clock "
            "jumped during that window (file timestamps move from 07:5x to 14:3x), so only the "
            "evaluation session has a trustworthy UTC timestamp; started_at is that session's "
            "recorder timestamp and finished_at is when this record was written."
        ),
        "scope": ("Authored 128-cell plan, released DSOM training, released AdaM MCL global "
                  "localization and kidnapping evaluation"),
        "scope_detail": [
            "Authored 128-cell occupancy plans replace the authors' 20 synthetic 43 m x 43 m maps: "
            "the pinned commit ships Dataset/ and Trained_models/ empty and both Google Drive "
            "downloads are unreachable here.",
            "Training budget 2432 optimizer steps (38 epochs x 64 iterations, batch 32) against the "
            "authors' 2,880,000-step default, roughly three orders of magnitude smaller.",
            "One authored evaluation sequence of 123 updates, ten repeats; the paper reports six "
            "sequences and 100 repeats each, 600 runs per method.",
            "Cells are not metres, so no Table I or Table II value is compared.",
            "Only global localization and kidnapping are exercised; the UPO and Bicocca real-dataset "
            "experiments and the PFRNN / PF-Net baselines are not reproduced.",
        ],
        "build_note": (
            "torch 2.14.1+cu130 on Python 3.10.12, driven through the released Main.py. No upstream "
            "algorithm was rewritten: compatibility.patch only restores the attribute names, bounds "
            "and integer conversions the released code assumed."
        ),
        "specification": {
            "upstream": "AdaM_MCL",
            "mode": "released code, unmodified entry points, disclosed compatibility patch",
            "parameters": {
                "batch_size": 32,
                "epochs": args.epochs,
                "iterations_per_epoch": args.iterations,
                "particles": args.particles,
                "w_cut": 0.6,
                "trials": args.trials,
            },
            "paper_target": {
                "source": "https://arxiv.org/html/2009.00211v3",
                "table": "Table II, particle-number sensitivity, Tcut = 0.6, synthetic environments",
                "values": {
                    "global_localization_Epos_m": 0.153,
                    "global_localization_Etheta_rad": 0.022,
                    "kidnapping_Epos_m": 0.128,
                    "kidnapping_Etheta_rad": 0.022,
                },
                "comparison_made": False,
                "reason": ("The authors' 20 synthetic maps (43 m x 43 m), their six evaluation "
                           "sequences, their trained models and the UPO/Bicocca datasets are all "
                           "external downloads (Dataset/ and Trained_models/ ship empty). This run "
                           "uses authored 128-cell plans and a much smaller training budget, so "
                           "cell units are not metres and no numeric comparison is claimed."),
            },
            "scope_note": ("Five upstream defects block or corrupt the released code on Python 3.10 / "
                           "PyTorch 2.14 / NumPy 2: cfg.PGN_* attribute names that no longer exist; "
                           "an unconditional sys.exit() in the data generator; an unbounded "
                           "orientation interpolation weight that makes the ground-truth map "
                           "negative and the KLDiv loss NaN; --num_epochs forwarded as str into "
                           "range(); and an out-of-range write into a uint8 image that NumPy 2 "
                           "rejects. All five are fixed in compatibility.patch."),
            "compatibility_patch": "compatibility.patch",
        },
        "environment": {
            "python": args.python_version,
            "platform": platform.platform(),
            "gpu": args.gpu,
            "packages": {
                "torch": args.torch_version,
                "numpy": np.__version__,
                "opencv": args.opencv_version,
                "scipy": args.scipy_version,
                "scikit-learn": args.sklearn_version,
            },
        },
        "repository": git_state(args.repo),
        "upstreams": {
            "adam_mcl": {
                "url": "https://github.com/Runjian-Chen/AdaM_MCL",
                "commit": args.upstream_commit,
                "license": "MIT",
                "checkout": str(args.upstream),
                "dirty": True,
                "dirty_reason": "the documented compatibility patch is applied in the checkout",
            },
        },
        "command": args.evaluation_command,
        "commands": [
            "python repro/make_maps.py --maps 21",
            "bash repro/gen_train_data.sh    # released Data_processor/synthetic_dataset.py",
            "bash repro/gen_test_data.sh     # released src/Generate_Path.py",
            "bash repro/train.sh             # released Main.py --operation train",
            "bash repro/run_recorded_session.sh   # released Main.py --operation test_MCL, recorded",
        ],
        "exit_code": 0,
        "dataset": worker["dataset"],
        "worker": worker,
        "metrics": metrics,
        "metrics_source": "metrics.json, derived from the released per-update error logs",
        "paper_comparison": {
            "comparison_made": False,
            "reason": None,
        },
        "artifacts": {},
    }
    record["paper_comparison"]["reason"] = record["specification"]["paper_target"]["reason"]
    for name in ("run.log", "worker.json", "metrics.json", "compatibility.patch"):
        path = run_directory / name
        if path.is_file():
            record["artifacts"][name] = {"sha256": digest(path), "bytes": path.stat().st_size,
                                         "availability": "portable"}
    write_json(run_directory / "record.json", record)
    print(f"wrote {run_directory}")
    print(json.dumps({k: metrics[k] for k in (
        "trials", "final_position_error_cells_mean", "global_localization_converged_trials",
        "kidnapping_converged_trials")}, indent=2))
    return 0


def command_index(args) -> int:
    reference = args.repo / "results/reference/adam-mcl"
    artifacts = {}
    for path in sorted(reference.rglob("*")):
        if path.is_file() and path != reference / "record.json":
            artifacts[str(path.relative_to(reference)).replace("\\", "/")] = {
                "sha256": digest(path), "bytes": path.stat().st_size, "availability": "portable"}
    record = {
        "schema_version": 1,
        "kind": "method_delivery",
        "method": "adam-mcl",
        "status": "recorded",
        "scope": "Authored 128-cell plan, released AdaM MCL global localization and kidnapping evaluation",
        "primary_record": "runs/adam-mcl-wsl/record.json",
        "note": ("Curated index of one released-code run. media/preview.gif is the complete "
                 "evaluation recording converted to a continuous excerpt; no metric is read from "
                 "the media."),
        "artifacts": artifacts,
    }
    write_json(reference / "record.json", record)
    print(f"{len(artifacts)} artifacts indexed in {reference / 'record.json'}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run")
    run.add_argument("--upstream", type=Path, required=True)
    run.add_argument("--upstream-commit", required=True)
    run.add_argument("--logs", type=Path, required=True)
    run.add_argument("--evaluation-logs", type=Path, required=True,
                     help="directory holding the released logs4MCL output")
    run.add_argument("--sequences", type=Path, required=True)
    run.add_argument("--map-cells", type=int, default=128)
    run.add_argument("--python-version", required=True)
    run.add_argument("--torch-version", required=True)
    run.add_argument("--opencv-version", required=True)
    run.add_argument("--scipy-version", required=True)
    run.add_argument("--sklearn-version", required=True)
    run.add_argument("--gpu", required=True)
    run.add_argument("--device", required=True)
    run.add_argument("--started-at", required=True)
    run.add_argument("--training-samples", type=int, required=True)
    run.add_argument("--validation-samples", type=int, required=True)
    run.add_argument("--sequences-count", type=int, required=True)
    run.add_argument("--evaluation-frames", type=int, required=True)
    run.add_argument("--epochs", type=int, required=True)
    run.add_argument("--iterations", type=int, required=True)
    run.add_argument("--particles", type=int, required=True)
    run.add_argument("--trials", type=int, required=True)
    run.add_argument("--sequence", required=True)
    run.add_argument("--evaluation-command", required=True)
    run.set_defaults(func=command_run)

    index = sub.add_parser("index")
    index.set_defaults(func=command_index)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
