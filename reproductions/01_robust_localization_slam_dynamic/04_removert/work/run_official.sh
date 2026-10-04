#!/usr/bin/env bash
# 01-04 · drive the OFFICIAL Removert binary over a KITTI-format sequence.
#
# Upstream is offline: it reads `<seq>/velodyne/*.bin` + a poses file and needs
# ROS only as a parameter server (its README: "no topic flows within our
# system"). So the orchestration here is roscore + `rosparam load` + the node.
# Nothing upstream is edited.
#
# Usage (inside the ros1noetic env, after the catkin ws is built):
#   micromamba run -p <env> bash work/run_official.sh <generated_params.yaml> <out_dir>
#
# Env overrides: REMOVERT_WS (catkin workspace).

set -euo pipefail

PARAMS=${1:?usage: run_official.sh <generated_params.yaml> <out_dir>}
OUT=${2:?usage: run_official.sh <generated_params.yaml> <out_dir>}

HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPRO=$(cd "$HERE/.." && pwd)
WS=${REMOVERT_WS:-$(cd "$REPRO/../.." && pwd)/.ws/removert_ws}

# shellcheck disable=SC1091
source "$REPRO/../../tools/ros1_env.sh" "$WS"
mkdir -p "$OUT" "$HERE/logs"

FINAL_MAP="$OUT/map_static/StaticMapScansideMapGlobal.pcd"

roscore > "$HERE/logs/roscore.log" 2>&1 &
ROSCORE_PID=$!
cleanup() {
  set +e
  [[ -n "${RMV_PID:-}" ]] && kill $RMV_PID 2>/dev/null
  kill $ROSCORE_PID 2>/dev/null
  wait 2>/dev/null
}
trap cleanup EXIT

for _ in $(seq 1 60); do
  rosnode list > /dev/null 2>&1 && break
  sleep 1
done
rosnode list > /dev/null 2>&1 || { echo "[removert] roscore did not come up"; tail -20 "$HERE/logs/roscore.log"; exit 1; }

rosparam load "$PARAMS"
echo "[removert] params loaded from $PARAMS"
rosrun removert removert_removert > "$HERE/logs/removert.log" 2>&1 &
RMV_PID=$!

# the node does all the work in its constructor; a 141-scan KITTI map takes minutes
for i in $(seq 1 900); do
  if ! kill -0 $RMV_PID 2>/dev/null; then
    echo "[removert] node exited early (rc=$(wait $RMV_PID; echo $?))"; tail -40 "$HERE/logs/removert.log"; exit 1
  fi
  [[ -f "$FINAL_MAP" ]] && break
  sleep 2
done

if [[ ! -f "$FINAL_MAP" ]]; then
  echo "[removert] no $FINAL_MAP after 30 min"; tail -40 "$HERE/logs/removert.log"; exit 1
fi
# StaticMapScansideMapGlobal.pcd is written by the last step of run() (the
# scan-side pass), so its existence means the algorithm has finished; the node
# then only spins. Give the writer a moment to flush.
sleep 3
echo "[removert] static map: $(du -h "$FINAL_MAP" | cut -f1)"
find "$OUT" -name '*.pcd' | sort | sed 's/^/[removert] output: /'
echo "[removert] OK"
