#!/usr/bin/env bash
set -eo pipefail
METHOD="${1:?method}"; RUN="${2:?run directory}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../../.." && pwd)"
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=197 DISPLAY=:0 QT_QPA_PLATFORM=xcb GALLIUM_DRIVER=d3d12 MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA
export PRESENTATION_RUN="$RUN"
exec 9>/root/slam-author-live-view.lock
flock -w 15 9 || { echo 'An author live viewer is already active.'; exit 3; }
unset LIBGL_ALWAYS_SOFTWARE QT_QPA_PLATFORM_PLUGIN_PATH
python3 "$HERE/prepare_rviz_overlay.py"
export AMENT_PREFIX_PATH="$REPO/.cache/presentation/rviz-overlay:${AMENT_PREFIX_PATH:-}"
python3 "$HERE/prepare_author_view.py" "$RUN" "$METHOD"
PIDS=()
cleanup(){ for pid in "${PIDS[@]}"; do kill -TERM -- "-$pid" 2>/dev/null || true; done; }
trap cleanup EXIT INT TERM
setsid ros2 run tf2_ros static_transform_publisher --frame-id world --child-frame-id author_map > "$RUN/display-frame.log" 2>&1 &
PIDS+=("$!")
setsid rviz2 -d "$RUN/author-live.rviz" -t "SLAM AUTHOR LIVE - $METHOD" > "$RUN/author-rviz.log" 2>&1 &
PIDS+=("$!")
setsid python3 -u "$HERE/author_live_bridge.py" "$RUN" "$METHOD" > "$RUN/bridge.log" 2>&1 &
PIDS+=("$!")
while [[ ! -f "$RUN/viewer-stop" ]]; do sleep .3; done
