#!/usr/bin/env bash
#
# record_live_split.sh -- record one scenario level as a split-screen clip.
#
#   LEFT  960x1080  Gazebo's own third-person overview render (live, not a replay)
#   RIGHT 960x1080  RViz2 drawing the map slam_toolbox is building online
#
# Both halves come from a single 1920x1080 x11grab of the virtual display :99, so
# they are the same instant.
#
#   ./record_live_split.sh S1_static [SECONDS]
#   ./record_live_split.sh S2_dynamic 150
#
# Level table (world / obstacles / lidar) matches
# Sim2Real-AlgoBench/scenario_variants/run_scenario.sh, which is the single source
# of truth for what each level is; this script only decides how to film it.
#
# ---------------------------------------------------------------------------
# WHY THERE IS A DERIVED URDF AND BRIDGE CONFIG
# ---------------------------------------------------------------------------
# Flat camera frames have been observed on this WSL/Mesa setup despite healthy
# topic rates. A universal one-camera limit or gpu_lidar render-target conflict
# has NOT been isolated: removing the robot camera did not establish a successful
# split-screen recording. See docs/self-recovery/STATUS.zh-CN.md for M0/M1/M2.
#
# To reduce the number of rendering variables this script generates, in its
# scratch directory only:
#   * <urdf>_nocam.urdf      the robot URDF with the front_camera sensor removed
#   * bridge_sensors_nocam.yaml  the sensor bridge config without /camera topics
#   * topcam.sdf             the overview camera model, spawned at runtime
# Nothing tracked in Sim2Real-AlgoBench or SLAM-Physical is ever modified.
#
# The overview camera's placement is upstream's (tools/topcam.sdf, pose
# "3.65 1.0 10.5 0 1.5708 0"), only the resolution/field of view are widened here
# to fill a 960x1080 panel while still covering the whole 30x30 arena.  Upstream's
# own measurement (docs/RECORDING.md) is that world +X is image-up and world +Y is
# image-left, so the left half is rotated 90 degrees clockwise to match RViz.
#
# `-u` is deliberately left off: the ROS and ament setup files below dereference
# variables they expect to be set already, and abort under `set -u` with
# "AMENT_TRACE_SETUP_FILES: unbound variable".  `-e` and `pipefail` are on.
set -eo pipefail

LEVEL="${1:?usage: record_live_split.sh <S1_static|S2_dynamic|S3_large_change|S4_degradation> [SECONDS]}"
SECONDS_TO_RECORD="${2:-150}"

REPO="${S2R_REPO:-/root/projects/Sim2Real-AlgoBench}"
VARIANTS="$REPO/scenario_variants"
NEWREPO="${SLAM_LEARNING_REPO:-/mnt/d/workspace/be2/slam_learning_updated}"
OUTDIR="${OUTDIR:-$NEWREPO/results/localization/self-recovery}"
SCRATCH="${SCRATCH:-/root/live-split/$LEVEL}"
DISPLAY_NUM="${DISPLAY_NUM:-:99}"
SPLIT_X="${SPLIT_X:-960}"
SCREEN="${SCREEN:-1920x1080}"

# the recording-specific RViz layout: top-down, so the growing occupancy grid is
# the subject.  The repository's own race_sim.rviz is for interactive driving and
# uses an orbit camera, which is not readable as a map-growth figure.
RVIZ_VIEW_CENTER="${RVIZ_VIEW_CENTER:-3.65,1.0}"
RVIZ_VIEW_SCALE="${RVIZ_VIEW_SCALE:-52}"

# ---------------------------------------------------------------- level table
WORLD=""; URDF="$REPO/src/race_description/urdf/omni_car_ros2_control.urdf"
SLAM=false; PATROL=false; OBSTACLES=false; TRUTH=false
SX=8.0727; SY=7.5312; SYAW=-1.5708
# /odom does not exist in this stack; the drive controller publishes here.
ODOM_TOPIC=/omni_drive_controller/odom
ROUTE_MAIN='8.5,7.6;5.3,7.6;5.3,6.5;8.2,6.5;8.2,5.2;9.7,5.2;9.7,4.2;6.7,4.2;6.7,1.8;9.7,1.8'
ROUTE_CORRIDOR='9.4,-3.1;5.0,-3.1'
WAYPOINTS="$ROUTE_MAIN"
CONDITION=""

