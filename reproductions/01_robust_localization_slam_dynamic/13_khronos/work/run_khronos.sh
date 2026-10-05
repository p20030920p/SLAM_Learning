#!/usr/bin/env bash
# 01-13 · run the official Khronos pipeline headless, then ask it to save.
#
# Upstream's instructions assume a desktop: `ros2 launch khronos_ros
# uhumans2_khronos.launch.yaml`, watch RViz, and when the bag ends call
# `/khronos_node/experiment/finish_mapping_and_save` by hand. This script is that
# sequence without the desktop:
#
#   1. source ROS 2 Jazzy + the workspace install;
#   2. launch with the bag path, dataset and output dir we want, and
#      `start_visualizer:=false` (see work/local_patches.patch - upstream gates
#      both the visualiser node and rviz on that flag but never forwarded it, so
#      it could not be turned off from the command line);
#   3. wait for the bag player to exit (that is when the experiment has consumed
#      all input), then call the finish service, which is what makes the map and
#      the evaluation files get written;
#   4. wait for `final.4dmap`, then stop the launch.
#
# Usage:
#   bash work/run_khronos.sh <bag_dir> <output_dir> <dataset_name> [timeout_minutes]

set -uo pipefail

BAG_DIR=${1:?usage: run_khronos.sh <bag_dir> <output_dir> <dataset> [timeout_min]}
OUT_DIR=${2:?usage: run_khronos.sh <bag_dir> <output_dir> <dataset> [timeout_min]}
DATASET=${3:?usage: run_khronos.sh <bag_dir> <output_dir> <dataset> [timeout_min]}
TIMEOUT_MIN=${4:-90}

HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPRO=$(cd "$HERE/.." && pwd)
WS=${KHRONOS_WS:-$REPRO/code}
mkdir -p "$OUT_DIR" "$HERE/logs"

# ROS 2 setup scripts are not `set -u` clean
set +u
source /opt/ros/jazzy/setup.bash
source "$WS/install/setup.bash"
set -u

LOG=$HERE/logs/khronos_${DATASET}.log
: > "$LOG"

echo "[khronos] bag     : $BAG_DIR"
echo "[khronos] output  : $OUT_DIR"
echo "[khronos] log     : $LOG"

ros2 launch khronos_ros uhumans2_khronos.launch.yaml \
  dataset:="$DATASET" \
  bag_path:="$BAG_DIR" \
  output_dir:="$OUT_DIR" \
  start_visualizer:=false \
  evaluate:=true \
  use_gt_semantics:=true \
  > "$LOG" 2>&1 &
LAUNCH_PID=$!

cleanup() {
  set +e
  kill -INT $LAUNCH_PID 2>/dev/null
  sleep 5
  kill -TERM $LAUNCH_PID 2>/dev/null
  pkill -f "ros2 launch khronos_ros" 2>/dev/null
}
trap cleanup EXIT

# --- 1. wait for the player to appear, then to disappear ---------------------
echo "[khronos] waiting for the bag player"
for _ in $(seq 1 120); do
  ros2 node list 2>/dev/null | grep -q "play" && break
  kill -0 $LAUNCH_PID 2>/dev/null || { echo "[khronos] launch died early"; tail -40 "$LOG"; exit 1; }
  sleep 5
done

deadline=$(( $(date +%s) + TIMEOUT_MIN * 60 ))
while ros2 node list 2>/dev/null | grep -q "play"; do
  [[ $(date +%s) -gt $deadline ]] && { echo "[khronos] playback timed out"; break; }
  kill -0 $LAUNCH_PID 2>/dev/null || { echo "[khronos] launch died during playback"; tail -40 "$LOG"; exit 1; }
  sleep 10
done
echo "[khronos] playback finished; letting the pipeline drain"
sleep 30

# --- 2. ask the experiment to finish and save --------------------------------
echo "[khronos] calling finish_mapping_and_save"
ros2 service call /khronos_node/experiment/finish_mapping_and_save std_srvs/srv/Empty || true

# --- 3. wait for the artefacts the evaluator needs ---------------------------
for _ in $(seq 1 180); do
  [[ -f "$OUT_DIR/final.4dmap" ]] && break
  sleep 10
done

for f in final.4dmap experiment_log.txt config.txt; do
  if [[ -e "$OUT_DIR/$f" ]]; then
    echo "[khronos] wrote $f"
  else
    echo "[khronos] MISSING $f"
  fi
done
grep -q "Finished Cleanly" "$OUT_DIR/experiment_log.txt" 2>/dev/null \
  && echo "[khronos] experiment log says it finished cleanly" \
  || echo "[khronos] WARNING: experiment log has no 'Finished Cleanly' marker"

find "$OUT_DIR" -maxdepth 2 -type f | sed 's/^/[khronos] artefact: /' | head -20
echo "[khronos] done"
