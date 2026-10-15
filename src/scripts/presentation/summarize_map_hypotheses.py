"""Score shared recording-time grids, retaining missing-output and corridor phase evidence."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pose_errors(path):
    with path.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if not rows:
        return np.empty((0, 3))
    keys = ["stamp_s", *[prefix + key for prefix in ("truth_", "estimate_")
                        for key in ("x", "y", "z", "qx", "qy", "qz", "qw")]]
    values = np.array([[float(row[key]) for key in keys] for row in rows])
    assert np.isfinite(values).all() and (np.diff(values[:, 0]) >= 0).all()
    error = np.linalg.norm(values[:, 8:11] - values[:, 1:4], axis=1)
    q1, q2 = values[:, 4:8], values[:, 11:15]
    q1 = q1 / np.linalg.norm(q1, axis=1)[:, None]
    q2 = q2 / np.linalg.norm(q2, axis=1)[:, None]
    angle = np.degrees(2 * np.arccos(np.clip(np.abs(np.sum(q1 * q2, axis=1)), 0, 1)))
    return np.column_stack([values[:, 0], error, angle])


def grid_scores(streams, start, finish, *, hz=10, max_age=.15):
    grid = np.arange(start, finish, 1 / hz)
    if not len(grid):
        raise ValueError("Empty scoring interval")
    selected, available = {}, {}
    for name, rows in streams.items():
        if not len(rows):
            selected[name] = np.full((len(grid), 3), np.nan)
            available[name] = np.zeros(len(grid), bool)
            continue
        ids = np.searchsorted(rows[:, 0], grid, side="right") - 1
        chosen = rows[np.maximum(ids, 0)]
        selected[name] = chosen
        available[name] = (ids >= 0) & (grid - chosen[:, 0] <= max_age + 1e-8)
    common = np.logical_and.reduce(list(available.values()))
    result = {}
    for name, rows in selected.items():
        valid = available[name]
        paired = rows[common]
        success = valid & (rows[:, 1] < .1) & (rows[:, 2] < 5)
        result[name] = {
            "output_coverage": float(valid.mean()),
            "success_fraction_all_grid": float(success.mean()),
            "common_grid_samples": int(common.sum()),
            "common_xyz_rmse_m": float(np.sqrt(np.mean(paired[:, 1] ** 2))) if common.any() else None,
            "common_xyz_p95_m": float(np.percentile(paired[:, 1], 95)) if common.any() else None,
            "common_rotation_rmse_deg": float(np.sqrt(np.mean(paired[:, 2] ** 2))) if common.any() else None,
            "available_xyz_rmse_m": float(np.sqrt(np.mean(rows[valid, 1] ** 2))) if valid.any() else None,
        }
    raw = result.get("raw")
    if raw and raw["common_xyz_rmse_m"] is not None:
        for value in result.values():
            value["paired_rmse_gain_m"] = raw["common_xyz_rmse_m"] - value["common_xyz_rmse_m"]
    return {"interval_sim_s": [start, finish], "grid_samples": len(grid),
            "common_grid_samples": int(common.sum()), "methods": result}


def summarize(folder):
    scenes = {}
    for scene in ("static", "dynamic", "corridor"):
        source = folder / scene / "localization-3d"
        record = json.loads((source / "record.json").read_text())
        metrics = json.loads((source / "metrics.json").read_text())
        start, finish = metrics["recording_interval_sim_s"]
        methods = ("raw", "dufomap", "beautymap")
        streams = {name: pose_errors(source / f"{name}-poses3d.csv") for name in methods}
        score = grid_scores(streams, start, finish)
        if scene == "corridor":
            events = [json.loads(line) for line in (source / "cloud-stress.jsonl").read_text().splitlines()]
            restored = next(row["stamp_s"] for row in events if row["phase"] == "restored")
            score["limited"] = grid_scores(streams, start, restored)
            score["restored"] = grid_scores(streams, restored, finish)
            full = {name: pose_errors(source / f"full_{name}-poses3d.csv") for name in methods}
            score["full_observations"] = grid_scores(full, start, finish)
        score["map_quality"] = json.loads((folder / scene / "map-quality/record.json").read_text())
        cases = json.loads((source / "cases.json").read_text())
        for method in methods:
            assert cases[method]["map_points_sha256"] == score["map_quality"]["methods"][method]["map_sha256"], \
                "Localization consumed a different map from the scored map"
        assert record["truth_input_to_localizers"] is False
        score["record"] = source.relative_to(ROOT).as_posix() + "/record.json"
        score["source_sha256"] = sha(source / "record.json")
        score["native_metrics_3d"] = record["metrics_3d"]
        scenes[scene] = score
    report = {
        "schema_version": 1, "kind": "map_quality_to_held_out_localization", "status": "executed",
        "protocol_sha256": sha(folder / "protocol.json"), "scenes": scenes,
        "scoring": "10Hz recording-time grid; latest causal native output age <=0.15s; pair RMSE only where all three maps have outputs. Missing outputs count as unsuccessful; report coverage and full grid success separately. No fitted trajectory alignment.",
        "trials_per_scene": 1, "truth_to_localizers": False,
        "limitations": ["Exploratory single run per scene; no population/significance claim",
                        "Given mapping poses; not complete autonomous SLAM",
                        "M4 controlled contamination trend and M5 matched geometry-selection mechanism remain untested"],
    }
    (folder / "summary.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({s: {k: v for k, v in data.items() if k in ("methods", "common_grid_samples")}
                      for s, data in scenes.items()}, indent=2))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    summarize(parser.parse_args().folder)
