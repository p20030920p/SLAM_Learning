#!/usr/bin/env python3
"""Turn a 3RScan scene into an explicit A/B session pair with object-level GT.

Session A = the scene's reference scan. Session B = one of its rescans.

What the dataset provides
-------------------------
3RScan.json
    per rescan: the global alignment `transform` (B -> A), plus the instance
    lists `rigid` (moved, each with its own 6DoF transform), `nonrigid`
    (deformed) and `removed`.
<scan>/semseg.v2.json
    instance segmentation: objectId, label, oriented bounding box
    (centroid / axesLengths / normalizedAxes).

What this script adds
---------------------
The dataset never states a per-object change class for a *pair* of sessions, and
the transforms it does give are easy to misuse. This script produces the class
for every instance in the pair, and pins down two conventions by measurement:

1. **Matrix layout.** 3RScan stores a 4x4 as 16 row-major floats with the
   translation in the LAST ROW (p' = p * M). Using the column-vector layout
   instead puts the floor, ceiling and walls 3.2-4.9 m away from their position
   in the reference scan; the row-vector layout leaves them within 0.03-0.32 m.

2. **What the object transform means.** `rigid[i].transform` maps the object
   from A's frame straight into B's frame — it already contains the scan-to-scan
   alignment: applying it to A's centroid reproduces B's centroid to 0.01-0.11 m.
   So its translation is NOT the object's motion; it also contains the ~1.6 m
   offset between the two scan origins. The motion is what is left once that
   offset is removed:

       motion = | (M . T . c_A) - c_A |      (expressed in A's frame)

   which is the same as |T.c_A - M^-1.c_A| because M is rigid.

Classes
-------
unchanged · moved · nonrigid · removed · absent_unlabelled · appeared

`appeared` is derived (the dataset annotates removed but not added), and
`absent_unlabelled` is kept strictly separate: the object is in A's instance
annotation, gone from B's, and the dataset does not call it removed. That case
is a real annotation gap and must never be folded into `removed`.

Usage
-----
  python3 build_ab_pair.py --scene-ref <scanId> --rescan <scanId> [--tolerance 1.0]
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys

CLASSES = ["unchanged", "moved", "nonrigid", "removed", "absent_unlabelled", "appeared"]


# --------------------------------------------------------------------------- #
# 3RScan matrix helpers: flat row-major 16 floats, translation in the last row
# --------------------------------------------------------------------------- #
def apply_row_matrix(flat, point):
    """p' = p * M, with M given as 16 row-major floats."""
    m = [float(v) for v in flat]
    x, y, z = point
    return [
        m[0] * x + m[4] * y + m[8] * z + m[12],
        m[1] * x + m[5] * y + m[9] * z + m[13],
        m[2] * x + m[6] * y + m[10] * z + m[14],
    ]


def translation_of(flat):
    return [float(flat[12]), float(flat[13]), float(flat[14])]


def distance(a, b):
    return sum((a[i] - b[i]) ** 2 for i in range(3)) ** 0.5


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def load_objects(path):
    seg = load_json(path)
    out = {}
    for group in seg["segGroups"]:
        obb = group.get("obb", {})
        out[group["objectId"]] = {
            "label": group.get("label", ""),
            "centroid": [round(float(v), 4) for v in obb.get("centroid", [])],
            "axes": [round(float(v), 4) for v in obb.get("axesLengths", [])],
            "segments": len(group.get("segments", [])),
        }
    return out


def find_scene(meta, scene_ref, rescan_ref):
    for scene in meta:
        if scene["reference"] == scene_ref:
            return scene, next(
                (r for r in scene["scans"] if r["reference"] == rescan_ref), None)
    return None, None


