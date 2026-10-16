"""Visible recomputation of the recorded H1 A inputs, with no truth input."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

import numpy as np
import rclpy
from sensor_msgs.msg import PointCloud2
from sensor_msgs_py import point_cloud2
from std_msgs.msg import Header
from visualization_msgs.msg import Marker
import yaml

from h1_revision import ROOT, OLD, SUITE, read, write, sha, METHODS
sys.path.insert(0, str(ROOT / "src"))
from slam_learning.runtime.own_mapping import RayEvidence, transform


def run(scene, refined=False):
    if refined:
        from h1_refined import SUITE, METHODS, process
    else:
        from h1_revision import SUITE, METHODS
        def process(scans, archive):
            grid = RayEvidence()
            for i, scan in enumerate(scans):
                pose = np.asarray(scan["sensor_pose"])
                grid.add(transform(archive[scan["key"]], pose), pose[:2, 2], scan["stamp_s"])
                yield i, grid, grid, pose
    out = SUITE / (scene + "-A")
    source = OLD / (scene + "-A")
    scans = read(source / "own-scans.json")
    archive = np.load(source / "own-inputs.npz")
    bounds = np.load(out / "maps/raw/points.npy")
    center = (bounds.min(axis=0) + bounds.max(axis=0)) / 2
    scale = min(1200 / np.ptp(bounds[:, 0]), 730 / np.ptp(bounds[:, 1])) * .9
    config = yaml.safe_load((ROOT / "config/presentation/live_base.rviz").read_text())
    vis = config["Visualization Manager"]
    vis["Global Options"]["Fixed Frame"] = "map"
    vis["Displays"] = []
    for method, color in (("raw", "175; 175; 175"), ("temporal", "40; 180; 255")):
        vis["Displays"].append({"Class": "rviz_default_plugins/PointCloud2", "Name": method.upper(), "Enabled": True,
            "Topic": {"Value": "/own/" + method, "Reliability Policy": "Reliable", "Durability Policy": "Volatile", "Depth": 1},
            "Style": "Points", "Size (Pixels)": 4, "Color Transformer": "FlatColor", "Color": color, "Position Transformer": "XYZ"})
    vis["Displays"].append({"Class": "rviz_default_plugins/Marker", "Name": "Input replay status", "Enabled": True,
                            "Topic": {"Value": "/own/status", "Reliability Policy": "Reliable", "Depth": 1}})
    vis["Views"]["Current"] = {"Class": "rviz_default_plugins/TopDownOrtho", "Name": "2D A input replay",
                                           "Target Frame": "map", "X": float(center[0]), "Y": float(center[1]), "Scale": float(scale), "Angle": 0}
    config["Window Geometry"].update({"X": 420, "Y": 0, "Width": 1320, "Height": 900})
    path = out / "replay.rviz"
    path.write_text(yaml.safe_dump(config, sort_keys=False))
    rclpy.init()
    node = rclpy.create_node("h1_A_algorithm_replay")
    pubs = {m: node.create_publisher(PointCloud2, "/own/" + m, 1) for m in ("raw", "temporal")}
    status = node.create_publisher(Marker, "/own/status", 1)
    log = (out / "rviz-replay.log").open("w")
    rviz = subprocess.Popen(["rviz2", "-d", str(path), "-t", "H1 MAP REPLAY " + scene + " - RViz2"],
                             stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    try:
        for _ in range(60):
            rclpy.spin_once(node, timeout_sec=.1)
        write(out / "A-replay-ready.json", {"scene": scene, "kind": "native_RViz_input_reprocessing"})
        deadline = time.monotonic() + 90
        while not (out / "A-capture-started").exists():
            if time.monotonic() > deadline or rviz.poll() is not None:
                raise RuntimeError("A screen capture did not start")
            rclpy.spin_once(node, timeout_sec=.05)
        start = time.monotonic()
        # Run the identical mapping procedure at recorded input timing.
        for i, base, aligned, estimate in process(scans, archive):
            scan = scans[i]
            due = start + scan["stamp_s"] - scans[0]["stamp_s"]
            while time.monotonic() < due:
                rclpy.spin_once(node, timeout_sec=max(0., min(.02, due - time.monotonic())))
            if i % 2 == 0 or i == len(scans)-1:
                header = Header(frame_id="map", stamp=node.get_clock().now().to_msg())
                for method, publisher in pubs.items():
                    points = base.points("raw") if method == "raw" else aligned.points("temporal")
                    publisher.publish(point_cloud2.create_cloud_xyz32(header, np.column_stack((points, np.zeros(len(points)))).astype(np.float32)))
                marker = Marker(header=header, ns="status", id=0, type=Marker.TEXT_VIEW_FACING, action=Marker.ADD)
                marker.pose.position.x, marker.pose.position.y = float(center[0]), float(bounds[:,1].max()+.2)
                marker.pose.orientation.w = 1.
                marker.scale.z = .18
                marker.color.r = marker.color.g = marker.color.b = marker.color.a = 1.
                marker.text = f"H1 2D A INPUT REPLAY / {scene.upper()}\nRAW grey | NEW blue | scan {i+1}/{len(scans)}"
                status.publish(marker)
            rclpy.spin_once(node, timeout_sec=.001)
        generated = {"raw": base.points("raw"), "filter_only": base.points("temporal"), "align_only": aligned.points("raw"), "temporal": aligned.points("temporal")} if refined else {method: base.points(method) for method in METHODS}
        for method in METHODS:
            np.testing.assert_array_equal(generated[method], np.load(out / "maps" / method / "points.npy"))
        write(out / "A-replay-finished.json", {"status": "executed", "scans": len(scans), "all_four_maps_reproduced_exactly": True,
                "truth_used": False, "algorithm_sha256": sha(ROOT / "src/slam_learning/runtime/own_mapping.py"), "refined": refined,
                "scope": "Recorded A endpoints + wheel-derived poses reprocessed at original scan timing; actual RViz capture, not new acquisition or saved-result animation."})
        deadline = time.monotonic() + 45
        while not (out / "A-capture-stopped").exists() and time.monotonic() < deadline:
            rclpy.spin_once(node, timeout_sec=.1)
    finally:
        if rviz.poll() is None:
            os.killpg(rviz.pid, signal.SIGINT)
            rviz.wait(timeout=10)
        log.close()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    run(sys.argv[1], "refined" in sys.argv[2:])
