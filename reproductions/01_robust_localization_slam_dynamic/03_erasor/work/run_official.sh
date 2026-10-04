#!/usr/bin/env bash
# 01-03 · drive the OFFICIAL ERASOR binaries over the OFFICIAL seq-00 rosbag.
#
# This script is deliberately thin: every algorithmic step is an upstream
# executable (`kitti_mapgen`, `offline_map_updater`) driven exactly the way
# `launch/mapgen.launch` and `launch/run_erasor.launch` drive it. What we add is
# only orchestration: roscore, `rosbag play`, and the `/saveflag` publish that
# upstream's README tells a human to type by hand.
#
# Nothing upstream is edited here. The one generated file is a copy of
# `config/seq_00.yaml` with `initial_map_path` / `save_path` pointed at this
# checkout (see work/generated/), because upstream ships the author's absolute
# paths.
#
# Usage (inside the ros1noetic env, after the catkin ws is built):
#   micromamba run -p <env> bash work/run_official.sh <bag> <mapgen_out> <result_out>
#
# Env overrides: ERASOR_WS (catkin workspace), ERASOR_SRC (upstream checkout).

set -euo pipefail

BAG=${1:?usage: run_official.sh <bag> <mapgen_out_dir> <result_out_dir>}
MAPGEN_OUT=${2:?usage: run_official.sh <bag> <mapgen_out_dir> <result_out_dir>}
RESULT_OUT=${3:?usage: run_official.sh <bag> <mapgen_out_dir> <result_out_dir>}

HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPRO=$(cd "$HERE/.." && pwd)
WS=${ERASOR_WS:-$(cd "$REPRO/../.." && pwd)/.ws/erasor_ws}
SRC=${ERASOR_SRC:-$REPRO/code/ERASOR}
GEN=$HERE/generated

# shellcheck disable=SC1091
source "$REPRO/../../tools/ros1_env.sh" "$WS"

mkdir -p "$MAPGEN_OUT" "$RESULT_OUT" "$GEN" "$HERE/logs"

BAG_NAME=$(basename "$BAG")
VOXEL=0.2
# mapgen names its output from the bag name: <seq>_<init>_to_<final>_w_interval<i>_voxel_<v>.pcd
SEQ=$(echo "$BAG_NAME" | cut -d_ -f1)
INIT=$(echo "$BAG_NAME" | cut -d_ -f2)
FINAL=$(echo "$BAG_NAME" | cut -d_ -f4)
INTERVAL=$(echo "$BAG_NAME" | cut -d_ -f7)
NAIVE_MAP="$MAPGEN_OUT/${SEQ}_${INIT}_to_${FINAL}_w_interval${INTERVAL}_voxel_$(printf '%.6f' $VOXEL).pcd"
RESULT_PCD="$RESULT_OUT/${SEQ}_result.pcd"

echo "[run_official] bag        : $BAG"
echo "[run_official] naive map  : $NAIVE_MAP"
echo "[run_official] result pcd : $RESULT_PCD"

# ---------------------------------------------------------------- parameters
cat > "$GEN/mapgen.yaml" <<EOF
map:
  voxelsize: $VOXEL
  target_rosbag: "$BAG_NAME"
  save_path: "$MAPGEN_OUT"
  viz_interval: 10
large_scale:
  is_large_scale: true
EOF

# upstream config/seq_00.yaml with only the two path fields rewritten
python3 - "$SRC/config/seq_00.yaml" "$GEN/erasor_seq.yaml" "$NAIVE_MAP" "$RESULT_OUT" <<'PY'
import sys, re
src, dst, naive, out = sys.argv[1:5]
s = open(src).read()
s = re.sub(r'^(\s*initial_map_path:).*$', r'\1 "' + naive + '"', s, flags=re.M)
s = re.sub(r'^(\s*save_path:).*$',       r'\1 "' + out + '"',   s, flags=re.M)
open(dst, 'w').write(s)
PY

cat > "$GEN/large_scale.yaml" <<EOF
large_scale:
  is_large_scale: true
  submap_size: 160.0
EOF

# ------------------------------------------------------------------- roscore
roscore > "$HERE/logs/roscore.log" 2>&1 &
ROSCORE_PID=$!
cleanup() {
  set +e
  [[ -n "${ERASOR_PID:-}"  ]] && kill $ERASOR_PID  2>/dev/null
  [[ -n "${MAPGEN_PID:-}"  ]] && kill $MAPGEN_PID  2>/dev/null
  [[ -n "${ROSBAG_PID:-}"  ]] && kill $ROSBAG_PID  2>/dev/null
  kill $ROSCORE_PID 2>/dev/null
  wait 2>/dev/null
}
trap cleanup EXIT

for _ in $(seq 1 60); do
  rosnode list > /dev/null 2>&1 && break
  sleep 1
done
rosnode list > /dev/null 2>&1 || { echo "[run_official] roscore did not come up"; tail -20 "$HERE/logs/roscore.log"; exit 1; }

# ------------------------------------------------------- step 1: naive mapgen
rosparam load "$GEN/mapgen.yaml"
rosparam load "$GEN/large_scale.yaml"
rosrun erasor kitti_mapgen > "$HERE/logs/mapgen.log" 2>&1 &
MAPGEN_PID=$!
rosbag play --quiet "$BAG" > "$HERE/logs/mapgen_bag.log" 2>&1 &
ROSBAG_PID=$!
wait $ROSBAG_PID || true; ROSBAG_PID=
for _ in $(seq 1 300); do
  [[ -f "$NAIVE_MAP" ]] && break
  sleep 2
done
if [[ ! -f "$NAIVE_MAP" ]]; then
  echo "[run_official] mapgen never wrote $NAIVE_MAP"; tail -30 "$HERE/logs/mapgen.log"; exit 1
fi
# `wait` on a killed child returns 143, which `set -e` would treat as fatal
kill $MAPGEN_PID 2>/dev/null || true; wait $MAPGEN_PID 2>/dev/null || true; MAPGEN_PID=
echo "[run_official] naive map written: $(du -h "$NAIVE_MAP" | cut -f1)"

# ---------------------------------------------------------- step 2: run ERASOR
rosparam load "$GEN/erasor_seq.yaml"
rosrun erasor offline_map_updater > "$HERE/logs/erasor.log" 2>&1 &
ERASOR_PID=$!
rosbag play --quiet "$BAG" > "$HERE/logs/erasor_bag.log" 2>&1 &
ROSBAG_PID=$!
wait $ROSBAG_PID || true; ROSBAG_PID=
sleep 5
echo "[run_official] publishing /saveflag 0.2"
rostopic pub -1 /saveflag std_msgs/Float32 "data: $VOXEL" > "$HERE/logs/saveflag.log" 2>&1
for _ in $(seq 1 300); do
  [[ -f "$RESULT_PCD" ]] && break
  sleep 2
done
if [[ ! -f "$RESULT_PCD" ]]; then
  echo "[run_official] ERASOR never wrote $RESULT_PCD"; tail -40 "$HERE/logs/erasor.log"; exit 1
fi
echo "[run_official] result written: $(du -h "$RESULT_PCD" | cut -f1)"
echo "[run_official] OK"
