#!/usr/bin/env python3
"""Generate the runtime overview camera model and the derived URDF + bridge config.

Why a derived URDF at all
-------------------------
On this machine Gazebo Harmonic gives exactly one RGB camera sensor a working
render target.  Every additional `camera` / `rgbd_camera` publishes a constant
untextured frame for ever (measured: rgb8 218,218,218, std 0.0, 1 distinct colour)
while still reporting a healthy update rate.  Confirmed both directions: dropping
the robot's camera makes the overview camera render, and dropping the overview
camera makes the robot's camera render.  2D and 3D lidar are unaffected.

The overview camera therefore has to be the only RGB camera, so the recording uses
a copy of the robot URDF with the `front_camera` sensor removed and a bridge config
without the image topic.  Nothing else in the URDF is touched.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

TOPCAM = """<?xml version="1.0"?>
<sdf version="1.9">
  <model name="{name}">
    <static>true</static>
    <pose>{pose}</pose>
    <link name="link">
      <sensor name="view" type="camera">
        <topic>{topic}</topic>
        <gz_frame_id>{name}</gz_frame_id>
        <update_rate>{rate}</update_rate>
        <camera>
          <horizontal_fov>{hfov}</horizontal_fov>
          <image><width>{width}</width><height>{height}</height><format>R8G8B8</format></image>
          <clip><near>0.05</near><far>60.0</far></clip>
        </camera>
        <always_on>true</always_on>
        <visualize>true</visualize>
      </sensor>
    </link>
  </model>
</sdf>
"""


def strip_camera_sensor(urdf_text: str) -> tuple[str, int]:
    """Remove the <sensor ...>...</sensor> block whose type is camera/rgbd_camera.

    Works on the raw text so xacro/urdf formatting and comments survive untouched.
    """
    out = []
    i = 0
    removed = 0
    pattern = re.compile(r"<sensor\b[^>]*>", re.S)
    while True:
        m = pattern.search(urdf_text, i)
        if not m:
            out.append(urdf_text[i:])
            break
        tag = m.group(0)
        if 'type="camera"' not in tag and 'type="rgbd_camera"' not in tag:
            out.append(urdf_text[i:m.end()])
            i = m.end()
            continue
        # find the matching </sensor>, allowing one level of nesting
        depth = 1
        j = m.end()
        scan = re.compile(r"</?sensor\b[^>]*>", re.S)
        while depth:
            n = scan.search(urdf_text, j)
            if not n:
                raise SystemExit("unbalanced <sensor> while stripping the camera")
            depth += -1 if n.group(0).startswith("</") else 1
            j = n.end()
        out.append(urdf_text[i:m.start()])
        i = j
        removed += 1
    return "".join(out), removed


def retype_lidar(urdf_text: str, new_type: str) -> tuple[str, list[str]]:
    """Rewrite the `type` attribute of every lidar sensor, in place.

    `gpu_lidar` renders the depth buffer with the GPU.  On this machine that does
    not work: the platform's own S1 evidence recorder reported
    "topic [/scan] does not appear to be published yet" for an entire run, so the
    mapping got no laser data at all.  `ray` does the same raycast on the CPU, needs
    no render target, and leaves the single working render target to the overview
    camera.  The scan geometry is unchanged.
    """
    changed: list[str] = []
    pattern = re.compile(r'<sensor\b[^>]*type="(gpu_lidar|ray|lidar)"[^>]*>', re.S)

    def repl(m: re.Match) -> str:
        tag = m.group(0)
        old = m.group(1)
        name = re.search(r'name="([^"]*)"', tag)
        changed.append(f"{name.group(1) if name else '?'}:{old}->{new_type}")
        return tag.replace(f'type="{old}"', f'type="{new_type}"')

    return pattern.sub(repl, urdf_text), changed


def strip_bridge_entries(text: str, topics: list[str]) -> tuple[str, list[str]]:
    """Drop every YAML list item that mentions one of `topics`."""
    items = re.split(r"(?m)^(?=- )", text)
    kept, dropped = [], []
    for item in items:
        if not item.strip():
            continue
        if any(t in item for t in topics):
            m = re.search(r'(?:ros_topic_name|gz_topic_name):\s*"?([^"\n]+)"?', item)
            dropped.append(m.group(1).strip() if m else item.splitlines()[0])
        else:
            kept.append(item)
    return "".join(kept), dropped


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--urdf", required=True)
    ap.add_argument("--bridge", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--name", default="topcam")
    ap.add_argument("--topic", default="/top_view")
    ap.add_argument("--pose", default="3.65 1.0 10.5 0 1.5708 0")
    ap.add_argument("--rate", type=float, default=10.0)
    ap.add_argument("--hfov", type=float, default=1.92)
    ap.add_argument("--width", type=int, default=600)
    ap.add_argument("--height", type=int, default=675)
    ap.add_argument("--drop-camera-topics", default="/camera/image_raw,/camera/camera_info")
    ap.add_argument("--lidar-type", default="ray",
                    choices=["ray", "gpu_lidar", "keep"],
                    help="rewrite lidar sensor type; 'keep' leaves the URDF alone")
    args = ap.parse_args()

    outdir = Path(args.outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    topcam = outdir / "topcam.sdf"
    topcam.write_text(TOPCAM.format(
        name=args.name, pose=args.pose, topic=args.topic, rate=args.rate,
        hfov=args.hfov, width=args.width, height=args.height,
    ))

    urdf_src = Path(args.urdf).resolve()
    urdf_out = outdir / (urdf_src.stem + "_rec" + urdf_src.suffix)
    text = urdf_src.read_text()
    text, n_cam = strip_camera_sensor(text)
    lidar_changed: list[str] = []
    if args.lidar_type != "keep":
        text, lidar_changed = retype_lidar(text, args.lidar_type)
    urdf_out.write_text(text)

    bridge_src = Path(args.bridge).resolve()
    drops = [t.strip() for t in args.drop_camera_topics.split(",") if t.strip()]
    bridge_out = outdir / (bridge_src.stem + "_nocam" + bridge_src.suffix)
    kept, dropped = strip_bridge_entries(bridge_src.read_text(), drops)
    bridge_out.write_text(kept)

    print(f"topcam  -> {topcam}")
    print(f"  pose={args.pose} topic={args.topic} {args.width}x{args.height} "
          f"hfov={args.hfov} rate={args.rate}")
    print(f"urdf    -> {urdf_out}  (camera sensors removed: {n_cam})")
    print(f"  lidar sensors rewritten: {lidar_changed or 'none'}")
    print(f"bridge  -> {bridge_out}  (entries dropped: {dropped})")
    if n_cam == 0:
        print("  WARNING: no camera sensor found in the URDF; the overview camera "
              "may end up as the second RGB camera and render flat.")


if __name__ == "__main__":
    main()
