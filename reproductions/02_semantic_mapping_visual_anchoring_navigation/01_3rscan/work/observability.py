#!/usr/bin/env python3
"""Observability of each object in session B — the missing half of the GT.

The dataset labels *what changed*; it never says *whether the robot could have
seen it*. That is the difference between "the cushion is gone" and "I did not
look at the cushion", and 3RScan does not distinguish them. This module measures
it from the session's own camera poses and depth frames.

Method (per object, per frame of session B):

    points (B frame) -> camera frame -> pixel + depth
    measured depth ~= predicted depth   -> the surface was seen      (visible)
    measured depth << predicted depth   -> something is in front     (occluded)
    no point lands in the image         -> the object is out of view

An object is `visible` when at least `min_visible_frames` frames confirm its
surface, `occluded` when it is inside the frustum in enough frames but never
confirmed, `out_of_view` when no frame contains it, and `insufficient` when
there were too few frames either way. Aggregate over the session, not per frame:
one confirmed sighting in 51 frames is not the same as 30.

Conventions used here were each established by measurement, not assumption:

  pose        p_world = R p + t  (translation in the fourth column). Verified by
              frame-to-frame reprojection: this reading agrees with the observed
              depth to <5 cm for 97% of points, the alternative for 15%.
  OBB axes    `normalizedAxes` holds the three axis vectors as ROWS, so the
              half-extent for axis k is axesLengths[k]/2. Verified on the floor
              and the walls, whose thinnest axis must be their normal.
"""

from __future__ import annotations

import json
import os
import re

import numpy as np

# --------------------------------------------------------------------------- #
# 3RScan sensor files
# --------------------------------------------------------------------------- #
def read_pgm(path):
    """Binary P5 reader that tolerates a comment between the magic and the size."""
    data = open(path, "rb").read()
    toks, i = [], 0
    while len(toks) < 4:
        while data[i:i + 1].isspace():
            i += 1
        if data[i:i + 1] == b"#":
            while data[i:i + 1] not in (b"\n", b""):
                i += 1
            continue
        j = i
        while not data[j:j + 1].isspace():
            j += 1
        toks.append(data[i:j])
        i = j
    width, height, maxval = int(toks[1]), int(toks[2]), int(toks[3])
    i += 1  # a single whitespace byte follows maxval
    if maxval > 255:
        arr = np.frombuffer(data[i:i + width * height * 2], dtype=">u2")
    else:
        arr = np.frombuffer(data[i:i + width * height], dtype=np.uint8)
    return arr.reshape(height, width).astype(np.float64)


