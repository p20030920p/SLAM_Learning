#!/usr/bin/env bash
# Real desktop Gazebo/RViz session. No Xvfb or substitute map viewer.
set -eo pipefail
FLOW="${1:?usage: run_live.sh FLOW RUN_DIR DURATION AUTO}"
RUN_DIR="${2:?fresh output directory required}"
DURATION="${3:-90}"
AUTO="${4:-false}"
export PRESENTATION_MULTI_VIEW="${5:-false}"
mkdir -p "$RUN_DIR/logs"
startup_failure() {
  local status=$?
  if [[ "$status" -ne 0 ]]; then printf '{"state":"FAILED","exit_code":%s}\n' "$status" > "$RUN_DIR/failed.json"; fi
}
trap startup_failure EXIT
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../../.." && pwd)"
export S2R_REPO="${S2R_REPO:-/root/projects/Sim2Real-AlgoBench}"
source /opt/ros/jazzy/setup.bash
source "$S2R_REPO/install/setup.bash"
if [[ "$FLOW" == *-ndt-* || "$FLOW" == *-gicp-* ]]; then
  source /root/slam-alternative-ws/build_ws/install/setup.bash
fi
exec 9>/root/slam-presentation.lock
flock -w 15 9 || { echo 'A presentation is active. Finish it with q before starting another.'; exit 3; }
export ROS_DOMAIN_ID="${SLAM_ROS_DOMAIN_ID:-198}"
export GZ_PARTITION="slam_presentation_$(basename "$RUN_DIR")"
export GALLIUM_DRIVER=d3d12 MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA
export QT_QPA_PLATFORM=xcb DISPLAY=:0
unset LIBGL_ALWAYS_SOFTWARE MESA_GL_VERSION_OVERRIDE QT_QPA_PLATFORM_PLUGIN_PATH
mkdir -p "$RUN_DIR/logs" "$REPO/.cache/presentation"
export PRESENTATION_RUN="$RUN_DIR" PRESENTATION_FLOW="$FLOW" PRESENTATION_REPO="$REPO"
glxinfo -B > "$RUN_DIR/logs/renderer.txt"
grep -q 'D3D12.*NVIDIA' "$RUN_DIR/logs/renderer.txt" || {
  echo 'GPU renderer not verified; refusing to record a black or substitute scene.'; exit 4;
}
cmake -S "$HERE" -B "$REPO/.cache/presentation/truth-build" > "$RUN_DIR/logs/cmake.log" 2>&1
cmake --build "$REPO/.cache/presentation/truth-build" -j2 >> "$RUN_DIR/logs/cmake.log" 2>&1
python3 "$HERE/prepare_rviz_overlay.py"
export AMENT_PREFIX_PATH="$REPO/.cache/presentation/rviz-overlay:${AMENT_PREFIX_PATH:-}"
python3 "$HERE/prepare_session.py"
export PRESENTATION_GUI_CONFIG="$RUN_DIR/gazebo-gui.config"
LEVEL=S1_static
OBSTACLES=false
if [[ "$FLOW" == *dynamic* ]]; then LEVEL=S2_dynamic; OBSTACLES=true; fi
WORLD="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["world"])' "$RUN_DIR/runtime.json")"
SPAWN_X="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["spawn"][0])' "$RUN_DIR/runtime.json")"
SPAWN_Y="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["spawn"][1])' "$RUN_DIR/runtime.json")"
SPAWN_YAW="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["spawn"][2])' "$RUN_DIR/runtime.json")"
MODE=mapping
SLAM=true
if [[ "$FLOW" == localization-* ]]; then MODE=localization; SLAM=false; fi
PIDS=()
cleanup() {
  local status=$?
  trap - EXIT INT TERM
  for pid in "${PIDS[@]:-}"; do kill -TERM -- "-$pid" 2>/dev/null || true; done
  python3 "$HERE/stop_owned_session.py" --run "$RUN_DIR" || true
  if [[ "$status" -ne 0 ]]; then printf '{"state":"FAILED","exit_code":%s}\n' "$status" > "$RUN_DIR/failed.json"; fi
  exit "$status"
}
trap cleanup EXIT INT TERM
echo "EXECUTING: ros2 launch scenario_gpu.launch.py $LEVEL; profile=omni-3d-v1; mode=$MODE"
setsid ros2 launch "$HERE/scenario_gpu.launch.py" \
  "world:=$WORLD" "spawn_x:=$SPAWN_X" "spawn_y:=$SPAWN_Y" "spawn_yaw:=$SPAWN_YAW" \
  "urdf:=$REPO/config/robot_profiles/omni-3d-v1/omni_car_lidar3d.urdf" \
  "bridge_config:=$REPO/config/robot_profiles/omni-3d-v1/bridge_sensors.yaml" \
  headless:=false "slam:=$SLAM" patrol:=false "obstacles:=$OBSTACLES" truth:=false \
  > "$RUN_DIR/logs/stack.log" 2>&1 &
