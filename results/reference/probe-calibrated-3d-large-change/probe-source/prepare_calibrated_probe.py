"""Align internal 3D matching and published world poses using mapping A alone."""
import hashlib
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from slam_learning.runtime.frame_prior import height_from_mapping


def configure(repo, run, cases):
    config_path = run / "probe-config.json"
    config = json.loads(config_path.read_text())
    maps = Path(config["maps"])
    source = Path(json.loads((maps / "record.json").read_text())["source_recording"])
    prior = height_from_mapping(source)
    config["ground_z_m"] = prior["ground_z_m"]
    config["frame_alignment"] = prior
    config["pose_dof"] = "x/y/yaw; z fixed to mapping-A calibrated reference; roll/pitch=0"
    for name in cases:
        if name != "native":
            cases[name]["initial_pose"] = {**cases[name]["initial_pose"], "z": prior["ground_z_m"]}
    for path in (repo / "src/slam_learning/runtime/frame_prior.py", Path(__file__).resolve()):
        shutil.copyfile(path, run / "probe-source" / path.name)
        config["source_sha256"][path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    config_path.write_text(json.dumps(config, indent=2) + "\n")
    return cases


def views(run):
    path = run / "views.json"
    specs = json.loads(path.read_text())
    for spec in specs.values():
        spec["full_pose_display_tf"] = True
        spec["map_topic"] = "/probe/map_points"
        spec["title"] = spec["title"].replace(" - RViz2", " CALIBRATED - RViz2")
    path.write_text(json.dumps(specs, indent=2) + "\n")