# --------------------------------------------------------------------------- #
def build(scene_ref, rescan_ref, data_root, tolerance):
    meta = load_json(os.path.join(data_root, "3RScan.json"))
    scene, rescan = find_scene(meta, scene_ref, rescan_ref)
    if scene is None:
        raise SystemExit(f"{scene_ref} is not a reference scan in 3RScan.json")
    if rescan is None:
        raise SystemExit(f"{rescan_ref} is not a rescan of scene {scene_ref}")

    a_path = os.path.join(data_root, "extracted", scene_ref, "semseg.v2.json")
    b_path = os.path.join(data_root, "extracted", rescan_ref, "semseg.v2.json")
    for p in (a_path, b_path):
        if not os.path.exists(p):
            raise SystemExit(
                f"missing {p}\n"
                "The public example archive only ships two scans; fetch other "
                "scan folders with the dataset download script first."
            )

    A, B = load_objects(a_path), load_objects(b_path)

    M = rescan.get("transform")
    if not isinstance(M, list) or len(M) != 16:
        raise SystemExit(f"rescan {rescan_ref} has no global alignment transform")

    rigid = {r["instance_reference"]: r for r in rescan.get("rigid", []) if isinstance(r, dict)}
    rigid_bare = [r for r in rescan.get("rigid", []) if isinstance(r, int)]
    removed_ids = set(rescan.get("removed", []) or [])
    nonrigid_ids = set(rescan.get("nonrigid", []) or [])

    objects = []
    for oid in sorted(set(A) | set(B)):
        in_a, in_b = oid in A, oid in B
        src = A.get(oid) or B.get(oid)
        entry = {"objectId": oid, "label": src["label"], "in_A": in_a, "in_B": in_b}

        r = rigid.get(oid)
        if r is not None:
            entry["gt_class"] = "moved"
            entry["source"] = "3RScan.json rigid"
            entry["symmetry"] = r.get("symmetry", 0)
            entry["object_transform"] = r["transform"]
            entry["object_transform_translation_m"] = round(
                distance(translation_of(r["transform"]), [0, 0, 0]), 4)
            if in_a:
                c_a = A[oid]["centroid"]
                # T maps A's frame -> B's frame; M maps B's frame -> A's frame.
                # Their composition therefore lands back in A's frame, and the
                # distance from the original position is the object's real move.
                moved_to = apply_row_matrix(M, apply_row_matrix(r["transform"], c_a))
                entry["motion_in_room_frame_m"] = round(distance(moved_to, c_a), 4)
                if in_b:
                    entry["transform_reproduces_centroid_m"] = round(
                        distance(apply_row_matrix(r["transform"], c_a), B[oid]["centroid"]), 4)
        elif oid in nonrigid_ids:
            entry["gt_class"] = "nonrigid"
            entry["source"] = "3RScan.json nonrigid"
        elif oid in removed_ids:
            entry["gt_class"] = "removed"
            entry["source"] = "3RScan.json removed"
        elif in_a and in_b:
            entry["gt_class"] = "unchanged"
            entry["source"] = "present in both, not listed as changed"
            # Residual of the global alignment on this object: this is the
            # dataset's annotation noise, and it sets the usable tolerance.
            entry["alignment_residual_m"] = round(
                distance(apply_row_matrix(M, B[oid]["centroid"]), A[oid]["centroid"]), 4)
        elif in_a and not in_b:
            entry["gt_class"] = "absent_unlabelled"
            entry["source"] = "in A semseg, absent from B semseg, not in `removed`"
        else:
            entry["gt_class"] = "appeared"
            entry["source"] = "in B semseg, absent from A semseg (no `added` list exists)"

        if in_a:
            entry["A_centroid"] = A[oid]["centroid"]
        if in_b:
            entry["B_centroid"] = B[oid]["centroid"]
            entry["B_centroid_in_A_frame"] = [
                round(v, 4) for v in apply_row_matrix(M, B[oid]["centroid"])]
        objects.append(entry)

    counts = {c: sum(1 for o in objects if o["gt_class"] == c) for c in CLASSES}

    residuals = [o["alignment_residual_m"] for o in objects if "alignment_residual_m" in o]
    residuals.sort()
    noise = {
        "n": len(residuals),
        "mean_m": round(sum(residuals) / len(residuals), 4) if residuals else None,
        "max_m": residuals[-1] if residuals else None,
        "p95_m": residuals[int(0.95 * (len(residuals) - 1))] if residuals else None,
    } if residuals else None

    moved = [o for o in objects if o["gt_class"] == "moved"]
    return {
        "protocol": {
            "session_A": scene_ref,
            "session_B": rescan_ref,
            "scene_split": scene.get("type"),
            "tolerance_radius_m": tolerance,
            "global_alignment_B_to_A": M,
            "global_alignment_translation_m": round(distance(translation_of(M), [0, 0, 0]), 4),
            "gt_source": "3RScan.json (rigid / nonrigid / removed) + per-scan semseg.v2.json",
            "matrix_layout": "flat row-major 4x4, translation in the LAST ROW (p' = p * M)",
            "object_transform_meaning": (
                "rigid[i].transform maps the object from A's frame into B's frame and "
                "already contains the scan-to-scan alignment; its translation is not "
                "the object's motion. motion = |M . T . c_A - c_A|."
            ),
            "classes_note": (
                "`appeared` is derived (no `added` list exists). `absent_unlabelled` is "
                "kept separate: present in A, absent from B, not called removed."
            ),
        },
        "counts": counts,
        "alignment_noise_on_unchanged": noise,
        "tolerance_check": {
            "measured_noise_max_m": noise["max_m"] if noise else None,
            "requested_tolerance_m": tolerance,
            "tolerance_above_noise": (noise["max_m"] is not None and tolerance > noise["max_m"]),
            "implication": (
                "The tolerance radius must exceed the alignment residual on objects that "
                "did not move, otherwise unchanged objects are reported as moved."
            ),
        },
        "moved_objects": moved,
        "bare_integer_rigid_entries": {
            "count": len(rigid_bare),
            "ids": rigid_bare[:20],
            "note": "listed as rigid without a transform; not used for motion here",
        },
        "objects": objects,
    }


