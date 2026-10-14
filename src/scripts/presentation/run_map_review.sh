#!/usr/bin/env bash
set -eo pipefail
RUN="${1:?review output directory required}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../../.." && pwd)"
export ROS_DOMAIN_ID=199 GALLIUM_DRIVER=d3d12 MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA QT_QPA_PLATFORM=xcb DISPLAY=:0
source /opt/ros/jazzy/setup.bash
glxinfo -B > "$RUN/renderer.txt"
PIDS=()
cleanup() { for pid in "${PIDS[@]}"; do kill -TERM -- "-$pid" 2>/dev/null || true; done; }
trap cleanup EXIT
setsid python3 -u "$HERE/map_review.py" "$REPO/results/reference/robot-3d-map-audit" "$RUN" > >(tee "$RUN/review.log") 2>&1 &
PIDS+=("$!")
while [[ ! -f "$RUN/ready.json" ]]; do sleep .2; done
for method in raw dufomap beautymap; do
  setsid rviz2 -d "$RUN/view-$method.rviz" -t "3D MAP REVIEW $method - RViz2" > "$RUN/rviz-$method.log" 2>&1 &
  PIDS+=("$!")
done
while [[ ! -f "$RUN/STOP" ]]; do sleep .2; done
