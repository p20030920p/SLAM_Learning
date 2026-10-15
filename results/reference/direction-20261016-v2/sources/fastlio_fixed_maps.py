"""Use only the two frozen experimental maps in a separate native GICP run."""

import hashlib
import json
from pathlib import Path


def configure(repo, run, spawn, offset):
    marker = repo / ".cache/presentation/fastlio-maps-latest.json"
    if marker.exists():
        value = json.loads(marker.read_text())["path"].replace("\\", "/")
        maps = Path("/mnt/" + value[0].lower() + "/" + value[3:]) if ":/" in value else Path(value)
    else:
        maps = repo / "results/reference/direction-20261016/fastlio-maps"
    cases = {}
    for name in ("deskew", "no_deskew"):
        p = maps / name
        cases[name] = {
            "method": name,
            "dimension": "3d",
            "localizer": "GICP",
            "map_yaml": str(p / "map.yaml"),
            "map_pcd": str(p / "map-3d.pcd"),
            "pose_topic": f"/{name}/pcl_pose",
            "cloud_topic": "/points",
            "native_map_odom_tf": True,
            "broadcast_tf": False,
            "map_points_sha256": hashlib.sha256((p / "points.npy").read_bytes()).hexdigest(),
            "initial_pose": {
                "x": spawn[0] + offset[0],
                "y": spawn[1] + offset[1],
                "z": 0.0,
                "yaw": spawn[2] + offset[2],
            },
        }
    return cases
