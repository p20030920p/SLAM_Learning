"""Reject unmatched sensor histories, relabelled poses and missing depth evidence."""
import hashlib
import json

import numpy as np

from slam_learning.core.provenance import digest
from slam_learning.runtime.presentation_evidence import read_samples
from slam_learning.runtime.frame_prior import sensor_extrinsic


def verify_probe_map_manifest(path, manifest):
    """A nested map-build manifest is bound to its complete mapping-A record."""
    try:
        folder = path.parent.parent
        parent = json.loads((folder / "record.json").read_text(encoding="utf-8"))
        runtime = json.loads((folder / "runtime.json").read_text(encoding="utf-8"))
        if (path.parent.name != "probe-maps" or parent.get("schema_version") != 1
                or parent.get("kind") != "native_desktop_mapping" or not parent.get("probe_mapping_A")):
            raise ValueError("Map manifest lacks its complete mapping-A parent")
        if manifest["provided_mapping_poses"] is not True or manifest["truth_to_localization_B"] is not False:
            raise ValueError("Map-build pose scope changed")
        if manifest["world_sha256"] != runtime["world_sha256"]:
            raise ValueError("Map-build world differs from mapping A")
        required = {"mapping-clouds.npz", "probe-mapping-inputs.npz", "probe-mapping-inputs.json"}
        if set(manifest["inputs"]) != required:
            raise ValueError("Unexpected mapping-A inputs")
        for name, sha in manifest["inputs"].items():
            if digest(folder / name) != sha:
                raise ValueError("Map-build input changed")
        bound_files = [path]
        for name in ("lidar2d", "lidar3d", "depth"):
            source = path.parent / ("depth.npy" if name == "depth" else f"{name}/points.npy")
            points = np.load(source, allow_pickle=False)
            counts = manifest["maps"][name]
            if (points.ndim != 2 or points.shape[1] != 3 or not np.isfinite(points).all()
                    or len(points) != counts["voxel_points"] or counts["raw_points"] < len(points)):
                raise ValueError("Map-build point counts or coordinates changed")
            bound_files.append(source)
        for source in bound_files:
            relative = source.relative_to(folder).as_posix()
            if digest(source) != parent["artifacts"][relative]["sha256"]:
                raise ValueError("Map manifest/output differs from its sealed parent")
        return []
    except (OSError, KeyError, TypeError, ValueError) as exc:
        return [f"Invalid probe map manifest: {exc}"]


def verify_probe(path, record):
    try:
        folder = path.parent
        config = json.loads((folder / "probe-config.json").read_text())
        if config != record["hypothesis_probes"] or config["truth_input_to_localizers"] is not False:
            raise ValueError("Probe configuration differs or accepts truth")
        for name, sha in config["source_sha256"].items():
            if digest(folder / "probe-source" / name) != sha:
                raise ValueError("Prototype source snapshot changed")
        robot = (folder / "probe-robot.urdf").read_text()
        if config["dimension"] == "2d" and "research_lidar_3d" in robot:
            raise ValueError("2D arm still contains a 3D lidar")
        if 'type="depth_camera"' not in robot:
            raise ValueError("A rendered depth camera is missing")
        if "ground_z_m" in config:
            prior = config["frame_alignment"]
            if prior["localization_B_truth_used"] is not False or digest(folder / "height-prior-source.urdf") != prior["mapping_A_urdf_sha256"]:
                raise ValueError("Height reference lacks independent mapping-A calibration")
            calibration = np.load(folder / "height-prior-inputs.npz", allow_pickle=False)
            body_from_sensor = np.linalg.inv(sensor_extrinsic(folder / "height-prior-source.urdf"))
            if not np.allclose(body_from_sensor, calibration["body_from_sensor"], atol=1e-12, rtol=0):
                raise ValueError("Height reference uses the wrong sensor extrinsic")
            height = float(np.median((calibration["provided_sensor_poses"] @ body_from_sensor)[:, 2, 3]))
            if abs(height - config["ground_z_m"]) > 1e-12:
                raise ValueError("Height reference differs from archived provided A poses")
        inputs = np.load(folder / "probe-B-inputs.npz", allow_pickle=False)
        frames = json.loads((folder / "probe-B-inputs.json").read_text())["frames"]
        updates = [json.loads(line) for line in (folder / "probe-updates.jsonl").read_text().splitlines()]
        by_frame = {}
        for update in updates:
            by_frame.setdefault(update["frame"], []).append(update)
        variants = config["variants"]
        rows = {name: read_samples(folder / f"{name}-samples.csv") for name in variants}
        for frame in frames:
            index, stamp = frame["frame"], frame["stamp_s"]
            key = f"frame_{index:05d}"
            lidar, depth, odom = (inputs[key + suffix] for suffix in ("_lidar", "_depth", "_odom"))
            sha = hashlib.sha256(lidar.tobytes() + depth.tobytes() + odom.tobytes()).hexdigest()
            shared = by_frame[index]
            if len(shared) != len(variants) or {row["case"] for row in shared} != set(variants):
                raise ValueError("Variants did not process identical frame IDs")
            for update in shared:
                if update["stamp_s"] != stamp or update["input_sha256"] != sha:
                    raise ValueError("Variants were given different sensor/odom history")
                if abs(update.get("z_m", 0.) - config.get("ground_z_m", 0.)) > 1e-12:
                    raise ValueError("Published prototype height differs from its A-derived reference")
                scored = rows[update["case"]]
                selected = scored[np.abs(scored[:, 0] - stamp) < 1e-9]
                if len(selected) != 1 or not np.allclose(selected[0, 4:7], update["pose"], atol=1e-10, rtol=0):
                    raise ValueError("Scored pose differs from the actual prototype output")
            if len(depth) and (frame["depth_delta_s"] is None or frame["depth_delta_s"] > .12):
                raise ValueError("Unsynchronized depth entered the prototype")
        if not frames or len(updates) != len(frames) * len(variants):
            raise ValueError("Incomplete prototype input/output history")
        if config["dimension"] == "3d":
            for name in variants:
                poses = np.genfromtxt(folder / f"{name}-poses3d.csv", delimiter=",", names=True)
                if not np.allclose(poses["estimate_z"], config.get("ground_z_m", 0.), atol=1e-12, rtol=0):
                    raise ValueError("Scored 3D height differs from the actual prototype output")
    except (OSError, ValueError, KeyError, TypeError) as error:
        return [f"Hypothesis probes: {error}"]
    return []
