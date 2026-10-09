"""Paired stress test of a structural ambiguity, not an implementation of any paper."""
from __future__ import annotations

import csv
import json
import uuid
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from slam_learning.core.provenance import digest, environment, git_state, source_hashes, utc_now, write_json

METHODS = ("raw_residual", "visibility_only", "common_mode_only", "combined")


def normalize_residual(displacements: np.ndarray, visible: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Translation-only robust pose correction; >50% common movers can fool it."""
    correction = np.median(displacements[visible], axis=0) if visible.any() else np.zeros(2)
    return displacements - correction, correction


def classify_change(displacements: np.ndarray, visible: np.ndarray, threshold: float,
                    normalize: bool, gate_visibility: bool) -> tuple[np.ndarray, np.ndarray]:
    residual, correction = normalize_residual(displacements, visible) if normalize else (displacements, np.zeros(2))
    prediction = (np.linalg.norm(residual, axis=1) > threshold).astype(int)
    # -1 is unknown, not "static"; the unsafe baseline treats absence as deletion.
    prediction[~visible] = -1 if gate_visibility else 1
    return prediction, correction


def summarize(rows: list[dict], config: dict) -> list[dict]:
    rng = np.random.default_rng(8128)
    result = []
    for bias in config["pose_bias_m"]:
        for fraction in config["moved_fraction"]:
            for occlusion in config["occlusion_fraction"]:
                for method in METHODS:
                    selection = [r for r in rows if r["pose_bias_m"] == bias and r["moved_fraction"] == fraction
                                 and r["occlusion_fraction"] == occlusion and r["method"] == method]
                    entry = {"pose_bias_m": bias, "moved_fraction": fraction,
                             "occlusion_fraction": occlusion, "method": method, "seeds": len(selection)}
                    for metric in ("static_false_change_rate", "moved_recall_all", "coverage", "query_error_m", "pose_error_m"):
                        values = np.array([r[metric] for r in selection])
                        samples = rng.choice(values, (config["bootstrap_samples"], len(values)), replace=True).mean(axis=1)
                        entry[metric] = {"mean": float(values.mean()),
                                         "ci95": list(map(float, np.quantile(samples, [0.025, 0.975])))}
                    result.append(entry)
    return result


def plot(summary: list[dict], output: Path) -> None:
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
    fig, axes = plt.subplots(1, 3, figsize=(13, 3.8), layout="constrained")
    colors = ("#c24b42", "#d29435", "#6b68a8", "#167e81")
    for method, color in zip(METHODS, colors):
        selected = [r for r in summary if r["method"] == method and r["moved_fraction"] == 0.2
                    and r["occlusion_fraction"] == 0.5]
        selected.sort(key=lambda r: r["pose_bias_m"])
        for ax, metric in zip(axes[:2], ("static_false_change_rate", "query_error_m")):
            x = [r["pose_bias_m"] for r in selected]
            y = [r[metric]["mean"] for r in selected]
            ax.plot(x, y, "o-", label=method.replace("_", " "), color=color)
            ax.fill_between(x, [r[metric]["ci95"][0] for r in selected],
                            [r[metric]["ci95"][1] for r in selected], alpha=0.12, color=color)
        selected = [r for r in summary if r["method"] == method and r["pose_bias_m"] == 0.3
                    and r["occlusion_fraction"] == 0.0]
        selected.sort(key=lambda r: r["moved_fraction"])
        axes[2].plot([r["moved_fraction"] for r in selected], [r["pose_error_m"]["mean"] for r in selected],
                     "o-", color=color, label=method.replace("_", " "))
    axes[0].set(xlabel="Shared pose bias (m)", ylabel="Static false-change rate", ylim=(-0.02, 1.05),
                title="Occlusion is not evidence of deletion")
    axes[1].set(xlabel="Shared pose bias (m)", ylabel="Object-coordinate error (m)",
                title="Query quality on returned objects")
    axes[2].set(xlabel="Fraction moving together", ylabel="Residual pose bias (m)",
                title="Failure boundary: majority movers")
    axes[0].legend(fontsize=8)
    fig.savefig(output / "mechanism.png", dpi=180)
    fig.savefig(output / "mechanism.svg")
    plt.close(fig)


def run_synthetic(root: Path) -> Path:
    config_path = root / "configs/synthetic.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    output = root / "results/runs" / f"mechanism-{uuid.uuid4().hex[:12]}"
    output.mkdir(parents=True)
    validation = np.concatenate([np.linalg.norm(np.random.default_rng(seed).normal(
        0, config["noise_sigma_m"], (config["objects"], 2)), axis=1) for seed in config["validation_seeds"]])
    threshold = float(np.quantile(validation, config["noise_gate_quantile"]))
    rows = []
    for seed in config["test_seeds"]:
        for bias in config["pose_bias_m"]:
            for fraction in config["moved_fraction"]:
                for occlusion in config["occlusion_fraction"]:
                    # Same randomness for every method AND every factor cell: paired comparisons.
                    rng = np.random.default_rng(seed)
                    n = config["objects"]
                    moved = np.zeros(n, dtype=bool)
                    moved[rng.permutation(n)[:round(n * fraction)]] = True
                    visible = rng.random(n) >= occlusion
                    noise = rng.normal(0, config["noise_sigma_m"], (n, 2))
                    motion = np.column_stack([moved * config["object_displacement_m"], np.zeros(n)])
                    pose_bias = np.array([bias, 0.0])
                    displacements = motion + pose_bias + noise
                    for method in METHODS:
                        prediction, correction = classify_change(displacements, visible, threshold,
                            normalize=method in ("common_mode_only", "combined"),
                            gate_visibility=method in ("visibility_only", "combined"))
                        retained = prediction != 1
                        # Visibility-aware methods abstain from current-coordinate queries for unseen objects.
                        returned = visible if method in ("visibility_only", "combined") else retained | visible
                        updated = np.where((visible & (prediction == 1))[:, None],
                                           displacements - correction, np.zeros_like(displacements))
                        error = np.linalg.norm(updated - motion, axis=1)
                        rows.append({"seed": seed, "pose_bias_m": bias, "moved_fraction": fraction,
                            "occlusion_fraction": occlusion, "method": method,
                            "static_false_change_rate": float(np.mean(prediction[~moved] == 1)),
                            "moved_recall_all": float(np.mean(prediction[moved] == 1)),
                            "coverage": float(returned.mean()),
                            "query_error_m": float(error[returned].mean()) if returned.any() else 0.0,
                            "pose_error_m": float(np.linalg.norm(pose_bias - correction))})
    with (output / "trials.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    summary = summarize(rows, config)
    write_json(output / "summary.json", {"threshold_m": threshold, "configuration": config, "cells": summary})
    plot(summary, output)
    record = {"schema_version": 1, "kind": config["kind"], "status": "executed", "finished_at": utc_now(),
              "environment": environment(), "repository": git_state(root), "source_sha256": source_hashes(root),
              "config_sha256": digest(config_path), "configuration": config, "trials": len(rows),
              "threshold_m": threshold, "artifacts": {}, "scope_note": config["note"]}
    for name in ("trials.csv", "summary.json", "mechanism.png", "mechanism.svg"):
        path = output / name
        record["artifacts"][name] = {"sha256": digest(path), "bytes": path.stat().st_size, "availability": "portable"}
    write_json(output / "record.json", record)
    print(f"Synthetic mechanism experiment: {len(rows)} trials -> {output / 'record.json'}")
    return output / "record.json"
