"""Keep compact numeric inputs so map scores can be checked without local MCAPs."""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import numpy as np
import open3d as o3d
from scipy.spatial import cKDTree

from score_hypothesis_maps import closest, representative, sha


def package(folder):
    verified = {}
    for name in ("static", "dynamic", "corridor"):
        output = folder / name / "map-quality"
        report = json.loads((output / "record.json").read_text())
        maps, run = Path(report["maps"]), Path(report["mapping_run"])
        mesh = o3d.io.read_triangle_mesh(str(output / "evaluation-static-mesh.ply"))
        scene = o3d.t.geometry.RaycastingScene(nthreads=2)
        scene.add_triangles(o3d.t.geometry.TriangleMesh.from_legacy(mesh))
        processing = json.loads((maps / "record.json").read_text())
        archived = np.load(run / "mapping-clouds.npz", allow_pickle=False)
        raw = np.load(maps / "raw/points.npy", allow_pickle=False)
        valid = np.concatenate([np.linalg.norm(archived[f"scan_{i:04d}"], axis=1) >= .45
                                for i in processing["selected_scan_ids"]])
        valid &= (raw[:, 2] >= .12) & (raw[:, 2] <= 2.2)
        reference = np.load(output / "observed-static-reference.npy")
        label_source = maps / "point-labels.npy"
        if label_source.exists():
            labels = np.load(label_source)
            for part in ("point-label-scores.json", "point-label-inputs.npz"):
                shutil.copyfile(maps / part, output / part)
            for part in ("object-geometry.json", "object-scene.pbtxt", "object-truth.jsonl"):
                shutil.copyfile(run / part, output / part)
        else:
            static = valid & (np.linalg.norm(raw - closest(scene, raw), axis=1) <= .02)
            labels = np.where(static, 0, -1).astype(np.int8)
        values = {"reference_points": reference, "source_classification": labels}
        for method in ("raw", "dufomap", "beautymap"):
            source = maps / method / "points.npy"
            assert sha(source) == report["methods"][method]["map_sha256"]
            points = np.load(source, allow_pickle=False)
            _, ids = cKDTree(raw).query(points, workers=2)
            sampled = representative(points[valid[ids]])
            distances = np.linalg.norm(sampled - closest(scene, sampled), axis=1)
            covered = cKDTree(sampled).query(reference, workers=2)[0]
            keep = cKDTree(points).query(raw, workers=2)[0] < 2e-5
            recomputed = {
                "surface_rmse_m": float(np.sqrt(np.mean(distances ** 2))),
                "surface_precision_5cm": float((distances <= .05).mean()),
                "observed_static_coverage_5cm": float((covered <= .05).mean()),
                "static_retention": float(keep[labels == 0].mean()),
                "dynamic_removal": float((~keep[labels == 1]).mean()) if (labels == 1).any() else None,
            }
            for key, value in recomputed.items():
                saved = report["methods"][method][key]
                assert (value is None and saved is None) or abs(value - saved) < 1e-8, (name, method, key)
            values[method + "_surface_samples"] = sampled
            values[method + "_source_retained"] = keep
        target = output / "geometry-and-retention-inputs.npz"
        np.savez_compressed(target, **values)
        shutil.copyfile(maps / "record.json", output / "native-processing.json")
        verified[name] = {"all_reported_metrics_recomputed": True,
                          "inputs_sha256": sha(target), "bytes": target.stat().st_size}
    (folder / "map-score-verification.json").write_text(json.dumps(verified, indent=2) + "\n")
    print(json.dumps(verified, indent=2), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    package(parser.parse_args().folder)
