"""Gazebo sensor profile and two FAST-LIO2 nodes for a paired deskew ablation."""

import hashlib
import json
import xml.etree.ElementTree as ET

import yaml


def configure(repo, run, runtime, config):
    tree = ET.parse(repo / "config/robot_profiles/omni-3d-v1/omni_car_lidar3d.urdf")
    robot = tree.getroot()
    gz = robot.find("gazebo[@reference='base_link']")
    if gz is None:
        gz = ET.SubElement(robot, "gazebo", reference="base_link")
    sensor = ET.SubElement(gz, "sensor", name="study_imu", type="imu")
    for key, value in (
        ("topic", "/study/imu"),
        ("gz_frame_id", "base_link"),
        ("update_rate", "200"),
        ("always_on", "true"),
    ):
        ET.SubElement(sensor, key).text = value
    ET.SubElement(sensor, "imu")
    urdf = run / "fastlio-imu.urdf"
    tree.write(urdf, encoding="unicode")
    world = ET.parse(runtime["world"])
    ET.SubElement(
        world.getroot().find("world"), "plugin", filename="gz-sim-imu-system", name="gz::sim::systems::Imu"
    )
    world_path = run / "fastlio-world.sdf"
    world.write(world_path, encoding="unicode")
    bridge = yaml.safe_load((repo / "config/robot_profiles/omni-3d-v1/bridge_sensors.yaml").read_text())
    bridge.append(
        dict(
            ros_topic_name="/study/imu",
            gz_topic_name="/study/imu",
            ros_type_name="sensor_msgs/msg/Imu",
            gz_type_name="gz.msgs.IMU",
            direction="GZ_TO_ROS",
        )
    )
    bridge_path = run / "fastlio-bridge.yaml"
    bridge_path.write_text(yaml.safe_dump(bridge))
    runtime.update(
        urdf=str(urdf),
        bridge_config=str(bridge_path),
        world=str(world_path),
        world_sha256=hashlib.sha256(world_path.read_bytes()).hexdigest(),
        motion_test="Native Gazebo sector packets at their measured times; paired deskew ablation",
    )
    (run / "runtime.json").write_text(json.dumps(runtime, indent=2) + "\n")
    params = {
        "use_sim_time": True,
        "feature_extract_enable": False,
        "point_filter_num": 1,
        "max_iteration": 4,
        "filter_size_surf": 0.10,
        "filter_size_map": 0.10,
        "cube_side_length": 100.0,
        "runtime_pos_log_enable": False,
        "common.lid_topic": "/study/rolling",
        "common.imu_topic": "/study/imu_ready",
        "common.time_sync_en": False,
        "common.time_offset_lidar_to_imu": 0.0,
        "preprocess.lidar_type": 2,
        "preprocess.scan_line": 16,
        "preprocess.scan_rate": 3,
        "preprocess.timestamp_unit": 0,
        "preprocess.blind": 0.4,
        "mapping.acc_cov": 0.01,
        "mapping.gyr_cov": 0.001,
        "mapping.b_acc_cov": 0.0001,
        "mapping.b_gyr_cov": 0.0001,
        "mapping.fov_degree": 360.0,
        "mapping.det_range": 12.0,
        "mapping.extrinsic_est_en": False,
        "mapping.extrinsic_T": [0.0, 0.0, 0.30],
        "mapping.extrinsic_R": [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0],
        "publish.path_en": True,
        "publish.scan_publish_en": True,
        "publish.dense_publish_en": True,
        "publish.scan_bodyframe_pub_en": True,
        "pcd_save.pcd_save_en": False,
    }
    (run / "fastlio.yaml").write_text(yaml.safe_dump({"/**": {"ros__parameters": params}}))
    view = yaml.safe_load(config)
    vm = view["Visualization Manager"]
    vm["Global Options"]["Fixed Frame"] = "camera_init"
    vm["Displays"] = [d for d in vm["Displays"] if d["Class"] == "rviz_default_plugins/Grid"]
    for name, color in (("deskew", "40; 200; 120"), ("no_deskew", "255; 120; 60")):
        vm["Displays"].append(
            {
                "Class": "rviz_default_plugins/PointCloud2",
                "Name": name + " · native FAST-LIO2 output",
                "Enabled": True,
                "Topic": {
                    "Value": f"/{name}/cloud_registered",
                    "Reliability Policy": "Reliable",
                    "Durability Policy": "Volatile",
                    "Depth": 5,
                },
                "Style": "Points",
                "Size (Pixels)": 2,
                "Decay Time": 15.0,
                "Color Transformer": "FlatColor",
                "Color": color,
                "Position Transformer": "XYZ",
            }
        )
    vm["Views"]["Current"].update(X=0.0, Y=0.0, Scale=45.0)
    return yaml.safe_dump(view, sort_keys=False)
