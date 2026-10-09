"""Plot measured API/evaluation effects directly from a verified run record."""
from __future__ import annotations

import argparse
import json
import uuid
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from slam_learning.core.provenance import digest, environment, git_state, utc_now, write_json
from slam_learning.runtime.runner import verify_record


def main():
    p = argparse.ArgumentParser()
    p.add_argument("record", type=Path)
    args = p.parse_args()
    started = utc_now()
    root = Path(__file__).resolve().parents[2]
    record_path = args.record.resolve()
    issues = verify_record(record_path)
    source = json.loads(record_path.read_text(encoding="utf-8"))
    if issues or source.get("kind") != "dufomap_api_diagnostic" or source.get("status") != "executed":
        raise ValueError(f"Completed verified API diagnostic required: {issues}")
    measured = json.loads((record_path.parent / "summary.json").read_text(encoding="utf-8"))
    if measured != source["summary"]:
        raise ValueError("Summary artifact differs from source record")
    output = root / "results/runs" / f"api-diagnostic-plot-{uuid.uuid4().hex[:12]}"
    output.mkdir(parents=True)
    modes = ["direct_segment", "nn_of_segment_kept_map", "nn_of_native_output_map"]
    labels = ["Direct labels", "Same kept points\n5 cm map NN", "Native export\n5 cm map NN"]
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.8), layout="constrained")
    for ax, metric, limits in zip(axes, ("SA", "DA"), ((90, 100), (98.4, 99.3))):
        values = [measured[key][metric] for key in modes]
        ax.plot(range(3), values, "o-", color="#167e81")
        for x, value in enumerate(values):
            ax.annotate(f"{value:.4f}", (x, value), xytext=(0, 8), textcoords="offset points",
                        ha="center", fontsize=9)
        ax.set(xticks=range(3), xticklabels=labels, ylim=limits, ylabel=f"{metric} (%)")
        ax.set_xlim(-0.3, 2.3)
        ax.grid(axis="y", alpha=0.2)
    fig.suptitle("One trained DUFOMap | 141 source frames | zero injected pose error", fontsize=11)
    fig.savefig(output / "metric_correspondence.png", dpi=160)
    plt.close(fig)
    write_json(output / "input-api-record.json", source)
    record = {"schema_version": 1, "kind": "measured_diagnostic_plot", "status": "executed",
              "started_at": started, "finished_at": utc_now(), "environment": environment(),
              "repository": git_state(root), "generator_sha256": digest(Path(__file__)),
              "input_record_sha256": digest(record_path), "artifacts": {}}
    for name in ("metric_correspondence.png", "input-api-record.json"):
        path = output / name
        record["artifacts"][name] = {"sha256": digest(path), "bytes": path.stat().st_size, "availability": "portable"}
    write_json(output / "record.json", record)
    print(output / "record.json")


if __name__ == "__main__":
    main()
