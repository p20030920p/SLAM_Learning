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
if "height-corridor" in flow:
    from probe_sensors import height_control_world
    world_path = height_control_world(world_path, run)
if "-landmark-" in flow:
    from direction_landmarks import landmark_world
    world_path = landmark_world(world_path, run)
spawn = [7.15, -3.1, 0.0] if scene == "corridor" else [8.0727, 7.5312, -1.5708]
initial_offset = [1.0, 0.15, 0.12] if scene == "corridor" else [0.25, 0.15, 0.12]
runtime = {"world": str(world_path), "spawn": spawn, "scene": scene, "flow": flow,
           "world_sha256": hashlib.sha256(world_path.read_bytes()).hexdigest(),
           "initial_offset": initial_offset, "scan_restore_after_s": 50.0 if scene == "corridor" else None}
if "height-corridor" in flow:
    runtime["scene"] = "height-corridor"
    runtime["derived_control"] = "original corridor plus two high geometric blocks; same ground-level corridor, route and initial offset"
(run / "runtime.json").write_text(json.dumps(runtime, indent=2)+"\n")
if "-probe-" in flow:
    from probe_sensors import configure as configure_probe_sensors
    configure_probe_sensors(repo, run, flow, runtime)
cases = {}
native_2d = mode == "localization" and not any(tag in flow for tag in ("-3d-", "-gicp-", "-ndt-", "-probe-"))
if mode == "localization":
    marker_scene = ("landmark-" if "-landmark-" in flow else "") + mapping_scene
    own_scene = "motion" if "motion" in flow else mapping_scene
    marker_name = f"mapping-own-{own_scene}-latest.json" if "-own-" in flow else (f"mapping-srrg-{marker_scene}-latest.json" if native_2d else f"maps-{mapping_scene}-latest.json")
    marker = repo / ".cache/presentation" / marker_name
    fallback = {"static": "robot-static", "dynamic": "robot-dynamic", "corridor": "robot-degradation"}[mapping_scene]
    maps = Path(json.loads(marker.read_text())["path"]) if marker.exists() else repo / f"results/reference/{fallback}/maps"
    if native_2d and not marker.exists():
        maps = repo / f"results/reference/direction-20261016/2d-A-{mapping_scene}"
        if not (maps / "runtime.json").is_file():
            raise FileNotFoundError("Record native SRRG mapping A before localization B")
    if native_2d:
        # Markers are written by Windows capture; normalize them for Linux ROS.
        if ":\\" in str(maps):
            value = str(maps)
            maps = Path("/mnt/" + value[0].lower() + "/" + value[3:].replace("\\", "/"))
        source_runtime = json.loads((maps / "runtime.json").read_text())
        if scene != "large-change" and source_runtime["world_sha256"] != runtime["world_sha256"]:
            raise ValueError("Native 2D mapping world differs from localization world")
        runtime["mapping_source"] = str(maps)
        maps = maps / "maps"
        from srrg.prepare import sensor_profile
        sensor_profile(repo, run, runtime)
        (run / "runtime.json").write_text(json.dumps(runtime, indent=2) + "\n")
    if scene == "corridor" and "-probe-" not in flow and not native_2d:
        processing = json.loads((maps / "record.json").read_text())
        if processing.get("world_sha256") != runtime["world_sha256"]:
            raise ValueError("Corridor geometry changed: record mapping-corridor A and rebuild maps first")
    methods = ("raw", "srrg") if native_2d else ("raw", "dufomap", "beautymap")
    if "-own-" in flow:
        methods = json.loads((maps.parent / "own-finished.json").read_text())["methods"]
    for method in methods:
        path = maps / method / "map.yaml"
        if not path.exists():
            raise FileNotFoundError(path)
        cases[method] = {"method": method, "map_yaml": str(path), "mapping_scene": mapping_scene,
                         "initial_pose": {"x": spawn[0]+initial_offset[0], "y": spawn[1]+initial_offset[1], "z": 0.0, "yaw": spawn[2]+initial_offset[2]}}
    if scene == "corridor":
        for method in methods:
            cases["degraded_"+method] = {**cases[method], "scan_topic": "/scan_degraded"}
    if scene == "dynamic" and not native_2d:
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
    if "-3d-" in flow and "-probe-" not in flow and "-fastlio-" not in flow:
        from prepare_3d import configure
        cases = configure(cases, maps, run, scene)
    if "-fastlio-" in flow:
        from fastlio_fixed_maps import configure as configure_fastlio_maps
        cases = configure_fastlio_maps(repo, run, spawn, initial_offset)
    if "-probe-" in flow:
        from prepare_probe import configure as configure_probe
        cases = configure_probe(repo, run, runtime)
        if "-calibrated-" in flow:
            from prepare_calibrated_probe import configure as configure_calibrated_probe
            cases = configure_calibrated_probe(repo, run, cases)
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
if "-probe-" in flow:
    from probe_sensors import add_depth_display
    config = add_depth_display(config)