def parse_info(sequence_dir):
    """Calibration block of _info.txt."""
    info = {}
    with open(os.path.join(sequence_dir, "_info.txt"), encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            info[key.strip()] = value.strip()

    def nums(key):
        return [float(v) for v in re.findall(r"-?\d+\.?\d*(?:e[-+]?\d+)?", info.get(key, ""))]

    ci = nums("m_calibrationColorIntrinsic")     # 3x4 row-major
    di = nums("m_calibrationDepthIntrinsic")
    # The depth PNG/PGM stores millimetres (the FAQ says as much: "multiply with
    # 0.001"), and m_depthShift is the divisor, not the factor. Reading it as a
    # multiplier leaves every depth 1000x too large, which silently turns every
    # surface into "measured far behind predicted".
    depth_shift = float(info.get("m_depthShift", 1000.0)) or 1000.0
    return {
        "color_wh": (int(info["m_colorWidth"]), int(info["m_colorHeight"])),
        "depth_wh": (int(info["m_depthWidth"]), int(info["m_depthHeight"])),
        "color_K": (ci[0], ci[5], ci[2], ci[6]) if len(ci) >= 11 else None,
        "depth_K": (di[0], di[5], di[2], di[6]) if len(di) >= 11 else None,
        "depth_scale_m": 1.0 / depth_shift,
    }


def frame_ids(sequence_dir):
    ids = []
    for name in os.listdir(sequence_dir):
        m = re.match(r"frame-(\d+)\.pose\.txt$", name)
        if m:
            ids.append(int(m.group(1)))
    return sorted(ids)


def load_pose(sequence_dir, frame):
    return np.loadtxt(os.path.join(sequence_dir, f"frame-{frame:06d}.pose.txt"))


def load_depth(sequence_dir, frame, scale):
    return read_pgm(os.path.join(sequence_dir, f"frame-{frame:06d}.depth.pgm")) * scale


# --------------------------------------------------------------------------- #
# geometry
# --------------------------------------------------------------------------- #
def obb_surface_points(centroid, axes_lengths, normalized_axes, grid=3):
    """Sample the surface of an oriented box. `normalizedAxes` rows are the axes."""
    axes = np.asarray(normalized_axes, dtype=float).reshape(3, 3)
    half = np.asarray(axes_lengths, dtype=float) / 2.0
    steps = np.linspace(-1.0, 1.0, grid)
    points = []
    for k in range(3):
        u, v = [i for i in range(3) if i != k]
        for sign in (-1.0, 1.0):
            for a in steps:
                for b in steps:
                    off = np.zeros(3)
                    off[k] = sign * half[k]
                    off[u] = a * half[u]
                    off[v] = b * half[v]
                    points.append(np.asarray(centroid, float) + off @ axes)
    return np.array(points)


def to_camera(points_world, pose):
    """p_world = R p + t  =>  p_cam = R^T (p_world - t)."""
    R, t = pose[:3, :3], pose[:3, 3]
    return (np.asarray(points_world, float) - t) @ R


def is_rotation(pose, tol=1e-3):
    R = pose[:3, :3]
    return bool(np.allclose(R @ R.T, np.eye(3), atol=tol)
                and abs(np.linalg.det(R) - 1.0) < tol)


# --------------------------------------------------------------------------- #
# the measurement
# --------------------------------------------------------------------------- #
def observe_object(points_in_B, obs, tau_visible=0.10, min_samples=3,
                   min_visible_frames=3, max_frames=None):
    """Per-frame visibility of one object's sampled surface in session B."""
    fx, fy, cx, cy = obs["depth_K"]
    width, height = obs["depth_wh"]
    frames = obs["frames"][:max_frames] if max_frames else obs["frames"]

    visible_frames, occluded_frames, in_frustum_frames = 0, 0, 0
    seen_samples, occluded_samples, tested = 0, 0, 0

    for frame in frames:
        cam = to_camera(points_in_B, obs["poses"][frame])
        z = cam[:, 2]
        front = z > 0.05
        if not front.any():
            continue
        u = cam[front, 0] / z[front] * fx + cx
        v = cam[front, 1] / z[front] * fy + cy
        zz = z[front]
        inside = (u >= 0) & (u < width) & (v >= 0) & (v < height)
        if inside.sum() == 0:
            continue
        in_frustum_frames += 1

        depth = obs["depth"][frame]
        ui = np.clip(u[inside].astype(int), 0, width - 1)
        vi = np.clip(v[inside].astype(int), 0, height - 1)
        measured = depth[vi, ui]
        predicted = zz[inside]
        valid = measured > 0
        tested += int(valid.sum())
        if not valid.any():
            continue

        diff = measured[valid] - predicted[valid]
        seen = int((np.abs(diff) <= tau_visible).sum())
        blocked = int((diff < -tau_visible).sum())
        seen_samples += seen
        occluded_samples += blocked

        if seen >= min_samples:
            visible_frames += 1
        elif blocked >= min_samples:
            occluded_frames += 1

    if visible_frames >= min_visible_frames:
        verdict = "visible"
    elif in_frustum_frames >= min_visible_frames and visible_frames == 0:
        verdict = "occluded"
    elif in_frustum_frames == 0:
        verdict = "out_of_view"
    else:
        verdict = "insufficient"

    return {
        "observability": verdict,
        "frames_total": len(frames),
        "frames_in_frustum": in_frustum_frames,
        "frames_visible": visible_frames,
        "frames_occluded": occluded_frames,
        "samples_tested": tested,
        "samples_visible": seen_samples,
        "samples_occluded": occluded_samples,
    }


def load_session(sequence_dir, poses_cache=None, max_frames=None):
    """Everything `observe_object` needs for one scan."""
    info = parse_info(sequence_dir)
    ids = frame_ids(sequence_dir)
    if max_frames:
        ids = ids[:max_frames]
    poses, depths = {}, {}
    for frame in ids:
        poses[frame] = load_pose(sequence_dir, frame)
        depths[frame] = load_depth(sequence_dir, frame, info["depth_scale_m"])
    return {
        "depth_K": info["depth_K"],
        "depth_wh": info["depth_wh"],
        "frames": ids,
        "poses": poses,
        "depth": depths,
    }


def load_objects(scan_dir):
    seg = json.load(open(os.path.join(scan_dir, "semseg.v2.json"), encoding="utf-8"))
    return {g["objectId"]: g for g in seg["segGroups"]}


def invert_alignment(M):
    """Inverse of one of 3RScan's row-vector 4x4 matrices."""
    m = np.asarray(M, dtype=float).reshape(4, 4)
    R, t = m[:3, :3], m[3, :3]
    Ri = R.T
    ti = -t @ Ri
    out = np.eye(4)
    out[:3, :3] = Ri
    out[3, :3] = ti
    return out.flatten().tolist()


def map_obb(obb, flat_transform):
    """Move an OBB through a row-vector 4x4 (p' = p M)."""
    m = np.asarray(flat_transform, dtype=float).reshape(4, 4)
    centroid = np.append(np.asarray(obb["centroid"], float), 1.0) @ m
    axes = np.asarray(obb["normalizedAxes"], float).reshape(3, 3) @ m[:3, :3]
    return {"centroid": centroid[:3].tolist(),
            "axesLengths": list(obb["axesLengths"]),
            "normalizedAxes": axes.flatten().tolist()}
