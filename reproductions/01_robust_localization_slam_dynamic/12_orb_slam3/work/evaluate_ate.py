#!/usr/bin/env python3
"""RMS ATE for an ORB-SLAM3 EuRoC run, using the repository's own evaluation tool.

The paper's Table II (p.7) reports RMS ATE in metres for EuRoC, stereo-inertial:
MH01 0.036, MH02 0.033, MH03 0.035, MH04 0.051, MH05 0.082, ... average 0.035.
The note under the table says the comparison is against "the processed GT", and
`evaluation/Ground_truth/EuRoC_imu/` is exactly that: the IMU-frame ground truth
ORB-SLAM3 evaluates against.

So this script does not invent a metric. It
  1. takes the trajectory ORB-SLAM3 wrote (`f_<name>.txt`, TUM format),
  2. cuts `evaluation/Ground_truth/EuRoC_imu/MH_GT.txt` down to the sequence's
     time stamps and converts it to TUM format,
  3. calls the repository's own `evaluation/evaluate_ate_scale.py` and reads the
     RMS ATE it prints.

Usage:
    python3 evaluate_ate.py --run-dir ../results/run_mh01 --gt-seq MH01 \
        --out ../results/orbslam3_mh01_ate.json
"""
import argparse
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", "code", "ORB_SLAM3"))

# Table II, p.7 - stereo-inertial, RMS ATE (m)
PAPER = {"MH01": 0.036, "MH02": 0.033, "MH03": 0.035, "MH04": 0.051, "MH05": 0.082,
         "V101": 0.038, "V102": 0.014, "V103": 0.024, "V201": 0.032, "V202": 0.014,
         "V203": 0.024}


def read_times(path):
    with open(path, encoding="utf-8") as fh:
        return [int(line) for line in fh if line.strip()]


def gt_to_tum(gt_path, t_start, t_end, out_path):
    """MH_GT.txt (header, comma separated, qw qx qy qz) -> TUM (qx qy qz qw)."""
    rows = []
    with open(gt_path, encoding="utf-8") as fh:
        next(fh)
        for line in fh:
            parts = line.strip().split(",")
            if len(parts) < 8:
                continue
            t = int(float(parts[0]))
            if t < t_start or t > t_end:
                continue
            p = parts[1:4]
            qw, qx, qy, qz = parts[4:8]
            rows.append(f"{t} {' '.join(p)} {qx} {qy} {qz} {qw}")
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(rows) + "\n")
    return len(rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run-dir", required=True, help="directory the example wrote into")
    ap.add_argument("--name", default=None, help="file name passed to the example")
    ap.add_argument("--gt-seq", default="MH01", help="which sequence the run was")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    run_dir = os.path.abspath(args.run_dir)
    name = args.name or f"dataset-{args.gt_seq}"
    est = os.path.join(run_dir, f"f_{name}.txt")
    if not os.path.exists(est):
        raise SystemExit(f"no estimated trajectory at {est} - has the run finished?")

    # the time stamps the example was given bound the sequence
    times_file = os.path.join(REPO, "Examples", "Stereo-Inertial", "EuRoC_TimeStamps",
                              f"{args.gt_seq}.txt")
    times = read_times(times_file)
    gt_path = os.path.join(REPO, "evaluation", "Ground_truth", "EuRoC_imu", "MH_GT.txt")
    gt_tum = os.path.join(run_dir, f"gt_{args.gt_seq}_tum.txt")
    n_gt = gt_to_tum(gt_path, times[0] - 1, times[-1] + 1, gt_tum)

    evaluator = os.path.join(REPO, "evaluation", "evaluate_ate_scale.py")
    proc = subprocess.run([sys.executable, evaluator, gt_tum, est, "--plot", "none"],
                          capture_output=True, text=True, cwd=run_dir)
    text = (proc.stdout or "") + (proc.stderr or "")
    print(text.strip()[-1200:])

    m_ate = re.search(r"ATE w\.r\.t\. (?:translation part|rotation part)[^:]*:\s*([0-9.]+)", text)
    m_rmse = re.search(r"RMSE\s*:\s*([0-9.]+)", text)
    rmse = float(m_rmse.group(1)) if m_rmse else None
    ate = float(m_ate.group(1)) if m_ate else None
    n_est = sum(1 for line in open(est, encoding="utf-8") if line.strip())

    result = {
        "run_dir": run_dir,
        "estimated": os.path.basename(est),
        "ground_truth": os.path.relpath(gt_path, REPO),
        "gt_rows_in_sequence_range": n_gt,
        "estimated_poses": n_est,
        "ATE_translation_m": ate,
        "RMSE_m": rmse,
        "evaluator": "code/ORB_SLAM3/evaluation/evaluate_ate_scale.py (upstream's own tool)",
        "paper_value_m": PAPER.get(args.gt_seq),
        "paper_table": "Table II, p.7 - EuRoC, stereo-inertial, RMS ATE in m",
    }
    if rmse is not None and PAPER.get(args.gt_seq):
        result["delta_vs_paper_m"] = round(rmse - PAPER[args.gt_seq], 4)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(result, fh, indent=2, ensure_ascii=False)
        print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
