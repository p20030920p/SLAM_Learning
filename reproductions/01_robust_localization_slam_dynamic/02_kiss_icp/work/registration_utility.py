#!/usr/bin/env python3
"""Downstream localizability: can a robot still register a new scan into this map?

Why this file exists
--------------------
Every cleaning method in this folder chain (01-03 … 01-06) ends its plan with the
same unchecked box: *"hand the cleaned map to 01-02 and get a registration
failure rate"*. The task book asks for it as H1' (§6, 并行实验):

    do the methods rank the same way by map-quality metrics (SA/DA/AA, PR/RR/F1)
    as they do by *whether the cleaned map is still usable for localization*?

Without this measurement, "F1 = 0.95" is a statement about points, not about
robots, and the whole D line has no answer to its own question.

What is measured
----------------
For each candidate map M and each KITTI-00 frame k:

  1. query = frame k's scan, in world coordinates, voxel-downsampled to 0.2 m
     (identical for every map - the query is never method-specific);
  2. M is cropped to a 40 m box around the sensor, and its normals are estimated;
  3. the query is displaced by a fixed, seeded perturbation (a wrong initial
     guess, as an AMCL prior or a drifted odometry would give);
  4. point-to-plane ICP tries to put the query back into M;
  5. success = final pose error < (0.20 m, 2.0°) AND inlier ratio ≥ 0.30.

The per-map failure rate is the number H1' needs. `--voxel-map` re-voxelises
every map to the same resolution first, so that a method which submits a sparse
map (ERASOR voxelises at 0.1-0.2 m, DUFOMap does not) is not penalised merely
for being sparse - both variants are reported.

Why ICP and not KISS-ICP
------------------------
KISS-ICP is **odometry**: it builds its own map from the incoming stream and has
no "localize into a prior map" mode, so it cannot consume a cleaned map at all.
The primitive that *does* consume a prior map is scan-to-map registration, which
is what this script runs (Open3D's ICP, the same primitive inside AMCL-lite
localizers). 01-02 keeps its own role - it is the folder that owns "downstream
localization" in this chain - but the localizer here is registration, and that
substitution is stated rather than hidden.

Honest limitations (recorded as findings, not concealed)
-------------------------------------------------------
* **Self-registration**: the maps were built from these same 141 frames, so each
  query's own points are in the map. This measures whether cleaning left the
  structure registrable at all; it is not a revisit in a new session. Every
  method is treated identically, so the *ranking* comparison still holds, but
  the absolute failure rates are optimistic.
* The query scan still contains whatever was moving in frame k, while the map has
  had dynamic points removed. That is realistic (a new observation arrives before
  any cleaning) and again identical across maps.

Usage:
    work/registration_utility.py --seq-dir <bench>/data/raw/00 \
        --out results/registration_utility.json [--frames 141] [--levels 2]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time

import numpy as np
import open3d as o3d

# The maps. Each entry names where the map comes from, because "removert" alone
# is ambiguous in this repo: the official repo and the benchmark's port produce
# measurably different maps (01-04), and this experiment can see that.
MAP_SOURCES = {
    "uncleaned": ("<built here: all 141 world-frame scans accumulated>", "naive accumulation"),
    "erasor_official": ("03_erasor/results/erasor_official/00_result.pcd", "official LimHyungTae/ERASOR"),
    "erasor_port": ("01_dynamicmap_benchmark/data/raw/00/erasor_output.pcd", "DynamicMap_Benchmark port"),
    "removert_official": ("04_removert/results/removert_kitti00/map_static/"
                          "StaticMapScansideMapGlobal.pcd", "official irapkaist/removert"),
    "removert_port": ("01_dynamicmap_benchmark/data/raw/00/removert_output.pcd", "DynamicMap_Benchmark port"),
    "dufomap": ("01_dynamicmap_benchmark/data/raw/00/dufomap_output_paper_default_dp1.pcd", "official PyPI dufomap, d_p=1"),
    "beautymap": ("01_dynamicmap_benchmark/data/raw/00/beautymap_output.pcd", "official MKJia/BeautyMap"),
}

# Maps that exist on disk but cannot enter this experiment, and why. This is a
# measurement, not a caveat: 03_erasor/README.md records that the official
# ERASOR output is expressed in the *official* bag's frame (SuMa poses over the
# 72-frame snippet), and that this frame differs from the benchmark's world
# frame by ~1.6 m median nearest-neighbour distance. A query scan in the
# benchmark frame therefore cannot be registered into it at all - which is
# exactly what the first pilot showed (100 % failure at every perturbation
# level, while the port's map of the same method passed).
EXCLUDED = {
    "erasor_official": "different coordinate frame (official SuMa/bag frame, not the "
                       "benchmark world frame); see 03_erasor/README.md",
}

# query perturbation levels, mild -> hard. A single level can saturate (0 % for
# everything, or 100 % for everything) and then the ranking carries no signal,
# so the sweep spans an order of magnitude of initial-guess error.
LEVELS = [
    {"m": 0.50, "deg": 5.0},
    {"m": 1.00, "deg": 8.0},
    {"m": 2.00, "deg": 12.0},
    {"m": 3.00, "deg": 20.0},
]

MARK = b"DATA binary\n"


def read_world_pcd(path):
    """Benchmark PCD: binary x y z [intensity], VIEWPOINT = sensor pose in world."""
    with open(path, "rb") as fh:
        raw = fh.read()
    i = raw.find(MARK)
    if i < 0:
        pts = np.asarray(o3d.io.read_point_cloud(path).points, dtype=np.float64)
        return pts, np.array([0, 0, 0, 1, 0, 0, 0], dtype=np.float64)
    head = raw[:i].decode("ascii", "replace")
    n = int(re.search(r"POINTS (\d+)", head).group(1))
    fields = len(re.search(r"FIELDS (.*)", head).group(1).split())
    vp = [float(x) for x in re.search(r"VIEWPOINT (.*)", head).group(1).split()]
    body = raw[i + len(MARK):]
    pts = np.frombuffer(body[: n * 4 * fields], dtype=np.float32).reshape(-1, fields)[:, :3]
    return pts.astype(np.float64), np.array(vp, dtype=np.float64)


def quat_to_R(qw, qx, qy, qz):
    n = np.sqrt(qw * qw + qx * qx + qy * qy + qz * qz)
    qw, qx, qy, qz = qw / n, qx / n, qy / n, qz / n
    return np.array([
        [1 - 2 * (qy * qy + qz * qz), 2 * (qx * qy - qz * qw), 2 * (qx * qz + qy * qw)],
        [2 * (qx * qy + qz * qw), 1 - 2 * (qx * qx + qz * qz), 2 * (qy * qz - qx * qw)],
        [2 * (qx * qz - qy * qw), 2 * (qy * qz + qx * qw), 1 - 2 * (qx * qx + qy * qy)],
    ])


def rot_z(deg):
    a = np.deg2rad(deg)
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])


def make_pcd(points):
    p = o3d.geometry.PointCloud()
    p.points = o3d.utility.Vector3dVector(points)
    return p


def load_maps(repro_dir, seq_dir, voxel_map, cache_dir):
    """Every map, normalised to one resolution, with normals estimated once.

    Two decisions here are about cost, and both are stated because they change
    what the numbers mean:

    * every map is voxel-downsampled to `voxel_map` (default 0.2 m) before use.
      Without that, this experiment would partly measure *density*: ERASOR
      submits a map voxelised at 0.1-0.2 m while DUFOMap submits a dense one, and
      a denser map is easier to register into for reasons that have nothing to do
      with how well it was cleaned. Normalising makes it a comparison of
      *structure*, which is the question H1' asks.
    * normals are estimated per map once (not per crop), which is the difference
      between minutes and hours. Cropping preserves them.
    """
    maps = {}
    for name, (rel, _) in MAP_SOURCES.items():
        if name == "uncleaned":
            continue
        if name in EXCLUDED:
            print(f"  [skip] {name}: {EXCLUDED[name]}")
            continue
        path = os.path.join(repro_dir, rel)
        if not os.path.exists(path):
            print(f"  [skip] {name}: {rel} not found")
            continue
        pcd = o3d.io.read_point_cloud(path)
        raw_n = len(pcd.points)
        pcd = pcd.voxel_down_sample(voxel_map)
        pcd.estimate_normals(o3d.geometry.KDTreeSearchParamHybrid(radius=1.0, max_nn=30))
        print(f"  [map ] {name:20s} {raw_n:>10,} -> {len(pcd.points):>9,} pts "
              f"(@{voxel_map} m, normals ready)")
        maps[name] = pcd

    cache = os.path.join(cache_dir, "uncleaned_map.ply")
    if os.path.exists(cache):
        maps["uncleaned"] = o3d.io.read_point_cloud(cache)
    else:
        frames = sorted(f for f in os.listdir(os.path.join(seq_dir, "pcd")) if f.endswith(".pcd"))
        allpts = []
        for f in frames:
            pts, _ = read_world_pcd(os.path.join(seq_dir, "pcd", f))
            allpts.append(pts.astype(np.float32))
        naive = make_pcd(np.concatenate(allpts).astype(np.float64))
        os.makedirs(cache_dir, exist_ok=True)
        naive = naive.voxel_down_sample(voxel_map)
        o3d.io.write_point_cloud(cache, naive)
        maps["uncleaned"] = naive
    maps["uncleaned"].estimate_normals(
        o3d.geometry.KDTreeSearchParamHybrid(radius=1.0, max_nn=30))
    print(f"  [map ] {'uncleaned':20s} {'-':>10s} -> {len(maps['uncleaned'].points):>9,} pts "
          f"(@{voxel_map} m, normals ready)")
    return maps


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seq-dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--frames", type=int, default=141, help="use the first N frames as queries")
    ap.add_argument("--levels", type=int, default=3, help="how many perturbation levels")
    ap.add_argument("--crop-radius", type=float, default=40.0)
    ap.add_argument("--voxel-query", type=float, default=0.2)
    ap.add_argument("--voxel-map", type=float, default=0.2,
                    help="resolution every map is normalised to before use")
    ap.add_argument("--max-corr", type=float, default=1.0)
    ap.add_argument("--max-iter", type=int, default=30)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    repro_dir = os.path.normpath(os.path.join(here, "..", ".."))

    print("[utility] loading maps")
    maps = load_maps(repro_dir, args.seq_dir, args.voxel_map, os.path.join(here, "generated"))

    frames = sorted(f for f in os.listdir(os.path.join(args.seq_dir, "pcd")) if f.endswith(".pcd"))
    frames = frames[: args.frames]
    print(f"[utility] {len(frames)} query frames, {len(maps)} maps, "
          f"{min(args.levels, len(LEVELS))} perturbation levels")

    levels = LEVELS[: args.levels]
    results = {name: {f"L{i}": {"n": 0, "fail": 0, "errs": [], "fits": [], "rmses": []}
                      for i in range(len(levels))} for name in maps}
    t0 = time.time()

    # pre-crop each map around each sensor position once, per frame
    for fi, fname in enumerate(frames):
        pts_world, vp = read_world_pcd(os.path.join(args.seq_dir, "pcd", fname))
        t = vp[:3]
        query_full = make_pcd(pts_world).voxel_down_sample(args.voxel_query)
        src_pts = np.asarray(query_full.points)
        # keep only what the cropped map could possibly explain, so `fitness`
        # measures registration rather than "the map stops 40 m from the sensor"
        keep = np.linalg.norm(src_pts - t, axis=1) <= args.crop_radius
        src_pts = src_pts[keep]

        box = o3d.geometry.AxisAlignedBoundingBox(
            t - args.crop_radius, t + args.crop_radius)
        rng = np.random.default_rng(args.seed * 100003 + fi)

        for li, lv in enumerate(levels):
            # seeded perturbation about the sensor origin: wrong initial guess
            psi = rng.uniform(-lv["deg"], lv["deg"])
            d = rng.normal(size=3)
            d = d / (np.linalg.norm(d) + 1e-9) * rng.uniform(0.5, 1.0) * lv["m"]
            R = rot_z(psi)
            src_l = (src_pts - t) @ R.T + t + d
            src = make_pcd(src_l)
            T_pert = np.eye(4)
            T_pert[:3, :3] = R
            T_pert[:3, 3] = t + d - R @ t          # world transform applied to the query
            # ICP must find inv(T_pert); the residual is therefore T_icp @ T_pert,
            # which is identity when the registration is exact. (Composing with
            # inv(T_pert) instead inflates the error by roughly |(I-R)t| - at a
            # 4 deg yaw and a 15 m lever arm that alone is about 1 m, and it
            # swamped the signal in the first pilot.)

            for name, m in maps.items():
                # crop keeps the precomputed normals; per-frame cost is O(N) numpy
                crop = m.crop(box)
                if len(crop.points) < 200:
                    results[name][f"L{li}"]["n"] += 1
                    results[name][f"L{li}"]["fail"] += 1
                    continue
                try:
                    reg = o3d.pipelines.registration.registration_icp(
                        src, crop, args.max_corr, np.eye(4),
                        o3d.pipelines.registration.TransformationEstimationPointToPlane(),
                        o3d.pipelines.registration.ICPConvergenceCriteria(
                            max_iteration=args.max_iter))
                except Exception as exc:                       # noqa: BLE001
                    print(f"    [warn] {name} {fname} L{li}: {exc}")
                    results[name][f"L{li}"]["n"] += 1
                    results[name][f"L{li}"]["fail"] += 1
                    continue

                T_err = reg.transformation @ T_pert
                err_t = float(np.linalg.norm(T_err[:3, 3]))
                cosang = (np.trace(T_err[:3, :3]) - 1.0) / 2.0
                err_r = float(np.degrees(np.arccos(np.clip(cosang, -1.0, 1.0))))
                ok = err_t < 0.20 and err_r < 2.0 and reg.fitness >= 0.30

                r = results[name][f"L{li}"]
                r["n"] += 1
                r["fail"] += 0 if ok else 1
                r["errs"].append(err_t)
                r["fits"].append(float(reg.fitness))
                r["rmses"].append(float(reg.inlier_rmse))

        if (fi + 1) % 10 == 0 or fi + 1 == len(frames):
            el = time.time() - t0
            print(f"  [{fi + 1}/{len(frames)}] {el:.0f}s elapsed "
                  f"({el / (fi + 1):.2f}s/frame)")

    def summarise(r):
        errs = np.array(r["errs"]) if r["errs"] else np.array([np.nan])
        fits = np.array(r["fits"]) if r["fits"] else np.array([np.nan])
        return {
            "frames": r["n"],
            "failures": r["fail"],
            "failure_rate_pct": round(100.0 * r["fail"] / max(r["n"], 1), 4),
            "err_trans_median_m": round(float(np.nanmedian(errs)), 4),
            "err_trans_p90_m": round(float(np.nanpercentile(errs, 90)), 4),
            "fitness_median": round(float(np.nanmedian(fits)), 4),
        }

    out = {
        "protocol": {
            "query": "frame scan, world frame, voxel 0.2 m; identical for every map",
            "registration": "Open3D point-to-plane ICP, max_corr_dist "
                            f"{args.max_corr} m, {args.max_iter} iterations",
            "crop_radius_m": args.crop_radius,
            "map_voxel_m": args.voxel_map or None,
            "perturbation_levels": levels,
            "success": "err_trans < 0.20 m AND err_rot < 2.0 deg AND fitness >= 0.30",
            "limitation": "self-registration: the maps were built from these frames, so "
                          "absolute rates are optimistic; all maps are treated identically, "
                          "so the ranking comparison is the valid part",
            "frames": len(frames),
        },
        "maps": {name: {lv: summarise(results[name][lv]) for lv in results[name]}
                 for name in maps},
    }
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, ensure_ascii=False)

    print("\n[utility] failure rate by map (lower is better)")
    hdr = f"{'map':22s} " + " ".join(f"L{i}({lv['m']}m,{lv['deg']}deg)" for i, lv in enumerate(levels))
    print("  " + hdr)
    for name in maps:
        row = " ".join(f"{out['maps'][name][f'L{i}']['failure_rate_pct']:>14.1f}%"
                       for i in range(len(levels)))
        print(f"  {name:22s} {row}")
    print(f"\n[utility] wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
