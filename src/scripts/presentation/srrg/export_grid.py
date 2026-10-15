"""Export usable 2D occupancy maps using measured rays and estimated poses only."""

import json
from pathlib import Path
import numpy as np
from scipy.ndimage import binary_dilation


def export(run):
    raw = np.load(run / "srrg-raw.npy")
    clean = np.load(run / "srrg-final.npy")
    origin = np.floor(np.concatenate((raw, clean)).min(axis=0) - 0.5)
    upper = np.ceil(np.concatenate((raw, clean)).max(axis=0) + 0.5)
    resolution = 0.05
    width, height = np.ceil((upper - origin) / resolution).astype(int) + 1
    free = np.full((height, width), 205, np.uint8)
    rows = [json.loads(line) for line in (run / "srrg-inputs.jsonl").read_text().splitlines()]
    for row in rows:
        pose = np.array(row["estimated_laser_pose"])
        start = pose[:2, 2]
        ranges = np.array(row["ranges"])
        angles = row["angle_min"] + np.arange(len(ranges)) * row["angle_increment"]
        valid = (ranges > 0.45) & (ranges < 12)
        local = np.column_stack(
            (ranges[valid] * np.cos(angles[valid]), ranges[valid] * np.sin(angles[valid]))
        )
        points = local @ pose[:2, :2].T + start
        for end in points[::4]:
            n = max(2, int(np.linalg.norm(end - start) / resolution) + 1)
            cells = np.floor(
                (start + np.linspace(0, 1, n)[:, None] * (end - start) - origin) / resolution
            ).astype(int)
            ok = (cells[:, 0] >= 0) & (cells[:, 0] < width) & (cells[:, 1] >= 0) & (cells[:, 1] < height)
            cells = cells[ok]
            free[cells[:, 1], cells[:, 0]] = 254
    for name, points in [("raw", raw), ("srrg", clean)]:
        image = free.copy()
        occ = np.zeros(image.shape, bool)
        cells = np.floor((points - origin) / resolution).astype(int)
        occ[cells[:, 1], cells[:, 0]] = True
        image[binary_dilation(occ, iterations=1)] = 0
        folder = run / "maps" / name
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "map.pgm").write_bytes(f"P5\n{width} {height}\n255\n".encode() + np.flipud(image).tobytes())
        (folder / "map.yaml").write_text(
            f"image: map.pgm\nmode: trinary\nresolution: {resolution}\norigin: [{origin[0]}, {origin[1]}, 0.0]\nnegate: 0\noccupied_thresh: 0.65\nfree_thresh: 0.196\n"
        )
    (run / "maps/record.json").write_text(
        json.dumps(
            {
                "source": "Actual 2D scans and native estimated laser poses, no truth",
                "resolution_m": resolution,
                "occupied_dilation_cells": 1,
                "free_ray_stride": 4,
                "scope": "Export for manual localization B; no held-out AMCL result is claimed",
            },
            indent=2,
        )
        + "\n"
    )
    return run / "maps"


if __name__ == "__main__":
    import sys

    print(export(Path(sys.argv[1])))
