#!/usr/bin/env python3
"""Borderless Tk viewer for the Gazebo overview camera, rotated to match RViz.

The upstream calibration (Sim2Real-AlgoBench docs/RECORDING.md) measured that the
arena top camera maps world +X to image-up and world +Y to image-left, while RViz
draws +X right and +Y up.  The camera half is therefore rotated 90 degrees
clockwise so both halves show the same orientation.  The rotation happens at
display time; the pixels are whatever the simulator rendered.

Usage:
  sdk_image_view.py --topic /top_view --geometry 960x1080+0+0 --rotate cw
"""

from __future__ import annotations

import argparse
import sys
import threading
import time
import tkinter as tk
from pathlib import Path

import rclpy
from PIL import Image, ImageTk
from rclpy.node import Node
from rclpy.qos import QoSHistoryPolicy, QoSProfile, QoSReliabilityPolicy
from sensor_msgs.msg import Image as RosImage

sys.path.insert(0, str(Path(__file__).resolve().parent))
from image_utils import to_pil  # noqa: E402

# PIL's transpose angles are counter-clockwise, so 90 deg clockwise == ROTATE_270.
ROTATE = {
    "none": None,
    "cw": Image.ROTATE_270,
    "ccw": Image.ROTATE_90,
    "180": Image.ROTATE_180,
}


class Viewer(Node):
    def __init__(self, topic: str) -> None:
        super().__init__("live_split_view")
        self.frame: Image.Image | None = None
        self.stamp = 0.0
        self.count = 0
        qos = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=1,
        )
        self.create_subscription(RosImage, topic, self.on_image, qos)
        self.get_logger().info(f"viewing {topic}")

    def on_image(self, msg: RosImage) -> None:
        try:
            self.frame = to_pil(msg)
        except Exception as exc:  # noqa: BLE001
            self.get_logger().warning(f"decode failed: {exc}")
            return
        self.stamp = time.monotonic()
        self.count += 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--topic", required=True)
    ap.add_argument("--geometry", default="960x1080+0+0")
    ap.add_argument("--rotate", default="cw", choices=sorted(ROTATE))
    ap.add_argument("--label", default="")
    args = ap.parse_args()

    rclpy.init()
    node = Viewer(args.topic)
    tw, th = (int(v) for v in args.geometry.split("+")[0].split("x"))

    root = tk.Tk()
    root.overrideredirect(True)
    root.geometry(args.geometry)
    canvas = tk.Canvas(root, width=tw, height=th, bg="#000000",
                       highlightthickness=0, borderwidth=0)
    canvas.pack(fill="both", expand=True)

    state: dict[str, object] = {"photo": None, "count": -1, "item": None}
    text_item = canvas.create_text(
        12, th - 14, anchor="sw", fill="#e8eef5",
        font=("DejaVu Sans Mono", 15), text="",
    )

    threading.Thread(target=rclpy.spin, args=(node,), daemon=True).start()

    def tick() -> None:
        frame = node.frame
        if frame is not None and state["count"] != node.count:
            if ROTATE[args.rotate] is not None:
                frame = frame.transpose(ROTATE[args.rotate])
            photo = ImageTk.PhotoImage(frame.resize((tw, th), Image.BILINEAR))
            if state["item"] is None:
                state["item"] = canvas.create_image(0, 0, anchor="nw", image=photo)
            else:
                canvas.itemconfigure(state["item"], image=photo)
            state["photo"] = photo  # keep a reference alive
            state["count"] = node.count
        age = time.monotonic() - node.stamp if node.stamp else float("inf")
        canvas.itemconfigure(
            text_item,
            text=f"{args.label}  frames {node.count}  age {age:4.1f}s",
            fill="#e8eef5" if age < 2.0 else "#ff8a5c",
        )
        root.after(20, tick)

    tick()
    try:
        root.mainloop()
    finally:
        node.destroy_node()
        rclpy.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
