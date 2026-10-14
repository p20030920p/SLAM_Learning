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
runtime = {"world": str(world_path), "spawn": spawn, "scene": scene,
           "world_sha256": hashlib.sha256(world_path.read_bytes()).hexdigest(),
           "initial_offset": initial_offset, "scan_restore_after_s": 50.0 if scene == "corridor" else None}
(run / "runtime.json").write_text(json.dumps(runtime, indent=2)+"\n")
cases = {}
if mode == "localization":
    marker = repo / ".cache/presentation" / f"maps-{mapping_scene}-latest.json"
    fallback = {"static": "robot-static", "dynamic": "robot-dynamic", "corridor": "robot-degradation"}[mapping_scene]
    maps = Path(json.loads(marker.read_text())["path"]) if marker.exists() else repo / f"results/reference/{fallback}/maps"
    if scene == "corridor":
        processing = json.loads((maps / "record.json").read_text())
        if processing.get("world_sha256") != runtime["world_sha256"]:
            raise ValueError("Corridor geometry changed: record mapping-corridor A and rebuild maps first")
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
    if "-ndt-" in flow or "-gicp-" in flow:
        algorithm = "NDT_OMP" if "-ndt-" in flow else "GICP"
        name = "ndt" if algorithm == "NDT_OMP" else "gicp"
        pcd = maps / "raw-map.pcd"
        if not pcd.is_file():
            raise FileNotFoundError("Native 3D map missing; process mapping A first: " + str(pcd))
        cases = {name: {**cases["raw"], "localizer": algorithm, "map_pcd": str(pcd),
                        "pose_topic": f"/{name}/pcl_pose", "native_map_odom_tf": True}}
    if "-3d-" in flow:
        from prepare_3d import configure
        cases = configure(cases, maps, run, scene)
(run / "cases.json").write_text(json.dumps(cases, indent=2) + "\n")
config = (repo / "config/presentation/live_base.rviz").read_text()
if mode == "localization":
    config = config.replace("Value: /map\n", "Value: /raw/map\n")
    map_yaml = Path(next(iter(cases.values()))["map_yaml"])
    settings = map_yaml.read_text()
    origin = [float(item) for item in re.search(r"origin:\s*\[([^]]+)\]", settings).group(1).split(",")]
    resolution = float(re.search(r"resolution:\s*([\d.]+)", settings).group(1))
    dimensions = re.match(rb"P5\s+(\d+)\s+(\d+)", map_yaml.with_name("map.pgm").read_bytes()[:512])
    width, height = [float(item) * resolution for item in dimensions.groups()]
    centre_x, centre_y = origin[0] + width / 2, origin[1] + height / 2
    scale = min(55.0, 840 / width, 590 / height)
    config = config.replace("X: 0\n", f"X: {centre_x}\n").replace("Y: 0\n", f"Y: {centre_y}\n")
    config = config.replace("Scale: 55", f"Scale: {scale}")
    config = config.replace("slam_toolbox map (live)", "Raw map + common AMCL (live)")
else:
    # slam_toolbox's map origin follows the initial odometry frame, not world.
    config = config.replace("X: 0\n", "X: 3.0\n").replace("Y: 0\n", "Y: -2.0\n")
if scene == "corridor":
    if mode == "mapping":
        config = config.replace("X: 3.0\n", "X: 0.0\n").replace("Y: -2.0\n", "Y: 0.0\n")
    config = config.replace("Scale: 55", "Scale: 25")
if "-ndt-" in flow or "-gicp-" in flow:
    name = next(iter(cases))
    config = config.replace("Value: /raw/map\n", f"Value: /{name}/map\n")
    config = config.replace("Raw map + common AMCL (live)", cases[name]["localizer"] + " 3D fixed-map localization")
    additions = f'''    - Class: rviz_default_plugins/PoseWithCovariance
      Name: {cases[name]["localizer"]} native pose
      Enabled: true
      Topic:
        Value: /{name}/pcl_pose
      Color: 60; 180; 255
      Shape: Arrow
    - Class: rviz_default_plugins/Path
      Name: {cases[name]["localizer"]} native trajectory
      Enabled: true
      Topic:
        Value: /{name}/path
      Color: 60; 180; 255
      Line Width: 0.05
    - Class: rviz_default_plugins/PointCloud2
      Name: Frozen 3D prior map
      Enabled: true
      Topic:
        Value: /{name}/initial_map
        Reliability Policy: Reliable
        Durability Policy: Transient Local
        Depth: 1
      Style: Points
      Size (Pixels): 1
      Color Transformer: FlatColor
      Color: 170; 185; 200
      Position Transformer: XYZ
'''
    config = config.replace("  Global Options:\n", additions + "  Global Options:\n")
(run / "live.rviz").write_text(config)
if "-3d-" in flow:
    from prepare_3d import views as prepare_3d_views
    prepare_3d_views(config, cases, run, scene)
elif os.environ.get("PRESENTATION_MULTI_VIEW") == "true" and mode == "localization":
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
camera.text = "7.15 -3.1 27 0 1.5707963267948966 -1.5707963267948966" if scene == "corridor" else "7.5 4.5 22 0 1.5707963267948966 0"
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
if "-ndt-" in flow or "-gicp-" in flow:
    manifest["input_to_localizers"] = "live 3D /points, wheel odometry and frozen Raw 3D prior map"
    manifest["scope"] = "3D fixed-map scan registration; no new map update, IMU or deskew claim"
if "-3d-" in flow:
    manifest["input_to_localizers"] = "same live 3D point clouds and wheel odometry; Raw/DUFOMap/BeautyMap frozen 3D maps; no truth input"
    manifest["scope"] = "3D map cleaning with provided mapping-A poses and native GICP localization in fresh B; no full 3D SLAM or online map-update claim"
(run / "session.json").write_text(json.dumps(manifest, indent=2) + "\n")
print(json.dumps(manifest, indent=2), flush=True)
