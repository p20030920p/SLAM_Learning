#!/usr/bin/env python3
"""01-01 · DynamicMap_Benchmark — automated reproduction of the benchmark itself.

This folder is not a method, it is the ground everything else stands on: one
sequence, one ground truth, one evaluation rule. So what gets reproduced here is
the *measurement*, not a score:

  - the sequence and its ground truth are intact (141 frames, 17,362,230 points,
    labels binary, 0.55% dynamic);
  - the evaluation rule is implemented twice and both implementations agree on
    the ground-truth labels - the official C++ `export_eval_pcd` and an
    independent scipy rewrite;
  - the four methods that depend on this folder are collected and ranked.

The last point produces the finding this whole folder exists to support. Because
dynamic points are 0.55% of the map, a method can score near-perfect SA by
deleting nothing at all, and the same four methods order differently under SA
than under AA. That is the task book's section 6 ranking-stability question,
answered from the benchmark's own numbers.
"""

from __future__ import annotations

import json
import os
import sys

# How many GT points the cross-check samples. The full 17.4M run is ~60 s and
# has been done; this is the per-run regression guard.
CROSSCHECK_POINTS = 3_000_000

METHOD_IDS = {"01-03": "ERASOR", "01-04": "Removert", "01-05": "DUFOMap", "01-06": "BeautyMap"}


def _seq_dir(ctx):
    local = os.path.join(ctx["data_root"], "00")
    return local if os.path.isdir(os.path.join(local, "pcd")) else None


def _eval_bin(ctx):
    return os.path.join(ctx["code_root"], "DynamicMap_Benchmark", "scripts", "build",
                        "export_eval_pcd")


def require(ctx):
    seq = _seq_dir(ctx)
    if seq is None:
        return ("sequence 00 not found - wget "
                "https://zenodo.org/records/10886629/files/00.zip and unzip into "
                "this folder's data/raw/ (385 MB, no KITTI registration)")
    if not os.path.exists(_eval_bin(ctx)):
        return ("export_eval_pcd not built - cmake -S "
                "code/DynamicMap_Benchmark/scripts -B code/DynamicMap_Benchmark/scripts/build "
                "&& cmake --build code/DynamicMap_Benchmark/scripts/build")
    return None


