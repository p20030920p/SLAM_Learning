#!/usr/bin/env python3
"""02-07 · AnyLoc — needs a GPU; the requirement is recorded, not guessed.

No `run()` here on purpose. The blocker is hardware, and the exact bar is known
from the original paper (see `paper_baseline.md`), so this file only wires that
fact into `run_all.py` so the progress table says *why* instead of "not started".

The official repo has been cloned to `code/AnyLoc` and its demo script is a real
entry point; what cannot be reproduced without a GPU is the *paper's* number, which
is tied to ViT-G14. A smaller backbone would be a different experiment.
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
        'AnyLoc (RA-L 2023)',
        'an RTX 3090-class GPU for the ViT-G14 backbone the headline number uses (1.1B parameters; 10k database + 6.8k query images for Pitts-30k)',
        'Baidu Mall / Pitts-30k / other VPR sets; the AnyLoc repo ships a demo and the vocabulary cache is a public OneDrive link',
        '',
    )
