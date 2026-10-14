#!/usr/bin/env bash
# Isolated author-source build; requires the existing Jazzy/PCL dependencies.
set -eo pipefail
WS=/root/slam-alternative-ws
if [[ -n "$1" ]]; then WS="$1"; fi
mkdir -p "$WS/src" "$WS/build_ws"
fetch() {
  local name="$1" url="$2" revision="$3"
  if [[ ! -d "$WS/src/$name/.git" ]]; then
    git -c http.proxy= -c https.proxy= clone "$url" "$WS/src/$name"
    git -C "$WS/src/$name" checkout --detach "$revision"
  fi
  [[ "$(git -C "$WS/src/$name" rev-parse HEAD)" == "$revision" ]] || {
    echo "Existing $name is another revision; refusing to reset it"; exit 3;
  }
}
fetch lidar_localization_ros2 https://github.com/rsasaki0109/lidar_localization_ros2.git ba9f7f06dbe80aeabff602c37d712dfaa948241d
fetch ndt_omp_ros2 https://github.com/rsasaki0109/ndt_omp_ros2.git 63bf15b965b71d3a53db1757abe8e31b6114372a
export LIDAR_LOCALIZATION_ROS_DISTRO=jazzy
source "$WS/src/lidar_localization_ros2/scripts/setup_local_env.sh"
cd "$WS/build_ws"
colcon build --base-paths ../src --symlink-install --packages-up-to lidar_localization_ros2 \
  --executor sequential --cmake-args -DCMAKE_BUILD_TYPE=Release
source install/setup.bash
ros2 run lidar_localization_ros2 check_lidar_localization_bringup.py --help
