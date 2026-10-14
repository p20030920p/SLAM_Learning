#!/usr/bin/env python3
"""Shared helpers for turning a sensor_msgs/Image into a PIL image.

The one non-obvious part is the row stride.  Gazebo pads each image row up to a
4-byte boundary, and ros_gz_bridge forwards that padded buffer unchanged while
still reporting the unpadded `step` is not guaranteed.  A 600x675 rgb8 frame is
1800 bytes per row, padded to 1804, so `Image.frombytes` sees a 1,217,700-byte
buffer where it expects 1,215,000 and raises
"unknown raw mode for given image mode".
"""

from __future__ import annotations

import numpy as np
from PIL import Image
from sensor_msgs.msg import Image as RosImage

_CHANNELS = {"rgb8": 3, "bgr8": 3, "rgba8": 4, "bgra8": 4, "mono8": 1}


def to_pil(msg: RosImage) -> Image.Image:
    enc = msg.encoding.lower()
    h, w = msg.height, msg.width
    data = bytes(msg.data)

    if enc in _CHANNELS:
        ch = _CHANNELS[enc]
        packed = w * ch
        padding = -packed % 4
        stride = packed + padding
        if len(data) == stride * h and padding:
            arr = np.frombuffer(data, dtype=np.uint8).reshape(h, stride)[:, :packed]
            arr = arr.reshape(h, w, ch)
        elif len(data) == packed * h:
            arr = np.frombuffer(data, dtype=np.uint8).reshape(h, w, ch)
        else:
            raise ValueError(
                f"{enc} {w}x{h}: got {len(data)} bytes, "
                f"expected {packed * h} (packed) or {stride * h} (padded)"
            )
        if enc == "rgb8":
            return Image.fromarray(arr, "RGB")
        if enc == "bgr8":
            return Image.fromarray(arr[:, :, ::-1], "RGB")
        if enc == "rgba8":
            return Image.fromarray(arr, "RGBA").convert("RGB")
        if enc == "bgra8":
            return Image.fromarray(arr[:, :, [2, 1, 0, 3]], "RGBA").convert("RGB")
        return Image.fromarray(arr[:, :, 0], "L").convert("RGB")

    if enc in ("32fc1", "16uc1"):
        dtype = "<f4" if enc == "32fc1" else "<u2"
        itemsize = 4 if enc == "32fc1" else 2
        packed = w * itemsize
        stride = packed + (-packed % 4)
        a = np.frombuffer(data[: stride * h], dtype=np.uint8).reshape(h, stride)
        a = a[:, :packed].copy().view(dtype).reshape(h, w)
        finite = a[np.isfinite(a) & (a > 0)]
        hi = float(np.percentile(finite, 99)) if finite.size else 1.0
        vis = (np.clip(a, 0, max(hi, 1e-6)) / max(hi, 1e-6) * 255).astype(np.uint8)
        return Image.fromarray(vis, "L").convert("RGB")

    raise ValueError(f"unsupported encoding {msg.encoding!r}")


def describe(msg: RosImage) -> str:
    """Statistics that distinguish a rendered frame from a flat one."""
    img = to_pil(msg)
    arr = np.asarray(img)
    return (
        f"mean={arr.mean():7.2f} std={arr.std():7.2f} "
        f"uniq={len(np.unique(arr.reshape(-1, 3), axis=0))} "
        f"{msg.width}x{msg.height} {msg.encoding} bytes={len(msg.data)}"
    )