case "$LEVEL" in
  S1_static)
    WORLD="$VARIANTS/worlds/S1_static.world"; SLAM=true; PATROL=true; TRUTH=true
    CONDITION="Nominal arena, no moving obstacle, full 720-beam 12 m lidar; the map is built from scratch while the robot patrols." ;;
  S2_dynamic)
    WORLD="$VARIANTS/worlds/S2_dynamic.world"; SLAM=true; PATROL=true; OBSTACLES=true; TRUTH=true
    CONDITION="Same arena with three scripted moving obstacles (amplitudes 1.6/1.4/1.75 m, periods 8/7/6 s) crossing the patrol route." ;;
  S3_large_change)
    WORLD="$VARIANTS/worlds/S3_large_change.world"; PATROL=true; TRUTH=true
    CONDITION="Structurally altered arena: the passage the robot mapped in S1 is walled off, so the live scan contradicts the previously built map." ;;
  S4_degradation)
    WORLD="$VARIANTS/worlds/S4_degradation.world"
    URDF="$VARIANTS/urdf/omni_car_lidar_sparse.urdf"
    PATROL=true; TRUTH=true
    SX=7.15; SY=-3.10; SYAW=0.0; WAYPOINTS="$ROUTE_CORRIDOR"
    CONDITION="Long straight featureless corridor with a degraded lidar: 72 beams over 240 deg, 3.5 m range, 0.03 m gaussian range noise." ;;
  *) echo "unknown level '$LEVEL'" >&2; exit 2 ;;
esac

mkdir -p "$SCRATCH/logs" "$OUTDIR"

# The helper tools live next to this script in the repository and are copied into
# the scratch directory so the run is self-contained and nothing outside it is
# written to.
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
for tool in rec_tools.py grab_overview.py make_rviz_config.py sdk_image_view.py \
            verify_split.py image_utils.py; do
  cp -f "$HERE/$tool" "$SCRATCH/$tool"
done

# ------------------------------------------------------------------ toolchain
source /opt/ros/jazzy/setup.bash
if [ -f "$REPO/install/setup.bash" ]; then
  source "$REPO/install/setup.bash"
else
  echo "error: $REPO/install/setup.bash missing -- build the workspace first" >&2
  exit 3
fi
# A domain and partition of our own, so a concurrently running scenario on another
# domain/partition cannot collide with this recording.
export ROS_DOMAIN_ID="${ROS_DOMAIN_ID:-79}"
export GZ_PARTITION="${GZ_PARTITION:-live_split_$LEVEL}"
export DISPLAY="$DISPLAY_NUM"

# the display and window manager have to exist before anything is placed on them
if ! xdpyinfo -display "$DISPLAY_NUM" >/dev/null 2>&1; then
  echo "starting Xvfb on $DISPLAY_NUM"
  Xvfb "$DISPLAY_NUM" -screen 0 1920x1080x24 +extension GLX +render -noreset \
    >"$SCRATCH/logs/xvfb.log" 2>&1 &
  sleep 3
fi
if ! pgrep -x openbox >/dev/null 2>&1; then
  echo "starting openbox"
  openbox >"$SCRATCH/logs/openbox.log" 2>&1 &
  sleep 2
fi

# ------------------------------------------------- derived URDF, bridge, camera
# --lidar-type keep: the URDF is taken as upstream wrote it apart from the camera
# sensor being dropped.  Measured on this gz-sim 8 build, `gpu_lidar` is the only
# lidar type that publishes at all (`type="ray"` and `type="lidar"` give no /scan
# data whatsoever), and one `gpu_lidar` plus one `camera` do coexist in a world, so
# the lidar is left exactly as upstream has it.
python3 "$SCRATCH/rec_tools.py" \
  --urdf "$URDF" \
  --bridge "$REPO/src/race_bringup/config/bridge_sensors.yaml" \
  --outdir "$SCRATCH" \
  --name topcam --topic /top_view \
  --pose '3.65 1.0 10.5 0 1.5708 0' \
  --rate 10 --hfov 1.92 --width 600 --height 675 \
  --lidar-type keep \
  2>&1 | tee "$SCRATCH/logs/rec_tools.log"

