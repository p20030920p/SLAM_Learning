"""Report map cleaning separately from pose error; derive 2D support from labels.

The projected metric scores unique 5cm input cells, excluding cells containing
both static and dynamic labels. It never relabels 3D point scores as 2D accuracy.
"""

import json
from pathlib import Path
import numpy as np
from PIL import Image
import yaml
from scipy.spatial import cKDTree
import hashlib

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "results/analysis/map-quality"


def projection():
    folder = ROOT / "results/reference/robot-2d-dynamic-matched/maps"
    inputs = np.load(ROOT / "results/reference/robot-3d-map-audit/point-label-inputs.npz")
    p, labels = inputs["points"], inputs["labels"]
    settings = yaml.safe_load((folder / "raw/map.yaml").read_text())
    origin = np.array(settings["origin"][:2])
    resolution = settings["resolution"]
    valid = (p[:, 2] >= 0.12) & (p[:, 2] <= 1.2) & (labels >= 0)
    cells = np.floor((p[valid, :2] - origin) / resolution).astype(int)
    lab = labels[valid]
    static = set(map(tuple, cells[lab == 0]))
    dynamic = set(map(tuple, cells[lab == 1]))
    overlap = static & dynamic
    static = sorted(static - overlap)
    dynamic = sorted(dynamic - overlap)
    result = {}
    for method in ("raw", "dufomap", "beautymap"):
        image = np.flipud(np.array(Image.open(folder / method / "map.pgm")))
        sx, sy = np.array(static).T
        dx, dy = np.array(dynamic).T
        result[method] = {
            "static_retention": float((image[sy, sx] == 0).mean()),
            "dynamic_removal": float((image[dy, dx] != 0).mean()),
        }
    return {
        "kind": "projected_unique_cell_coverage",
        "resolution_m": resolution,
        "height_band_m": [0.12, 1.2],
        "static_cells": len(static),
        "dynamic_cells": len(dynamic),
        "excluded_overlap_cells": len(overlap),
        "scope": "Observed static/dynamic-exclusive input cells scored on actual occupied projection; includes existing one-cell map dilation; distinct from 3D point retention and online ghost removal",
        "methods": result,
    }


def quality(name, dimension, root=ROOT):
    dynamic = "dynamic" in name
    if dynamic:
        if dimension == "2d":
            return json.loads((root / "results/analysis/map-quality/projected-dynamic.json").read_text())[
                "methods"
            ]
        return json.loads((root / "results/reference/robot-3d-map-audit/record.json").read_text())[
            "configurations"
        ]["baseline"]["metrics"]
    scene = "corridor" if "corridor" in name else "static"
    p = root / f"results/analysis/map-quality/{scene}.json"
    return json.loads(p.read_text())[dimension] if p.exists() else None


def metric_text(name, dimension, method, chinese=True, root=ROOT):
    data = quality(name, dimension, root)
    if data:
        v = data[method]
        da = f"{v['dynamic_removal']*100:.2f}%" if v["dynamic_removal"] is not None else "N/A"
        suffix = ("（静态A旧图）" if chinese else " (static-A old map)") if "large-change" in name else ""
        return (
            f"动态{'格' if dimension=='2d' else '点'}删除 {da}；静态{'格' if dimension=='2d' else '点'}保留 {v['static_retention']*100:.2f}%"
            if chinese
            else f"Dynamic {'cell' if dimension=='2d' else 'point'} removal {da}; static retention {v['static_retention']*100:.2f}%"
        ) + suffix
    if "large-change" in name:
        return (
            "动态删除 N/A；变化后静态保留未测（旧图未更新）"
            if chinese
            else "Dynamic removal N/A; post-change static retention unmeasured (frozen old map)"
        )
    return (
        "动态删除 N/A（无动态目标）；静态保留未独立标注"
        if chinese
        else "Dynamic removal N/A (no moving targets); static retention not independently labelled"
    )


def static_scene(scene):
    diagnostic = json.loads((ROOT / f"results/analysis/map-2d-3d/{scene}.json").read_text())
    folder = ROOT / diagnostic["maps"].replace("\\", "/")
    processing = json.loads((folder / "record.json").read_text())
    source = folder.parent / "mapping-clouds.npz"
    archive = np.load(source)
    raw = np.load(folder / "raw/points.npy")
    masks = []
    for i in processing["selected_scan_ids"]:
        scan = archive[f"scan_{i:04d}"]
        masks.append(np.linalg.norm(scan, axis=1) >= 0.45)
    static = np.concatenate(masks)
    assert len(static) == len(raw)
    settings = yaml.safe_load((folder / "raw/map.yaml").read_text())
    selected = raw[static & (raw[:, 2] >= 0.12) & (raw[:, 2] <= 1.2)]
    cells = np.unique(
        np.floor((selected[:, :2] - settings["origin"][:2]) / settings["resolution"]).astype(int), axis=0
    )
    result = {
        "2d": {},
        "3d": {},
        "static_points": int(static.sum()),
        "static_cells": len(cells),
        "classification": "No moving scene actors; self returns within 0.45m excluded. Observed static support, not hand labels.",
        "inputs": {
            "raw_sha256": hashlib.sha256((folder / "raw/points.npy").read_bytes()).hexdigest(),
            "mapping_archive_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        },
    }
    for method in ("raw", "dufomap", "beautymap"):
        points = np.load(folder / method / "points.npy")
        keep = cKDTree(points).query(raw[static], workers=2)[0] < 2e-5
        result["3d"][method] = {"static_retention": float(keep.mean()), "dynamic_removal": None}
        image = np.flipud(np.array(Image.open(folder / method / "map.pgm")))
        result["2d"][method] = {
            "static_retention": float((image[cells[:, 1], cells[:, 0]] == 0).mean()),
            "dynamic_removal": None,
        }
    return result


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    report = projection()
    (OUT / "projected-dynamic.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    for scene in ("static", "corridor"):
        result = static_scene(scene)
        (OUT / f"{scene}.json").write_text(json.dumps(result, indent=2) + "\n")
        print(scene, result["2d"], result["3d"])
