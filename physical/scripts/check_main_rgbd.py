"""CPU-only checks through unmodified author RGB-D loaders pinned by main.

Run separately in main's existing semantic and HOV-SG environments. No model
weights, CUDA kernels, semantic mapping, odometry, or quality scores are run.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys
import traceback

import numpy as np


def sha(path):
    with Path(path).open("rb") as stream:
        h = hashlib.sha256()
        for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            h.update(chunk)
        return h.hexdigest()


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("dataset", type=Path)
    ap.add_argument("--method", choices=("conceptgraphs", "hovsg"), required=True)
    ap.add_argument("--main-repo", type=Path, required=True)
    ap.add_argument("--runtime", type=Path, required=True)
    ap.add_argument("--commit", default="354b02d69ccc90304174f6d36010d25043d739ca")
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    args.dataset = args.dataset.resolve()
    args.output.mkdir(parents=True, exist_ok=False)
    record = {"kind": "physical_rgbd_author_loader_check", "method": args.method,
              "status": "failed", "started_at": datetime.now(timezone.utc).isoformat(),
              "main_commit": args.commit, "script_sha256": sha(__file__),
              "execution_device": "cpu", "semantic_algorithm_executed": False,
              "quality_metrics_evaluated": False, "frames": [],
              "limitations": ["Does not load SAM/CLIP or execute object mapping",
                              "Projection consistency is not independent camera range accuracy",
                              "Identity poses are an operator fixed-camera assumption, not estimated SLAM"]}
    try:
        import cv2
        from PIL import Image
        import torch
        torch.set_num_threads(2)
        record["packages"] = {p: importlib.metadata.version(p) for p in ("torch", "numpy", "Pillow")}
        manifest_path = args.dataset / "rgbd.json"
        manifest = json.loads(manifest_path.read_text())
        record["input_manifest_sha256"] = sha(manifest_path)
        record["raw_recording_sha256"] = manifest["source_sha256"]
        record["pose_source"] = manifest["pose_source"]
        if manifest["status"] != "exported" or manifest["source_session_note"].get("camera_fixed_declared_by_operator") is not True:
            raise ValueError("Require successful export from an operator-declared fixed camera")
        if manifest["depth_aligned_to"] != "color":
            raise ValueError("Require depth aligned to color")
        for row in manifest["frames"]:
            for item in row["files"].values():
                path = (args.dataset / item["path"]).resolve()
                if not path.is_relative_to(args.dataset) or sha(path) != item["sha256"]:
                    raise ValueError("Input file hash or containment failed")
        for path, expected in manifest["configuration_files"].items():
            candidate = (args.dataset / path).resolve()
            if not candidate.is_relative_to(args.dataset) or sha(candidate) != expected:
                raise ValueError("Configuration hash or containment failed")
        cfg_path = "configs/semantic.json" if args.method == "conceptgraphs" else "configs/hovsg.json"
        cfg_blob = git(args.main_repo, "show", f"{args.commit}:{cfg_path}")
        cfg = json.loads(cfg_blob)
        record["main_configuration_sha256"] = hashlib.sha256(cfg_blob).hexdigest()
        spec = cfg["upstreams"]["conceptgraphs"] if args.method == "conceptgraphs" else cfg["upstream"]
        source = args.runtime / ".cache/upstream" / args.method
        if git(source, "rev-parse", "HEAD").decode().strip() != spec["commit"] or git(source, "status", "--porcelain").strip():
            raise ValueError("Author source must be clean and match frozen main configuration")
        namespace = "conceptgraph" if args.method == "conceptgraphs" else "hovsg"
        snapshot = args.output / "author-source"
        snapshot.mkdir()
        files = git(source, "ls-tree", "-r", "--name-only", spec["commit"], namespace).decode().splitlines()
        source_hashes = {}
        for relative in files:
            if not relative.endswith(".py"):
                continue
            blob = git(source, "show", f"{spec['commit']}:{relative}")
            target = snapshot / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(blob)
            source_hashes[relative] = hashlib.sha256(blob).hexdigest()
        record["upstream_commit"] = spec["commit"]
        record["source_blobs"] = source_hashes
        sys.path.insert(0, str(snapshot.resolve()))
        intr = manifest["color_intrinsics"]
        K = np.array([[intr["fx"], 0, intr["ppx"]], [0, intr["fy"], intr["ppy"]], [0, 0, 1]])
        layout = args.dataset / "replica-layout"
        if args.method == "conceptgraphs":
            from conceptgraph.dataset.datasets_common import ReplicaDataset
            dataset = ReplicaDataset(json.loads((args.dataset / "conceptgraphs-camera.json").read_text()),
                basedir=str(layout), sequence="physical", stride=1, desired_height=intr["height"],
                desired_width=intr["width"], device="cpu", relative_pose=False)
        else:
            from hovsg.dataloader.replica import ReplicaDataset
            dataset = ReplicaDataset({"root_dir": str(layout / "physical"), "transforms": None})
        if len(dataset) != len(manifest["frames"]):
            raise ValueError("Native loader frame count mismatch")
        for index, row in enumerate(manifest["frames"]):
            reference_rgb = np.asarray(Image.open(args.dataset / row["files"]["color"]["path"]))
            raw_depth = np.asarray(Image.open(args.dataset / row["files"]["depth"]["path"])).astype(np.float64)
            expected_depth = raw_depth * manifest["depth_unit_m"]
            if args.method == "conceptgraphs":
                rgb, depth, native_K, pose = dataset[index]
                rgb, depth = rgb.numpy(), depth.numpy().squeeze(-1)
                native_K, pose = native_K.numpy()[:3, :3], pose.numpy()
            else:
                rgb, depth, pose, _, native_K = dataset[index]
                rgb = np.asarray(rgb)
                depth = np.asarray(depth, dtype=np.float64) / dataset.scale
            if rgb.shape != reference_rgb.shape or depth.shape != raw_depth.shape:
                raise ValueError("Native loader image dimensions differ")
            rgb_error = float(np.max(np.abs(rgb.astype(float) - reference_rgb.astype(float))))
            depth_error = float(np.max(np.abs(depth - expected_depth)))
            intr_error = float(np.max(np.abs(native_K - K)))
            if rgb_error != 0 or depth_error > 2e-6 or intr_error > 1e-4 or not np.allclose(pose, np.eye(4), atol=1e-7):
                raise ValueError(f"Native loader color/depth/calibration/pose mismatch: {rgb_error, depth_error, intr_error}")
            valid = raw_depth > 0
            y, x = np.nonzero(valid)
            z = expected_depth[valid]
            expected_points = np.column_stack(((x - K[0, 2]) * z / K[0, 0], (y - K[1, 2]) * z / K[1, 1], z))
            geometry_error = None
            reprojection_error = None
            if args.method == "hovsg":
                cloud = dataset.create__pcd(Image.fromarray(reference_rgb), Image.open(args.dataset / row["files"]["depth"]["path"]), pose)
                points = np.asarray(cloud.points)
                if points.shape != expected_points.shape or not len(points) or not np.isfinite(points).all():
                    raise ValueError("Native point cloud count/finite check failed")
                geometry_error = float(np.max(np.abs(points - expected_points)))
                pixel = points @ K.T
                pixel = pixel[:, :2] / pixel[:, 2:3]
                reprojection_error = float(np.max(np.abs(pixel - np.column_stack((x, y)))))
                if geometry_error > 2e-5 or reprojection_error > 1e-3:
                    raise ValueError("Native point cloud geometry consistency failed")
                if index == 0:
                    import open3d as o3d
                    if not o3d.io.write_point_cloud(str(args.output / "native-first-frame.ply"), cloud):
                        raise OSError("Native PLY write failed")
            record["frames"].append({"index": index, "color_error_jpeg_units": rgb_error,
                "depth_max_error_m": depth_error, "intrinsics_max_error": intr_error,
                "valid_depth_points": int(valid.sum()), "native_xyz_max_error_m": geometry_error,
                "native_reprojection_max_error_px": reprojection_error})
        record.update(status="loader_check_passed", frames_checked=len(record["frames"]))
    except Exception as error:
        record.update(error=repr(error), traceback=traceback.format_exc())
    finally:
        record["finished_at"] = datetime.now(timezone.utc).isoformat()
        (args.output / "record.json").write_text(json.dumps(record, indent=2, allow_nan=False) + "\n")
    print(json.dumps({k: v for k, v in record.items() if k not in ("frames", "source_blobs")}, indent=2))
    return int(record["status"] != "loader_check_passed")


if __name__ == "__main__":
    raise SystemExit(main())
