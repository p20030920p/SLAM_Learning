#!/usr/bin/env bash
# Build the official ROS2 branch; Livox interfaces only, no hardware driver.
set -eo pipefail
WS=/root/fastlio-study-ws
source /opt/ros/jazzy/setup.bash
export http_proxy= https_proxy= HTTP_PROXY= HTTPS_PROXY=
mkdir -p "$WS/src"
if [[ ! -d "$WS/src/fast_lio/.git" ]]; then
 git -c http.proxy= -c https.proxy= clone --branch ROS2 --recursive https://github.com/hku-mars/FAST_LIO.git "$WS/src/fast_lio"
fi
mkdir -p "$WS/src/livox_ros_driver2/msg"
for msg in CustomMsg CustomPoint; do
 curl -fLsS "https://raw.githubusercontent.com/Livox-SDK/livox_ros_driver2/master/msg/$msg.msg" -o "$WS/src/livox_ros_driver2/msg/$msg.msg"
done
cat > "$WS/src/livox_ros_driver2/CMakeLists.txt" <<'EOF'
cmake_minimum_required(VERSION 3.8)
project(livox_ros_driver2)
find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(std_msgs REQUIRED)
rosidl_generate_interfaces(${PROJECT_NAME} "msg/CustomPoint.msg" "msg/CustomMsg.msg" DEPENDENCIES std_msgs)
ament_export_dependencies(rosidl_default_runtime)
ament_package()
EOF
cat > "$WS/src/livox_ros_driver2/package.xml" <<'EOF'
<package format="3"><name>livox_ros_driver2</name><version>0.0.0</version><description>Official Livox message definitions for a simulated PointCloud2 study; no driver</description><maintainer email="study@example.org">Study</maintainer><license>MIT</license><buildtool_depend>ament_cmake</buildtool_depend><build_depend>rosidl_default_generators</build_depend><exec_depend>rosidl_default_runtime</exec_depend><depend>std_msgs</depend><member_of_group>rosidl_interface_packages</member_of_group><export><build_type>ament_cmake</build_type></export></package>
EOF
# Jazzy/PCL require C++17. These are build-only compatibility changes.
sed -i 's/c++14/c++17/g; s/c++0x/c++17/g; s/CMAKE_CXX_STANDARD 14/CMAKE_CXX_STANDARD 17/' "$WS/src/fast_lio/CMakeLists.txt"
python3 - "$WS/src/fast_lio/src/IMU_Processing.hpp" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1]); text=p.read_text()
marker='  /*** undistort each lidar point (backward propagation) ***/'
if 'FASTLIO_STUDY_NO_DESKEW' not in text:
    assert text.count(marker)==1
    text='#include <cstdlib>\n'+text.replace(marker,
        '  // Study ablation: keep IMU prediction/state; skip point correction only.\n'
        '  if (std::getenv("FASTLIO_STUDY_NO_DESKEW")) return;\n\n'+marker)
    p.write_text(text)
PY
cd "$WS"
git -C src/fast_lio rev-parse HEAD > upstream-commit.txt
git -C src/fast_lio diff > build-compatibility.patch
colcon build --symlink-install --executor sequential --cmake-args -DCMAKE_BUILD_TYPE=Release > build.log 2>&1
tail -15 build.log
