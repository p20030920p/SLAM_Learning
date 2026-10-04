#!/usr/bin/env python3
"""Reproduce the KITTI table of the KISS-ICP paper, headlessly.

This is the command-line equivalent of the authors' own notebook
<https://github.com/PRBonn/kiss-icp/blob/main/eval/kitti.ipynb>:

    results = {}
    for sequence in range(0, 11):
        run_sequence(kitti_sequence, sequence=sequence, results=results)
    print_metrics_table(results)

Same dataloader (`kiss_icp.datasets.dataset_factory(dataloader="kitti")`), same
pipeline, same metric definitions — only the notebook cell is replaced by a script,
because there is no display on this machine.  The comparison target is Table II of
the paper (KITTI 00–10, mean relative translational error 0.50 %).

Usage:
    python3 run_kitti_benchmark.py                     # sequences 0–10
    python3 run_kitti_benchmark.py --seq 4             # one sequence
    python3 run_kitti_benchmark.py --out ../results/kiss_icp_kitti.json
"""
import argparse
import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DATA = os.path.normpath(os.path.join(HERE, "..", "data", "raw", "kitti-odometry",
                                             "dataset"))
# the metric the paper's Table II reports
METRIC_TRANSLATION = "Average Translation Error"


def main():
    # the pipeline dumps a timestamped run directory wherever this points; keep it
    # under work/generated/ (gitignored) so a re-run does not churn the results/
    os.environ.setdefault("kiss_icp_out_dir", os.path.join(HERE, "generated", "kiss_icp_logs"))

    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", default=DEFAULT_DATA, help="…/kitti-odometry/dataset")
    ap.add_argument("--seq", nargs="*", type=int, default=list(range(11)))
    ap.add_argument("--out", default=None, help="write the metrics as JSON here")
    ap.add_argument("--reference",
                    default=os.path.join(HERE, "kiss_icp_notebook_reference.json"),
                    help="the authors' own per-sequence numbers, for the side-by-side")
    args = ap.parse_args()

    from kiss_icp.datasets import dataset_factory
    from kiss_icp.pipeline import OdometryPipeline

    data_dir = os.path.abspath(args.data)
    print(f"data: {data_dir}")
    print(f"sequences: {args.seq}\n")

    per_sequence = {}
    metric_names = []
    for seq in args.seq:
        t0 = time.time()
        pipeline = OdometryPipeline(dataset=dataset_factory(
            dataloader="kitti", data_dir=data_dir, sequence=seq))
        result = pipeline.run()
        row = {}
        for metric in result:
            row[metric.desc] = {"value": metric.value, "units": metric.units}
            if metric.desc not in metric_names:
                metric_names.append(metric.desc)
        # the pose the pipeline estimated, saved in KITTI format for later checks
        # (work/generated/ is gitignored: derived data, not a deliverable)
        poses_dir = os.path.join(HERE, "generated", "kiss_icp_kitti_poses")
        os.makedirs(poses_dir, exist_ok=True)
        pipeline.save_poses_kitti_format(os.path.join(poses_dir, f"kiss_icp_kitti_{seq:02d}"),
                                         pipeline.poses)
        row["_frames"] = len(pipeline.poses)
        row["_seconds"] = round(time.time() - t0, 1)
        per_sequence[f"{seq:02d}"] = row
        headline = "  ".join(f"{k} = {v['value']:.4f} {v['units']}"
                             for k, v in row.items() if not k.startswith("_"))
        print(f"seq {seq:02d}: {headline}   ({row['_frames']} frames, {row['_seconds']} s)\n")

    print("| Metric | Value | Units |")
    print("|-:|:-:|:-|")
    for name in metric_names:
        values = [per_sequence[s][name]["value"] for s in per_sequence if name in per_sequence[s]]
        units = per_sequence[next(iter(per_sequence))][name]["units"]
        print(f"{name}| {np.mean(values):.2f}|{units} |")

    comparison = None
    if os.path.exists(args.reference):
        with open(args.reference, encoding="utf-8") as fh:
            ref = json.load(fh)["sequences"]
        common = [s for s in per_sequence if s in ref]
        if common:
            print("\nours vs the authors' own executed notebook"
                  f" ({os.path.basename(args.reference)}):\n")
            print("| seq | ours % | authors % | diff pp |")
            print("| :-- | --: | --: | --: |")
            diffs = {}
            for s in common:
                ours = per_sequence[s][METRIC_TRANSLATION]["value"]
                theirs = ref[s]["translation_error_pct"]
                diffs[s] = round(ours - theirs, 4)
                print(f"| {s} | {ours:.3f} | {theirs:.3f} | {diffs[s]:+.3f} |")
            worst = max(diffs, key=lambda s: abs(diffs[s]))
            comparison = {
                "reference": os.path.basename(args.reference),
                "per_sequence_diff_pp": diffs,
                "max_abs_diff_pp": abs(diffs[worst]),
                "max_abs_diff_sequence": worst,
                "mean_ours_pct": round(float(np.mean([per_sequence[s][METRIC_TRANSLATION]["value"]
                                                      for s in common])), 4),
                "mean_theirs_pct": round(float(np.mean([ref[s]["translation_error_pct"]
                                                        for s in common])), 4),
            }
            print(f"\nlargest per-sequence difference: seq {worst} "
                  f"{diffs[worst]:+.3f} pp\n")

    summary = {
        "protocol": "authors' eval/kitti.ipynb: kiss-icp dataloader 'kitti', sequences 0-10, "
                    "metrics as printed by kiss_icp.pipeline.OdometryPipeline",
        "paper_table": "Tab. II, p.6: KITTI seq. 00-10, relative translational error 0.50 %",
        "data_dir": data_dir,
        "sequences": per_sequence,
        "mean": {name: float(np.mean([per_sequence[s][name]["value"] for s in per_sequence
                                      if name in per_sequence[s]]))
                 for name in metric_names},
        "reference_comparison": comparison,
        "frames_total": sum(r["_frames"] for r in per_sequence.values()),
        "seconds_total": round(sum(r["_seconds"] for r in per_sequence.values()), 1),
    }
    if args.out:
        out = os.path.abspath(args.out)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "w", encoding="utf-8") as fh:
            json.dump(summary, fh, indent=2, ensure_ascii=False)
        print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
