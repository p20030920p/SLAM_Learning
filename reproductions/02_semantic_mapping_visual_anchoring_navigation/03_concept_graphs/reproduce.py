#!/usr/bin/env python3
"""02-03 · ConceptGraphs — needs a GPU; the requirement is recorded, not guessed.

No `run()` here on purpose. The blocker is hardware, and the exact bar is known
from the original paper (see `paper_baseline.md`), so this file only wires that
fact into `run_all.py` so the progress table says *why* instead of "not started".

The paper never states its hardware; the requirement is derived from the pipeline it
names (SAM + CLIP + LLaVA-7B + GPT-4) - see paper_baseline.md, which records that
grep for GPU/RTX/A100/V100 in the PDF returns nothing.
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
        'ConceptGraphs (ICRA 2024)',
        'a GPU for SAM (ViT-H) + CLIP + LLaVA-7B; the LVLM alone is ~14 GB in fp16, so 16-24 GB of VRAM is the realistic floor, plus a paid GPT-4 (gpt-4-0613) API key for the LLM stage',
        'Replica / HM3D, public',
        '',
    )
