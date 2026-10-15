#!/usr/bin/env bash
# Real desktop Gazebo/RViz session. No Xvfb or substitute map viewer.
set -eo pipefail
FLOW="${1:?usage: run_live.sh FLOW RUN_DIR DURATION AUTO}"
RUN_DIR="${2:?fresh output directory required}"
DURATION="${3:-90}"
AUTO="${4:-false}"
export PRESENTATION_MULTI_VIEW="${5:-false}"
export PRESENTATION_COMPARE_METHODS="${6:-raw,dufomap,beautymap}"
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
if [[ "$FLOW" == *-ndt-* || "$FLOW" == *-gicp-* || "$FLOW" == *-3d-* ]]; then
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
if [[ "$FLOW" == *-srrg-* ]]; then SLAM=false; fi
if [[ "$FLOW" == localization-* ]]; then MODE=localization; SLAM=false; fi
URDF="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("urdf",sys.argv[2]))' "$RUN_DIR/runtime.json" "$REPO/config/robot_profiles/omni-3d-v1/omni_car_lidar3d.urdf")"
BRIDGE="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("bridge_config",sys.argv[2]))' "$RUN_DIR/runtime.json" "$REPO/config/robot_profiles/omni-3d-v1/bridge_sensors.yaml")"
PIDS=()
cleanup() {
  local status=$?
  trap - EXIT INT TERM
  for pid in "${PIDS[@]:-}"; do kill -TERM -- "-$pid" 2>/dev/null || true; done
  python3 "$HERE/stop_owned_session.py" --run "$RUN_DIR" || true
  printf '{"state":"STOPPED","exit_code":%s}\n' "$status" > "$RUN_DIR/session-stopped.json"
  if [[ "$status" -ne 0 ]]; then printf '{"state":"FAILED","exit_code":%s}\n' "$status" > "$RUN_DIR/failed.json"; fi
  exit "$status"
}
trap cleanup EXIT INT TERM
echo "EXECUTING: ros2 launch scenario_gpu.launch.py $LEVEL; profile=omni-3d-v1; mode=$MODE"
setsid ros2 launch "$HERE/scenario_gpu.launch.py" \
  "world:=$WORLD" "spawn_x:=$SPAWN_X" "spawn_y:=$SPAWN_Y" "spawn_yaw:=$SPAWN_YAW" \
  "urdf:=$URDF" "bridge_config:=$BRIDGE" \
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
if [[ "$FLOW" == *-srrg-* ]]; then
  setsid python3 -u "$HERE/srrg/live.py" "$RUN_DIR" > "$RUN_DIR/logs/srrg-transport.log" 2>&1 &
  SRRG_PID=$!
  PIDS+=("$!")
  timeout 40 ros2 topic echo /scan sensor_msgs/msg/LaserScan --once --field header > "$RUN_DIR/logs/sensor-preflight.log" 2>&1
fi
if [[ "$MODE" == mapping && "$FLOW" == *-probe-* ]]; then
  setsid python3 -u "$HERE/collect_probe_mapping.py" "$RUN_DIR" "$NATIVE_TRUTH" > "$RUN_DIR/logs/probe-mapping.log" 2>&1 &
  PROBE_MAPPING_PID=$!
  PIDS+=("$!")
fi
if [[ "$MODE" == mapping && "$FLOW" == *dynamic* ]]; then
  setsid "$REPO/.cache/presentation/truth-build/gz_truth" \
    /world/competition_world/dynamic_pose/info '*' "$RUN_DIR/object-truth.jsonl" &
  PIDS+=("$!")
  setsid bash -c '
    while [[ ! -f "$PRESENTATION_RUN/ready.json" ]]; do sleep .2; done
    gz service -s /world/competition_world/scene/info --reqtype gz.msgs.Empty \
      --reptype gz.msgs.Scene --timeout 3000 --req "" > "$PRESENTATION_RUN/object-scene.pbtxt"
    python3 "$PRESENTATION_REPO/src/scripts/presentation/object_scene.py" "$PRESENTATION_RUN"
  ' > "$RUN_DIR/logs/object-scene.log" 2>&1 &
  PIDS+=("$!")
fi
if [[ "$MODE" == localization ]]; then
  if [[ "$FLOW" == *degradation || "$FLOW" == *height-corridor ]]; then
    setsid python3 -u "$HERE/stress_scan.py" "$RUN_DIR" > "$RUN_DIR/logs/stress.log" 2>&1 &
    PIDS+=("$!")
  fi
  LOCALIZER_LAUNCH=localization.launch.py
  if [[ "$FLOW" == *-ndt-* || "$FLOW" == *-gicp-* || "$FLOW" == *-3d-* ]]; then LOCALIZER_LAUNCH=registration.launch.py; fi
  LOCALIZER_CASES="$RUN_DIR/cases.json"
  if [[ "$FLOW" == *-probe-* ]]; then
    LOCALIZER_CASES="$RUN_DIR/native-cases.json"
    setsid python3 -u "$HERE/probe_localizer.py" "$RUN_DIR" > "$RUN_DIR/logs/probes.log" 2>&1 &
    PROBE_LOCALIZER_PID=$!
    PIDS+=("$!")
  fi
  setsid ros2 launch "$HERE/$LOCALIZER_LAUNCH" "cases_file:=$LOCALIZER_CASES" \
    > "$RUN_DIR/logs/localizers.log" 2>&1 &
  PIDS+=("$!")
