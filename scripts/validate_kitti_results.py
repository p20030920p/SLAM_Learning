"""Check all six completed maps and bind original scoring logs to records."""
import argparse
import json
from pathlib import Path
import numpy as np
from validate_kitti_prepared import sha256


def validate_cloud(path):
    with path.open('rb') as stream:
        header = {}
        while True:
            line = stream.readline().decode('ascii').strip()
            assert line
            if line.startswith('#'):
                continue
            parts = line.split()
            header[parts[0]] = parts[1:]
            if parts[0] == 'DATA':
                break
        assert header['DATA'] == ['binary']
        assert all(int(n) == 1 for n in header.get('COUNT', ['1'] * len(header['FIELDS'])))
        formats = [{'F': 'f', 'U': 'u', 'I': 'i'}[kind] + size for kind, size in zip(header['TYPE'], header['SIZE'])]
        dtype = np.dtype(list(zip(header['FIELDS'], formats)))
        points = int(header['POINTS'][0])
        assert points > 0 and points == int(header['WIDTH'][0]) * int(header['HEIGHT'][0])
        assert path.stat().st_size - stream.tell() == points * dtype.itemsize
        remaining = points
        while remaining:
            take = min(remaining, 262144)
            block = np.frombuffer(stream.read(take * dtype.itemsize), dtype=dtype)
            assert len(block) == take
            assert all(np.isfinite(block[name]).all() for name in ['x', 'y', 'z'])
            remaining -= take
    return points


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    state = json.loads((args.run / 'outcomes.json').read_text())
    assert state['status'] == 'executed_selected_intervals'
    names = ['01-dufomap', '01-beautymap', '02-dufomap', '02-beautymap', '02-beautymap_xy05', '02-beautymap_xy20']
    artifacts, maps = {}, {}
    for name in [*names, '01-scores', '02-scores']:
        record_path = args.run / name / 'record.json'
        record = json.loads(record_path.read_text())
        assert record['status'] == 'executed' and record['exit_code'] == 0
        assert record['source_dirty_before'] == '' and record['source_dirty_after'] == ''
        log = record_path.with_name('run.log')
        assert sha256(log) == record['artifacts']['run.log']['sha256']
        if name not in names:
            continue
        outputs = [(Path(key), value) for key, value in record['artifacts'].items()
                   if key.endswith('_output.pcd')]
        assert len(outputs) == 1
        path, expected = outputs[0]
        assert path.stat().st_size == expected['bytes'] and sha256(path) == expected['sha256']
        maps[name] = {'output_points': validate_cloud(path), 'path': str(path)}
        artifacts[str(path)] = expected
    result = {'status': 'validated', 'maps': maps, 'artifacts': artifacts,
              'scope': 'Six completed binary maps: recorded hashes, sizes, finite XYZ, point counts and original log hashes; no new accuracy formula'}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'artifacts'}, indent=2), flush=True)


if __name__ == '__main__':
    main()
