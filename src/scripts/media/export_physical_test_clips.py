"""Convert user-edited physical-test clips to full-duration GIF previews."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from fractions import Fraction
from pathlib import Path

from PIL import Image, ImageSequence, ImageStat


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def export(source, output, clips=None, image=None, compact_clips=None):
    videos = [source / name for name in clips] if clips else sorted(source.glob("*.mp4"))
    if not videos:
        raise ValueError("No MP4 clips found")
    if not all(video.is_file() for video in videos):
        raise FileNotFoundError("A selected video is missing")
    output.mkdir(parents=True, exist_ok=False)
    ffmpeg, ffprobe = shutil.which("ffmpeg"), shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        raise RuntimeError("FFmpeg and FFprobe are required")
    items = []
    for video in videos:
        probe = json.loads(subprocess.check_output([
            ffprobe, "-v", "error", "-select_streams", "v:0", "-show_entries",
            "stream=width,height,avg_frame_rate,nb_frames:format=duration", "-of", "json", str(video),
        ], text=True))
        stream = probe["streams"][0]
        duration = float(probe["format"]["duration"])
        subprocess.run([ffmpeg, "-v", "error", "-i", str(video), "-f", "null", "-"], check=True)
        portrait = stream["height"] > stream["width"]
        compact = video.name in (compact_clips or [])
        width = min(stream["width"], 360 if portrait else (480 if compact else 960))
        colors = 96 if portrait or compact else 128
        fps = 8 if compact else 10
        graph = (f"fps={fps},scale={width}:-2:flags=lanczos,split[a][b];"
                 f"[a]palettegen=max_colors={colors}:stats_mode=diff[p];"
                 "[b][p]paletteuse=dither=none:diff_mode=rectangle")
        gif = output / (video.stem + ".gif")
        subprocess.run([ffmpeg, "-v", "error", "-i", str(video), "-filter_complex_threads", "1",
                        "-filter_complex", graph, "-loop", "0", str(gif)], check=True)
        moments = [min(.5, duration / 4), duration / 2, max(0, duration - .3)]
        for index, moment in enumerate(moments):
            preview = output / f"{video.stem}-qa-{index}.png"
            subprocess.run([ffmpeg, "-v", "error", "-ss", str(moment), "-i", str(video),
                            "-frames:v", "1", "-vf", f"scale={width}:-2", str(preview)], check=True)
            with Image.open(preview) as frame:
                assert max(ImageStat.Stat(frame.convert("RGB")).stddev) > 3, "Blank review frame"
        with Image.open(gif) as animation:
            gif_duration = sum(frame.info.get("duration", 0) for frame in ImageSequence.Iterator(animation)) / 1000
            frames = animation.n_frames
            dimensions = list(animation.size)
        assert abs(gif_duration - duration) <= 1 / fps + .02, "GIF duration differs from the full source clip"
        item = {
            "source_name": video.name, "source_sha256": sha(video), "source_availability": "user_local_directory",
            "gif": gif.name, "source_video_dimensions": [stream["width"], stream["height"]],
            "source_frames": int(stream["nb_frames"]),
            "source_fps": float(Fraction(stream["avg_frame_rate"])),
            "source_duration_s": duration, "gif_duration_s": gif_duration, "gif_frames": frames,
            "gif_dimensions": dimensions, "gif_fps": fps, "speed_multiplier": 1,
            "additional_trim": False, "crop": False, "video_reencoded": False,
            "full_video_decoded": True, "qa_source_times_s": moments,
            "conversion_filter": graph,
        }
        items.append(item)
        print(f"{video.name}: full {duration:.3f}s → GIF {gif_duration:.3f}s, {frames} frames", flush=True)
    image_item = None
    if image:
        with Image.open(image) as original:
            dimensions = list(original.size)
        copied_image = output / "annotated-maps.png"
        shutil.copyfile(image, copied_image)
        image_item = {
            "source_name": image.name, "source_sha256": sha(image),
            "source_availability": "user_attachment", "image": copied_image.name,
            "dimensions": dimensions, "edited": False,
        }
    generator = output / "export_physical_test_clips.source.py"
    shutil.copyfile(Path(__file__), generator)
    record = {
        "schema_version": 1, "kind": "user_provided_physical_test_clips", "status": "recorded",
        "source_kind": "User-provided edited clips; conversion applies no further cuts or speed changes",
        "scope": "Physical scene and RViz video evidence; interpretation and analysis supplied by the user",
        "items": items,
        **({"image": image_item} if image_item else {}),
        "artifacts": {p.relative_to(output).as_posix(): {"sha256": sha(p), "bytes": p.stat().st_size,
                                                       "availability": "portable"}
                      for p in sorted(output.rglob("*")) if p.is_file()},
    }
    (output / "record.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--clips", nargs="+", help="Only convert these source filenames, in this order")
    parser.add_argument("--image", type=Path, help="Copy the user's annotated PNG without changes")
    parser.add_argument("--compact-clips", nargs="+", help="Use 480px / 8fps previews for selected camera clips")
    args = parser.parse_args()
    export(args.source.resolve(), args.output.resolve(), args.clips, args.image, args.compact_clips)
