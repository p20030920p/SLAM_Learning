"""Report the kidnapping update index and pose jump of every released evaluation sequence."""

import sys
from pathlib import Path

import numpy as np

root = Path("../Dataset/simulation/Data_Transformed/Test_MCL")
for sequence in sorted(root.iterdir()):
    gt = sequence / "gt_pose.txt"
    if not gt.is_file():
        continue
    pose = np.loadtxt(gt, ndmin=2)
    steps = np.linalg.norm(np.diff(pose[:, :2], axis=0), axis=1)
    index = int(np.argmax(steps)) + 1
    print(f"{sequence.name:>3}  frames={len(pose):4d}  kidnapping_update_index={index:4d}  "
          f"jump_cells={steps[index - 1]:6.2f}  median_step_cells={np.median(steps):5.3f}")
