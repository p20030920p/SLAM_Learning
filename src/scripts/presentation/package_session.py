"""Pair genuine desktop capture with a clearly labelled measured-pose replay."""
from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from slam_learning.core.provenance import digest
from slam_learning.runtime.presentation_evidence import read_samples, restoration, score, validate_truth
from slam_learning.runtime.runner import verify_record


def windows_path(value):
    if value.startswith("/mnt/"):
        return Path(value[5].upper()+":"+value[6:].replace("/", "\\"))
    return Path(value)


def probe(path):
    result = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "stream=width,height,nb_frames,r_frame_rate", "-show_entries", "format=duration,size", "-of", "json", str(path)], text=True)
    return json.loads(result)


def gif(video, output):
    subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), "-filter_complex",
                    "fps=5,scale=768:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=64:stats_mode=diff[p];[b][p]paletteuse=dither=none:diff_mode=rectangle", "-loop", "0", "-y", str(output)], check=True)
    with Image.open(output) as frames:
        duration = 0
        for i in range(frames.n_frames):
            frames.seek(i)
            duration += frames.info.get("duration", 0)/1000
        count = frames.n_frames
    expected = float(probe(video)["format"]["duration"])
    if abs(duration-expected) > .21:
        raise ValueError("GIF timing differs from source video")
    return {"duration_s": duration, "frames": count, "fps": 5, "video_duration_s": expected,
            "scope": "full interval sampled at 5fps; no speed change; GIF 10ms delay precision"}


