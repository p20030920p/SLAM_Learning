"""Rerun native AMCL on the identical recorded B bag, without a simulator."""
import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import threading
import time

import numpy as np
import rclpy
from rclpy.executors import SingleThreadedExecutor
from rclpy.qos import QoSProfile, DurabilityPolicy
from rclpy.serialization import deserialize_message
from rosidl_runtime_py.utilities import get_message
from geometry_msgs.msg import PoseWithCovarianceStamped
from lifecycle_msgs.srv import GetState
from rosgraph_msgs.msg import Clock
import rosbag2_py

from h1_revision import ROOT, OLD, SUITE, METHODS, read, write, sha
from score_direction_time_grid import score


def linux_path(text):
    text = text.replace("\\", "/")
    return Path("/mnt/" + text[0].lower() + text[2:]) if text[1:3] == ":/" else Path(text)


def run(scene, trial, rate):
    out = SUITE / (scene + "-replay") / ("trial-" + str(trial))
    assert not out.exists(), "Preserve completed/failed replay evidence"
    out.mkdir(parents=True)
    original = read(OLD / (scene + "-B/record.json"))
    source_run = linux_path(original["source_run"])
    bag = source_run / "input-bag"
    frozen = read(SUITE / (scene + "-A/frozen-before-scoring.json"))["maps"]
    initial = read(OLD / (scene + "-B/cases.json"))["raw"]["initial_pose"]
    cases = {name: {"method": name, "map_yaml": str(SUITE / (scene + "-A/maps") / name / "map.yaml"),
                    "initial_pose": initial} for name in METHODS}
    write(out / "cases.json", cases)
    node = None
    process = None
    rclpy.init()
    node = rclpy.create_node("h1_exact_B_replay")
    executor = SingleThreadedExecutor()
    executor.add_node(node)
    thread = threading.Thread(target=executor.spin, daemon=True)
    thread.start()
    poses = {name: [] for name in METHODS}
    def receive(name, msg):
        pose = msg.pose.pose
        q = pose.orientation
        poses[name].append([msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9,
                            pose.position.x, pose.position.y,
                            math.atan2(2*(q.w*q.z+q.x*q.y), 1-2*(q.y*q.y+q.z*q.z))])
    for name in METHODS:
        node.create_subscription(PoseWithCovarianceStamped, "/" + name + "/amcl_pose",
                                 lambda msg, name=name: receive(name, msg), 100)
    reader = rosbag2_py.SequentialReader()
    reader.open(rosbag2_py.StorageOptions(uri=str(bag), storage_id="mcap"), rosbag2_py.ConverterOptions("", ""))
    selected = {"/scan", "/tf", "/tf_static", "/clock", "/omni_drive_controller/odom"}
    types = {t.name: get_message(t.type) for t in reader.get_all_topics_and_types() if t.name in selected}
    pubs = {name: node.create_publisher(cls, name, QoSProfile(depth=100,
            durability=DurabilityPolicy.TRANSIENT_LOCAL if name == "/tf_static" else DurabilityPolicy.VOLATILE))
            for name, cls in types.items()}
    pubs["/clock"].publish(Clock())
    log = (out / "native-amcl.log").open("w")
    process = subprocess.Popen(["ros2", "launch", str(Path(__file__).with_name("localization.launch.py")),
                               "cases_file:=" + str(out / "cases.json")], stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    try:
        clients = {name: node.create_client(GetState, "/" + name + "/amcl/get_state") for name in METHODS}
        deadline = time.monotonic() + 50
        active = set()
        while len(active) != len(METHODS):
            if time.monotonic() > deadline or process.poll() is not None:
                raise RuntimeError("Native AMCL did not activate")
            for name, client in clients.items():
                if name in active or not client.service_is_ready():
                    continue
                future = client.call_async(GetState.Request())
                wait = time.monotonic() + .5
                while not future.done() and time.monotonic() < wait:
                    time.sleep(.01)
                if future.done() and future.result().current_state.id == 3:
                    active.add(name)
            time.sleep(.1)
        time.sleep(2)
        print(f"REPLAY B {scene} trial {trial}: all three AMCL nodes active, rate={rate}", flush=True)
        start = time.monotonic()
        first = None
        scan_hash = hashlib.sha256()
        scans = 0
        while reader.has_next():
            topic, data, stamp = reader.read_next()
            if topic not in selected:
                continue
            if first is None:
                first = stamp
            wait = start + (stamp-first)*1e-9/rate - time.monotonic()
            if wait > 0:
                time.sleep(wait)
            msg = deserialize_message(data, types[topic])
            if topic in ("/tf", "/tf_static"):
                msg.transforms = [t for t in msg.transforms if t.header.frame_id != "map"]
            pubs[topic].publish(msg)
            if topic == "/scan":
                scan_hash.update(data)
                scans += 1
                if scans % 150 == 0:
                    print(f"REPLAY B {scene}: published {scans} scans", flush=True)
        time.sleep(2)
    finally:
        if process and process.poll() is None:
            os.killpg(process.pid, signal.SIGINT)
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGTERM)
        log.close()
        executor.shutdown()
        node.destroy_node()
        rclpy.shutdown()
        thread.join(timeout=2)
    for name, values in poses.items():
        assert len(values) > 50, (name, len(values))
        with (out / (name + "-samples.csv")).open("w") as stream:
            writer = csv.writer(stream)
            writer.writerow(["stamp_s", "estimate_x", "estimate_y", "estimate_yaw"])
            writer.writerows(sorted(values))
    # Evaluation starts only after all native estimates have been produced.
    (out / "truth.jsonl").write_bytes((OLD / (scene + "-B/truth.jsonl")).read_bytes())
    write(out / "metrics.json", {"cases": cases, "recording_interval_sim_s": read(OLD / (scene + "-B/metrics.json"))["recording_interval_sim_s"]})
    score(out)
    for name, expected in frozen.items():
        assert sha(SUITE / (scene + "-A") / name) == expected
    write(out / "record.json", {"status": "executed", "kind": "native_AMCL_fixed_B_input_replay",
          "bag_sha256": {p.name: sha(p) for p in bag.glob("*.mcap")}, "scan_messages": scans,
          "scan_bytes_sha256": scan_hash.hexdigest(), "rate": rate, "truth_to_AMCL": False,
          "frozen_maps_unchanged": True, "native_pose_counts": {k: len(v) for k, v in poses.items()},
          "AMCL_parameters": "Unchanged localization.launch.py; three separate native AMCL processes.",
          "scope": "Same measured independent B as historical experiment; reprocessing, not a new acquisition. Repeat trials assess replay reproducibility, not independent statistical trials."})
    print(json.dumps({name: data["common"]["rmse_m"]*100 for name, data in read(out / "time-grid-score.json")["methods"].items()}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scene", choices=("static", "dynamic"))
    parser.add_argument("--trial", type=int, default=1)
    parser.add_argument("--rate", type=float, default=2.)
    args = parser.parse_args()
    run(args.scene, args.trial, args.rate)
