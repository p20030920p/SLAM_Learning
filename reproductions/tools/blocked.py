#!/usr/bin/env python3
"""Shared `require()` payloads for reproductions this machine cannot run.

`run_all.py` separates two "not done" states on purpose:

    ⬜ planned   no `reproduce.py` yet - nobody has looked closely enough to say
                 what is missing;
    ⛔ blocked   `require(ctx)` returns a string saying exactly what is missing.

For a folder whose blocker is a machine-level fact (no GPU, upstream code not
released), a five-line `reproduce.py` that states the fact is worth more than an
empty folder: the progress table then says *why*, and reviewers can disagree with
a reason instead of guessing at silence.

The facts below come from each folder's `paper_baseline.md` (recorded 2026-10-05,
read off the original PDFs) and, for DynoSAM, from `work/feasibility.md`.
"""

from __future__ import annotations

MACHINE = ("this machine has no GPU (nvidia-smi/nvcc absent, no /usr/local/cuda*); "
           "20-core CPU, 15 GB RAM")


def gpu_blocker(paper, requirement, data="", extra=""):
    """A `require()` string for a reproduction whose blocker is the missing GPU.

    paper       - short name, used as the subject of the sentence
    requirement - what the paper/repo actually needs (from paper_baseline.md)
    data        - datasets the run would need, and whether they are obtainable
    extra       - anything else worth knowing before someone retries this
    """
    parts = [f"{MACHINE}. {paper} needs {requirement}."]
    if data:
        parts.append(f"Data: {data}.")
    parts.append("Recorded in paper_baseline.md, which also lists the paper's own "
                 "headline numbers, so the target is known before the hardware arrives.")
    if extra:
        parts.append(extra)
    return " ".join(parts)