def run(ctx):
    sys.path.insert(0, ctx["work_dir"])
    import numpy as np
    from evaluate import read_pcd, export_gt_official, export_gt_python  # noqa: E402

    seq = _seq_dir(ctx)
    gt = read_pcd(os.path.join(seq, "gt_cloud.pcd"))
    gt_labels = gt[:, 3]
    frames = sorted(f for f in os.listdir(os.path.join(seq, "pcd")) if f.endswith(".pcd"))
    n_static = int(np.count_nonzero(gt_labels == 0))
    n_dynamic = int(np.count_nonzero(gt_labels == 1))
    unlabelled = int(len(gt_labels) - n_static - n_dynamic)

    # ---- the four methods that live on this benchmark --------------------
    scores, missing = {}, []
    for rid, name in METHOD_IDS.items():
        folder = os.path.normpath(os.path.join(ctx["path"], "..",
                                               {"01-03": "03_erasor", "01-04": "04_removert",
                                                "01-05": "05_dufomap", "01-06": "06_beautymap"}[rid]))
        found = None
        results = os.path.join(folder, "results")
        if os.path.isdir(results):
            # method folders name their scores differently
            # (erasor_score.json, dufomap_score_paper_default_dp1.json, ...)
            for f in sorted(os.listdir(results)):
                if not (f.endswith(".json") and "score" in f):
                    continue
                with open(os.path.join(results, f), encoding="utf-8") as fh:
                    payload = json.load(fh)
                if "official" not in payload:
                    continue
                # a folder may hold several configs; keep the one that is not an
                # explicitly-marked variant (d_p=2, benchmark example, ...)
                if found is None or "dp2" not in payload.get("method", ""):
                    found = payload
        if found and "official" in found:
            scores[rid] = {"name": name, **{k: found["official"][k] for k in ("SA", "DA", "AA", "HA")}}
        else:
            missing.append(name)

    # ---- the evaluation rule, twice -------------------------------------
    # Both implementations must answer the *same* question: given this map,
    # which GT points did it drop? export_eval_pcd always reads `<seq>/gt_cloud.pcd`,
    # so the sample is staged as its own one-file sequence and the reference map is
    # symlinked in - that keeps the check on a 3M-point sample instead of 17.4M
    # while exercising the real binary end to end.
    disagreements = None
    ref_map = os.path.normpath(os.path.join(
        ctx["path"], "..", "05_dufomap", "data", "output", "dufomap_output_paper_default_dp1.pcd"))
    if os.path.exists(ref_map):
        import shutil
        rng = np.random.default_rng(0)  # deterministic: same sample every run
        idx = np.sort(rng.choice(len(gt), size=min(CROSSCHECK_POINTS, len(gt)), replace=False))
        stage = os.path.join(ctx["work_dir"], "_xcheck")
        shutil.rmtree(stage, ignore_errors=True)
        os.makedirs(stage)
        try:
            sample = os.path.join(stage, "gt_cloud.pcd")
            _write_pcd(sample, gt[idx])
            os.symlink(ref_map, os.path.join(stage, "ref.pcd"))
            a = export_gt_official(stage, os.path.join(stage, "ref.pcd"), 0.05, _eval_bin(ctx))
            b = export_gt_python(sample, ref_map, 0.05)
            disagreements = int(np.count_nonzero(a != b))
        finally:
            shutil.rmtree(stage, ignore_errors=True)

    metrics = {
        "frames": len(frames), "gt_points": len(gt_labels),
        "gt_static": n_static, "gt_dynamic": n_dynamic, "gt_unlabelled": unlabelled,
        "dynamic_fraction_pct": round(100.0 * n_dynamic / len(gt_labels), 4),
        "methods_scored": len(scores),
        **{f"{v['name']}_SA": v["SA"] for v in scores.values()},
        **{f"{v['name']}_AA": v["AA"] for v in scores.values()},
    }
    if disagreements is not None:
        metrics["crosscheck_points"] = min(CROSSCHECK_POINTS, len(gt))
        metrics["crosscheck_disagreements"] = disagreements

    checks = [
        {
            "name": "ground_truth_is_a_binary_label_set",
            "ok": unlabelled == 0 and n_static > 0 and n_dynamic > 0,
            "detail": (f"{n_static} static + {n_dynamic} dynamic + {unlabelled} other over "
                       f"{len(gt_labels)} points"),
        },
        {
            "name": "sequence_is_the_published_one",
            "ok": len(frames) == 141 and len(gt_labels) == 17362230,
            "detail": f"{len(frames)} frames, {len(gt_labels)} GT points",
        },
    ]

    if disagreements is not None:
        checks.append({
            "name": "the_two_eval_implementations_agree",
            "ok": disagreements == 0,
            "detail": (f"official PCL binary vs independent scipy rewrite label "
                       f"{metrics['crosscheck_points']} sampled GT points with "
                       f"{disagreements} disagreements"),
        })

    findings = []
    if len(scores) >= 2:
        by_sa = sorted(scores.values(), key=lambda v: -v["SA"])
        by_aa = sorted(scores.values(), key=lambda v: -v["AA"])
        same = [v["name"] for v in by_sa] == [v["name"] for v in by_aa]
        findings.append({
            "name": "ranking_depends_on_the_metric",
            "detail": (f"by SA: {' > '.join(v['name'] for v in by_sa)}; "
                       f"by AA: {' > '.join(v['name'] for v in by_aa)}. "
                       + ("The two orders agree." if same else
                          "The two orders disagree, so any single-metric ranking of these "
                          "methods is a statement about the metric as much as the method.")),
            "by_SA": [v["name"] for v in by_sa],
            "by_AA": [v["name"] for v in by_aa],
            "rankings_agree": same,
        })
    findings.append({
        "name": "dynamic_points_are_a_rounding_error_of_the_map",
        "detail": (f"{n_dynamic} of {len(gt_labels)} GT points are dynamic "
                   f"({metrics['dynamic_fraction_pct']}%). A method that deletes nothing scores "
                   f"~100% SA, which is why SA alone cannot rank these methods."),
    })
    if missing:
        findings.append({
            "name": "not_all_methods_scored_yet",
            "detail": f"no score json yet for: {', '.join(missing)}",
        })

    return {
        "metrics": metrics,
        "checks": checks,
        "findings": findings,
        "artifacts": [],
        "note": (f"benchmark infrastructure verified: {len(frames)} frames, "
                 f"{len(scores)}/4 methods scored"
                 + (f", eval cross-check {disagreements} disagreements"
                    if disagreements is not None else "")),
    }


def _write_pcd(path: str, arr) -> None:
    """Binary PCD with the 4-field layout this benchmark uses."""
    import numpy as np
    a = np.ascontiguousarray(arr.astype(np.float32))
    header = ("# .PCD v0.7 - Point Cloud Data file format\nVERSION 0.7\n"
              "FIELDS x y z intensity\nSIZE 4 4 4 4\nTYPE F F F F\nCOUNT 1 1 1 1\n"
              f"WIDTH {len(a)}\nHEIGHT 1\nVIEWPOINT 0 0 0 1 0 0 0\n"
              f"POINTS {len(a)}\nDATA binary\n")
    with open(path, "wb") as fh:
        fh.write(header.encode("ascii"))
        fh.write(a.tobytes())
