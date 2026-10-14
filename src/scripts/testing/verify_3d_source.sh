#!/usr/bin/env bash
set -eo pipefail
source /opt/ros/jazzy/setup.bash
source /root/projects/Sim2Real-AlgoBench/install/setup.bash
TEST_REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
export SLAM_TEST_REPO="$TEST_REPO"
TEST_CACHE="$TEST_REPO/.cache/omni-3d-smoke"
mkdir -p "$TEST_CACHE"
gz sdf -p "$TEST_REPO/config/robot_profiles/omni-3d-v1/omni_car_lidar3d.urdf" > "$TEST_REPO/.cache/omni-3d.sdf" 2> "$TEST_CACHE/conversion.log"
export ROS_DOMAIN_ID=94 GZ_PARTITION=omni_3d_verified_source DISPLAY=:120
export LIBGL_ALWAYS_SOFTWARE=1 QT_QPA_PLATFORM=offscreen
cleanup() {
  for process in "${BRIDGE_PID:-}" "${SIM_PID:-}" "${RSP_PID:-}" "${XVFB_PID:-}"; do
    if [ -n "$process" ]; then kill -TERM -- "-$process" 2>/dev/null || kill -TERM "$process" 2>/dev/null || true; fi
  done
}
trap cleanup EXIT
setsid Xvfb "$DISPLAY" -screen 0 1280x720x24 +extension GLX -noreset > "$TEST_CACHE/xvfb.log" 2>&1 &
XVFB_PID=$!
sleep 2
python3 - <<'PY'
import os
import xml.etree.ElementTree as ET
from pathlib import Path
from ament_index_python.packages import get_package_share_directory
repo=Path(os.environ['SLAM_TEST_REPO'])
import yaml
robot=(repo/'config/robot_profiles/omni-3d-v1/omni_car_lidar3d.urdf').read_text()
params={'robot_state_publisher':{'ros__parameters':{'robot_description':robot,'use_sim_time':True}}}
(repo/'.cache/omni-3d-smoke/rsp.yaml').write_text(yaml.safe_dump(params))
tree=ET.parse(repo/'.cache/omni-3d.sdf')
model=tree.find('model')
pose=ET.SubElement(model,'pose')
pose.text='0 0 0.15 0 0 0'
for element in model.findall('.//parameters'):
    element.text=element.text.replace('$(find race_bringup)',get_package_share_directory('race_bringup'))
for element in model.findall('.//uri'):
    if element.text and element.text.startswith(('package://race_description/','model://race_description/')):
        element.text=element.text.replace('package://race_description/',get_package_share_directory('race_description')+'/').replace('model://race_description/',get_package_share_directory('race_description')+'/')
world=ET.fromstring('''<world name="source_smoke">
<physics name="p" type="ignored"><max_step_size>0.001</max_step_size><real_time_factor>1</real_time_factor></physics>
<plugin filename="gz-sim-physics-system" name="gz::sim::systems::Physics"/>
<plugin filename="gz-sim-sensors-system" name="gz::sim::systems::Sensors"><render_engine>ogre2</render_engine></plugin>
<plugin filename="gz-sim-scene-broadcaster-system" name="gz::sim::systems::SceneBroadcaster"/>
<light name="sun" type="directional"><pose>0 0 10 0 0 0</pose><diffuse>1 1 1 1</diffuse><direction>0 0 -1</direction></light>
</world>''')
for name,pose_text,size in [('ground','0 0 -0.1 0 0 0','14 14 0.2'),
    ('east','4 0 1.5 0 0 0','0.2 8 3'),('west','-4 0 1.5 0 0 0','0.2 8 3'),
    ('north','0 4 1.5 0 0 0','8 0.2 3'),('south','0 -4 1.5 0 0 0','8 0.2 3')]:
    box=ET.SubElement(world,'model',name=name)
    ET.SubElement(box,'static').text='true'
    ET.SubElement(box,'pose').text=pose_text
    link=ET.SubElement(box,'link',name='link')
    for tag in ('visual','collision'):
        geom=ET.SubElement(ET.SubElement(link,tag,name=tag),'geometry')
        ET.SubElement(ET.SubElement(geom,'box'),'size').text=size
world.append(model)
sdf=ET.Element('sdf',version='1.10')
sdf.append(world)
ET.ElementTree(sdf).write(repo/'.cache/omni-3d-smoke/world.sdf')
PY
setsid ros2 run robot_state_publisher robot_state_publisher --ros-args --params-file "$TEST_CACHE/rsp.yaml" > "$TEST_CACHE/rsp.log" 2>&1 &
RSP_PID=$!
sleep 2
setsid gz sim -s -r --headless-rendering "$TEST_CACHE/world.sdf" > "$TEST_CACHE/sim.log" 2>&1 &
SIM_PID=$!
setsid ros2 run ros_gz_bridge parameter_bridge '/lidar_3d/points@sensor_msgs/msg/PointCloud2[gz.msgs.PointCloudPacked' --ros-args -r /lidar_3d/points:=/points > "$TEST_CACHE/bridge.log" 2>&1 &
BRIDGE_PID=$!
python3 "$TEST_REPO/src/scripts/testing/verify_3d_source.py"
