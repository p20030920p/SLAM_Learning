"""Explicit sensor profiles for the hypothesis experiments; no synthetic depth."""
import json
import xml.etree.ElementTree as ET

import yaml


def height_control_world(source, run):
    tree = ET.parse(source)
    world = tree.getroot().find("world")
    # A disclosed derived feasibility control, never labelled the original world.
    for name, xyz, size in [("probe_high_block_A", (9.6, -2.3, 1.55), (.45, .35, .4)),
                            ("probe_high_block_B", (5.0, -3.9, 1.7), (.3, .5, .35))]:
        model = ET.SubElement(world, "model", name=name)
        ET.SubElement(model, "static").text = "true"
        ET.SubElement(model, "pose").text = " ".join(map(str, (*xyz, 0, 0, 0)))
        link = ET.SubElement(model, "link", name="link")
        for kind in ("collision", "visual"):
            element = ET.SubElement(link, kind, name=kind)
            box = ET.SubElement(ET.SubElement(element, "geometry"), "box")
            ET.SubElement(box, "size").text = " ".join(map(str, size))
            if kind == "visual":
                material = ET.SubElement(element, "material")
                ET.SubElement(material, "ambient").text = "0.8 0.3 0.9 1"
                ET.SubElement(material, "diffuse").text = "0.8 0.3 0.9 1"
    output = run / "height-control.world"
    ET.indent(tree, space="  ")
    tree.write(output, encoding="unicode", xml_declaration=True)
    return output


def configure(repo, run, flow, runtime):
    tree = ET.parse(repo / "config/robot_profiles/omni-3d-v1/omni_car_lidar3d.urdf")
    robot = tree.getroot()
    # The inexpensive localization arm has physically no 3D lidar in Gazebo.
    simple = "-2d-" in flow
    if simple:
        for element in list(robot):
            if (element.get("name") in ("lidar_3d_link", "lidar_3d_joint")
                    or element.get("reference") == "lidar_3d_link"):
                robot.remove(element)
    camera = robot.find("gazebo[@reference='camera_link']")
    sensor = ET.SubElement(camera, "sensor", name="probe_depth", type="depth_camera")
    for tag, value in (("pose", "0 0 0 0 0 0"), ("topic", "/probe_depth"),
                       ("gz_frame_id", "camera_link"), ("update_rate", "10"),
                       ("always_on", "true"), ("visualize", "false")):
        ET.SubElement(sensor, tag).text = value
    optics = ET.SubElement(sensor, "camera")
    ET.SubElement(optics, "horizontal_fov").text = "1.3962634"
    image = ET.SubElement(optics, "image")
    ET.SubElement(image, "width").text = "320"
    ET.SubElement(image, "height").text = "240"
    ET.SubElement(image, "format").text = "R_FLOAT32"
    clip = ET.SubElement(optics, "clip")
    ET.SubElement(clip, "near").text = "0.25"
    ET.SubElement(clip, "far").text = "4.0"
    ET.indent(tree, space="  ")
    urdf = run / "probe-robot.urdf"
    tree.write(urdf, encoding="unicode", xml_declaration=True)
    bridge = yaml.safe_load((repo / "config/robot_profiles/omni-3d-v1/bridge_sensors.yaml").read_text())
    if simple:
        bridge = [entry for entry in bridge if entry["ros_topic_name"] != "/points"]
    for ros_topic, gz_topic, ros_type, gz_type in [
        ("/depth/points", "/probe_depth/points", "PointCloud2", "PointCloudPacked"),
        ("/depth/image", "/probe_depth/depth_image", "Image", "Image"),
        ("/depth/camera_info", "/probe_depth/camera_info", "CameraInfo", "CameraInfo"),
    ]:
        bridge.append({"ros_topic_name": ros_topic, "gz_topic_name": gz_topic,
                       "ros_type_name": "sensor_msgs/msg/" + ros_type,
                       "gz_type_name": "gz.msgs." + gz_type, "direction": "GZ_TO_ROS"})
    bridge_path = run / "probe-bridge.yaml"
    bridge_path.write_text(yaml.safe_dump(bridge, sort_keys=False))
    runtime.update({"urdf": str(urdf), "bridge_config": str(bridge_path),
                    "sensor_arm": "2D lidar + depth camera" if simple else "3D lidar + depth camera",
                    "depth_sensor": {"type": "Gazebo depth_camera", "resolution": [320, 240],
                                     "horizontal_fov_deg": 80, "near_far_m": [.25, 4.0],
                                     "rate_hz": 10, "extrinsics": "actual robot_state_publisher TF",
                                     "noise": "ideal rendered depth; no hardware noise model"}})
    (run / "runtime.json").write_text(json.dumps(runtime, indent=2) + "\n")


def add_depth_display(config):
    base = yaml.safe_load(config)
    base["Visualization Manager"]["Displays"].append({
        "Class": "rviz_default_plugins/PointCloud2", "Name": "Actual 4m depth camera points",
        "Enabled": True, "Topic": {"Value": "/depth/points", "Reliability Policy": "Best Effort",
                                   "Durability Policy": "Volatile", "Depth": 1},
        "Style": "Points", "Size (Pixels)": 2, "Position Transformer": "XYZ",
        "Color Transformer": "FlatColor", "Color": "255; 180; 40",
    })
    return yaml.safe_dump(base, sort_keys=False)
