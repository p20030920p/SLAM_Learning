"""Author the synthetic occupancy maps that synthetic_dataset.py / Generate_Path.py expect.

Upstream AdaM_MCL ships an empty Dataset/ directory: the simulation maps, the
Bicocca extraction and the UPO sequences are all external downloads. This script
creates only the *input layouts* the released code needs, in the exact directory
and pixel format the released data generator reads:

    Dataset/simulation/map_<n>/map.png        128x128 uint8, free = 0, occupied = 255

The layouts are deterministic (fixed seed) so the numbers in our record can be
re-derived. They are our own authored input, not the authors' data.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np

FREE, OCCUPIED = 0, 255


def room_layout(rng: np.random.Generator, size: int = 128) -> np.ndarray:
    """Outer wall plus a grid of rooms joined by doorways (palace-like plan)."""
    plan = np.zeros((size, size), dtype=np.uint8)
    plan[0:2, :] = OCCUPIED
    plan[-2:, :] = OCCUPIED
    plan[:, 0:2] = OCCUPIED
    plan[:, -2:] = OCCUPIED
    splits = [0, size // 2, size]
    for index in range(1, len(splits) - 1):
        position = splits[index] + int(rng.integers(-6, 7))
        plan[2:-2, position : position + 2] = OCCUPIED
        plan[position : position + 2, 2:-2] = OCCUPIED
        for _ in range(3):
            gap = int(rng.integers(6, size - 6))
            plan[gap : gap + 6, position : position + 2] = FREE
            gap = int(rng.integers(6, size - 6))
            plan[position : position + 2, gap : gap + 6] = FREE
    columns = rng.integers(20, size - 20, size=12)
    rows = rng.integers(20, size - 20, size=12)
    for column, row in zip(columns, rows, strict=True):
        cv2.rectangle(plan, (int(column), int(row)), (int(column) + 2, int(row) + 2), OCCUPIED, -1)
    return plan


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-root", type=Path, default=Path("../Dataset/simulation"))
    parser.add_argument("--maps", type=int, default=21)
    args = parser.parse_args()
    root = args.dataset_root.resolve()
    for number in range(1, args.maps + 1):
        rng = np.random.default_rng(20210000 + number)
        plan = room_layout(rng)
        directory = root / f"map_{number}"
        directory.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(directory / "map.png"), plan)
    (root / "Data_Transformed/Test_MCL").mkdir(parents=True, exist_ok=True)
    # A hold-out layout: distinct seed, so the evaluated scene is not one of the
    # training/validation maps (paper: train on 18 maps, test on 2 unseen ones).
    cv2.imwrite(str(root / "Data_Transformed/Test_MCL/global_map.png"), room_layout(np.random.default_rng(20219999)))
    print(f"wrote {args.maps} maps and the global evaluation map under {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
