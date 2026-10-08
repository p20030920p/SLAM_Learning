"""Human review gates, complete map snapshots and pure candidate-budget readouts.

No native mapper, Torch or model imports: these contracts are CPU-testable.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

from .delayed_pose import visible_precision


ARMS = ("native_fixed", "threshold_fixed", "visibility_fixed", "oracle_replay")
REVIEW_CHECKS = ("identities", "boundaries", "category_queries", "parts", "exclusions", "all_reference_views",
                 "room1_ontology")


def check_resources():
    """Read GPU process inventory; refuse heavy work when another process owns it."""
    result = subprocess.run(["nvidia-smi", "--query-compute-apps=pid,process_name,used_gpu_memory",
                             "--format=csv,noheader"], capture_output=True, text=True, timeout=15, check=True)
    processes = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    foreign = [line for line in processes if line.split(",")[0].strip() != str(os.getpid())]
    if foreign:
        raise RuntimeError("Another GPU process is active; defer this run without changing its environment: " +
                           "; ".join(foreign))
    running = subprocess.run(["ps", "-eo", "pid,args"], capture_output=True, text=True, timeout=15, check=True)
    author_jobs = [line.strip()[:300] for line in running.stdout.splitlines()
                   if "/SLAM_Author_Originals/" in line and "ps -eo" not in line]
    if author_jobs:
        raise RuntimeError("Other window has active author reproduction jobs; defer heavy work: " +
                           "; ".join(author_jobs))
    return {"gpu_process_inventory": processes, "no_other_compute_processes": True,
            "active_author_reproduction_jobs": author_jobs}


def restore_fixed_semantics(rebuilt, original, membership):
    if len(rebuilt) != len(original) or [membership(o) for o in rebuilt] != [membership(o) for o in original]:
        raise ValueError("Coordinate correction changed historical memberships")
    for new, old in zip(rebuilt, original):
        if new["num_detections"] != old["num_detections"]:
            raise ValueError("Coordinate correction changed detection support")
        for key in ("clip_ft", "text_ft"):
            new[key] = old[key].clone() if hasattr(old[key], "clone") else old[key].copy()
    return rebuilt


def digest(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def validate_protocol(cfg, exploratory=False):
    expected = {"schema_version": 2, "scene": "room2", "arms": list(ARMS),
                "mapping_frames": list(range(0, 400, 25)), "reference_frames": [12, 62, 112, 162],
                "correction_after_observations": 8, "evaluation_observations": [8, 12, 16],
                "primary_observation": 8, "translation_rms_m": [.10, .30], "seeds": [417, 518, 619],
                "expected_mapping_cells": 28, "support_minima": [1, 2, 3],
                "candidate_caps": [25, 50, 100, None], "requires_human_review": not exploratory,
                "candidate_sort": ["detection_support_desc", "point_count_desc", "object_id_asc"]}
    for key, value in expected.items():
        if cfg.get(key) != value:
            raise ValueError(f"Identity-budget v2 protocol mismatch: {key}")
    if exploratory and (cfg.get("analysis_type") != "ai_only_exploratory" or not cfg.get("owner_amendment")):
        raise ValueError("Explicit owner-amended exploratory protocol required")
    if set(cfg["mapping_frames"]) & set(cfg["reference_frames"]):
        raise ValueError("Reference observations leaked into mapping")


def validate_annotations(cfg, ann, require_review=True, exploratory=False):
    validate_protocol(cfg, exploratory=exploratory)
    if ann.get("scene") != cfg["scene"] or ann.get("schema_version") != 2:
        raise ValueError("Annotation scene/version mismatch")
    instances = ann.get("instances", [])
    if not 4 <= len(instances) <= 6:
        raise ValueError("Need 4-6 qualified physical instances; stop annotation stage")
    ids = [i["id"] for i in instances]
    if len(set(ids)) != len(ids) or any(not i.strip() for i in ids):
        raise ValueError("Physical IDs must be unique and nonempty")
    canvas = ann.get("coordinate_canvas", [])
    if len(canvas) != 2 or min(canvas) < 1 or not ann.get("exclusions") or not ann.get("duplicate_definition"):
        raise ValueError("Canvas, exclusions and duplicate definition required")
    for instance in instances:
        if not instance.get("query", "").strip() or not instance.get("parts"):
            raise ValueError("Each physical ID needs a category query and explicit parts")
        frames = [v["frame"] for v in instance["views"]]
        if not frames or len(set(frames)) != len(frames) or not set(frames) <= set(cfg["reference_frames"]):
            raise ValueError("Invalid independent reference views")
        if instance["first_reference_frame"] != min(frames):
            raise ValueError("First reference frame inconsistent")
        if instance["first_reference_frame"] > cfg["mapping_frames"][7]:
            raise ValueError("Primary targets must be visible in prefix references")
        visibility = instance.get("visibility", {})
        if set(visibility) != {str(f) for f in cfg["reference_frames"]}:
            raise ValueError("Explicit visibility/occlusion decision needed for every reference")
        allowed = {"annotated", "occluded", "out_of_view"}
        if not set(visibility.values()) <= allowed or {int(f) for f, v in visibility.items()
                                                       if v == "annotated"} != set(frames):
            raise ValueError("Visibility decisions disagree with polygons")
        for view in instance["views"]:
            polygon = np.asarray(view["polygon"], dtype=float)
            if (polygon.ndim != 2 or polygon.shape[1] != 2 or len(polygon) < 3 or
                    not np.isfinite(polygon).all() or (polygon < 0).any() or (polygon >= canvas).any()):
                raise ValueError("Invalid polygon bounds")
            area = abs(np.dot(polygon[:, 0], np.roll(polygon[:, 1], 1)) -
                       np.dot(polygon[:, 1], np.roll(polygon[:, 0], 1))) / 2
            if area < 4:
                raise ValueError("Degenerate reference polygon")
    if require_review and ann.get("human_reviewed") is not True:
        raise ValueError("Independent human annotation review pending; frontend forbidden")
    if exploratory and ann.get("human_reviewed") is not False:
        raise ValueError("AI-only labels must not claim human review")


def validate_review(cfg_path, ann_path, data, receipt):
    cfg = json.loads(Path(cfg_path).read_text(encoding="utf-8"))
    ann = json.loads(Path(ann_path).read_text(encoding="utf-8"))
    validate_annotations(cfg, ann)
    if (receipt.get("reviewer_role") != "human" or not receipt.get("reviewer", "").strip() or
            not receipt.get("reviewed_at_utc") or receipt.get("approved") is not True or
            any(receipt.get("checks", {}).get(k) is not True for k in REVIEW_CHECKS)):
        raise ValueError("Explicit independent human review receipt required")
    if not receipt.get("room1_ontology_notes", "").strip():
        raise ValueError("room1 vase/plant and duplicate ontology audit notes required")
    for key, path in (("protocol_sha256", cfg_path), ("annotations_sha256", ann_path),
                      ("source_manifest_sha256", Path(data) / "manifest.json")):
        if receipt.get(key) != digest(path):
            raise ValueError(f"Human review input mismatch: {key}")
    manifest = json.loads((Path(data) / "manifest.json").read_text())
    if (manifest.get("scene") != cfg["scene"] or manifest.get("protocol_sha256") != digest(cfg_path) or
            manifest.get("mapping_frames") != cfg["mapping_frames"] or
            manifest.get("reference_frames") != cfg["reference_frames"]):
        raise ValueError("Source manifest/protocol mismatch")
    files = {i["path"] for i in manifest.get("files", [])}
    required = {f"room2/results/{stem}{f:06d}.{ext}" for f in cfg["mapping_frames"] + cfg["reference_frames"]
                for stem, ext in (("frame", "jpg"), ("depth", "png"))} | {"room2/traj.full.txt", "room2/traj.txt"}
    if not required <= files:
        raise ValueError("Source manifest missing required RGB-D/trajectory files")
    for item in manifest["files"]:
        relative = Path(item["path"])
        path = (Path(data) / relative).resolve()
        if not path.is_relative_to(Path(data).resolve()) or digest(path) != item["sha256"]:
            raise ValueError(f"Source changed: {item['path']}")


def validate_freeze(cfg_path, ann_path, data, freeze, exploratory=False):
    """Recheck the embedded human receipt and every raw source before models load."""
    if exploratory:
        cfg = json.loads(Path(cfg_path).read_text())
        ann = json.loads(Path(ann_path).read_text())
        validate_annotations(cfg, ann, require_review=False, exploratory=True)
        if freeze.get("analysis_type") != "ai_only_exploratory" or "human_review" in freeze:
            raise ValueError("Exploratory freeze cannot claim human review")
        manifest = json.loads((Path(data) / "manifest.json").read_text())
        if (manifest.get("scene") != cfg["scene"] or manifest.get("protocol_sha256") != digest(cfg_path) or
                manifest.get("mapping_frames") != cfg["mapping_frames"] or
                manifest.get("reference_frames") != cfg["reference_frames"]):
            raise ValueError("Exploratory source manifest/protocol mismatch")
        expected = {f"room2/results/{stem}{f:06d}.{ext}" for f in cfg["mapping_frames"] + cfg["reference_frames"]
                    for stem, ext in (("frame", "jpg"), ("depth", "png"))} | {"room2/traj.full.txt", "room2/traj.txt"}
        if not expected <= {item["path"] for item in manifest.get("files", [])}:
            raise ValueError("Exploratory manifest missing raw RGB-D files")
        for item in manifest["files"]:
            path = (Path(data) / item["path"]).resolve()
            if not path.is_relative_to(Path(data).resolve()) or digest(path) != item["sha256"]:
                raise ValueError("Exploratory source hash mismatch")
    else:
        validate_review(cfg_path, ann_path, data, freeze.get("human_review", {}))
    for key, path in (("protocol_sha256", cfg_path), ("annotations_sha256", ann_path),
                      ("source_manifest_sha256", Path(data) / "manifest.json")):
        if freeze.get(key) != digest(path):
            raise ValueError(f"Frozen input changed: {key}")
    if not exploratory and freeze.get("human_review_sha256") != hashlib.sha256(
            json.dumps(freeze["human_review"], sort_keys=True, separators=(",", ":")).encode()).hexdigest():
        raise ValueError("Embedded human receipt changed")


def object_id(members):
    canonical = sorted([list(map(int, m)) for m in members])
    return "obj-" + hashlib.sha256(json.dumps(canonical, separators=(",", ":")).encode()).hexdigest()[:24]


def save_snapshot(path, clouds, features, members, supports, *, colors=None, text_features=None, metadata=None):
    """Store all objects; no support or candidate filtering is permitted here."""
    ids = [object_id(m) for m in members]
    if len(set(ids)) != len(ids) or len(clouds) != len(members) or len(features) != len(clouds):
        raise ValueError("Inconsistent complete map state")
    if list(map(int, supports)) != [len(m) for m in members] or any(s < 1 for s in supports):
        raise ValueError("Detection supports disagree with historical contributors")
    if not all(np.asarray(c).ndim == 2 and np.asarray(c).shape[1] == 3 and
               np.isfinite(c).all() for c in clouds) or not np.isfinite(features).all():
        raise ValueError("Invalid snapshot geometry/features")
    payload = {f"pcd_{i:04d}": np.array(c, copy=True) for i, c in enumerate(clouds)}
    if colors is not None:
        for i, (color, cloud) in enumerate(zip(colors, clouds)):
            if np.shape(color) != np.shape(cloud):
                raise ValueError("Point/color count mismatch")
            payload[f"rgb_{i:04d}"] = np.array(color, copy=True)
    payload.update(schema_version=np.array(2), object_ids=np.array(ids, dtype="U28"),
                   supports=np.array(supports, dtype=np.int64), features=np.array(features, copy=True),
                   members_json=np.array(json.dumps(members)),
                   metadata_json=np.array(json.dumps(metadata or {}, sort_keys=True)))
    if text_features is not None:
        payload["object_text_features"] = np.array(text_features, copy=True)
    if Path(path).exists():
        raise FileExistsError("Never overwrite a state snapshot")
    np.savez_compressed(path, **payload)


def load_snapshot(path):
    with np.load(path, allow_pickle=False) as archive:
        if int(archive["schema_version"]) != 2:
            raise ValueError("Need a complete v2 snapshot, not a filtered v1 snapshot")
        ids, supports, features = [archive[k].copy() for k in ("object_ids", "supports", "features")]
        members = json.loads(str(archive["members_json"]))
        clouds = [archive[f"pcd_{i:04d}"].copy() for i in range(len(ids))]
        metadata = json.loads(str(archive["metadata_json"]))
    if (len(set(ids)) != len(ids) or len(clouds) != len(features) or len(ids) != len(members) or
            ids.tolist() != [object_id(m) for m in members] or supports.tolist() != [len(m) for m in members]):
        raise ValueError("Snapshot provenance/support mismatch")
    for value in [ids, supports, features, *clouds]:
        value.setflags(write=False)
    return {"ids": ids, "supports": supports, "features": features, "clouds": clouds,
            "members": members, "metadata": metadata}


def select_candidates(state, min_support, cap):
    if min_support not in (1, 2, 3) or (cap is not None and cap not in (25, 50, 100)):
        raise ValueError("Undeclared readout condition")
    candidates = [i for i, support in enumerate(state["supports"]) if support >= min_support]
    candidates.sort(key=lambda i: (-int(state["supports"][i]), -len(state["clouds"][i]), str(state["ids"][i])))
    return np.asarray(candidates if cap is None else candidates[:cap], dtype=int)


def metric_cache(state, text_features, instances, cfg, latest_frame):
    eligible = [(i, target) for i, target in enumerate(instances) if target["first_reference_frame"] <= latest_frame]
    if not eligible:
        raise ValueError("No eligible targets; do not emit NaN scores")
    cover = np.zeros((len(state["clouds"]), len(eligible)))
    precision = np.zeros_like(cover)
    for i, cloud in enumerate(state["clouds"]):
        if not len(cloud):
            continue
        tree = cKDTree(cloud)
        for j, (_, target) in enumerate(eligible):
            cover[i, j] = np.mean(tree.query(target["points"], workers=2)[0] <= cfg["reference_distance_m"])
            precision[i, j] = visible_precision(cloud, target, cfg["reference_distance_m"])
    features = state["features"]
    text_features = np.asarray(text_features)
    if text_features.shape != (len(instances), features.shape[1]):
        raise ValueError("Query features/instance count mismatch")
    normalized = features / np.maximum(np.linalg.norm(features, axis=1, keepdims=True), 1e-12)
    scores = text_features @ normalized.T
    return {"coverage": cover, "precision": precision, "scores": scores,
            "eligible": eligible, "qualifying": (cover >= cfg["reference_coverage_min"]) &
            (precision >= cfg["reference_precision_min"]),
            "mix_support": (cover >= cfg["reference_coverage_min"]) & (precision >= .20)}


def readout(state, cache, min_support, cap):
    selected = select_candidates(state, min_support, cap)
    qualifying = cache["qualifying"][selected]
    coverage = cache["coverage"][selected]
    rows, query_rows = [], []
    query_groups = {}
    for j, (query_index, target) in enumerate(cache["eligible"]):
        query_groups.setdefault(target["query"], []).append((j, query_index, target["id"]))
        hits = int(qualifying[:, j].sum())
        rows.append({"physical_id": target["id"], "category_query": target["query"],
                     "best_coverage": float(coverage[:, j].max()) if len(selected) else 0.,
                     "recovered": hits > 0, "qualifying_fragments": hits, "duplicate_excess": max(0, hits - 1)})
    for query, targets in query_groups.items():
        local = int(np.argmax(cache["scores"][targets[0][1], selected])) if len(selected) else None
        matched = [identity for j, _, identity in targets if local is not None and qualifying[local, j]]
        top = int(selected[local]) if local is not None else None
        query_rows.append({"category_query": query, "top1_object_id": str(state["ids"][top]) if top is not None else None,
                           "annotated_category_hit": bool(matched), "matched_physical_ids": matched,
                           "annotation_status": "annotated_hit" if matched else "unknown_or_failed_target_match"})
    return {"min_support": min_support, "candidate_cap": cap, "actual_candidates": len(selected),
            "actual_points": sum(len(state["clouds"][i]) for i in selected),
            "selected_object_ids": state["ids"][selected].tolist(), "eligible_instances": len(rows),
            "mean_coverage": float(np.mean([r["best_coverage"] for r in rows])),
            "instance_recovery": float(np.mean([r["recovered"] for r in rows])),
            "category_query_hit": float(np.mean([r["annotated_category_hit"] for r in query_rows])),
            "annotated_duplicate_excess": sum(r["duplicate_excess"] for r in rows),
            "annotated_mixed_objects": int((cache["mix_support"][selected].sum(axis=1) > 1).sum()),
            "instances": rows, "category_queries": query_rows,
            "unknown_candidates_are_false_positives": False}


def scan_readouts(state, cache, cfg):
    return [readout(state, cache, support, cap) for support in cfg["support_minima"]
            for cap in cfg["candidate_caps"]]


def hypothesis_decision(rows, cfg):
    """Require one consistent RMS/support/endpoint at two finite caps, with seed pairing."""
    primary = [r for r in rows if r["observation"] == cfg["primary_observation"] and r["rms_m"] > 0]
    keys = [(r["rms_m"], r["min_support"], r["candidate_cap"], r["seed"], r["arm"]) for r in primary]
    expected = {(rms, support, cap, seed, arm) for rms in cfg["translation_rms_m"]
                for support in cfg["support_minima"] for cap in cfg["candidate_caps"]
                for seed in cfg["seeds"] for arm in ARMS}
    if len(set(keys)) != len(keys) or set(keys) != expected:
        raise ValueError("Missing/duplicate primary cells; no hypothesis decision allowed")
    checks, passing = [], []
    for rms in cfg["translation_rms_m"]:
        for support in cfg["support_minima"]:
            for endpoint in ("instance_recovery", "category_query_hit"):
                passed_caps = []
                for cap in [c for c in cfg["candidate_caps"] if c is not None]:
                    subset = [r for r in primary if r["rms_m"] == rms and r["min_support"] == support
                              and r["candidate_cap"] == cap]
                    lookup = {(r["arm"], r["seed"]): r for r in subset}
                    if len(lookup) != len(subset) or len(lookup) != 12:
                        raise ValueError("Missing/duplicate primary cells; no hypothesis decision allowed")
                    comparisons = []
                    for control in ARMS[:-1]:
                        pairs = [(lookup[("oracle_replay", seed)], lookup[(control, seed)]) for seed in cfg["seeds"]]
                        deltas = [o[endpoint] - c[endpoint] for o, c in pairs]
                        no_identity_increase = all(o[k] <= c[k] for o, c in pairs for k in
                                                   ("annotated_duplicate_excess", "annotated_mixed_objects"))
                        comparisons.append({"control": control, "mean_advantage_pp": 100 * float(np.mean(deltas)),
                                            "positive_seeds": sum(d > 1e-12 for d in deltas),
                                            "no_identity_error_increase": no_identity_increase,
                                            "passes": np.mean(deltas) >= .10 - 1e-12 and
                                            sum(d > 1e-12 for d in deltas) >= 2 and no_identity_increase})
                    passed = all(c["passes"] for c in comparisons)
                    checks.append({"rms_m": rms, "min_support": support, "endpoint": endpoint,
                                   "cap": cap, "passed": passed, "comparisons": comparisons})
                    if passed:
                        passed_caps.append(cap)
                if len(passed_caps) >= 2:
                    passing.append({"rms_m": rms, "min_support": support, "endpoint": endpoint, "caps": passed_caps})
    return {"status": "prototype_plan_eligible" if passing else "narrow_or_stop_H1",
            "H1_validated": False, "passing_conditions": passing, "checks": checks}
