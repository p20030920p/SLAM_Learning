"""Seal pre-output annotations and source hashes; draw independent review overlays."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from slam_learning.identity_budget import validate_annotations, validate_protocol, validate_review


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--annotations", type=Path, required=True)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seal", action="store_true")
    parser.add_argument("--human-review", type=Path,
                        help="Owner's reviewed, hash-bound receipt; mandatory for v2 sealing")
    parser.add_argument("--exploratory", action="store_true", help="Explicit AI-only owner-amended protocol")
    args = parser.parse_args()
    cfg = json.loads(args.protocol.read_text())
    ann = json.loads(args.annotations.read_text())
    manifest = json.loads((args.data / "manifest.json").read_text())
    if ann["scene"] != cfg["scene"] or manifest["protocol_sha256"] != sha(args.protocol):
        raise ValueError("Frozen scene/protocol mismatch")
    if set(cfg["mapping_frames"]) & set(cfg["reference_frames"]):
        raise ValueError("Reference observations must not enter mapping")
    review = None
    if args.exploratory:
        validate_protocol(cfg, exploratory=True)
        validate_annotations(cfg, ann, require_review=False, exploratory=True)
    elif cfg.get("analysis_type") == "ai_only_exploratory":
        raise ValueError("AI-only protocol requires explicit --exploratory")
    if cfg.get("requires_human_review"):
        validate_annotations(cfg, ann, require_review=args.seal)
        if args.seal:
            if not args.human_review:
                raise ValueError("Human review receipt required before sealing room2")
            review = json.loads(args.human_review.read_text(encoding="utf-8"))
            validate_review(args.protocol, args.annotations, args.data, review)
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
                draw.line(polygon + [polygon[0]], fill=palette[i % len(palette)], width=2)
                x, y = polygon[0]
                draw.text((max(0, x), max(0, y - 12)), instance["id"], fill=palette[i % len(palette)], stroke_width=1)
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
        if review is not None:
            record.update(annotation_review="Independent human review recorded before frontend",
                          human_review=review, human_review_sha256=hashlib.sha256(json.dumps(
                              review, sort_keys=True, separators=(",", ":")).encode()).hexdigest())
        if args.exploratory:
            record.update(analysis_type="ai_only_exploratory", human_reviewed=False,
                          annotation_review="AI-only raw-view review; owner waived manual review on experimental branch",
                          owner_amendment=cfg["owner_amendment"])
        target.write_text(json.dumps(record, indent=2) + "\n")
        print(f"Annotations and RGB-D bound before frontend: {target}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
