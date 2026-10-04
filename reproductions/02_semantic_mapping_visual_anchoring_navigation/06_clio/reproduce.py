#!/usr/bin/env python3
"""02-06 · Clio — needs a GPU; the requirement is recorded, not guessed.

No `run()` here on purpose. The blocker is hardware, and the exact bar is known
from the original paper (see `paper_baseline.md`), so this file only wires that
fact into `run_all.py` so the progress table says *why* instead of "not started".

Clio is the one D2 base that states its compute honestly and claims real-time
onboard operation - which is exactly why CPU substitution is not a valid proxy.
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
        'Clio (RA-L 2024)',
        'an RTX 3090 (24 GB) for FastSAM + CLIP ViT-L/14, or the Spot onboard RTX 4090 Laptop (16 GB)',
        'Replica, public',
        '',
    )
