#!/usr/bin/env bash
# 01-09 · drive the OFFICIAL ltremovert binary over the two generated sessions.
#
# Upstream is offline: it reads a scan directory plus a pose file per session and
# needs ROS only as a parameter server (upstream README: "no topic flows within
# our system"), so the orchestration is roscore + `rosparam load` + the node -
# exactly the shape of 04_removert/work/run_official.sh. Nothing upstream is
# edited; the single portability patch is documented in work/local_patches.patch.
#
# Usage (inside the ros1noetic env, after the catkin ws is built):
#   micromamba run -p <env> bash work/run_official.sh <generated_params.yaml> <out_dir>
#
# Env overrides: LTMAPPER_WS (catkin workspace).

set -euo pipefail

PARAMS=${1:?usage: run_official.sh <generated_params.yaml> <out_dir>}
OUT=${2:?usage: run_official.sh <generated_params.yaml> <out_dir>}

HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPRO=$(cd "$HERE/.." && pwd)
WS=${LTMAPPER_WS:-$(cd "$REPRO/../.." && pwd)/.ws/lt_mapper_ws}

# shellcheck disable=SC1091
source "$REPRO/../../tools/ros1_env.sh" "$WS"
mkdir -p "$OUT" "$HERE/logs"

# run() ends with saveAllTypeOfScans() (Removerter.cpp:1676), whose last write is
# `saveStrongNDScans` into scans_nd_strong/ under the *original* central scan
# names; the node spins forever after that, so that file is the completion marker.
CENTRAL_SCAN_DIR=$(sed -n 's/^ *central_sess_scan_dir: *//p' "$PARAMS" | tr -d '"')
LAST_SCAN=$(ls -1 "$CENTRAL_SCAN_DIR" | sort | tail -1)
DONE_MARKER="$OUT/scans_nd_strong/$LAST_SCAN"
LOG="$HERE/logs/ltmapper.log"

# A marker left over from an earlier run would make the wait loop below return
# immediately and the trap would kill the node mid-computation, silently
# "succeeding" with the previous run's maps. Clear it, and verify completion
# against this run's log (which the redirect above truncates) rather than
# against the file alone.
rm -f "$DONE_MARKER"

roscore > "$HERE/logs/roscore.log" 2>&1 &
ROSCORE_PID=$!
cleanup() {
  set +e
  [[ -n "${LTM_PID:-}" ]] && kill $LTM_PID 2>/dev/null
  kill $ROSCORE_PID 2>/dev/null
  wait 2>/dev/null
}
trap cleanup EXIT

for _ in $(seq 1 60); do
  rosnode list > /dev/null 2>&1 && break
  sleep 1
done
rosnode list > /dev/null 2>&1 || { echo "[ltmapper] roscore did not come up"; tail -20 "$HERE/logs/roscore.log"; exit 1; }

rosparam load "$PARAMS"
echo "[ltmapper] params loaded from $PARAMS"
echo "[ltmapper] completion marker: $DONE_MARKER"
rosrun removert removert_removert > "$LOG" 2>&1 &
LTM_PID=$!

# the node does all the work in its constructor; the paper's own runs are
# minutes-scale, this KITTI pair is smaller. 1 h cap.
for i in $(seq 1 1800); do
  if ! kill -0 $LTM_PID 2>/dev/null; then
    echo "[ltmapper] node exited early (rc=$(wait $LTM_PID; echo $?))"; tail -40 "$LOG"; exit 1
  fi
  [[ -f "$DONE_MARKER" ]] && break
  sleep 2
done

if [[ ! -f "$DONE_MARKER" ]]; then
  echo "[ltmapper] no $DONE_MARKER after 60 min"; tail -40 "$LOG"; exit 1
fi
# The marker alone is the completion proof: it is the last file written by the
# last saveScans() call of run(), it was removed above so it cannot be stale, and
# the output directory as a whole was wiped by the caller. Verify the per-scan
# directories really hold one file per central scan, and only *warn* about the
# log: rosconsole's stdout is block-buffered when redirected, so the log can lag
# the actual progress by a few KB even after the run has finished.
NUM_CENTRAL=$(ls -1 "$CENTRAL_SCAN_DIR" | wc -l)
for d in scans_updated scans_updated_strong scans_nd_strong; do
  n=$(ls -1 "$OUT/$d" 2>/dev/null | wc -l)
  if [[ "$n" -ne "$NUM_CENTRAL" ]]; then
    echo "[ltmapper] $d holds $n files, expected $NUM_CENTRAL - the run did not finish"
    exit 1
  fi
done
grep -q "scans_nd_strong/$LAST_SCAN" "$LOG" \
  || echo "[ltmapper] warning: the log has not flushed the final save line yet (buffered stdout); file evidence says the run finished"
# the marker file is created by the last saveScans() call of the run; give the
# writer a moment to flush before the trap kills the node.
sleep 5
echo "[ltmapper] updated_map.pcd: $(du -h "$OUT/updated_map.pcd" 2>/dev/null | cut -f1)"
find "$OUT" -maxdepth 1 -name '*.pcd' | sort | sed 's/^/[ltmapper] output: /'
echo "[ltmapper] OK"
