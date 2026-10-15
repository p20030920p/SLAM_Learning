"""Archive measured mapping A and independently check every supplied sensor pose."""
import argparse
import json
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
from scipy.spatial.transform import Rotation

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from slam_learning.core.provenance import digest
from slam_learning.runtime.runner import verify_record


def audit(run):
    transforms = {"base_footprint": np.eye(4)}
    joints = ET.parse(run / "probe-robot.urdf").findall("joint")
    for _ in range(len(joints)):
        changed = False
        for joint in joints:
            parent, child = joint.find("parent").get("link"), joint.find("child").get("link")
            if joint.get("type") != "fixed" or parent not in transforms or child in transforms:
                continue
            origin = joint.find("origin")
            pose = np.eye(4)
            pose[:3, 3] = np.fromstring(origin.get("xyz", "0 0 0"), sep=" ") if origin is not None else 0
            pose[:3, :3] = Rotation.from_euler("xyz", np.fromstring(origin.get("rpy", "0 0 0"), sep=" ") if origin is not None else [0, 0, 0]).as_matrix()
            transforms[child] = transforms[parent] @ pose
            changed = True
        if not changed:
            break
    truth = [json.loads(line) for line in (run / "truth.jsonl").read_text().splitlines()]
    stamps = np.array([row["stamp_s"] for row in truth])
    comparisons = []

    def check(stamp, frame, pose):
        index = int(np.argmin(abs(stamps - stamp)))
        measured = truth[index]
        world = np.eye(4)
        world[:3, :3] = Rotation.from_quat(measured["xyzw"]).as_matrix()
        world[:3, 3] = measured["xyz"]
        difference = float(np.max(np.abs(world @ transforms[frame] - pose)))
        delta = abs(stamps[index] - stamp)
        if delta > .05 or difference > 1e-7:
            raise ValueError(f"Mapping A pose differs from robot truth + actual URDF extrinsics: {frame}, {difference}")
        comparisons.append((delta, difference))

    extra = np.load(run / "probe-mapping-inputs.npz", allow_pickle=False)
    for row in json.loads((run / "probe-mapping-inputs.json").read_text())["records"]:
        check(row["stamp_s"], row["frame_id"], extra[row["key"] + "_pose"])
    lidar = np.load(run / "mapping-clouds.npz", allow_pickle=False)
    for stamp, pose in zip(lidar["stamps"], lidar["poses"]):
        check(stamp, "lidar_3d_link", pose)
    return {"scope": "mapping A provided poses independently reconstructed from Gazebo model truth and fixed-joint URDF extrinsics",
            "checked_sensor_poses": len(comparisons), "max_truth_delta_s": max(row[0] for row in comparisons),
            "max_transform_element_error": max(row[1] for row in comparisons), "truth_to_localization_B": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    checked = audit(args.run)
    subprocess.run([sys.executable, str(Path(__file__).with_name("package_session.py")), str(args.run), str(args.output), "--no-replay"], check=True)
    for name in ("mapping-clouds.npz", "probe-mapping-inputs.npz", "probe-mapping-inputs.json", "probe-robot.urdf", "probe-bridge.yaml", "height-control.world"):
        if (args.run / name).is_file():
            shutil.copyfile(args.run / name, args.output / name)
    shutil.copytree(args.run / "probe-maps", args.output / "probe-maps", ignore=shutil.ignore_patterns("*.pcd"))
    (args.output / "provided-pose-audit.json").write_text(json.dumps(checked, indent=2) + "\n")
    path = args.output / "record.json"
    record = json.loads(path.read_text())
    record["probe_mapping_A"] = checked
    record["scope"] = "actual mapping-A lidar/depth sensor capture, supplied poses checked against truth + URDF; no full 3D SLAM claim; no truth in localization B"
    record["artifacts"] = {part.relative_to(args.output).as_posix(): {"sha256": digest(part), "bytes": part.stat().st_size, "availability": "portable"} for part in args.output.rglob("*") if part.is_file() and part != path}
    path.write_text(json.dumps(record, indent=2) + "\n")
    if verify_record(path):
        raise ValueError("Mapping A archive validation failed")
    print(json.dumps(checked, indent=2))


if __name__ == "__main__":
    main()
