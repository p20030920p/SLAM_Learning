"""Export complete hardware recordings at their original playback speed."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from fractions import Fraction
from pathlib import Path

from PIL import Image, ImageSequence, ImageStat


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--photo", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--wsl", default="Ubuntu-22.04")
    args = parser.parse_args()
    source = args.source.resolve()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)

    def media_path(path: Path) -> str:
        value = path.resolve().as_posix()
        if len(value) < 3 or value[1:3] != ":/":
            raise ValueError("Expected a Windows drive path")
        return "/mnt/" + value[0].lower() + value[2:]

    def run(program: str, options: list[str]) -> bytes:
        result = subprocess.run(["wsl", "-d", args.wsl, "--exec", program, *options],
                                capture_output=True, check=False)
        if result.returncode:
            raise RuntimeError(result.stderr.decode("utf-8", errors="replace")[-2000:])
        return result.stdout

    evidence = source / "evidence/postfall-dual-lowlight-20261009.json"
    original = json.loads(evidence.read_text(encoding="utf-8"))
    pair = original["live_pairs"][0]
    videos = {item["path"].replace("\\", "/"): item["sha256"] for item in pair["media"]}
    destination = output / "evidence"
    destination.mkdir()
    shutil.copy2(evidence, destination / evidence.name)
    shutil.copy2(args.photo, output / "devices.jpg")
    items = []
    for name, sensor, key in [("d435", "camera", "camera_session"), ("l2", "lidar", "lidar_session"),
                              ("d435-input", "camera", None)]:
        session_name = pair[key] if key else original["projector_trials"][0]["session"] + "/camera"
        session = source / session_name.replace("\\", "/")
        video = session / ("rviz-live.mp4" if key else "preview.mp4")
        relative = video.relative_to(source).as_posix()
        if key and digest(video) != videos[relative]:
            raise ValueError(f"Recorded video changed: {relative}")
        saved = destination / name
        saved.mkdir()
        for filename in ("capture.json", "live-result.json", "config.json", "video.json", "code-hashes.json"):
            if (session / filename).is_file():
                shutil.copy2(session / filename, saved / filename)
        probe = json.loads(run("ffprobe", ["-v", "error", "-show_entries",
                                           "stream=width,height,avg_frame_rate,nb_frames:format=duration",
                                           "-of", "json", media_path(video)]))
        duration = float(probe["format"]["duration"])
        frames = int(probe["streams"][0]["nb_frames"])
        source_fps = float(Fraction(probe["streams"][0]["avg_frame_rate"]))
        if source_fps not in (10, 30):
            raise ValueError("Unexpected source frame rate")
        delivered = output / f"{name}.mp4"
        if key:
            shutil.copy2(video, delivered)
        else:
            run("ffmpeg", ["-v", "error", "-i", media_path(video), "-map", "0:v:0",
                           "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
                           "-vsync", "0", "-an", "-movflags", "+faststart", media_path(delivered)])
            encoded = json.loads(run("ffprobe", ["-v", "error", "-show_entries",
                                                 "stream=avg_frame_rate,nb_frames:format=duration",
                                                 "-of", "json", media_path(delivered)]))
            if (int(encoded["streams"][0]["nb_frames"]) != frames
                    or abs(float(encoded["format"]["duration"]) - duration) > 0.04
                    or encoded["streams"][0]["avg_frame_rate"] != probe["streams"][0]["avg_frame_rate"]):
                raise ValueError("Delivery compression changed frames or timing")
            run("ffmpeg", ["-v", "error", "-i", media_path(delivered), "-f", "null", "-"])
        run("ffmpeg", ["-v", "error", "-i", media_path(video), "-f", "null", "-"])
        gif = output / f"{name}.gif"
        graph = "fps=10,scale=720:-1:flags=lanczos,split[a][b];[a]palettegen=stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=3"
        if not key:
            graph = "fps=10,scale=640:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=96[p];[b][p]paletteuse=dither=none"
        run("ffmpeg", ["-v", "error", "-i", media_path(video), "-filter_complex", graph,
                       "-loop", "0", media_path(gif)])
        qa = [2, round(duration / 2, 2), round(duration - 2, 2)]
        for index, moment in enumerate(qa):
            image = output / f"{name}-qa-{index}.png"
            run("ffmpeg", ["-v", "error", "-ss", str(moment), "-i", media_path(video),
                           "-frames:v", "1", "-vf", "scale=720:-1", media_path(image)])
            with Image.open(image) as frame:
                if max(ImageStat.Stat(frame.convert("RGB")).stddev) < 3:
                    raise ValueError("Blank recording")
        with Image.open(gif) as animated:
            gif_duration = sum(frame.info.get("duration", 0) for frame in ImageSequence.Iterator(animated)) / 1000
            gif_frames = animated.n_frames
        if abs(gif_duration - duration) > 0.11:
            raise ValueError("GIF playback duration differs from the complete recording")
        items.append({"device": "RealSense D435" if sensor == "camera" else "Unitree L2",
                      "algorithm": pair[f"{sensor}_result"]["algorithm"] if key else "four-stream capture",
                      "session": session_name, "hash_bound_at": "original evidence" if key else "publication",
                      "source_sha256": digest(video), "source_frames": frames, "source_fps": source_fps,
                      "duration_seconds": duration, "gif_frames": gif_frames,
                      "gif_duration_seconds": gif_duration, "gif_fps": 10,
                      "trimmed": False, "speed_multiplier": 1, "qa_times_seconds": qa,
                      "transcoded_for_delivery": not bool(key), "delivered_video_sha256": digest(delivered),
                      "full_video_decoded": True, "quality_claim": False})
        print(f"{name}: full {duration:.1f}s, {frames} source frames, GIF {gif_duration:.1f}s", flush=True)
    generator = output / "export_hardware_previews.source.py"
    shutil.copy2(Path(__file__), generator)
    record = {"schema_version": 1, "kind": "hardware_preview", "status": "recorded",
              "generator_sha256": digest(generator),
              "scope": "Basic sensor and odometry display; no accuracy or fusion claim",
              "items": items, "photo": {"source": "User-provided device photograph", "edited": False},
              "artifacts": {path.relative_to(output).as_posix(): {"sha256": digest(path), "availability": "portable"}
                            for path in sorted(output.rglob("*")) if path.is_file()}}
    (output / "record.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
