"""Independently recheck portable native evidence and every published map score."""

import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[4]


def verify(folder):
    r = json.loads((folder / "record.json").read_text())
    assert r["status"] == "executed" and r["exit_code"] == 0
    assert r["truth_input_to_mapper"] is False
    for name, meta in r["artifacts"].items():
        p = folder / name
        assert p.is_file() and p.stat().st_size == meta["bytes"], p
        assert hashlib.sha256(p.read_bytes()).hexdigest() == meta["sha256"], p
    robot = ET.parse(folder / "srrg-2d.urdf").getroot()
    assert not robot.findall("gazebo[@reference='lidar_3d_link']")
    assert json.loads((folder / "runtime.json").read_text())["srrg_graph_merge"] is False
    data = np.load(folder / "srrg-quality-inputs.npz")
    for key in ("raw", "srrg"):
        tree = cKDTree(data[key])
        expected = r["map_quality"][key]
        sa = float((tree.query(data["static_support"], workers=2)[0] <= 0.15).mean())
        assert abs(sa - expected["static_retention"]) < 1e-12
        dyn = data["dynamic_ghost_support"]
        da = float((tree.query(dyn, workers=2)[0] > 0.15).mean()) if len(dyn) else None
        assert da == expected["dynamic_removal"]
    frames = [json.loads(line) for line in (folder / "srrg-frames.jsonl").read_text().splitlines()]
    inputs = [json.loads(line) for line in (folder / "srrg-inputs.jsonl").read_text().splitlines()]
    assert len(frames) == len(inputs) == r["audit"]["frames"]
    assert [f["stamp_s"] for f in frames] == [i["stamp_s"] for i in inputs]
    assert all(len(i["ranges"]) == 720 and all(np.isfinite(i["ranges"])) for i in inputs)
    assert max(abs(i["odom_stamp_s"] - i["stamp_s"]) for i in inputs) <= 0.1 + 1e-9
    if folder.name.endswith("large-change"):
        assert r["multi_session_prior"]
    if folder.name.endswith("corridor"):
        assert any(f["phase"] == "limited" for f in frames) and any(f["phase"] == "full" for f in frames)
    print(folder.name, "PASS", r["map_quality"])


if __name__ == "__main__":
    for scene in ("static", "dynamic", "large-change", "corridor"):
        verify(ROOT / f"results/reference/srrg-2d-{scene}")
