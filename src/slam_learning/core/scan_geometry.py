"""A planar normal-coverage diagnostic; not a localization confidence estimate."""
from __future__ import annotations

import numpy as np


def normal_coverage(ranges, angle_min, angle_increment, range_min, range_max):
    values = np.asarray(ranges, dtype=float)
    angle = angle_min+np.arange(len(values))*angle_increment
    valid = np.isfinite(values) & (values > range_min) & (values < range_max-.001)
    finite = np.where(valid, values, 0.0)
    points = np.column_stack([finite*np.cos(angle), finite*np.sin(angle)])
    if len(points) < 3:
        return None
    tangent = points[2:]-points[:-2]
    length = np.linalg.norm(tangent, axis=1)
    selected = valid[:-2] & valid[1:-1] & valid[2:] & (length > 1e-5) & (length < .4)
    tangent = tangent[selected]
    length = length[selected]
    if len(tangent) < 5:
        return None
    normal = np.column_stack([-tangent[:, 1], tangent[:, 0]])/length[:, None]
    eigen = np.linalg.eigvalsh(normal.T@normal/len(normal))
    return {"normal_count": len(normal), "eigenvalues": eigen.tolist(),
            "ratio": float(eigen[0]/max(eigen[1], 1e-12)),
            "scope": "2D local scan normal Gram eigenvalue ratio; excludes max-range returns and >0.4m neighbor gaps; not a SLAM Hessian or calibrated confidence"}
