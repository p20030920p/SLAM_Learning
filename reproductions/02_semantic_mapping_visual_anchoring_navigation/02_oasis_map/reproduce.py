#!/usr/bin/env python3
"""02-02 · OASIS-Map — excluded by the workspace's own rule, not by failure.

The rule this workspace runs on is: reproduce from the authors' code, and when
there is no code, do not pretend to reproduce the paper. OASIS-Map has no code
to run.

Checked 2026-10-05:

  * the project page is up and says **"Code Soon"** - no repository link;
  * the paper (arXiv 2026-07) is under review, so there is no artifact to pin;
  * what the folder *can* do without code is read the paper, and that is already
    done - see `paper_baseline.md` (its 3RScan moved-F1 0.353 / static-F1 0.663
    and Car Park replaced-F1 0.783) and the correction recorded in
    `../README.md` §"一处必须修正的判断": OASIS-Map **does** have an Unknown class
    ("If an object is not seen in one of the sessions, it remains Unknown"), so
    the differentiator for our own work cannot be "add an abstain class" - it has
    to be making observability a *calibrated* quantity and measuring it in layers.

When the code is released, this file is where the real `run()` goes: OASIS-Map's
own pipeline (semantic correspondence matching over multi-session RGB-D) plus the
3RScan revisit pair already used by 02-01.
"""

from __future__ import annotations


def require(ctx):
    return ("no upstream code to run: the OASIS-Map project page (checked 2026-10-05) "
            "still says 'Code Soon' and the paper is under review, so by this workspace's "
            "rule - reproduce from the authors' code or not at all - this folder stays a "
            "paper study. What it does contribute is recorded in paper_baseline.md and in "
            "the README's correction about its Unknown class.")
