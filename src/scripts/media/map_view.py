#!/usr/bin/env python3
"""Draw slam_toolbox's live occupancy grid, the laser scan and the robot pose.

This is the right half of the split screen.  It exists because RViz2's Map display
fails to render on this machine: its GLSL program does not link under llvmpipe

    rviz2]: rviz/glsl120/indexed_8bit_image.vert ... GLSL link result :
    active samplers with a different type refer to the same texture image unit

so the occupancy grid never appears.  Everything drawn here comes from the same
topics RViz would have used -- /map, /scan, and the odom frame -- so the picture is
the same information, drawn with the X11 canvas that is known to work.

Left 960x1080 is the simulator's own overview render; this fills the right 960x1080.
"""

from __future__ import annotations

import argparse
import math
import sys
import threading
import time
import tkinter as tk
from pathlib import Path

import numpy as np
import rclpy
from nav_msgs.msg import OccupancyGrid, Odometry
from rclpy.node import Node
from rclpy.qos import (
    QoSDurabilityPolicy,
    QoSHistoryPolicy,
    QoSProfile,
    QoSReliabilityPolicy,
)
from rclpy.time import Time
from sensor_msgs.msg import LaserScan
from tf2_ros import Buffer, TransformListener

UNKNOWN = (58, 58, 62)
FREE = (238, 238, 234)
OCCUPIED = (24, 24, 28)
SCAN = (255, 62, 62)
ROBOT = (40, 220, 90)
TRAIL = (120, 200, 255)
BG = (18, 22, 28)


