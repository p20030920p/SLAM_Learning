"""Render existing evidence for the README; no inference or new experiments."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from slam_learning.provenance import digest, environment, utc_now, write_json


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="New output directory")
    args = parser.parse_args()
    out = args.output.resolve()
    if (out / "record.json").exists() or any(out.glob("*.gif")) or any(out.glob("*.png")):
        raise SystemExit("Refusing to replace existing media; choose a new output directory")
    out.mkdir(parents=True, exist_ok=True)
    source = root / "results/reference/homepage-media/inputs"
    inputs = {}

    def read(path: Path):
        inputs[path.relative_to(root).as_posix()] = digest(path)
        return json.loads(path.read_text(encoding="utf-8"))

    dufo = read(root / "results/reference/dufomap-wsl/metrics.json")
    beauty = read(root / "results/reference/beautymap-wsl/metrics.json")
    cg = read(source / "conceptgraphs-room0-metrics.json")["rows"][0]
    delayed = read(root / "results/reference/delayed-support-control/summary.json")
    origins = read(source / "origins.json")
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
    colors = ("#137d8d", "#ba5148")

    def grouped(ax, labels, values, names, limit=100):
        x = np.arange(len(labels))
        for index, (series, name) in enumerate(zip(values, names)):
            bars = ax.bar(x + (index - .5) * .34, series, .32, color=colors[index], label=name)
            ax.bar_label(bars, fmt="%.1f", fontsize=9, padding=3)
        ax.set_xticks(x, labels)
        ax.set_ylim(0, limit)
        ax.grid(axis="y", alpha=.15)
        ax.set_axisbelow(True)
        ax.legend(frameon=False, loc="upper right", fontsize=9)

    fig, axes = plt.subplots(1, 2, figsize=(11, 3.7), layout="constrained")
    grouped(axes[0], ["DUFOMap", "BeautyMap"],
            [[dufo["SA"], beauty["SA"]], [dufo["DA"], beauty["DA"]]],
            ["Static retention (SA)", "Dynamic removal (DA)"], 130)
    axes[0].set_yticks(np.arange(0, 101, 20))
    axes[0].set_title("Mapping cores | KITTI-00 teaser, 141 scans")
    axes[0].set_ylabel("Points (%) | 5 cm map-neighbor scoring")
    keys = ["miou", "fmiou", "mrecall", "mprecision"]
    bars = axes[1].bar(np.arange(4), [cg[k] for k in keys], color=colors[0], width=.58)
    axes[1].bar_label(bars, fmt="%.2f", padding=3)
    axes[1].set_xticks(np.arange(4), ["mIoU", "FW-IoU", "mRecall", "mPrecision"])
    axes[1].set_ylim(0, 100)
    axes[1].set_title("Author ConceptGraphs | room0, 400 frames")
    axes[1].set_ylabel("Semantic classification (%) | 23 valid classes")
    axes[1].grid(axis="y", alpha=.15)
    axes[1].set_axisbelow(True)
    fig.savefig(out / "baseline-metrics.png", dpi=170)
    plt.close(fig)

    row = next(r for r in delayed["results"] if r["rms_m"] == .3)
    conditions = ["Fixed history / support 3", "Fixed history / support 1*",
                  "Oracle reassociation / support 3"]
    labels = ["Fixed / support 3", "Fixed / support 1*", "Oracle / support 3"]
    fig, axes = plt.subplots(1, 2, figsize=(11, 3.7), layout="constrained")
    grouped(axes[0], labels,
            [[100 * row[c][key] for c in conditions] for key in ("prefix_recovery", "prefix_query_hit")],
            ["Target recovery", "Restricted query hit"], 125)
    axes[0].set_title("room1 | immediately after 30 cm pose correction")
    axes[0].set_ylabel("Mean over 3 seeds (%)")
    bars = axes[1].bar(np.arange(3), [row[c]["map_objects"] for c in conditions], color=colors[0], width=.58)
    axes[1].bar_label(bars, fmt="%.1f", padding=3)
    axes[1].set_xticks(np.arange(3), labels)
    axes[1].set_ylim(0, 140)
    axes[1].set_title("Exposure cost | candidate caps are NOT matched")
    axes[1].set_ylabel("Exposed candidates (mean count)")
    axes[1].grid(axis="y", alpha=.15)
    axes[1].set_axisbelow(True)
    fig.suptitle("Partial AI labels; *support-1 is post-hoc. Descriptive means, not confidence intervals.", fontsize=10)
    fig.savefig(out / "recovery-cost.png", dpi=170)
    plt.close(fig)

    prefix = ["wsl", "-d", "Ubuntu-22.04", "--exec"] if os.name == "nt" else []

    def native_path(path: Path) -> str:
        value = path.as_posix()
        return f"/mnt/{value[0].lower()}{value[2:]}" if os.name == "nt" else value

    clips = [(f"{m}-rviz", root / f"docs/media/rviz/{m}.mp4", 5, 24)
             for m in ("dufomap", "beautymap", "conceptgraphs", "hovsg")]
    clips.append(("conceptgraphs-author-viewer", source / "conceptgraphs-room0-original-window.mp4", 5, 48))
    commands = []
    for name, video, start, duration in clips:
        inputs[video.relative_to(root).as_posix()] = digest(video)
        target = out / f"{name}.gif"
        filters = ("fps=2,scale=720:-1:flags=lanczos,split[a][b];"
                   "[a]palettegen=max_colors=96[p];[b][p]paletteuse=dither=bayer")
        cmd = [*prefix, "ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-threads", "1",
               "-ss", str(start), "-t", str(duration), "-i", native_path(video),
               "-filter_complex_threads", "1", "-filter_complex", filters, "-loop", "0", native_path(target)]
        subprocess.run(cmd, check=True, capture_output=True)
        commands.append({"name": name, "start_seconds": start, "duration_seconds": duration, "command": cmd})
    artifacts = {p.name: {"sha256": digest(p), "bytes": p.stat().st_size, "availability": "portable"}
                 for p in sorted(out.iterdir()) if p.suffix in (".png", ".gif")}
    write_json(out / "record.json", {
        "schema_version": 1, "kind": "homepage_evidence_render", "status": "executed", "exit_code": 0,
        "finished_at": utc_now(), "generator": "scripts/build_homepage_media.py",
        "generator_sha256": digest(Path(__file__)), "environment": environment(),
        "input_sha256": inputs, "external_origins": origins, "clips": commands, "artifacts": artifacts,
        "scope": "Existing measurements and saved-map viewer recordings. No new inference, runtime or H1 claim.",
        "plots": {"baseline-metrics.png": "Separate LiDAR core and single-scene author semantic protocols; no common ranking.",
                  "recovery-cost.png": "30 cm, correction at observation 8; three-seed descriptive means, partial AI surfaces; support-1 post-hoc; unequal candidate budgets."}})
    print(f"Rendered {len(artifacts)} assets: {out}")


if __name__ == "__main__":
    main()
