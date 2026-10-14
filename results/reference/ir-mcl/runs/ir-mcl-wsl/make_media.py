#!/usr/bin/env python3
"""Derive the IR-MCL replay media from the delivered GIF.

Inputs (written by the recorded reproduction run):
  media/preview.gif                     upstream loc_demo.py output, all saved frames
Outputs:
  media/replay/replay.mp4               H.264, constant frame rate, faststart
  media/replay/poster.png               first frame
  media/replay/render.json              measured encode facts and QA results
  media/replay/record.json              media record (kind: paper_reproduction_media)

Every number written here is measured from the produced files; nothing is assumed.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageSequence, ImageStat

ROOT = Path(__file__).resolve().parents[5]          # repository root
DELIVERY = ROOT / "results/reference/ir-mcl"
GIF = DELIVERY / "media/preview.gif"
REPLAY = DELIVERY / "media/replay"
FPS = 10


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def probe(path: Path) -> dict:
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
        text=True,
    )
    return json.loads(out)


def main() -> int:
    REPLAY.mkdir(parents=True, exist_ok=True)

    # --- measure the source GIF ---
    with Image.open(GIF) as gif:
        delays = [frame.info.get("duration", 0) for frame in ImageSequence.Iterator(gif)]
        gif_frames = len(delays)
        gif_duration_ms = delays[0]
        gif_size = list(gif.size)
    if set(delays) != {100}:
        raise ValueError("Expected the upstream's continuous 10 fps GIF")
    gif_seconds = sum(delays) / 1000.0

    replay = REPLAY / "replay.mp4"
    command = [
        "ffmpeg", "-y", "-v", "error", "-i", str(GIF),
        "-r", str(FPS), "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(replay),
    ]
    subprocess.run(command, check=True)

    # --- verify the encode by decoding every frame ---
    subprocess.run(["ffmpeg", "-v", "error", "-i", str(replay), "-f", "null", "-"], check=True)
    info = probe(replay)
    stream = next(s for s in info["streams"] if s["codec_type"] == "video")
    duration = float(info["format"]["duration"])
    expected = round(gif_seconds * FPS)
    decoded = int(stream["nb_frames"])
    if decoded != expected or abs(duration - gif_seconds) > 0.011:
        raise ValueError("Replay frame count or duration differs from recorded GIF")

    # --- blank-frame QA at the start, middle and end ---
    stddevs = []
    for label, moment in (("start", 0.5), ("middle", duration / 2), ("end", max(0.0, duration - 0.5))):
        frame = REPLAY / f"qa-{label}.png"
        subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-ss", str(moment), "-i", str(replay),
             "-frames:v", "1", str(frame)],
            check=True,
        )
        with Image.open(frame) as image:
            stddevs.append(round(max(ImageStat.Stat(image).stddev), 3))
    if min(stddevs) < 3:
        raise SystemExit(f"nearly blank QA frame: {stddevs}")

    with Image.open(replay.with_name("qa-start.png")) as first:
        first.convert("RGB").save(REPLAY / "poster.png")

    render = {
        "source_gif": "results/reference/ir-mcl/media/preview.gif",
        "source_gif_sha256": sha(GIF),
        "source_gif_frames": gif_frames,
        "source_gif_frame_delay_ms": gif_duration_ms,
        "source_gif_dimensions": gif_size,
        "source_gif_duration_seconds": round(gif_seconds, 3),
        "playback_fps": FPS,
        "encoded_frames": decoded,
        "expected_frames": expected,
        "encoded_duration_seconds": round(duration, 3),
        "dimensions": [stream["width"], stream["height"]],
        "codec": stream["codec_name"],
        "pix_fmt": stream["pix_fmt"],
        "command": command,
        "qa_frame_stddev": stddevs,
        "full_decode_passed": True,
        "frame_count_passed": decoded == expected,
        "scope": "Constant-rate re-encode of the saved localization frames; playback rate is not algorithm throughput",
    }
    (REPLAY / "render.json").write_text(json.dumps(render, indent=2) + "\n")

    artifacts = {}
    for name in ("replay.mp4", "poster.png", "render.json", "qa-start.png", "qa-middle.png", "qa-end.png"):
        path = REPLAY / name
        artifacts[name] = {"sha256": sha(path), "bytes": path.stat().st_size, "availability": "portable"}

    record = {
        "schema_version": 1,
        "kind": "paper_reproduction_media",
        "method": "ir-mcl",
        "status": "executed",
        "started_at": now(),
        "finished_at": now(),
        "input_record_sha256": sha(DELIVERY / "runs/ir-mcl-wsl/record.json"),
        "rendering": render,
        "artifacts": artifacts,
    }
    (REPLAY / "record.json").write_text(json.dumps(record, indent=2) + "\n")

    record["artifacts"]["record.json"] = {
        "sha256": sha(REPLAY / "record.json"),
        "bytes": (REPLAY / "record.json").stat().st_size,
        "availability": "portable",
    }
    print(json.dumps({k: render[k] for k in
                      ("source_gif_frames", "encoded_frames", "encoded_duration_seconds",
                       "dimensions", "qa_frame_stddev", "frame_count_passed")}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
