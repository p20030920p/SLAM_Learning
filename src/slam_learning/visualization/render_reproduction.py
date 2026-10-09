"""Render an offline replay from verified original-evaluator point labels."""
from __future__ import annotations

import json
import shutil
import traceback
import uuid
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
from PIL import Image

from slam_learning.runtime.evaluation import check_point_order
from slam_learning.core.pcd import read_pcd
from slam_learning.core.provenance import digest, environment, git_state, source_hashes, utc_now, write_json
from slam_learning.runtime.runner import verify_record


def render_reproduction(root: Path, cross_record: Path) -> Path:
    output = root / "results/runs" / f"reproduction-media-{uuid.uuid4().hex[:12]}"
    output.mkdir(parents=True)
    record = {"schema_version": 1, "kind": "author_map_replay", "status": "running",
              "started_at": utc_now(), "environment": environment(), "repository": git_state(root),
              "source_sha256": source_hashes(root), "artifacts": {}}
    write_json(output / "record.json", record)
    try:
        issues = verify_record(cross_record, full=True)
        source = json.loads(cross_record.read_text(encoding="utf-8"))
        if issues or source.get("kind") != "map_evaluator_cross_check" or source.get("status") != "executed":
            raise ValueError(f"A verified completed evaluator cross-check is required: {issues}")
        if source.get("total_disagreement_points") != 0:
            raise ValueError("Resolve evaluator disagreements before publishing a common replay")
        sequence = root / ".cache/datasets/00"
        manifest = json.loads((sequence / "provenance.json").read_text(encoding="utf-8"))
        if manifest["archive_sha256"] != source["dataset"]["archive_sha256"]:
            raise ValueError("Render dataset differs from evaluator dataset")
        gt_path = sequence / "gt_cloud.pcd"
        if digest(gt_path) != manifest["files"]["gt_cloud.pcd"]:
            raise ValueError("Render GT differs from verified dataset")
        gt = read_pcd(gt_path)
        truth = np.asarray(gt.records["intensity"])
        paths = sorted((sequence / "pcd").glob("*.pcd"))
        offsets, start = [], 0
        for path in paths:
            cloud = read_pcd(path)
            if digest(path) != manifest["files"][path.relative_to(sequence).as_posix()]:
                raise ValueError("Render scan differs from verified dataset")
            stop = start + len(cloud.records)
            if not np.array_equal(cloud.xyz(), gt.xyz(slice(start, stop))):
                raise ValueError("Scan/GT identity is not exact")
            offsets.append((start, stop))
            start = stop
        if start != len(truth):
            raise ValueError("Scans do not exactly cover GT")
        predictions = {}
        for method in ("dufomap", "beautymap"):
            cloud = read_pcd(cross_record.parent / method / "eval/cleaned_exportGT.pcd")
            check_point_order(gt, cloud)
            predictions[method] = np.asarray(cloud.records["intensity"])
        config_path = root / "src/configs/rendering.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        palette = config["palette"]
        colors = {"static": palette["static"], "true_positive": palette["correct_dynamic_removal"],
                  "false_positive": palette["false_static_removal"], "false_negative": palette["missed_dynamic"]}
        frame_indexes = np.unique(np.linspace(0, len(paths) - 1, config["gif_target"]["max_frames"], dtype=int))
        # Choose once over the whole source sequence, then reuse on every panel/frame.
        sample = gt.xyz(slice(None, None, 500))
        lower, upper = np.quantile(sample[:, :2], [0.005, 0.995], axis=0)
        margin = np.maximum((upper - lower) * 0.03, 1.0)
        lower, upper = lower - margin, upper + margin
        camera = {"projection": "world XY bird's-eye", "bounds_xy_m": [lower.tolist(), upper.tolist()],
                  "selection": "0.5/99.5 percentiles of every 500th GT point, plus 3 percent/minimum 1 m margin"}
        settings = {"frame_ids": [paths[i].name for i in frame_indexes], "camera": camera,
                    "colors": colors, "display_points_per_class": 8000, "sampling": "uniform index spacing",
                    "fps": config["gif_target"]["fps"], "label_protocol": "original PCL map correspondence at 5 cm",
                    "counts": "all points in each selected scan, before display thinning/cropping",
                    "scope": "Offline labels from final maps; selected teaser entries, not online inference"}
        write_json(output / "render.json", settings)
        shutil.copy2(cross_record, output / "input-evaluator-record.json")
        record.update(input_record_sha256=digest(cross_record), dataset_archive_sha256=manifest["archive_sha256"],
                      rendering_config_sha256=digest(config_path), rendering=settings)
        images, statistics = [], []
        fig, axes = plt.subplots(2, 3, figsize=(12, 6.6), layout="constrained")
        categories = {"static": (truth == 0), "dynamic": (truth == 1)}
        for frame in frame_indexes:
            start, stop = offsets[frame]
            xy = gt.xyz(slice(start, stop))[:, :2]
            static = categories["static"][start:stop]
            dynamic = categories["dynamic"][start:stop]
            visible = ((xy >= lower) & (xy <= upper)).all(axis=1)

            def scatter(ax, mask, color, size=1):
                indices = np.flatnonzero(mask & visible)
                if len(indices) > 8000:
                    indices = indices[np.linspace(0, len(indices) - 1, 8000, dtype=int)]
                if len(indices):
                    ax.scatter(xy[indices, 0], xy[indices, 1], s=size, c=color, linewidths=0)

            for row, method in enumerate(("dufomap", "beautymap")):
                removed = predictions[method][start:stop] == 1
                tp, fp, fn = dynamic & removed, static & removed, dynamic & ~removed
                kept_static = static & ~removed
                statistics.append({"frame": paths[frame].name, "method": method, "points": stop - start,
                    "display_roi_points": int(visible.sum()), "removed_dynamic": int(tp.sum()),
                    "removed_static": int(fp.sum()), "kept_dynamic": int(fn.sum()),
                    "kept_static": int(kept_static.sum())})
                for column, ax in enumerate(axes[row]):
                    ax.clear()
                    ax.set(xlim=(lower[0], upper[0]), ylim=(lower[1], upper[1]), aspect="equal")
                    ax.set_facecolor("#f6f7f8")
                    ax.set_xlabel("World X (m)", fontsize=8)
                    ax.set_ylabel("World Y (m)", fontsize=8)
                    ax.tick_params(labelsize=7)
                    if column == 0:
                        scatter(ax, static, colors["static"], 0.5)
                        scatter(ax, dynamic, colors["true_positive"], 2)
                        ax.set_title(f"{method.upper()} | input with GT color", fontsize=9)
                    elif column == 1:
                        scatter(ax, fp, colors["false_positive"], 1)
                        scatter(ax, tp, colors["true_positive"], 2)
                        ax.set_title(f"Removed | dynamic {tp.sum():,} / static {fp.sum():,}", fontsize=9)
                    else:
                        scatter(ax, kept_static, colors["static"], 0.5)
                        scatter(ax, fn, colors["false_negative"], 2)
                        ax.set_title(f"Retained | dynamic {fn.sum():,}", fontsize=9)
            fig.suptitle(f"KITTI-00 teaser | {paths[frame].stem} | Offline final-map replay", fontsize=13)
            legend = [Line2D([], [], marker="o", linestyle="", color=colors[k], markersize=4, label=label)
                      for k, label in (("static", "Static retained / reference"),
                       ("true_positive", "Dynamic removed / GT dynamic"),
                       ("false_positive", "Static wrongly removed"), ("false_negative", "Dynamic retained"))]
            if fig.legends:
                fig.legends[0].remove()
            fig.legend(handles=legend, loc="outside lower center", ncols=2, fontsize=8)
            fig.canvas.draw()
            images.append(Image.fromarray(np.asarray(fig.canvas.buffer_rgba())).convert("RGB"))
        plt.close(fig)
        images[0].save(output / "replication_frame.png")
        images[0].save(output / "replication_hero.gif", save_all=True, append_images=images[1:],
                       duration=round(1000 / settings["fps"]), loop=0, optimize=True)
        write_json(output / "frame_counts.json", statistics)
        record.update(status="executed", frames_rendered=len(images), metrics_scope="Full maps scored before rendering")
    except Exception as e:
        record.update(status="failed", error=str(e), traceback=traceback.format_exc())
    finally:
        record["finished_at"] = utc_now()
        for name in ("replication_hero.gif", "replication_frame.png", "render.json", "frame_counts.json",
                     "input-evaluator-record.json"):
            path = output / name
            if path.is_file():
                record["artifacts"][name] = {"sha256": digest(path), "bytes": path.stat().st_size,
                                           "availability": "portable"}
        write_json(output / "record.json", record)
    print(f"Reproduction replay: {record['status']} -> {output / 'record.json'}", flush=True)
    return output / "record.json"
