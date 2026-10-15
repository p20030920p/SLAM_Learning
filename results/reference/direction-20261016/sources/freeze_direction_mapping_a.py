"""Bind each new 2D B run to its actual mapping A, not a different old demo."""

import hashlib
import json
from pathlib import Path
import shutil
import sys

import numpy as np
from scipy.spatial import cKDTree

from package_session import gif

ROOT = Path(__file__).resolve().parents[3]


def windows(value):
    text = str(value).replace("\\", "/")
    return Path(text[5].upper() + ":/" + text[7:]) if text.startswith("/mnt/") else Path(text)


def freeze(scene):
    b = ROOT / "results/reference/direction-20261016" / ("2d-" + scene)
    runtime = json.loads((b / "runtime.json").read_text())
    run = windows(runtime["mapping_source"])
    out = b.parent / ("2d-A-" + scene)
    out.mkdir(exist_ok=False)
    for name in (
        "srrg-quality.json",
        "srrg-quality-inputs.npz",
        "srrg-final.npy",
        "srrg-raw.npy",
        "runtime.json",
        "session.json",
        "srrg-frames.jsonl",
        "srrg-inputs.jsonl",
        "truth.jsonl",
    ):
        shutil.copyfile(run / name, out / name)
    shutil.copytree(run / "maps", out / "maps")
    source = np.load(out / "srrg-quality-inputs.npz")
    reference = source["static_support"]
    tree = cKDTree(reference)
    methods = {}
    quality = json.loads((out / "srrg-quality.json").read_text())
    for name, file in [("raw", "srrg-raw.npy"), ("srrg", "srrg-final.npy")]:
        points = np.load(out / file)
        _, ids = np.unique(np.floor(points / 0.1).astype(int), axis=0, return_index=True)
        distance = tree.query(points[ids])[0]
        methods[name] = {
            **quality["methods"][name],
            "observed_static_support_distance_rmse_m": float(np.sqrt(np.mean(distance**2))),
        }
        assert (b / "maps" / name / "map.pgm").read_bytes() == (run / "maps" / name / "map.pgm").read_bytes()
    shutil.copyfile(run / "execution.mp4", out / "execution.mp4")
    timing = gif(out / "execution.mp4", out / "execution.gif")
    record = {
        "schema_version": 1,
        "kind": "frozen_actual_native_2d_mapping_a",
        "status": "executed",
        "exit_code": 0,
        "scope": "Previously recorded actual A that generated the maps used in this new B; no new A execution claimed. Geometry metric is 10cm-voxel point distance to observed static support, not exact surface RMSE.",
        "source_run": str(run),
        "methods": methods,
        "timing": timing,
        "artifacts": {
            p.relative_to(out).as_posix(): {
                "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
                "bytes": p.stat().st_size,
                "availability": "portable",
            }
            for p in out.rglob("*")
            if p.is_file()
        },
    }
    (out / "record.json").write_text(json.dumps(record, indent=2) + "\n")
    print(scene, json.dumps(methods))


if __name__ == "__main__":
    for scene in sys.argv[1:]:
        freeze(scene)
