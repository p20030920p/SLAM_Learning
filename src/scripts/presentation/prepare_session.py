"""Freeze settings, source hashes and genuine application display layouts."""

from __future__ import annotations

import hashlib
import json
import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path

repo = Path(os.environ["PRESENTATION_REPO"])
run = Path(os.environ["PRESENTATION_RUN"])
flow = os.environ["PRESENTATION_FLOW"]
root = Path(os.environ["S2R_REPO"])
mode = "localization" if flow.startswith("localization-") else "mapping"
scene = "dynamic" if "dynamic" in flow else "static"
if "corridor" in flow or "degradation" in flow:
    scene = "corridor"
if "large-change" in flow:
    scene = "large-change"
mapping_scene = "static" if scene == "large-change" else scene
level = {"static": "S1_static", "dynamic": "S2_dynamic", "large-change": "S3_large_change", "corridor": "S4_degradation"}[scene]
world_path = repo / f"config/presentation/worlds/{level}.world"
spawn = [7.15, -3.1, 0.0] if scene == "corridor" else [8.0727, 7.5312, -1.5708]
initial_offset = [1.0, 0.15, 0.12] if scene == "corridor" else [0.25, 0.15, 0.12]
if scene == "corridor":
    # Matched-map test: remove the arena mesh rather than confound old-map mismatch.
    world = ET.parse(world_path)
    body = world.find("world")
    for include in list(body.findall("include")):
        body.remove(include)
    for wall in body.findall("model"):
        if wall.get("name", "").startswith("s4_corridor_wall"):
            for size in wall.findall(".//box/size"):
                size.text = "20.0 0.16 1.5"
            pose = wall.find("pose")
            values = pose.text.split()
            values[2] = "0.75"
            pose.text = " ".join(values)
    for name, x in [("west", -2.93), ("east", 17.23)]:
        body.append(ET.fromstring(f'<model name="corridor_end_{name}"><static>true</static><pose>{x} -3.1 0.75 0 0 0</pose><link name="link"><collision name="collision"><geometry><box><size>0.16 3.16 1.5</size></box></geometry></collision><visual name="visual"><geometry><box><size>0.16 3.16 1.5</size></box></geometry><material><ambient>0.25 0.35 0.55 1</ambient><diffuse>0.25 0.35 0.55 1</diffuse></material></visual></link></model>'))
    world_path = run / "corridor.world"
    world.write(world_path, encoding="utf-8", xml_declaration=True)
runtime = {"world": str(world_path), "spawn": spawn, "scene": scene,
           "initial_offset": initial_offset, "scan_restore_after_s": 50.0 if scene == "corridor" else None}
(run / "runtime.json").write_text(json.dumps(runtime, indent=2)+"\n")
cases = {}
if mode == "localization":
    marker = repo / ".cache/presentation" / f"maps-{mapping_scene}-latest.json"
    fallback = {"static": "robot-static", "dynamic": "robot-dynamic", "corridor": "robot-degradation"}[mapping_scene]
    maps = Path(json.loads(marker.read_text())["path"]) if marker.exists() else repo / f"results/reference/{fallback}/maps"
    for method in ("raw", "dufomap", "beautymap"):
        path = maps / method / "map.yaml"
        if not path.exists():
            raise FileNotFoundError(path)
        cases[method] = {"method": method, "map_yaml": str(path), "mapping_scene": mapping_scene,
                         "initial_pose": {"x": spawn[0]+initial_offset[0], "y": spawn[1]+initial_offset[1], "z": 0.0, "yaw": spawn[2]+initial_offset[2]}}
    if scene == "corridor":
        for method in ("raw", "dufomap", "beautymap"):
            cases["degraded_"+method] = {**cases[method], "scan_topic": "/scan_degraded"}
    if scene == "dynamic":
        static_marker = repo / ".cache/presentation/maps-static-latest.json"
        if static_marker.exists():
            static_maps = Path(json.loads(static_marker.read_text())["path"])
            for method in ("raw", "dufomap", "beautymap"):
                path = static_maps / method / "map.yaml"
                cases["clean_" + method] = {
                    "method": method,
                    "map_yaml": str(path),
                    "mapping_scene": "static",
                }
(run / "cases.json").write_text(json.dumps(cases, indent=2) + "\n")
config = (repo / "config/presentation/live_base.rviz").read_text()
if mode == "localization":
    config = config.replace("Value: /map\n", "Value: /raw/map\n")
    config = config.replace("X: 0\n", "X: 3.65\n").replace("Y: 0\n", "Y: 1.0\n")
    config = config.replace("slam_toolbox map (live)", "Raw map + common AMCL (live)")
