#!/usr/bin/env python3
"""02-01 · 3RScan — automated reproduction.

Runs the A/B session protocol and turns every claim the protocol makes into a
machine check, so the reproduction can be re-run unattended (see
`reproductions/run_all.py`) and backtested against `baselines.json`.

The checks are the point. Each one corresponds to a sentence in
`work/protocol.md` that a reader would otherwise have to take on trust:

  matrix_layout                 the 4x4 is row-major with the translation in the
                                last row - proved by contradiction: the correct
                                reading keeps structural objects in place, the
                                column-vector reading throws them metres away
  object_transform_alignment    rigid[i].transform already contains the
                                scan-to-scan alignment, so it maps A's centroid
                                onto B's centroid
  class_partition               every instance ends up in exactly one class
  tolerance_above_noise         the chosen tolerance exceeds the measured
                                alignment residual on objects that did not move

`findings` are measurements that are *not* invariants: facts about the data that
belong in the record but must never gate the run. On this pair the smallest real
motion (0.265 m) is smaller than the largest alignment residual (0.639 m), so
geometry alone cannot separate moved from unchanged — a result, not a bug.
"""

from __future__ import annotations

import importlib.util
import json
import os

SCENE_REF = "4acaebcc-6c10-2a2a-858b-29c7e4fb410d"
RESCAN = "754e884c-ea24-2175-8b34-cead19d4198d"
TOLERANCE_M = 1.0

# Labels that cannot have moved between sessions. Used to decide which matrix
# reading is the correct one, independently of any annotation.
STRUCTURAL_LABELS = {"floor", "ceiling", "wall"}

# What "the wrong reading" looks like: metres, not centimetres.
WRONG_LAYOUT_MIN_ERROR_M = 3.0
CORRECT_LAYOUT_MAX_ERROR_M = 0.5
TRANSFORM_MATCH_MAX_M = 0.2


