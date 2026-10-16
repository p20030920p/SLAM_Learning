"""Show the frozen A cleaning outputs; explicitly a saved-result visualization."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.spatial import cKDTree

from package_frozen_practice import ROOT, read, sha, windows_path, write
from package_session import gif


def render(scene, maps=None, output=None, source_record=None):
    source = ROOT / "results/reference/practice-frozen-20261016" / ("3d-" + scene)
    if maps is None:
        cases = read(source / "cases.json")
        maps = windows_path(cases["raw"]["map_yaml"]).parent.parent
    if output is None:
        output = ROOT / "results/reference/practice-map-cleaning-review-20261016" / scene
    output.mkdir(parents=True, exist_ok=True)
    raw = np.load(maps / "raw/points.npy", allow_pickle=False)
    sample = raw[np.linspace(0, len(raw)-1, min(8000, len(raw)), dtype=int)]
    lower, upper = raw.min(axis=0), raw.max(axis=0)
    fig = plt.figure(figsize=(16, 6), dpi=80, facecolor="#111827")
    axes, hashes, counts = [], {}, {}
    for index, method in enumerate(("raw", "dufomap", "beautymap"), 1):
        path = maps / method / "points.npy"
        actual = np.load(path, allow_pickle=False)
        # Visual classification queries the saved output; it does not alter the map.
        retained = cKDTree(actual).query(sample)[0] <= 1e-5
        ax = fig.add_subplot(1, 3, index, projection="3d", facecolor="#111827")
        for mask, color, label in [(retained, "#60a5fa", "retained"), (~retained, "#ef4444", "removed")]:
            points = sample[mask]
            ax.scatter(*points.T, s=1, color=color, alpha=.6, label=label, depthshade=False)
        ax.set(xlim=(lower[0], upper[0]), ylim=(lower[1], upper[1]), zlim=(lower[2], upper[2]))
        ax.set_box_aspect(upper-lower, zoom=1.3)
        ax.set_title({"raw":"Raw", "dufomap":"DUFOMap", "beautymap":"BeautyMap"}[method], color="white", fontsize=15)
        ax.set_axis_off()
        ax.legend(loc="lower center", facecolor="#111827", labelcolor="white", markerscale=4)
        axes.append(ax)
        hashes[method] = {"path":str(path), "sha256":sha(path)}
        counts[method] = len(actual)
    fig.suptitle(scene.upper() + " A | SAVED MAP-CLEANING RESULTS", color="white", fontsize=16)
    fig.text(.5,.89,"Saved outputs only; no new inference. Blue: retained; red: removed. Display sample: up to 8,000 raw points.",
             color="#d1d5db",ha="center",fontsize=10)
    fig.subplots_adjust(left=.01,right=.99,bottom=.08,top=.78,wspace=.02)
    video = output / "result.mp4"
    width,height=fig.canvas.get_width_height()
    process=subprocess.Popen(["ffmpeg","-v","error","-f","rawvideo","-pix_fmt","rgba","-s",f"{width}x{height}",
                              "-r","6","-i","-","-an","-c:v","libx264","-preset","veryfast","-crf","20",
                              "-pix_fmt","yuv420p","-y",str(video)],stdin=subprocess.PIPE)
    try:
        for frame in range(48):
            for ax in axes:
                ax.view_init(elev=25,azim=-70+frame*1.5)
            fig.canvas.draw()
            process.stdin.write(fig.canvas.buffer_rgba())
            if frame==24:
                fig.savefig(output / "frame-mid.png",facecolor=fig.get_facecolor())
    finally:
        process.stdin.close()
        status=process.wait()
        plt.close(fig)
    assert status==0
    timing=gif(video,output / "result.gif")
    write(output / "record.json",{"kind":"saved_map_cleaning_result_visualization","status":"rendered",
          "new_inference":False,"source_record":source_record or source.relative_to(ROOT).as_posix()+"/record.json",
          "scope":"Camera orbit over exactly the stored A map outputs. Retention colors use a 1e-5 m membership query on a display-only sample; no new DA/SA score or cleaner execution.",
          "source_maps":hashes,"full_map_points":counts,"display_raw_points":len(sample),"timing":timing,
          "artifacts":{path.name:{"sha256":sha(path),"bytes":path.stat().st_size} for path in output.iterdir() if path.is_file() and path.name!="record.json"}})
    print(json.dumps({"scene":scene,"output":str(output)},ensure_ascii=False),flush=True)


if __name__ == "__main__":
    for scene in ("static","corridor"):
        render(scene)
