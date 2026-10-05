#!/usr/bin/env python3
"""Map-alignment metrics exactly as the ELite paper defines them.

ELite (ICRA 2025) §IV-A, p.5:

    "we establish point correspondences between two point clouds using the nearest
     neighbor search and get the inlier set using a distance threshold σ_inlier
     (set to 0.5 m). AC measures the ratio of inlier pairs, RMSE is their root
     mean squared distance, and CD is the bidirectional sum of average inlier
     distance."

Table I then reports, for LT-ParkingLot, ICP 0.962 / 0.117 / 0.194,
LT-mapper 0.968 / 0.121 / 0.175 and ELite 0.969 / 0.090 / 0.133.

Implemented here:

    for every point of A, the distance to its nearest neighbour in B   -> d_AB
    for every point of B, the distance to its nearest neighbour in A   -> d_BA
    inliers(A->B) = { d_AB <= sigma }
    AC  = |inliers(A->B)| / |A|                (ratio of inlier pairs)
    RMSE = sqrt(mean(d_AB^2 over inliers(A->B)))
    CD  = mean(d_AB over inliers(A->B)) + mean(d_BA over inliers(B->A))

The paper does not say *which* two clouds it feeds in, so the choice is made
explicit on the command line and echoed into the JSON: here it is the two
sessions' maps after ELite has aligned and cleaned them.

Usage:
    python3 evaluate_alignment.py --a <session01 map.pcd> --b <session02 map.pcd> \
        --out ../results/elite_alignment.json
"""
import argparse
import json
import os
import sys

import numpy as np
import open3d as o3d


def nn_distances(src: np.ndarray, tgt: np.ndarray) -> np.ndarray:
    """Nearest-neighbour distance from every point of `src` into `tgt`.

    Open3D's `compute_point_cloud_distance` is the same query as a per-point
    `KDTreeFlann.search_knn_vector_3d` loop, but vectorised in C++ - the Python
    loop took tens of minutes on a multi-million-point session map, this takes
    seconds. The numbers are identical (both report the distance to the single
    nearest neighbour), so the metric stays the paper's.
    """
    src_pcd = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(src))
    tgt_pcd = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(tgt))
    return np.asarray(src_pcd.compute_point_cloud_distance(tgt_pcd))


def metrics(a_pts: np.ndarray, b_pts: np.ndarray, sigma: float):
    d_ab = nn_distances(a_pts, b_pts)
    d_ba = nn_distances(b_pts, a_pts)
    in_ab = d_ab[d_ab <= sigma]
    in_ba = d_ba[d_ba <= sigma]
    return {
        "sigma_inlier_m": sigma,
        "points_a": int(len(a_pts)),
        "points_b": int(len(b_pts)),
        "inlier_ratio_a_to_b": round(float(len(in_ab) / len(a_pts)), 6),
        "inlier_ratio_b_to_a": round(float(len(in_ba) / len(b_pts)), 6),
        "AC": round(float(len(in_ab) / len(a_pts)), 4),
        "RMSE_m": round(float(np.sqrt(np.mean(in_ab ** 2))), 4) if len(in_ab) else None,
        "CD_m": round(float(np.mean(in_ab) + np.mean(in_ba)), 4)
                if len(in_ab) and len(in_ba) else None,
        "mean_nn_a_to_b_m": round(float(np.mean(d_ab)), 4),
        "mean_nn_b_to_a_m": round(float(np.mean(d_ba)), 4),
    }


def load(path, voxel=None):
    pcd = o3d.io.read_point_cloud(path)
    if voxel:
        pcd = pcd.voxel_down_sample(voxel)
    return np.asarray(pcd.points)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--a", required=True, help="first session map")
    ap.add_argument("--b", required=True, help="second session map (aligned into A)")
    ap.add_argument("--sigma", type=float, default=0.5, help="inlier threshold in m")
    ap.add_argument("--voxel", type=float, default=0.0,
                    help="optional voxel downsample before measuring (0 = raw)")
    ap.add_argument("--label-a", default=None)
    ap.add_argument("--label-b", default=None)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    a_pts = load(args.a, args.voxel or None)
    b_pts = load(args.b, args.voxel or None)
    result = metrics(a_pts, b_pts, args.sigma)
    result.update({
        "a": os.path.basename(args.a),
        "b": os.path.basename(args.b),
        "label_a": args.label_a or args.a,
        "label_b": args.label_b or args.b,
        "voxel_downsample_m": args.voxel,
        "definition": "ELite paper §IV-A p.5: NN correspondences, inliers at 0.5 m, "
                      "AC = inlier ratio, RMSE = root mean squared inlier distance, "
                      "CD = bidirectional sum of average inlier distance",
        "paper_table": {"LT-ParkingLot": {"ICP": [0.962, 0.117, 0.194],
                                          "LT-mapper": [0.968, 0.121, 0.175],
                                          "ELite (Ours)": [0.969, 0.090, 0.133]}},
    })
    print(f"A: {result['a']}  ({result['points_a']} points)")
    print(f"B: {result['b']}  ({result['points_b']} points)")
    print(f"AC   = {result['AC']}    (paper, LT-ParkingLot: 0.969)")
    print(f"RMSE = {result['RMSE_m']} m  (paper: 0.090)")
    print(f"CD   = {result['CD_m']} m  (paper: 0.133)")
    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(result, fh, indent=2, ensure_ascii=False)
        print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
