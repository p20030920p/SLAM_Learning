#!/usr/bin/env python3
"""Aggregate the repository's own visibility scores into a per-object verdict.

The renderer (`rio_renderer_render_all ... 0`) writes one `frame-*.visibility.txt`
per frame with a line per object:

    instance_id  trunc_orig  trunc_full  trunc_ratio  occ_orig  occ_full  occ_ratio

decoded from `Renderer::CalcOcclusions` / `CalcTruncations` (src/renderer.cc):

  occlusion ratio = pixels of the object visible in the full scene
                    / pixels visible when that instance is rendered ALONE
                    -> low means other objects hide it

  truncation ratio = pixels inside the normal field of view
                     / pixels inside a 2x-wider field of view
                     -> low means it is cut off by the FOV or the image border

This is the repository's own answer to "could the robot see it", rendered from
the real mesh instead of approximated from an oriented box. An object that does
not appear in a frame's file was not rendered at all in that frame.

Usage:
    python3 work/repo_visibility.py <scan_dir> [--min-frames 3] [--out results]
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import statistics
import sys

VISIBLE_OCC = 0.50   # most of what is not occluded is in fact visible
VISIBLE_TRUNC = 0.20  # and a usable part of it sits inside the field of view


def parse_frame(path):
    """instance_id -> (trunc_ratio, occ_ratio, trunc_pixels, occ_pixels)."""
    out = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            parts = line.split()
            if len(parts) != 7:
                continue
            oid = int(parts[0])
            out[oid] = {
                "trunc_ratio": float(parts[3]),
                "occ_ratio": float(parts[6]),
                "trunc_visible_px": int(parts[1]),
                "trunc_full_px": int(parts[2]),
                "occ_visible_px": int(parts[4]),
                "occ_alone_px": int(parts[5]),
            }
    return out


def aggregate(sequence_dir, min_frames=3):
    frames = sorted(f for f in os.listdir(sequence_dir) if f.endswith(".visibility.txt"))
    per_object = {}
    for name in frames:
        for oid, rec in parse_frame(os.path.join(sequence_dir, name)).items():
            e = per_object.setdefault(oid, {
                "objectId": oid, "frames_present": 0, "frames_visible": 0,
                "occlusion_ratios": [], "truncation_ratios": []})
            e["frames_present"] += 1
            e["occlusion_ratios"].append(rec["occ_ratio"])
            e["truncation_ratios"].append(rec["trunc_ratio"])
            if rec["occ_ratio"] >= VISIBLE_OCC and rec["trunc_ratio"] >= VISIBLE_TRUNC:
                e["frames_visible"] += 1

    for e in per_object.values():
        occ = e["occlusion_ratios"]
        tr = e["truncation_ratios"]
        e["occlusion_ratio_median"] = round(statistics.median(occ), 4) if occ else None
        e["occlusion_ratio_max"] = round(max(occ), 4) if occ else None
        e["truncation_ratio_median"] = round(statistics.median(tr), 4) if tr else None
        e["truncation_ratio_max"] = round(max(tr), 4) if tr else None
        if e["frames_visible"] >= min_frames:
            e["repo_observability"] = "visible"
        elif e["frames_present"] >= min_frames and (e["occlusion_ratio_median"] or 0) < VISIBLE_OCC:
            e["repo_observability"] = "occluded"
        elif e["frames_present"] == 0:
            e["repo_observability"] = "out_of_view"
        else:
            e["repo_observability"] = "insufficient"
        for k in ("occlusion_ratios", "truncation_ratios"):
            e.pop(k)
    return {"frames": len(frames), "objects": per_object,
            "thresholds": {"visible_occlusion_ratio": VISIBLE_OCC,
                           "visible_truncation_ratio": VISIBLE_TRUNC,
                           "min_frames": min_frames}}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("scan_dir")
    ap.add_argument("--min-frames", type=int, default=3)
    ap.add_argument("--out", default=None, help="results directory for the json/csv")
    ap.add_argument("--labels", default=None,
                    help="optional per-object json (objectId -> label/gt_class) to cross-tab")
    args = ap.parse_args()

    seq = os.path.join(args.scan_dir, "sequence")
    agg = aggregate(seq, args.min_frames)
    print(f"{args.scan_dir}")
    print(f"  frames with visibility.txt : {agg['frames']}")
    print(f"  objects seen at least once : {len(agg['objects'])}")
    print(f"  thresholds                 : {agg['thresholds']}")

    order = ["visible", "occluded", "out_of_view", "insufficient"]
    counts = {lvl: sum(1 for e in agg["objects"].values()
                       if e["repo_observability"] == lvl) for lvl in order}
    print("  verdicts:", counts)

    labelled = None
    if args.labels and os.path.exists(args.labels):
        labelled = json.load(open(args.labels, encoding="utf-8"))
        by_id = {o["objectId"]: o for o in labelled["objects"]}

        # Two ways an object can be missing from every frame, and they mean
        # different things. The renderer draws the scan's OWN mesh and labels,
        # so an instance that is not in this scan's annotation can never be
        # evaluated here - the tool is silent about it, it is not evidence of
        # anything. An instance that IS in the scan but never rendered was
        # outside the field of view in every frame.
        for oid, l in by_id.items():
            if oid in agg["objects"]:
                continue
            agg["objects"][oid] = {
                "objectId": oid,
                "repo_observability": "out_of_view" if l["in_B"] else "not_in_B_scene",
                "frames_present": 0, "frames_visible": 0,
                "occlusion_ratio_median": None, "occlusion_ratio_max": None,
                "truncation_ratio_median": None, "truncation_ratio_max": None,
            }

        order_all = order + ["not_in_B_scene"]
        table = {}
        for oid, e in agg["objects"].items():
            l = by_id.get(oid)
            if not l:
                continue
            table.setdefault(l["gt_class"], {k: 0 for k in order_all})
            table[l["gt_class"]][e["repo_observability"]] += 1
        agg["cross_tab"] = table
        print("\n  gt_class x repo_observability")
        print("    " + f"{'gt_class':<18}" + "".join(f"{o:>16}" for o in order_all))
        for cls in ["unchanged", "moved", "nonrigid", "removed",
                    "absent_unlabelled", "appeared"]:
            if cls in table:
                print("    " + f"{cls:<18}" + "".join(f"{table[cls][o]:>16}" for o in order_all))
        print("\n  objects missing from B, as the repository's tool sees them:")
        for oid, e in sorted(agg["objects"].items()):
            l = by_id.get(oid)
            if l and l["gt_class"] in ("absent_unlabelled", "removed"):
                print(f"    id={oid} {l['label']:<11} gt={l['gt_class']:<18} "
                      f"repo={e['repo_observability']:<16} "
                      f"frames_present={e['frames_present']} "
                      f"frames_visible={e['frames_visible']} "
                      f"occ_median={e['occlusion_ratio_median']}")

    if args.out:
        os.makedirs(args.out, exist_ok=True)
        jp = os.path.join(args.out, "repo_visibility.json")
        cp = os.path.join(args.out, "repo_visibility.csv")
        payload = {"scan_dir": args.scan_dir, **agg}
        json.dump(payload, open(jp, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
        with open(cp, "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["objectId", "repo_observability", "frames_present", "frames_visible",
                        "occlusion_ratio_median", "occlusion_ratio_max",
                        "truncation_ratio_median", "truncation_ratio_max"])
            for oid in sorted(agg["objects"]):
                e = agg["objects"][oid]
                w.writerow([oid, e["repo_observability"], e["frames_present"],
                            e["frames_visible"], e["occlusion_ratio_median"],
                            e["occlusion_ratio_max"], e["truncation_ratio_median"],
                            e["truncation_ratio_max"]])
        print(f"\n  wrote {jp}\n  wrote {cp}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
