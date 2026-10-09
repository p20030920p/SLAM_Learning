"""Real-data sensitivity test; preserve GT point identity under injected pose drift."""
from __future__ import annotations

import contextlib
import csv
import json
import traceback
import uuid
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from slam_learning.core.metrics import confusion_metrics
from slam_learning.core.pcd import read_pcd
from slam_learning.core.provenance import digest, environment, git_state, source_hashes, utc_now, write_json
from slam_learning.runtime.runner import MissingRequirement, validate_inputs


def run_pose_stress(root: Path) -> Path:
    output = root / "results/runs" / f"pose-stress-{uuid.uuid4().hex[:12]}"
    output.mkdir(parents=True)
    config_path = root / "configs/pose_stress.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    record = {"schema_version": 1, "kind": "real_data_pose_sensitivity", "status": "running",
              "started_at": utc_now(), "environment": environment(), "repository": git_state(root),
              "source_sha256": source_hashes(root), "configuration": config,
              "config_sha256": digest(config_path), "artifacts": {}}
    write_json(output / "record.json", record)
    try:
        record.update(validate_inputs(root, "dufomap"))
        from dufomap import dufomap
        seq = root / ".cache/datasets/00"
        paths = sorted((seq / "pcd").glob("*.pcd"))[:config["frames"]]
        gt = read_pcd(seq / "gt_cloud.pcd")
        clouds, poses, labels = [], [], []
        start = 0
        for path in paths:
            cloud = read_pcd(path)
            xyz = cloud.xyz()
            stop = start + len(xyz)
            # Refuse silent nearest-neighbor relabeling if the exact point identity is lost.
            if not np.array_equal(xyz, gt.xyz(slice(start, stop))):
                raise ValueError("GT/scan concatenation identity is not exact; diagnostic cannot assign labels")
            clouds.append(xyz)
            poses.append(cloud.viewpoint)
            labels.append(np.array(gt.records["intensity"][start:stop]))
            start = stop
        if start != len(gt.records):
            raise ValueError("This diagnostic requires all teaser frames and exact GT coverage")
        gt_labels = np.concatenate(labels)
        rows, per_frame = [], []
        with (output / "run.log").open("w", encoding="utf-8") as log, contextlib.redirect_stdout(log):
            for dp in config["d_p"]:
                for amplitude in config["translation_amplitudes_m"]:
                    mapper = dufomap(config["resolution_m"], config["d_s_m"], dp, num_threads=config["threads"])
                    shifts = amplitude * np.sin(np.linspace(0, 2 * np.pi, len(clouds)))
                    perturbed, perturbed_poses = [], []
                    for i, (cloud, pose) in enumerate(zip(clouds, poses)):
                        xyz = cloud.copy()
                        xyz[:, 0] += shifts[i]
                        view = pose.copy()
                        view[0] += shifts[i]
                        ranges = np.linalg.norm(xyz - np.asarray(view[:3]), axis=1)
                        mapper.run(xyz[(ranges > 0.2) & (ranges < 50)], view, cloud_transform=False)
                        perturbed.append(xyz)
                        perturbed_poses.append(view)
                    mapper.oncePropagateCluster(if_propagate=True, if_cluster=False)
                    predictions = []
                    for i, (xyz, pose, truth) in enumerate(zip(perturbed, perturbed_poses, labels)):
                        prediction = np.asarray(mapper.segment(xyz, pose, cloud_transform=False))
                        if prediction.shape != truth.shape or not np.isin(prediction, [0, 1]).all():
                            raise ValueError("Invalid segment API labels")
                        predictions.append(prediction)
                        static = truth == 0
                        dynamic = truth == 1
                        per_frame.append({"d_p": dp, "amplitude_m": amplitude, "frame": paths[i].name,
                            "shift_m": float(shifts[i]), "static_points": int(static.sum()),
                            "false_dynamic_static": int(np.count_nonzero(static & (prediction == 1))),
                            "dynamic_points": int(dynamic.sum()),
                            "detected_dynamic": int(np.count_nonzero(dynamic & (prediction == 1)))})
                    prediction = np.concatenate(predictions)
                    metrics = confusion_metrics(gt_labels, prediction)
                    rows.append({"d_p": dp, "amplitude_m": amplitude, **{k: metrics[k] for k in ("SA", "DA", "AA", "HA")},
                                 **metrics["counts"]})
                    print(f"d_p={dp}, amplitude={amplitude}: {metrics}", flush=True)
                    del mapper, perturbed, predictions
        for name, values in (("sensitivity.csv", rows), ("per_frame.csv", per_frame)):
            with (output / name).open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=list(values[0]))
                writer.writeheader()
                writer.writerows(values)
        write_json(output / "summary.json", {"configuration": config, "exact_gt_scan_identity_verified": True,
                                             "gt_points": start, "cells": rows})
        fig, axes = plt.subplots(1, 2, figsize=(8.5, 3.4), layout="constrained")
        for dp, color in zip(config["d_p"], ("#167e81", "#c24b42")):
            selection = [r for r in rows if r["d_p"] == dp]
            for ax, metric in zip(axes, ("SA", "DA")):
                ax.plot([r["amplitude_m"] for r in selection], [r[metric] for r in selection],
                        "o-", label=f"d_p={dp}", color=color)
                ax.set(xlabel="Smooth pose error amplitude (m)", ylabel=f"Point-label {metric} (%)")
                ax.legend()
        fig.suptitle("DUFOMap on real KITTI teaser: exact point-label sensitivity")
        fig.savefig(output / "sensitivity.png", dpi=180)
        plt.close(fig)
        record["status"] = "executed"
        record["scope_note"] = config["scope"]
    except MissingRequirement as e:
        record.update(status="blocked", error=str(e))
    except Exception as e:
        record.update(status="failed", error=str(e), traceback=traceback.format_exc())
    finally:
        record["finished_at"] = utc_now()
        for name in ("run.log", "sensitivity.csv", "per_frame.csv", "summary.json", "sensitivity.png"):
            if (output / name).exists():
                record["artifacts"][name] = {"sha256": digest(output / name),
                    "bytes": (output / name).stat().st_size, "availability": "portable"}
        write_json(output / "record.json", record)
    print(f"Real-data sensitivity: {record['status']} -> {output / 'record.json'}", flush=True)
    return output / "record.json"
