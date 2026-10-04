#!/usr/bin/env python3
"""02-05 · HOV-SG — needs a GPU; the requirement is recorded, not guessed.

No `run()` here on purpose. The blocker is hardware, and the exact bar is known
from the original paper (see `paper_baseline.md`), so this file only wires that
fact into `run_all.py` so the progress table says *why* instead of "not started".

The paper reports no GPU and no timing at all - it only warns that map construction
is 'time-consuming ... unsuitable for real-time mapping'. The bar here is inferred
from its feature-storage table, so even the hardware target is uncertain.
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
        'HOV-SG (RSS 2024)',
        'a GPU for SAM masks plus three CLIP ViT-H-14 encodings per segment; this is the heaviest of the four D2 bases',
        'ScanNet, registration-gated',
        '',
    )
