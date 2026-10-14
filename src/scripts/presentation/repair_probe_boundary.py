"""Recover only observer-boundary omissions from the retained emitted-pose log.

No estimates are interpolated or synthesized. Original ROS-observer CSVs remain
portable alongside the timestamp-paired canonical evaluation files.
"""
import csv
import math
import shutil

import numpy as np


def repair(run, folder, name, values, updates, truth, dimension, ground_z=0.):
    emitted = [row for row in updates if row["case"] == name]
    missing = [row for row in emitted if not np.any(np.abs(values[:, 0] - row["stamp_s"]) < 1e-9)]
    if not missing:
        return None
    if any(values[0, 0] <= row["stamp_s"] <= values[-1, 0] for row in missing):
        raise ValueError("A missing interior observer update needs separate diagnosis")
    stamps = np.array([row["stamp_s"] for row in truth])
    additions = []
    for row in missing:
        stamp = row["stamp_s"]
        index = int(np.argmin(abs(stamps - stamp)))
        delta = abs(stamps[index] - stamp)
        if delta > .05:
            raise ValueError("A boundary output has no synchronized independent truth")
        additions.append((row, truth[index], delta))
    source = run / f"{name}-samples.csv"
    shutil.copyfile(source, folder / f"{name}-observer-samples.csv")
    with source.open(newline="") as stream:
        reader = csv.DictReader(stream)
        fields, rows = reader.fieldnames, list(reader)
    for update, measured, delta in additions:
        x, y, heading = update["pose"]
        qx, qy, qz, qw = measured["xyzw"]
        actual_yaw = math.atan2(2 * (qw * qz + qx * qy), 1 - 2 * (qy * qy + qz * qz))
        error_yaw = math.atan2(math.sin(heading - actual_yaw), math.cos(heading - actual_yaw))
        rows.append(dict(zip(fields, [update["stamp_s"], *measured["xyz"][:2], actual_yaw, x, y, heading,
                                      math.hypot(x - measured["xyz"][0], y - measured["xyz"][1]), error_yaw, delta])))
    with (folder / source.name).open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(sorted(rows, key=lambda row: float(row["stamp_s"])))
    if dimension == "3d":
        source = run / f"{name}-poses3d.csv"
        shutil.copyfile(source, folder / f"{name}-observer-poses3d.csv")
        with source.open(newline="") as stream:
            reader = csv.DictReader(stream)
            fields, rows = reader.fieldnames, list(reader)
        for update, measured, delta in additions:
            x, y, heading = update["pose"]
            rows.append(dict(zip(fields, [update["stamp_s"], *measured["xyz"], *measured["xyzw"],
                                          x, y, update.get("z_m", ground_z), 0., 0., math.sin(heading / 2), math.cos(heading / 2), delta])))
        with (folder / source.name).open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(sorted(rows, key=lambda row: float(row["stamp_s"])))
    return {"case": name, "recovered_rows": len(additions), "stamps_s": [row[0]["stamp_s"] for row in additions],
            "source": "actual emitted sensor-only estimator poses in probe-updates.jsonl; nearest independent truth <=0.05s",
            "reason": "ROS observer boundary omission; original observer CSV retained; no interpolation or missing-output zero fill"}
