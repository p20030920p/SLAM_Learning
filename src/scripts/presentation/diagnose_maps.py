"""Measure information lost by 2D projection; never treat point removal as accuracy."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image


def voxels(points, resolution=.1):
    cells = np.floor(points/resolution).astype(np.int64)
    return set(map(tuple, cells))


def diagnose(maps):
    raw = np.load(maps / "raw/points.npy", allow_pickle=False)
    reference = np.asarray(Image.open(maps / "raw/map.pgm"))
    occupied = voxels(raw)
    result = {}
    for method in ("raw", "dufomap", "beautymap"):
        source = maps / method / "points.npy"
        points = np.load(source, allow_pickle=False)
        image = np.asarray(Image.open(maps / method / "map.pgm"))
        own = voxels(points)
        result[method] = {"points": len(points), "removed_fraction": 1-len(points)/len(raw),
                          "occupied_3d_voxels_0p1m": len(own),
                          "removed_3d_voxels": len(occupied-own), "new_3d_voxels": len(own-occupied),
                          "changed_2d_pixels": int(np.count_nonzero(image != reference)),
                          "raw_occupied_2d_pixels": int(np.count_nonzero(reference == 0)),
                          "points_sha256": hashlib.sha256(source.read_bytes()).hexdigest()}
    return {"maps": str(maps), "methods": result, "voxel_size_m": .1,
            "scope": "representation differences only; neither geometric map error nor static/dynamic accuracy"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("maps", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = diagnose(args.maps)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
