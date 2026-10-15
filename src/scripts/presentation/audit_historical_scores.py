"""Recompute the historical homepage RMSE from retained AMCL update samples."""

import argparse
import csv
import hashlib
import json
import shutil
from pathlib import Path

import numpy as np

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--benchmark", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
args.output.mkdir(parents=True, exist_ok=True)
summary = list(csv.DictReader((args.benchmark / "summary.csv").open()))
records = []
for condition in ("static", "dynamic", "clean-map-dynamic-test"):
    for method in ("raw", "dufomap", "beautymap"):
        trials = []
        folder = args.benchmark / ("comparison-" + condition)
        for repeat in sorted(folder.glob("repeat-*")) or [folder]:
            repeat_name = repeat.name if repeat != folder else "repeat-01"
            source = repeat / method / "amcl_samples.csv"
            if not source.exists():
                raise FileNotFoundError(source)
            target = args.output / condition / method / (repeat_name + ".csv")
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            rows = list(csv.DictReader(source.open()))
            stamps = np.array([float(row["stamp_sim_s"]) for row in rows])
            error = np.array([float(row["xy_error_m"]) for row in rows])
            calculated = np.array(
                [
                    np.hypot(
                        float(row["estimate_x"]) - float(row["truth_x"]),
                        float(row["estimate_y"]) - float(row["truth_y"]),
                    )
                    for row in rows
                ]
            )
            if not np.allclose(error, calculated, rtol=0, atol=1e-12):
                raise ValueError("Per-update geometry mismatch: " + str(source))
            selected = error[stamps >= stamps.min() + 5]
            if not len(rows) or not len(selected):
                raise ValueError("Empty scoring window: " + str(source))
            trials.append(
                {
                    "repeat": repeat_name,
                    "samples": len(rows),
                    "post_warmup_samples": len(selected),
                    "first_stamp_s": float(stamps.min()),
                    "last_stamp_s": float(stamps.max()),
                    "full_position_rmse_m": float(np.sqrt(np.mean(error**2))),
                    "post_warmup_5s_position_rmse_m": float(np.sqrt(np.mean(selected**2))),
                    "samples_file": str(target.relative_to(args.output)),
                    "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
                }
            )
        actual = float(np.mean([trial["post_warmup_5s_position_rmse_m"] for trial in trials]))
        original = next(row for row in summary if row["condition"] == condition and row["method"] == method)
        expected = float(original["post_warmup_5s_position_rmse_m_mean"])
        if not np.isfinite(actual) or abs(actual - expected) > 1e-12:
            raise ValueError("Historical summary mismatch")
        records.append(
            {
                "condition": condition,
                "method": method,
                "trials": trials,
                "full_position_rmse_m_mean": float(
                    np.mean([trial["full_position_rmse_m"] for trial in trials])
                ),
                "post_warmup_5s_position_rmse_m_mean": actual,
                "original_summary_match": True,
            }
        )
report = {
    "source_benchmark": args.benchmark.name,
    "recomputed": True,
    "entries": records,
    "formula": "sqrt(mean((estimate_x-truth_x)^2 + (estimate_y-truth_y)^2))",
    "window": "AMCL pose updates, stamp >= first matched pose stamp + 5 simulation seconds",
    "aggregation": "arithmetic mean of per-replay RMSE values; repeats replay identical recorded input",
    "coordinates": "same simulator map frame, no fitted SE2 alignment",
    "truth_sync": "original recorder interpolates evaluation-only simulator truth at AMCL update timestamps",
    "video_sampling": "continuous AMCL+odometry predictions differ from scored AMCL update samples",
}
(args.output / "audit.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
print(
    f'Historical scores verified: {len(records)} condition/method entries, {sum(len(r["trials"]) for r in records)} scored CSVs'
)