if "-srrg-" in flow:
    from srrg.prepare import configure as configure_srrg
    config = configure_srrg(repo, run, runtime, config)
if "-fastlio-" in flow and mode == "mapping":
    from fastlio_study import configure as configure_fastlio
    config = configure_fastlio(repo, run, runtime, config)
if "-own-" in flow and mode == "mapping":
    import yaml
    configured = yaml.safe_load(config)
    vis = configured["Visualization Manager"]
    vis["Global Options"]["Fixed Frame"] = "map"
    vis["Displays"] = []
    own_methods = ("off", "deskew") if "motion" in flow else (("strict", "protected") if scene == "corridor" else ("raw", "temporal"))
    for method, color in zip(own_methods, ("170; 170; 170", "40; 180; 255")):
        vis["Displays"].append({"Class": "rviz_default_plugins/PointCloud2", "Name": "OWN " + method, "Enabled": True,
            "Topic": {"Value": "/own/" + method, "Reliability Policy": "Reliable", "Durability Policy": "Volatile", "Depth": 1},
            "Style": "Points", "Size (Pixels)": 3, "Color Transformer": "FlatColor", "Color": color, "Position Transformer": "XYZ"})
    vis["Views"]["Current"].update(X=7.15 if scene == "corridor" else 7.5, Y=-3.1 if scene == "corridor" else 4.5, Scale=40)
    config = yaml.safe_dump(configured, sort_keys=False)
(run / "live.rviz").write_text(config)
if "-probe-" in flow and mode == "localization":
    from prepare_probe import views as prepare_probe_views
    prepare_probe_views(config, cases, run, runtime)
    if "-calibrated-" in flow:
        from prepare_calibrated_probe import views as calibrated_views
        calibrated_views(run)
elif mode == "localization" and "-3d-" in flow:
    from prepare_3d import views as prepare_3d_views
    prepare_3d_views(config, cases, run, scene)
elif os.environ.get("PRESENTATION_MULTI_VIEW") == "true" and mode == "localization":
    views = {}
    display_methods = [(method, "OWN " + method) for method in methods] if "-own-" in flow else [("raw", "Raw"), ("srrg", "SRRG")]
    for method, label in display_methods:
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
if mode == "localization" and "-3d-" in flow:
    manifest["input_to_localizers"] = "same live 3D point clouds and wheel odometry; Raw/DUFOMap/BeautyMap frozen 3D maps; no truth input"
    manifest["scope"] = "3D map cleaning with provided mapping-A poses and native GICP localization in fresh B; no full 3D SLAM or online map-update claim"
if "-probe-" in flow:
    manifest["robot"] = "Sim2Real omni chassis with " + runtime["sensor_arm"]
    manifest["source_robot_profile"] = "omni-3d-v1 adapted; generated URDF is the authoritative sensor inventory"
    manifest["input_to_localizers"] = "actual lidar, optional 4m depth and wheel odometry; no simulator truth in B"
    manifest["scope"] = "hypothesis prototypes, planar ground-robot pose; 2D arm has no 3D lidar; frozen provided-pose mapping A"
if "-srrg-" in flow:
    manifest["provided_mapping_poses"] = False
    manifest["robot"] = runtime["sensor_arm"]
    manifest["input_to_localizers"] = "actual 2D LaserScan, wheel odometry and measured laser TF; fixed known start anchor only"
    manifest["scope"] = "native author Mapper2D, local projective merger and graph merger; one short session per scene, not full long-term multi-session reproduction"
    manifest["assets"].update({str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in (repo / "src/scripts/presentation/srrg").glob("*") if p.is_file()})
if flow.startswith("mapping-compare-"):
    manifest["scope"] = "provided-pose 3D map cleaning in periodic native batches; 2D view is projection; BeautyMap remains offline"
    manifest["input_to_localizers"] = "none: mapping comparison only; all displayed methods share completed batch inputs"
if "-own-" in flow:
    manifest["provided_mapping_poses"] = False
    manifest["scope"] = "Project-written geometric prototypes, wheel odometry plus configured start anchor; no truth in algorithms; not a published-method reproduction"
    manifest["input_to_localizers"] = "2D scans and wheel odometry, project-written frozen maps, identical native AMCL"
    core = repo / "src/slam_learning/runtime/own_mapping.py"
    manifest["assets"][str(core)] = hashlib.sha256(core.read_bytes()).hexdigest()
(run / "session.json").write_text(json.dumps(manifest, indent=2) + "\n")
print(json.dumps(manifest, indent=2), flush=True)
