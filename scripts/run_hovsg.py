"""Execute the original HOV-SG feature-map core with traceable resource adaptations."""
from __future__ import annotations

import contextlib
import difflib
import importlib.metadata
import json
import os
import shutil
import subprocess
import sys
import traceback
import uuid
from pathlib import Path

from run_conceptgraphs import sha, timestamp


def main():
    root = Path(__file__).resolve().parents[1]
    output = root / "results/runs" / f"hovsg-{uuid.uuid4().hex[:12]}"
    output.mkdir(parents=True)
    cfg_path = root / "configs/hovsg.json"
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    semantic = json.loads((root / "configs/semantic.json").read_text(encoding="utf-8"))
    source = root / ".cache/upstream/hovsg"
    record = {"schema_version": 1, "kind": "semantic_frontend_baseline", "method": "HOV-SG",
              "status": "running", "started_at": timestamp(), "configuration": cfg, "artifacts": {},
              "script_sha256": sha(__file__), "config_sha256": sha(cfg_path), "exit_code": None,
              "repository": {"commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
                             "dirty": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=root, text=True).strip())}}

    def save():
        (output / "record.json").write_text(json.dumps(record, indent=2, allow_nan=False) + "\n", encoding="utf-8")

    save()
    try:
        import numpy as np
        import torch
        from PIL import Image
        from omegaconf import OmegaConf
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA required")
        torch.set_num_threads(8)
        torch.manual_seed(7)
        np.random.seed(7)
        if subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source, text=True).strip() != cfg["upstream"]["commit"]:
            raise ValueError("HOV-SG commit mismatch")
        if subprocess.check_output(["git", "status", "--porcelain"], cwd=source, text=True).strip():
            raise ValueError("Author source must be clean")
        (output / "environment.txt").write_text("\n".join(sorted(
            f"{d.metadata['Name']}=={d.version}" for d in importlib.metadata.distributions())) + "\n")
        data_source = root / ".cache/semantic-data/Replica"
        manifest = json.loads((data_source / "manifest.json").read_text())
        expected = list(range(0, 200, 5))
        if manifest["source_frame_indexes"] != expected:
            raise ValueError("Replica subset mismatch")
        input_root = output / "input/Replica"
        dimensions = None
        for item in manifest["files"]:
            original = (data_source / item["path"]).resolve()
            if not original.is_relative_to(data_source.resolve()) or sha(original) != item["sha256"]:
                raise ValueError("Dataset hash mismatch")
            target = input_root / item["path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            if original.suffix.lower() in (".jpg", ".png"):
                with Image.open(original) as image:
                    dimensions = image.size
                    resample = Image.Resampling.NEAREST if original.name.startswith("depth") else Image.Resampling.BILINEAR
                    image.resize((cfg["image_width"], cfg["image_height"]), resample).save(target)
            else:
                shutil.copy2(original, target)
        # The ZIP subset has no camera file; use the same pinned author calibration as ConceptGraphs.
        params_path = input_root / "cam_params.json"
        camera_source = root / ".cache/upstream/conceptgraphs/conceptgraph/dataset/dataconfigs/replica/replica.yaml"
        camera = OmegaConf.load(camera_source).camera_params
        if dimensions != (camera.image_width, camera.image_height):
            raise ValueError("Original image dimensions disagree with pinned Replica calibration")
        params = {"camera": {"w": camera.image_width, "h": camera.image_height, "fx": camera.fx,
                             "fy": camera.fy, "cx": camera.cx, "cy": camera.cy, "scale": camera.png_depth_scale}}
        shutil.copy2(camera_source, output / "camera-source.yaml")
        record["camera_source"] = {"commit": semantic["upstreams"]["conceptgraphs"]["commit"],
                                   "path": "conceptgraph/dataset/dataconfigs/replica/replica.yaml",
                                   "sha256": sha(camera_source)}
        cam = params["camera"]
        sx, sy = cfg["image_width"] / dimensions[0], cfg["image_height"] / dimensions[1]
        for key in ("fx", "cx"):
            cam[key] *= sx
        for key in ("fy", "cy"):
            cam[key] *= sy
        cam.update(w=cfg["image_width"], h=cfg["image_height"])
        params_path.write_text(json.dumps(params, indent=2) + "\n")
        shutil.copy2(data_source / "manifest.json", output / "dataset-manifest.json")
        derived = [{"path": p.relative_to(input_root).as_posix(), "sha256": sha(p)}
                   for p in sorted(input_root.rglob("*")) if p.is_file()]
        (output / "derived-input.json").write_text(json.dumps({"source_dimensions": dimensions,
            "target_dimensions": [cfg["image_width"], cfg["image_height"]], "intrinsics_scale": [sx, sy],
            "files": derived}, indent=2) + "\n")
        checkpoints = {}
        for weight in semantic["weights"]:
            path = root / ".cache/semantic-weights" / weight["local"]
            if sha(path) != weight["sha256"]:
                raise ValueError("Weight hash mismatch")
            checkpoints["sam" if weight["local"].startswith("sam/") else "clip"] = str(path)
        record["weights"] = semantic["weights"]
        work = output / "author-code"
        shutil.copytree(source, work, ignore=shutil.ignore_patterns(".git", "__pycache__", "media"))
        clip_path = work / "hovsg/utils/clip_utils.py"
        original = clip_path.read_text()
        old = "img_feats = clip_model.encode_image(imgs_in.cuda()).float()"
        if original.count(old) != 1:
            raise ValueError("Unexpected CLIP batch implementation")
        replacement = ("img_feats = torch.cat([clip_model.encode_image(batch.cuda()).float() "
                       f"for batch in imgs_in.split({cfg['clip_batch_size']})], dim=0)")
        patched = original.replace(old, replacement)
        clip_path.write_text(patched)
        (output / "compatibility.patch").write_text("".join(difflib.unified_diff(
            original.splitlines(keepends=True), patched.splitlines(keepends=True),
            fromfile="author/hovsg/utils/clip_utils.py", tofile="isolated/hovsg/utils/clip_utils.py")))
        sys.path.insert(0, str(work))
        os.environ["MPLBACKEND"] = "Agg"
        import hovsg.graph.graph as graph_module
        native_extract = graph_module.extract_feats_per_pixel
        frame_log = []
        observations = output / "observations"
        observations.mkdir()

        def observed_extract(*args, **kwargs):
            result = native_extract(*args, **kwargs)
            features, mask_features, masks, global_features = result
            index = len(frame_log)
            np.savez_compressed(observations / f"{index:06d}.npz",
                masks=np.asarray([m["segmentation"] for m in masks], dtype=bool),
                mask_features=mask_features.numpy(), global_features=global_features,
                source_index=expected[index])
            frame_log.append({"observation": index, "source_index": expected[index], "masks": len(masks)})
            (output / "frame_observations.json").write_text(json.dumps(frame_log, indent=2) + "\n")
            return result

        graph_module.extract_feats_per_pixel = observed_extract
        config = OmegaConf.load(work / cfg["author_config"])
        config.main.dataset_path = str(input_root / cfg["scene"])
        config.main.save_path = str(output / "map")
        config.models.clip.checkpoint = checkpoints["clip"]
        config.models.sam.checkpoint = checkpoints["sam"]
        config.models.sam.points_per_batch = cfg["sam_points_per_batch"]
        config.pipeline.skip_frames = cfg["skip_frames"]
        OmegaConf.save(config, output / "effective-config.yaml")
        with (output / "mapping.log").open("w") as log, contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
            graph = graph_module.Graph(config)
            torch.cuda.reset_peak_memory_stats()
            graph.create_feature_map()
            if len(frame_log) != len(expected) or not len(graph.mask_pcds):
                raise ValueError("Native map is incomplete")
            import open3d as o3d
            import open_clip
            o3d.io.write_point_cloud(str(output / "map.ply"), graph.full_pcd)
            objects = output / "objects"
            objects.mkdir()
            centers = []
            for i, cloud in enumerate(graph.mask_pcds):
                o3d.io.write_point_cloud(str(objects / f"{i:04d}.ply"), cloud)
                centers.append(np.asarray(cloud.points).mean(axis=0).tolist())
            features = np.asarray(graph.mask_feats).reshape(len(graph.mask_feats), -1)
            np.save(output / "segment_features.npy", features)
            tokenizer = open_clip.get_tokenizer("ViT-H-14")
            with torch.no_grad():
                text_features = graph.clip_model.encode_text(tokenizer(cfg["queries"]).cuda()).float()
                text_features = torch.nn.functional.normalize(text_features, dim=-1).cpu().numpy()
            normalized = features / np.maximum(np.linalg.norm(features, axis=1, keepdims=True), 1e-12)
            scores = text_features @ normalized.T
            queries = [{"query": query, "top_objects": [{"object_index": int(i),
                       "cosine_similarity": float(score[i]), "center_world_m": centers[i]}
                       for i in np.argsort(score)[::-1][:3]]} for query, score in zip(cfg["queries"], scores)]
        summary = {"scope": cfg["scope"], "observations": len(frame_log), "objects": len(centers),
                   "reference_points": len(graph.full_pcd.points), "queries": queries,
                   "query_correctness_evaluated": False, "paper_semantic_metrics_evaluated": False,
                   "gpu_peak_allocated_bytes": torch.cuda.max_memory_allocated(),
                   "coordinate_frame": "Supplied Replica camera-to-world; no SLAM estimate"}
        (output / "summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n")
        record.update(status="executed", exit_code=0, summary=summary,
                      gpu={"name": torch.cuda.get_device_name(0), "torch": torch.__version__, "cuda": torch.version.cuda})
    except Exception as error:
        record.update(status="failed", error=str(error), traceback=traceback.format_exc(), exit_code=1)
    finally:
        for path in sorted(output.rglob("*")):
            if not path.is_file() or path.name == "record.json" or "author-code" in path.parts or "input" in path.parts:
                continue
            name = path.relative_to(output).as_posix()
            local = path.suffix in (".ply", ".npy", ".npz")
            record["artifacts"][name] = {"sha256": sha(path), "bytes": path.stat().st_size,
                                       "availability": "local_only" if local else "portable"}
        record["finished_at"] = timestamp()
        save()
    print(f"HOV-SG: {record['status']} -> {output / 'record.json'}", flush=True)
    return int(record["status"] != "executed")


if __name__ == "__main__":
    raise SystemExit(main())
