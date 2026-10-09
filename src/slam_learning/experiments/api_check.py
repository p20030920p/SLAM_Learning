"""Separate direct-label, correspondence and native-export effects on one mapper."""
from __future__ import annotations

import json
import subprocess
import sys
import traceback
import uuid
from pathlib import Path

import numpy as np

from slam_learning.core.metrics import confusion_metrics, score_map
from slam_learning.core.pcd import read_pcd, write_pcd
from slam_learning.core.provenance import digest, environment, git_state, source_hashes, utc_now, write_json
from slam_learning.runtime.runner import execute, validate_inputs


def worker(root: Path, output: Path):
    from dufomap import dufomap
    config = json.loads((root / "configs/methods.json").read_text())["dufomap"]["parameters"]
    mapper = dufomap(config["resolution"], config["d_s"], config["d_p"], num_threads=config["threads"])
    sequence = root / ".cache/datasets/00"
    gt = read_pcd(sequence / "gt_cloud.pcd")
    clouds, poses, start = [], [], 0
    for path in sorted((sequence / "pcd").glob("*.pcd")):
        cloud = read_pcd(path)
        xyz = cloud.xyz()
        stop = start + len(xyz)
        if not np.array_equal(xyz, gt.xyz(slice(start, stop))):
            raise ValueError("Exact scan/GT identity required")
        ranges = np.linalg.norm(xyz - np.asarray(cloud.viewpoint[:3]), axis=1)
        mapper.run(xyz[(ranges > config["min_range"]) & (ranges < config["max_range"])],
                   cloud.viewpoint, cloud_transform=False)
        clouds.append(xyz)
        poses.append(cloud.viewpoint)
        start = stop
    if start != len(gt.records):
        raise ValueError("Scans do not exactly cover GT")
    mapper.oncePropagateCluster(if_propagate=True, if_cluster=False)
    prediction = np.concatenate([np.asarray(mapper.segment(xyz, pose, cloud_transform=False))
                                 for xyz, pose in zip(clouds, poses)])
    direct = confusion_metrics(gt.records["intensity"], prediction)
    all_xyz = np.concatenate(clouds)
    write_pcd(output / "segment-kept.pcd", all_xyz[prediction == 0])
    mapper.outputMap(all_xyz, voxel_map=False)
    native_path = output / "dufomap_output.pcd"
    segment_map = score_map(sequence / "gt_cloud.pcd", output / "segment-kept.pcd")
    native_map = score_map(sequence / "gt_cloud.pcd", native_path)
    write_json(output / "summary.json", {
        "frames": len(clouds), "gt_points": start, "configuration": config,
        "one_trained_mapper": True, "exact_scan_gt_identity": True,
        "direct_segment": direct, "nn_of_segment_kept_map": segment_map, "nn_of_native_output_map": native_map,
        "decomposition_pp": {
            "segment_map_nn_minus_direct": {k: segment_map[k] - direct[k] for k in ("SA", "DA", "AA", "HA")},
            "native_nn_minus_segment_map_nn": {k: native_map[k] - segment_map[k] for k in ("SA", "DA", "AA", "HA")}},
        "scope": "API/evaluation diagnostic at zero injected pose error; no paper-table or structural-failure claim",
        "binding_docstrings": {"segment": mapper.segment.__doc__, "outputMap": mapper.outputMap.__doc__}})


def run_api_check(root: Path, timeout: float = 3600) -> Path:
    if timeout <= 0:
        raise ValueError("Timeout must be positive")
    output = root / "results/runs" / f"api-check-{uuid.uuid4().hex[:12]}"
    output.mkdir(parents=True)
    record = {"schema_version": 1, "kind": "dufomap_api_diagnostic", "status": "running", "scope": "full_teaser",
              "started_at": utc_now(), "environment": environment(), "repository": git_state(root),
              "source_sha256": source_hashes(root), "artifacts": {}, "exit_code": None}
    write_json(output / "record.json", record)
    try:
        record.update(validate_inputs(root, "dufomap"))
        command = [sys.executable, "-m", "slam_learning.experiments.api_check", str(root), str(output)]
        record["command"] = command
        record["exit_code"] = execute(command, output, output / "run.log", timeout)
        record["summary"] = json.loads((output / "summary.json").read_text())
        record["status"] = "executed"
    except Exception as e:
        record.update(status="failed", error=str(e), traceback=traceback.format_exc())
        if isinstance(e, subprocess.CalledProcessError):
            record["exit_code"] = e.returncode
    finally:
        record["finished_at"] = utc_now()
        for name in ("run.log", "summary.json", "segment-kept.pcd", "dufomap_output.pcd"):
            path = output / name
            if path.is_file():
                record["artifacts"][name] = {"sha256": digest(path), "bytes": path.stat().st_size,
                                           "availability": "local_only" if name.endswith('.pcd') else "portable"}
        write_json(output / "record.json", record)
    print(f"DUFOMap API diagnostic: {record['status']} -> {output / 'record.json'}", flush=True)
    return output / "record.json"


if __name__ == "__main__":
    worker(Path(sys.argv[1]), Path(sys.argv[2]))
