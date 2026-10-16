"""Small robust SE(2) scan-to-supported-map alignment, implemented locally."""
import numpy as np
from scipy.spatial import cKDTree

from .own_mapping import transform


def refine_scan_pose(points, predicted, reference, iterations=12):
    """Trim distant/moving correspondences; never use a reference pose or labels.

    Reference points come only from the preceding temporal map. An invalid or
    poorly supported update returns the wheel-odometry prediction unchanged.
    """
    if len(points) < 30 or len(reference) < 80:
        return predicted.copy()
    tree = cKDTree(reference)
    estimate = predicted.copy()
    for _ in range(iterations):
        world = transform(points, estimate)
        distance, index = tree.query(world)
        ids = np.flatnonzero(distance < .30)
        if len(ids) < 30:
            return predicted.copy()
        ids = ids[np.argsort(distance[ids])[:max(30, int(.7 * len(ids)))]]
        source, target = world[ids], reference[index[ids]]
        weight = np.minimum(1., .05 / np.maximum(distance[ids], 1e-9))
        weight /= weight.sum()
        a, b = (source * weight[:, None]).sum(axis=0), (target * weight[:, None]).sum(axis=0)
        u, _, vt = np.linalg.svd(((source-a)*weight[:, None]).T @ (target-b))
        rotation = vt.T @ u.T
        if np.linalg.det(rotation) < 0:
            vt[-1] *= -1
            rotation = vt.T @ u.T
        delta = np.eye(3)
        delta[:2, :2], delta[:2, 2] = rotation, b - rotation @ a
        updated = delta @ estimate
        # A local correction, not unconstrained global registration.
        relative = np.linalg.inv(predicted) @ updated
        angle = np.arctan2(relative[1, 0], relative[0, 0])
        if np.linalg.norm(relative[:2, 2]) > .15 or abs(angle) > .05:
            return predicted.copy()
        estimate = updated
        if np.linalg.norm(delta[:2, 2]) < 1e-5 and abs(np.arctan2(rotation[1, 0], rotation[0, 0])) < 1e-5:
            break
    return estimate
