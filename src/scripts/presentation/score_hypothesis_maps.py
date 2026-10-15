"""Evaluate frozen maps against rendered static geometry, never feeding it to mapping/B."""
from __future__ import annotations

import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import open3d as o3d
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pose(values):
    x, y, z, roll, pitch, yaw = map(float, values.split())
    result = np.eye(4)
    result[:3, :3] = Rotation.from_euler("xyz", [roll, pitch, yaw]).as_matrix()
    result[:3, 3] = [x, y, z]
    return result


def mesh_from_dae(path):
    """The pinned converter emits triangle geometry with identity scene instances."""
    root = ET.parse(path).getroot()
    ns = {"c": "http://www.collada.org/2005/11/COLLADASchema"}
    unit = root.find("c:asset/c:unit", ns)
    assert root.find("c:asset/c:up_axis", ns).text == "Z_UP"
    assert float(unit.get("meter")) == 1
    for node in root.findall(".//c:visual_scene//c:node", ns):
        assert not any(node.find("c:" + tag, ns) is not None
                       for tag in ("matrix", "translate", "rotate", "scale"))
    vertices, triangles, offset = [], [], 0
    for mesh in root.findall("c:library_geometries/c:geometry/c:mesh", ns):
        sources = {item.get("id"): np.fromstring(item.find("c:float_array", ns).text, sep=" ").reshape(-1, 3)
                   for item in mesh.findall("c:source", ns)
                   if item.find("c:technique_common/c:accessor", ns).get("stride") == "3"}
        bindings = {item.get("id"): item.find("c:input[@semantic='POSITION']", ns).get("source")[1:]
                    for item in mesh.findall("c:vertices", ns)}
        for primitive in mesh.findall("c:triangles", ns):
            inputs = primitive.findall("c:input", ns)
            vertex = next(item for item in inputs if item.get("semantic") == "VERTEX")
            points = sources[bindings[vertex.get("source")[1:]]]
            stride = max(int(item.get("offset", "0")) for item in inputs) + 1
            ids = np.fromstring(primitive.find("c:p", ns).text, sep=" ", dtype=np.int64)
            ids = ids.reshape(-1, stride)[:, int(vertex.get("offset", "0"))].reshape(-1, 3)
            vertices.append(points)
            triangles.append(ids + offset)
            offset += len(points)
    assert vertices and triangles, "No rendered triangle geometry"
    return o3d.geometry.TriangleMesh(
        o3d.utility.Vector3dVector(np.concatenate(vertices)),
        o3d.utility.Vector3iVector(np.concatenate(triangles)),
    )


def static_scene(world_path, assets):
    world = ET.parse(world_path).getroot().find("world")
    mesh = o3d.geometry.TriangleMesh()
    includes = world.findall("include")
    if includes:
        assert len(includes) == 1
        include = includes[0]
        assert include.findtext("uri") == "model://competition_map_dae"
        model = ET.parse(assets / "model.sdf").getroot().find("model")
        link = model.find("link")
        visual = link.find("visual")
        assert visual.findtext("geometry/mesh/uri").endswith("competition_map_color_rules.dae")
        assert visual.findtext("geometry/mesh/scale") == "1 1 1"
        mesh = mesh_from_dae(assets / "competition_map_color_rules.dae")
        mesh.transform(pose(link.findtext("pose", "0 0 0 0 0 0")))
        mesh.transform(pose(include.findtext("pose", "0 0 0 0 0 0")))
    for model in world.findall("model"):
        if model.findtext("static") != "true":
            continue
        for link in model.findall("link"):
            for visual in link.findall("visual"):
                size = visual.findtext("geometry/box/size")
                if not size:
                    # Only the z=0 ground plane is excluded by the fixed height ROI.
                    assert visual.find("geometry/plane") is not None
                    continue
                dimensions = np.fromstring(size, sep=" ")
                box = o3d.geometry.TriangleMesh.create_box(*dimensions)
                box.translate(-dimensions / 2)
                box.transform(pose(visual.findtext("pose", "0 0 0 0 0 0")))
                box.transform(pose(link.findtext("pose", "0 0 0 0 0 0")))
                box.transform(pose(model.findtext("pose", "0 0 0 0 0 0")))
                mesh += box
    assert len(mesh.triangles)
    scene = o3d.t.geometry.RaycastingScene(nthreads=2)
    scene.add_triangles(o3d.t.geometry.TriangleMesh.from_legacy(mesh))
    return scene, mesh


