"""Prepare traceable, thinned measured outputs for an actual RViz inspection.

No mapper or front end is executed here. Pickles must be trusted local author outputs.
"""
from __future__ import annotations

import argparse
import gzip
import json
import pickle
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from slam_learning.core.pcd import read_pcd
from slam_learning.core.provenance import digest
from slam_learning.runtime.runner import verify_record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("method", choices=("dufomap", "beautymap", "conceptgraphs", "hovsg"))
    parser.add_argument("record", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--dataset", type=Path)
    args = parser.parse_args()
    issues = verify_record(args.record, full=True)
    record = json.loads(args.record.read_text())
    if issues or record.get("status") != "executed":
        raise ValueError(f"Completed full local evidence required: {issues}")
    run = args.record.parent
    args.output.mkdir(parents=True, exist_ok=False)
    sources = {str(args.record.resolve()): digest(args.record)}
    steps = []

    def bound(path):
        sources[str(path.resolve())] = digest(path)
        return path

    def save(xyz, colors, label, image=None, source_index=None):
        xyz = np.asarray(xyz, dtype=np.float32)
        colors = np.broadcast_to(np.asarray(colors, dtype=np.uint8), xyz.shape).copy()
        if args.method in ("conceptgraphs", "hovsg"):
            # Display only: Replica Y-down -> RViz Z-up, preserving a right-handed frame.
            xyz = xyz[:, [0, 2, 1]] * np.array([1, 1, -1], dtype=np.float32)
        selection = np.linspace(0, len(xyz)-1, min(len(xyz), 120000), dtype=int)
        path = args.output / f"{len(steps):03d}.npz"
        payload = {"xyz": xyz[selection], "rgb": colors[selection]}
        if image is not None:
            payload["image"] = np.asarray(image.resize((640, 360)).convert("RGB"))
        np.savez_compressed(path, **payload)
        steps.append({"file": path.name, "sha256": digest(path), "label": label,
                      "source_index": source_index, "input_points": len(xyz),
                      "display_points": len(selection)})

    if args.method in ("dufomap", "beautymap"):
        if args.dataset is None or record.get("kind") != "map_evaluator_cross_check":
            raise ValueError("LiDAR review requires the native evaluator record and --dataset")
        if record.get("total_disagreement_points") != 0:
            raise ValueError("Resolve evaluator disagreements before visual publication")
        gt_path = bound(args.dataset / "gt_cloud.pcd")
        gt = read_pcd(gt_path)
        manifest_path = bound(args.dataset / "provenance.json")
        manifest = json.loads(manifest_path.read_text())
        if digest(gt_path) != manifest["files"]["gt_cloud.pcd"]:
            raise ValueError("Dataset hash mismatch")
        predicted = read_pcd(bound(run / args.method / "eval/cleaned_exportGT.pcd"))
        if len(predicted.records) != len(gt.records):
            raise ValueError("Evaluator point count mismatch")
        # First 21 source scans, same point sample in all stages. Scoring used all 141.
        paths = sorted((args.dataset / "pcd").glob("*.pcd"))[:21]
        n = sum(len(read_pcd(p).records) for p in paths)
        idx = np.arange(0, n, 12)
        idx = idx[np.linspace(0, len(idx)-1, min(len(idx), 120000), dtype=int)]
        xyz = gt.xyz(idx)
        if not np.array_equal(xyz, predicted.xyz(idx)):
            raise ValueError("Evaluator identities differ")
        dynamic = np.asarray(gt.records["intensity"][idx]) == 1
        removed = np.asarray(predicted.records["intensity"][idx]) == 1
        colors = np.full(xyz.shape, [160, 176, 190], dtype=np.uint8)
        colors[dynamic & removed] = [70, 220, 130]
        colors[~dynamic & removed] = [255, 80, 80]
        colors[dynamic & ~removed] = [70, 145, 255]
        save(xyz, colors, "INPUT | GT colors for inspection only | 21 selected scans")
        save(xyz[removed], colors[removed], "REMOVED | green dynamic / red static loss")
        save(xyz[~removed], colors[~removed], "RETAINED | gray static / blue dynamic leakage")
        save(xyz, colors, "INPUT again | final-map decisions, not online growth")
    else:
        expected = "ConceptGraphs" if args.method == "conceptgraphs" else "HOV-SG"
        if record.get("method") != expected:
            raise ValueError("Method and source record differ")
        summary = record["summary"]
        if args.method == "conceptgraphs":
            with gzip.open(bound(run / "objects.pkl.gz"), "rb") as stream:
                objects = pickle.load(stream)["objects"]
            clouds = [np.asarray(o["pcd_np"]) for o in objects]
            images = sorted((run / "input/Replica/room0/gsa_vis_none").glob("*.jpg"))
            if not images:
                raise ValueError("Native SAM observation images missing")
            poses = np.loadtxt(bound(run / "input/Replica/room0/traj.txt")).reshape(-1, 4, 4)
            snapshots = {int(p.name.split(".")[0]): p for p in
                         (run / "input/Replica/room0/objects_all_frames").rglob("[0-9]*.pkl.gz")}
            for index in (1, 10, 20, 30, 39):
                with gzip.open(bound(snapshots[index]), "rb") as stream:
                    snapshot = pickle.load(stream)
                if not np.allclose(snapshot["camera_pose"], poses[index], atol=1e-6, rtol=0):
                    raise ValueError("Snapshot pose does not match supplied absolute pose")
                parts = [np.asarray(o["pcd_np"]) for o in snapshot["objects"]]
                image_path = bound(images[index])
                save(np.concatenate(parts), [135, 185, 200],
                     f"SAVED MAPPING SNAPSHOT | observation {index}/39 | {len(parts)} object entries",
                     Image.open(image_path), image_path.stem)
        else:
            import open3d as o3d
            clouds = [np.asarray(o3d.io.read_point_cloud(str(bound(p))).points)
                      for p in sorted((run / "objects").glob("*.ply"))]
            frames = json.loads(bound(run / "frame_observations.json").read_text())
            images = [run / "input/Replica/room0/results" / f"frame{f['source_index']:06d}.jpg"
                      for f in frames]
        if not clouds or any(not len(c) for c in clouds):
            raise ValueError("Empty map")
        xyz = np.concatenate(clouds)
        for i, query in enumerate(summary["queries"]):
            best = query["top_objects"][0]
            colors = np.concatenate([np.tile([255, 95, 60] if k == best["object_index"]
                                            else [135, 170, 185], (len(c), 1))
                                     for k, c in enumerate(clouds)])
            image_path = bound(images[round(i * (len(images)-1) / max(1, len(summary["queries"])-1))])
            image = Image.open(image_path)
            label = (f"FINAL MAP | query {query['query']} | candidate #{best['object_index']} "
                     f"| cosine {best['cosine_similarity']:.3f} (not probability)")
            save(xyz, colors, label, image, image_path.stem)
    combined = np.concatenate([np.load(args.output / s["file"])["xyz"] for s in steps])
    lower, upper = np.quantile(combined, [.01, .99], axis=0)
    manifest = {"schema_version": 1, "method": args.method, "kind": "measured_output_rviz_review",
                "scope": "Recorded graphical inspection of saved measured outputs; no new inference or FPS claim",
                "generator_sha256": digest(Path(__file__)), "sources": sources, "steps": steps,
                "display_transform": "(x,y,z)->(x,z,-y) for Replica only; stored maps unchanged",
                "focal_point": ((lower+upper)/2).tolist(), "distance": float(np.linalg.norm(upper-lower)*1.15)}
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2)+"\n")
    print(args.output / "manifest.json", flush=True)


if __name__ == "__main__":
    main()