fi
if [[ "$FLOW" == *-probe-* ]]; then
  # Avoid concurrent initial D3D12 context creation by Gazebo and RViz on WSLg.
  timeout 40 ros2 topic echo /scan sensor_msgs/msg/LaserScan --once --field header > "$RUN_DIR/logs/sensor-preflight.log" 2>&1
  if [[ "$MODE" == localization ]]; then
    for ((probe_wait=0; probe_wait<200; probe_wait++)); do
      [[ -f "$RUN_DIR/probes-ready.json" ]] && break
      kill -0 "$PROBE_LOCALIZER_PID" 2>/dev/null || { echo 'Probe process failed; see logs/probes.log'; exit 7; }
      sleep .1
    done
    [[ -f "$RUN_DIR/probes-ready.json" ]] || { echo 'Probe initialization timed out'; exit 7; }
  fi
fi
if [[ "$FLOW" == mapping-compare-* ]]; then
  timeout 40 ros2 topic echo /scan sensor_msgs/msg/LaserScan --once --field header > "$RUN_DIR/logs/sensor-preflight.log" 2>&1
  setsid python3 -u "$HERE/mapping_compare.py" "$RUN_DIR" "$NATIVE_TRUTH" > "$RUN_DIR/logs/compare-viewer.log" 2>&1 &
  COMPARE_PID=$!
  PIDS+=("$!")
  for ((compare_wait=0; compare_wait<100; compare_wait++)); do
    [[ -f "$RUN_DIR/compare-configs.json" ]] && break
    kill -0 "$COMPARE_PID" 2>/dev/null || { echo 'Comparison viewer failed'; exit 9; }
    sleep .1
  done
  [[ -f "$RUN_DIR/compare-configs.json" ]] || { echo 'Comparison view initialization timed out'; exit 9; }
  for method in ${PRESENTATION_COMPARE_METHODS//,/ }; do
    setsid rviz2 -d "$RUN_DIR/compare-$method.rviz" -t "MAP BATCH - $method - $FLOW" --ros-args -p use_sim_time:=true > "$RUN_DIR/logs/rviz-$method.log" 2>&1 &
    PIDS+=("$!")
    sleep 1
  done
elif [[ "$PRESENTATION_MULTI_VIEW" == true && "$MODE" == localization ]]; then
  setsid python3 -u "$HERE/case_view_tf.py" "$RUN_DIR" > "$RUN_DIR/logs/views.log" 2>&1 &
  PIDS+=("$!")
  for name in $(python3 -c 'import json,sys; print(" ".join(json.load(open(sys.argv[1]))))' "$RUN_DIR/views.json"); do
    VIEW_TITLE="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))[sys.argv[2]]["title"])' "$RUN_DIR/views.json" "$name")"
    setsid rviz2 -d "$RUN_DIR/view-$name.rviz" -t "$VIEW_TITLE" --ros-args -p use_sim_time:=true \
      -r "/tf:=/$name/view/tf" -r "/tf_static:=/$name/view/tf_static" > "$RUN_DIR/logs/rviz-$name.log" 2>&1 &
    PIDS+=("$!")
  done
else
  setsid rviz2 -d "$RUN_DIR/live.rviz" -t "SLAM LIVE - RViz2 - $FLOW" --ros-args -p use_sim_time:=true \
    > "$RUN_DIR/logs/rviz.log" 2>&1 &
  PIDS+=("$!")
fi
# Record the actual ROS inputs, independent of the visual screen capture.
if [[ "$FLOW" == localization-probe-* || "$FLOW" == *-srrg-* ]]; then
  setsid python3 -u "$HERE/window_capture_heartbeat.py" "$RUN_DIR" > "$RUN_DIR/logs/window-capture.log" 2>&1 &
  PIDS+=("$!")
fi
setsid ros2 bag record -o "$RUN_DIR/input-bag" /clock /scan /points /tf /tf_static \
  /omni_drive_controller/odom /map /scan_degraded /depth/points /depth/image > "$RUN_DIR/logs/bag.log" 2>&1 &
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
if [[ -n "${PROBE_MAPPING_PID:-}" ]]; then
  for ((probe_wait=0; probe_wait<100; probe_wait++)); do
    [[ -f "$RUN_DIR/probe-mapping-inputs.npz" ]] && break
    sleep .1
  done
fi
if [[ -n "${PROBE_LOCALIZER_PID:-}" ]]; then
  for ((probe_wait=0; probe_wait<200; probe_wait++)); do
    [[ -f "$RUN_DIR/probe-B-inputs.json" ]] && break
    sleep .1
  done
fi
if [[ -n "${SRRG_PID:-}" ]]; then
  for ((srrg_wait=0; srrg_wait<200; srrg_wait++)); do
    [[ -f "$RUN_DIR/srrg-finished.json" ]] && break
    kill -0 "$SRRG_PID" 2>/dev/null || break
    sleep .1
  done
  [[ -f "$RUN_DIR/srrg-finished.json" ]] || { echo 'Native SRRG did not finalize; see author/transport logs'; exit 8; }
fi
# Keep native windows alive until all Windows capture encoders flush their MP4s.
# Destroying a WGC source first can leave an encoder waiting for a final frame.
if [[ -f "$RUN_DIR/recording.capture" ]]; then
  for ((flush_wait=0; flush_wait<350; flush_wait++)); do
    [[ -f "$RUN_DIR/recording.stopped" ]] && break
    # WGC is event driven: a frozen terminal can block a multi-source framesync
    # request before ffmpeg gets to read its quit command. Keep this real status
    # window repainting while encoders finish, without changing simulation data.
    if ((flush_wait % 2 == 0)); then printf '\rFINALIZING NATIVE RECORDING %s ' "$flush_wait"; fi
    sleep 0.1
  done
fi
kill -TERM -- "-$TRUTH_PID" 2>/dev/null || true
sleep 0.5
cp "$NATIVE_TRUTH" "$RUN_DIR/truth.jsonl"
echo "FINISHED: $RUN_DIR"