def closest(scene, points):
    return scene.compute_closest_points(o3d.core.Tensor(points.astype(np.float32)), nthreads=2)["points"].numpy()


def representative(points, voxel=.05):
    _, ids = np.unique(np.floor(points / voxel).astype(np.int64), axis=0, return_index=True)
    return points[ids]


def evaluate(run, maps, assets, output):
    runtime = json.loads((run / "runtime.json").read_text())
    world_path = Path(runtime["world"])
    assert sha(world_path) == runtime["world_sha256"]
    scene, mesh = static_scene(world_path, assets)
    processing = json.loads((maps / "record.json").read_text())
    archive = np.load(run / "mapping-clouds.npz", allow_pickle=False)
    raw = np.load(maps / "raw/points.npy", allow_pickle=False)
    valid = np.concatenate([np.linalg.norm(archive[f"scan_{i:04d}"], axis=1) >= .45
                            for i in processing["selected_scan_ids"]])
    assert len(raw) == len(valid)
    valid &= (raw[:, 2] >= .12) & (raw[:, 2] <= 2.2)
    # The reference covers static surfaces actually observed by A, not hidden or whole-world surfaces.
    raw_distance = np.linalg.norm(raw - closest(scene, raw), axis=1)
    static = valid & (raw_distance <= .02)
    reference = representative(closest(scene, raw[static]))
    assert len(reference) > 100
    output.mkdir(parents=True, exist_ok=False)
    np.save(output / "observed-static-reference.npy", reference)
    o3d.io.write_triangle_mesh(str(output / "evaluation-static-mesh.ply"), mesh)
    labels_path = maps / "point-labels.npy"
    labels = np.load(labels_path) if labels_path.exists() else None
    raw_tree = cKDTree(raw)
    methods = {}
    for method in ("raw", "dufomap", "beautymap"):
        points = np.load(maps / method / "points.npy", allow_pickle=False)
        match_distance, source = raw_tree.query(points, workers=2)
        assert np.max(match_distance) < 2e-5, "Cleaner generated new coordinates; retention needs another definition"
        evaluated = representative(points[valid[source]])
        distance = np.linalg.norm(evaluated - closest(scene, evaluated), axis=1)
        coverage = cKDTree(evaluated).query(reference, workers=2)[0]
        retained = cKDTree(points).query(raw, workers=2)[0] < 2e-5
        static_labels = labels == 0 if labels is not None else static
        dynamic_labels = labels == 1 if labels is not None else np.zeros(len(raw), dtype=bool)
        methods[method] = {
            "points": len(points), "evaluated_voxels": len(evaluated),
            "surface_mean_m": float(distance.mean()),
            "surface_rmse_m": float(np.sqrt(np.mean(distance ** 2))),
            "surface_p95_m": float(np.percentile(distance, 95)),
            "surface_precision_5cm": float((distance <= .05).mean()),
            "observed_static_coverage_5cm": float((coverage <= .05).mean()),
            "static_retention": float(retained[static_labels].mean()),
            "dynamic_removal": float((~retained[dynamic_labels]).mean()) if dynamic_labels.any() else None,
            "map_sha256": sha(maps / method / "points.npy"),
        }
    report = {
        "kind": "static_mesh_distance_and_observed_surface_coverage", "scene": runtime["scene"],
        "mapping_run": str(run), "maps": str(maps), "reference_voxels": len(reference),
        "roi": {"height_m": [.12, 2.2], "sensor_distance_min_m": .45, "voxel_m": .05},
        "surface_tolerance_m": .05, "reference_static_hit_tolerance_m": .02,
        "methods": methods,
        "scope": "Exact nearest rendered static triangle distance; one retained point per 5cm voxel. Coverage of A-observed static surface reference only, not whole-world completeness. Self/ground excluded. Mapping poses supplied; no autonomous SLAM accuracy claim.",
        "truth_in_estimators": False,
        "inputs": {str(p): sha(p) for p in [world_path, run / "mapping-clouds.npz", maps / "record.json",
                   *sorted(assets.glob("*"))] if p.is_file()},
    }
    (output / "record.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"output": str(output), "methods": methods}, indent=2), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("run", "maps", "assets", "output"):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    evaluate(args.run, args.maps, args.assets, args.output)
