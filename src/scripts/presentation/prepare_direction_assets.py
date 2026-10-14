"""Render atomic sensor/map fields for the bilingual direction figure."""
import argparse
from pathlib import Path
import hashlib
import json
import subprocess

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "docs/assets/direction"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def path_on_windows(value):
    if value.startswith("/mnt/"):
        return Path(value[5].upper() + ":" + value[6:].replace("/", "\\"))
    return Path(value)


def cloud_field(points, path, *, elevation, azimuth, sensor_scan=False):
    # Dense irregular geometry is a single raster field; all labels/arrows are
    # added as native PowerPoint objects, outside this image.
    points = points[np.isfinite(points).all(axis=1)]
    ids = np.linspace(0, len(points) - 1, min(55000, len(points)), dtype=int)
    points = points[ids]
    fig = plt.figure(figsize=(6, 3.75), dpi=180, facecolor="white")
    axis = fig.add_axes([0, 0, 1, 1], projection="3d")
    colour = {"color": "#28699E"} if sensor_scan else {"c": points[:, 2], "cmap": "viridis"}
    axis.scatter(*points.T, **colour, s=1.2 if sensor_scan else .35,
                 alpha=1, depthshade=False, linewidths=0)
    span = np.ptp(points, axis=0)
    axis.set_box_aspect(np.maximum(span, .1), zoom=1.35)
    axis.view_init(elev=elevation, azim=azimuth)
    axis.set_axis_off()
    fig.savefig(path, facecolor="white")
    plt.close(fig)


def main():
    previous = json.loads((OUT / "sources.json").read_text(encoding="utf-8"))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scan-archive", default=previous["sources"]["scan-3d"]["file"])
    parser.add_argument("--raw-map", default=previous["sources"]["map-3d"]["file"])
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    sources = {}
    scan_path = OUT / "scan-2d.json"
    scan = json.loads(scan_path.read_text())
    ranges = np.array([np.nan if r is None else r for r in scan["ranges"]])
    angle = scan["angle_min"] + np.arange(len(ranges)) * scan["angle_increment"]
    fig = plt.figure(figsize=(6, 4), dpi=180, facecolor="white")
    axis = fig.add_axes([0, 0, 1, 1])
    axis.scatter(ranges*np.cos(angle), ranges*np.sin(angle), s=2, color="#3276BC")
    axis.set_aspect("equal", adjustable="datalim")
    axis.set_axis_off()
    fig.savefig(OUT / "scan-2d.png", facecolor="white")
    plt.close(fig)
    sources["scan-2d"] = {"file": str(scan_path), "sha256": sha(scan_path), "stamp_s": scan["stamp_s"]}

    archive_path = path_on_windows(args.scan_archive)
    with np.load(archive_path) as archive:
        index = min(20, len(archive["stamps"])-1)
        cloud_field(archive[f"scan_{index:04d}"], OUT / "scan-3d.png", elevation=30, azimuth=-115, sensor_scan=True)
        sources["scan-3d"] = {"file": str(archive_path), "sha256": sha(archive_path), "scan_index": index,
                              "stamp_s": float(archive["stamps"][index])}
    map_path = path_on_windows(args.raw_map)
    cloud_field(np.load(map_path), OUT / "map-3d.png", elevation=52, azimuth=-20)
    sources["map-3d"] = {"file": str(map_path), "sha256": sha(map_path),
                         "scope": "controlled mapping A with provided sensor poses; not full 3D SLAM"}

    video = ROOT / "results/reference/robot-corridor-v2-mapping/execution.mp4"
    # Extract one simulator viewport directly from the screen-capture video.
    # The crop excludes window chrome, RViz, Terminal, and performance text.
    subprocess.run(["ffmpeg", "-v", "error", "-ss", "35", "-i", str(video),
                    "-vf", "crop=650:345:240:270", "-frames:v", "1", "-y",
                    str(OUT / "gazebo-corridor.png")], check=True)
    sources["gazebo-corridor"] = {"file": str(video), "sha256": sha(video), "wall_time_s": 35,
                                  "viewport_crop_xywh": [240,270,650,345]}
    for name, filename in [("chassis", "chassis.jpg"), ("sensors", "sensors.png")]:
        photo = ROOT / "docs/assets/robot" / filename
        sources[name] = {"file": str(photo), "sha256": sha(photo),
                         "scope": "user-supplied hardware photograph; physical accuracy tests pending"}
    report = {"kind": "direction_figure_visual_sources", "sources": sources,
              "outputs": {p.name: {"sha256":sha(p),"bytes":p.stat().st_size} for p in OUT.glob("*.png")}}
    (OUT / "sources.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print("Rendered actual sensor, map and simulator fields:", len(sources))


if __name__ == "__main__":
    main()
