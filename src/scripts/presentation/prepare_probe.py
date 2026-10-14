"""Freeze the matched ablation cases and a single native comparison RViz view."""
import hashlib
import json
import shutil
from pathlib import Path

import numpy as np
import yaml


LABELS = {
    "plain": ("Plain ICP", "245; 90; 90"),
    "guard": ("H1 Robust + odometry", "240; 210; 60"),
    "depth": ("H2 Guard + depth", "255; 150; 45"),
    "search": ("H3 Lidar-only search", "210; 100; 255"),
    "recover": ("H3 Depth + search", "75; 235; 160"),
    "native": ("Native AMCL / GICP", "70; 165; 255"),
}


def configure(repo, run, runtime):
    import sys
    sys.path.insert(0, str(repo / "src"))
    from slam_learning.runtime.recovery_probe import PARAMETERS
    scene = runtime["scene"]
    mapping = "static" if scene == "large-change" else scene
    marker = repo / f".cache/presentation/probe-maps-{mapping}-latest.json"
    maps = Path(json.loads(marker.read_text())["path"])
    source = json.loads((maps / "record.json").read_text())
    if scene != "large-change" and source["world_sha256"] != runtime["world_sha256"]:
        raise ValueError("Probe mapping A and localization B worlds differ")
    dimension = "2d" if runtime["sensor_arm"].startswith("2D") else "3d"
    lidar = maps / ("lidar2d" if dimension == "2d" else "lidar3d")
    points = np.load(lidar / "points.npy", allow_pickle=False).astype("<f4")
    pcd = lidar / "map-3d.pcd"
    header = ("# .PCD v0.7\nVERSION 0.7\nFIELDS x y z\nSIZE 4 4 4\nTYPE F F F\n"
              f"COUNT 1 1 1\nWIDTH {len(points)}\nHEIGHT 1\nVIEWPOINT 0 0 0 1 0 0 0\nPOINTS {len(points)}\nDATA binary\n").encode()
    pcd.write_bytes(header + points.tobytes())
    initial = np.array(runtime["spawn"]) + np.array(runtime["initial_offset"])
    common = {"dimension": dimension, "map_yaml": str(lidar / "map.yaml"), "mapping_scene": mapping,
              "initial_pose": dict(zip(("x", "y", "yaw"), initial.tolist())),
              "native_map_odom_tf": True, "broadcast_tf": False, "map_pcd": str(pcd)}
    common["initial_pose"]["z"] = 0.0
    cases = {name: {**common, "method": name, "localizer": "SE2 hypothesis probe",
                    "pose_topic": f"/{name}/probe_pose"} for name in LABELS if name != "native"}
    native = {**common, "method": "native", "localizer": "AMCL" if dimension == "2d" else "GICP",
              "pose_topic": "/native/amcl_pose" if dimension == "2d" else "/native/pcl_pose"}
    limited = scene in ("corridor", "height-corridor")
    native["scan_topic"] = "/scan_degraded" if limited else "/scan"
    native["cloud_topic"] = "/points_degraded" if limited else "/points"
    cases["native"] = native
    (run / "native-cases.json").write_text(json.dumps({"native": native}, indent=2) + "\n")
    config = {"dimension": dimension, "maps": str(maps), "lidar_map": str(lidar / "points.npy"),
              "depth_map": str(maps / "depth.npy"), "parameters": PARAMETERS,
              "scan_topic": native["scan_topic"], "cloud_topic": native["cloud_topic"],
              "truth_input_to_localizers": False, "pose_dof": "x/y/yaw; z=roll=pitch=0",
              "depth_time_alignment": "nearest <=0.12s; wheel-odometry transform from depth stamp to lidar stamp; two callback threads",
              "mapping_A_record_sha256": hashlib.sha256((maps / "record.json").read_bytes()).hexdigest(),
              "variants": {"plain": {"guarded": False, "depth": False, "recovery": False},
                           "guard": {"guarded": True, "depth": False, "recovery": False},
                           "depth": {"guarded": True, "depth": True, "recovery": False},
                           "search": {"guarded": True, "depth": False, "recovery": True},
                           "recover": {"guarded": True, "depth": True, "recovery": True}}}
    frozen = run / "probe-source"
    frozen.mkdir()
    sources = [repo / "src/slam_learning/runtime/recovery_probe.py", repo / "src/scripts/presentation/probe_localizer.py"]
    for path in sources:
        shutil.copyfile(path, frozen / path.name)
    config["source_sha256"] = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in sources}
    (run / "probe-config.json").write_text(json.dumps(config, indent=2) + "\n")
    return cases


def views(config, cases, run, runtime):
    base = yaml.safe_load(config)
    displays = base["Visualization Manager"]["Displays"]
    displays[:] = [display for display in displays if display["Class"] not in
                   ("rviz_default_plugins/Map", "rviz_default_plugins/LaserScan", "rviz_default_plugins/PointCloud2")]
    displays.append({"Class": "rviz_default_plugins/PointCloud2", "Name": "Frozen lidar map A",
                     "Enabled": True, "Topic": {"Value": "/probe/map_points", "Reliability Policy": "Reliable",
                                                "Durability Policy": "Transient Local", "Depth": 1},
                     "Color Transformer": "FlatColor", "Color": "155; 165; 180", "Position Transformer": "XYZ",
                     "Style": "Points", "Size (Pixels)": 2})
    displays.append({"Class": "rviz_default_plugins/PointCloud2", "Name": "Actual depth (aligned by green estimate)",
                     "Enabled": True, "Topic": {"Value": "/depth/points", "Reliability Policy": "Best Effort", "Depth": 1},
                     "Color Transformer": "FlatColor", "Color": "255; 200; 60", "Position Transformer": "XYZ",
                     "Style": "Points", "Size (Pixels)": 1})
    for name, (label, colour) in LABELS.items():
        displays.extend([
            {"Class": "rviz_default_plugins/Path", "Name": label + " path", "Enabled": True,
             "Topic": {"Value": f"/{name}/probe_path", "Depth": 1}, "Color": colour, "Line Width": .035},
            {"Class": "rviz_default_plugins/PoseWithCovariance", "Name": label, "Enabled": True,
             "Topic": {"Value": cases[name]["pose_topic"], "Depth": 1}, "Color": colour,
             "Shape": "Arrow", "Shaft Length": .4, "Head Length": .15},
        ])
    initial = cases["recover"]["initial_pose"]
    if cases["recover"]["dimension"] == "3d":
        base["Visualization Manager"]["Views"]["Current"] = {
            "Class": "rviz_default_plugins/Orbit", "Name": "3D input, planar robot hypotheses", "Target Frame": "map",
            "Distance": 18., "Pitch": .8, "Yaw": .8,
            "Focal Point": {"X": initial["x"] - 1, "Y": initial["y"] - 1, "Z": .5}}
    base["Window Geometry"].update({"X": 960, "Y": 0, "Width": 960, "Height": 720})
    path = run / "view-recover.rviz"
    path.write_text(yaml.safe_dump(base, sort_keys=False))
    dimension = cases["recover"]["dimension"].upper()
    (run / "views.json").write_text(json.dumps({"recover": {
        "method": "comparison", "dimension": dimension.lower(), "title": f"SLAM LIVE - probe {dimension} - RViz2",
        "config": path.name, "map_topic": "/recover/map", "pose_topic": cases["recover"]["pose_topic"],
        "tf_topic": "/recover/view/tf", "scan_topic": "/depth/points",
        "display_scope": "six labelled paths/poses; live depth aligned by recover estimate; no truth displayed"}}, indent=2) + "\n")
