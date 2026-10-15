"""Create an additive 3D LiDAR profile from the inspected Sim2Real robot source."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

ADDITION = '''
  <!-- Research sensor extension: native chassis and sensors are preserved. -->
  <link name="lidar_3d_link">
    <inertial><mass value="0.05"/><origin xyz="0 0 0" rpy="0 0 0"/>
      <inertia ixx="0.00001" ixy="0" ixz="0" iyy="0.00001" iyz="0" izz="0.00001"/>
    </inertial>
    <visual><geometry><cylinder radius="0.03" length="0.04"/></geometry></visual>
    <collision><geometry><cylinder radius="0.03" length="0.04"/></geometry></collision>
  </link>
  <joint name="lidar_3d_joint" type="fixed">
    <parent link="base_link"/><child link="lidar_3d_link"/>
    <origin xyz="0 0 0.30" rpy="0 0 0"/>
  </joint>
  <gazebo reference="lidar_3d_link">
    <sensor name="research_lidar_3d" type="gpu_lidar">
      <pose>0 0 0 0 0 0</pose><topic>/lidar_3d</topic><gz_frame_id>lidar_3d_link</gz_frame_id>
      <update_rate>10</update_rate><always_on>true</always_on><visualize>false</visualize>
      <ray><scan>
        <horizontal><samples>720</samples><resolution>1</resolution>
          <min_angle>-3.141592653589793</min_angle><max_angle>3.141592653589793</max_angle>
        </horizontal>
        <vertical><samples>16</samples><resolution>1</resolution>
          <min_angle>-0.2617993877991494</min_angle><max_angle>0.2617993877991494</max_angle>
        </vertical>
      </scan><range><min>0.08</min><max>12.0</max><resolution>0.01</resolution></range></ray>
    </sensor>
  </gazebo>
'''
BRIDGE_ADDITION = '''
# Same-chassis research LiDAR extension; native bridge entries above are retained.
- ros_topic_name: "/points"
  gz_topic_name: "/lidar_3d/points"
  ros_type_name: "sensor_msgs/msg/PointCloud2"
  gz_type_name: "gz.msgs.PointCloudPacked"
  direction: GZ_TO_ROS
'''


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    repo = Path(__file__).resolve().parents[3]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--upstream-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=repo / "config/robot_profiles/omni-3d-v1")
    args = parser.parse_args()
    source, output = args.upstream_root.resolve(), args.output.resolve()
    if output.is_relative_to(source):
        raise ValueError("The derived profile must not modify the upstream checkout")
    inspection = json.loads((repo / "docs/testing/robot-model.json").read_text(encoding="utf-8"))
    commit = subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip()
    if commit != inspection["commit"]:
        raise ValueError("Upstream revision differs from the inspected robot model")
    for name, info in inspection["assets"].items():
        if sha((source / name).read_bytes()) != info["sha256"]:
            raise ValueError("Source asset differs from the inspected snapshot: " + name)
    original = (source / inspection["robot_urdf"]).read_bytes()
    if original.count(b"</robot>") != 1:
        raise ValueError("Expected one complete robot URDF")
    derived = original.replace(b"</robot>", ADDITION.encode() + b"</robot>")
    before, after = ET.fromstring(original), ET.fromstring(derived)
    for element in (*before, *after):
        element.tail = None
    if before.attrib != after.attrib or any(
        ET.tostring(left) != ET.tostring(right) for left, right in zip(before, after)
    ):
        raise ValueError("Native robot elements changed")
    if derived.replace(ADDITION.encode(), b"") != original:
        raise ValueError("Native source bytes changed")
    output.mkdir(parents=True, exist_ok=True)
    urdf = output / "omni_car_lidar3d.urdf"
    urdf.write_bytes(derived)
    bridge = output / "bridge_sensors.yaml"
    native_bridge = source / "src/race_bringup/config/bridge_sensors.yaml"
    bridge.write_bytes(native_bridge.read_bytes() + BRIDGE_ADDITION.encode())
    license_file = output / "LICENSE"
    license_file.write_bytes((source / "LICENSE").read_bytes())
    profile = {
        "schema_version": 1, "profile": "omni-3d-v1", "status": "generated_static_profile",
        "runtime_verified": False, "upstream": inspection["repository"], "upstream_commit": commit,
        "native_elements_preserved": len(before), "native_element_comparison_passed": True,
        "source_urdf_sha256": sha(original), "source_assets": inspection["assets"],
        "sensor": {"type": "gpu_lidar", "frame": "lidar_3d_link", "parent": "base_link",
                   "mount_xyz_m": [0, 0, 0.30], "mount_rpy_rad": [0, 0, 0], "added_mass_kg": 0.05,
                   "horizontal_samples": 720, "vertical_samples": 16, "vertical_fov_deg": 30,
                   "configured_rate_hz": 10, "range_m": [0.08, 12.0],
                   "ros_topic": "/points", "gz_topic": "/lidar_3d/points",
                   "per_point_time_field": "not provided or assumed; verify algorithm requirements"},
        "motion_model": "nav2_amcl::OmniMotionModel", "odom_topic": "/omni_drive_controller/odom",
        "artifacts": {p.name: {"sha256": sha(p.read_bytes()), "bytes": p.stat().st_size}
                      for p in (urdf, bridge, license_file)},
        "note": "Adds a 0.05 kg sensor assembly; native chassis mass/inertia, joints, sensors and control remain unchanged.",
    }
    (output / "profile.json").write_text(json.dumps(profile, indent=2) + "\n", encoding="utf-8")
    print("Generated additive robot profile: " + str(output))


if __name__ == "__main__":
    main()
