"""Archive real Windows author-code execution and fresh, labelled result replays."""
from __future__ import annotations

import argparse
import json
import os
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
from slam_learning.core.pcd import read_pcd
from slam_learning.core.provenance import digest
from slam_learning.runtime.localization_evidence import trajectory_metrics
from package_session import gif, probe


def render_frames(path, fig, count, fps, update):
    width, height = fig.canvas.get_width_height()
    child = subprocess.Popen(["ffmpeg", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{width}x{height}", "-r", str(fps), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-pix_fmt", "yuv420p", "-y", str(path)], stdin=subprocess.PIPE)
    try:
        for i in range(count):
            update(i)
            fig.canvas.draw()
            child.stdin.write(fig.canvas.buffer_rgba())
    finally:
        child.stdin.close()
        code = child.wait()
        plt.close(fig)
    if code:
        raise RuntimeError("Author result encoder failed")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    run, out = args.run.resolve(), args.output.resolve()
    if os.name == "nt":
        run = Path("\\\\?\\"+str(run))
    native = json.loads((run / "execution.json").read_text())
    if native["status"] != "executed" or native["exit_code"] != 0:
        raise ValueError("Completed fresh inference required")
    subprocess.run(["ffmpeg", "-v", "error", "-i", str(run / "execution.mp4"), "-f", "null", "-"], check=True)
    if (out / "record.json").exists():
        raise ValueError("Completed author package is sealed; choose a fresh output")
    out.mkdir(parents=True, exist_ok=True)
    for name in ("execution.mp4", "execution.json", "native-output.log", "terminal.log"):
        if (run / name).exists():
            shutil.copyfile(run / name, out / name)
    live_state = (run / "live/events.jsonl").is_file()
    if live_state:
        for source, name in ((run / "live/events.jsonl", "live-events.jsonl"), (run / "live-published.jsonl", "live-published.jsonl"),
                             (run / "author-live.rviz", "author-live.rviz"), (run / "capture-filter.txt", "capture-filter.txt"),
                             (run / "instrumentation.patch", "instrumentation.patch"), (run / "author-rviz.log", "author-rviz.log")):
            if source.exists():
                shutil.copyfile(source, out / name)
    method = native["method"]
    inputs, metrics = {}, native.get("metrics", {})
    fig = plt.figure(figsize=(12, 6.75), dpi=80, facecolor="#111827")
    if method in ("dufomap", "beautymap"):
        gt = Path("D:/workspace/be2/SLAM_Learning/.cache/datasets/00/gt_cloud.pcd")
        cleaned = run / "native-run/cleaned.pcd"
        inputs.update({str(gt): digest(gt), str(cleaned): digest(cleaned)})
        for name in ("record.json", "metrics.json", "worker.json", "run.log", "compatibility.patch", "instrumentation.patch"):
            if (run / "native-run" / name).exists():
                (out / "native-run").mkdir(exist_ok=True)
                shutil.copyfile(run / "native-run" / name, out / "native-run" / name)
        clouds = []
        for path in (gt, cleaned):
            data = read_pcd(path)
            ids = np.linspace(0, len(data.records)-1, min(15000, len(data.records)), dtype=int)
            clouds.append(data.xyz(ids))
        axes = []
        for idx, (cloud, label) in enumerate(zip(clouds, ("INPUT (XYZ only in mapper)", "NATIVE RETAINED FINAL MAP"))):
            ax = fig.add_subplot(1, 2, idx+1, projection="3d")
            ax.set_facecolor("#e5e7eb")
            ax.scatter(*cloud.T, s=.7, c=cloud[:, 2], cmap="viridis", rasterized=True)
            ax.set_title(label, color="white", fontsize=10)
            ax.set_box_aspect(np.maximum(np.ptp(cloud, axis=0), 1))
            axes.append(ax)
        fig.suptitle(method+" | saved final point clouds | camera orbit, no online map-growth claim", color="white", fontsize=12)
        fig.text(.05, .03, f"141 scans | thinned display | measured SA={metrics['SA']:.4f}% DA={metrics['DA']:.4f}% | native execution shown separately", color="white", fontsize=9)
        def update(index):
            for ax in axes:
                ax.view_init(elev=55, azim=20+index*1.5)
        count, fps = 120, 6
        scope = "Final measured input/retained point clouds, 15000 display points per panel, camera orbit; no online growth or runtime claim"
    elif method == "ir-mcl":
        estimate = run / "author-code/results/ipblab/loc_test/test1/IRMCL.txt"
        truth = Path("D:/workspace/be2/tmp/repro/ir-mcl/data/ipblab/loc_test/test1/seq_1_gt_pose.txt")
        config = run / "author-code/config/global_localization/loc_config_test1.yml"
        for source, name in ((estimate, "IRMCL.txt"), (truth, "seq_1_gt_pose.txt"), (config, "loc_config.yml")):
            shutil.copyfile(source, out / name)
            inputs[str(source)] = digest(source)
        metrics, samples = trajectory_metrics(estimate, truth, 20, .01)
        est, gt = np.loadtxt(estimate), np.loadtxt(truth)
        gt = gt[gt[:, 0] >= 20]
        ids = np.argmin(abs(est[:, 0, None]-gt[:, 0]), axis=0)
        est = est[ids]
        if len(est) != samples:
            raise ValueError("IR-MCL association count changed")
        ax = fig.add_subplot(211)
        ax.set_facecolor("#192338")
        ax.plot(gt[:, 1], gt[:, 2], color="#6ee7b7", alpha=.4)
        trail, = ax.plot([], [], color="#60a5fa", lw=1.5, label="IR-MCL")
        dot, = ax.plot([], [], "o", color="#60a5fa", ms=4)
        ax.set_aspect("equal", adjustable="box")
        ax.tick_params(colors="white")
        ax.set_title(f"IR-MCL | {samples} scored poses | RMSE {metrics['location_rmse_cm']:.2f} cm", color="white")
        ax.set_xlabel("x metres", color="white")
        ax.set_ylabel("y metres", color="white")
        error = np.linalg.norm(est[:, 1:4]-gt[:, 1:4], axis=1)*100
        bottom = fig.add_subplot(212)
        bottom.plot(gt[:, 0]-gt[0, 0], error, color="#fbbf24")
        cursor = bottom.axvline(0, color="#ef4444")
        bottom.set_xlabel("sequence seconds after scoring starts")
        bottom.set_ylabel("position error cm")
        fig.suptitle("MEASURED RESULT REPLAY | native TUM output | first 20s excluded by upstream scorer | no inference", color="white", fontsize=11)
        start = gt[0, 0]
        fps, count = 8, int((gt[-1, 0]-start)*8)+1
        def update(index):
            stamp = start+index/fps
            last = max(1, int(np.searchsorted(gt[:, 0], stamp, side="right")))
            trail.set_data(est[:last, 1], est[:last, 2])
            dot.set_data([est[last-1, 1]], [est[last-1, 2]])
            cursor.set_xdata([stamp-start]*2)
        scope = "Fresh native estimated trajectory and released truth, same 1354-pose scoring window; saved-output replay at sequence timestamps"
    else:
        trials = sorted((run / "AdaM_MCL/Code/logs4MCL").rglob("error_position.txt"))
        if len(trials) != 1:
            raise ValueError("This demonstration packager requires the explicitly scoped single trial")
        trial = trials[0].parent
        errors = np.loadtxt(trials[0])
        times = np.loadtxt(trial / "time_consumption.txt")
        orientations = np.loadtxt(trial / "error_orientation.txt")
        for name in ("error_position.txt", "error_orientation.txt", "time_consumption.txt"):
            shutil.copyfile(trial / name, out / name)
        metrics = {"position_rmse_cells": float(np.sqrt(np.mean(errors**2))), "updates": len(errors), "trials": 1,
                   "mean_update_seconds": float(np.mean(times)), "unit": "cells, not metres",
                   "final_error_cells": float(errors[-1]), "paper_comparison": False}
        frames = sorted(trial.glob("*_th_iter.png"), key=lambda p: int(p.name.split("_")[0]))
        frame_times = np.r_[0, np.cumsum(times)]
        inputs.update({str(p): digest(p) for p in frames})
        ax = fig.add_subplot(121)
        image = ax.imshow(Image.open(frames[0]))
        ax.set_axis_off()
        ax.set_title("Native particle frame (written before update)", color="white", fontsize=10)
        bottom = fig.add_subplot(122)
        bottom.plot(frame_times[1:], errors, color="#d97706")
        cursor = bottom.axvline(0, color="#dc2626")
        bottom.set_xlabel("measured update time, seconds")
        bottom.set_ylabel("position error, cells")
        title = fig.suptitle("", color="white", fontsize=11)
        fps, count = 8, int(frame_times[-1]*8)+1
        def update(index):
            stamp = index/fps
            idx = min(len(frames)-1, int(np.searchsorted(frame_times, stamp, side="right")-1))
            image.set_data(Image.open(frames[idx]))
            cursor.set_xdata([stamp]*2)
            title.set_text(f"AdaM-MCL SAVED OUTPUT | update {idx+1}/{len(errors)} | one fresh trial | authored 128-cell plan")
        if len(orientations) != len(errors):
            raise ValueError("Native orientation/position logs differ in length")
        scope = "One fresh trial, saved upstream particle images and native errors, replayed using measured update durations; checkpoint/data surrogate disclosed"
    fig.tight_layout(rect=[0, .06, 1, .90])
    render_frames(out / "result.mp4", fig, count, fps, update)
    timing = {"execution": gif(out / "execution.mp4", out / "execution.gif"), "result": gif(out / "result.mp4", out / "result.gif")}
    (out / "metrics.json").write_text(json.dumps(metrics, indent=2)+"\n")
    (out / "timing.json").write_text(json.dumps(timing, indent=2)+"\n")
    duration = float(probe(out / "execution.mp4")["format"]["duration"])
    for name, stamp in (("first", 2), ("mid", duration/2), ("last", max(0, duration-2))):
        subprocess.run(["ffmpeg", "-v", "error", "-ss", str(stamp), "-i", str(out / "execution.mp4"), "-frames:v", "1", "-y", str(out / f"frame-{name}.png")], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-i", str(out / "result.mp4"), "-f", "null", "-"], check=True)
    record = {"schema_version": 1, "kind": "author_desktop_demo", "method": method, "status": "executed", "exit_code": 0,
              "command": native["command"], "scope": native["scope"], "result_scope": scope, "metrics": metrics,
              "inputs_sha256": inputs, "source_run": str(run.resolve()), "timing": timing,
              "live_state": {"enabled": live_state, "scope": "RViz shows newly emitted native execution states; display thinning and observer overhead disclosed"} if live_state else None,
              "artifacts": {p.relative_to(out).as_posix(): {"sha256": digest(p), "bytes": p.stat().st_size, "availability": "portable"} for p in out.rglob("*") if p.is_file()}}
    (out / "record.json").write_text(json.dumps(record, indent=2)+"\n")
    print(json.dumps({"output": str(out), "metrics": metrics}, indent=2), flush=True)


if __name__ == "__main__":
    main()
