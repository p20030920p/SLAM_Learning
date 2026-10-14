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
# On this machine (WSL2, no GPU, Mesa llvmpipe) Gazebo Harmonic gives exactly one
# RGB camera sensor a working render target.  Every additional camera sensor
# publishes a constant untextured frame for ever while still reporting a healthy
# update rate; measured on the robot's own rgbd_camera, 320x180 rgb8, mean 218.00,
# std 0.00, one distinct colour.  Removing the robot camera makes the overview
# camera render, and removing the overview camera makes the robot camera render, so
# it is a one-camera limit, not a broken sensor.  2D and 3D lidar are unaffected.
#
# The overview camera therefore has to be the only RGB camera, so this script
# generates, in its scratch directory only:
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

# --------------------------------------------------------------- viewer + RViz
python3 "$SCRATCH/make_rviz_config.py" \
  --out "$SCRATCH/live_split.rviz" \
  --center "$RVIZ_VIEW_CENTER" --scale "$RVIZ_VIEW_SCALE" \
  >"$SCRATCH/logs/rviz_config.log" 2>&1

ros2 run rviz2 rviz2 -d "$SCRATCH/live_split.rviz" \
  --ros-args -p use_sim_time:=true >"$SCRATCH/logs/rviz.log" 2>&1 &
RECORDER_PIDS+=($!)
sleep 15

python3 "$SCRATCH/sdk_image_view.py" --topic /top_view \
  --geometry 960x1080+0+0 --rotate cw --label "$LEVEL" \
  >"$SCRATCH/logs/viewer.log" 2>&1 &
RECORDER_PIDS+=($!)
sleep 8

# ------------------------------------------------------------------- placement
place() {  # window-name-substring  x y w h
  local wid
  wid=$(xdotool search --name "$1" 2>/dev/null | head -1 || true)
  [ -z "$wid" ] && { echo "  window '$1' not found"; return 0; }
  xdotool windowmove "$wid" "$2" "$3" 2>/dev/null || true
  xdotool windowsize "$wid" "$4" "$5" 2>/dev/null || true
  xdotool windowraise "$wid" 2>/dev/null || true
  echo "  placed '$1' -> $2,$3 ${4}x${5}"
}
echo "placing windows"
place "$LEVEL"        0   0 960 1080
place "RViz"        960   0 960 1080
sleep 3

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

MP4="$OUTDIR/$LEVEL.mp4"
echo "recording ${SECONDS_TO_RECORD}s -> $MP4"
ffmpeg -y -loglevel warning -f x11grab -framerate 15 \
  -video_size 1920x1080 -i "$DISPLAY_NUM.0" \
  -t "$SECONDS_TO_RECORD" \
  -c:v libx264 -preset veryfast -crf 21 -pix_fmt yuv420p -movflags +faststart \
  "$MP4"

echo "encoding $OUTDIR/$LEVEL.gif"
ffmpeg -y -loglevel error -i "$MP4" \
  -vf "fps=12,scale=1280:-1:flags=lanczos,split[a][b];[a]palettegen[p];[b][p]paletteuse" \
  -loop 0 "$OUTDIR/$LEVEL.gif"

# --------------------------------------------------------------------- verify
echo "checking the exported frames"
python3 "$SCRATCH/verify_split.py" --video "$MP4" --outdir "$OUTDIR" \
  --stem "$LEVEL" --split 960 | tee "$SCRATCH/logs/verify.log"

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
  cat "$STATS_FILE"
} >"$SCRATCH/logs/params.txt"
echo "parameters -> $SCRATCH/logs/params.txt"
echo "done"
