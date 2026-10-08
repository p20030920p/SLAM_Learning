"""One isolated author mapping replay with frozen inputs and injected translations."""

from __future__ import annotations

import argparse
import contextlib
import gzip
import json
import os
import pickle
import shutil
import subprocess
import sys
import time
import traceback
from pathlib import Path

import numpy as np

# CUDA environments intentionally do not install the separate CPU project lock.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from slam_learning.paired_pose import reference_targets, target_metrics
from slam_learning.provenance import digest, utc_now, write_json


def semantic_inputs(root, output, source, method, errors):
    config = json.loads((root / "configs/paired_pose.json").read_text())
    indexes = config["semantic_source_frames"]
    if method == "conceptgraphs":
        original = source / "input/Replica/room0"
    else:
        original = source / "input/Replica/room0"
    data = output / "input/Replica/room0"
    (data / "results").mkdir(parents=True)
    for index in indexes:
        for prefix, suffix in (("frame", ".jpg"), ("depth", ".png")):
            name = f"{prefix}{index:06d}{suffix}"
            (data / "results" / name).symlink_to(original / "results" / name)
        if method == "conceptgraphs":
            detections = data / "gsa_detections_none"
            detections.mkdir(exist_ok=True)
            name = f"frame{index:06d}.pkl.gz"
            (detections / name).symlink_to(original / "gsa_detections_none" / name)
    if method == "conceptgraphs":
        for name in ("gsa_classes_none.json", "gsa_classes_none_colors.json"):
            shutil.copy2(original / name, data / name)
    poses = np.loadtxt(root / ".cache/semantic-data/Replica/room0/traj.full.txt").reshape(-1, 4, 4)[indexes]
    poses[:, :3, 3] += errors
    # Preserve float64 native poses through the text adapter, including zero error.
    np.savetxt(data / "traj.txt", poses.reshape(-1, 16), fmt="%.17g")
    if method == "hovsg":
        shutil.copy2(source / "input/Replica/cam_params.json", data.parent / "cam_params.json")
    return data


def conceptgraphs(root, output, source, errors, threshold):
    data = semantic_inputs(root, output, source, "conceptgraphs", errors)
    work = source / "author-code"
    config = json.loads((root / "configs/semantic.json").read_text())
    overrides = dict(config["mapping_overrides"], save_suffix="paired", save_objects_all_frames=True)
    if threshold is not None:
        overrides["sim_threshold"] = threshold
    env = dict(
        os.environ,
        PYTHONPATH=str(work),
        MPLBACKEND="Agg",
        OMP_NUM_THREADS="4",
        OPENBLAS_NUM_THREADS="4",
        PYTHONHASHSEED="7",
    )
    command = [
        sys.executable,
        "-c",
        "import random,sys,runpy,numpy as np,torch; random.seed(7); np.random.seed(7); "
        "torch.manual_seed(7); sys.argv=sys.argv[1:]; runpy.run_path(sys.argv[0],run_name='__main__')",
        str(work / "conceptgraph/slam/cfslam_pipeline_batch.py"),
        f"dataset_root={data.parent}",
        f"dataset_config={work}/conceptgraph/dataset/dataconfigs/replica/replica.yaml",
        "scene_id=room0",
        *[f"{k}={str(v).lower() if isinstance(v,bool) else v}" for k, v in overrides.items()],
    ]
    print("Native ConceptGraphs mapping from frozen SAM/CLIP detections", flush=True)
    with (output / "native.log").open("w") as log:
        subprocess.run(
            command,
            cwd=work / "conceptgraph",
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
            check=True,
            timeout=1800,
        )
    with gzip.open(next((data / "pcd_saves").glob("*_post.pkl.gz")), "rb") as stream:
        saved = pickle.load(stream)
    objects = saved["objects"]
    clouds = [obj["pcd_np"] for obj in objects]
    features = np.asarray([obj["clip_ft"] for obj in objects])
    snapshots = sorted((data / "objects_all_frames/none_paired").glob("[0-9]*.pkl.gz"))
    history = []
    for path in snapshots:
        with gzip.open(path, "rb") as stream:
            snap = pickle.load(stream)
        history.append({"observation": int(path.name[:6]), "objects": len(snap["objects"])})
    return (
        clouds,
        features,
        {"command": command, "observations": 8, "history": history, "threshold": overrides["sim_threshold"]},
    )