def replay(folder, values, restore_stamp, *, output_folder=None, heading_label=None, interval=None):
    names = list(values)
    count = len(names)
    start, finish = interval or (max(array[0, 0] for array in values.values()),
                                 min(array[-1, 0] for array in values.values()))
    if finish-start < 10:
        raise ValueError("Pose replay is too short")
    fig = plt.figure(figsize=(16, 9), dpi=80, facecolor="#111827")
    cols = 1 if count == 1 else 3
    rows = math.ceil(count/cols)
    gs = fig.add_gridspec(rows*2, cols, height_ratios=[3, 1]*rows, left=.04, right=.99, bottom=.06, top=.90, hspace=.50, wspace=.23)
    artists = []
    for idx, name in enumerate(names):
        array = values[name]
        top = fig.add_subplot(gs[(idx//cols)*2, idx%cols])
        bottom = fig.add_subplot(gs[(idx//cols)*2+1, idx%cols])
        for ax in (top, bottom):
            ax.set_facecolor("#192338")
            ax.tick_params(colors="#d7e0ee", labelsize=8)
            for spine in ax.spines.values():
                spine.set_color("#526277")
        map_dir = folder / "maps" / name
        yaml = (map_dir / "map.yaml").read_text()
        import re
        origin = [float(v) for v in re.search(r"origin:\s*\[([^]]+)\]", yaml).group(1).split(",")]
        resolution = float(re.search(r"resolution:\s*([\d.]+)", yaml).group(1))
        image = np.asarray(Image.open(map_dir / "map.pgm"))
        extent = [origin[0], origin[0]+image.shape[1]*resolution, origin[1], origin[1]+image.shape[0]*resolution]
        top.imshow(image, cmap="gray", vmin=0, vmax=255, extent=extent, origin="upper", alpha=.72)
        x = array[:, [1, 4]]
        y = array[:, [2, 5]]
        pad = .65
        top.set_xlim(x.min()-pad, x.max()+pad)
        top.set_ylim(y.min()-pad, y.max()+pad)
        top.set_aspect("equal", adjustable="box")
        top.set_title(name+f" | AMCL | full RMSE {score(array)['position_rmse_m']*100:.2f} cm", color="white", fontsize=13 if count == 1 else 10)
        gt, = top.plot([], [], color="#6ee7b7", lw=2, label="truth")
        est, = top.plot([], [], color="#60a5fa", lw=1.6, label="AMCL")
        dot, = top.plot([], [], "o", color="#60a5fa", ms=5)
        top.legend(fontsize=7, facecolor="#192338", labelcolor="white", loc="best")
        bottom.plot(array[:, 0]-start, array[:, 7]*100, color="#fbbf24", lw=1)
        line = bottom.axvline(0, color="#ef4444", lw=1)
        bottom.set_xlim(0, finish-start)
        bottom.set_ylabel("error cm", color="white", fontsize=8)
        bottom.set_xlabel("simulation seconds", color="white", fontsize=8)
        if restore_stamp is not None:
            bottom.axvline(restore_stamp-start, color="#6ee7b7", ls="--")
        artists.append((array, gt, est, dot, line))
    heading = fig.suptitle("", color="white", fontsize=15)
    fig.text(.04, .95, "MEASURED RESULT REPLAY | saved AMCL updates + independent Gazebo truth | no new inference", color="#b9c5d9", fontsize=10)
    fps = 8
    frames = int(math.floor((finish-start)*fps))+1
    output = (output_folder or folder) / "result.mp4"
    width, height = fig.canvas.get_width_height()
    process = subprocess.Popen(["ffmpeg", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{width}x{height}", "-r", str(fps), "-i", "-", "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-pix_fmt", "yuv420p", "-y", str(output)], stdin=subprocess.PIPE)
    try:
        for idx in range(frames):
            stamp = start+idx/fps
            phase = ""
            if restore_stamp is not None:
                phase = " | LIMITED OBSERVATIONS" if stamp < restore_stamp else " | FULL OBSERVATIONS RESTORED"
            heading.set_text((heading_label or folder.name)+f" | simulation t={stamp-start:.1f}s"+phase)
            for array, gt, est, dot, line in artists:
                end = max(1, int(np.searchsorted(array[:, 0], stamp, side="right")))
                gt.set_data(array[:end, 1], array[:end, 2])
                est.set_data(array[:end, 4], array[:end, 5])
                dot.set_data([array[end-1, 4]], [array[end-1, 5]])
                line.set_xdata([stamp-start, stamp-start])
            fig.canvas.draw()
            process.stdin.write(fig.canvas.buffer_rgba())
    finally:
        process.stdin.close()
        code = process.wait()
        plt.close(fig)
    if code:
        raise RuntimeError("Result replay encoder failed")
    return {"frame_sampling": "latest saved AMCL update at each 8fps simulation timestamp", "common_start_s": start, "common_end_s": finish, "alignment": "none", "frames": frames}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    run, folder = args.run, args.output
    measured = json.loads((run / "metrics.json").read_text())
    if measured["status"] != "completed" or not (run / "execution.mp4").is_file():
        raise ValueError("Completed native recording is required")
    folder.mkdir(parents=True, exist_ok=False)
    for name in ("session.json", "runtime.json", "cases.json", "metrics.json", "truth.jsonl", "execution.mp4", "capture-filter.txt", "scan-stress.jsonl", "geometry-audit.json", "slam-map.pgm"):
        if (run / name).exists():
            shutil.copyfile(run / name, folder / name)
    truth = [json.loads(line) for line in (run / "truth.jsonl").read_text().splitlines()]
    input_hashes = {}
    for path in [run / "mapping-clouds.npz", *sorted((run / "input-bag").glob("*.mcap"))]:
        if path.is_file():
            input_hashes[str(path.resolve())] = {"sha256": digest(path), "bytes": path.stat().st_size, "availability": "local_only"}
    log_dir = folder / "logs"
    log_dir.mkdir()
    for name in ("renderer.txt", "observer.log", "stress.log", "patrol.log", "localizers.log", "rviz.log"):
        if (run / "logs" / name).exists():
            shutil.copyfile(run / "logs" / name, log_dir / name)
    values, case_maps = {}, {}
    cases = json.loads((run / "cases.json").read_text())
    for name in cases:
        source = run / f"{name}-samples.csv"
        values[name] = read_samples(source)
        validate_truth(values[name], truth)
        actual = score(values[name])
        for key, value in actual.items():
            if value is not None and not math.isclose(value, measured["cases"][name][key], abs_tol=1e-10, rel_tol=0):
                raise ValueError(f"{name}: {key} differs")
        shutil.copyfile(source, folder / source.name)
        yaml = windows_path(cases[name]["map_yaml"])
        target = folder / "maps" / name
        target.mkdir(parents=True)
        for part in ("map.yaml", "map.pgm"):
            shutil.copyfile(yaml.parent / part, target / part)
        processing = yaml.parent.parent / "record.json"
        shutil.copyfile(processing, target / "processing.json")
        case_maps[name] = {"yaml_sha256": digest(yaml), "pgm_sha256": digest(yaml.parent / "map.pgm"),
                           "processing_record_sha256": digest(processing), "mapping_run": json.loads(processing.read_text())["source_recording"]}
    restored = None
    events = []
    if (run / "scan-stress.jsonl").exists():
        events = [json.loads(line) for line in (run / "scan-stress.jsonl").read_text().splitlines()]
        restored_events = [event for event in events if event["phase"] == "restored"]
        if restored_events:
            restored = restored_events[0]["stamp_s"]
            if any(array[-1, 0] <= restored+5 for array in values.values()):
                raise ValueError("Restoration stage lacks scored pose updates; retain as a diagnostic")
    timing = {"execution": gif(folder / "execution.mp4", folder / "execution.gif")}
    if values:
        replay_meta = replay(folder, values, restored)
        timing["result"] = gif(folder / "result.mp4", folder / "result.gif")
    else:
        replay_meta = None
    media = ["execution.mp4"]+(["result.mp4"] if values else [])
    for name in media:
        subprocess.run(["ffmpeg", "-v", "error", "-i", str(folder / name), "-f", "null", "-"], check=True)
    duration = float(probe(folder / "execution.mp4")["format"]["duration"])
    for name, stamp in [("first", min(2, duration/4)), ("mid", duration/2), ("last", duration-2)]:
        subprocess.run(["ffmpeg", "-v", "error", "-ss", str(stamp), "-i", str(folder / "execution.mp4"), "-frames:v", "1", "-y", str(folder / f"frame-{name}.png")], check=True)
    (folder / "timing.json").write_text(json.dumps(timing, indent=2)+"\n")
    xyz = np.asarray([item["xyz"] for item in truth])
    record = {"schema_version": 1, "kind": "native_desktop_localization" if values else "native_desktop_mapping",
              "status": "executed", "exit_code": 0, "source_run": str(run.resolve()),
              "command": json.loads((run / "session.json").read_text())["flow"],
              "scope": "Sim2Real same chassis; native 2D slam_toolbox/AMCL; 3D mapping with supplied poses; no 3D SLAM claim",
              "metrics": measured, "truth_input_to_localizers": False, "case_maps": case_maps,
              "recorded_inputs": input_hashes,
              "robot_motion_xy_span_m": np.ptp(xyz[:, :2], axis=0).tolist(),
              "result_replay": replay_meta, "timing": timing,
              "restoration": {name: restoration(array, restored) for name, array in values.items()} if restored is not None else {},
              "artifacts": {path.relative_to(folder).as_posix(): {"sha256": digest(path), "bytes": path.stat().st_size, "availability": "portable"} for path in folder.rglob("*") if path.is_file()}}
    (folder / "record.json").write_text(json.dumps(record, indent=2)+"\n")
    issues = verify_record(folder / "record.json")
    if issues:
        raise ValueError(issues)
    print(json.dumps({"output": str(folder), "motion": record["robot_motion_xy_span_m"], "restoration": record["restoration"]}, indent=2), flush=True)


if __name__ == "__main__":
    main()
