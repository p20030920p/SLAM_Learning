"""Thin adapters to author implementations; run only in an isolated worker cwd."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np

from slam_learning.core.pcd import read_pcd


def dufomap_run(sequence: Path, output: Path, parameters: dict, frames: int) -> dict:
    from dufomap import dufomap

    paths = sorted((sequence / "pcd").glob("*.pcd"))
    if frames:
        paths = paths[:frames]
    mapper = dufomap(parameters["resolution"], parameters["d_s"], parameters["d_p"],
                     num_threads=parameters["threads"])
    accumulated = []
    for i, path in enumerate(paths):
        cloud = read_pcd(path)
        points = cloud.xyz()
        if not np.isfinite(points).all():
            raise ValueError(f"Nonfinite coordinates in {path}")
        ranges = np.linalg.norm(points - np.asarray(cloud.viewpoint[:3]), axis=1)
        mask = (ranges > parameters["min_range"]) & (ranges < parameters["max_range"])
        mapper.run(points[mask], cloud.viewpoint, cloud_transform=False)
        # Author demo accumulates ALL input points, including those excluded from integration.
        accumulated.append(points)
        if (i + 1) % 20 == 0 or i == len(paths) - 1:
            print(f"DUFOMap frame {i + 1}/{len(paths)}", flush=True)
    mapper.oncePropagateCluster(if_propagate=True, if_cluster=False)
    mapper.outputMap(np.concatenate(accumulated), voxel_map=False)
    produced = Path.cwd() / "dufomap_output.pcd"
    if not produced.is_file():
        raise RuntimeError("Author binding produced no dufomap_output.pcd")
    produced.replace(output)
    return {"frames": len(paths), "compatibility_patch": None,
            "integration_filter": "0.2 < range < 50 m, per current author demo"}


def beautymap_run(sequence: Path, output: Path, upstream: Path, parameters: dict, frames: int) -> dict:
    # Leave pinned checkout untouched; patch only a per-run copy and record the diff.
    work = output.parent / "author-code"
    shutil.copytree(upstream, work, ignore=shutil.ignore_patterns(".git", "__pycache__", "data", "assets"))
    source = work / "utils/pcdpy3.py"
    text = source.read_text(encoding="utf-8")
    changes = {
        "metadata[key] = map(int, value.split())": "metadata[key] = list(map(int, value.split()))",
        "metadata[key] = map(float, value.split())": "metadata[key] = list(map(float, value.split()))",
    }
    for before, after in changes.items():
        if text.count(before) != 1:
            raise RuntimeError(f"Upstream changed; compatibility patch requires exactly one {before}")
        text = text.replace(before, after)
    source.write_text(text, encoding="utf-8")
    dtype_changes = {}
    for relative in ("main.py", "lib/bee_tree.py"):
        code = work / relative
        original = code.read_text(encoding="utf-8")
        # NumPy 1.x uses a 32-bit C long for dtype=int on Windows. Author bitmasks
        # contain 2**32-1. Explicit int64 preserves the Linux representation.
        count = original.count("dtype=int")
        code.write_text(original.replace("dtype=int", "dtype=np.int64"), encoding="utf-8")
        dtype_changes[relative] = {"replacement": "dtype=int -> dtype=np.int64", "count": count}
    (output.parent / "compatibility.patch").write_text(
        "\n".join(f"- {before}\n+ {after}" for before, after in changes.items())
        + "\n" + json.dumps(dtype_changes, indent=2) + "\n", encoding="utf-8")
    # Avoid GT labels reaching the algorithm: convert GT geometry to unlabeled XYZ raw_map.
    staged = output.parent / "input"
    staged.mkdir()
    from slam_learning.core.pcd import write_pcd
    write_pcd(staged / "raw_map.pcd", read_pcd(sequence / "gt_cloud.pcd").xyz())
    (staged / "pcd").mkdir()
    paths = sorted((sequence / "pcd").glob("*.pcd"))
    if frames:
        paths = paths[:frames]
    for path in paths:
        # Scans also contain annotation-bearing intensity; remove it physically.
        # Preserve the world coordinates and VIEWPOINT required by author code.
        cloud = read_pcd(path)
        write_pcd(staged / "pcd" / path.name, cloud.xyz(), viewpoint=cloud.viewpoint)
    command = [sys.executable, str(work / "main.py"), "--data_dir", str(staged),
               *[arg for k, v in parameters.items() for arg in (f"--{k}", str(v))]]
    subprocess.run(command, cwd=work, check=True)
    produced = staged / "beautymap_output.pcd"
    if not produced.is_file():
        raise RuntimeError("Author script produced no beautymap_output.pcd")
    produced.replace(output)
    return {"frames": len(paths), "compatibility_patch": {"iterator": changes, "bitmask_width": dtype_changes},
            "author_command": command,
            "algorithm_input": "Only XYZ and VIEWPOINT in both map/scans; all intensity annotations stripped"}


def worker(root: Path, method: str, output_dir: Path, frames: int) -> None:
    specification = json.loads((root / "configs/methods.json").read_text(encoding="utf-8"))[method]
    sequence = root / ".cache/datasets/00"
    output = output_dir / "cleaned.pcd"
    if method == "dufomap":
        details = dufomap_run(sequence, output, specification["parameters"], frames)
    else:
        details = beautymap_run(sequence, output, root / ".cache/upstream/beautymap",
                                specification["parameters"], frames)
    from slam_learning.core.provenance import write_json
    write_json(output_dir / "worker.json", details)
