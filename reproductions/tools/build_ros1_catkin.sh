#!/usr/bin/env bash
# Build an upstream ROS 1 (catkin) checkout into a machine-local workspace.
#
# Both upstream repos we build this way (ERASOR, Removert) are plain catkin
# packages, so the build is the documented one - `catkin_make` in a ws whose
# `src/` holds a symlink to the pristine checkout. Three things are specific to
# this machine and are the reason this wrapper exists:
#
#   1. The ambient ROS 2 Jazzy environment has to be stripped first
#      (see tools/ros1_env.sh) or the link step can pick ROS 2 libraries.
#   2. conda-forge's PCL 1.13 config does not export the VTK include dir, but
#      `pcl/visualization` headers need it -> CXX flags point at vtk-9.2.
#   3. The same PCL config does not put all VTK DSOs on the link line
#      (`libvtksys-9.2.so.1: DSO missing from command line`) ->
#      `--copy-dt-needed-entries` plus an rpath into the env's lib dir.
#
# Nothing in the upstream source tree is touched by this script. The upstream
# source patches that *are* needed (PCL/OpenCV API drift) live next to each
# reproduction as `work/local_patches.patch`.
#
# Usage: build_ros1_catkin.sh <ws> <pkg_symlink_name> <upstream_src_dir> [extra catkin_make args...]

set -euo pipefail

WS=${1:?usage: build_ros1_catkin.sh <ws> <pkg_name> <src_dir> [extra args...]}
NAME=${2:?usage: build_ros1_catkin.sh <ws> <pkg_name> <src_dir> [extra args...]}
SRC=${3:?usage: build_ros1_catkin.sh <ws> <pkg_name> <src_dir> [extra args...]}
shift 3

TOOLS=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck disable=SC1091
source "$TOOLS/ros1_env.sh"

ENV_PREFIX=${CONDA_PREFIX:-$(dirname "$(dirname "$(command -v roscore)")")}

mkdir -p "$WS/src"
ln -sfn "$(cd "$SRC" && pwd)" "$WS/src/$NAME"

cd "$WS"
catkin_make \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_CXX_FLAGS="-I$ENV_PREFIX/include/vtk-9.2" \
  -DCMAKE_EXE_LINKER_FLAGS="-Wl,--copy-dt-needed-entries -L$ENV_PREFIX/lib -Wl,-rpath,$ENV_PREFIX/lib" \
  -j"$(nproc)" "$@"

echo "[build_ros1_catkin] built $NAME in $WS"
ls -1 "$WS/devel/lib/$NAME" 2>/dev/null | sed 's/^/[build_ros1_catkin] binary: /' || true
