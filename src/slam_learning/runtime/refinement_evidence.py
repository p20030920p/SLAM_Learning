"""Validate paired offline refinement against its complete native parent evidence."""
import hashlib
import json
from pathlib import Path

import numpy as np

from slam_learning.core.provenance import digest
from slam_learning.runtime.poses3d import score_poses3d
from slam_learning.runtime.presentation_evidence import read_samples, restoration, score, validate_truth


def verify_refinement(path, record):
    try:
        root = Path(__file__).resolve().parents[3]
        parent = (root / record["parent_repository_path"]).resolve()
        if not parent.is_relative_to((root / "results/reference").resolve()) or digest(parent) != record["parent_sha256"]:
            raise ValueError("Refinement parent is missing, outside references, or changed")
        protocol_path = (root / record.get("protocol_repository_path", "results/analysis/hypotheses/refinement-protocol.json")).resolve()
        if not protocol_path.is_relative_to((root / "results/analysis/hypotheses").resolve()):
            raise ValueError("Refinement protocol escaped the analysis directory")
        protocol = json.loads(protocol_path.read_text())
        if digest(protocol_path) != record["protocol_sha256"] or record["truth_input_to_estimators"] is not False:
            raise ValueError("Refinement protocol changed or estimator accepts truth")
        folder = path.parent
        for name, sha in protocol["source_sha256"].items():
            if digest(folder / "sources" / name) != sha:
                raise ValueError("Refinement algorithm differs from frozen protocol")
        parent_record = json.loads(parent.read_text())
        parent_folder = parent.parent
        ground_z = parent_record["hypothesis_probes"].get("ground_z_m", 0.)
        if abs(record.get("ground_z_m", 0.) - ground_z) > 1e-12:
            raise ValueError("Refinement changed the parent height reference")
        expected_inputs = {"cases.json", "probe-config.json", "probe-B-inputs.npz", "probe-B-inputs.json",
                           "probe-maps/lidar.npy", "probe-maps/depth.npy", "truth.jsonl", "search-samples.csv", "recover-samples.csv"}
        if set(record["source_inputs"]) != expected_inputs:
            raise ValueError("Refinement input inventory differs")
        for name, sha in record["source_inputs"].items():
            if digest(parent_folder / name) != sha or parent_record["artifacts"][name]["sha256"] != sha:
                raise ValueError("Refinement inputs differ from retained native B")
        if digest(folder / "truth.jsonl") != digest(parent_folder / "truth.jsonl"):
            raise ValueError("Refinement evaluation truth changed")
        for coarse, original in (("coarse_lidar", "search"), ("coarse_depth", "recover")):
            if digest(folder / f"{coarse}-samples.csv") != digest(parent_folder / f"{original}-samples.csv"):
                raise ValueError("Saved coarse control was altered")
            if record["dimension"] == "3d" and digest(folder / f"{coarse}-poses3d.csv") != digest(parent_folder / f"{original}-poses3d.csv"):
                raise ValueError("Saved full-3D coarse control was altered")
        truth = [json.loads(line) for line in (folder / "truth.jsonl").read_text().splitlines()]
        restore = parent_record["restoration"]["plain"]["restore_stamp_s"]
        values = {name: read_samples(folder / f"{name}-samples.csv") for name in record["metrics"]}
        first = min(array[0, 0] for array in values.values())
        for name, array in values.items():
            validate_truth(array, truth)
            if score(array) != record["metrics"][name] or restoration(array, restore) != record["restoration"][name]:
                raise ValueError("Refinement score/recovery differs from independent truth")
            if restoration(array, first)["sustained_convergence_delay_s"] != record["initial_sustained_delay_s"][name]:
                raise ValueError("Refinement startup-convergence timing differs")
            if record["dimension"] == "3d" and score_poses3d(folder / f"{name}-poses3d.csv", truth) != record["metrics_3d"][name]:
                raise ValueError("Refinement full 3D score differs")
            if record["dimension"] == "3d":
                poses = np.genfromtxt(folder / f"{name}-poses3d.csv", delimiter=",", names=True)
                if not np.allclose(poses["estimate_z"], ground_z, atol=1e-12, rtol=0):
                    raise ValueError("Refinement 3D output has the wrong height reference")
        frames = json.loads((parent_folder / "probe-B-inputs.json").read_text())["frames"]
        arrays = np.load(parent_folder / "probe-B-inputs.npz", allow_pickle=False)
        updates = [json.loads(line) for line in (folder / "inference.jsonl").read_text().splitlines()]
        if len(updates) != len(frames) * 2:
            raise ValueError("New refinement inference did not process all retained frames")
        for index, frame in enumerate(frames):
            key = f"frame_{frame['frame']:05d}"
            lidar, depth, odom = (arrays[key + suffix] for suffix in ("_lidar", "_depth", "_odom"))
            sha = hashlib.sha256(lidar.tobytes() + depth.tobytes() + odom.tobytes()).hexdigest()
            group = updates[index * 2:index * 2 + 2]
            if {row["case"] for row in group} != {"fine_lidar", "fine_depth"}:
                raise ValueError("Refinement cases were relabelled")
            for row in group:
                if row["frame"] != frame["frame"] or row["stamp_s"] != frame["stamp_s"] or row["input_sha256"] != sha:
                    raise ValueError("Refinement sensor/odometry history differs")
                scored = values[row["case"]]
                scored = scored[np.abs(scored[:, 0] - row["stamp_s"]) < 1e-9]
                if len(scored) != 1 or not np.allclose(scored[0, 4:7], row["pose"], atol=1e-10, rtol=0):
                    raise ValueError("Refinement scored pose differs from new inference")
    except (OSError, ValueError, KeyError, TypeError) as error:
        return [f"Offline refinement: {error}"]
    return []
