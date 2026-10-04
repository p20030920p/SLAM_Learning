#!/usr/bin/env bash
# Put this machine's ROS 1 Noetic toolchain (micromamba + robostack) in front of
# the ambient ROS 2 Jazzy environment.
#
# Why this exists
# ---------------
# The shell that runs these reproductions has ROS 2 Jazzy sourced, so
# `LD_LIBRARY_PATH`, `PYTHONPATH`, `CMAKE_PREFIX_PATH` and `AMENT_PREFIX_PATH`
# all point into `/opt/ros/jazzy`. ROS 1 and ROS 2 ship libraries with *the same
# names* (`libimage_transport.so`, `libroscpp.so`, `libcv_bridge.so`, ...). If
# Jazzy stays on the search path, a ROS 1 binary silently loads ROS 2 libraries
# and dies at run time with a `symbol lookup error` — the build itself succeeds,
# which is what makes it confusing. Observed here on
# `removert_removert` (undefined `image_transport::ImageTransport`).
#
# So: strip every `/opt/ros/jazzy*` entry, unset the ROS 2 variables, then source
# the catkin devel space of the workspace we are about to use.
#
# Usage
# -----
#   micromamba run -p <repo>/reproductions/.venvs/ros1noetic \
#       bash -c 'source <this file> <catkin_ws>; <command>'
#
# The driver scripts under `*/work/run_official.sh` source it themselves, so in
# practice you only need the `micromamba run` wrapper.

if [[ -z "${BASH_VERSION:-}" ]]; then
  echo "ros1_env.sh must be sourced from bash" >&2
  return 1 2>/dev/null || exit 1
fi

_ros1_ws=${1-}

_ros1_strip_paths() {
  local name=$1 val=${!1-} out="" p oldifs=$IFS
  [[ -z "$val" ]] && return 0
  IFS=:
  for p in $val; do
    case "$p" in
      /opt/ros/jazzy*) ;;                       # ROS 2: drop
      *) out="${out:+$out:}$p" ;;
    esac
  done
  IFS=$oldifs
  export "$name=$out"
}

for _v in LD_LIBRARY_PATH PYTHONPATH CMAKE_PREFIX_PATH PKG_CONFIG_PATH ROS_PACKAGE_PATH; do
  _ros1_strip_paths "$_v"
done
unset AMENT_PREFIX_PATH ROS_DISTRO ROS_VERSION ROS_PYTHON_VERSION \
      ROS_AUTOMATIC_DISCOVERY_RANGE ROS_LOCALHOST_ONLY 2>/dev/null || true
unset _v

# We run in this env, so declare it: some ROS 1 tools read these back.
export ROS_DISTRO=noetic ROS_VERSION=1 ROS_PYTHON_VERSION=3

if ! command -v roscore > /dev/null 2>&1; then
  cat >&2 <<'EOF'
ros1_env.sh: no `roscore` on PATH - the ROS 1 Noetic environment is not active.
Run through micromamba, e.g.

  micromamba run -p "$(git rev-parse --show-toplevel)/reproductions/.venvs/ros1noetic" \
      bash -c 'source reproductions/tools/ros1_env.sh <ws>; ...'

(see the folder README for the one-time env build command)
EOF
  return 1 2>/dev/null || exit 1
fi

export ROS_MASTER_URI=${ROS_MASTER_URI:-http://localhost:11311}
# ROS 1 setup scripts are not `set -u` clean (they touch ZSH_VERSION).
if [[ -n "$_ros1_ws" && -f "$_ros1_ws/devel/setup.bash" ]]; then
  set +u
  # shellcheck disable=SC1091
  source "$_ros1_ws/devel/setup.bash"
  set -u
  echo "[ros1_env] ROS_DISTRO=$(rosversion -d)  ws=$_ros1_ws"
else
  echo "[ros1_env] ROS_DISTRO=$(rosversion -d)  (no devel space sourced)"
fi
