"""Audit and publish paired measurements, annotation overlays and parameter controls."""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from slam_learning.provenance import digest, git_state, utc_now, write_json
from slam_learning.paired_pose import reference_targets
from slam_learning.runner import export_record, verify_record


def csv_write(path, rows):
    columns = sorted(set().union(*(row.keys() for row in rows)))
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: json.dumps(v) if isinstance(v, (list, dict)) else v for k, v in row.items()})


def flatten(spec, record):
    result = {k: spec[k] for k in ("id", "method", "mode", "seed", "rms_m")}
    result["lag1_correlation"] = spec["error"]["lag1_correlation"]
    result["elapsed_seconds"] = record["elapsed_seconds"]
    summary = record["summary"]
    for key, value in summary["metrics"].items():
        if isinstance(value, (float, int)):
            result[key] = value
    direct = summary.get("direct_point_metrics")
    if direct:
        result.update({f"direct_{k}": direct[k] for k in ("SA", "DA")})
    if "objects" in summary:
        result["objects"] = summary["objects"]
    return result


def query_audit(root, suite, target):
    """Project retrieved map geometry into raw annotated views; no predicted-mask GT."""
    from PIL import Image

    references = reference_targets(root)
    fig, axes = plt.subplots(2, 2, figsize=(11, 6.5), layout="constrained")
    for row, method in enumerate(("conceptgraphs", "hovsg")):
        cell = suite / "cells" / f"{method}-reference"
        summary = json.loads((cell / "summary.json").read_text())
        with np.load(cell / "objects.npz") as saved:
            for col, name in enumerate(("cabinet", "ottoman_right")):
                ref = next(t for t in references if t["id"] == name)
                result = next(t for t in summary["metrics"]["targets"] if t["target"] == name)
                points = saved[f"cloud_{result['top1_segment']:04d}"]
                camera = (points - ref["pose"][:3, 3]) @ ref["pose"][:3, :3]
                camera = camera[camera[:, 2] > 0.01]
                k, depth = ref["camera_k"], ref["depth"]
                uv = np.rint(camera[:, :2] / camera[:, 2, None] * [k[0, 0], k[1, 1]] + [k[0, 2], k[1, 2]]).astype(int)
                valid = (uv[:, 0] >= 0) & (uv[:, 0] < depth.shape[1]) & (uv[:, 1] >= 0) & (uv[:, 1] < depth.shape[0])
                uv, camera = uv[valid], camera[valid]
                uv = uv[np.abs(camera[:, 2] - depth[uv[:, 1], uv[:, 0]]) <= 0.1]
                ax = axes[row, col]
                image = root / f".cache/semantic-data/Replica/room0/results/frame{ref['source_frame']:06d}.jpg"
                ax.imshow(Image.open(image))
                ax.scatter(uv[:, 0], uv[:, 1], s=0.35, c="#ed584d", alpha=0.6, label="Top-1 visible geometry")
                for other in references:
                    if other["source_frame"] != ref["source_frame"]:
                        continue
                    polygon = np.vstack([other["polygon_original"], other["polygon_original"][0]])
                    ax.plot(polygon[:, 0], polygon[:, 1], color="#00d7ef", linewidth=1.4)
                ax.set_title(f"{method} | query: {ref['query']} | zero pose error")
                ax.axis("off")
    fig.suptitle("Red: retrieved visible geometry | cyan: partial reference polygons | unmatched is not open-world false")
    fig.savefig(target, dpi=180)
    plt.close(fig)


