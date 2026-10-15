"""Read-only snapshots emitted during author execution, consumed by a live RViz bridge."""
from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path

import numpy as np


def emit(method, frame, phase, **arrays):
    destination = os.environ.get("SLAM_AUTHOR_LIVE")
    if not destination:
        return
    folder = Path(destination)
    folder.mkdir(parents=True, exist_ok=True)
    serial = len(list(folder.glob("frame-*.npz")))
    name = f"frame-{serial:05d}.npz"
    temporary = folder / "pending.npz"
    np.savez_compressed(temporary, **arrays)
    temporary.replace(folder / name)
    meta = {"method": method, "frame": int(frame), "serial": serial, "phase": phase,
            "wall_unix": time.time(), "monotonic_s": time.monotonic(), "file": name,
            "sha256": hashlib.sha256((folder / name).read_bytes()).hexdigest(),
            "counts": {key: len(value) for key, value in arrays.items() if np.asarray(value).ndim}}
    with (folder / "events.jsonl").open("a") as log:
        log.write(json.dumps(meta)+"\n")
    temp = folder / "latest.tmp"
    temp.write_text(json.dumps(meta))
    temp.replace(folder / "latest.json")


def dufomap_snapshot(mapper, frame, current, accumulated, final=False):
    if not os.environ.get("SLAM_AUTHOR_LIVE") or (frame % 3 and not final):
        return
    # Only display is thinned. Classification queries the current author octree.
    cloud = np.concatenate([points[np.linspace(0, len(points)-1, min(240, len(points)), dtype=int)]
                            for points in accumulated])
    labels = mapper.segment(cloud, np.eye(4), cloud_transform=False)
    scan = current[np.linspace(0, len(current)-1, min(5000, len(current)), dtype=int)]
    emit("dufomap", frame, "after final propagation" if final else "current octree before final propagation",
         map=cloud[labels == 0], removed=cloud[labels != 0], input=scan)


def beauty_snapshot(mapper, trigger, ground, current, frame):
    if not os.environ.get("SLAM_AUTHOR_LIVE") or (frame % 7 and frame != 140):
        return
    removed = []
    # Exact upstream extraction from the current cumulative triggers; no state writes.
    for i, j in zip(*np.where(trigger != 0)):
        for z in mapper.binTo3id(trigger[i, j]):
            removed.extend(mapper.root_matrix[i, j].children[z].pts_id.tolist())
        for child in range(len(ground)):
            for z in mapper.binTo3id(ground[child, i, j]):
                removed.extend(mapper.root_matrix[i, j].children[child].children[z].pts_id.tolist())
    points = mapper.original_points
    ids = np.linspace(0, len(points)-1, min(22000, len(points)), dtype=int)
    keep = ~np.isin(ids, removed)
    scan = current[np.linspace(0, len(current)-1, min(5000, len(current)), dtype=int)]
    emit("beautymap", frame, "full input map available; current cumulative cleaning decisions",
         map=points[ids[keep]], removed=points[ids[~keep]], input=scan)


def ir_snapshot(frame, timestamp, particles, truth, occupancy, scans, config):
    if not os.environ.get("SLAM_AUTHOR_LIVE") or (frame % 5 and frame != 1542):
        return
    ids = np.linspace(0, len(particles)-1, min(2500, len(particles)), dtype=int)
    chosen = particles[np.argsort(particles[:, 3])[-max(1, int(.8*len(particles))):]]
    weight = chosen[:, 3]/chosen[:, 3].sum()
    pose = np.array([np.sum(chosen[:, 0]*weight), np.sum(chosen[:, 1]*weight),
                     np.arctan2(np.sum(np.sin(chosen[:, 2])*weight), np.sum(np.cos(chosen[:, 2])*weight))])
    occupied = np.column_stack(np.where(occupancy > .9)).astype(float)
    occupied -= np.asarray(occupancy.shape)/2
    occupied *= config["map_res"]
    occupied = occupied[np.linspace(0, len(occupied)-1, min(18000, len(occupied)), dtype=int)]
    emit("ir-mcl", frame, "native IR-MCL particle update", particles=particles[ids], pose=pose,
         truth=np.asarray(truth), map=np.column_stack([occupied, np.zeros(len(occupied))]),
         timestamp=np.asarray([timestamp]))
