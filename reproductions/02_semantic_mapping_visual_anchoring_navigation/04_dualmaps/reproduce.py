#!/usr/bin/env python3
"""02-04 · DualMap — needs a GPU; the requirement is recorded, not guessed.

No `run()` here on purpose. The blocker is hardware, and the exact bar is known
from the original paper (see `paper_baseline.md`), so this file only wires that
fact into `run_all.py` so the progress table says *why* instead of "not started".

This is the best-documented hardware requirement of the four D2 bases: the paper
names the GPU in the main experiment (p.6) and in both appendix tables.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "tools"))
from blocked import gpu_blocker  # noqa: E402


def require(ctx):
    return gpu_blocker(
        'DualMap (RA-L 2025)',
        "an NVIDIA RTX 4090 (the paper's main-experiment GPU; RTX 3080 Laptop for the appendix)",
        'Replica, public',
        '',
    )