def hovsg(root, output, source, errors, threshold):
    import torch
    import open3d as o3d
    from omegaconf import OmegaConf

    work = source / "author-code"
    sys.path.insert(0, str(work))
    from hovsg.dataloader.replica import ReplicaDataset
    import hovsg.graph.graph as graph_module

    data = semantic_inputs(root, output, source, "hovsg", errors)
    cfg = OmegaConf.load(source / "effective-config.yaml")
    cfg.main.dataset_path = str(data)
    cfg.main.save_path = str(output / "map")
    cfg.pipeline.skip_frames = 1
    if threshold is not None:
        cfg.pipeline.init_overlap_thresh = threshold
    torch.manual_seed(7)
    np.random.seed(7)
    # Native CPU advanced-index feature fusion is sensitive to thread count.
    torch.set_num_threads(8)
    graph = graph_module.Graph.__new__(graph_module.Graph)
    # Same native initialization except unused SAM/CLIP models: features are fixed.
    graph.cfg, graph.clip_feat_dim = cfg, 1024
    graph.full_pcd = o3d.geometry.PointCloud()
    graph.mask_pcds, graph.mask_feats, graph.full_feats_array = [], [], []
    graph.mask_generator = graph.clip_model = graph.preprocess = None
    graph.dataset = ReplicaDataset({"root_dir": str(data), "transforms": None})
    index = 0

    def cached_extract(image, *args, **kwargs):
        nonlocal index
        path = source / "observations" / f"{index:06d}.npz"
        with np.load(path) as saved:
            masks = saved["masks"]
            fp = torch.from_numpy(saved["mask_features"])
            global_features = saved["global_features"]
            expected = json.loads((root / "configs/paired_pose.json").read_text())["semantic_source_frames"][
                index
            ]
            if int(saved["source_index"]) != expected:
                raise ValueError("Cached HOV feature/frame association changed")
        if tuple(masks.shape[1:]) != tuple(image.shape[:2]):
            raise ValueError("Frozen HOV feature resolution differs")
        # These saved mask_features are native F_p, already including global/local fusion.
        # Repeat the original CUDA float32 accumulation, normalization and float16 cast.
        out = torch.zeros((image.shape[0] * image.shape[1], 1024), device="cuda")
        features_cuda = fp.cuda()
        for i, mask in enumerate(masks):
            ids = torch.from_numpy(np.flatnonzero(mask)).cuda()
            out[ids] += features_cuda[i]
        out = torch.nn.functional.normalize(out, p=2, dim=-1).half().reshape(*image.shape[:2], 1024).cpu()
        index += 1
        print(f"Frozen native HOV features: {index}/8", flush=True)
        return out, fp, [{"segmentation": mask} for mask in masks], global_features

    graph_module.extract_feats_per_pixel = cached_extract
    print("Native HOV-SG create_feature_map, frozen per-mask features", flush=True)
    with (
        (output / "native.log").open("w") as log,
        contextlib.redirect_stdout(log),
        contextlib.redirect_stderr(log),
    ):
        graph.create_feature_map()
    if index != 8:
        raise ValueError("Incomplete HOV feature replay")
    o3d.io.write_point_cloud(str(output / "map.ply"), graph.full_pcd)
    clouds = [np.asarray(cloud.points) for cloud in graph.mask_pcds]
    features = np.asarray(graph.mask_feats).reshape(len(clouds), -1)
    np.save(output / "segment_features.npy", features)
    # Strong zero-error control against the previous complete native execution.
    equivalent = (
        {name: digest(output / name) == digest(source / name) for name in ("map.ply", "segment_features.npy")}
        if not np.any(errors) and threshold is None
        else None
    )
    if equivalent is not None and not all(equivalent.values()):
        raise ValueError(f"HOV zero-error cached replay differs from native execution: {equivalent}")
    return (
        clouds,
        features,
        {
            "observations": 8,
            "reference_points": len(graph.full_pcd.points),
            "cache_zero_error_byte_equivalence": equivalent,
            "native_overlap_threshold": float(cfg.pipeline.init_overlap_thresh),
        },
    )


