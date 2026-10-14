"""Derive a ground-robot height reference only from provided mapping-A poses."""
import hashlib
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
from scipy.spatial.transform import Rotation


def sensor_extrinsic(urdf, frame="lidar_3d_link"):
    transforms = {"base_footprint": np.eye(4)}
    joints = ET.parse(urdf).findall("joint")
    for _ in joints:
        changed = False
        for joint in joints:
            parent, child = joint.find("parent").get("link"), joint.find("child").get("link")
            if joint.get("type") != "fixed" or parent not in transforms or child in transforms:
                continue
            origin = joint.find("origin")
            transform = np.eye(4)
            transform[:3, 3] = np.fromstring(origin.get("xyz", "0 0 0"), sep=" ") if origin is not None else 0
            transform[:3, :3] = Rotation.from_euler("xyz", np.fromstring(origin.get("rpy", "0 0 0"), sep=" ") if origin is not None else [0, 0, 0]).as_matrix()
            transforms[child] = transforms[parent] @ transform
            changed = True
        if not changed:
            break
    return transforms[frame]


def height_from_mapping(run):
    run = Path(run)
    archive = run / "mapping-clouds.npz"
    urdf = run / "probe-robot.urdf"
    extrinsic = sensor_extrinsic(urdf)
    with np.load(archive, allow_pickle=False) as data:
        body = data["poses"] @ np.linalg.inv(extrinsic)
    heights = body[:, 2, 3]
    if len(heights) < 10 or not np.isfinite(heights).all():
        raise ValueError("Insufficient provided mapping poses for a height reference")
    return {"ground_z_m": float(np.median(heights)), "provided_pose_count": len(heights),
            "height_p10_p90_m": np.quantile(heights, [.1, .9]).tolist(),
            "source": "median body height reconstructed from mapping-A supplied sensor poses and actual URDF extrinsics",
            "mapping_A_pose_archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
            "mapping_A_urdf_sha256": hashlib.sha256(urdf.read_bytes()).hexdigest(),
            "body_from_sensor": np.linalg.inv(extrinsic).tolist(), "localization_B_truth_used": False}