if scene == "corridor":
    config = config.replace("X: 3.65\n", "X: 7.15\n").replace("Y: 1.0\n", "Y: -3.1\n")
    if mode == "mapping":
        config = config.replace("X: 0\n", "X: 0.0\n").replace("Y: 0\n", "Y: 0.0\n")
    config = config.replace("Scale: 35", "Scale: 25")
(run / "live.rviz").write_text(config)
if os.environ.get("PRESENTATION_MULTI_VIEW") == "true" and mode == "localization":
    views = {}
    for method, label in (("raw", "Raw"), ("dufomap", "DUFOMap"), ("beautymap", "BeautyMap")):
        case = "degraded_"+method if scene == "corridor" else method
        own = config.replace("Value: /raw/map\n", f"Value: /{case}/map\n")
        own = own.replace("Raw map + common AMCL (live)", label+" map + AMCL (LIVE)")
        own = own.replace("Value: /scan\n", "Value: "+cases[case].get("scan_topic", "/scan")+"\n")
        additions = f'''    - Class: rviz_default_plugins/PoseWithCovariance
      Name: {label} native AMCL pose
      Enabled: true
      Topic:
        Value: /{case}/amcl_pose
      Color: 60; 180; 255
      Shape: Arrow
    - Class: rviz_default_plugins/Path
      Name: {label} estimated trajectory
      Enabled: true
      Topic:
        Value: /{case}/view/path
      Color: 60; 180; 255
      Line Width: 0.05
    - Class: nav2_rviz_plugins/ParticleCloud
      Name: {label} native AMCL particles
      Enabled: true
      Topic:
        Value: /{case}/particle_cloud
        Reliability Policy: Best Effort
        Durability Policy: Volatile
        Depth: 5
      Color: 250; 210; 50
'''
        own = own.replace("  Global Options:\n", additions+"  Global Options:\n")
        path = run / f"view-{case}.rviz"
        path.write_text(own)
        views[case] = {"method": method, "title": f"SLAM LIVE - {case} - RViz2",
                       "config": path.name, "map_topic": f"/{case}/map", "pose_topic": f"/{case}/amcl_pose",
                       "tf_topic": f"/{case}/view/tf", "scan_topic": cases[case].get("scan_topic", "/scan")}
    (run / "views.json").write_text(json.dumps(views, indent=2)+"\n")
default_gui = Path("/root/.gz/sim/8/gui.config").read_text()
gui = ET.fromstring("<root>" + re.sub(r"<\?xml.*?\?>", "", default_gui) + "</root>")
for plugin in list(gui.findall("plugin")):
    if plugin.get("filename") in ("ComponentInspector", "EntityTree"):
        gui.remove(plugin)
camera = gui.find("plugin[@filename='MinimalScene']/camera_pose")
camera.text = "7.15 -3.1 15 0 1.5707963267948966 0" if scene == "corridor" else "7.5 4.5 13 0 1.5707963267948966 0"
gui.find("window/width").text = "960"
gui.find("window/height").text = "720"
gui.find("window/dialog_on_exit").text = "false"
(run / "gazebo-gui.config").write_text("\n".join(ET.tostring(element, encoding="unicode") for element in gui))
paths = [
    world_path,
    repo / "src/scripts/presentation/patrol_waypoints.py",
    root / "src/race_description/urdf/omni_car_ros2_control.urdf",
    repo / "config/robot_profiles/omni-3d-v1/omni_car_lidar3d.urdf",
]
paths.extend((repo / "src/scripts/presentation").glob("*"))
paths.extend([repo / "demo/presentation.ps1", run / "gazebo-gui.config", run / "live.rviz"])
manifest = {
    "flow": flow,
    "mode": mode,
    "scene": scene,
    "robot": "Sim2Real omni-3d-v1",
    "source_commit": "53324d40def0dd753b4a99021b8fe596955a1ecd",
    "world_scope": "local scenario adaptation; robot/source assets pinned separately",
    "capture": "actual Windows Gazebo Sim, RViz2 and Windows Terminal windows",
    "provided_mapping_poses": mode == "mapping",
    "truth_input_to_localizers": False,
    "input_to_localizers": "same live /scan and wheel odometry, different frozen author-derived maps",
    "initial_pose_offset_m_rad": initial_offset,
    "runtime": runtime,
    "assets": {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths if path.is_file()},
    "cases": cases,
}
(run / "session.json").write_text(json.dumps(manifest, indent=2) + "\n")
print(json.dumps(manifest, indent=2), flush=True)
