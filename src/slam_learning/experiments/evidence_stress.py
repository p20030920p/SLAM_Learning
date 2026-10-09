"""Show why uncertain but correlated observations are not independent confirmations."""
from __future__ import annotations

import csv
import json
import uuid
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.special import expit, logit

from slam_learning.core.provenance import digest, environment, git_state, source_hashes, utc_now, write_json


def change_probability(mean: float, count: int, sensor_sigma: float, pose_sigma: float,
                       motion_sigma: float, prior: float, model: str) -> float:
    if count <= 0 or not 0 < prior < 1:
        raise ValueError("Positive count and nondegenerate prior required")
    if model == "condition_on_pose":
        variance = sensor_sigma**2 / count
    elif model == "independent_pose_noise":
        variance = (sensor_sigma**2 + pose_sigma**2) / count
    elif model == "shared_pose_latent":
        variance = sensor_sigma**2 / count + pose_sigma**2
    else:
        raise ValueError(model)
    alternative = variance + motion_sigma**2
    log_bayes_factor = 0.5 * np.log(variance / alternative) + 0.5 * mean**2 * (1 / variance - 1 / alternative)
    return float(expit(logit(prior) + log_bayes_factor))


def run_evidence_stress(root: Path) -> Path:
    config_path = root / "src/configs/evidence_stress.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    output = root / "results/runs" / f"evidence-stress-{uuid.uuid4().hex[:12]}"
    output.mkdir(parents=True)
    models = ("condition_on_pose", "independent_pose_noise", "shared_pose_latent")
    rows = []
    for seed in range(config["test_seeds_start"], config["test_seeds_start"] + config["test_seeds_count"]):
        rng = np.random.default_rng(seed)
        changed = rng.random() < config["change_prior"]
        displacement = float(rng.normal(0, config["motion_sigma_m"])) if changed else 0.0
        shared_bias = float(rng.normal(0, config["pose_sigma_m"]))
        observations = displacement + shared_bias + rng.normal(0, config["sensor_sigma_m"], max(config["observations"]))
        for count in config["observations"]:
            for model in models:
                p = change_probability(float(observations[:count].mean()), count, config["sensor_sigma_m"],
                    config["pose_sigma_m"], config["motion_sigma_m"], config["change_prior"], model)
                rows.append({"seed": seed, "observations": count, "model": model, "changed": int(changed),
                    "shared_bias_m": shared_bias, "displacement_m": displacement, "probability_change": p,
                    "delete": int(p > config["delete_probability"]), "brier": (p - changed)**2})
    with (output / "trials.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    cells = []
    for model in models:
        for count in config["observations"]:
            subset = [r for r in rows if r["model"] == model and r["observations"] == count]
            static = [r for r in subset if not r["changed"]]
            moving = [r for r in subset if r["changed"]]
            cells.append({"model": model, "observations": count, "trials": len(subset),
                "static_false_delete_rate": float(np.mean([r["delete"] for r in static])),
                "moved_delete_recall": float(np.mean([r["delete"] for r in moving])),
                "brier": float(np.mean([r["brier"] for r in subset])),
                "static_trials": len(static), "changed_trials": len(moving)})
    write_json(output / "summary.json", {"configuration": config, "cells": cells})
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.5), layout="constrained")
    for model, color in zip(models, ("#c24b42", "#d29435", "#167e81")):
        subset = [r for r in cells if r["model"] == model]
        for ax, metric in zip(axes, ("static_false_delete_rate", "brier", "moved_delete_recall")):
            ax.plot([r["observations"] for r in subset], [r[metric] for r in subset], "o-", color=color,
                    label=model.replace("_", " "))
            ax.set(xscale="log", xlabel="Observations sharing the same pose bias", ylabel=metric.replace("_", " "))
    axes[0].legend(fontsize=8)
    fig.suptitle("More evidence cannot average away a shared pose error")
    fig.savefig(output / "calibration.png", dpi=180)
    plt.close(fig)
    record = {"schema_version": 1, "kind": config["kind"], "status": "executed", "finished_at": utc_now(),
        "environment": environment(), "repository": git_state(root), "source_sha256": source_hashes(root),
        "configuration": config, "config_sha256": digest(config_path), "trials": len(rows), "artifacts": {},
        "scope_note": config["scope"]}
    for name in ("trials.csv", "summary.json", "calibration.png"):
        path = output / name
        record["artifacts"][name] = {"sha256": digest(path), "bytes": path.stat().st_size, "availability": "portable"}
    write_json(output / "record.json", record)
    print(f"Correlated evidence experiment: {len(rows)} trials -> {output / 'record.json'}")
    return output / "record.json"
