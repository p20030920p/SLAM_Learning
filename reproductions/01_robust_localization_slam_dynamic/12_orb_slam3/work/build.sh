#!/usr/bin/env bash
# Build ORB-SLAM3 against a locally built Pangolin, without root.
#
# Upstream's build.sh assumes Pangolin is installed system-wide and that the
# compiler is from 2021. Three things have to be said explicitly on this machine
# (Ubuntu 24.04, GCC 13, no sudo, OpenCV 4.6 and Eigen 3.4 from apt):
#
#   1. where Pangolin and GLFW are            -> CMAKE_PREFIX_PATH
#   2. `-include cstdint -include type_traits`  -> GCC 13 no longer drags these in
#      through old headers, and Pangolin v0.8 / sigslot / g2o predate that.
#      Forcing the includes for every translation unit fixes a whole class of
#      errors at once instead of patching each file (the errors look unrelated:
#      `uint32_t does not name a type`, `std::decay_t is not a member of std`).
#   3. BUILD_PANGOLIN_FFMPEG=OFF              -> Pangolin v0.8 references
#      AV_PIX_FMT_XVMC_*, removed in FFmpeg 7; ORB-SLAM3 only needs Pangolin for
#      its viewer, so the video driver is not needed. (Done when Pangolin was
#      built; repeated here as a comment so the dependency is not a mystery.)
#
# Usage:  bash work/build.sh          # from the 12_orb_slam3 folder
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"                 # reproductions/
VENVS="$ROOT/.venvs"
SRC="$HERE/../code/ORB_SLAM3"
PREFIX_PATH="$VENVS/pangolin;$VENVS/glfw"
FLAGS="-include cstdint -include type_traits -O3"

echo "ORB-SLAM3 : $SRC"
echo "Pangolin  : $VENVS/pangolin"
echo "GLFW      : $VENVS/glfw"
echo

build_one() {
    local dir="$1" name="$2"
    echo "── $name"
    mkdir -p "$dir/build" && cd "$dir/build"
    cmake .. -DCMAKE_BUILD_TYPE=Release \
             -DCMAKE_PREFIX_PATH="$PREFIX_PATH" \
             -DCMAKE_CXX_FLAGS="$FLAGS" > /tmp/orbslam3_${name}.log 2>&1
    make -j"$(nproc)" >> /tmp/orbslam3_${name}.log 2>&1
    echo "   ok ($(date +%T))"
}

build_one "$SRC/Thirdparty/DBoW2" "DBoW2"
build_one "$SRC/Thirdparty/g2o"   "g2o"
build_one "$SRC"                  "ORB_SLAM3"

echo
echo "binaries:"
ls -la "$SRC/Examples/Stereo-Inertial/stereo_inertial_euroc" 2>/dev/null || true
