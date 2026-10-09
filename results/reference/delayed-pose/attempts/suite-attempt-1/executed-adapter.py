"""Execute a sealed ConceptGraphs late-correction test with native primitives."""
from __future__ import annotations

import argparse
import copy
import gzip
import hashlib
import json
import os
import pickle
import random
import subprocess
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from slam_learning.delayed_pose import measure_map, prefix_errors, reference_instances


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def seed_frame(index, seed, torch):
    random.seed(seed + index)
    np.random.seed(seed + index)
    torch.manual_seed(seed + index)


def members(obj):
    return list(zip(map(int, obj["image_idx"]), map(int, obj["mask_idx"])))


def arrays(objects):
    return ([np.asarray(o["pcd"].points).copy() for o in objects],
            np.asarray([o["clip_ft"].detach().cpu().numpy() for o in objects]).reshape(len(objects), -1)
            if objects else np.empty((0, 1024)))


def compare_maps(left, right, tolerance=1e-8):
    if len(left) != len(right):
        return {"passed": False, "reason": "object count", "counts": [len(left), len(right)]}
    max_error, feature_error = 0., 0.
    for a, b in zip(left, right):
        if members(a) != members(b):
            return {"passed": False, "reason": "historical membership"}
        pa, pb = np.asarray(a["pcd"].points), np.asarray(b["pcd"].points)
        if pa.shape != pb.shape:
            return {"passed": False, "reason": "point count"}
        pa = pa[np.lexsort(pa.T[::-1])]
        pb = pb[np.lexsort(pb.T[::-1])]
        max_error = max(max_error, float(np.max(np.abs(pa - pb))))
        feature_error = max(feature_error, float(np.max(np.abs(
            a["clip_ft"].cpu().numpy() - b["clip_ft"].cpu().numpy()))))
    return {"passed": bool(max_error <= tolerance and feature_error <= tolerance),
            "max_coordinate_difference_m": max_error, "max_feature_difference": feature_error,
            "memberships_equal": True, "objects": len(left)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--frontend", type=Path, required=True)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--freeze", type=Path, required=True)
    parser.add_argument("--weights", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.root
    config_path = root / "configs/delayed_pose.json"
    annotation_path = root / "annotations/room1/targets.json"
    config = json.loads(config_path.read_text())
    seal = json.loads(args.freeze.read_text())
    for key, path in (("protocol_sha256", config_path), ("annotations_sha256", annotation_path),
                      ("source_manifest_sha256", args.data / "manifest.json")):
        if seal[key] != sha(path):
            raise ValueError(f"Frozen input changed: {path}")
    front = json.loads((args.frontend / "record.json").read_text())
    if front["status"] != "executed" or front["freeze_sha256"] != sha(args.freeze):
        raise ValueError("Frontend did not pass the frozen-input gate")
    for name, info in front["artifacts"].items():
        if sha(args.frontend / name) != info["sha256"]:
            raise ValueError("Frozen frontend changed")
    args.output.mkdir(parents=True, exist_ok=False)
    for name, source in (("protocol.json", config_path), ("annotations.json", annotation_path),
                         ("freeze.json", args.freeze), ("source-manifest.json", args.data / "manifest.json"),
                         ("frontend-record.json", args.frontend / "record.json"),
                         ("executed-adapter.py", Path(__file__)),
                         ("executed-metrics.py", root / "src/slam_learning/delayed_pose.py")):
        (args.output / name).write_bytes(source.read_bytes())
    record = {"kind": "delayed_pose_correction", "status": "running",
              "started_at": datetime.now(timezone.utc).isoformat(), "configuration": config,
              "freeze_sha256": sha(args.freeze), "cells": [], "gates": {}, "artifacts": {}}
    record_path = args.output / "record.json"
    write(record_path, record)
    try:
        import torch
        from omegaconf import OmegaConf

        work = args.frontend / "author-code"
        sys.path.insert(0, str(work))
        from conceptgraph.dataset.datasets_common import get_dataset
        from conceptgraph.slam.slam_classes import MapObjectList
        from conceptgraph.slam.utils import (
            create_or_load_colors, denoise_objects, filter_objects, gobs_to_detection_list, merge_objects,
        )
        from conceptgraph.slam.mapping import (
            aggregate_similarities, compute_spatial_similarities, compute_visual_similarities,
            merge_detections_to_objects,
        )

        torch.set_num_threads(4)
        cfg = OmegaConf.load(work / "conceptgraph/configs/slam_pipeline/base.yaml")
        mapping = json.loads((root / "configs/semantic.json").read_text())["mapping_overrides"]
        for key, value in mapping.items():
            cfg[key] = value
        cfg.dataset_root = str(args.frontend / "input/Replica")
        cfg.dataset_config = str(work / "conceptgraph/dataset/dataconfigs/replica/replica.yaml")
        cfg.scene_id, cfg.save_suffix, cfg.save_objects_all_frames = config["scene"], "late_zero_gate", False
        dataset = get_dataset(dataconfig=Path(cfg.dataset_config), start=cfg.start, end=cfg.end,
                              stride=cfg.stride, basedir=Path(cfg.dataset_root), sequence=cfg.scene_id,
                              desired_height=cfg.image_height, desired_width=cfg.image_width,
                              device="cpu", dtype=torch.float)
        if len(dataset) != len(config["mapping_frames"]):
            raise ValueError("Reference views leaked into mapping")
        classes, _ = create_or_load_colors(cfg, cfg.color_file_name)
        true_poses = np.stack([p.cpu().numpy() for p in dataset.poses])
        instances = reference_instances(annotation_path, args.data)
        text_path = args.output / "text_features.npy"
        import open_clip

        model, _, _ = open_clip.create_model_and_transforms(
            "ViT-H-14", str(args.weights / "clip/open_clip_pytorch_model.bin"), device="cuda")
        model.eval()
        with torch.no_grad():
            text = model.encode_text(open_clip.get_tokenizer("ViT-H-14")(
                [i["query"] for i in instances]).to("cuda")).float()
            text = torch.nn.functional.normalize(text, dim=-1).cpu().numpy()
        del model
        torch.cuda.empty_cache()
        np.save(text_path, text)
        split = config["correction_after_observations"]

        def observations(index, offset):
            seed_frame(index, config["mapping_seed"], torch)
            color_tensor, depth_tensor, intrinsics, *_ = dataset[index]
            image = color_tensor.cpu().numpy().astype(np.uint8)
            depth = depth_tensor[..., 0].cpu().numpy()
            k = intrinsics.cpu().numpy()[:3, :3]
            color_path = Path(dataset.color_paths[index])
            det_path = color_path.parent.parent / "gsa_detections_none" / color_path.with_suffix(".pkl.gz").name
            with gzip.open(det_path, "rb") as stream:
                gobs = pickle.load(stream)
            pose = true_poses[index].astype(float).copy()
            pose[:3, 3] += offset
            detections, background = gobs_to_detection_list(
                cfg=cfg, image=image, depth_array=depth, cam_K=k, idx=index, gobs=gobs,
                trans_pose=pose, class_names=classes, BG_CLASSES=["wall", "floor", "ceiling"],
                color_path=str(color_path))
            if len(background):
                raise ValueError("Unexpected background in class-agnostic core")
            return detections, (pose, depth, k)

        def visibility(obj, detection, view):
            pose, depth, k = view
            points = np.asarray(obj["pcd"].points)
            camera = (points - pose[:3, 3]) @ pose[:3, :3]
            camera = camera[camera[:, 2] > .01]
            uv = np.rint(camera[:, :2] / camera[:, 2, None] * [k[0, 0], k[1, 1]] +
                         [k[0, 2], k[1, 2]]).astype(int)
            valid = ((uv[:, 0] >= 0) & (uv[:, 0] < depth.shape[1]) &
                     (uv[:, 1] >= 0) & (uv[:, 1] < depth.shape[0]))
            uv, camera = uv[valid], camera[valid]
            uv = np.unique(uv[np.abs(camera[:, 2] - depth[uv[:, 1], uv[:, 0]]) <=
                              config["visibility_depth_tolerance_m"]], axis=0)
            return (len(uv) >= config["visibility_min_pixels"] and
                    np.mean(detection["mask"][0][uv[:, 1], uv[:, 0]]) >= config["visibility_min_support"])

        def step(objects, index, offset, arm, forced=None):
            detections, view = observations(index, offset)
            keys = [int(d["mask_idx"][0]) for d in detections]
            if forced is not None and keys != forced["mask_keys"]:
                raise ValueError("Pose-dependent accepted detections changed: pure association contrast invalid")
            if not detections:
                return objects, {"frame": index, "mask_keys": keys, "assignments": []}
            if not objects:
                objects.extend(detections)
                return objects, {"frame": index, "mask_keys": keys, "assignments": [-1] * len(keys)}
            if forced is not None:
                assignments = forced["assignments"]
                similarity = torch.full((len(keys), len(objects)), float("-inf"))
                for i, j in enumerate(assignments):
                    if j >= 0:
                        if j >= len(objects):
                            raise ValueError("Historical object index missing")
                        similarity[i, j] = 1.
            else:
                spatial = compute_spatial_similarities(cfg, detections, objects)
                visual = compute_visual_similarities(cfg, detections, objects)
                similarity = aggregate_similarities(cfg, spatial, visual)
                threshold = config["simple_threshold"] if arm in ("threshold", "visibility") else config["native_threshold"]
                similarity[similarity < threshold] = float("-inf")
                if arm == "visibility":
                    for i in range(len(detections)):
                        for j in torch.where(torch.isfinite(similarity[i]))[0].tolist():
                            if not visibility(objects[j], detections[i], view):
                                similarity[i, j] = float("-inf")
                assignments = [int(row.argmax()) if torch.isfinite(row).any() else -1 for row in similarity]
            objects = merge_detections_to_objects(cfg, detections, objects, similarity)
            for interval, operation in ((cfg.denoise_interval, denoise_objects),
                                        (cfg.filter_interval, filter_objects), (cfg.merge_interval, merge_objects)):
                if interval > 0 and (index + 1) % interval == 0:
                    objects = operation(cfg, objects)
            return objects, {"frame": index, "mask_keys": keys, "assignments": assignments}

        def prefix(forced=None):
            objects = MapObjectList(device=cfg.device)
            for index in range(split):
                objects, _ = step(objects, index, np.zeros(3), "native", None if forced is None else forced[index])
            return objects

        def finish(objects):
            objects = denoise_objects(cfg, objects)
            objects = filter_objects(cfg, objects)
            return merge_objects(cfg, objects)

        zero_stages = {}

        def evaluate(objects, stage, cell_dir, trace):
            exposed = MapObjectList([o for o in objects if o["num_detections"] >= cfg.obj_min_detections])
            clouds, features = arrays(exposed)
            payload = {f"pcd_{i:04d}": p for i, p in enumerate(clouds)}
            payload.update(features=features, members_json=np.array(json.dumps([members(o) for o in exposed])))
            np.savez_compressed(cell_dir / f"stage-{stage:02d}.npz", **payload)
            metric = measure_map(clouds, features, text, instances, config, config["mapping_frames"][stage - 1])
            metric["observation"] = stage
            metric["native_state_objects"] = len(objects)
            write(cell_dir / f"stage-{stage:02d}.json", metric)
            return metric

        settings = [(0., 0)] + [(rms, seed) for rms in config["translation_rms_m"] for seed in config["seeds"]]
        for rms, seed in settings:
            errors = prefix_errors(split, rms, seed)
            for arm in config["arms"]:
                name = f"{arm}-{rms:.2f}-{seed}"
                cell_dir = args.output / "cells" / name
                cell_dir.mkdir(parents=True)
                cell = {"arm": arm, "rms_m": rms, "seed": seed, "status": "running",
                        "started_at": datetime.now(timezone.utc).isoformat(), "stages": []}
                write(cell_dir / "record.json", cell)
                started = time.monotonic()
                objects, trace = MapObjectList(device=cfg.device), []
                try:
                    for index in range(len(dataset)):
                        objects, event = step(objects, index, errors[index] if index < split else np.zeros(3), arm)
                        trace.append(event)
                        if index + 1 == split:
                            before_clouds, before_features = arrays(objects)
                            np.savez_compressed(cell_dir / "before-correction.npz", features=before_features,
                                                **{f"pcd_{j:04d}": p for j, p in enumerate(before_clouds)})
                            correction_start = time.monotonic()
                            if arm == "fixed_association":
                                original = objects
                                objects = prefix(trace)
                                if [members(o) for o in objects] != [members(o) for o in original]:
                                    raise ValueError("Coordinate control changed historical memberships")
                                for rebuilt, old in zip(objects, original):
                                    rebuilt["clip_ft"], rebuilt["text_ft"] = old["clip_ft"].clone(), old["text_ft"].clone()
                            elif arm == "oracle_replay":
                                objects = prefix()
                            cell["correction_compute_seconds"] = time.monotonic() - correction_start
                        if index + 1 == len(dataset):
                            objects = finish(objects)
                        if index + 1 in config["evaluation_observations"]:
                            stage = index + 1
                            cell["stages"].append(evaluate(objects, stage, cell_dir, trace))
                            if rms == 0 and arm == "native":
                                zero_stages[stage] = copy.deepcopy(objects)
                            elif rms == 0 and arm in ("fixed_association", "oracle_replay"):
                                gate = compare_maps(zero_stages[stage], objects)
                                record["gates"][f"zero-{arm}-{stage}"] = gate
                                if not gate["passed"]:
                                    raise ValueError(f"Zero-error correction gate failed: {gate}")
                    if rms == 0 and arm == "native":
                        # Run the original batch script with only the identical per-frame RNG wrapper.
                        original_script = work / "conceptgraph/slam/cfslam_pipeline_batch.py"
                        source = original_script.read_text()
                        marker = 'BG_CLASSES = ["wall", "floor", "ceiling"]'
                        wrapper = '\n_native_detection_factory = gobs_to_detection_list\n' + \
                            'def gobs_to_detection_list(*args, **kwargs):\n' + \
                            '    import random\n' + \
                            '    s = 7 + int(kwargs["idx"])\n' + \
                            '    random.seed(s); np.random.seed(s); torch.manual_seed(s)\n' + \
                            '    return _native_detection_factory(*args, **kwargs)\n'
                        if source.count(marker) != 1:
                            raise ValueError("Unexpected pinned mapper source")
                        runtime_script = args.output / "native-zero-gate.py"
                        runtime_script.write_text(source.replace(marker, marker + wrapper))
                        # Hydra resolves config relative to the runtime script; supply its exact directory.
                        command = [sys.executable, str(runtime_script),
                                   "--config-path", str(work / "conceptgraph/configs/slam_pipeline"),
                                   f"dataset_root={cfg.dataset_root}", f"dataset_config={cfg.dataset_config}",
                                   f"scene_id={cfg.scene_id}",
                                   *[f"{k}={str(v).lower() if isinstance(v, bool) else v}" for k, v in mapping.items()],
                                   "save_suffix=late_zero_gate", "save_objects_all_frames=false"]
                        env = dict(os.environ, PYTHONPATH=str(work), MPLBACKEND="Agg", OMP_NUM_THREADS="4",
                                   OPENBLAS_NUM_THREADS="4", PYTHONHASHSEED="7")
                        write(args.output / "native-zero-command.json", command)
                        with (args.output / "native-zero.log").open("w") as log:
                            subprocess.run(command, cwd=work / "conceptgraph", env=env, stdout=log,
                                           stderr=subprocess.STDOUT, timeout=600, check=True)
                        saved = Path(cfg.dataset_root) / cfg.scene_id / "pcd_saves/full_pcd_none_late_zero_gate_post.pkl.gz"
                        with gzip.open(saved, "rb") as stream:
                            native_saved = pickle.load(stream)
                        native_objects = MapObjectList()
                        native_objects.load_serializable(native_saved["objects"])
                        gate = compare_maps(objects, native_objects)
                        record["gates"]["extracted-loop-vs-native-batch"] = gate
                        if not gate["passed"]:
                            raise ValueError(f"Native loop parity failed: {gate}")
                    cell.update(status="executed", elapsed_seconds=time.monotonic() - started)
                except Exception as error:
                    cell.update(status="failed", error=str(error), traceback=traceback.format_exc())
                cell["finished_at"] = datetime.now(timezone.utc).isoformat()
                write(cell_dir / "decision-trace.json", trace)
                write(cell_dir / "record.json", cell)
                record["cells"].append({"name": name, "status": cell["status"], "record_sha256": sha(cell_dir / "record.json")})
                write(record_path, record)
                print(f"{name}: {cell['status']} ({time.monotonic() - started:.1f}s)", flush=True)
                if cell["status"] != "executed":
                    raise RuntimeError(f"Stop on failed cell: {name}: {cell.get('error')}")
        record["status"] = "executed"
    except Exception as error:
        record.update(status="failed", error=str(error), traceback=traceback.format_exc())
    finally:
        record["finished_at"] = datetime.now(timezone.utc).isoformat()
        for path in args.output.iterdir():
            if path.is_file() and path != record_path:
                record["artifacts"][path.name] = {"sha256": sha(path), "bytes": path.stat().st_size}
        write(record_path, record)
    print(f"Delayed correction {record['status']}: {record_path}", flush=True)
    return int(record["status"] != "executed")


if __name__ == "__main__":
    raise SystemExit(main())