def write_outputs(pair, out_dir):
    """Write ab_pair.json and ab_pair.csv; returns the two paths."""
    os.makedirs(out_dir, exist_ok=True)
    json_path = os.path.join(out_dir, "ab_pair.json")
    csv_path = os.path.join(out_dir, "ab_pair.csv")
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(pair, fh, indent=2, ensure_ascii=False)
    with open(csv_path, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["objectId", "label", "gt_class", "in_A", "in_B",
                    "motion_in_room_frame_m", "alignment_residual_m",
                    "transform_reproduces_centroid_m", "symmetry", "source"])
        for o in pair["objects"]:
            w.writerow([o["objectId"], o["label"], o["gt_class"], o["in_A"], o["in_B"],
                        o.get("motion_in_room_frame_m", ""),
                        o.get("alignment_residual_m", ""),
                        o.get("transform_reproduces_centroid_m", ""),
                        o.get("symmetry", ""), o["source"]])
    return json_path, csv_path


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scene-ref", required=True, help="reference scan id (session A)")
    ap.add_argument("--rescan", required=True, help="rescan id (session B)")
    ap.add_argument("--data-root", default=os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "data", "raw"))
    ap.add_argument("--tolerance", type=float, default=0.5,
                    help="identity/change tolerance radius in metres")
    ap.add_argument("--out-dir", default=os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "results"))
    args = ap.parse_args()

    pair = build(args.scene_ref, args.rescan,
                 os.path.normpath(args.data_root), args.tolerance)
    out_dir = os.path.normpath(args.out_dir)
    json_path, csv_path = write_outputs(pair, out_dir)

    p = pair["protocol"]
    print(f"A = {p['session_A']}")
    print(f"B = {p['session_B']}   split={p['scene_split']}  tolerance={p['tolerance_radius_m']} m")
    print(f"objects: {len(pair['objects'])}")
    for c in CLASSES:
        print(f"  {c:<18} {pair['counts'][c]}")

    n = pair["alignment_noise_on_unchanged"]
    if n:
        print(f"\nalignment noise on {n['n']} unchanged objects: "
              f"mean={n['mean_m']} m  p95={n['p95_m']} m  max={n['max_m']} m")
    tc = pair["tolerance_check"]
    print(f"tolerance {tc['requested_tolerance_m']} m above measured noise "
          f"({tc['measured_noise_max_m']} m)? {tc['tolerance_above_noise']}")

    if pair["moved_objects"]:
        print("\nmoved objects:")
        for o in pair["moved_objects"]:
            print(f"  id={o['objectId']:<4} {o['label']:<9} "
                  f"motion={o.get('motion_in_room_frame_m')} m  "
                  f"(raw |t_T|={o['object_transform_translation_m']} m)  "
                  f"T reproduces centroid to {o.get('transform_reproduces_centroid_m')} m  "
                  f"symmetry={o['symmetry']}")

    odd = [o for o in pair["objects"] if o["gt_class"] == "absent_unlabelled"]
    if odd:
        print("\nvanished from B but NOT labelled removed:")
        for o in odd:
            print(f"  id={o['objectId']:<4} {o['label']:<9} A_centroid={o['A_centroid']}")

    print(f"\nwrote {json_path}\nwrote {csv_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