URDF_NOCAM="$SCRATCH/$(basename "${URDF%.urdf}")_rec.urdf"
BRIDGE_NOCAM="$SCRATCH/bridge_sensors_nocam.yaml"
TOPCAM_SDF="$SCRATCH/topcam.sdf"

# --------------------------------------------------------------- the stack
LAUNCH_LOG="$SCRATCH/logs/stack.log"
echo "launching $LEVEL: world=$WORLD"
setsid ros2 launch "$VARIANTS/launch/scenario.launch.py" \
  "world:=$WORLD" "urdf:=$URDF_NOCAM" "bridge_config:=$BRIDGE_NOCAM" \
  headless:=true "slam:=$SLAM" "patrol:=$PATROL" "obstacles:=$OBSTACLES" \
  "truth:=$TRUTH" "waypoints:=$WAYPOINTS" \
  "spawn_x:=$SX" "spawn_y:=$SY" "spawn_yaw:=$SYAW" \
  >"$LAUNCH_LOG" 2>&1 &
STACK_PID=$!
STACK_PGID=$(ps -o pgid= -p "$STACK_PID" | tr -d ' ')

RECORDER_PIDS=()
cleanup() {
  local rc=$?
  echo "cleaning up"
  # Kill the processes this run started, by PID and by process group.  A global
  # `pkill -f 'gz sim'` is deliberately not used: it reaches across ROS domains and
  # GZ partitions and kills a concurrently running scenario (it did, once).
  for p in "${RECORDER_PIDS[@]:-}"; do
    [ -n "$p" ] && kill -TERM "$p" 2>/dev/null || true
  done
  [ -n "${STACK_PGID:-}" ] && kill -TERM -- "-$STACK_PGID" 2>/dev/null || true
  sleep 5
  for p in "${RECORDER_PIDS[@]:-}"; do
    [ -n "$p" ] && kill -KILL "$p" 2>/dev/null || true
  done
  [ -n "${STACK_PGID:-}" ] && kill -KILL -- "-$STACK_PGID" 2>/dev/null || true
  exit $rc
}
trap cleanup EXIT INT TERM

# ------------------------------------------------------------------- readiness
wait_topic() {
  local topic=$1 limit=$2 i=0
  while [ "$i" -lt "$limit" ]; do
    if ros2 topic list 2>/dev/null | grep -qx "$topic"; then return 0; fi
    sleep 3; i=$((i + 3))
  done
  return 1
}

# Refuse to run if another stack is already on this domain/partition.  Two stacks
# sharing a domain means two robots publishing /scan and two things writing
# /cmd_vel, and the recording would silently contain someone else's simulation.
if ros2 topic list 2>/dev/null | grep -qx /scan; then
  echo "error: /scan already exists on ROS_DOMAIN_ID=$ROS_DOMAIN_ID." >&2
  echo "       Another scenario is running on this domain; pick another" >&2
  echo "       ROS_DOMAIN_ID or wait for it to finish. Refusing to start a" >&2
  echo "       second stack, which would corrupt both." >&2
  exit 8
fi

# The odometry topic is /omni_drive_controller/odom; /odom does not exist in this
# stack (the remap in slam_launch.py is named /odom but nothing publishes there).
for t in /clock /scan "$ODOM_TOPIC" /robot_description; do
  echo "waiting for $t"
  wait_topic "$t" 240 || { echo "error: $t never appeared; see $LAUNCH_LOG" >&2; exit 4; }
done
if [ "$SLAM" = true ]; then
  echo "waiting for slam_toolbox to publish /map"
  wait_topic /map 300 || { echo "error: /map never appeared" >&2; exit 5; }
fi

