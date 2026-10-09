"""Export native-size GIF previews from hash-verified recorded MP4 files."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageStat

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from slam_learning.core.provenance import digest, utc_now, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--author-video", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--wsl", help="Use an existing WSL distro's ffmpeg/ffprobe, without installation")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = args.output.resolve()

    def media_path(path):
        value = Path(path).resolve().as_posix()
        if args.wsl:
            if len(value) < 3 or value[1:3] != ":/":
                raise ValueError("WSL input must be a local Windows drive path")
            return "/mnt/" + value[0].lower() + value[2:]
        return value

    def run(program, options):
        prefix = ["wsl", "-d", args.wsl, "--exec"] if args.wsl else []
        if program == "ffmpeg" and (args.wsl or os.name != "nt"):
            prefix += ["nice", "-n", "10"]
        command = [*prefix, program, *options]
        result = subprocess.run(command, capture_output=True, check=False)
        if result.returncode:
            error = result.stderr.decode("utf-8", errors="replace")
            raise RuntimeError(f"{program} failed ({result.returncode}): {error[-3000:]}")
        return result.stdout, command

    def probe(path):
        data, _ = run("ffprobe", ["-v", "error", "-show_entries",
                                 "stream=width,height,avg_frame_rate:format=duration",
                                 "-of", "json", media_path(path)])
        return json.loads(data)

    def record_source(relative, artifact, video, name, fps, start, end):
        record_path = root / relative
        record = json.loads(record_path.read_text(encoding="utf-8"))
        if record.get("status") != "executed":
            raise ValueError(f"Source record is not completed: {relative}")
        return {"name": name, "video": video, "sha256": record["artifacts"][artifact]["sha256"],
                "source_record": relative, "record_sha256": digest(record_path),
                "fps": fps, "start_seconds": start, "end_seconds": end}

    methods = ("dufomap", "beautymap", "conceptgraphs", "hovsg")
    items = [record_source(f"results/reference/paper-media-{method}/record.json", "replay.mp4",
                           root / f"docs/media/{method}/replay.mp4", method, 1.5, 0, None)
             for method in methods]
    items += [record_source("results/reference/visual-review/record.json", f"{method}/review.mp4",
                            root / f"docs/media/rviz/{method}.mp4", method + "-rviz", 5, 5,
                            64 if method == "conceptgraphs" else 29) for method in methods]
    items.append({"name": "conceptgraphs-author-viewer", "video": args.author_video.resolve(),
                  "sha256": "2eb0bc99c6319ebac785eaccc444a3a8fe9db1701775ab30c2ea6888af3883b3",
                  "source_record": "https://github.com/p20030920p/SLAM_Learning/blob/"
                  "4361d4f353a7449c7d6964887643915d2fc72a11/results/reference/homepage-media/record.json",
                  "source_url": "https://github.com/p20030920p/SLAM_Learning/blob/"
                  "3b0b9a88ac7c77431268b6c869c369e01bd19b3e/evidence/videos/"
                  "conceptgraphs-room0-original-window.mp4",
                  "fps": 5, "start_seconds": 5, "end_seconds": 53})
    for item in items:
        if digest(item["video"]) != item["sha256"]:
            raise ValueError(f"Source video changed: {item['name']}")
        item["source_metadata"] = probe(item["video"])
        stream = item["source_metadata"]["streams"][0]
        duration = float(item["source_metadata"]["format"]["duration"])
        end = duration if item["end_seconds"] is None else item["end_seconds"]
        if not 0 <= item["start_seconds"] < end <= duration:
            raise ValueError(f"Clip outside source: {item['name']}")
        item["duration_seconds"] = end - item["start_seconds"]
        item["dimensions"] = [stream["width"], stream["height"]]
        item["source_intervals_seconds"] = [[item["start_seconds"], end]]
        item["sampling_filter"] = f"fps={item['fps']}"
        if item["name"] == "conceptgraphs-rviz":
            original = json.loads((root / item["source_record"]).read_text(encoding="utf-8"))
            summary = next(part for part in original["summary"] if part["method"] == "conceptgraphs")
            starts = summary["qa_times_s"]
            if len(starts) != summary["steps"] or len(starts) != 9:
                raise ValueError("Expected all nine recorded ConceptGraphs stages")
            item["source_intervals_seconds"] = [[start, start + 3] for start in starts]
            terms = [f"gte(t,{start - item['start_seconds']})*lt(t,{start + 3 - item['start_seconds']})"
                     for start in starts]
            item["sampling_filter"] = "select='" + "+".join(terms) + "',setpts=N/(5*TB),fps=5"
        item["preview_duration_seconds"] = sum(end - start for start, end in item["source_intervals_seconds"])

    output.mkdir(parents=True, exist_ok=False)
    version, _ = run("ffmpeg", ["-version"])
    records = []
    for item in items:
        target = output / (item["name"] + ".gif")
        palette = output / (item["name"] + ".palette.png")
        source_options = ["-hide_banner", "-loglevel", "error", "-nostdin", "-threads", "1",
                          "-ss", str(item["start_seconds"]), "-t", str(item["duration_seconds"]),
                          "-i", media_path(item["video"])]
        _, palette_command = run("ffmpeg", [*source_options, "-filter_threads", "1", "-vf",
                                            f"{item['sampling_filter']},palettegen=max_colors=256:"
                                            "reserve_transparent=1:stats_mode=diff",
                                            "-frames:v", "1", media_path(palette)])
        _, gif_command = run("ffmpeg", [*source_options, "-i", media_path(palette),
                                        "-filter_complex_threads", "1", "-lavfi",
                                        f"{item['sampling_filter']}[a];[a][1:v]paletteuse="
                                        "dither=sierra2_4a:diff_mode=rectangle",
                                        "-threads", "1", "-loop", "0", "-gifflags", "+transdiff",
                                        media_path(target)])
        run("ffmpeg", ["-v", "error", "-threads", "1", "-i", media_path(target),
                       "-f", "null", "-"])
        with Image.open(target) as gif:
            if list(gif.size) != item["dimensions"] or gif.info.get("loop") != 0:
                raise ValueError(f"Incorrect GIF size or loop: {item['name']}")
            frames = gif.n_frames
            elapsed_ms = 0
            for index in range(frames):
                gif.seek(index)
                gif.convert("RGB").load()
                elapsed_ms += gif.info.get("duration", 0)
                if index in (0, frames // 2, frames - 1):
                    if max(ImageStat.Stat(gif.convert("RGB")).stddev) < 3:
                        raise ValueError(f"Blank GIF: {item['name']}")
            if abs(elapsed_ms / 1000 - item["preview_duration_seconds"]) > 0.15:
                raise ValueError(f"Unexpected GIF duration: {item['name']}")
        if target.stat().st_size > 10 * 1024 * 1024:
            raise ValueError(f"Preview exceeds the local 10 MiB budget: {target.name}")
        if digest(item["video"]) != item["sha256"]:
            raise ValueError("Source changed during export")
        public = {key: value for key, value in item.items() if key != "video"}
        public.update(source_video=item["video"].relative_to(root).as_posix()
                      if item["video"].is_relative_to(root) else item["source_url"],
                      decoded_frames=frames, gif_duration_seconds=elapsed_ms / 1000,
                      palette_colors=256, dither="sierra2_4a", full_decode_passed=True,
                      commands=[palette_command, gif_command])
        records.append(public)
        print(f"{target.name}: {item['dimensions']}, {elapsed_ms / 1000:.2f}s, "
              f"{target.stat().st_size / 1024 / 1024:.2f} MiB", flush=True)
        palette.unlink()
    shutil.copy2(__file__, output / "export_media_previews.source.py")
    record = {"schema_version": 1, "kind": "recorded_media_preview_export", "status": "executed",
              "created_at": utc_now(), "exit_code": 0, "generator_sha256": digest(Path(__file__)),
              "ffmpeg": version.decode("utf-8").splitlines()[0], "clips": records,
              "scope": "Existing measured MP4s, native dimensions, palette optimization only. "
              "No new inference, interpolated frames or algorithm-runtime claim.", "artifacts": {}}
    for path in sorted(output.iterdir()):
        record["artifacts"][path.name] = {"sha256": digest(path), "bytes": path.stat().st_size,
                                          "availability": "portable"}
    write_json(output / "record.json", record)
    print(output / "record.json", flush=True)


if __name__ == "__main__":
    main()
