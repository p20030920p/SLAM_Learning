"""Project prototypes: temporal ray evidence, odometry deskew and weak-axis retention.

No external mapper, semantic labels or evaluation truth is used here. These are
experimental implementations of common geometric ideas, not novelty claims.
"""

import numpy as np
from scipy.ndimage import binary_dilation
from scipy.spatial import cKDTree


def pose2(x, y, angle):
    c, s = np.cos(angle), np.sin(angle)
    return np.array([[c, -s, x], [s, c, y], [0., 0., 1.]])


def interpolate_pose(times, poses, target):
    """Interpolate measured XY and unwrapped yaw; forbid extrapolation."""
    times, poses = np.asarray(times), np.asarray(poses)
    if target < times[0] - 1e-6 or target > times[-1] + 1e-6:
        raise ValueError("Odometry does not bracket the point timestamp")
    values = [np.interp(target, times, poses[:, i]) for i in (0, 1)]
    angle = np.interp(target, times, np.unwrap(poses[:, 2]))
    return pose2(*values, angle)


def transform(points, pose):
    return np.asarray(points) @ pose[:2, :2].T + pose[:2, 2]


def deskew(points, point_times, times, poses, end):
    """Return all sectors in the end-of-scan frame using measured odometry."""
    reference = np.linalg.inv(interpolate_pose(times, poses, end))
    result = np.empty_like(points)
    for stamp in np.unique(point_times):
        mask = point_times == stamp
        result[mask] = transform(points[mask], reference @ interpolate_pose(times, poses, stamp))
    return result


class RayEvidence:
    def __init__(self, resolution=.05, origin=(-6., -14.), shape=(600, 640)):
        self.resolution, self.origin = resolution, np.asarray(origin)
        self.hits = np.zeros(shape, np.int32)
        self.free = np.zeros(shape, np.int32)
        self.hit_bin = np.full(shape, -1, np.int32)
        self.free_bin = np.full(shape, -1, np.int32)
        self.last_support_bin = np.full(shape, -1, np.int32)
        self.clear_bins = np.zeros(shape, np.int32)
        self.clear_bin = np.full(shape, -1, np.int32)
        radius = int(np.ceil(.10 / resolution))
        yy, xx = np.mgrid[-radius:radius+1, -radius:radius+1]
        self.support_kernel = (xx * resolution) ** 2 + (yy * resolution) ** 2 <= .10 ** 2 + 1e-12

    def cells(self, points):
        cells = np.floor((points - self.origin) / self.resolution).astype(int)
        ok = (cells[:, 0] >= 0) & (cells[:, 0] < self.hits.shape[1])
        ok &= (cells[:, 1] >= 0) & (cells[:, 1] < self.hits.shape[0])
        return np.unique(cells[ok], axis=0)

    def add(self, points, sensor, stamp):
        epoch = int(stamp / .5)
        cells = self.cells(points)
        if len(cells):
            x, y = cells.T
            fresh = self.hit_bin[y, x] != epoch
            self.hits[y[fresh], x[fresh]] += 1
            self.hit_bin[y, x] = epoch
            supported = np.zeros(self.hits.shape, bool)
            supported[y, x] = True
            supported = binary_dilation(supported, structure=self.support_kernel)
            self.last_support_bin[supported] = epoch
            self.clear_bins[supported] = 0
        rays = []
        for endpoint in points[::2]:
            distance = np.linalg.norm(endpoint - sensor)
            if distance > .2:
                # Stop 15cm before the measured return, never behind an occluder.
                fractions = np.arange(.1, distance - .15, self.resolution) / distance
                rays.append(sensor + fractions[:, None] * (endpoint - sensor))
        if rays:
            cells = self.cells(np.concatenate(rays))
            x, y = cells.T
            fresh = self.free_bin[y, x] != epoch
            self.free[y[fresh], x[fresh]] += 1
            self.free_bin[y, x] = epoch
            # Positive removal evidence must follow the latest nearby hit.
            # One full bin separates a hit from a clearing vote; an unobserved
            # or seldom-observed cell is never removed just for being rare.
            cleared = (self.hits[y, x] > 0) & (epoch > self.last_support_bin[y, x] + 1)
            cleared &= self.clear_bin[y, x] != epoch
            self.clear_bins[y[cleared], x[cleared]] += 1
            self.clear_bin[y[cleared], x[cleared]] = epoch

    def mask(self, method):
        if method in ("raw", "off", "deskew"):
            return self.hits > 0
        if method == "temporal":
            return (self.hits > 0) & (self.clear_bins < 3)
        required = 5 if method in ("strict", "protected") else 3
        mask = (self.hits >= required) & (self.hits >= 1.5 * self.free)
        if method == "protected":
            candidates = np.argwhere((self.hits >= 2) & (self.free == 0))
            if len(candidates) >= 8:
                points = self.origin + (candidates[:, ::-1] + .5) * self.resolution
                tree = cKDTree(points)
                normals, ids = [], []
                for i, neighbors in enumerate(tree.query_ball_point(points, .30)):
                    if len(neighbors) < 4:
                        continue
                    local = points[neighbors]
                    eigen, vectors = np.linalg.eigh(np.cov(local.T))
                    if eigen[1] > 4 * max(eigen[0], 1e-8):
                        normals.append(vectors[:, 0])
                        ids.append(i)
                if normals:
                    normals = np.asarray(normals)
                    eigen, vectors = np.linalg.eigh(normals.T @ normals)
                    if eigen[0] < .25 * eigen[1]:
                        weak = vectors[:, 0]
                        rescue = np.asarray(ids)[np.abs(normals @ weak) > .7]
                        rc = candidates[rescue]
                        mask[rc[:, 0], rc[:, 1]] = True
        return mask

    def points(self, method):
        return self.origin + (np.argwhere(self.mask(method))[:, ::-1] + .5) * self.resolution

    def image(self, method):
        result = np.full(self.hits.shape, 205, np.uint8)
        result[self.free > 0] = 254
        result[binary_dilation(self.mask(method), iterations=1)] = 0
        return result

    def save(self, folder, method):
        folder.mkdir(parents=True, exist_ok=True)
        image = self.image(method)
        h, w = image.shape
        (folder / "map.pgm").write_bytes(f"P5\n{w} {h}\n255\n".encode() + np.flipud(image).tobytes())
        (folder / "map.yaml").write_text(
            f"image: map.pgm\nmode: trinary\nresolution: {self.resolution}\n"
            f"origin: [{self.origin[0]}, {self.origin[1]}, 0.0]\nnegate: 0\noccupied_thresh: 0.65\nfree_thresh: 0.196\n"
        )
        np.save(folder / "points.npy", self.points(method))
