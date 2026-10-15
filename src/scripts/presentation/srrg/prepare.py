"""Generate a physically 2D-only robot and honest native point-map display."""

import json
import xml.etree.ElementTree as ET
import yaml
import os


def configure(repo, run, runtime, config):
    tree = ET.parse(repo / "config/robot_profiles/omni-3d-v1/omni_car_lidar3d.urdf")
    robot = tree.getroot()
    for element in list(robot):
        if (
            element.get("name") in ("lidar_3d_link", "lidar_3d_joint")
            or element.get("reference") == "lidar_3d_link"
        ):
            robot.remove(element)
    urdf = run / "srrg-2d.urdf"
    tree.write(urdf, encoding="unicode", xml_declaration=True)
    bridge = yaml.safe_load((repo / "config/robot_profiles/omni-3d-v1/bridge_sensors.yaml").read_text())
    bridge = [e for e in bridge if e["ros_topic_name"] != "/points"]
    bridge_path = run / "srrg-bridge.yaml"
    bridge_path.write_text(yaml.safe_dump(bridge, sort_keys=False))
    runtime.update(
        urdf=str(urdf), bridge_config=str(bridge_path), sensor_arm="2D lidar + wheel odometry; no 3D lidar"
    )
    runtime["srrg_graph_merge"] = False
    if runtime["scene"] == "large-change" and os.environ.get("SRRG_STATIC_PRIOR"):
        runtime["srrg_prior"] = os.environ["SRRG_STATIC_PRIOR"]
    if runtime["scene"] == "large-change" and "srrg_prior" not in runtime:
        marker = repo / ".cache/presentation/srrg-static-prior-latest.json"
        if not marker.is_file():
            raise FileNotFoundError(
                "Run SRRG static mapping and export its native prior before the changed-world session"
            )
        runtime["srrg_prior"] = json.loads(marker.read_text())["path"]
    (run / "runtime.json").write_text(json.dumps(runtime, indent=2) + "\n")
    conf = yaml.safe_load(config)
    vis = conf["Visualization Manager"]
    vis["Displays"] = [
        d
        for d in vis["Displays"]
        if d["Class"] not in ("rviz_default_plugins/Map", "rviz_default_plugins/PointCloud2")
    ]
    for d in vis["Displays"]:
        if d["Class"] == "rviz_default_plugins/LaserScan":
            d["Topic"]["Value"] = "/srrg/scan_used"
    for label, topic, color, size in [
        ("Raw scan accumulation (same estimated trajectory)", "/srrg/raw", "160; 160; 160", 2),
        ("Author SRRG maintained point map", "/srrg/clean", "40; 160; 255", 3),
    ]:
        vis["Displays"].append(
            {
                "Class": "rviz_default_plugins/PointCloud2",
                "Name": label,
                "Enabled": True,
                "Topic": {
                    "Value": topic,
                    "Reliability Policy": "Reliable",
                    "Durability Policy": "Volatile",
                    "Depth": 1,
                },
                "Style": "Points",
                "Size (Pixels)": size,
                "Color Transformer": "FlatColor",
                "Color": color,
                "Position Transformer": "XYZ",
            }
        )
    view = vis["Views"]["Current"]
    view["X"] = 7.15 if runtime["scene"] == "corridor" else 7.5
    view["Y"] = -3.1 if runtime["scene"] == "corridor" else 4.5
    view["Scale"] = 40
    return yaml.safe_dump(conf, sort_keys=False)
