"""Second-stage hypothesis: refine coarse candidates without changing H1/H2."""
import numpy as np

from slam_learning.runtime.recovery_probe import Probe, compose, fit, inverse, wrap

REFINEMENT = {"coarse_translation_step_m": .4, "fine_translation_radius_m": .3,
              "fine_translation_step_m": .1, "fine_yaw_offsets_deg": [-2, 0, 2],
              "uniqueness_pool": "all evaluated coarse/fine positions and refined modes outside 0.35m / 0.15rad",
              "unchanged": "H1/H2 residuals, motion prior, score>=0.65, distinct margin>=0.025 and two-confirmation gate"}


def likelihood(groups, poses):
    return np.mean([surface.likelihood(scan, poses) for surface, scan in groups if len(scan) >= 12], axis=0)


def candidates(groups, centre):
    translations = np.arange(-2., 2.01, .4)
    angles = np.radians(np.arange(-30., 30.01, 10.))
    offsets = np.stack(np.meshgrid(translations, translations, angles, indexing="ij"), axis=-1).reshape(-1, 3)
    poses = centre + offsets
    scores = likelihood(groups, poses)
    coarse, attempts = [], 0
    for index in np.argsort(-scores):
        seed = poses[index]
        if any(np.linalg.norm(seed[:2] - prior[:2]) < .5 and abs(wrap(seed[2] - prior[2])) < .2 for prior, _ in coarse):
            continue
        attempts += 1
        solution, _ = fit(groups, seed, guarded=True, iterations=8)
        score = float(likelihood(groups, solution[None])[0])
        if not any(np.linalg.norm(solution[:2] - prior[:2]) < .35 and abs(wrap(solution[2] - prior[2])) < .15 for prior, _ in coarse):
            coarse.append((solution, score))
        if len(coarse) >= 4 or attempts >= 12:
            break
        if not coarse and scores[index] < .2:
            break
    fine_offsets = np.stack(np.meshgrid(np.arange(-.3, .301, .1), np.arange(-.3, .301, .1),
                                        np.radians([-2., 0., 2.]), indexing="ij"), axis=-1).reshape(-1, 3)
    refined, sampled_poses, sampled_scores = [], [poses], [scores]
    for pose, _ in coarse:
        neighborhood = pose + fine_offsets
        neighborhood_scores = likelihood(groups, neighborhood)
        sampled_poses.append(neighborhood)
        sampled_scores.append(neighborhood_scores)
        seed = neighborhood[int(np.argmax(neighborhood_scores))]
        solution, _ = fit(groups, seed, guarded=True, iterations=8)
        score = float(likelihood(groups, solution[None])[0])
        overlap = next((index for index, (prior, _) in enumerate(refined)
                        if np.linalg.norm(solution[:2] - prior[:2]) < .35 and abs(wrap(solution[2] - prior[2])) < .15), None)
        if overlap is None:
            refined.append((solution, score))
        elif score > refined[overlap][1]:
            refined[overlap] = (solution, score)
    refined.sort(key=lambda item: -item[1])
    if not refined:
        return centre.copy(), {"accepted_geometry": False, "best_score": 0., "margin": 0.}
    best, score = refined[0]
    all_poses = np.concatenate([*sampled_poses, np.array([value[0] for value in refined])])
    all_scores = np.concatenate([*sampled_scores, np.array([value[1] for value in refined])])
    distinct = ((np.linalg.norm(all_poses[:, :2] - best[:2], axis=1) >= .35)
                | (np.abs(wrap(all_poses[:, 2] - best[2])) >= .15))
    margin = score - float(np.max(all_scores[distinct])) if distinct.any() else 0.
    return best, {"accepted_geometry": bool(score >= .65 and margin >= .025),
                  "best_score": score, "margin": margin, "distinct_candidates": len(refined),
                  "fine_translation_step_m": .1}


class FineProbe:
    def __init__(self, initial, *, depth):
        # Composition keeps the frozen H1/H2 prediction and local updates intact.
        self.base = Probe(initial, guarded=True, depth=depth, recovery=False)
        self.depth = depth
        self.last_search = -1e9
        self.confirmations = 0
        self.candidate_alignment = None

    def update(self, stamp, odom, lidar_group, depth_group=None):
        pose, info = self.base.update(stamp, odom, lidar_group, depth_group)
        groups = [lidar_group] + ([depth_group] if self.depth and depth_group is not None else [])
        uncertain = (self.confirmations < 2 or info["rank"] < 3 or info["inlier_fraction"] < .6
                     or (info["median_residual_m"] is not None and info["median_residual_m"] > .08))
        if uncertain and stamp - self.last_search >= 3:
            self.last_search = stamp
            candidate, search = candidates(groups, pose)
            alignment = compose(candidate, inverse(odom))
            consistent = (self.candidate_alignment is not None
                          and np.linalg.norm(alignment[:2] - self.candidate_alignment[:2]) < .25
                          and abs(wrap(alignment[2] - self.candidate_alignment[2])) < np.radians(8))
            self.confirmations = self.confirmations + 1 if search["accepted_geometry"] and consistent else int(search["accepted_geometry"])
            self.candidate_alignment = alignment
            if self.confirmations >= 2:
                self.base.pose = candidate
                pose = candidate.copy()
                info["relocalized"] = True
            search["confirmations"] = self.confirmations
            info["search"] = search
        return pose, info