# ------------------------------------------------------- spawn the overview cam
echo "spawning the overview camera"
ros2 run ros_gz_sim create -file "$TOPCAM_SDF" -name topcam \
  -x 3.65 -y 1.0 -z 10.5 -P 1.5708 -world competition_world \
  >>"$SCRATCH/logs/topcam_spawn.log" 2>&1
sleep 8

ros2 run ros_gz_bridge parameter_bridge \
  "/top_view@sensor_msgs/msg/Image[gz.msgs.Image" \
  >>"$SCRATCH/logs/topcam_bridge.log" 2>&1 &
RECORDER_PIDS+=($!)
wait_topic /top_view 90 || { echo "error: /top_view never appeared" >&2; exit 6; }

# Confirm the overview camera really renders before spending time recording it.
# The gate is the frame's standard deviation: a camera with no render target
# publishes a constant colour, which measures std ~ 0.
RENDER_OK=0
for _ in 1 2 3 4 5 6; do
  STATS=$(python3 "$SCRATCH/grab_overview.py" "$SCRATCH/probe.png" 20 \
            --topic /top_view 2>/dev/null || true)
  echo "  $STATS"
  STD=$(printf '%s' "$STATS" | sed -n 's/.*std= *\([0-9.]*\).*/\1/p')
  if [ -n "$STD" ]; then
    if awk "BEGIN{exit !($STD > 3.0)}"; then RENDER_OK=1; break; fi
  fi
  sleep 8
done
if [ "$RENDER_OK" != 1 ]; then
  echo "error: /top_view is a flat frame -- the overview camera has no render target." >&2
  echo "       That means another RGB camera is active. Check that the derived URDF" >&2
  echo "       really removed the front_camera sensor: $URDF_NOCAM" >&2
  exit 7
fi

# --------------------------------------------------------- viewer + right half
# The right half is either RViz2 or the purpose-built map viewer.
#
# Default is the map viewer.  RViz2 cannot draw the occupancy grid on this machine:
# its GLSL program fails to link under llvmpipe --
#   rviz2]: rviz/glsl120/indexed_8bit_image.vert ... GLSL link result :
#   active samplers with a different type refer to the same texture image unit
# -- so the Map display is blank and the "map is growing" evidence is missing.
# map_view.py draws the same /map grid, the same /scan and the same odom pose with
# the X11 canvas, which does work here.  Set RIGHT_VIEW=rviz to use RViz instead.
RIGHT_VIEW="${RIGHT_VIEW:-map}"
RIGHT_TITLE="$LEVEL map"

if [ "$RIGHT_VIEW" = rviz ]; then
  python3 "$SCRATCH/make_rviz_config.py" \
    --out "$SCRATCH/live_split.rviz" \
    --center "$RVIZ_VIEW_CENTER" --scale "$RVIZ_VIEW_SCALE" \
    >"$SCRATCH/logs/rviz_config.log" 2>&1
  ros2 run rviz2 rviz2 -d "$SCRATCH/live_split.rviz" \
    --ros-args -p use_sim_time:=true >"$SCRATCH/logs/rviz.log" 2>&1 &
  RECORDER_PIDS+=($!)
  RIGHT_MATCH="RViz"
  sleep 15
else
  python3 "$SCRATCH/map_view.py" \
    --geometry 960x1080+960+0 --split "$SPLIT_X" \
    --scan-topic /scan --odom-topic "$ODOM_TOPIC" \
    --frame map --odom-child base_footprint \
    --view-center "$RVIZ_VIEW_CENTER" --view-size 22 \
    --label "$LEVEL" >"$SCRATCH/logs/map_view.log" 2>&1 &
  RECORDER_PIDS+=($!)
  RIGHT_MATCH="live_map_view"
  sleep 10
fi

python3 "$SCRATCH/sdk_image_view.py" --topic /top_view \
  --geometry 960x1080+0+0 --rotate cw --label "$LEVEL" \
  >"$SCRATCH/logs/viewer.log" 2>&1 &
RECORDER_PIDS+=($!)
sleep 8