def lidar(root, output, method, errors, threshold):
    from slam_learning.pcd import read_pcd, write_pcd
    from slam_learning.adapters import beautymap_run
    from slam_learning.metrics import confusion_metrics
    from scipy.spatial import cKDTree

    config = json.loads((root / "configs/methods.json").read_text())[method]
    source = root / ".cache/datasets/00"
    truth = read_pcd(source / "gt_cloud.pcd")
    labels = np.asarray(truth.records["intensity"])
    paths = sorted((source / "pcd").glob("*.pcd"))
    sequence = output / "sequence"
    (sequence / "pcd").mkdir(parents=True)
    points, sensor_poses, start = [], [], 0
    for i, path in enumerate(paths):
        cloud = read_pcd(path)
        xyz = cloud.xyz()
        if not np.array_equal(xyz, truth.xyz(slice(start, start + len(xyz)))):
            raise ValueError("Original scan/GT point identity mismatch")
        start += len(xyz)
        xyz += errors[i].astype(np.float32)
        pose = cloud.viewpoint.copy()
        pose[:3] = (np.asarray(pose[:3]) + errors[i]).tolist()
        write_pcd(sequence / "pcd" / path.name, xyz, viewpoint=pose)
        points.append(xyz)
        sensor_poses.append(pose)
    points = np.concatenate(points)
    if start != len(labels):
        raise ValueError("GT scan coverage mismatch")
    write_pcd(sequence / "gt_cloud.pcd", points)  # No intensity/GT is passed to algorithms.
    params = dict(config["parameters"])
    if threshold is not None:
        params["d_p" if method == "dufomap" else "xy_resolution"] = threshold
    cleaned = output / "cleaned.pcd"
    direct_metrics = None
    with (
        (output / "native.log").open("w") as log,
        contextlib.redirect_stdout(log),
        contextlib.redirect_stderr(log),
    ):
        if method == "dufomap":
            from dufomap import dufomap

            previous = Path.cwd()
            os.chdir(output)
            try:
                mapper = dufomap(
                    params["resolution"], params["d_s"], params["d_p"], num_threads=params["threads"]
                )
                offset = 0
                sizes = [len(read_pcd(path).records) for path in paths]
                for index, (size, pose) in enumerate(zip(sizes, sensor_poses)):
                    xyz = points[offset : offset + size]
                    ranges = np.linalg.norm(xyz - np.asarray(pose[:3]), axis=1)
                    mapper.run(xyz[(ranges > 0.2) & (ranges < 50)], pose, cloud_transform=False)
                    offset += size
                    if index % 20 == 0:
                        print(f"DUFOMap integration {index+1}/141", flush=True)
                mapper.oncePropagateCluster(if_propagate=True, if_cluster=False)
                mapper.outputMap(points, voxel_map=False)
                (output / "dufomap_output.pcd").rename(cleaned)
                direct = np.empty(len(points), dtype=np.uint8)
                offset = 0
                for size, pose in zip(sizes, sensor_poses):
                    predicted = np.asarray(
                        mapper.segment(points[offset : offset + size], pose, cloud_transform=False)
                    )
                    if predicted.shape != (size,) or not np.isin(predicted, [0, 1]).all():
                        raise ValueError("Invalid DUFO point labels")
                    direct[offset : offset + size] = predicted
                    offset += size
                direct_metrics = confusion_metrics(labels, direct)
                np.save(output / "direct_point_predictions.npy", direct)
                details = {
                    "frames": 141,
                    "author_api": "dufomap 1.1.1; integration, propagation, outputMap and segment",
                    "integration_range_m": [0.2, 50],
                }
            finally:
                os.chdir(previous)
        else:
            details = beautymap_run(sequence, cleaned, root / ".cache/upstream/beautymap", params, 0)
    prediction = np.empty(len(points), dtype=np.uint8)
    tree = cKDTree(read_pcd(cleaned).xyz())
    for start in range(0, len(points), 500_000):
        distances = tree.query(points[start : start + 500_000], workers=4)[0]
        prediction[start : start + len(distances)] = (distances > 0.05).astype(np.uint8)
    np.save(output / "point_predictions.npy", prediction)
    measured = confusion_metrics(labels, prediction)
    return {
        "mapping": details,
        "metrics": measured,
        "direct_point_metrics": direct_metrics,
        "input_points": len(points),
        "input_has_labels": False,
        "parameters": params,
        "evaluation": "Original point identities/labels, evaluated at their own perturbed XYZ against cleaned map, 5cm NN. Not a paper-table score or unperturbed-world alignment score.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--method", required=True, choices=["dufomap", "beautymap", "conceptgraphs", "hovsg"])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--errors", type=Path, required=True)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--text-features", type=Path)
    parser.add_argument("--threshold", type=json.loads)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    errors = np.load(args.errors)
    record = {
        "schema_version": 1,
        "kind": "paired_author_mapping_cell",
        "method": args.method,
        "status": "running",
        "started_at": utc_now(),
        "artifacts": {},
        "command": sys.argv,
        "errors_sha256": digest(args.errors),
        "script_sha256": digest(Path(__file__)),
        "annotations_sha256": digest(root / "annotations/room0/targets.json"),
        "exit_code": None,
    }
    write_json(output / "record.json", record)
    start = time.monotonic()
    try:
        if args.method in ("dufomap", "beautymap"):
            result = lidar(root, output, args.method, errors, args.threshold)
        else:
            mapper = conceptgraphs if args.method == "conceptgraphs" else hovsg
            clouds, features, details = mapper(root, output, args.source, errors, args.threshold)
            if not clouds or any(not len(cloud) for cloud in clouds):
                raise ValueError("Empty author segments")
            artifact = {f"cloud_{i:04d}": points for i, points in enumerate(clouds)}
            artifact["features"] = features
            np.savez_compressed(output / "objects.npz", **artifact)
            cfg = json.loads((root / "configs/paired_pose.json").read_text())
            result = {
                "mapping": details,
                "objects": len(clouds),
                "metrics": target_metrics(
                    clouds,
                    features,
                    np.load(args.text_features),
                    cfg["semantic_queries"],
                    reference_targets(root),
                    cfg["semantic_matching_distance_m"],
                    cfg["semantic_reference_coverage_min"],
                    cfg["semantic_prediction_precision_min"],
                ),
            }
        write_json(output / "summary.json", result)
        record.update(status="executed", exit_code=0, summary=result)
    except Exception as error:
        record.update(status="failed", exit_code=1, error=str(error), traceback=traceback.format_exc())
        print(record["traceback"], flush=True)
    finally:
        record.update(finished_at=utc_now(), elapsed_seconds=time.monotonic() - start)
        for path in output.rglob("*"):
            if (
                not path.is_file()
                or path.is_symlink()
                or path.name == "record.json"
                or any(name in path.parts for name in ("input", "author-code", "sequence"))
            ):
                continue
            name = path.relative_to(output).as_posix()
            record["artifacts"][name] = {
                "sha256": digest(path),
                "bytes": path.stat().st_size,
                "availability": "local_only"
                if path.suffix in (".pcd", ".npy", ".npz", ".gz", ".ply")
                else "portable",
            }
        write_json(output / "record.json", record)
    print(f"{args.method} {record['status']} -> {output / 'record.json'}", flush=True)
    return record["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
