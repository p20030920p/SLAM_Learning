"""Small, disclosed SE(2) hypothesis probes, not a reproduction of a new paper.

Both lidar arms estimate a ground robot's x/y/yaw. The 3D arm uses XYZ surface
residuals while keeping z/roll/pitch fixed. This module has no ROS or truth I/O.
"""
from __future__ import annotations

import numpy as np
from scipy.spatial import cKDTree


PARAMETERS = {
    "map_voxel_m": .06, "scan_voxel_m": .08, "scan_period_s": .3,
    "maximum_points_per_sensor": 850, "normal_neighbors": 12,
    "maximum_iterations": 12, "plain_correspondence_m": 1.0,
    "guard_correspondence_m": .5, "huber_m": .08,
    "weak_eigenvalue_ratio": .02, "odom_regularizer": .003,
    "search_translation_radius_m": 2.0, "search_translation_step_m": .4,
    "search_yaw_radius_deg": 30, "search_yaw_step_deg": 10,
    "search_period_s": 3.0, "search_min_score": .65,
    "search_distinct_margin": .025, "search_confirmations": 2,
    "search_consistency_translation_m": .25, "search_consistency_yaw_deg": 8,
    "search_trigger": "unconfirmed startup, rank<3, median residual>0.08m, or inlier fraction<0.6",
}


def wrap(angle):
    return np.arctan2(np.sin(angle), np.cos(angle))


def transform(points, pose):
    result = np.array(points, dtype=float, copy=True)
    c, s = np.cos(pose[2]), np.sin(pose[2])
    result[:, :2] = points[:, :2] @ np.array([[c, s], [-s, c]]) + pose[:2]
    return result


def compose(first, second):
    xy = transform(np.array([[second[0], second[1], 0.]]), first)[0, :2]
    return np.array([*xy, wrap(first[2] + second[2])])


def inverse(pose):
    c, s = np.cos(pose[2]), np.sin(pose[2])
    return np.array([-c * pose[0] - s * pose[1], s * pose[0] - c * pose[1], -pose[2]])


def voxel(points, size, limit=None):
    points = np.asarray(points, dtype=float)
    points = points[np.isfinite(points).all(axis=1)]
    if not len(points):
        return points
    _, ids = np.unique(np.floor(points / size).astype(np.int64), axis=0, return_index=True)
    result = points[np.sort(ids)]
    if limit and len(result) > limit:
        result = result[np.linspace(0, len(result) - 1, limit, dtype=int)]
    return result


