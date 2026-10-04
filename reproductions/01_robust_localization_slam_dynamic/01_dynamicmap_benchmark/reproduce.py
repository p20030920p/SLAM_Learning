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

# This ledger is about the benchmark's own row for each method - the ROS-free
# ports that DynamicMap_Benchmark ships. 01-03 and 01-04 now ALSO score the
# official upstream implementations, in files that sit in the same results/
# directory. Picking by directory order (which is how this used to work) then
# silently swaps the ledger's Removert row for the official implementation's -
# which is a different measurement, not a regression. Name the file explicitly.
BENCHMARK_ROW_FILE = {
    "01-03": "erasor_benchmark_port.json",
    "01-04": "score_benchmark_port.json",
}

# Where the official-implementation scores live, so the ledger can carry both
# numbers instead of conflating them.
OFFICIAL_SCORE_FILE = {
    "01-04": os.path.join("04_removert", "results", "score_official_scanside.json"),
}


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
    scores, missing, official = {}, [], {}
    for rid, name in METHOD_IDS.items():
        folder = os.path.normpath(os.path.join(ctx["path"], "..",
                                               {"01-03": "03_erasor", "01-04": "04_removert",
                                                "01-05": "05_dufomap", "01-06": "06_beautymap"}[rid]))
        payloads = []
        results = os.path.join(folder, "results")
        if os.path.isdir(results):
            # method folders name their scores differently
            # (erasor_score.json, dufomap_score_paper_default_dp1.json, ...)
            for f in sorted(os.listdir(results)):
                if not (f.endswith(".json") and "score" in f):
                    continue
                with open(os.path.join(results, f), encoding="utf-8") as fh:
                    payload = json.load(fh)
                if "official" in payload:
                    payloads.append((f, payload))

        want = BENCHMARK_ROW_FILE.get(rid)
        found = next((p for f, p in payloads if f == want), None) if want else None
        if found is None:
            for _, payload in payloads:
                # a folder may hold several configs; keep the one that is not an
                # explicitly-marked variant (d_p=2, benchmark example, ...)
                if found is None or "dp2" not in payload.get("method", ""):
                    found = payload
        if found is not None:
            scores[rid] = {"name": name, **{k: found["official"][k] for k in ("SA", "DA", "AA", "HA")}}
        else:
            missing.append(name)

        # the official upstream implementation's score, when the folder has one
        rel = OFFICIAL_SCORE_FILE.get(rid)
        if rel:
            p = os.path.join(ctx["path"], "..", rel)
            if os.path.exists(p):
                with open(p, encoding="utf-8") as fh:
                    payload = json.load(fh)
                impl = payload.get("official") or payload.get("python")
                if impl:
                    official[name] = {k: impl[k] for k in ("SA", "DA", "AA")}

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
        # kept separate on purpose: the benchmark row above is the port's, these
        # are the official upstream implementation's, on the same data
        **{f"{k}_official_SA": v["SA"] for k, v in official.items()},
        **{f"{k}_official_AA": v["AA"] for k, v in official.items()},
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
    if official and "01-04" in scores:
        findings.append({
            "name": "the_benchmark_row_and_the_official_row_are_not_the_same_measurement",
            "detail": (
                "On this same KITTI 00 GT, the benchmark's ROS-free port of Removert scores "
                f"SA {scores['01-04']['SA']:.2f} / AA {scores['01-04']['AA']:.2f}, while the "
                f"authors' own repo scores SA {official['Removert']['SA']:.2f} / "
                f"AA {official['Removert']['AA']:.2f} (official scan-side output; see 01-04). "
                "Both are recorded above under separate metric names. ERASOR's port, by "
                "contrast, is faithful in its own metric - so 'the port stands in for the "
                "method' has to be checked per method, not assumed."),
            "benchmark_row": {k: scores["01-04"][k] for k in ("SA", "DA", "AA")},
            "official_row": official["Removert"],
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
