"""A disclosed observation adapter, not a localization or recovery algorithm."""
from __future__ import annotations

import copy
import json
import math
import sys
from pathlib import Path

import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import LaserScan


class ScanStress(Node):
    def __init__(self, run):
        super().__init__("presentation_scan_stress")
        self.set_parameters([rclpy.parameter.Parameter("use_sim_time", value=True)])
        self.run, self.started, self.phase, self.count = run, None, None, 0
        self.pub = self.create_publisher(LaserScan, "/scan_degraded", qos_profile_sensor_data)
        self.create_subscription(LaserScan, "/scan", self.on_scan, qos_profile_sensor_data)
        self.log = (run / "scan-stress.jsonl").open("w")

    def on_scan(self, msg):
        stamp = msg.header.stamp.sec + msg.header.stamp.nanosec*1e-9
        if self.started is None and (self.run / "recording.started").exists():
            self.started = stamp
        elapsed = stamp-self.started if self.started is not None else 0.0
        phase = "limited" if elapsed < 50 else "restored"
        output = copy.deepcopy(msg)
        if phase == "limited":
            target = np.linspace(-2*math.pi/3, 2*math.pi/3, 72)
            ids = np.rint((target-msg.angle_min)/msg.angle_increment).astype(int)
            ids = np.clip(ids, 0, len(msg.ranges)-1)
            values = np.asarray(msg.ranges)[ids]
            output.ranges = np.where(np.isfinite(values) & (values <= 3.5), values, np.inf).astype(float).tolist()
            output.intensities = []
            output.angle_min, output.angle_max = float(target[0]), float(target[-1])
            output.angle_increment = float(target[1]-target[0])
            output.range_max = 3.5
            output.time_increment = 0.0
        record = {"stamp_s": stamp, "elapsed_s": elapsed, "phase": phase,
                  "beams": len(output.ranges), "range_max_m": output.range_max,
                  "angle_span_deg": math.degrees(output.angle_max-output.angle_min),
                  "finite_returns": int(np.isfinite(output.ranges).sum())}
        self.log.write(json.dumps(record)+"\n")
        self.log.flush()
        if phase != self.phase:
            self.phase = phase
            print("OBSERVATION EVENT: "+json.dumps(record), flush=True)
        self.pub.publish(output)


def main():
    rclpy.init()
    node = ScanStress(Path(sys.argv[1]))
    try:
        rclpy.spin(node)
    finally:
        node.log.close()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
