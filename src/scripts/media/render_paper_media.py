"""Render measured outputs as H.264 replays; playback rate is not algorithm throughput."""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import uuid
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageSequence

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from slam_learning.core.provenance import digest, environment, git_state, utc_now, write_json
from slam_learning.runtime.runner import verify_record


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("method", choices=("dufomap", "beautymap"))
    parser.add_argument("record", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    source = args.record.resolve()
    issues = verify_record(source, full=True)
    record = json.loads(source.read_text(encoding="utf-8"))
    if issues or record.get("status") != "executed":
        raise ValueError(f"Completed full local evidence required: {issues}")
    output = root / "results/runs" / f"paper-media-{args.method}-{uuid.uuid4().hex[:12]}"
    output.mkdir(parents=True)
    started = utc_now()
    if record.get("kind") != "author_map_replay":
        raise ValueError("Verified PCL map replay input required")
    frames = []
    with Image.open(source.parent / "replication_hero.gif") as gif:
        font = ImageFont.truetype("DejaVuSans.ttf", 20)
        for index, frame in enumerate(ImageSequence.Iterator(gif)):
            frame = frame.convert("RGB")
            # One method's native map panels, retaining full horizontal world view.
            y0, y1 = (30, 315) if args.method == "dufomap" else (320, 600)
            panel = frame.crop((0, y0, frame.width, y1)).resize((1200, 320))
            canvas = Image.new("RGB", (1200, 440), "white")
            canvas.paste(panel, (0, 65))
            draw = ImageDraw.Draw(canvas)
            frame_id = record["rendering"]["frame_ids"][index]
            draw.text((25, 15), args.method.upper() + " | " + frame_id + " | offline final-map replay", font=font, fill="#19383f")
            draw.text((25, 385), "Green: removed dynamic   Red: removed static   Blue: retained dynamic", font=font, fill="#19383f")
            draw.text((25, 413), "21 selected frames / 141 scored. Playback speed is not runtime.", font=font, fill="#19383f")
            frames.append(canvas)
    settings = {"view": record["rendering"]["camera"], "source_frame_ids": record["rendering"]["frame_ids"],
                "scope": "One method cropped from the verified common PCL-label replay; all metrics computed before rendering"}
    # Encode H.264 for browser playback; decode every frame to validate completion.
    import imageio_ffmpeg
    import cv2
    width, height = frames[0].size
    fps, repeats = 12, 8
    writer = imageio_ffmpeg.write_frames(str(output / "replay.mp4"), (width, height), fps=fps,
                                        codec="libx264", quality=7, macro_block_size=2,
                                        output_params=["-pix_fmt", "yuv420p", "-movflags", "+faststart"])
    writer.send(None)
    for frame in frames:
        for _ in range(repeats):
            writer.send(np.asarray(frame))
    writer.close()
    cap = cv2.VideoCapture(str(output / "replay.mp4"))
    decoded, ranges = 0, []
    while True:
        okay, frame = cap.read()
        if not okay:
            break
        decoded += 1
        if decoded in (1, len(frames)*repeats//2, len(frames)*repeats):
            ranges.append(float(frame.std()))
    cap.release()
    if decoded != len(frames)*repeats or min(ranges) < 5:
        raise ValueError("Encoded replay is truncated or blank")
    preview = [frame.resize((960, round(frame.height * 960 / frame.width))).quantize(colors=128)
               for frame in frames]
    preview[0].save(output / "preview.gif", save_all=True, append_images=preview[1:],
                    duration=round(1000*repeats/fps), loop=0, optimize=True)
    frames[0].save(output / "poster.png")
    shutil.copy2(source, output / "input-record.json")
    settings.update(playback_fps=fps, repeats_per_observation=repeats, encoded_frames=decoded,
                    duration_s=decoded/fps, codec="H.264", inspected_frame_stddev=ranges,
                    reference={"repository": "https://github.com/p20030920p/Sim2Real-AlgoBench",
                               "commit": "53324d40def0dd753b4a99021b8fe596955a1ecd",
                               "adapted_convention": "Per-method MP4 + GIF + metadata, fixed view and decoded-output QA; no source copied"})
    write_json(output / "render.json", settings)
    result = {"schema_version": 1, "kind": "paper_reproduction_media", "method": args.method,
              "status": "executed", "started_at": started, "finished_at": utc_now(),
              "environment": environment(), "repository": git_state(root), "generator_sha256": digest(Path(__file__)),
              "input_record_sha256": digest(source), "rendering": settings, "artifacts": {}}
    for name in ("replay.mp4", "preview.gif", "poster.png", "render.json", "input-record.json"):
        path = output / name
        result["artifacts"][name] = {"sha256": digest(path), "bytes": path.stat().st_size, "availability": "portable"}
    write_json(output / "record.json", result)
    print(output / "record.json", flush=True)


if __name__ == "__main__":
    main()
