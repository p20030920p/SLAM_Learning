"""Build reviewable raw-image overlays and evaluation-only surface references."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from slam_learning.core.paired_pose import reference_targets
from slam_learning.core.provenance import digest, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    args.output.mkdir(parents=True, exist_ok=False)
    targets = reference_targets(root)
    colors = ["#10b981", "#f97316", "#06b6d4", "#f43f5e"]
    for frame in sorted({t["source_frame"] for t in targets}):
        image = Image.open(root / f".cache/semantic-data/Replica/room0/results/frame{frame:06d}.jpg").resize(
            (640, 363)
        )
        draw = ImageDraw.Draw(image)
        for target, color in zip(targets, colors):
            if target["source_frame"] != frame:
                continue
            polygon = [tuple(point) for point in target["polygon"]]
            draw.line(polygon + [polygon[0]], fill=color, width=3)
            x, y = target["anchor_pixel"]
            draw.ellipse((x - 4, y - 4, x + 4, y + 4), fill=color)
            draw.text(
                (polygon[0][0], max(0, polygon[0][1] - 14)),
                target["id"],
                fill=color,
                stroke_width=1,
                stroke_fill="black",
            )
        image.save(args.output / f"annotation-{frame:06d}.png")
    portable = []
    for target in targets:
        portable.append(
            {k: target[k] for k in ("id", "query", "source_frame", "polygon", "anchor_pixel", "points_count")}
            | {
                "anchor_world_m": target["anchor_world_m"].tolist(),
                "visible_surface_min_m": target["points"].min(axis=0).tolist(),
                "visible_surface_max_m": target["points"].max(axis=0).tolist(),
            }
        )
    write_json(
        args.output / "reference-targets.json",
        {
            "targets": portable,
            "annotation_sha256": digest(root / "src/configs/annotations/room0/targets.json"),
            "calibration": "Pinned Replica original K=[600,600,599.5,339.5], depth divisor 6553.5",
            "reference": "AI-assisted visual labels; provided depth/pose geometry; partial visible surfaces only; no human validation",
        },
    )
    np.savez_compressed(args.output / "reference-points.npz", **{t["id"]: t["points"] for t in targets})
    print(json.dumps(portable, indent=2))


if __name__ == "__main__":
    main()