PIDS+=("$!")
mkdir -p /root/slam-presentation-truth
NATIVE_TRUTH="/root/slam-presentation-truth/$(basename "$RUN_DIR").jsonl"
touch "$NATIVE_TRUTH"
setsid "$REPO/.cache/presentation/truth-build/gz_truth" \
  /world/competition_world/dynamic_pose/info omni_car "$NATIVE_TRUTH" &
TRUTH_PID=$!
PIDS+=("$!")
if [[ "$MODE" == localization ]]; then
  if [[ "$FLOW" == localization-degradation ]]; then
    setsid python3 -u "$HERE/stress_scan.py" "$RUN_DIR" > "$RUN_DIR/logs/stress.log" 2>&1 &
    PIDS+=("$!")
  fi
  LOCALIZER_LAUNCH=localization.launch.py
  if [[ "$FLOW" == *-ndt-* || "$FLOW" == *-gicp-* ]]; then LOCALIZER_LAUNCH=registration.launch.py; fi
  setsid ros2 launch "$HERE/$LOCALIZER_LAUNCH" "cases_file:=$RUN_DIR/cases.json" \
    > "$RUN_DIR/logs/localizers.log" 2>&1 &
  PIDS+=("$!")
fi
if [[ "$PRESENTATION_MULTI_VIEW" == true && "$MODE" == localization ]]; then
  setsid python3 -u "$HERE/case_view_tf.py" "$RUN_DIR" > "$RUN_DIR/logs/views.log" 2>&1 &
  PIDS+=("$!")
  for name in $(python3 -c 'import json,sys; print(" ".join(json.load(open(sys.argv[1]))))' "$RUN_DIR/views.json"); do
    setsid rviz2 -d "$RUN_DIR/view-$name.rviz" -t "SLAM LIVE - $name - RViz2" --ros-args -p use_sim_time:=true \
      -r "/tf:=/$name/view/tf" -r "/tf_static:=/$name/view/tf_static" > "$RUN_DIR/logs/rviz-$name.log" 2>&1 &
    PIDS+=("$!")
  done
else
  setsid rviz2 -d "$RUN_DIR/live.rviz" -t "SLAM LIVE - RViz2 - $FLOW" --ros-args -p use_sim_time:=true \
    > "$RUN_DIR/logs/rviz.log" 2>&1 &
  PIDS+=("$!")
fi
# Record the actual ROS inputs, independent of the visual screen capture.
setsid ros2 bag record -o "$RUN_DIR/input-bag" /clock /scan /points /tf /tf_static \
  /omni_drive_controller/odom /map /scan_degraded > "$RUN_DIR/logs/bag.log" 2>&1 &
PIDS+=("$!")
if [[ "$AUTO" == true ]]; then
  setsid bash "$HERE/auto_patrol.sh" "$RUN_DIR" > "$RUN_DIR/logs/patrol.log" 2>&1 &
  PIDS+=("$!")
fi
CASE_NAMES="$(python3 -c 'import json,sys; print(",".join(json.load(open(sys.argv[1]))))' "$RUN_DIR/cases.json")"
OPTIONS=()
if [[ "$AUTO" == true ]]; then OPTIONS+=(--auto); fi
python3 -u "$HERE/observe_session.py" --run "$RUN_DIR" --truth "$NATIVE_TRUTH" --mode "$MODE" \
  --duration "$DURATION" --cases "$CASE_NAMES" "${OPTIONS[@]}" | tee "$RUN_DIR/logs/observer.log"
kill -TERM -- "-$TRUTH_PID" 2>/dev/null || true
sleep 0.5
cp "$NATIVE_TRUTH" "$RUN_DIR/truth.jsonl"
echo "FINISHED: $RUN_DIR"