# ------------------------------------------------------------------- placement
# The window is found by frame name *and* by having a real size.  `xdotool search
# --name RViz` alone matches Qt's internal "Qt Selection Owner for rviz2" helper
# window, which is 3x3; moving that leaves the visible RViz window where it was and
# the right half of the capture comes out black.
place() {  # window-name-substring  x y w h
  local wid geom name
  wid=""
  for wid_candidate in $(xdotool search --name "$1" 2>/dev/null); do
    name=$(xdotool getwindowname "$wid_candidate" 2>/dev/null)
    geom=$(xdotool getwindowgeometry "$wid_candidate" 2>/dev/null | awk '/Geometry/{print $2}')
    case "$geom" in
      [0-9]*x[0-9]*)
        local w=${geom%x*} h=${geom#*x}
        if [ "$w" -ge 200 ] && [ "$h" -ge 200 ]; then
          wid="$wid_candidate"
          break
        fi
        ;;
    esac
  done
  [ -z "$wid" ] && { echo "  window matching '$1' not found (no window >=200x200)"; return 0; }
  xdotool windowmove "$wid" "$2" "$3" 2>/dev/null || true
  xdotool windowsize "$wid" "$4" "$5" 2>/dev/null || true
  xdotool windowraise "$wid" 2>/dev/null || true
  echo "  placed '$1' -> $2,$3 ${4}x${5}"
}
echo "placing windows"
place "$LEVEL"        0   0 960 1080
place "$RIGHT_MATCH" 960   0 960 1080
sleep 5

# Gate on the layout itself before spending minutes recording it: grab the display
# and check that each half has content.  A misplaced window shows up here as a
# black half rather than as a wasted recording.
layout_gate() {
  import -window root "$SCRATCH/layout.png" 2>/dev/null || return 0
  python3 - "$SCRATCH/layout.png" "$SPLIT_X" <<'PY'
import sys
import numpy as np
from PIL import Image
a = np.asarray(Image.open(sys.argv[1]).convert("RGB"))
split = int(sys.argv[2])
ok = True
for name, h in (("left", a[:, :split]), ("right", a[:, split:])):
    uniq = len(np.unique(h.reshape(-1, 3), axis=0))
    good = h.std() > 4.0 and uniq > 20
    ok = ok and good
    print(f"  {name:5s} mean={h.mean():7.2f} std={h.std():6.2f} uniq={uniq:6d} "
          f"{'OK' if good else 'EMPTY'}")
sys.exit(0 if ok else 1)
PY
}
LAYOUT_TRIES=0
until layout_gate || [ "$LAYOUT_TRIES" -ge 3 ]; do
  LAYOUT_TRIES=$((LAYOUT_TRIES + 1))
  echo "layout incomplete, re-placing (attempt $LAYOUT_TRIES)"
  place "$LEVEL"    0   0 960 1080
  place "RViz"    960   0 960 1080
  sleep 6
done
echo "layout gate: $([ "$LAYOUT_TRIES" -ge 3 ] && echo 'still incomplete, recording anyway' || echo 'both halves have content')"

# ---------------------------------------------------------------- measurements
# `ros2 topic hz` is written to a file rather than piped into grep -m1: grep exits
# after the first match, SIGPIPEs the pipeline and turns a healthy topic into a
# false "no rate".  The last average-rate line is what gets reported.
STATS_FILE="$SCRATCH/logs/rates.txt"
: >"$STATS_FILE"
measure() {  # topic seconds
  local topic=$1 secs=$2 tmp
  tmp="$SCRATCH/logs/hz$(echo "$topic" | tr '/' '_').txt"
  timeout "$secs" ros2 topic hz "$topic" >"$tmp" 2>/dev/null || true
  printf '%-30s %s\n' "$topic" \
    "$(awk '/average rate:/{r=$3} END{print (r=="" ? "no data" : r" Hz")}' "$tmp")" \
    >>"$STATS_FILE"
}
echo "measuring topic rates"
measure /scan 20
measure "$ODOM_TOPIC" 20
measure /top_view 20
measure /map 20
cat "$STATS_FILE"

# -------------------------------------------------------------------- capture
echo "settling 15 s before capture"
sleep 15

