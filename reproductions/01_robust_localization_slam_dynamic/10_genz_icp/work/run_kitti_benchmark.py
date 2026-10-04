#!/usr/bin/env python3
"""Reproduce the KITTI column of the GenZ-ICP paper.

Target: Table III of GenZ-ICP (RA-L 2025) reports the relative translational
error over KITTI odometry 00-10 as **0.51 %** (and KISS-ICP 0.50 % on the same
table). The metric and the data are therefore identical to 01-02's KISS-ICP run,
which makes the two folders a controlled head-to-head: same sequences, same
dataloader family, same metric.

Two things this script does that the plain CLI does not:

1. `config=kitti.yaml`, the pre-tuned parameter set the authors ship for KITTI.
   Without it the pipeline runs on generic defaults and KITTI sequence 04 comes
   out at 5.23 % / ATE 10.10 m instead of 0.39 % / 0.86 m. The CLI takes it with
   `--config kitti.yaml`; here it is passed to the pipeline directly.
2. It replaces `OdometryPipeline.save_poses_tum_format`, which crashes on NumPy 2:
   `float(timestamps[idx])` where the KITTI dataloader hands back a shape-(1,)
   array (the same bug and the same place as kiss-icp 1.3.0 - see 01-02's
   work/local_patches.patch). The crash happens after the metrics are computed,
   so the numbers below are unaffected; the replacement only writes the file.

Usage:
    python3 run_kitti_benchmark.py                       # sequences 0-10
    python3 run_kitti_benchmark.py --seq 4               # one sequence
    python3 run_kitti_benchmark.py --out ../results/genz_icp_kitti.json
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DATA = os.path.normpath(os.path.join(HERE, "..", "data", "raw", "kitti-odometry",
                                             "dataset"))
METRIC_TRANSLATION = "Average Translation Error"
METRIC_ROTATION = "Average Rotational Error"
METRIC_ATE = "Absolute Trajectory Error (ATE)"

# Table III, p.5: relative translational error in % on KITTI 00-10
PAPER_KITTI_00_10 = 0.51
# what this workspace measured for KISS-ICP on the same data (01-02)
KISS_ICP_MEASURED = ("02_kiss_icp", "results/kiss_icp_kitti_official.json")


def patch_tum_writer():
    """NumPy 2 removed float() on a shape-(1,) array; this is the one-line fix."""
    from pyquaternion import Quaternion
    from genz_icp.pipeline import OdometryPipeline

    def fixed(filename, poses, timestamps):
        rows = [[float(np.asarray(timestamps[i]).reshape(-1)[0]),
                 *poses[i, :3, -1].flatten(),
                 *Quaternion(matrix=poses[i], atol=0.01).elements]
                for i in range(len(poses))]
        np.savetxt(fname=f"{filename}_tum.txt", X=np.asarray(rows), fmt="%.4f")

    OdometryPipeline.save_poses_tum_format = staticmethod(fixed)


def main():
    here_results = os.path.normpath(os.path.join(HERE, "..", "results"))
    os.environ.setdefault("genz_icp_out_dir", os.path.join(HERE, "generated", "genz_icp_logs"))

    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", default=DEFAULT_DATA, help="…/kitti-odometry/dataset")
    ap.add_argument("--seq", nargs="*", type=int, default=list(range(11)))
    ap.add_argument("--config", default="kitti.yaml",
                    help="pre-tuned config shipped inside the genz-icp package")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    patch_tum_writer()

    from genz_icp.datasets import dataset_factory
    from genz_icp.pipeline import OdometryPipeline

    data_dir = os.path.abspath(args.data)
    print(f"data:   {data_dir}")
    print(f"config: {args.config}\n")

    per_sequence = {}
    metric_names = []
    for seq in args.seq:
        t0 = time.time()
        pipeline = OdometryPipeline(
            dataset=dataset_factory(dataloader="kitti", data_dir=data_dir, sequence=seq),
            config=Path(args.config))
        result = pipeline.run()
        row = {}
        for metric in result:
            row[metric.desc] = {"value": metric.value, "units": metric.units}
            if metric.desc not in metric_names:
                metric_names.append(metric.desc)
        row["_frames"] = len(pipeline.poses)
        row["_seconds"] = round(time.time() - t0, 1)
        per_sequence[f"{seq:02d}"] = row
        print(f"seq {seq:02d}: " + "  ".join(
            f"{k} = {v['value']:.4f} {v['units']}" for k, v in row.items()
            if not k.startswith("_")) + f"   ({row['_frames']} frames, {row['_seconds']} s)\n")

    print("| Metric | Value | Units |")
    print("|-:|:-:|:-|")
    for name in metric_names:
        values = [per_sequence[s][name]["value"] for s in per_sequence if name in per_sequence[s]]
        units = per_sequence[next(iter(per_sequence))][name]["units"]
        print(f"{name}| {np.mean(values):.2f}|{units} |")

    mean = {name: float(np.mean([per_sequence[s][name]["value"] for s in per_sequence
                                 if name in per_sequence[s]]))
            for name in metric_names}

    # KISS-ICP on the same sequences, measured in 01-02 - the paper's own
    # comparison row, so it belongs next to this one.
    kiss = None
    repo_root = os.path.abspath(os.path.join(HERE, "..", ".."))
    kiss_path = os.path.join(repo_root, KISS_ICP_MEASURED[0], KISS_ICP_MEASURED[1])
    if os.path.exists(kiss_path):
        with open(kiss_path, encoding="utf-8") as fh:
            kiss = json.load(fh)["mean"]
        print(f"\nKISS-ICP on the same data (01-02): "
              f"{kiss[METRIC_TRANSLATION]:.2f} % / {kiss[METRIC_ATE]:.2f} m")
        print(f"GenZ-ICP here:                     "
              f"{mean[METRIC_TRANSLATION]:.2f} % / {mean[METRIC_ATE]:.2f} m")

    summary = {
        "protocol": "genz_icp python API: dataloader 'kitti', pre-tuned kitti.yaml, "
                    "sequences 0-10, metrics as printed by genz_icp.pipeline",
        "paper_table": "GenZ-ICP Table III, p.5: KITTI seq. 00-10, relative translational "
                       "error 0.51 % (KISS-ICP 0.50 % in the same table)",
        "config": args.config,
        "data_dir": data_dir,
        "sequences": per_sequence,
        "mean": mean,
        "kiss_icp_same_data": kiss,
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
