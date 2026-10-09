"""Keep the post-hoc minimum-support control separate from frozen primary cells."""
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
from slam_learning.runtime.runner import verify_record


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("suite", type=Path)
    parser.add_argument("--primary", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    primary = args.primary
    if verify_record(primary / "record.json"):
        raise ValueError("Primary evidence changed")
    raw = json.loads((args.suite / "record.json").read_text())
    if (raw["status"] != "executed" or raw["kind"] != "posthoc_support_control" or
            raw["primary_parent_sha256"] != digest(primary / "inputs/record.json") or len(raw["cells"]) != 6):
        raise ValueError("Incomplete or mismatched post-hoc support control")
    cfg = raw["configuration"]
    ann = json.loads((primary / "inputs/annotations.json").read_text())
    prefix_ids = {i["id"] for i in ann["instances"] if i["first_reference_frame"] <= cfg["mapping_frames"][7]}
    args.output.mkdir(parents=True, exist_ok=False)
    rows = []
    for info in raw["cells"]:
        directory = args.suite / "cells" / info["name"]
        cell = json.loads((directory / "record.json").read_text())
        if digest(directory / "record.json") != info["record_sha256"]:
            raise ValueError("Changed post-hoc cell")
        parent_dir = primary / "cells" / info["name"]
        before = json.loads((parent_dir / "decision-trace.json").read_text())[:8]
        after = json.loads((directory / "decision-trace.json").read_text())[:8]
        if before != after:
            raise ValueError("Minimum-support control changed historical associations")
        destination = args.output / "cells" / info["name"]
        destination.mkdir(parents=True)
        artifacts = {}
        for path in directory.iterdir():
            portable = path.suffix == ".json"
            artifacts[path.name] = {"sha256": digest(path), "bytes": path.stat().st_size,
                                    "availability": "portable" if portable else "local_only"}
            if portable:
                shutil.copy2(path, destination / path.name)
        write_json(destination / "artifact-manifest.json", artifacts)
        for stage in cell["stages"]:
            targets = [t for t in stage["targets"] if t["target"] in prefix_ids]
            rows.append({"rms_m": cell["rms_m"], "seed": cell["seed"], "observation": stage["observation"],
                         "prefix_coverage": float(np.mean([t["best_coverage"] for t in targets])),
                         "prefix_recovery": float(np.mean([t["recovered"] for t in targets])),
                         "prefix_query_hit": float(np.mean([t["restricted_top1_hit"] for t in targets])),
                         "map_objects": stage["map_objects"], "fragment_count": stage["fragment_count"]})
    with (args.output / "measurements.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    with (primary / "measurements.csv").open(newline="") as stream:
        parent_rows = list(csv.DictReader(stream))
    summary = []
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.8))
    labels = ["Fixed history / support 3", "Fixed history / support 1*", "Oracle reassociation / support 3"]
    for rms, color in zip(cfg["translation_rms_m"], ["#0072b2", "#d55e00"]):
        groups = [[r for r in parent_rows if float(r["rms_m"]) == rms and r["observation"] == "8" and
                   r["arm"] == "fixed_association"],
                  [r for r in rows if r["rms_m"] == rms and r["observation"] == 8],
                  [r for r in parent_rows if float(r["rms_m"]) == rms and r["observation"] == "8" and
                   r["arm"] == "oracle_replay"]]
        entry = {"rms_m": rms}
        for group, label in zip(groups, labels):
            entry[label] = {k: float(np.mean([float(r[k]) for r in group])) for k in (
                "prefix_coverage", "prefix_recovery", "prefix_query_hit", "map_objects")}
        summary.append(entry)
        for ax, metric, title in zip(axes, ["prefix_recovery", "prefix_query_hit", "map_objects"],
                                     ["Prefix-target recovery", "Restricted prefix-query hit", "Exposed candidate objects"]):
            values = [[float(r[metric]) for r in g] for g in groups]
            means = [np.mean(v) for v in values]
            ax.errorbar(np.arange(3) + (0 if rms == .10 else .08), means,
                        yerr=[[m - min(v) for m, v in zip(means, values)],
                              [max(v) - m for m, v in zip(means, values)]],
                        fmt="o-", color=color, capsize=3, label=f"{rms:.2f} m prefix RMS")
            ax.set(title=title, xticks=range(3), xticklabels=["Fixed / 3", "Fixed / 1*", "Oracle / 3"])
            ax.grid(alpha=.2)
            if metric != "map_objects":
                ax.set_ylim(-.04, 1.04)
    axes[0].legend(fontsize=8)
    fig.suptitle("Immediately after correction: *post-hoc minimum-support control\n"
                 "Means and seed ranges; candidate counts are not false-positive rates", fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, .87))
    (args.output / "figures").mkdir()
    fig.savefig(args.output / "figures/support-control.png", dpi=170)
    plt.close(fig)
    inputs = args.output / "inputs"
    inputs.mkdir()
    for name in ("record.json", "executed-adapter.py", "executed-metrics.py"):
        shutil.copy2(args.suite / name, inputs / name)
    shutil.copy2(Path(__file__), inputs / "executed-analysis.py")
    shutil.copy2(Path(__file__).resolve().parents[1] / "configs/delayed_support_followup.json",
                 inputs / "declared-followup.json")
    write_json(args.output / "summary.json", {"scope": "Six post-hoc support-threshold controls", "results": summary})
    record = {"schema_version": 1, "kind": "posthoc_delayed_support_analysis", "status": "executed",
              "exit_code": 0, "finished_at": utc_now(), "primary_analysis_sha256": digest(primary / "record.json"),
              "summary": summary, "artifacts": {}}
    for path in args.output.rglob("*"):
        if path.is_file():
            record["artifacts"][path.relative_to(args.output).as_posix()] = {
                "sha256": digest(path), "bytes": path.stat().st_size, "availability": "portable"}
    write_json(args.output / "record.json", record)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
