#!/usr/bin/env python3
"""02-08 · Revisit Anything — needs a GPU; the requirement is recorded, not guessed.

No `run()` here on purpose. The blocker is hardware, and the exact bar is known
from the original paper (see `paper_baseline.md`), so this file only wires that
fact into `run_all.py` so the progress table says *why* instead of "not started".

The paper states no hardware anywhere in its 29 pages; the requirement follows
from the models and from its own descriptor-size table.
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
        'Revisit Anything (ECCV 2024)',
        'a GPU for ViT-G (1.1B) + SAM ViT-H segment descriptors, plus the descriptor store the full benchmark needs (6.65 GB for Pitts-30k)',
        'Baidu Mall / Pitts-30k, public',
        '',
    )
