"""Compare derived geometry on exactly the same elapsed fresh-output grid."""

import csv
import hashlib
import json
from pathlib import Path
import sys
import numpy as np


def compare(base, landmark, out):
    grid = np.arange(5.0, 72.0, 0.1)
    errors = {}
    valids = {}
    inputs = {}
    for scene, folder in [("original", base), ("landmark", landmark)]:
        report = json.loads((folder / "metrics.json").read_text())
        start = report["recording_interval_sim_s"][0]
        truth = [json.loads(line) for line in (folder / "truth.jsonl").read_text().splitlines()]
        t = np.array([r["stamp_s"] for r in truth])
        xy = np.array([r["xyz"][:2] for r in truth])
        target = np.column_stack([np.interp(grid + start, t, xy[:, i]) for i in range(2)])
        for method in ["degraded_raw", "degraded_srrg"]:
            file = folder / f"{method}-samples.csv"
            with file.open() as f:
                rows = list(csv.DictReader(f))
            a = np.array([[float(r[k]) for k in ("stamp_s", "estimate_x", "estimate_y")] for r in rows])
            ids = np.searchsorted(a[:, 0], grid + start, side="right") - 1
            valid = (ids >= 0) & ((grid + start - a[np.maximum(ids, 0), 0]) <= 0.15)
            name = scene + "-" + method
            valids[name] = valid
            errors[name] = a[np.maximum(ids, 0), 1:] - target
            inputs[str(file)] = hashlib.sha256(file.read_bytes()).hexdigest()
    common = np.logical_and.reduce(list(valids.values()))
    methods = {}
    for name, e in errors.items():
        methods[name] = {}
        for phase, mask in [
            ("all", common),
            ("limited", common & (grid < 50)),
            ("restored", common & (grid >= 50)),
        ]:
            q = e[mask]
            d = np.linalg.norm(q, axis=1)
            methods[name][phase] = {
                "samples": len(q),
                "xy_rmse_m": float(np.sqrt(np.mean(d * d))),
                "along_rmse_m": float(np.sqrt(np.mean(q[:, 0] ** 2))),
                "across_rmse_m": float(np.sqrt(np.mean(q[:, 1] ** 2))),
            }
        methods[name]["fresh_coverage"] = float(valids[name].mean())
    report = {
        "schema_version": 1,
        "kind": "corridor_geometry_common_elapsed_grid",
        "status": "executed",
        "exit_code": 0,
        "scope": "Exploratory environment intervention; 10Hz common elapsed grid, pose age<=0.15s across all four methods. Environment changes; no universal algorithmic recovery claim.",
        "common_samples": int(common.sum()),
        "expected_samples": len(grid),
        "methods": methods,
        "inputs": inputs,
    }
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(methods, indent=2))


if __name__ == "__main__":
    compare(*map(Path, sys.argv[1:]))
