"""Execute the author classifier with recorded Python and small-map boundary fixes."""

from __future__ import annotations

import difflib
import hashlib
import json
import shutil
import subprocess
import sys
import time

import numpy as np


def run_beautymap(scans, poses, output, upstream, parameters):
    from slam_physical.storage import read_pcd, write_pcd

    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=upstream, text=True).strip()
    status = subprocess.check_output(
        ["git", "status", "--porcelain", "--untracked-files=no"], cwd=upstream, text=True
    )
    if commit != "98bce4a97db96ddd0d5342e31425c7679f58ba2e" or status.strip():
        raise ValueError("Expected the clean pinned author checkout")
    output.mkdir(parents=True, exist_ok=False)
    work = output / "author-code"
    shutil.copytree(upstream, work, ignore=shutil.ignore_patterns(".git", "__pycache__", "data", "assets"))
    patches = []
    reader = work / "utils/pcdpy3.py"
    original = reader.read_text()
    changed = original.replace(
        "metadata[key] = map(int, value.split())", "metadata[key] = list(map(int, value.split()))"
    )
    changed = changed.replace(
        "metadata[key] = map(float, value.split())", "metadata[key] = list(map(float, value.split()))"
    )
    if changed != original:
        reader.write_text(changed)
        patches.extend(
            difflib.unified_diff(
                original.splitlines(True),
                changed.splitlines(True),
                fromfile="a/utils/pcdpy3.py",
                tofile="b/utils/pcdpy3.py",
            )
        )
    entry = work / "main.py"
    original = entry.read_text()
    anchor = 'save_pcd(f"{data_dir}/beautymap_output.pcd", Mpts.original_points[points_index2Retain])'
    if original.count(anchor) != 1 or original.count("    Mpts.calculate_matrix_order()\n") != 1:
        raise ValueError("Unexpected author code")
    changed = original.replace(
        anchor, 'np.save(f"{data_dir}/retained_indices.npy", points_index2Retain)\n    ' + anchor
    )
    changed = changed.replace(
        "    Mpts.calculate_matrix_order()\n",
        "    # Reindex working XY cells into an empty border; original points stay unchanged.\n"
        "    border_cells = int(np.ceil(dis_range / xy_resolution))\n"
        "    border_shift = np.array([border_cells * xy_resolution, border_cells * xy_resolution, 0.0])\n"
        "    Mpts.non_negtive_points = Mpts.non_negtive_points.astype(float) + border_shift\n"
        "    Mpts.non_negtive_center = Mpts.non_negtive_center.astype(float) + border_shift\n"
        "    Mpts.calculate_matrix_order()\n"
        "    Mpts.matrix_order += 2 * border_cells\n"
        "    Mpts.minz_matrix = np.full((Mpts.matrix_order, Mpts.matrix_order), float('inf'))\n",
    )
    query_anchor = "        Qpts.calculate_query_matrix_start_id()\n"
    if changed.count(query_anchor) != 1:
        raise ValueError("Unexpected author query indexing")
    changed = changed.replace(
        query_anchor,
        "        Qpts.non_negtive_points = Qpts.non_negtive_points.astype(float) + border_shift\n"
        "        Qpts.non_negtive_center = Qpts.non_negtive_center.astype(float) + border_shift\n"
        + query_anchor,
    )
    entry.write_text(changed)
    patches.extend(
        difflib.unified_diff(
            original.splitlines(True), changed.splitlines(True), fromfile="a/main.py", tofile="b/main.py"
        )
    )
    patch = output / "compatibility.patch"
    patch.write_text("".join(patches))
    data = output / "input"
    (data / "pcd").mkdir(parents=True)
    clouds = []
    for index, (scan, pose) in enumerate(zip(scans, poses)):
        points = scan @ pose[:3, :3].T + pose[:3, 3]
        clouds.append(points)
        write_pcd(data / "pcd" / f"{index:06d}.pcd", points, pose[:3, 3])
    raw = np.concatenate(clouds)
    write_pcd(data / "raw_map.pcd", raw)
    command = [sys.executable, "-u", str(entry), "--data_dir", str(data)]
    for key, value in parameters.items():
        command.extend(["--" + key, str(value)])
    print("NATIVE BEAUTYMAP COMMAND: " + " ".join(command), flush=True)
    started = time.perf_counter()
    with (output / "native.log").open("w") as log:
        process = subprocess.Popen(
            command, cwd=work, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )
        for line in process.stdout:
            print(line, end="", flush=True)
            log.write(line)
        code = process.wait()
    record = {
        "commit": commit,
        "command": command,
        "exit_code": code,
        "seconds": time.perf_counter() - started,
        "frames": len(scans),
        "parameters": parameters,
        "raw_input_sha256": hashlib.sha256((data / "raw_map.pcd").read_bytes()).hexdigest(),
        "compatibility_patch_sha256": hashlib.sha256(patch.read_bytes()).hexdigest(),
        "boundary_fix": "reindex working XY cells by an integer query-width border; empty bitmap border on all sides, min-z unknown remains infinity; original world points unchanged",
        "scope": "platform adaptation; not an unmodified original-paper metric reproduction",
    }
    (output / "record.json").write_text(json.dumps(record, indent=2) + "\n")
    if code:
        raise RuntimeError("Native BeautyMap failed: " + str(output / "native.log"))
    kept = np.load(data / "retained_indices.npy", allow_pickle=False)
    if len(np.unique(kept)) != len(kept) or np.any(kept < 0) or np.any(kept >= len(raw)):
        raise ValueError("Invalid native retained indices")
    cloud = read_pcd(data / "beautymap_output.pcd")
    if cloud.shape != raw[kept].shape or not np.allclose(
        cloud, raw.astype(np.float32)[kept], atol=2e-5, rtol=0
    ):
        raise ValueError("Native retained indices do not identify the output points")
    mask = np.zeros(len(raw), dtype=bool)
    mask[kept] = True
    np.save(output / "keep_mask.npy", mask)
    return mask, record