class SurfaceMap:
    def __init__(self, points, dimension=3):
        self.points = voxel(points, PARAMETERS["map_voxel_m"])
        self.dimension = dimension
        self.tree = cKDTree(self.points[:, :dimension])
        _, neighbors = self.tree.query(self.points[:, :dimension], k=PARAMETERS["normal_neighbors"])
        local = self.points[neighbors, :dimension]
        local -= local.mean(axis=1, keepdims=True)
        _, vectors = np.linalg.eigh(np.einsum("nki,nkj->nij", local, local))
        self.normals = np.zeros(self.points.shape)
        self.normals[:, :dimension] = vectors[:, :, 0]

    def correspondences(self, scan, pose, maximum):
        moved = transform(scan, pose)
        distance, ids = self.tree.query(moved[:, :self.dimension])
        selected = distance < maximum
        local, moved = scan[selected], moved[selected]
        normals = self.normals[ids[selected]]
        residual = np.sum(normals * (moved - self.points[ids[selected]]), axis=1)
        c, s = np.cos(pose[2]), np.sin(pose[2])
        angular_x = -s * local[:, 0] - c * local[:, 1]
        angular_y = c * local[:, 0] - s * local[:, 1]
        jacobian = np.column_stack((normals[:, 0], normals[:, 1],
                                    (normals[:, 0] * angular_x + normals[:, 1] * angular_y) / 3.0))
        return jacobian, residual, float(selected.mean())

    def likelihood(self, scan, poses):
        scan = scan[::max(1, len(scan) // 140)]
        c, s = np.cos(poses[:, 2]), np.sin(poses[:, 2])
        points = np.broadcast_to(scan, (len(poses), *scan.shape)).copy()
        points[:, :, 0] = c[:, None] * scan[:, 0] - s[:, None] * scan[:, 1] + poses[:, 0, None]
        points[:, :, 1] = s[:, None] * scan[:, 0] + c[:, None] * scan[:, 1] + poses[:, 1, None]
        distance, _ = self.tree.query(points[:, :, :self.dimension].reshape(-1, self.dimension))
        return np.exp(-.5 * (distance.reshape(len(poses), -1) / .12) ** 2).mean(axis=1)


def fit(groups, predicted, *, guarded, iterations=None):
    pose = np.array(predicted, dtype=float, copy=True)
    info = {"rank": 0, "inlier_fraction": 0., "median_residual_m": None, "fallback": True}
    for _ in range(iterations or PARAMETERS["maximum_iterations"]):
        hessian, gradient, ratios, residuals = np.zeros((3, 3)), np.zeros(3), [], []
        for surface, scan in groups:
            if len(scan) < 12:
                continue
            jacobian, residual, ratio = surface.correspondences(scan, pose, .5 if guarded else 1.0)
            ratios.append(ratio)
            if len(residual) < 12:
                continue
            weights = np.minimum(1., .08 / np.maximum(np.abs(residual), 1e-9)) if guarded else np.ones(len(residual))
            hessian += (jacobian.T * weights) @ jacobian / len(residual)
            gradient += jacobian.T @ (weights * residual) / len(residual)
            residuals.extend(np.abs(residual).tolist())
        if not residuals:
            break
        values, vectors = np.linalg.eigh(hessian)
        observable = values > max(values[-1] * (.02 if guarded else 1e-8), 1e-8)
        if guarded:
            offset = pose - predicted
            offset[2] = wrap(offset[2]) * 3
            gradient += .003 * offset
        step = -(vectors[:, observable] @ ((vectors[:, observable].T @ gradient) /
                                           (values[observable] + (.003 if guarded else 1e-8))))
        step[2] /= 3.0
        scale = max(np.linalg.norm(step[:2]) / .25, abs(step[2]) / .12, 1.)
        pose += step / scale
        pose[2] = wrap(pose[2])
        info = {"rank": int(observable.sum()), "inlier_fraction": float(np.mean(ratios)),
                "median_residual_m": float(np.median(residuals)), "fallback": False,
                "eigenvalues": values.tolist()}
        if np.linalg.norm(step) < .0003:
            break
    return pose, info


def search_candidates(groups, centre):
    translations = np.arange(-2., 2.01, .4)
    angles = np.radians(np.arange(-30., 30.01, 10.))
    offsets = np.stack(np.meshgrid(translations, translations, angles, indexing="ij"), axis=-1).reshape(-1, 3)
    candidates = centre + offsets
    scores = np.mean([surface.likelihood(scan, candidates) for surface, scan in groups if len(scan) >= 12], axis=0)
    ranked = np.argsort(-scores)
    refined = []
    attempts = 0
    for index in ranked:
        seed = candidates[index]
        if any(np.linalg.norm(seed[:2] - prior[:2]) < .5 and abs(wrap(seed[2] - prior[2])) < .2 for prior, _ in refined):
            continue
        attempts += 1
        solution, _ = fit(groups, seed, guarded=True, iterations=8)
        score = float(np.mean([surface.likelihood(scan, solution[None])[0] for surface, scan in groups if len(scan) >= 12]))
        if not any(np.linalg.norm(solution[:2] - prior[:2]) < .35 and abs(wrap(solution[2] - prior[2])) < .15 for prior, _ in refined):
            refined.append((solution, score))
        if len(refined) >= 4 or attempts >= 12:
            break
        if len(refined) == 0 and scores[index] < .2:
            break
    refined.sort(key=lambda item: -item[1])
    if not refined:
        return centre.copy(), {"accepted_geometry": False, "best_score": 0., "margin": 0.}
    best, score = refined[0]
    margin = score - refined[1][1] if len(refined) > 1 else 0.
    return best, {"accepted_geometry": bool(score >= .65 and margin >= .025),
                  "best_score": score, "margin": margin, "distinct_candidates": len(refined)}


class Probe:
    def __init__(self, initial, *, guarded, depth, recovery):
        self.pose = np.array(initial, dtype=float)
        self.guarded, self.depth, self.recovery = guarded, depth, recovery
        self.previous_odom = None
        self.last_search = -1e9
        self.candidate_alignment = None
        self.confirmations = 0

    def update(self, stamp, odom, lidar_group, depth_group=None):
        groups = [lidar_group] + ([depth_group] if self.depth and depth_group is not None else [])
        if self.previous_odom is not None:
            self.pose = compose(self.pose, compose(inverse(self.previous_odom), odom))
        self.previous_odom = odom.copy()
        self.pose, info = fit(groups, self.pose, guarded=self.guarded)
        info.update({"used_depth": len(groups) > 1, "relocalized": False, "search": None})
        uncertain = (self.confirmations < 2 or info["rank"] < 3 or info["inlier_fraction"] < .6
                     or (info["median_residual_m"] is not None and info["median_residual_m"] > .08))
        if self.recovery and uncertain and stamp - self.last_search >= 3:
            self.last_search = stamp
            candidate, search = search_candidates(groups, self.pose)
            alignment = compose(candidate, inverse(odom))
            consistent = (self.candidate_alignment is not None
                          and np.linalg.norm(alignment[:2] - self.candidate_alignment[:2]) < .25
                          and abs(wrap(alignment[2] - self.candidate_alignment[2])) < np.radians(8))
            self.confirmations = self.confirmations + 1 if search["accepted_geometry"] and consistent else int(search["accepted_geometry"])
            self.candidate_alignment = alignment
            if self.confirmations >= 2:
                self.pose = candidate
                info["relocalized"] = True
            search["confirmations"] = self.confirmations
            info["search"] = search
        return self.pose.copy(), info
