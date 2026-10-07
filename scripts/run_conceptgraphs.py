"""Run author SAM/CLIP segmentation and object mapping in a separate Linux env."""
from __future__ import annotations

import difflib
import gzip
import hashlib
import importlib.metadata
import json
import os
import pickle
import shutil
import subprocess
import sys
import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for data in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(data)
    return h.hexdigest()


def timestamp():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def main():
    root = Path(__file__).resolve().parents[1]
    output = root / "results/runs" / f"conceptgraphs-{uuid.uuid4().hex[:12]}"
    output.mkdir(parents=True)
    config = json.loads((root / "configs/semantic.json").read_text())
    record = {"schema_version": 1, "kind": "semantic_frontend_baseline", "method": "ConceptGraphs",
              "status": "running", "scope": "Replica room0 40-observation subset", "started_at": timestamp(),
              "configuration": config, "artifacts": {}, "commands": [], "exit_code": None,
              "repository": {"commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
                             "dirty": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=root, text=True).strip())},
              "script_sha256": sha(__file__), "config_sha256": sha(root / "configs/semantic.json")}
    record_path = output / "record.json"

    def save():
        record_path.write_text(json.dumps(record, indent=2, allow_nan=False) + "\n")

    def execute(command, name, env):
        record["commands"].append(command)
        save()
        with (output / name).open("w") as log:
            subprocess.run(command, cwd=work / "conceptgraph", env=env, stdout=log,
                           stderr=subprocess.STDOUT, check=True, timeout=7200)

    save()
    try:
        import numpy as np
        import torch
        if not torch.cuda.is_available():
            raise RuntimeError("Semantic frontend requires the separately checked CUDA environment")
        record["gpu"] = {"torch": torch.__version__, "cuda_runtime": torch.version.cuda,
                          "name": torch.cuda.get_device_name(0), "memory_bytes": torch.cuda.get_device_properties(0).total_memory}
        freeze = "\n".join(sorted(f"{d.metadata['Name']}=={d.version}" for d in importlib.metadata.distributions())) + "\n"
        (output / "environment.txt").write_text(freeze)
        for name, spec in config["upstreams"].items():
            checkout = root / ".cache/upstream" / name
            commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=checkout, text=True).strip()
            dirty = subprocess.check_output(["git", "status", "--porcelain"], cwd=checkout, text=True).strip()
            if commit != spec["commit"] or dirty:
                raise ValueError(f"{name} does not match clean pinned source")
        data_root = root / ".cache/semantic-data/Replica"
        manifest_path = data_root / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        indexes = config["source_frame_indexes"]
        expected = list(range(indexes["start"], indexes["stop_exclusive"], indexes["stride"]))
        if manifest["source_frame_indexes"] != expected:
            raise ValueError("Source RGB-D frame indexes differ from configuration")
        for item in manifest["files"]:
            path = (data_root / item["path"]).resolve()
            if not path.is_relative_to(data_root.resolve()) or sha(path) != item["sha256"]:
                raise ValueError("Dataset file differs from manifest")
        shutil.copy2(manifest_path, output / "dataset-manifest.json")
        source_data_root = data_root
        data_root = output / "input/Replica"
        for item in manifest["files"]:
            target = data_root / item["path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_data_root / item["path"], target)
        for weight in config["weights"]:
            path = root / ".cache/semantic-weights" / weight["local"]
            if sha(path) != weight["sha256"]:
                raise ValueError(f"Checkpoint hash mismatch: {weight['local']}")
        work = output / "author-code"
        shutil.copytree(root / ".cache/upstream/conceptgraphs", work,
                        ignore=shutil.ignore_patterns(".git", "__pycache__", "assets"))
        script = work / "conceptgraph/scripts/generate_gsa_results.py"
        original = script.read_text()
        text = original.replace('matplotlib.use("TkAgg")', 'matplotlib.use("Agg")')
        text = text.replace("    from groundingdino.util.inference import Model", "    Model = None  # Unused in class_set=none")
        start = text.index("try:\n    from ram.models import ram")
        stop = text.index("# Disable torch gradient computation", start)
        text = text[:start] + "# RAM/tagging are unused in the fixed class_set=none run.\n\n" + text[stop:]
        start = text.index("    grounding_dino_model = Model(")
        stop = text.index("    ### Initialize the SAM model", start)
        text = text[:start] + "    grounding_dino_model = None  # Class-agnostic run only\n\n" + text[stop:]
        before = '"ViT-H-14", "laion2b_s32b_b79k"'
        if text.count(before) != 1:
            raise ValueError("Unexpected upstream CLIP construction")
        text = text.replace(before, '"ViT-H-14", os.environ["SLAM_STUDY_CLIP_CHECKPOINT"]')
        if text.count("points_per_batch=144,") != 1:
            raise ValueError("Unexpected upstream SAM point batching")
        text = text.replace("points_per_batch=144,", 'points_per_batch=int(os.environ["SLAM_STUDY_SAM_BATCH"]),')
        script.write_text(text)
        (output / "compatibility.patch").write_text("".join(difflib.unified_diff(
            original.splitlines(keepends=True), text.splitlines(keepends=True),
            fromfile="original/generate_gsa_results.py", tofile="runtime/generate_gsa_results.py")))
        env = dict(os.environ, PYTHONPATH=str(work), MPLBACKEND="Agg",
                   GSA_PATH=str(root / ".cache/semantic-weights/sam/checkpoints"),
                   SLAM_STUDY_SAM_BATCH=str(config["segmentation"]["points_per_batch"]),
                   SLAM_STUDY_CLIP_CHECKPOINT=str(root / ".cache/semantic-weights/clip/open_clip_pytorch_model.bin"))
        dataset_config = work / "conceptgraph/dataset/dataconfigs/replica/replica.yaml"
        command = [sys.executable, str(script), "--dataset_root", str(data_root), "--dataset_config", str(dataset_config),
                   "--scene_id", config["scene"], "--class_set", "none", "--stride", "1"]
        execute(command, "segmentation.log", env)
        command = [sys.executable, str(work / "conceptgraph/slam/cfslam_pipeline_batch.py"),
                   f"dataset_root={data_root}", f"dataset_config={dataset_config}", f"scene_id={config['scene']}",
                   *[f"{k}={str(v).lower() if isinstance(v, bool) else v}" for k, v in config["mapping_overrides"].items()]]
        execute(command, "mapping.log", env)
        sys.path.insert(0, str(work))
        import open_clip
        from conceptgraph.slam.slam_classes import MapObjectList
        files = sorted((data_root / config["scene"] / "pcd_saves").glob("*replica_subset_baseline*_post.pkl.gz"))
        if len(files) != 1:
            raise ValueError("Expected one fresh postprocessed object map")
        map_path = files[0]
        with gzip.open(map_path, "rb") as f:
            saved = pickle.load(f)
        objects = MapObjectList()
        objects.load_serializable(saved["objects"])
        if not len(objects):
            raise ValueError("Author map contains no objects")
        model, _, _ = open_clip.create_model_and_transforms(
            "ViT-H-14", env["SLAM_STUDY_CLIP_CHECKPOINT"], device="cuda")
        model.eval()
        tokenizer = open_clip.get_tokenizer("ViT-H-14")
        with torch.no_grad():
            feature = model.encode_text(tokenizer(config["queries"]).to("cuda")).float()
            feature = torch.nn.functional.normalize(feature, dim=-1)
            objects_ft = torch.nn.functional.normalize(objects.get_stacked_values_torch("clip_ft").float(), dim=-1)
            similarity = (feature.cpu() @ objects_ft.cpu().T).numpy()
        results = []
        # cfslam_pipeline_batch uses dataset.poses[idx], not normalized __getitem__ poses.
        world_from_map = np.eye(4)
        for query, scores in zip(config["queries"], similarity):
            ids = np.argsort(scores)[::-1][:3]
            results.append({"query": query, "top_objects": [{"object_index": int(i), "cosine_similarity": float(scores[i]),
                "center_map_m": np.asarray(objects[i]["bbox"].get_center()).tolist(),
                "center_world_m": (world_from_map[:3, :3] @ np.asarray(objects[i]["bbox"].get_center()) + world_from_map[:3, 3]).tolist(),
                "num_detections": int(objects[i]["num_detections"])} for i in ids]})
        summary = {"scope": config["scope"], "objects": len(objects), "queries": results,
                   "map_sha256": sha(map_path), "coordinate_frame": "Replica world; batch mapper uses absolute dataset.poses, not normalized __getitem__ poses",
                   "map_frame_to_replica_world": world_from_map.tolist(),
                   "query_correctness_evaluated": False, "paper_semantic_metrics_evaluated": False}
        (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
        shutil.copy2(map_path, output / "objects.pkl.gz")
        record.update(status="executed", exit_code=0, summary=summary,
                      gpu_peak_note="Subprocess GPU peak is not measured by parent; no performance claim")
    except Exception as e:
        record.update(status="failed", error=str(e), traceback=traceback.format_exc())
        if isinstance(e, subprocess.CalledProcessError):
            record["exit_code"] = e.returncode
    finally:
        record["finished_at"] = timestamp()
        for name in ("environment.txt", "dataset-manifest.json", "compatibility.patch", "segmentation.log",
                     "mapping.log", "summary.json", "objects.pkl.gz"):
            path = output / name
            if path.is_file():
                record["artifacts"][name] = {"sha256": sha(path), "bytes": path.stat().st_size,
                                           "availability": "local_only" if name == "objects.pkl.gz" else "portable"}
        save()
    print(f"ConceptGraphs: {record['status']} -> {record_path}", flush=True)
    return int(record["status"] != "executed")


if __name__ == "__main__":
    raise SystemExit(main())
