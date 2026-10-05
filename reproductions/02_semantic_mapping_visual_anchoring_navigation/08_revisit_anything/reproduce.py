#!/usr/bin/env python3
"""02-08 · Revisit Anything (SegVLAD) on 17Places - the paper's row, on CPU.

The folder was filed as GPU-blocked because the method is SAM + DINOv2 + VLAD.
That is true for *building* the descriptors, and unnecessary for reproducing the
number: the authors ship the preprocessed pack (`17places_full.zip`, 11.1 GB from
their own Box mirror - it contains `out/*.h5` with the per-segment DINO features
and masks plus the fitted PCA model), so the pipeline that produces Table 2 runs
on CPU in about 25 minutes.

Result on the paper's default configuration (`exp0_global_SegLoc_VLAD_PCA_o3`,
order 3 with PCA) with the shipped **map** vocabulary, full 406/406:

    R@1 95.32 · R@2 97.04 · R@3 97.29 · R@4 97.78 · R@5 98.28
    paper Table 2 p.9, 17Places, SegVLAD-PreT (D)/(M): R@1 95.3 / R@5 98.0

Read the README before comparing this to 02-07: the two folders report "17Places
R@1" under *different GT windows* (this repo's `gt.py` uses loc_rad = 15, i.e.
±15 frames; AnyLoc uses the dataset's own ±5-frame ground truth). 95.3 vs 65.0 is
the protocol, not the method.

Two local patches, both recorded in `work/local_patches.patch` and neither one
touching the algorithm:

  * `workdir_data` repointed at this folder's data directory (upstream points at
    one author's home directory);
  * CUDA is hardcoded in the aggregation path (`_DEV` now resolves to cuda when
    available, cpu otherwise - identical behaviour on a GPU box).

The map-vocabulary PCA model ships in the pack; the domain-vocabulary one does
not, which is why this runs `--vocab-vlad map`. The paper lists (D) and (M) as
tied at 95.3/98.0 for this dataset, so the row is still the paper's row.
"""

from __future__ import annotations

import json
import os
import re
import subprocess

PAPER = {"R@1": 95.3, "R@5": 98.0}       # Table 2, p.9 - SegVLAD-PreT
TOL = 1.5                                # pp; the log prints two decimals
EXPERIMENT = "exp0_global_SegLoc_VLAD_PCA_o3"


def _repo(ctx):
    return os.path.join(ctx["code_root"], "Revisit-Anything")


def _workdir(ctx):
    return os.path.join(ctx["data_root"], "workdir_root")


def _venv(ctx):
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        ".venvs", "anyloc", "bin", "python")


def _log(ctx):
    return os.path.join(ctx["work_dir"], "logs", "segloc_17places_map.log")


def _results(ctx):
    return os.path.join(ctx["results_dir"], "segloc_17places.json")


def require(ctx):
    repo = _repo(ctx)
    if not os.path.isdir(repo):
        return ("official repo not cloned - git clone https://github.com/AnyLoc/Revisit-Anything "
                + os.path.relpath(repo, ctx["path"]))
    out = os.path.join(_workdir(ctx), "17places", "out")
    if not os.path.exists(os.path.join(out, "17places_r_masks_320.h5")):
        return (f"preprocessed pack missing - the authors' Box mirror ships 17places_full.zip "
                f"(11.1 GB: out/*.h5 with per-segment DINO features, masks and the fitted PCA "
                f"model); extract it so that {os.path.relpath(out, ctx['path'])} holds the .h5 "
                "files (see the README for the link)")
    for f in ("17places_r_fitted_pca_model_order3_map.pkl",
              "17places_r_dino_640.h5", "17places_q_dino_640.h5"):
        if not os.path.exists(os.path.join(out, f)):
            return f"preprocessed pack incomplete ({f} missing under 17places/out/)"
    vocab = os.path.join(repo, "cache", "vocabulary", "dinov2_vitg14", "l31_value_c32",
                         "17places", "c_centers.pt")
    if not os.path.exists(vocab):
        return ("the shipped VLAD vocabulary is missing (cache/vocabulary/dinov2_vitg14/"
                "l31_value_c32/17places/c_centers.pt) - it is part of the upstream checkout")
    if not os.path.exists(_venv(ctx)):
        return ("python environment missing - reproductions/.venvs/anyloc (torch CPU, faiss-cpu, "
                "pytorch_lightning, wandb, pytorch_metric_learning, prettytable, pandas, h5py, "
                "opencv-python-headless, plus the repo's bundled `sam` package installed with "
                "`pip install -e sam`); see the README")
    func_vpr = os.path.join(repo, "func_vpr.py")
    if "_DEV" not in open(func_vpr, encoding="utf-8").read():
        return ("the CPU device patch is not applied - upstream hardcodes cuda in the "
                "aggregation path; apply work/local_patches.patch")
    cfg = os.path.join(repo, "place_rec_global_config.py")
    if str(_workdir(ctx)) not in open(cfg, encoding="utf-8").read():
        return ("workdir_data in place_rec_global_config.py does not point at this folder's data "
                "directory; apply work/local_patches.patch")
    return None