def _builder(ctx):
    path = os.path.join(ctx["work_dir"], "build_ab_pair.py")
    spec = importlib.util.spec_from_file_location("build_ab_pair_mod", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _column_vector_read(flat, point):
    """The wrong reading: p' = M p, translation in the fourth column."""
    m = [float(v) for v in flat]
    x, y, z = point
    return [m[0] * x + m[1] * y + m[2] * z + m[3],
            m[4] * x + m[5] * y + m[6] * z + m[7],
            m[8] * x + m[9] * y + m[10] * z + m[11]]


def require(ctx):
    """Blocked unless both scans of the pair are on disk."""
    meta = os.path.join(ctx["data_root"], "3RScan.json")
    if not os.path.exists(meta):
        return ("3RScan.json missing — run code/setup.sh, or download it from "
                "http://campar.in.tum.de/public_datasets/3RScan/3RScan.json")
    for scan in (SCENE_REF, RESCAN):
        seg = os.path.join(ctx["data_root"], "extracted", scan, "semseg.v2.json")
        if not os.path.exists(seg):
            return (f"scan {scan} not extracted — the public example archive only "
                    "ships two scans; other scans need the gated full dataset")
    return None


def run(ctx):
    mod = _builder(ctx)
    ov = _load("observability", os.path.join(ctx["work_dir"], "observability.py"))
    an = _load("analyze_observability", os.path.join(ctx["work_dir"], "analyze_observability.py"))

    pair = mod.build(SCENE_REF, RESCAN, ctx["data_root"], TOLERANCE_M)

    os.makedirs(ctx["results_dir"], exist_ok=True)
    json_path, csv_path = mod.write_outputs(pair, ctx["results_dir"])

    M = pair["protocol"]["global_alignment_B_to_A"]
    objects = pair["objects"]
    counts = pair["counts"]

    # ---- observability: could session B actually see each object? ---------
    obs = an.analyze(ctx["data_root"], SCENE_REF, RESCAN, grid=3)
    obs_json, obs_csv = an.write_outputs(obs, ctx["results_dir"])
    obs_levels = ["visible", "occluded", "out_of_view", "insufficient"]
    obs_counts = {f"obs_{lvl}": sum(1 for r in obs["objects"] if r["observability"] == lvl)
                  for lvl in obs_levels}

    # ---- metrics ---------------------------------------------------------
    residuals = sorted(o["alignment_residual_m"] for o in objects
                       if "alignment_residual_m" in o)
    motions = sorted(o["motion_in_room_frame_m"] for o in objects
                     if "motion_in_room_frame_m" in o)
    tmatch = [o["transform_reproduces_centroid_m"] for o in objects
              if "transform_reproduces_centroid_m" in o]
    metrics = {
        "objects_total": len(objects),
        "unchanged": counts["unchanged"],
        "moved": counts["moved"],
        "nonrigid": counts["nonrigid"],
        "removed": counts["removed"],
        "absent_unlabelled": counts["absent_unlabelled"],
        "appeared": counts["appeared"],
        "global_alignment_translation_m": pair["protocol"]["global_alignment_translation_m"],
        "noise_mean_m": round(sum(residuals) / len(residuals), 4) if residuals else None,
        "noise_p95_m": residuals[int(0.95 * (len(residuals) - 1))] if residuals else None,
        "noise_max_m": residuals[-1] if residuals else None,
        "moved_motion_min_m": motions[0] if motions else None,
        "moved_motion_max_m": motions[-1] if motions else None,
        "transform_reproduce_centroid_max_m": round(max(tmatch), 4) if tmatch else None,
        "obs_frames_available": obs["frames_available"],
        "obs_frames_declared": obs["frames_declared_in_sequence"],
        **obs_counts,
    }

    # ---- the repository's own visibility scores, when the renderer has run --
    # `rio_renderer_render_all <data> <scan> sequence 0` writes
    # frame-*.visibility.txt with an occlusion ratio (visible / visible-when-
    # alone) and a truncation ratio (inside-FOV / inside-2x-FOV) per object per
    # frame, rendered from the real mesh. Where it applies it is the better
    # measurement, so the agreement between it and the OBB estimator is
    # reported rather than hidden.
    repo_finding = None
    scan_b_dir = os.path.join(ctx["code_root"], "data", "3RScan", RESCAN)
    seq_b_dir = os.path.join(scan_b_dir, "sequence")
    if os.path.isdir(seq_b_dir) and any(f.endswith(".visibility.txt")
                                        for f in os.listdir(seq_b_dir)):
        rv = _load("repo_visibility", os.path.join(ctx["work_dir"], "repo_visibility.py"))
        agg = rv.aggregate(seq_b_dir)
        by_id = {o["objectId"]: o for o in pair["objects"]}
        for oid, l in by_id.items():
            if oid not in agg["objects"]:
                agg["objects"][oid] = {
                    "objectId": oid,
                    "repo_observability": "out_of_view" if l["in_B"] else "not_in_B_scene",
                    "frames_present": 0, "frames_visible": 0,
                    "occlusion_ratio_median": None, "occlusion_ratio_max": None,
                    "truncation_ratio_median": None, "truncation_ratio_max": None}
        levels = ["visible", "occluded", "out_of_view", "insufficient", "not_in_B_scene"]
        metrics.update({f"repo_{lvl}": sum(1 for e in agg["objects"].values()
                                           if e["repo_observability"] == lvl)
                        for lvl in levels})
        both = [o["observability"] for o in obs["objects"]
                if o["objectId"] in agg["objects"]
                and agg["objects"][o["objectId"]]["repo_observability"] != "not_in_B_scene"]
        agree = sum(1 for o in obs["objects"]
                    if o["objectId"] in agg["objects"]
                    and agg["objects"][o["objectId"]]["repo_observability"] == o["observability"])
        repo_finding = {
            "name": "obb_estimator_versus_repo_renderer",
            "detail": (f"the two observability measurements agree on {agree}/{len(both)} "
                       f"objects ({round(100 * agree / max(1, len(both)))}%); where they "
                       f"differ the repository's renderer is right, because it renders the "
                       f"real mesh while the OBB estimator samples a box surface that "
                       f"includes faces pointing away from the camera"),
        }

    checks = []

    # ---- 1. matrix layout, by contradiction ------------------------------
    structural = [o for o in objects
                  if o["label"] in STRUCTURAL_LABELS and o["in_A"] and o["in_B"]]
    right, wrong = [], []
    for o in structural:
        flat = None
        # the object's own transform is not available for unchanged objects, so
        # use the rescan-level alignment on both readings
        c_b = o["B_centroid"]
        right.append(mod.distance(mod.apply_row_matrix(M, c_b), o["A_centroid"]))
        wrong.append(mod.distance(_column_vector_read(M, c_b), o["A_centroid"]))
    checks.append({
        "name": "matrix_layout",
        "ok": bool(structural)
              and max(right) < CORRECT_LAYOUT_MAX_ERROR_M
              and min(wrong) > WRONG_LAYOUT_MIN_ERROR_M * max(right),
        "detail": (f"{len(structural)} structural objects: row-vector max error "
                   f"{max(right):.3f} m, column-vector min error {min(wrong):.3f} m "
                   f"({min(wrong) / max(right):.1f}x worse)"
                   if structural else "no structural object found in both scans"),
    })

    # ---- 2. the object transform already carries the alignment -----------
    checks.append({
        "name": "object_transform_alignment",
        "ok": bool(tmatch) and max(tmatch) < TRANSFORM_MATCH_MAX_M,
        "detail": (f"{len(tmatch)} moved objects: T·c_A reproduces c_B to within "
                   f"{max(tmatch):.4f} m" if tmatch else "no moved object with a transform"),
    })

    # ---- 3. every instance lands in exactly one class --------------------
    total = sum(counts.values())
    checks.append({
        "name": "class_partition",
        "ok": total == len(objects) and len({o["objectId"] for o in objects}) == len(objects),
        "detail": f"{total} classified over {len(objects)} distinct instances",
    })

    # ---- 4. tolerance is above the alignment noise -----------------------
    checks.append({
        "name": "tolerance_above_noise",
        "ok": bool(residuals) and residuals[-1] < TOLERANCE_M,
        "detail": (f"max residual on unchanged objects {residuals[-1]:.3f} m "
                   f"< tolerance {TOLERANCE_M} m" if residuals else "no residuals"),
    })

    # ---- 5. moved objects vs that noise: a MEASUREMENT, not an invariant ---
    # On this pair the smallest real motion is smaller than the largest
    # alignment residual, so a pure centroid-difference detector cannot
    # separate moved from unchanged here. That is a result about the data, not
    # a defect in the pipeline, so it is recorded as a finding (below) and
    # never gates the run.
    separable = bool(motions and residuals) and motions[0] > residuals[-1]

    # ---- 6. the depth really is in millimetres, not metres ---------------
    # Regression guard: reading m_depthShift as a multiplier instead of a
    # divisor leaves every depth 1000x too large, which turns every surface
    # into "measured far behind predicted" and silently empties the `visible`
    # class. A plausible indoor depth range catches that immediately.
    depth_lo, depth_hi = obs["depth_range_m"] if obs["depth_range_m"] else (None, None)
    checks.append({
        "name": "depth_scale_plausible",
        "ok": depth_lo is not None and 0.05 < depth_lo < 2.0 and depth_hi < 20.0,
        "detail": f"depth range {obs['depth_range_m']} m at scale "
                  f"{obs['depth_scale_m_per_unit']} m/unit",
    })

    # ---- 6. poses are proper rigid transforms ----------------------------
    checks.append({
        "name": "poses_are_rigid",
        "ok": len(obs["invalid_poses"]) == 0,
        "detail": f"{obs['frames_available']} frames, "
                  f"{len(obs['invalid_poses'])} with a non-orthonormal rotation",
    })

    # ---- 7. observability is a partition ---------------------------------
    obs_total = sum(obs_counts.values())
    checks.append({
        "name": "observability_partition",
        "ok": obs_total == len(obs["objects"]) == len(objects),
        "detail": f"{obs_total} objects classified over {len(obs['objects'])} measured "
                  f"({len(objects)} in the pair)",
    })

    # ---- findings --------------------------------------------------------
    vanished = [o for o in obs["objects"]
                if o["gt_class"] in ("absent_unlabelled", "removed")]
    covered = sum(1 for v in vanished if v["observability"] == "visible")
    findings = [
        *([repo_finding] if repo_finding else []),
        {
            "name": "vanished_objects_are_not_all_observable",
            "detail": (f"{len(vanished) - covered} of {len(vanished)} objects missing from B "
                       f"were NOT observable there (out of view or occluded) — for those the "
                       f"dataset's silence cannot be read as 'removed'"),
        },
        {
            "name": "observability_spreads_even_within_one_gt_class",
            "detail": ("unchanged objects: " + ", ".join(
                f"{lvl}={obs['cross_tab']['unchanged'][lvl]}" for lvl in obs_levels)),
        },
        {
            "name": "frame_coverage_is_partial",
            "detail": (f"{obs['frames_available']} of {obs['frames_declared_in_sequence']} "
                       f"frames shipped, a prefix — `out_of_view` is provisional"),
        },
        {
            "name": "geometric_separation",
            "detail": (f"smallest real motion {motions[0]:.3f} m vs largest alignment "
                       f"noise {residuals[-1]:.3f} m — moved objects are "
                       f"{'separable' if separable else 'NOT separable'} on geometry alone"
                       if motions and residuals else "insufficient data"),
            "separable": separable,
        },
    ]

    # ---- artifacts -------------------------------------------------------
    artifacts = [os.path.relpath(p, ctx["path"])
                 for p in (json_path, csv_path, obs_json, obs_csv)]
    return {
        "metrics": metrics,
        "checks": checks,
        "findings": findings,
        "artifacts": artifacts,
        "note": (f"A/B pair + observability — {obs_counts['obs_visible']} visible, "
                 f"{obs_counts['obs_occluded']} occluded, "
                 f"{obs_counts['obs_out_of_view']} out of view"),
    }
