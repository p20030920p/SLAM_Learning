"""Score native FAST-LIO outputs, freeze maps, and prepare separate GICP B."""

from pathlib import Path
import hashlib
import json
import sys

import numpy as np
import open3d as o3d
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation

from score_hypothesis_maps import representative, closest

ROOT = Path(__file__).resolve().parents[3]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def matrix(p, q):
    t = np.eye(4)
    t[:3, :3] = Rotation.from_quat(q).as_matrix()
    t[:3, 3] = p
    return t


def evaluate(run, output):
    assert not (output / "score.json").exists(), "Do not overwrite completed scores"
    output.mkdir(parents=True, exist_ok=True)
    record = json.loads((run / "metrics.json").read_text())
    start, end = record["recording_interval_sim_s"]
    truth = [json.loads(line) for line in (run / "truth.jsonl").read_text().splitlines()]
    tt = np.array([r["stamp_s"] for r in truth])
    positions = np.array([r["xyz"] for r in truth])
    quats = np.array([r["xyzw"] for r in truth])
    archive = np.load(run / "mapping-clouds.npz")
    mesh_path = (
        ROOT / "results/reference/map-hypotheses-20261015/static/map-quality/evaluation-static-mesh.ply"
    )
    mesh = o3d.io.read_triangle_mesh(str(mesh_path))
    # Include the actual ground for this full-cloud experiment; never hide drift
    # by dropping estimates outside a world-height band.
    ground = o3d.geometry.TriangleMesh.create_box(30.0, 30.0, 0.001)
    ground.translate([-15.0, -15.0, -0.001])
    mesh += ground
    scene = o3d.t.geometry.RaycastingScene()
    scene.add_triangles(o3d.t.geometry.TriangleMesh.from_legacy(mesh))
    references = []
    for i, pose in enumerate(archive["poses"]):
        p = archive[f"scan_{i:04d}"]
        p = p[np.isfinite(p).all(axis=1)]
        p = p @ pose[:3, :3].T + pose[:3, 3]
        distance = np.linalg.norm(p - closest(scene, p), axis=1)
        references.append(p[distance < 0.02])
    reference = representative(np.concatenate(references))
    np.save(output / "observed-static-reference.npy", reference)
    snapshots = {n: np.load(run / f"fastlio-{n}-clouds.npz") for n in ("deskew", "no_deskew")}
    common = set(snapshots["deskew"].files) & set(snapshots["no_deskew"].files)
    common = sorted(k for k in common if float(k[2:]) <= end)
    assert len(common) > 10
    methods = {}
    for name in snapshots:
        rows = [json.loads(line) for line in (run / f"fastlio-{name}.jsonl").read_text().splitlines()]
        first = rows[0]
        idx = np.argmin(np.abs(tt - first["t"]))
        assert abs(tt[idx] - first["t"]) < 0.05
        # One supplied initial pose anchors the coordinate frame; no trajectory fit.
        anchor = matrix(positions[idx], quats[idx]) @ np.linalg.inv(matrix(first["p"], first["q"]))
        points = np.concatenate([snapshots[name][k] for k in common])
        points = representative(points[np.isfinite(points).all(axis=1)])
        points = points @ anchor[:3, :3].T + anchor[:3, 3]
        points = points.astype(np.float32)
        points = representative(points)
        dest = output / name
        dest.mkdir(exist_ok=True)
        np.save(dest / "points.npy", points)
        header = f"# .PCD v0.7\nVERSION 0.7\nFIELDS x y z\nSIZE 4 4 4\nTYPE F F F\nCOUNT 1 1 1\nWIDTH {len(points)}\nHEIGHT 1\nVIEWPOINT 0 0 0 1 0 0 0\nPOINTS {len(points)}\nDATA binary\n".encode()
        (dest / "map-3d.pcd").write_bytes(header + points.astype("<f4").tobytes())
        # Occupancy is only a map-server/readiness display, not GICP input.
        res = 0.05
        origin = np.array([-2.0, -9.0])
        image = np.full((500, 350), 205, np.uint8)
        cells = np.floor((points[:, :2] - origin) / res).astype(int)
        valid = (cells[:, 0] >= 0) & (cells[:, 0] < 350) & (cells[:, 1] >= 0) & (cells[:, 1] < 500)
        cells = cells[valid]
        image[cells[:, 1], cells[:, 0]] = 0
        (dest / "map.pgm").write_bytes(b"P5\n350 500\n255\n" + np.flipud(image).tobytes())
        (dest / "map.yaml").write_text(
            "image: map.pgm\nmode: trinary\nresolution: 0.05\norigin: [-2, -9, 0]\nnegate: 0\noccupied_thresh: 0.65\nfree_thresh: 0.196\n"
        )
        distance = np.linalg.norm(points - closest(scene, points), axis=1)
        coverage = cKDTree(points).query(reference)[0]
        errors = []
        for row in rows:
            if not start + 5 <= row["t"] <= end:
                continue
            i = np.argmin(abs(tt - row["t"]))
            if abs(tt[i] - row["t"]) > 0.05:
                continue
            est = anchor @ matrix(row["p"], row["q"])
            truth_t = matrix(positions[i], quats[i])
            errors.append(
                [
                    row["t"],
                    np.linalg.norm(est[:3, 3] - truth_t[:3, 3]),
                    np.rad2deg(Rotation.from_matrix(truth_t[:3, :3].T @ est[:3, :3]).magnitude()),
                ]
            )
        e = np.array(errors)
        phases = {}
        for phase, a, b in [
            ("stationary", 0, 7),
            ("slow_turn", 7, 15),
            ("fast_turn", 15, 31),
            ("translation", 31, 39),
            ("stop", 39, 45),
        ]:
            p = e[(e[:, 0] >= start + a) & (e[:, 0] < start + b)]
            phases[phase] = {
                "samples": len(p),
                "xyz_rmse_m": float(np.sqrt(np.mean(p[:, 1] ** 2))) if len(p) else None,
                "rotation_rmse_deg": float(np.sqrt(np.mean(p[:, 2] ** 2))) if len(p) else None,
            }
        np.savetxt(
            dest / "odometry-errors.csv",
            e,
            delimiter=",",
            header="stamp_s,xyz_error_m,rotation_error_deg",
            comments="",
        )
        methods[name] = {
            "map_voxels": len(points),
            "surface_rmse_m": float(np.sqrt(np.mean(distance**2))),
            "surface_p95_m": float(np.percentile(distance, 95)),
            "observed_static_coverage_5cm": float(np.mean(coverage < 0.05)),
            "xyz_rmse_m": float(np.sqrt(np.mean(e[:, 1] ** 2))),
            "rotation_rmse_deg": float(np.sqrt(np.mean(e[:, 2] ** 2))),
            "native_pose_samples": len(e),
            "phases": phases,
            "initial_anchor": anchor.tolist(),
            "initial_anchor_stamp_s": first["t"],
        }
    report = {
        "schema_version": 1,
        "kind": "fastlio_point_compensation_ablation_score",
        "status": "executed",
        "exit_code": 0,
        "scope": "Supplied one initial pose per instance; no trajectory alignment; all common-time finite native registered clouds accumulated including initialization, 5cm voxels, rendered ground included; no estimated-height cropping. This freezes registered-scan accumulation, not a native ikd-Tree export. Independent localization is separate.",
        "source_run": str(run),
        "common_cloud_snapshots": len(common),
        "reference_voxels": len(reference),
        "methods": methods,
        "input_hashes": {
            str(p): sha(p)
            for p in [
                run / "truth.jsonl",
                run / "mapping-clouds.npz",
                run / "fastlio.yaml",
                mesh_path,
                *run.glob("fastlio-*.jsonl"),
                *run.glob("fastlio-*-clouds.npz"),
            ]
        },
    }
    (output / "score.json").write_text(json.dumps(report, indent=2) + "\n")
    marker = ROOT / ".cache/presentation/fastlio-maps-latest.json"
    marker.write_text(json.dumps({"path": str(output.resolve())}) + "\n")
    print(json.dumps(methods, indent=2))


if __name__ == "__main__":
    evaluate(Path(sys.argv[1]), Path(sys.argv[2]))