def run(ctx):
    repo = _repo(ctx)
    env = dict(os.environ, PYTHONPATH=os.path.join(repo, "VLAD-BuFF"))
    cmd = [_venv(ctx), "place_rec_main.py", "--dataset", "17places", "--experiment", EXPERIMENT,
           "--vocab-vlad", "map", "--save-results"]
    r = subprocess.run(cmd, cwd=repo, env=env, capture_output=True, text=True, timeout=4 * 3600)
    os.makedirs(os.path.dirname(_log(ctx)), exist_ok=True)
    open(_log(ctx), "w", encoding="utf-8").write((r.stdout or "") + "\n" + (r.stderr or ""))

    text = r.stdout or ""
    m = re.search(r"Max Seg Logs:\s*\[([^\]]+)\]", text)
    if not m:
        raise RuntimeError("the pipeline produced no recall line - see work/logs/")
    recall = [round(float(v) * 100, 2) for v in m.group(1).split(",")]
    pos = re.search(r"POSITIVES/TOTAL[^:]*:\s*\[([^\]]+)\]\s*/\s*(\d+)", text)

    metrics = {
        "R@1": recall[0], "R@5": recall[-1],
        "paper_R@1": PAPER["R@1"], "paper_R@5": PAPER["R@5"],
        "diff_R@1": round(recall[0] - PAPER["R@1"], 2),
        "diff_R@5": round(recall[-1] - PAPER["R@5"], 2),
        "recall_R@1_to_R@5": recall,
        "query_images": int(pos.group(2)) if pos else None,
    }
    os.makedirs(ctx["results_dir"], exist_ok=True)
    json.dump({"metrics": metrics, "command": " ".join(cmd), "experiment": EXPERIMENT,
               "vocab_vlad": "map"},
              open(_results(ctx), "w", encoding="utf-8"), indent=2, ensure_ascii=False)

    checks = [
        {"name": "paper_configuration_used",
         "ok": EXPERIMENT == "exp0_global_SegLoc_VLAD_PCA_o3",
         "detail": ("the paper's default experiment (neighbour aggregation order 3 + PCA, from "
                    "the README's 'Running the code'); the vocabulary variant is the shipped map "
                    "one, and Table 2 lists (D) and (M) as tied for this dataset")},
        {"name": "full_dataset_scored",
         "ok": metrics["query_images"] == 406,
         "detail": f"{metrics['query_images']} query images against the 406-image database"},
        {"name": "recall_matches_the_paper",
         "ok": (abs(metrics["R@1"] - PAPER["R@1"]) <= TOL
                and abs(metrics["R@5"] - PAPER["R@5"]) <= TOL),
         "detail": (f"R@1 {metrics['R@1']:.2f} (paper {PAPER['R@1']}) · R@5 {metrics['R@5']:.2f} "
                    f"(paper {PAPER['R@5']}) within {TOL} pp")},
    ]

    findings = [
        {"name": "the_row_reproduces_on_cpu_with_the_released_pack",
         "detail": (f"R@1 {metrics['R@1']:.2f} / R@5 {metrics['R@5']:.2f} against the paper's "
                    f"{PAPER['R@1']}/{PAPER['R@5']}; ~25 min on CPU, because the segmentation "
                    "and DINO features are precomputed upstream. Only the aggregation stage runs "
                    "here - which is exactly what Table 2 measures.")},
        {"name": "17places_r1_differs_by_30_points_between_the_two_papers",
         "detail": ("Revisit Anything reports 95.3 and AnyLoc reports 65.0 for '17Places' with the "
                    "same backbone. The cause is this repo's gt.py:63 - loc_rad = 15, so a query "
                    "counts as correct if any of 31 database frames is retrieved - while AnyLoc "
                    "uses the dataset's own ground_truth_new.npy with a 5-frame window (6 "
                    "candidates). The candidate sets differ 5x, so the numbers are not "
                    "comparable; each folder reports against its own paper's criterion.")},
        {"name": "only_the_map_vocabulary_pca_ships",
         "detail": ("the pack contains 17places_r_fitted_pca_model_order3_map.pkl and the two "
                    "dinoNV variants, but not the domain-vocabulary model the config lists as "
                    "pca_model_pkl, so --vocab-vlad domain stops at a missing file. The map "
                    "variant uses only shipped artefacts, and the paper reports (D) and (M) as "
                    "tied for 17Places, so the comparison stays honest.")},
        {"name": "upstream_hardcodes_cuda_in_the_aggregation_path",
         "detail": ("func_vpr.aggFt moves tensors with .to('cuda') and place_rec_main builds "
                    "torch.device('cuda'), with no CPU fallback, so the PreT pipeline does not run "
                    "on a CPU-only machine out of the box. work/local_patches.patch makes the "
                    "device conditional - identical behaviour wherever CUDA exists.")},
    ]

    return {
        "metrics": metrics,
        "checks": checks,
        "findings": findings,
        "artifacts": ["results/segloc_17places.json", "work/logs/segloc_17places_map.log"],
        "note": (f"SegVLAD-PreT on 17Places: R@1 {metrics['R@1']:.2f} / R@5 {metrics['R@5']:.2f} "
                 f"vs paper {PAPER['R@1']}/{PAPER['R@5']} (406+406, CPU, map vocabulary)"),
    }
