"""Check author-extracted PCD completeness and compare 00 with released inputs."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np


def sha256(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


def read_pcd(path):
    with path.open('rb') as stream:
        header = {}
        while True:
            line = stream.readline().decode('ascii').strip()
            if not line:
                raise ValueError('Unexpected PCD header EOF')
            if line.startswith('#'):
                continue
            parts = line.split()
            header[parts[0]] = parts[1:]
            if parts[0] == 'DATA':
                break
        offset = stream.tell()
    assert header['DATA'] == ['binary']
    assert header['FIELDS'] == ['x', 'y', 'z', 'intensity']
    assert header['SIZE'] == ['4'] * 4 and header['TYPE'] == ['F'] * 4
    points = int(header['POINTS'][0])
    assert points > 0 and points == int(header['WIDTH'][0]) * int(header['HEIGHT'][0])
    assert path.stat().st_size - offset == points * 16
    return header, np.memmap(path, mode='r', dtype='<f4', offset=offset, shape=(points, 4))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--folder', type=Path, required=True)
    parser.add_argument('--start', type=int, required=True)
    parser.add_argument('--end', type=int, required=True)
    parser.add_argument('--compare-release', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    files = sorted((args.folder / 'pcd').glob('*.pcd'))
    assert [p.stem for p in files] == [f'{i:06d}' for i in range(args.start, args.end + 1)]
    points = 0
    artifacts = {}
    comparisons = {}
    for path in [*files, args.folder / 'gt_cloud.pcd']:
        header, array = read_pcd(path)
        assert np.isfinite(array).all()
        assert np.isin(array[:, 3], [0.0, 1.0]).all()
        if path.parent.name == 'pcd':
            points += len(array)
            pose = np.asarray(header['VIEWPOINT'], dtype=float)
            assert len(pose) == 7 and np.isfinite(pose).all() and abs(np.linalg.norm(pose[3:]) - 1) < 1e-6
        else:
            assert len(array) == points
        artifacts[str(path)] = {'bytes': path.stat().st_size, 'sha256': sha256(path), 'points': len(array)}
        if args.compare_release:
            other = args.compare_release / path.relative_to(args.folder)
            old_header, old = read_pcd(other)
            row = {'new_points': len(array), 'released_points': len(old), 'same_points': len(array) == len(old),
                   'file_sha256_equal': sha256(other) == artifacts[str(path)]['sha256']}
            if array.shape == old.shape:
                row.update(xyz_equal=bool(np.array_equal(array[:, :3], old[:, :3])),
                           max_xyz_difference_m=float(np.max(np.abs(array[:, :3] - old[:, :3]))),
                           differing_labels=int(np.count_nonzero(array[:, 3] != old[:, 3])))
            row['viewpoint_equal'] = header['VIEWPOINT'] == old_header['VIEWPOINT']
            comparisons[path.name] = row
    result = {'status': 'validated', 'scans': len(files), 'total_points': points, 'artifacts': artifacts,
              'scope': 'Original author extraction; supplied SuMa poses, original 50m range/ego/label handling; not new localization',
              'released_00_comparison': comparisons}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ['artifacts', 'released_00_comparison']}), flush=True)
    if comparisons:
        print('Release comparison:', json.dumps({
            'files': len(comparisons), 'all_bytes_equal': all(r['file_sha256_equal'] for r in comparisons.values()),
            'all_geometry_and_labels_equal': all(r.get('xyz_equal', False) and r.get('differing_labels') == 0 for r in comparisons.values())}), flush=True)


if __name__ == '__main__':
    main()
