"""Seal pre-output annotations and source hashes; draw independent review overlays."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--annotations", type=Path, required=True)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seal", action="store_true")
    args = parser.parse_args()
    cfg = json.loads(args.protocol.read_text())
    ann = json.loads(args.annotations.read_text())
    manifest = json.loads((args.data / "manifest.json").read_text())
    if ann["scene"] != cfg["scene"] or manifest["protocol_sha256"] != sha(args.protocol):
        raise ValueError("Frozen scene/protocol mismatch")
    if set(cfg["mapping_frames"]) & set(cfg["reference_frames"]):
        raise ValueError("Reference observations must not enter mapping")
    args.output.mkdir(parents=True, exist_ok=True)
    palette = ["#ff3b30", "#00c7be", "#ffcc00", "#af52de"]
    for frame in cfg["reference_frames"]:
        image = Image.open(args.data / cfg["scene"] / "results" / f"frame{frame:06d}.jpg")
        image = image.resize(tuple(ann["coordinate_canvas"]))
        draw = ImageDraw.Draw(image)
        for i, instance in enumerate(ann["instances"]):
            for view in instance["views"]:
                if view["frame"] != frame:
                    continue
                polygon = [tuple(p) for p in view["polygon"]]
                draw.line(polygon + [polygon[0]], fill=palette[i], width=2)
                x, y = polygon[0]
                draw.text((max(0, x), max(0, y - 12)), instance["id"], fill=palette[i], stroke_width=1)
        image.save(args.output / f"annotation-{frame:06d}.png")
    if args.seal:
        target = args.output / "freeze.json"
        if target.exists():
            raise FileExistsError("Never overwrite an annotation freeze")
        for item in manifest["files"]:
            if sha(args.data / item["path"]) != item["sha256"]:
                raise ValueError(f"Source changed: {item['path']}")
        record = {"id": cfg["id"], "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
                  "protocol_sha256": sha(args.protocol), "annotations_sha256": sha(args.annotations),
                  "source_manifest_sha256": sha(args.data / "manifest.json"),
                  "frontend_started": False, "mapper_started": False,
                  "annotation_review": "AI visual review; independent human review pending",
                  "reference_frames_disjoint": True}
        target.write_text(json.dumps(record, indent=2) + "\n")
        print(f"Annotations and RGB-D bound before frontend: {target}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