class MapView(Node):
    def __init__(self, args: argparse.Namespace) -> None:
        super().__init__("live_map_view")
        self.args = args
        self.grid: OccupancyGrid | None = None
        self.grid_img: np.ndarray | None = None
        self.scan_xy: np.ndarray | None = None
        self.trail: list[tuple[float, float]] = []
        self.pose: tuple[float, float, float] | None = None
        self.map_count = 0
        self.scan_count = 0
        self.last_map_wall = 0.0
        self.last_scan_wall = 0.0
        self.map_via = "none"
        self.updates = 0

        # /map is subscribed twice with different durability.  A RELIABLE +
        # TRANSIENT_LOCAL reader only matches a publisher offering the same, and
        # when it does not match it receives *nothing at all* -- which is how a
        # recording came out with "map 0  scan 1090  age map 3351.0s" and an empty
        # grid.  A VOLATILE reader matches both a latched and an unlatched publisher,
        # so it is created as a fallback and whichever one is actually delivering is
        # the one drawn.  The active one is reported on screen and in the log.
        latched = QoSProfile(
            reliability=QoSReliabilityPolicy.RELIABLE,
            durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=1,
        )
        volatile = QoSProfile(
            reliability=QoSReliabilityPolicy.RELIABLE,
            durability=QoSDurabilityPolicy.VOLATILE,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=1,
        )
        best = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            durability=QoSDurabilityPolicy.VOLATILE,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=5,
        )
        self.create_subscription(OccupancyGrid, "/map",
                                 lambda m: self.on_map(m, "transient_local"), latched)
        self.create_subscription(OccupancyGrid, "/map",
                                 lambda m: self.on_map(m, "volatile"), volatile)
        self.create_subscription(LaserScan, args.scan_topic, self.on_scan, best)
        self.create_subscription(Odometry, args.odom_topic, self.on_odom, best)

        self.tf_buffer = Buffer(cache_time=rclpy.duration.Duration(seconds=30))
        self.tf_listener = TransformListener(self.tf_buffer, self)
        self.get_logger().info(
            f"map viewer: /map (latched+volatile) + {args.scan_topic} + {args.odom_topic}"
        )

    def on_map(self, msg: OccupancyGrid, via: str = "") -> None:
        self.grid = msg
        self.map_count += 1
        self.map_via = via
        self.last_map_wall = time.monotonic()

    def on_scan(self, msg: LaserScan) -> None:
        self.scan_count += 1
        self.last_scan_wall = time.monotonic()
        r = np.asarray(msg.ranges, dtype=np.float32)
        n = r.size
        ang = msg.angle_min + np.arange(n, dtype=np.float32) * msg.angle_increment
        good = np.isfinite(r) & (r >= msg.range_min) & (r <= msg.range_max)
        r, ang = r[good], ang[good]
        if r.size == 0:
            self.scan_xy = None
            return
        lx, ly = r * np.cos(ang), r * np.sin(ang)
        # lidar_link -> base_footprint -> odom -> map
        try:
            t = self.tf_buffer.lookup_transform(
                self.args.frame, "lidar_link", Time()
            )
        except Exception:  # noqa: BLE001 - transform may not exist yet
            self.scan_xy = None
            return
        q = t.transform.rotation
        yaw = math.atan2(2 * (q.w * q.z + q.x * q.y),
                         1 - 2 * (q.y * q.y + q.z * q.z))
        tx = t.transform.translation.x
        ty = t.transform.translation.y
        c, s = math.cos(yaw), math.sin(yaw)
        self.scan_xy = np.stack([tx + c * lx - s * ly, ty + s * lx + c * ly], axis=1)

    def on_odom(self, msg: Odometry) -> None:
        p = msg.pose.pose.position
        self.pose = (p.x, p.y, 0.0)

    def robot_in_map(self) -> tuple[float, float, float] | None:
        try:
            t = self.tf_buffer.lookup_transform(
                self.args.frame, self.args.odom_child, Time()
            )
        except Exception:  # noqa: BLE001
            return None
        q = t.transform.rotation
        yaw = math.atan2(2 * (q.w * q.z + q.x * q.y),
                         1 - 2 * (q.y * q.y + q.z * q.z))
        return (t.transform.translation.x, t.transform.translation.y, yaw)

    def palette(self) -> np.ndarray | None:
        g = self.grid
        if g is None:
            return None
        if self.grid_img is None or self.grid_img.shape[:2] != (g.info.height, g.info.width):
            self.grid_img = np.zeros((g.info.height, g.info.width, 3), dtype=np.uint8)
        data = np.asarray(g.data, dtype=np.int16).reshape(g.info.height, g.info.width)
        img = self.grid_img
        img[...] = UNKNOWN
        img[data == 0] = FREE
        img[data > 50] = OCCUPIED
        return img


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--geometry", default="960x1080+960+0")
    ap.add_argument("--split", type=int, default=960)
    ap.add_argument("--scan-topic", default="/scan")
    ap.add_argument("--odom-topic", default="/omni_drive_controller/odom")
    ap.add_argument("--frame", default="map")
    ap.add_argument("--odom-child", default="base_footprint")
    ap.add_argument("--view-center", default="3.65,1.0")
    ap.add_argument("--view-size", type=float, default=22.0,
                    help="metres of world height shown (ignored if --view-bounds is given)")
    ap.add_argument("--view-bounds", default="",
                    help="fixed world box 'xmin,xmax,ymin,ymax'.  Prefer this: with a "
                         "fixed box the mapped region visibly GROWS as the robot "
                         "explores.  Fitting the grid to the panel instead makes the "
                         "picture look identical from the first frame, because "
                         "slam_toolbox allocates its full max_size grid immediately "
                         "and only fills it in.")
    ap.add_argument("--label", default="")
    args = ap.parse_args()

    rclpy.init()
    node = MapView(args)
    w = args.geometry.split("+")[0]
    tw, th = (int(v) for v in w.split("x"))

    root = tk.Tk()
    root.title("live_map_view")
    root.overrideredirect(True)
    root.geometry(args.geometry)
    canvas = tk.Canvas(root, width=tw, height=th, bg="#12161c",
                       highlightthickness=0, borderwidth=0)
    canvas.pack(fill="both", expand=True)

    threading.Thread(target=rclpy.spin, args=(node,), daemon=True).start()

    state: dict[str, object] = {"photo": None, "item": None, "n": 0}
    if args.view_bounds:
        xmin, xmax, ymin, ymax = (float(v) for v in args.view_bounds.split(","))
    else:
        cx, cy = (float(v) for v in args.view_center.split(","))
        xmin, xmax = cx - args.view_size / 2.0, cx + args.view_size / 2.0
        ymin, ymax = cy - args.view_size / 2.0, cy + args.view_size / 2.0
    # world -> pixels.  Choose one isotropic scale so the map is never distorted, and
    # letterbox whichever axis has room to spare.
    scale = min(tw / (xmax - xmin), th / (ymax - ymin))
    pad_x = (tw - (xmax - xmin) * scale) / 2.0
    pad_y = (th - (ymax - ymin) * scale) / 2.0

    text_item = canvas.create_text(
        14, 14, anchor="nw", fill="#e8eef5", font=("DejaVu Sans Mono", 14), text=""
    )

    def to_px(x: float, y: float) -> tuple[float, float]:
        # +x to the right, +y up, so the viewer and RViz share one orientation
        return (pad_x + (x - xmin) * scale, th - pad_y - (y - ymin) * scale)

    def redraw() -> None:
        img = node.palette()
        canvas.delete("dyn")
        now = time.monotonic()
        if img is not None:
            g = node.grid
            res = g.info.resolution
            origin = g.info.origin
            h, wpx = img.shape[:2]
            # rotate so grid rows run along +Y, as RViz draws it
            rgba = np.transpose(img, (1, 0, 2))[::-1]
            rgba = np.ascontiguousarray(rgba)
            sys.path.insert(0, str(Path(__file__).resolve().parent))
            from PIL import Image, ImageTk

            # the grid's full extent in world metres, then in pixels
            gx0 = origin.position.x
            gy0 = origin.position.y
            gx1 = gx0 + wpx * res
            gy1 = gy0 + h * res
            p_left, p_bottom = to_px(gx0, gy0)
            p_right, p_top = to_px(gx1, gy1)
            px_w = max(1, int(round(p_right - p_left)))
            px_h = max(1, int(round(p_bottom - p_top)))
            photo = ImageTk.PhotoImage(
                Image.fromarray(rgba).resize((px_w, px_h), Image.NEAREST)
            )
            state["photo"] = photo
            canvas.create_image(p_left, p_top, anchor="nw", image=photo, tags="dyn")

        if node.scan_xy is not None and node.scan_xy.size:
            pts = node.scan_xy
            step = max(1, pts.shape[0] // 900)
            for px, py in pts[::step]:
                x, y = to_px(float(px), float(py))
                if 0 <= x < tw and 0 <= y < th:
                    canvas.create_oval(x - 1.5, y - 1.5, x + 1.5, y + 1.5,
                                       fill="#ff3e3e", outline="", tags="dyn")

        pose = node.robot_in_map()
        if pose is not None:
            if not node.trail or math.dist(pose[:2], node.trail[-1]) > 0.15:
                node.trail.append(pose[:2])
            if len(node.trail) > 1:
                coords = []
                for tx_, ty_ in node.trail:
                    x, y = to_px(tx_, ty_)
                    coords += [x, y]
                canvas.create_line(*coords, fill="#78c8ff", width=2, tags="dyn")
            x, y = to_px(pose[0], pose[1])
            canvas.create_oval(x - 6, y - 6, x + 6, y + 6, fill="#28dc5a",
                               outline="#ffffff", width=2, tags="dyn")
            # heading
            canvas.create_line(x, y, x + 26 * math.cos(-pose[2]),
                               y + 26 * math.sin(-pose[2]),
                               fill="#28dc5a", width=3, tags="dyn")

        gm = (node.grid.info.width, node.grid.info.height,
              node.grid.info.resolution) if node.grid else None
        canvas.itemconfigure(
            text_item,
            text=(f"{args.label}\n"
                  f"map grid + live scan + robot trail\n"
                  f"purpose-built viewer: RViz map display\n"
                  f"cannot render on llvmpipe\n"
                  + (f"grid {gm[0]}x{gm[1]} @ {gm[2]:.2f} m/cell "
                     f"[{node.map_via}]" if gm else "grid -- (no /map yet)")),
            fill="#e8eef5",
        )
        canvas.create_text(
            14, th - 16, anchor="sw", fill="#9fb0c0",
            font=("DejaVu Sans Mono", 13),
            text=(f"map {node.map_count}  scan {node.scan_count}  "
                  f"age map {now - node.last_map_wall:4.1f}s "
                  f"scan {now - node.last_scan_wall:4.1f}s"),
            tags="dyn",
        )
        state["n"] = int(state["n"]) + 1
        root.after(150, redraw)

    redraw()
    try:
        root.mainloop()
    finally:
        node.destroy_node()
        rclpy.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
