"""Compare downloaded inputs with released 00 data without changing either.

The rigid alignment residual below compares two supplied-pose conventions;
it is not localization ATE, and does not determine why the releases differ.
"""
import argparse
import json
import sys
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
from validate_kitti_prepared import read_pcd, sha256


def viewpoint(path):
    with path.open('rb') as source:
        while line := source.readline():
            if line.startswith(b'VIEWPOINT '):
                a = np.asarray(line.decode().split()[1:], dtype=float)
                result = np.eye(4)
                result[:3, :3] = Rotation.from_quat(a[[4, 5, 6, 3]]).as_matrix()
                result[:3, 3] = a[:3]
                return result
            if line.startswith(b'DATA '):
                break
    raise ValueError('Missing VIEWPOINT')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    runtime = args.runtime.resolve()
    sys.path.insert(0, str(runtime / 'upstream/dynamicmap/scripts/py'))
    from utils.semkitti_api import parse_calibration, parse_poses
    from utils import filterOutRange
    base = runtime / 'data/kitti-original'
    raw_path = base / 'data_odometry_velodyne/dataset/sequences/00/velodyne/004390.bin'
    label_path = base / 'data_odometry_labels/dataset/sequences/00/labels/004390.label'
    calib_path = base / 'data_odometry_calib/dataset/sequences/00/calib.txt'
    poses_path = base / 'data_odometry_labels/dataset/sequences/00/poses.txt'
    raw = np.fromfile(raw_path, dtype='<f4').reshape(-1, 4)
    labels = np.fromfile(label_path, dtype='<u4')
    calibration = parse_calibration(str(calib_path))
    poses = parse_poses(str(poses_path), calibration)
    release_paths = [runtime / f'data/00-pristine/pcd/{i:06d}.pcd' for i in range(4390, 4531)]
    header, released = read_pcd(release_paths[0])
    T = poses[4390]
    first = {'raw_points': len(raw), 'released_points': len(released),
             'current_50m_points': len(filterOutRange(raw, labels)[0]),
             'official_suma_sensor_translation_m': T[:3, 3].tolist(),
             'released_viewpoint': list(map(float, header['VIEWPOINT']))}
    if len(raw) == len(released):
        world = raw[:, :3] @ T[:3, :3].T + T[:3, 3]
        first['max_unaligned_pointwise_xyz_difference_m'] = float(np.max(np.abs(released[:, :3] - world)))
    released_poses = [viewpoint(path) for path in release_paths]
    alignment = released_poses[0] @ np.linalg.inv(poses[4390])
    translation, rotation = [], []
    for i, release in enumerate(released_poses):
        predicted = alignment @ poses[i + 4390]
        translation.append(float(np.linalg.norm(release[:3, 3] - predicted[:3, 3])))
        rotation.append(float(Rotation.from_matrix(release[:3, :3] @ predicted[:3, :3].T).magnitude()))
    result = {'status': 'compared', 'first_frame_004390': first,
              'viewpoint_comparison': {'frames': 141, 'left_alignment_from_first_frame': alignment.tolist(),
                  'max_translation_residual_m': max(translation), 'median_translation_residual_m': float(np.median(translation)),
                  'max_rotation_residual_rad': max(rotation)},
              'scope': 'Input protocol check only; supplied-pose differences are not localization ATE or evidence for H1; cause not established',
              'inputs': {str(path): {'bytes': path.stat().st_size, 'sha256': sha256(path)}
                         for path in [raw_path, label_path, calib_path, poses_path, *release_paths]}}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'inputs'}, indent=2), flush=True)


if __name__ == '__main__':
    main()
