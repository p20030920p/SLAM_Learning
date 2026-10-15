#!/usr/bin/env python3
"""Write the RViz2 config used for the right half of the split screen.

Right half shows the online map slam_toolbox is building, the live laser scan, the
robot, and the driven trajectory.  Frame is `map`; slam_toolbox publishes
map -> odom and the drive controller publishes odom -> base_footprint.
"""

from __future__ import annotations

import argparse
from pathlib import Path

TEMPLATE = """\
Panels:
  - Class: rviz_common/Displays
    Name: Displays
    Property Tree Widget:
      Expanded: ~
    Tree Height: 300
Visualization Manager:
  Class: ""
  Displays:
    - Class: rviz_default_plugins/Grid
      Name: Arena grid (1 m)
      Enabled: true
      Cell Size: 1
      Plane Cell Count: 60
      Color: 60; 70; 82
      Alpha: 0.35
    - Class: rviz_default_plugins/Map
      Name: slam_toolbox map (live)
      Enabled: true
      Topic:
        Value: /map
        Reliability Policy: Reliable
        Durability Policy: Transient Local
        Depth: 5
      Alpha: 0.85
      Color Scheme: map
      Draw Behind: true
      Update Topic:
        Value: /map_updates
    - Class: rviz_default_plugins/LaserScan
      Name: Laser scan
      Enabled: true
      Topic:
        Value: /scan
        Reliability Policy: Best Effort
        Durability Policy: Volatile
        Depth: 10
      Style: Points
      Size (Pixels): 4
      Color: 255; 60; 60
      Color Transformer: FlatColor
      Decay Time: 0
      Position Transformer: XYZ
    - Class: rviz_default_plugins/MarkerArray
      Name: Moving boxes
      Enabled: true
      Topic:
        Value: /live/markers
        Reliability Policy: Reliable
        Durability Policy: Volatile
        Depth: 5
    - Class: rviz_default_plugins/Marker
      Name: Driven trajectory
      Enabled: true
      Topic:
        Value: /live/trajectory
        Reliability Policy: Reliable
        Durability Policy: Volatile
        Depth: 5
    - Class: rviz_default_plugins/Odometry
      Name: Wheel odometry
      Enabled: true
      Topic:
        Value: /odom
        Reliability Policy: Best Effort
        Durability Policy: Volatile
        Depth: 10
      Keep: 1
      Position Tolerance: 0.05
      Angle Tolerance: 0.1
      Shape:
        Value: Arrow
        Shaft Length: 0.5
        Shaft Radius: 0.06
        Head Length: 0.2
        Head Radius: 0.12
      Color: 30; 190; 90
      Covariance:
        Value: false
    - Class: rviz_default_plugins/TF
      Name: TF frames
      Enabled: true
      Show Names: false
      Show Axes: true
      Show Arrows: false
      Marker Scale: 0.6
      Update Interval: 0
  Global Options:
    Background Color: 18; 22; 28
    Fixed Frame: map
    Frame Rate: 15
  Tools: []
  Views:
    Current:
      Class: rviz_default_plugins/TopDownOrtho
      Name: Current View
      Target Frame: map
      Angle: 0
      Scale: {scale}
      X: {cx}
      Y: {cy}
Window Geometry:
  Height: 1080
  Width: 960
  X: 0
  Y: 0
  Hide Left Dock: true
  Hide Right Dock: true
  Displays:
    collapsed: false
"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--center", default="3.65,1.0", help="view centre x,y in map frame")
    ap.add_argument("--scale", type=float, default=52.0,
                    help="TopDownOrtho pixels per metre")
    args = ap.parse_args()
    cx, cy = (float(v) for v in args.center.split(","))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(TEMPLATE.format(cx=cx, cy=cy, scale=args.scale))
    print(f"wrote {out} centre=({cx},{cy}) scale={args.scale}px/m")


if __name__ == "__main__":
    main()