# The display must still be there.  An Xvfb that dies between the layout gate and
# the capture makes ffmpeg fail with "No data available" after minutes of work, so
# both the display and a real 2-second grab are checked first.
#
# The Xvfb pid and uptime are recorded before and after the capture.  If the pid
# changes or the uptime resets, the display was restarted mid-recording and black
# frames mean a dead display, not a rendering failure.
xdisplay_info() {
  local pid
  pid=$(pgrep -f "Xvfb ${DISPLAY_NUM} " 2>/dev/null | head -1)
  if [ -z "$pid" ]; then
    echo "pid=none uptime_s=0"
  else
    echo "pid=$pid uptime_s=$(ps -o etimes= -p "$pid" 2>/dev/null | tr -d ' ')"
  fi
}
DISPLAY_BEFORE=$(xdisplay_info)
echo "display before capture: $DISPLAY_BEFORE"

if ! xdpyinfo -display "$DISPLAY_NUM" >/dev/null 2>&1; then
  echo "error: display $DISPLAY_NUM is gone; cannot capture" >&2
  exit 9
fi
if ! ffmpeg -y -loglevel error -f x11grab -framerate 10 -video_size "$SCREEN" \
     -i "$DISPLAY_NUM.0" -t 2 -c:v libx264 -preset ultrafast -pix_fmt yuv420p \
     "$SCRATCH/preflight.mp4" >"$SCRATCH/logs/preflight.log" 2>&1; then
  echo "error: preflight capture failed; see $SCRATCH/logs/preflight.log" >&2
  tail -5 "$SCRATCH/logs/preflight.log" >&2
  exit 10
fi
echo "preflight capture OK ($(stat -c%s "$SCRATCH/preflight.mp4") bytes)"

MP4="$OUTDIR/$LEVEL.mp4"
echo "recording ${SECONDS_TO_RECORD}s -> $MP4"
ffmpeg -y -loglevel warning -f x11grab -framerate 15 \
  -video_size "$SCREEN" -i "$DISPLAY_NUM.0" \
  -t "$SECONDS_TO_RECORD" \
  -c:v libx264 -preset veryfast -crf 21 -pix_fmt yuv420p -movflags +faststart \
  "$MP4"

DISPLAY_AFTER=$(xdisplay_info)
echo "display after capture: $DISPLAY_AFTER"
if [ "$DISPLAY_BEFORE" != "$DISPLAY_AFTER" ]; then
  echo "WARNING: the display changed during the capture ($DISPLAY_BEFORE -> $DISPLAY_AFTER)." >&2
  echo "         Any black frames are a restarted display, not a rendering failure." >&2
fi

echo "encoding $OUTDIR/$LEVEL.gif"
ffmpeg -y -loglevel error -i "$MP4" \
  -vf "fps=12,scale=1280:-1:flags=lanczos,split[a][b];[a]palettegen[p];[b][p]paletteuse" \
  -loop 0 "$OUTDIR/$LEVEL.gif"

# --------------------------------------------------------------------- verify
echo "checking the exported frames"
python3 "$SCRATCH/verify_split.py" --video "$MP4" --outdir "$OUTDIR" \
  --stem "$LEVEL" --split 960 \
  --display-before "$DISPLAY_BEFORE" --display-after "$DISPLAY_AFTER" \
  | tee "$SCRATCH/logs/verify.log"

{
  echo "level=$LEVEL"
  echo "condition=$CONDITION"
  echo "world=$WORLD"
  echo "urdf=$URDF"
  echo "urdf_used=$URDF_NOCAM"
  echo "bridge_used=$BRIDGE_NOCAM"
  echo "route_waypoints=$WAYPOINTS"
  echo "spawn=$SX,$SY,$SYAW"
  echo "seconds=$SECONDS_TO_RECORD fps=15"
  echo "right_view=$RIGHT_VIEW"
  echo "display_before=$DISPLAY_BEFORE"
  echo "display_after=$DISPLAY_AFTER"
  cat "$STATS_FILE"
} >"$SCRATCH/logs/params.txt"
echo "parameters -> $SCRATCH/logs/params.txt"
echo "done"
