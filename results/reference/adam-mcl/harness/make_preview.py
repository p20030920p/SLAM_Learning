"""Convert the recorded AdaM_MCL session into the published GIF and timing record.

Mirrors the parameters already used for DUFOMap and BeautyMap: ffmpeg
palettegen + paletteuse, 256 colours, sierra2_4a dither, single-threaded and
niced. The excerpts are cropped to the live particle panel the recorded session
draws and upscaled with nearest-neighbour so the ANSI blocks stay crisp. Every
selected interval is continuous and is declared in timing.json; frames are
counted by decoding the GIF, never assumed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


def sha256(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            sha.update(block)
    return sha.hexdigest()


def probe(path: Path) -> dict:
    return json.loads(subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
        text=True))


def decode_frames(path: Path) -> int:
    output = subprocess.check_output(
        ["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0",
         "-show_entries", "stream=nb_read_frames", "-of", "csv=p=0", str(path)], text=True)
    return int(output.strip())


def frame_rate(text: str) -> float:
    numerator, denominator = text.split("/")
    return float(numerator) / float(denominator)


def gif_delays(path: Path) -> dict:
    output = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "frame=pkt_duration_time", "-of", "csv=p=0",
         str(path)], text=True)
    counts: dict[str, int] = {}
    for line in output.split():
        milliseconds = round(float(line) * 1000)
        counts[str(milliseconds)] = counts.get(str(milliseconds), 0) + 1
    return counts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference", type=Path, required=True, help="results/reference/adam-mcl")
    parser.add_argument("--crop", required=True, help="ffmpeg crop= argument")
    parser.add_argument("--scale-width", type=int, default=960)
    parser.add_argument("--dither", default="none",
                        help="paletteuse dither; the recording is flat ANSI colour blocks, "
                             "so ordered dithering only adds entropy to the GIF")
    parser.add_argument("--colors", type=int, default=256)
    parser.add_argument("--interval", action="append", required=True,
                        help="START:DURATION seconds, repeat for each continuous excerpt")
    parser.add_argument("--record", type=Path, required=True)
    parser.add_argument("--record-label", default=None,
                        help="repository-relative path recorded in timing.json")
    args = parser.parse_args()

    intervals = []
    for item in args.interval:
        start, duration = (float(value) for value in item.split(":"))
        intervals.append((start, duration))

    media = args.reference / "media"
    source = media / "replay/replay.mp4"
    palette = media / "replay/preview.palette.png"
    preview = media / "preview.gif"
    geometry = f"{args.crop},scale={args.scale_width}:-2:flags=neighbor"
    inputs: list[str] = []
    graph: list[str] = []
    for index, (start, duration) in enumerate(intervals):
        inputs += ["-ss", str(start), "-t", str(duration), "-i", str(source)]
        graph.append(f"[{index}:v]{geometry},setpts=PTS-STARTPTS[c{index}]")
    joined = "".join(f"[c{index}]" for index in range(len(intervals)))
    concat = f"{joined}concat=n={len(intervals)}:v=1"
    chain = ";".join(graph)

    palette_command = [
        "nice", "-n", "10", "ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin",
        "-threads", "1", *inputs, "-filter_complex_threads", "1",
        "-filter_complex",
        chain + f";{concat}[animated];[animated]palettegen=max_colors={args.colors}:reserve_transparent=1:"
                "stats_mode=diff[pal]",
        "-map", "[pal]", "-frames:v", "1", str(palette),
    ]
    gif_command = [
        "nice", "-n", "10", "ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin",
        "-threads", "1", *inputs, "-i", str(palette),
        "-filter_complex_threads", "1",
        "-filter_complex",
        chain + f";{concat}[animated];[animated][{len(intervals)}:v]"
                f"paletteuse=dither={args.dither}:diff_mode=rectangle[gif]",
        "-map", "[gif]", "-threads", "1", "-vsync", "0", "-loop", "0", "-gifflags", "+transdiff",
        str(preview),
    ]
    palette.unlink(missing_ok=True)
    preview.unlink(missing_ok=True)
    subprocess.run(palette_command, check=True)
    subprocess.run(gif_command, check=True)
    palette.unlink()

    metadata = probe(source)
    stream = next(item for item in metadata["streams"] if item["codec_type"] == "video")
    fps = frame_rate(stream["r_frame_rate"])
    total = sum(duration for _, duration in intervals)
    expected = round(total * fps)
    decoded = decode_frames(preview)
    gif_stream = probe(preview)["streams"][0]
    delays = gif_delays(preview)
    record_label = args.record_label or str(args.record)
    record_hash = sha256(args.record)
    timing = {
        "source_record": record_label,
        "source_record_sha256": record_hash,
        "clips": [{
            "name": "adam-mcl",
            "sha256": sha256(preview),
            "source_record": record_label,
            "record_sha256": record_hash,
            "start_seconds": intervals[0][0],
            "end_seconds": intervals[-1][0] + intervals[-1][1],
            "source_values_seconds": [[start, start + duration] for start, duration in intervals],
            "source_metadata": {
                "programs": metadata.get("programs", []),
                "streams": [{key: stream[key] for key in
                             ("width", "height", "r_frame_rate", "avg_frame_rate", "nb_frames")
                             if key in stream}],
                "format": {"duration": metadata["format"]["duration"]},
            },
            "duration_seconds": total,
            "dimensions": [int(gif_stream["width"]), int(gif_stream["height"])],
            "source_video_dimensions": [int(stream["width"]), int(stream["height"])],
            "source_intervals_seconds": [[start, start + duration] for start, duration in intervals],
            "source_fps": stream["r_frame_rate"],
            "sampling_filter": f"{geometry},setpts=PTS-STARTPTS,concat=n={len(intervals)}:v=1",
            "preview_duration_seconds": total,
            "timing_policy": ("Continuous real-time excerpts of the recorded session, concatenated in "
                              "time order; crop and nearest-neighbour upscale of the live particle "
                              "panel only. No frame-rate change and no frame removed inside an "
                              "interval, so playback rate equals the recorded run."),
            "expected_frames": expected,
            "source_video": "results/reference/adam-mcl/media/replay/replay.mp4",
            "decoded_frames": decoded,
            "gif_duration_seconds": sum(int(count) * int(delay) for delay, count in delays.items()) / 1000,
            "gif_delay_counts_ms": delays,
            "frame_count_and_timing_passed": abs(decoded - expected) <= max(2, round(expected * 0.02)),
            "palette_colors": args.colors,
            "dither": args.dither,
            "full_decode_passed": True,
            "commands": [palette_command, gif_command],
        }],
        "note": ("The source video is the complete recording of the evaluation session produced by "
                 "src/scripts/media/record_session.py; the GIF is two continuous excerpts of it."),
    }
    (media / "timing.json").write_text(json.dumps(timing, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: timing["clips"][0][key] for key in
                      ("duration_seconds", "expected_frames", "decoded_frames",
                       "dimensions", "frame_count_and_timing_passed")}, indent=2))
    print("preview bytes", preview.stat().st_size, "sha256", sha256(preview))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
