"""Recompute the formal batch summary, including missing data and false accepts."""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from slam_learning.core.provenance import digest
from slam_learning.runtime.presentation_evidence import read_samples, restoration
from slam_learning.runtime.runner import verify_record

ROOT = Path(__file__).resolve().parents[3]

COLORS = {"plain": "#e24a4a", "guard": "#b28a00", "depth": "#e88718",
          "search": "#a64cce", "recover": "#159969", "native": "#2785c9"}


def summarize(path, plot):
    issues = verify_record(path)
    if issues:
        raise ValueError(issues)
    record = json.loads(path.read_text())
    runtime = json.loads((path.parent / "runtime.json").read_text())
    frames = json.loads((path.parent / "probe-B-inputs.json").read_text())["frames"]
    updates = [json.loads(line) for line in (path.parent / "probe-updates.jsonl").read_text().splitlines()]
    start = frames[0]["stamp_s"]
    methods = {}
    arrays = {}
    for name, metric in record["metrics"]["cases"].items():
        array = read_samples(path.parent / f"{name}-samples.csv")
        arrays[name] = array
        accepted = [row for row in updates if row["case"] == name and row["relocalized"]]
        bad_accepts, unscored_accepts = 0, 0
        for row in accepted:
            candidate = array[np.abs(array[:, 0] - row["stamp_s"]) < 1e-9]
            if not len(candidate):
                unscored_accepts += 1
            elif candidate[0, 7] >= .1 or abs(candidate[0, 8]) >= np.radians(5):
                bad_accepts += 1
        initial = restoration(array, start)
        methods[name] = {
            "xy_rmse_cm": metric["position_rmse_m"] * 100,
            "xyz_rmse_cm": record.get("metrics_3d", {}).get(name, {}).get("xyz_rmse_m", 0.) * 100 if record["hypothesis_probes"]["dimension"] == "3d" else None,
            "samples": len(array), "first_output_s": float(array[0, 0]), "last_output_s": float(array[-1, 0]),
            "max_output_gap_s": float(np.max(np.diff(array[:, 0]))),
            "initial_sustained_delay_from_first_probe_output_s": initial["sustained_convergence_delay_s"],
            "initial_sustained_status": initial["converged"],
            "candidate_acceptance_events": len(accepted), "wrong_acceptance_events": bad_accepts,
            "unscored_acceptance_events": unscored_accepts,
            "restoration": record.get("restoration", {}).get(name),
        }
    pairs = {}
    key = "xyz_rmse_cm" if record["hypothesis_probes"]["dimension"] == "3d" else "xy_rmse_cm"
    for label, before, after in (("H1", "plain", "guard"), ("H2", "guard", "depth"),
                                 ("H3_lidar", "guard", "search"), ("H3_depth", "depth", "recover"),
                                 ("depth_in_recovery", "search", "recover")):
        pairs[label] = {"before": before, "after": after,
                        "after_minus_before_cm": methods[after][key] - methods[before][key]}
    result = {"source_record": str(path), "source_record_sha256": digest(path),
              "dimension": record["hypothesis_probes"]["dimension"], "scene": runtime["scene"],
              "shared_prototype_frames": len(frames),
              "depth_used_frames": sum(row["depth_points"] >= 12 for row in frames),
              "depth_stale_or_absent_frames": sum(row["depth_delta_s"] is None or row["depth_delta_s"] > .12 for row in frames),
              "depth_synchronized_empty_frames": sum(row["depth_points"] < 12 and row["depth_delta_s"] is not None and row["depth_delta_s"] <= .12 for row in frames),
              "comparisons": pairs, "methods": methods,
              "source_sha256": record["hypothesis_probes"]["source_sha256"]}
    prefix = "probe-calibrated" if "ground_z_m" in record["hypothesis_probes"] else "probe"
    result["public_record"] = f"results/reference/{prefix}-{result['dimension']}-{result['scene']}/record.json"
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(2, 1, figsize=(10, 6), sharex=True, gridspec_kw={"height_ratios": [3, 1]})
    for name, color in COLORS.items():
        array = arrays[name]
        distance = array[:, 7]
        if key == "xyz_rmse_cm":
            poses = np.genfromtxt(path.parent / f"{name}-poses3d.csv", delimiter=",", names=True)
            distance = np.sqrt(sum((poses["estimate_" + axis] - poses["truth_" + axis]) ** 2 for axis in "xyz"))
        axes[0].plot(array[:, 0] - start, np.maximum(distance * 100, .001), color=color, label=name, linewidth=1.2)
        axes[1].plot(array[:, 0] - start, np.abs(np.degrees(array[:, 8])), color=color, linewidth=1.)
    axes[0].set_yscale("log")
    axes[0].set_ylabel("XYZ error (cm)" if key == "xyz_rmse_cm" else "XY error (cm)")
    axes[1].set_ylabel("|yaw| (deg)")
    axes[1].set_xlabel("Simulation seconds from first prototype output")
    axes[0].legend(ncol=3, fontsize=9)
    for axis in axes:
        axis.grid(alpha=.25)
    recovery = next(iter(record.get("restoration", {}).values()), None)
    if recovery:
        for axis in axes:
            axis.axvline(recovery["restore_stamp_s"] - start, color="#555555", linestyle="--", linewidth=1)
        axes[0].text(recovery["restore_stamp_s"] - start, .98, " lidar restored", transform=axes[0].get_xaxis_transform(), va="top", fontsize=9)
    fig.suptitle(f"{result['dimension'].upper()} / {result['scene']} — saved outputs, independent truth\nSingle trial; gaps are not filled; 3D prototypes constrain ground-robot motion", fontsize=11)
    fig.tight_layout()
    plot.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(plot, dpi=150)
    plt.close(fig)
    result["plot_sha256"] = digest(plot)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("batch", type=Path)
    parser.add_argument("--calibrated", action="store_true")
    args = parser.parse_args()
    batch = json.loads(args.batch.read_text(encoding="utf-8-sig"))
    if batch["status"] != "completed" or len(batch["runs"]) != 10:
        raise ValueError("A complete 10-condition batch is required; retain partial batches as diagnostics")
    output = ROOT / "results/analysis/hypotheses"
    protocol_name = "calibrated-protocol.json" if args.calibrated else "protocol.json"
    protocol = json.loads((output / protocol_name).read_text())
    values = []
    for run in batch["runs"]:
        path = Path(run["path"]) / "evidence/record.json"
        prefix = "calibrated-" if args.calibrated else ""
        row = summarize(path, output / f"{prefix}{run['dimension'].lower()}-{run['scene']}-errors.png")
        if any(row["source_sha256"][name] != protocol["source_sha256"][name] for name in row["source_sha256"]):
            raise ValueError("Formal prototype source differs from the frozen protocol")
        values.append(row)
    summary_name = "calibrated-summary.json" if args.calibrated else "summary.json"
    (output / summary_name).write_text(json.dumps({"batch": batch, "protocol_sha256": digest(output / protocol_name), "conditions": values}, indent=2) + "\n")
    print(json.dumps([{key: row[key] for key in ("dimension", "scene", "comparisons", "depth_used_frames", "shared_prototype_frames")} for row in values], indent=2))


if __name__ == "__main__":
    main()
