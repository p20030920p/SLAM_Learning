"""Publish verified RViz inspection clips without calling them live inference."""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageStat

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from slam_learning.core.provenance import digest, utc_now


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[3])
    args = parser.parse_args()
    destination = args.root / "results/reference/visual-review"
    destination.mkdir(parents=True, exist_ok=False)
    media = args.root / "docs/media/rviz"
    media.mkdir(parents=True, exist_ok=False)
    summaries = []
    for method in ("dufomap", "beautymap", "conceptgraphs", "hovsg"):
        source = args.source / method
        capture = source / "capture"
        raw_record = json.loads((capture / "recording.json").read_text())
        manifest = json.loads((source / "data/manifest.json").read_text())
        if raw_record["command_exit_code"] != 0 or not raw_record["full_video_decoded"]:
            raise ValueError(f"Rejected capture: {method}")
        video = capture / "full-session.mp4"
        if digest(video) != raw_record["artifacts"][video.name]["sha256"]:
            raise ValueError("Capture video changed")
        for path, expected in manifest["sources"].items():
            if digest(Path(path)) != expected:
                raise ValueError(f"Measured source changed: {path}")
        if digest(source / "data/prepare_visual_review.source.py") != manifest["generator_sha256"]:
            raise ValueError("Preparation source differs from manifest")
        subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), "-f", "null", "-"], check=True)
        out = destination / method
        out.mkdir()
        shutil.copy2(video, out / "review.mp4")
        shutil.copy2(video, media / f"{method}.mp4")
        for name in ("recording.json", "command.json", "exit.json", "terminal.raw", "terminal.time"):
            shutil.copy2(capture / name, out / name)
        for name in ("manifest.json", "review.rviz", "rviz.log", "prepare_visual_review.source.py",
                     "view_measured_rviz.source.py", "record_visual_review.source.sh"):
            shutil.copy2(source / "data" / name, out / name)
        steps = len(manifest["steps"])
        moments = [5+7*i for i in range(steps)]
        for i, moment in enumerate(moments):
            screenshot = out / f"qa-{i:02d}.png"
            subprocess.run(["ffmpeg", "-v", "error", "-ss", str(moment), "-i", str(video),
                            "-frames:v", "1", str(screenshot)], check=True)
            with Image.open(screenshot) as image:
                if max(ImageStat.Stat(image.crop((305, 72, 1250, 760))).stddev) < 3:
                    raise ValueError("Blank RViz scene")
        poster = out / f"qa-{min(steps-1, 2):02d}.png"
        shutil.copy2(poster, out / "poster.png")
        shutil.copy2(poster, media / f"{method}.png")
        summaries.append({"method": method, "duration_seconds": raw_record["duration_seconds"],
                          "steps": steps, "scope": manifest["scope"],
                          "source_manifest_sha256": digest(out / "manifest.json"),
                          "video_sha256": digest(video), "qa_times_s": moments,
                          "full_decode_passed": True, "human_visual_review": "pending"})
    recorder = args.root / "src/scripts/media/record_session.py"
    if digest(recorder) != raw_record["recorder_script_sha256"]:
        raise ValueError("Recorder source changed")
    shutil.copy2(recorder, destination / "record_session.source.py")
    shutil.copy2(Path(__file__), destination / "import_visual_reviews.source.py")
    (destination / "summary.json").write_text(json.dumps(summaries, indent=2)+"\n")
    record = {"schema_version": 1, "kind": "graphical_measured_map_inspection", "status": "executed",
              "created_at": utc_now(), "scope": "Actual RViz graphical windows captured from saved native outputs; no live inference, simulated robot or FPS benchmark",
              "wrapper_metadata_note": "Nested recording.json uses the historical terminal-wrapper kind; it captures the whole private X framebuffer including RViz and the evidence panel",
              "summary": summaries, "artifacts": {}}
    for path in sorted(destination.rglob("*")):
        if path.is_file():
            record["artifacts"][path.relative_to(destination).as_posix()] = {
                "sha256": digest(path), "bytes": path.stat().st_size, "availability": "portable"}
    (destination / "record.json").write_text(json.dumps(record, indent=2)+"\n")
    print(destination / "record.json")


if __name__ == "__main__":
    main()
