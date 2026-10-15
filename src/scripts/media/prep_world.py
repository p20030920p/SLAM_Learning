#!/usr/bin/env python3
"""Prepare a recording world: inject one overview camera, strip every other camera.

Why the stripping: on this machine (headless, llvmpipe software GL) Gazebo Harmonic
gives exactly one RGB camera sensor a working render target.  Any second
``camera``/``rgbd_camera`` publishes a constant, untextured frame forever
(measured: rgb8 218,218,218, std 0.0) while still reporting a healthy update rate.
Verified by removing the robot camera and watching the overview camera start
rendering, and vice versa.  2D/3D lidar is unaffected.

The overview camera is a ``gz-sim`` model that we *spawn at runtime* - but spawning
it needs a running server, so for reproducibility we also support baking it into a
derived world file.  Baking is what ``--bake`` does.

Also supports adding parameterised "large change" boxes, which is how the S3
scenario is built without touching the arena mesh.
"""

from __future__ import annotations

import argparse
import xml.etree.ElementTree as ET
from pathlib import Path

OVERVIEW = """
  <model name="{name}">
    <static>true</static>
    <pose>{px} {py} {pz} 0 {pitch} 0</pose>
    <link name="link">
      <sensor name="{name}_sensor" type="camera">
        <topic>{topic}</topic>
        <gz_frame_id>{name}</gz_frame_id>
        <update_rate>{rate}</update_rate>
        <always_on>true</always_on>
        <visualize>true</visualize>
        <camera>
          <horizontal_fov>{hfov}</horizontal_fov>
          <image>
            <width>{width}</width>
            <height>{height}</height>
            <format>R8G8B8</format>
          </image>
          <clip>
            <near>0.05</near>
            <far>200</far>
          </clip>
        </camera>
      </sensor>
    </link>
  </model>
"""

# a plain box: used for S3 "the map no longer matches" and for verify-only landmarks
BOX = """
  <model name="{name}">
    <static>true</static>
    <pose>{px} {py} {pz} 0 0 {yaw}</pose>
    <link name="link">
      <visual name="visual">
        <geometry><box><size>{sx} {sy} {sz}</size></box></geometry>
        <material>
          <ambient>{r} {g} {b} 1</ambient>
          <diffuse>{r} {g} {b} 1</diffuse>
        </material>
      </visual>
      <collision name="collision">
        <geometry><box><size>{sx} {sy} {sz}</size></box></geometry>
        <surface><friction><ode><mu>0.8</mu><mu2>0.8</mu2></ode></friction></surface>
      </collision>
    </link>
  </model>
"""


def strip_cameras(world: ET.Element, keep: str) -> list[str]:
    """Remove every camera/rgbd_camera sensor except the one inside model `keep`."""
    removed = []
    for model in world.iter("model"):
        if model.get("name") == keep:
            continue
        for link in model.findall("link"):
            for sensor in list(link.findall("sensor")):
                if sensor.get("type") in ("camera", "rgbd_camera", "depth_camera"):
                    removed.append(f"{model.get('name')}/{link.get('name')}/{sensor.get('name')}")
                    link.remove(sensor)
    return removed


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--name", default="topcam")
    ap.add_argument("--topic", default="/top_view")
    ap.add_argument("--pose", default="3.65 1.0 10.5 0 1.5708 0",
                    help="'x y z roll pitch yaw'")
    ap.add_argument("--rate", type=float, default=10.0)
    ap.add_argument("--hfov", type=float, default=1.92, help="110 deg default")
    ap.add_argument("--width", type=int, default=600)
    ap.add_argument("--height", type=int, default=675)
    ap.add_argument("--no-strip", action="store_true",
                    help="keep every camera (only valid when the world has just one)")
    # extra boxes: name,px,py,pz,sx,sy,sz[,yaw[,r,g,b]]
    ap.add_argument("--box", action="append", default=[],
                    help="name,x,y,z,sx,sy,sz[,yaw[,r,g,b]]")
    args = ap.parse_args()

    src, out = Path(args.src).resolve(), Path(args.out).resolve()
    pose = [float(v) for v in args.pose.split()]
    assert len(pose) == 6, "--pose needs 6 numbers"

    tree = ET.parse(src)
    root = tree.getroot()
    world = root.find("world")
    assert world is not None, f"no <world> in {src}"

    removed = [] if args.no_strip else strip_cameras(world, args.name)

    world.append(ET.fromstring(OVERVIEW.format(
        name=args.name, px=pose[0], py=pose[1], pz=pose[2], pitch=pose[4],
        topic=args.topic, rate=args.rate, hfov=args.hfov,
        width=args.width, height=args.height,
    )))

    added = []
    for spec in args.box:
        parts = [p.strip() for p in spec.split(",")]
        nums = [float(v) for v in parts[1:]]
        yaw = nums[6] if len(nums) > 6 else 0.0
        rgb = nums[7:10] if len(nums) >= 10 else [0.9, 0.15, 0.15]
        world.append(ET.fromstring(BOX.format(
            name=parts[0], px=nums[0], py=nums[1], pz=nums[2],
            sx=nums[3], sy=nums[4], sz=nums[5], yaw=yaw,
            r=rgb[0], g=rgb[1], b=rgb[2],
        )))
        added.append(parts[0])

    out.parent.mkdir(parents=True, exist_ok=True)
    tree.write(out, encoding="utf-8", xml_declaration=True)
    print(f"wrote {out}")
    print(f"  overview {args.name!r} topic={args.topic} pose={pose} "
          f"{args.width}x{args.height} hfov={args.hfov} rate={args.rate}")
    print(f"  stripped cameras: {removed or 'none'}")
    print(f"  added boxes: {added or 'none'}")


if __name__ == "__main__":
    main()
