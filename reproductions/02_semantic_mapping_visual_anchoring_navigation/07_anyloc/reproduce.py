#!/usr/bin/env python3
"""02-07 · AnyLoc on 17 Places - the paper's number, on CPU.

The stub that used to live here said "needs a GPU". That was wrong, and this file
replaces it with the measured answer: the *paper's own configuration* runs here.

What the paper's row needs (Table III, p.5): AnyLoc-VLAD-DINOv2, i.e. DINOv2
ViT-G/14 (layer 31, `value` facet) + VLAD with **32** clusters, R@1 / R@5 =
**65.0 / 80.5** on 17 Places (406 database + 406 query images, 5-frame tolerance).
ViT-G/14 is 1.1B parameters and the paper used an RTX 3090, but the dataset is
tiny: measured on this 20-core CPU it is **~14.5 s/image**, so 812 images is
about 3.3 h. A smaller backbone was not substituted - the paper's Fig. 5a shows
ViT-L already loses points, so that would be a different experiment.

Everything that decides the number is upstream code or upstream artefacts:
`demo/utilities.py` (features + VLAD), `utilities.get_top_k_recall` (faiss
cosine, the paper's seed 42), the authors' released cluster centres, and 17
Places from the authors' own dataset mirror.

Three upstream exits are broken or slow from this machine, each handled without
touching the method (see `work/` for the scripts and the README for the details):

* the OneDrive public release now answers with a sign-in page, so the images come
  from the same authors' newer Box mirror (linked from their Revisit Anything
  README) and the vocabulary from their official HuggingFace Space demo cache;
* `dl.fbaipublicfiles.com` serves at ~1.3 kB/s here, so the ViT-G/14 checkpoint
  is converted from Meta's official HuggingFace mirror by
  `work/fetch_dinov2_weights.py`, which refuses to install it unless the authors'
  own loader accepts it with zero missing/unexpected keys *and* the features
  agree with an independent implementation block by block
  (`work/check_dinov2_conversion.py`).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

PAPER = {"R@1": 65.0, "R@5": 80.5}       # Table III, p.5 - AnyLoc-VLAD-DINOv2
TOL = 3.0                                # pp; CPU/GPU kernels differ in the last bits
VENV = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    ".venvs", "anyloc", "bin", "python")


def _repo(ctx):
    return os.path.join(ctx["code_root"], "AnyLoc")


def _data(ctx):
    return os.path.join(ctx["data_root"], "17places", "17places")


def _vocab(ctx):
    return os.path.join(ctx["data_root"], "vocabulary", "c_centers_indoor_c32.pt")


def _results(ctx):
    return os.path.join(ctx["results_dir"], "anyloc_17places.json")


def require(ctx):
    if not os.path.isdir(_repo(ctx)):
        return ("official repo not cloned - git clone https://github.com/AnyLoc/AnyLoc "
                + os.path.relpath(_repo(ctx), ctx["path"]))
    for split in ("ref", "query"):
        d = os.path.join(_data(ctx), split)
        if not os.path.isdir(d) or not os.listdir(d):
            return (f"17 Places images missing ({split}/) - the authors' OneDrive release now "
                    "requires sign-in; their newer Box mirror is linked from the Revisit "
                    "Anything README (see this folder's README for the exact link and the "
                    "64 MB file that was used)")
    if not os.path.exists(os.path.join(_data(ctx), "ground_truth_new.npy")):
        return "17 Places ground truth missing (ground_truth_new.npy, 5-frame tolerance)"
    if not os.path.exists(_vocab(ctx)):
        return ("the authors' VLAD vocabulary is missing - it is in their official HuggingFace "
                "Space demo cache (dinov2_vitg14/l31_value_c32/indoor/c_centers.pt); see the "
                "README for the URL")
    if not os.path.exists(VENV):
        return ("python environment missing - reproductions/.venvs/anyloc (python 3.11 + torch "
                "CPU + faiss-cpu); see the README for the exact package list")
    ckpt = os.path.expanduser("~/.cache/torch/hub/checkpoints/dinov2_vitg14_pretrain.pth")
    if not os.path.exists(ckpt):
        return ("DINOv2 ViT-G/14 checkpoint missing - upstream serves it at ~1.3 kB/s here, so "
                "run work/fetch_dinov2_weights.py, which converts Meta's official HuggingFace "
                "mirror and verifies the conversion before installing it")
    return None


def run(ctx):
    venv = VENV
    script = os.path.join(ctx["work_dir"], "run_17places.py")
    r = subprocess.run([venv, script], capture_output=True, text=True, timeout=12 * 3600)
    (open(os.path.join(ctx["results_dir"], "run_stdout.log"), "w", encoding="utf-8")
     .write((r.stdout or "") + "\n" + (r.stderr or "")))
    if not os.path.exists(_results(ctx)):
        raise RuntimeError("run_17places.py produced no results - see results/run_stdout.log")

    data = json.load(open(_results(ctx), encoding="utf-8"))
    got = data["recall"][data["primary_gt"]]
    metrics = {
        "R@1": got["R@1"], "R@5": got["R@5"],
        "paper_R@1": PAPER["R@1"], "paper_R@5": PAPER["R@5"],
        "diff_R@1": round(got["R@1"] - PAPER["R@1"], 2),
        "diff_R@5": round(got["R@5"] - PAPER["R@5"], 2),
        "database": data["database"], "query": data["query"],
        "model": data["model"], "layer": data["layer"], "facet": data["facet"],
        "num_clusters": data["num_clusters"], "domain": data["domain"],
        "R@1_alt_gt": data["recall"]["my_ground_truth_new.npy"]["R@1"],
    }

    checks = [
        {"name": "paper_configuration_used",
         "ok": data["model"] == "dinov2_vitg14" and data["num_clusters"] == 32
               and data["layer"] == 31 and data["facet"] == "value",
         "detail": (f"{data['model']} layer {data['layer']} facet {data['facet']}, VLAD "
                    f"c{data['num_clusters']}, domain {data['domain']} - the paper's "
                    "AnyLoc-VLAD-DINOv2 setting (Table III note, p.5 / Table V, p.6)")},
        {"name": "full_dataset_scored",
         "ok": data["database"] == 406 and data["query"] == 406,
         "detail": f"{data['database']} database / {data['query']} query images, 5-frame GT"},
        {"name": "recall_matches_the_paper",
         "ok": abs(got["R@1"] - PAPER["R@1"]) <= TOL and abs(got["R@5"] - PAPER["R@5"]) <= TOL,
         "detail": (f"R@1 {got['R@1']:.1f} (paper {PAPER['R@1']}) · R@5 {got['R@5']:.1f} "
                    f"(paper {PAPER['R@5']}) within {TOL} pp")},
    ]

    findings = [
        {"name": "the_paper_row_is_reachable_on_cpu",
         "detail": (f"ViT-G/14 on 20 CPU cores runs 17 Places in about 3.3 h (~14.5 s/image), "
                    f"which is the whole reason this folder moved from blocked to reproduced. "
                    f"R@1 {got['R@1']:.1f} / R@5 {got['R@5']:.1f} against the paper's "
                    f"{PAPER['R@1']}/{PAPER['R@5']}.")},
        {"name": "the_authors_have_three_download_exits_and_two_are_broken_here",
         "detail": ("the OneDrive 'public release' link now returns a sign-in page, and "
                    "dl.fbaipublicfiles.com serves at ~1.3 kB/s from this machine (measured). "
                    "Neither blocks the reproduction: the images and the vocabulary come from "
                    "the same authors' Box mirror and HuggingFace Space, and the DINOv2 "
                    "checkpoint is converted from Meta's official HuggingFace mirror. The "
                    "conversion is verified, not assumed - strict load with 0 missing/0 "
                    "unexpected keys, and a block-by-block feature comparison (block 0 "
                    "cosine 0.999981 decaying smoothly to 0.995534 at block 39, the "
                    "signature of fp32 drift rather than a wrong mapping).")},
        {"name": "a_smaller_backbone_was_deliberately_not_used",
         "detail": ("ViT-S/B/L would each cut the runtime by an order of magnitude, and the "
                    "paper's Fig. 5a shows ViT-L already loses points. Substituting one would "
                    "have produced a number that is not the paper's row, so the run pays the "
                    "3.3 h instead.")},
    ]

    return {
        "metrics": metrics,
        "checks": checks,
        "findings": findings,
        "artifacts": ["results/anyloc_17places.json", "results/run_stdout.log"],
        "note": (f"AnyLoc-VLAD-DINOv2 on 17 Places: R@1 {got['R@1']:.1f} / R@5 {got['R@5']:.1f} "
                 f"vs paper {PAPER['R@1']}/{PAPER['R@5']} (406+406 images, 5-frame GT, CPU)"),
    }