def main():
    started_at = utc_now()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("suite", type=Path)
    parser.add_argument("--controls", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    suite = json.loads((args.suite / "record.json").read_text())
    controls = json.loads((args.controls / "record.json").read_text())
    if (
        suite["status"] != "executed"
        or suite.get("completed_cells") != 76
        or controls["status"] != "executed"
        or controls.get("completed_cells") != 21
    ):
        raise ValueError("Analysis requires all 76 primary cells and all 21 declared controls")
    args.output.mkdir(parents=True, exist_ok=False)
    export_record(args.suite / "record.json", args.output / "suite")
    export_record(args.controls / "record.json", args.output / "controls")
    rows, targets, by_id = [], [], {}
    for spec in suite["cells"]:
        source = args.suite / "cells" / spec["id"]
        problems = verify_record(source / "record.json", full=True)
        if problems:
            raise ValueError(str(problems))
        record = json.loads((source / "record.json").read_text())
        if record["status"] != "executed":
            raise ValueError("Incomplete primary cell")
        export_record(source / "record.json", args.output / "suite/cells" / spec["id"])
        row = flatten(spec, record)
        rows.append(row)
        by_id[spec["id"]] = row
        for target in record["summary"]["metrics"].get("targets", []):
            targets.append({**{k: row[k] for k in ("id", "method", "mode", "seed", "rms_m")}, **target})
    control_rows = []
    for spec in controls["cells"]:
        source = args.controls / "cells" / spec["id"]
        record = json.loads((source / "record.json").read_text())
        export_record(source / "record.json", args.output / "controls/cells" / spec["id"])
        control_rows.append(
            {**flatten(spec, record), "threshold": spec["threshold"], "original_id": spec["original_id"]}
        )
    differences = []
    for row in rows:
        if row["mode"] != "correlated":
            continue
        other = by_id[row["id"].replace("-correlated-", "-independent-")]
        delta = {k: row[k] for k in ("method", "seed", "rms_m")}
        for key in (
            "SA",
            "DA",
            "direct_SA",
            "direct_DA",
            "query_hit_fraction",
            "target_recovery_fraction",
            "mean_best_surface_coverage",
            "objects",
        ):
            if key in row:
                delta[key] = row[key] - other[key]
        differences.append(delta)
    csv_write(args.output / "measurements.csv", rows)
    csv_write(args.output / "targets.csv", targets)
    csv_write(args.output / "paired-differences.csv", differences)
    csv_write(args.output / "controls.csv", control_rows)
    amplitude_summary = []
    for method in ("dufomap", "beautymap", "conceptgraphs", "hovsg"):
        for amplitude in suite["protocol"]["translation_rms_m"]:
            subset = [r for r in differences if r["method"] == method and r["rms_m"] == amplitude]
            result = {"method": method, "rms_m": amplitude, "paired_seeds": len(subset)}
            for key in (
                "SA",
                "DA",
                "direct_SA",
                "direct_DA",
                "query_hit_fraction",
                "target_recovery_fraction",
                "mean_best_surface_coverage",
                "objects",
            ):
                if key in subset[0]:
                    values = [r[key] for r in subset]
                    result[key] = {
                        "mean": float(np.mean(values)),
                        "min": float(min(values)),
                        "max": float(max(values)),
                    }
            amplitude_summary.append(result)
    figure_dir = args.output / "figures"
    figure_dir.mkdir()
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
    colors = {"independent": "#b44c45", "correlated": "#147d85"}
    fig, axes = plt.subplots(2, 2, figsize=(11, 7.5), layout="constrained")
    settings = [
        ("dufomap", "direct_SA", "DUFOMap: direct-label static retention (%)"),
        ("beautymap", "SA", "BeautyMap: map-membership static retention (%)"),
        ("conceptgraphs", "mean_best_surface_coverage", "ConceptGraphs: partial reference coverage"),
        ("hovsg", "mean_best_surface_coverage", "HOV-SG: partial reference coverage"),
    ]
    for ax, (method, metric, title) in zip(axes.ravel(), settings):
        reference = by_id[method + "-reference"][metric]
        for mode in colors:
            xs = [0.0]
            means = [reference]
            lower = [reference]
            upper = [reference]
            for amp in suite["protocol"]["translation_rms_m"]:
                values = [
                    r[metric]
                    for r in rows
                    if r["method"] == method and r["mode"] == mode and r["rms_m"] == amp
                ]
                xs.append(amp)
                means.append(np.mean(values))
                lower.append(min(values))
                upper.append(max(values))
            ax.plot(xs, means, "o-", color=colors[mode], label=mode)
            ax.fill_between(xs, lower, upper, color=colors[mode], alpha=0.12)
        ax.set(title=title, xlabel="Translation RMS (m)", xticks=[0, 0.03, 0.1, 0.3])
        ax.legend(fontsize=8)
    fig.suptitle(
        "Paired temporal ordering | identical error samples | mean and seed range, not confidence intervals"
    )
    fig.savefig(figure_dir / "paired-results.png", dpi=180)
    plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.7), layout="constrained")
    for ax, method, metric in zip(axes, ("dufomap", "beautymap"), ("direct_DA", "DA")):
        for mode in colors:
            xs = [0.0] + suite["protocol"]["translation_rms_m"]
            means = [by_id[method + "-reference"][metric]]
            for amp in xs[1:]:
                means.append(
                    np.mean(
                        [
                            r[metric]
                            for r in rows
                            if r["method"] == method and r["mode"] == mode and r["rms_m"] == amp
                        ]
                    )
                )
            ax.plot(xs, means, "o-", color=colors[mode], label=mode)
        ax.set(title=f"{method}: dynamic removal", xlabel="Translation RMS (m)", ylabel="DA (%)")
        ax.legend()
    fig.suptitle("Static retention must be read with dynamic removal, not alone")
    fig.savefig(figure_dir / "dynamic-recall.png", dpi=180)
    plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.5), layout="constrained")
    for ax, group in zip(axes, ("lidar", "semantic")):
        for mode in colors:
            values = np.load(args.suite / f"inputs/{group}/{mode}-0.30-104.npy")[:, 0]
            ax.plot(values, label=mode, color=colors[mode])
        ax.set(
            title=f"{group}: same 30 cm RMS scalar multiset",
            xlabel="Observation",
            ylabel="Injected world-x error (m)",
        )
        ax.legend()
    fig.savefig(figure_dir / "paired-errors.png", dpi=180)
    plt.close(fig)
    query_audit(root, args.suite, figure_dir / "target-query-audit.png")
    subprocess.run(
        [
            str(root / ".venv/bin/python"),
            str(root / "scripts/review_annotations.py"),
            "--output",
            str(args.output / "annotations"),
        ],
        cwd=root,
        check=True,
        stdout=subprocess.DEVNULL,
    )
    summary = {
        "primary_cells": 76,
        "parameter_control_cells": 21,
        "paired_differences": amplitude_summary,
        "references": [r for r in rows if r["mode"] == "reference"],
        "scope": suite["protocol"]["scope"],
        "hypothesis_status": "candidate; no matched-delay or dynamic-semantic validation",
        "annotation_status": "AI-assisted visual polygons; not independently human-reviewed; partial visible surfaces",
        "statistical_unit": "one KITTI teaser and one static Replica scene; seed ranges are not scene confidence intervals",
        "controls_scope": controls["protocol"]["scope"],
    }
    write_json(args.output / "summary.json", summary)
    record = {
        "schema_version": 1,
        "kind": "paired_pose_analysis",
        "status": "executed",
        "started_at": started_at,
        "finished_at": utc_now(),
        "exit_code": 0,
        "summary": summary,
        "repository": git_state(root),
        "script_sha256": digest(Path(__file__)),
        "artifacts": {},
    }
    for path in args.output.rglob("*"):
        if not path.is_file() or path == args.output / "record.json":
            continue
        local = path.suffix == ".npz"
        record["artifacts"][path.relative_to(args.output).as_posix()] = {
            "sha256": digest(path),
            "bytes": path.stat().st_size,
            "availability": "local_only" if local else "portable",
        }
    write_json(args.output / "record.json", record)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
