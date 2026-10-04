#!/usr/bin/env python3
"""Cross-tabulate change ground truth against observability in session B.

This is the measurement the dataset cannot give you. For every object of the A/B
pair it answers two independent questions:

    did it change?            -> from 3RScan.json (build_ab_pair.py)
    could the robot see it?   -> from session B's own poses and depth (observability.py)

Where the two disagree is the interesting part. An object labelled
`absent_unlabelled` (gone from B's annotation, not called removed) is only
evidence of a real removal if its expected position was actually observable. If
it was out of view or occluded, the honest answer is "unknown" - and a system
that reports "removed" there is guessing.

Objects present in B are measured at their own annotated position. Objects
missing from B have no position of their own, so they are measured where they
would be if they had not moved (A's box carried into B's frame by the rescan's
alignment). That assumption is stated per object as `position_source`.

Use as a module:

    from analyze_observability import analyze
    payload = analyze(data_root, scene_ref, rescan, grid=3)

or from the command line:

    python3 work/analyze_observability.py [scene_ref] [rescan] [grid]
"""

from __future__ import annotations

import csv
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

CLASSES = ["unchanged", "moved", "nonrigid", "removed", "absent_unlabelled", "appeared"]
LEVELS = ["visible", "occluded", "out_of_view", "insufficient"]


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def analyze(data_root, scene_ref, rescan, grid=3, verbose=False):
    """Run the whole observability analysis and return the payload."""
    bp = _load("build_ab_pair", os.path.join(HERE, "build_ab_pair.py"))
    ov = _load("observability", os.path.join(HERE, "observability.py"))

    pair = bp.build(scene_ref, rescan, data_root, 1.0)
    M = pair["protocol"]["global_alignment_B_to_A"]
    M_inv = ov.invert_alignment(M)

    scan_a = os.path.join(data_root, "extracted", scene_ref)
    scan_b = os.path.join(data_root, "extracted", rescan)
    objects_a = ov.load_objects(scan_a)
    objects_b = ov.load_objects(scan_b)

    seq_b = os.path.join(scan_b, "sequence")
    session_b = ov.load_session(seq_b)
    info_b = ov.parse_info(seq_b)
    declared = None
    with open(os.path.join(seq_b, "_info.txt"), encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            if line.strip().startswith("m_frames.size"):
                declared = int(line.split("=")[1])

    if verbose:
        print(f"session B: {len(session_b['frames'])} of {declared} frames available")
        print(f"depth: {session_b['depth_wh']} scale {info_b['depth_scale_m']} m/unit")

    bad_poses = [f for f, p in session_b["poses"].items() if not ov.is_rotation(p)]

    records = []
    for entry in pair["objects"]:
        oid = entry["objectId"]
        if oid in objects_b:
            obb = objects_b[oid]["obb"]
            source = "B annotation (own position)"
        elif oid in objects_a:
            obb = ov.map_obb(objects_a[oid]["obb"], M_inv)
            source = "A box carried into B by the rescan alignment (assumed unchanged)"
        else:
            continue

        points = ov.obb_surface_points(
            obb["centroid"], obb["axesLengths"], obb["normalizedAxes"], grid=grid)
        obs = ov.observe_object(points, session_b)
        obs.update({"objectId": oid, "label": entry["label"],
                    "gt_class": entry["gt_class"], "position_source": source,
                    "n_samples": len(points)})
        records.append(obs)
        if verbose:
            print(f"  id={oid:<4} {entry['label']:<11} gt={entry['gt_class']:<18} "
                  f"obs={obs['observability']:<12} {obs['frames_visible']}v/"
                  f"{obs['frames_occluded']}o/{obs['frames_in_frustum']}f")

    table = {c: {o: 0 for o in LEVELS} for c in CLASSES}
    for r in records:
        table[r["gt_class"]][r["observability"]] += 1

    depths = [d[d > 0] for d in session_b["depth"].values()]
    all_valid = [float(v.min()) for v in depths if v.size] + \
                [float(v.max()) for v in depths if v.size]

    return {
        "session_A": scene_ref,
        "session_B": rescan,
        "obb_grid": grid,
        "frames_available": len(session_b["frames"]),
        "frames_declared_in_sequence": declared,
        "frame_coverage_note": (
            "The public example archive ships a 51-frame prefix of the sequence, "
            "so `out_of_view` means 'not in view in the sampled frames', not "
            "'never visible during the session'."),
        "invalid_poses": bad_poses,
        "depth_scale_m_per_unit": info_b["depth_scale_m"],
        "depth_range_m": [round(min(all_valid), 3), round(max(all_valid), 3)] if all_valid else None,
        "cross_tab": table,
        "objects": records,
    }


def write_outputs(payload, results_dir):
    os.makedirs(results_dir, exist_ok=True)
    out_json = os.path.join(results_dir, "observability.json")
    out_csv = os.path.join(results_dir, "observability.csv")
    with open(out_json, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)
    with open(out_csv, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["objectId", "label", "gt_class", "observability", "frames_total",
                    "frames_in_frustum", "frames_visible", "frames_occluded",
                    "samples_tested", "samples_visible", "samples_occluded",
                    "position_source"])
        for r in payload["objects"]:
            w.writerow([r["objectId"], r["label"], r["gt_class"], r["observability"],
                        r["frames_total"], r["frames_in_frustum"], r["frames_visible"],
                        r["frames_occluded"], r["samples_tested"], r["samples_visible"],
                        r["samples_occluded"], r["position_source"]])
    return out_json, out_csv


def main():
    scene_ref = sys.argv[1] if len(sys.argv) > 1 else "4acaebcc-6c10-2a2a-858b-29c7e4fb410d"
    rescan = sys.argv[2] if len(sys.argv) > 2 else "754e884c-ea24-2175-8b34-cead19d4198d"
    grid = int(sys.argv[3]) if len(sys.argv) > 3 else 3

    folder = os.path.dirname(HERE)
    payload = analyze(os.path.join(folder, "data", "raw"), scene_ref, rescan,
                      grid=grid, verbose=True)

    print(f"\nframes available: {payload['frames_available']} of "
          f"{payload['frames_declared_in_sequence']} declared "
          f"({payload['frame_coverage_note']})")
    print(f"poses that are not proper rotations: {len(payload['invalid_poses'])}")
    print(f"depth range: {payload['depth_range_m']} m "
          f"(scale {payload['depth_scale_m_per_unit']} m/unit)")

    print("\n=== gt_class x observability ===")
    print("  " + f"{'gt_class':<18}" + "".join(f"{o:>14}" for o in LEVELS))
    for c in CLASSES:
        if sum(payload["cross_tab"][c].values()):
            print("  " + f"{c:<18}" +
                  "".join(f"{payload['cross_tab'][c][o]:>14}" for o in LEVELS))

    vanished = [r for r in payload["objects"]
                if r["gt_class"] in ("absent_unlabelled", "removed")]
    print("\n=== objects missing from B: could the robot have seen them? ===")
    for r in vanished:
        verdict = {
            "visible": "YES - the spot was observed and empty -> real removal",
            "occluded": "NO - the spot was behind something",
            "out_of_view": "NO - the spot was never in the frustum",
            "insufficient": "UNCLEAR - too few valid samples",
        }[r["observability"]]
        print(f"  id={r['objectId']:<4} {r['label']:<11} gt={r['gt_class']:<18} "
              f"obs={r['observability']:<12} {verdict}")

    json_path, csv_path = write_outputs(payload, os.path.join(folder, "results"))
    print(f"\nwrote {json_path}\nwrote {csv_path}")


if __name__ == "__main__":
    main()
