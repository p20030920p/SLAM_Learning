"""Three frozen author-derived 3D maps with the same installed GICP configuration."""
import hashlib
import json
import os
import numpy as np
import yaml


def configure(cases, maps, run, scene):
    selected = {}
    for method in ("raw", "dufomap", "beautymap"):
        source = maps / method / "points.npy"
        points = np.load(source, allow_pickle=False).astype("<f4")
        pcd = maps / method / "map-3d.pcd"
        # Rebuild only this derived file if the measured points changed.
        header = ("# .PCD v0.7\nVERSION 0.7\nFIELDS x y z\nSIZE 4 4 4\nTYPE F F F\n"
                  f"COUNT 1 1 1\nWIDTH {len(points)}\nHEIGHT 1\nVIEWPOINT 0 0 0 1 0 0 0\n"
                  f"POINTS {len(points)}\nDATA binary\n").encode()
        payload = header + points.tobytes()
        if not pcd.exists() or hashlib.sha256(pcd.read_bytes()).digest() != hashlib.sha256(payload).digest():
            pcd.write_bytes(payload)
        selected[method] = {
            **cases[method], "dimension": "3d", "localizer": "GICP", "map_pcd": str(pcd),
            "pose_topic": f"/{method}/pcl_pose", "native_map_odom_tf": True, "broadcast_tf": False,
            "cloud_topic": "/points_degraded" if scene == "corridor" else "/points",
            "map_points_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        }
    if scene == "corridor" and os.environ.get("PRESENTATION_VIEW_PROFILE") != "3d":
        for method in ("raw", "dufomap", "beautymap"):
            selected["full_" + method] = {
                **selected[method], "cloud_topic": "/points", "pose_topic": f"/full_{method}/pcl_pose"
            }
    return selected


def views(config_text, cases, run, scene):
    base = yaml.safe_load(config_text)
    displays = base["Visualization Manager"]["Displays"]
    displays[:] = [display for display in displays if display["Class"] not in
                   ("rviz_default_plugins/Map", "rviz_default_plugins/LaserScan")]
    result = {}
    for index, method in enumerate(name for name in cases if not name.startswith("full_")):
        config = yaml.safe_load(yaml.safe_dump(base))
        case = cases[method]
        own = config["Visualization Manager"]["Displays"]
        own[:] = [display for display in own if display["Class"] == "rviz_default_plugins/Grid"]
        own.append({"Class":"rviz_default_plugins/PointCloud2", "Name":"CURRENT SCAN - GREEN", "Enabled":True,
                    "Topic":{"Value":case["cloud_topic"],"Reliability Policy":"Best Effort","Durability Policy":"Volatile","Depth":5},
                    "Style":"Points","Size (Pixels)":3,"Color Transformer":"FlatColor","Color":"55; 255; 120",
                    "Position Transformer":"XYZ","Decay Time":.15,"Alpha":1.0})
        for cls, name, topic in [
            ("PointCloud2", "Frozen " + method + " 3D map", f"/{method}/initial_map"),
            ("MarkerArray", "GICP POSE - PINK", f"/{method}/view/markers"),
            ("Path", "Native GICP trajectory", f"/{method}/view/path"),
        ]:
            display = {"Class": "rviz_default_plugins/" + cls, "Name": name, "Enabled": True,
                       "Topic": {"Value": topic, "Reliability Policy": "Reliable",
                                 "Durability Policy": "Transient Local" if cls == "PointCloud2" else "Volatile",
                                 "Depth": 1}, "Color": "80; 180; 255"}
            if cls == "PointCloud2":
                display.update({"Style": "Points", "Size (Pixels)": 2, "Color Transformer": "FlatColor",
                                "Color":"205; 210; 220", "Alpha":.70, "Position Transformer": "XYZ"})
            if cls == "Path":
                display.update({"Line Width":.10,"Line Style":"Billboards","Color":"40; 210; 255"})
            own.append(display)
        # An oblique view visibly preserves height rather than showing another 2D projection.
        position = case["initial_pose"]
        config["Visualization Manager"]["Views"]["Current"] = {
            "Class": "rviz_default_plugins/Orbit", "Name": "3D map comparison", "Target Frame": "map",
            "Distance": 11.5 if scene != "corridor" else 15.0, "Pitch": .85, "Yaw": .8,
            "Focal Point": {"X": 7.5 if scene != "corridor" else 7.15, "Y": 4.5 if scene != "corridor" else -3.1, "Z": .5},
        }
        config["Window Geometry"].update({"X": 480 + index * 20, "Y": 0, "Width": 1320, "Height": 900})
        path = run / f"view-{method}.rviz"
        path.write_text(yaml.safe_dump(config, sort_keys=False))
        # Quoted/unquoted yaml values are both accepted by the evidence checker.
        result[method] = {"method": method, "dimension": "3d", "title": f"SLAM LIVE - 3D {method} - RViz2",
                          "config": path.name, "map_topic": f"/{method}/initial_map", "pose_topic": case["pose_topic"],
                          "tf_topic": f"/{method}/view/tf", "scan_topic": case["cloud_topic"]}
    (run / "views.json").write_text(json.dumps(result, indent=2) + "\n")


def acquisition(config_text, scene):
    config=yaml.safe_load(config_text)
    vis=config["Visualization Manager"]
    vis["Global Options"]["Fixed Frame"]="odom"
    vis["Displays"]=[display for display in vis["Displays"] if display["Class"] in
                     ("rviz_default_plugins/Grid", "rviz_default_plugins/PointCloud2", "rviz_default_plugins/Odometry")]
    for display in vis["Displays"]:
        if display["Class"]=="rviz_default_plugins/PointCloud2":
            display.update({"Name":"LIVE 16-CHANNEL 3D POINTS", "Decay Time":2.0,"Size (Pixels)":2})
        if display["Class"]=="rviz_default_plugins/Odometry":
            display["Color"]="255; 50; 180"
    vis["Views"]["Current"]={"Class":"rviz_default_plugins/Orbit", "Name":"LIVE 3D ACQUISITION", "Target Frame":"odom",
        "Distance":11.5 if scene!="corridor" else 14.0,"Pitch":.8,"Yaw":.8,
        "Focal Point":{"X":1.5 if scene!="corridor" else 0.0,"Y":0.0,"Z":.5}}
    config["Window Geometry"].update({"X":480,"Y":0,"Width":1320,"Height":900})
    return yaml.safe_dump(config,sort_keys=False)
