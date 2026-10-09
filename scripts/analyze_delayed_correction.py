"""Export every sealed cell and summarize the predeclared late-correction contrast."""
from __future__ import annotations

import argparse
import csv
import json
import shutil
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from slam_learning.core.provenance import digest, utc_now, write_json


def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("suite", type=Path)
    parser.add_argument("--annotations-review", type=Path, required=True)
    parser.add_argument("--frontend", type=Path, required=True)
    parser.add_argument("--failed-attempts", type=Path, nargs="*", default=[])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    suite = json.loads((args.suite / "record.json").read_text())
    cfg = suite["configuration"]
    annotation = json.loads((args.suite / "annotations.json").read_text())
    prefix_ids = {i["id"] for i in annotation["instances"] if i["first_reference_frame"] <=
                  cfg["mapping_frames"][cfg["correction_after_observations"] - 1]}
    expected = len(cfg["arms"]) * (1 + len(cfg["translation_rms_m"]) * len(cfg["seeds"]))
    if suite["status"] != "executed" or len(suite["cells"]) != expected:
        raise ValueError("Incomplete native suite; no result selection allowed")
    if len(suite["gates"]) != 7 or not all(g["passed"] for g in suite["gates"].values()):
        raise ValueError("Native and zero-error gates must pass")
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "figures").mkdir()
    rows, targets, lookup = [], [], {}
    for cell_info in suite["cells"]:
        source = args.suite / "cells" / cell_info["name"]
        if digest(source / "record.json") != cell_info["record_sha256"]:
            raise ValueError("Cell record changed")
        cell = json.loads((source / "record.json").read_text())
        if cell["status"] != "executed":
            raise ValueError("Failed native cell")
        destination = args.output / "cells" / cell_info["name"]
        destination.mkdir(parents=True)
        cell_manifest = {}
        for path in source.iterdir():
            name = path.name
            portable = path.suffix == ".json"
            cell_manifest[name] = {"sha256": digest(path), "bytes": path.stat().st_size,
                                   "availability": "portable" if portable else "local_only"}
            if portable:
                shutil.copy2(path, destination / name)
        write_json(destination / "artifact-manifest.json", cell_manifest)
        for stage in cell["stages"]:
            prefix_targets = [t for t in stage["targets"] if t["target"] in prefix_ids]
            row = {"arm": cell["arm"], "rms_m": cell["rms_m"], "seed": cell["seed"],
                   "observation": stage["observation"], "eligible_targets": stage["eligible_targets"],
                   "prefix_targets": len(prefix_targets),
                   "prefix_coverage": float(np.mean([t["best_coverage"] for t in prefix_targets])),
                   "prefix_recovery": float(np.mean([t["recovered"] for t in prefix_targets])),
                   "prefix_query_hit": float(np.mean([t["restricted_top1_hit"] for t in prefix_targets])),
                   "all_coverage": stage["mean_coverage"], "all_recovery": stage["recovery"],
                   "all_query_hit": stage["restricted_query_hit"], "map_objects": stage["map_objects"],
                   "mixed_objects": stage["annotated_mixed_objects"], "fragments": stage["fragment_count"],
                   "correction_compute_seconds": cell["correction_compute_seconds"]}
            rows.append(row)
            lookup[(cell["arm"], cell["rms_m"], cell["seed"], stage["observation"])] = row
            for target in stage["targets"]:
                targets.append({"arm": cell["arm"], "rms_m": cell["rms_m"], "seed": cell["seed"],
                                "observation": stage["observation"], **target})
    contrasts = []
    for rms in cfg["translation_rms_m"]:
        for seed in cfg["seeds"]:
            for stage in cfg["evaluation_observations"]:
                fixed = lookup[("fixed_association", rms, seed, stage)]
                oracle = lookup[("oracle_replay", rms, seed, stage)]
                contrasts.append({"rms_m": rms, "seed": seed, "observation": stage,
                                  **{f"oracle_minus_fixed_{m}": oracle[m] - fixed[m] for m in (
                                      "prefix_coverage", "prefix_recovery", "prefix_query_hit",
                                      "all_recovery", "all_query_hit", "mixed_objects", "fragments")}})
    decisions = []
    for rms in cfg["translation_rms_m"]:
        immediate = [r for r in contrasts if r["rms_m"] == rms and r["observation"] == 8]
        # Mixing is a partial-label diagnostic; categorical recovery/query is the conservative gate.
        favorable = sum(r["oracle_minus_fixed_prefix_recovery"] > 0 or
                        r["oracle_minus_fixed_prefix_query_hit"] > 0 for r in immediate)
        decisions.append({"rms_m": rms, "favorable_seeds_out_of_three": favorable,
                          "categorical_gate_met": favorable >= 2,
                          "mean_recovery_difference": float(np.mean([
                              r["oracle_minus_fixed_prefix_recovery"] for r in immediate])),
                          "mean_query_hit_difference": float(np.mean([
                              r["oracle_minus_fixed_prefix_query_hit"] for r in immediate]))})
    write_csv(args.output / "measurements.csv", rows)
    write_csv(args.output / "targets.csv", targets)
    write_csv(args.output / "oracle-vs-fixed.csv", contrasts)
    colors = ["#555555", "#e69f00", "#009e73", "#0072b2", "#cc79a7"]
    labels = {"native": "Native", "threshold": "Threshold 1.0", "visibility": "Visibility guard",
              "fixed_association": "Correct geometry / fixed association", "oracle_replay": "Oracle reassociation"}
    fig, axes = plt.subplots(2, 3, figsize=(14, 7), sharey=True)
    metrics = ["prefix_coverage", "prefix_recovery", "prefix_query_hit"]
    titles = ["Prefix-target surface coverage", "Prefix-target recovery", "Restricted prefix-query hit"]
    for r, rms in enumerate(cfg["translation_rms_m"]):
        for c, (metric, title) in enumerate(zip(metrics, titles)):
            ax = axes[r, c]
            for arm, color in zip(cfg["arms"], colors):
                means, lows, highs = [], [], []
                for stage in cfg["evaluation_observations"]:
                    values = [lookup[(arm, rms, seed, stage)][metric] for seed in cfg["seeds"]]
                    means.append(np.mean(values))
                    lows.append(min(values))
                    highs.append(max(values))
                ax.plot(cfg["evaluation_observations"], means, "o-", color=color, label=labels[arm])
                ax.fill_between(cfg["evaluation_observations"], lows, highs, color=color, alpha=.10)
            ax.set(title=f"{title}\nPrefix RMS {rms:.2f} m", ylim=(-.04, 1.04), xticks=[8, 12, 16])
            ax.grid(alpha=.2)
            ax.set_xlabel("Observations (correction after 8)")
    fig.suptitle("Room1 delayed correction: same three prefix targets at every stage\n"
                 "Mean and seed range; not confidence intervals; AI-assisted labels await human review")
    handles, legend_labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, legend_labels, loc="lower center", ncol=3, fontsize=9)
    fig.tight_layout(rect=(0, .10, 1, .90))
    fig.savefig(args.output / "figures/delayed-results.png", dpi=160)
    plt.close(fig)
    summary = {"cells": expected, "gates": suite["gates"], "primary_decisions": decisions,
               "candidate_h1_validated": False,
               "decision": "Categorical prerequisite met provisionally" if any(d["categorical_gate_met"] for d in decisions)
                           else "Do not implement H1 based on this test; categorical prerequisite not met",
               "limits": ["One static scene", "AI-assisted partial labels await independent human audit",
                          "Exact supplied corrections", "Full-history diagnostic controls, not bounded replay",
                          "No real change recall, live stale-target duration or matched delay frontier"],
               "all_seed_contrasts": contrasts}
    write_json(args.output / "summary.json", summary)
    for name in ("record.json", "protocol.json", "annotations.json", "freeze.json", "source-manifest.json",
                 "frontend-record.json", "executed-adapter.py", "executed-metrics.py", "native-zero-gate.py",
                 "native-zero-command.json", "native-zero.log", "text_features.npy", "semantic-config.json"):
        source = args.suite / name
        if source.exists():
            target = args.output / "inputs" / name
            target.parent.mkdir(exist_ok=True)
            shutil.copy2(source, target)
    for path in args.annotations_review.glob("annotation-*.png"):
        target = args.output / "annotations" / path.name
        target.parent.mkdir(exist_ok=True)
        shutil.copy2(path, target)
    shutil.copy2(args.frontend / "frontend.log", args.output / "inputs/frontend.log")
    audit = args.suite.parent / "source-audit"
    if audit.is_dir():
        shutil.copytree(audit, args.output / "inputs/source-audit")
    native = args.frontend / "author-code"
    for relative in ("conceptgraph/slam/mapping.py", "conceptgraph/slam/utils.py",
                     "conceptgraph/slam/slam_classes.py", "conceptgraph/configs/slam_pipeline/base.yaml",
                     "conceptgraph/scripts/generate_gsa_results.py", "LICENSE"):
        path = native / relative
        if path.is_file():
            target = args.output / "inputs/native-source" / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
    for attempt in args.failed_attempts:
        target = args.output / "attempts" / attempt.name
        target.mkdir(parents=True)
        for path in attempt.glob("*.json"):
            shutil.copy2(path, target / path.name)
        for path in attempt.glob("executed-*.py"):
            shutil.copy2(path, target / path.name)
    shutil.copy2(Path(__file__), args.output / "inputs/executed-analysis.py")
    record = {"schema_version": 1, "kind": "delayed_pose_analysis", "status": "executed", "exit_code": 0,
              "finished_at": utc_now(), "summary": summary, "artifacts": {}}
    for path in sorted(args.output.rglob("*")):
        if path.is_file():
            record["artifacts"][path.relative_to(args.output).as_posix()] = {
                "sha256": digest(path), "bytes": path.stat().st_size, "availability": "portable"}
    write_json(args.output / "record.json", record)
    print(json.dumps({"cells": expected, "decisions": decisions, "decision": summary["decision"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
