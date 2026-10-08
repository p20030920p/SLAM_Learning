"""Prepare all four arms for an actual RViz window recording, labelled saved-map replay."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from slam_learning.identity_budget import ARMS, digest, load_snapshot


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    record = json.loads((args.run / "record.json").read_text())
    if record["status"] != "executed" or len(record["cells"]) != 28:
        raise ValueError("Completed full suite required")
    args.output.mkdir(parents=True, exist_ok=False)
    palette = np.array([[75, 184, 208], [248, 177, 65], [146, 207, 102], [193, 137, 244]], dtype=np.uint8)
    steps, sources, displayed = [], {str(args.run / "record.json"): digest(args.run / "record.json")}, []
    # Fixed illustration condition declared before results; every arm is shown.
    for stage, source_frame in ((8, 175), (12, 275), (16, 375)):
        for arm_index, arm in enumerate(ARMS):
            folder = args.run / "cells" / f"{arm}-0.30-417"
            source = folder / f"stage-{stage:02d}-complete.npz"
            cell_info = next(c for c in record["cells"] if c["name"] == folder.name)
            if digest(folder / "record.json") != cell_info["record_sha256"]:
                raise ValueError("Changed source cell")
            cell = json.loads((folder / "record.json").read_text())
            if digest(source) != cell["artifacts"][source.name]["sha256"]:
                raise ValueError("Changed saved state")
            saved = load_snapshot(source)
            xyz = np.concatenate(saved["clouds"]).astype(np.float32)
            transform = xyz[:, [0, 2, 1]] * np.array([1, 1, -1], dtype=np.float32)
            sample = np.linspace(0, len(xyz) - 1, min(len(xyz), 120000), dtype=int)
            xyz = transform[sample]
            target = args.output / f"{len(steps):03d}.npz"
            image_path = args.data / "room2/results" / f"frame{source_frame:06d}.jpg"
            rgb = np.broadcast_to(palette[arm_index], xyz.shape).copy()
            np.savez_compressed(target, xyz=xyz, rgb=rgb,
                                image=np.asarray(Image.open(image_path).convert("RGB").resize((640, 360))))
            steps.append({"file": target.name, "sha256": digest(target), "source_index": source_frame,
                          "label": f"AI-ONLY EXPLORATORY | SAVED MAP REPLAY | {arm} | obs {stage} | 30cm seed417",
                          "input_points": len(transform), "display_points": len(xyz)})
            sources[str(source)] = digest(source)
            sources[str(image_path)] = digest(image_path)
            displayed.append(xyz)
    lower, upper = np.quantile(np.concatenate(displayed), [.01, .99], axis=0)
    manifest = {"schema_version": 1, "kind": "measured_output_rviz_review", "method": "conceptgraphs",
                "legend": "Arm colors only, not query scores or ground truth.\n\nComplete saved native states; no support/cap filtering in this view.\n\nAI-only exploratory; saved-map replay, not inference.",
                "scope": "AI-only labels; actual RViz display of saved complete states, not live inference or FPS",
                "steps": steps, "sources": sources, "generator_sha256": digest(Path(__file__)),
                "display_transform": "Replica (x,y,z)->(x,z,-y), display thinning only; stored maps unchanged",
                "focal_point": ((lower + upper) / 2).tolist(), "distance": float(np.linalg.norm(upper - lower) * 1.15)}
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(args.output / "manifest.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
