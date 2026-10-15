#!/usr/bin/env python3
"""Grab one frame from an image topic and report simple statistics.

Used as the "is the overview camera actually rendering?" gate before recording.
A flat frame (std ~ 0) means no render target; that is the failure this guards
against, so the statistics are the point, not the PNG.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSHistoryPolicy, QoSProfile, QoSReliabilityPolicy
from sensor_msgs.msg import Image as RosImage

sys.path.insert(0, str(Path(__file__).resolve().parent))
from image_utils import describe, to_pil  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("out", help="path of the PNG to write")
    ap.add_argument("timeout", nargs="?", type=float, default=20.0)
    ap.add_argument("--topic", default="/top_view")
    args = ap.parse_args()

    rclpy.init()
    node = Node("grab_overview")
    held: dict[str, RosImage] = {}

    qos = QoSProfile(
        reliability=QoSReliabilityPolicy.BEST_EFFORT,
        history=QoSHistoryPolicy.KEEP_LAST,
        depth=1,
    )

    def cb(msg: RosImage) -> None:
        held.setdefault("m", msg)

    node.create_subscription(RosImage, args.topic, cb, qos)
    t0 = time.time()
    while "m" not in held and time.time() - t0 < args.timeout:
        rclpy.spin_once(node, timeout_sec=0.5)

    msg = held.get("m")
    if msg is None:
        print(f"NO_FRAME (topic {args.topic})")
        node.destroy_node()
        rclpy.shutdown()
        return 1

    try:
        to_pil(msg).save(args.out)
        print(describe(msg))
    except Exception as exc:  # noqa: BLE001
        print(f"DECODE_FAILED {exc}")
        node.destroy_node()
        rclpy.shutdown()
        return 2

    node.destroy_node()
    rclpy.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
