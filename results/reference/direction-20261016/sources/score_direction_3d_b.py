"""Score both frozen FAST-LIO maps with the same native GICP B timestamps."""

import csv
import json
from pathlib import Path
import sys
import numpy as np
from scipy.spatial.transform import Rotation, Slerp


def score(folder):
    report = json.loads((folder / "metrics.json").read_text())
    start, end = report["recording_interval_sim_s"]
    truth = [json.loads(line) for line in (folder / "truth.jsonl").read_text().splitlines()]
    tt = np.array([r["stamp_s"] for r in truth])
    xyz = np.array([r["xyz"] for r in truth])
    _, unique = np.unique(tt, return_index=True)
    tt = tt[unique]
    xyz = xyz[unique]
    grid = np.arange(start + 5, end, 0.1)
    target = np.column_stack([np.interp(grid, tt, xyz[:, i]) for i in range(3)])
    qtruth = Rotation.from_quat(np.array([r["xyzw"] for r in truth])[unique])
    target_rot = Slerp(tt, qtruth)(grid)
    data = {}
    valids = {}
    for name in ["deskew", "no_deskew"]:
        with (folder / f"{name}-poses3d.csv").open() as f:
            rows = list(csv.DictReader(f))
        columns = [
            "stamp_s",
            "estimate_x",
            "estimate_y",
            "estimate_z",
            "estimate_qx",
            "estimate_qy",
            "estimate_qz",
            "estimate_qw",
        ]
        a = np.array([[float(r[k]) for k in columns] for r in rows])
        finite = np.isfinite(a).all(axis=1) & (np.linalg.norm(a[:, 4:], axis=1) > 0.5)
        a = a[finite]
        ids = np.searchsorted(a[:, 0], grid, side="right") - 1
        valid = (ids >= 0) & (grid - a[np.maximum(ids, 0), 0] <= 0.15)
        valids[name] = valid
        selected = a[np.maximum(ids, 0)]
        dist = np.linalg.norm(selected[:, 1:4] - target, axis=1)
        angle = np.rad2deg((target_rot.inv() * Rotation.from_quat(selected[:, 4:])).magnitude())
        data[name] = (dist, angle, int((~finite).sum()))
    common = np.logical_and.reduce(list(valids.values()))
    out = {}
    assert common.any()
    for name, (d, a, invalid) in data.items():
        out[name] = {
            "xyz_rmse_m": float(np.sqrt(np.mean(d[common] ** 2))),
            "xyz_p95_m": float(np.percentile(d[common], 95)),
            "rotation_rmse_deg": float(np.sqrt(np.mean(a[common] ** 2))),
            "samples": int(common.sum()),
            "fresh_update_grid_coverage": float(valids[name].mean()),
            "invalid_native_rows": invalid,
            "expected_grid_samples": len(grid),
        }
    (folder / "score-3d.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    score(Path(sys.argv[1]))
