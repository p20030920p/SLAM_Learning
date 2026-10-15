"""Recompute errors at common truth timestamps; never hold the old error value."""

import csv
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
from scipy.spatial.transform import Rotation


def score(folder):
    run = json.loads((folder / "metrics.json").read_text())
    truth = [json.loads(x) for x in (folder / "truth.jsonl").read_text().splitlines()]
    ts = np.array([r["stamp_s"] for r in truth])
    xyz = np.array([r["xyz"] for r in truth])
    yaw = np.unwrap(Rotation.from_quat([r["xyzw"] for r in truth]).as_euler("xyz")[:, 2])
    start, end = run["recording_interval_sim_s"]
    grid = np.arange(start + 5, end, 0.1)
    target = np.column_stack([np.interp(grid, ts, xyz[:, i]) for i in range(3)])
    target_yaw = np.interp(grid, ts, yaw)
    output = {}
    validity = {}
    errors = {}
    for name in run["cases"]:
        with (folder / f"{name}-samples.csv").open() as f:
            rows = list(csv.DictReader(f))
        a = np.array(
            [[float(r[k]) for k in ("stamp_s", "estimate_x", "estimate_y", "estimate_yaw")] for r in rows]
        )
        ids = np.searchsorted(a[:, 0], grid, side="right") - 1
        age = grid - a[np.maximum(ids, 0), 0]
        valid = (ids >= 0) & (age <= 0.15)
        est = a[np.maximum(ids, 0)]
        xy = est[:, 1:3] - target[:, :2]
        ang = np.arctan2(np.sin(est[:, 3] - target_yaw), np.cos(est[:, 3] - target_yaw))
        errors[name] = (xy, ang)
        validity[name] = valid
    common = np.logical_and.reduce(list(validity.values()))
    for name, (xy, ang) in errors.items():

        def metrics(mask):
            d = np.linalg.norm(xy[mask], axis=1)
            return (
                {
                    "samples": int(mask.sum()),
                    "rmse_m": float(np.sqrt(np.mean(d * d))),
                    "p95_m": float(np.percentile(d, 95)),
                    "along_x_rmse_m": float(np.sqrt(np.mean(xy[mask, 0] ** 2))),
                    "across_y_rmse_m": float(np.sqrt(np.mean(xy[mask, 1] ** 2))),
                    "yaw_rmse_deg": float(np.rad2deg(np.sqrt(np.mean(ang[mask] ** 2)))),
                    "over_25cm_fraction": float(np.mean(d > 0.25)),
                    "over_10deg_fraction": float(np.mean(np.abs(ang[mask]) > np.deg2rad(10))),
                }
                if len(d)
                else None
            )

        output[name] = {
            "fresh_update_grid_coverage": float(validity[name].mean()),
            "common": metrics(common),
            "limited": metrics(common & (grid < start + 50)),
            "restored": metrics(common & (grid >= start + 50)),
        }
    report = {
        "schema_version": 1,
        "kind": "paired_common_truth_grid_score",
        "status": "executed",
        "exit_code": 0,
        "scope": "10Hz grid after 5s; latest native pose age<=0.15s; errors recomputed against interpolated grid truth; common timestamps across cases. Fresh-update coverage is affected by AMCL motion-triggered publishing and is not tracking-loss rate.",
        "common_grid_samples": int(common.sum()),
        "grid_expected": len(grid),
        "methods": output,
        "inputs": {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in [folder / "metrics.json", folder / "truth.jsonl", *folder.glob("*-samples.csv")]
        },
    }
    (folder / "time-grid-score.json").write_text(json.dumps(report, indent=2) + "\n")
    print(folder.name, json.dumps(output))


if __name__ == "__main__":
    for p in sys.argv[1:]:
        score(Path(p))
