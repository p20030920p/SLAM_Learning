#!/usr/bin/env bash
# Record the actual RViz window on record_session.py's private X display.
set -eo pipefail
manifest=$(realpath "$1")
scripts=$(cd "$(dirname "$0")" && pwd)
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID="${ROS_DOMAIN_ID:-71}"
export ROS_LOCALHOST_ONLY=1
export LIBGL_ALWAYS_SOFTWARE=1
export QT_X11_NO_MITSHM=1
export QT_QPA_PLATFORM=xcb
config="$(dirname "$manifest")/review.rviz"
python3 - "$manifest" "$config" <<'PY'
import json, sys
from pathlib import Path
m=json.loads(Path(sys.argv[1]).read_text())
x,y,z=m['focal_point']
semantic=m['method'] in ('conceptgraphs','hovsg')
text=f'''Panels: []
Visualization Manager:
  Class: ""
  Global Options:
    Background Color: 20; 27; 38
    Fixed Frame: map
    Frame Rate: 15
  Displays:
    - Class: rviz_default_plugins/Grid
      Name: Metric grid
      Enabled: true
      Cell Size: {0.5 if semantic else 5}
      Plane Cell Count: 50
      Color: 60; 75; 90
    - Class: rviz_default_plugins/PointCloud2
      Name: Measured output
      Enabled: true
      Topic:
        Value: /study/cloud
        Reliability Policy: Reliable
        Durability Policy: Volatile
        Depth: 1
      Size (Pixels): 3
      Style: Points
      Color Transformer: RGB8
      Position Transformer: XYZ
      Decay Time: 0
    - Class: rviz_default_plugins/Marker
      Name: Evidence label
      Enabled: true
      Marker Topic:
        Value: /study/label
        Reliability Policy: Reliable
        Durability Policy: Volatile
        Depth: 1
  Views:
    Current:
      Class: rviz_default_plugins/Orbit
      Distance: {m['distance']}
      Focal Point:
        X: {x}
        Y: {y}
        Z: {z}
      Pitch: 0.85
      Yaw: 1.4
      Target Frame: map
Window Geometry:
  Width: 1000
  Height: 800
  X: 280
  Y: 0
  Hide Left Dock: true
  Hide Right Dock: true
'''
Path(sys.argv[2]).write_text(text)
PY
echo "MEASURED OUTPUT REVIEW: actual RViz graphical window"
echo "No mapper runs in this recording. Saved output and display thinning only."
rviz2 -d "$config" >"$(dirname "$manifest")/rviz.log" 2>&1 &
viewer_pid=$!
trap 'kill "$viewer_pid" 2>/dev/null || true' EXIT
python3 "$scripts/view_measured_rviz.py" "$manifest" --seconds-per-step 7
sleep 2
kill -0 "$viewer_pid"
