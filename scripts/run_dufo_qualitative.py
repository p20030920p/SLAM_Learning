"""Execute the original DUFOMap on author-released unlabeled sensor demos.

These two datasets have no semantic accuracy GT. We validate output structure,
finite coordinates, point counts and hashes; none of these is an SA/DA score.
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path


def sha256(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--name', required=True)
    parser.add_argument('--wait-outcomes', type=Path)
    args = parser.parse_args()
    runtime = args.runtime.resolve()
    root = runtime / 'runs' / args.name
    root.mkdir(parents=True, exist_ok=False)
    state = {'status': 'waiting_for_inputs', 'pid': os.getpid(), 'scenes': {},
             'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
             'scope': 'Unlabeled kthcampus/twofloor qualitative workflow; no accuracy or efficiency claim'}

    def save():
        (root / 'outcomes.json').write_text(json.dumps(state, indent=2) + '\n')

    save()
    try:
        if args.wait_outcomes:
            while True:
                prior = json.loads(args.wait_outcomes.read_text())
                if prior['status'] in ['executed_five_settings', 'failed']:
                    break
                time.sleep(10)
        manifest = runtime / 'benchmark-qualitative-manifest.json'
        while not manifest.exists():
            time.sleep(10)
        data = json.loads(manifest.read_text())
        assert {item['name'] for item in data} == {'kthcampus', 'twofloor'}
        source = runtime / 'upstream/dufomap'
        for item in data:
            scene = item['name']
            assert item['zip_crc'] == 'verified' and not item['has_ground_truth']
            original = Path(item['root'])
            scans = sorted((original / 'pcd').glob('*.pcd'))
            assert len(scans) == item['scans']
            inputs = root / 'inputs' / scene
            inputs.mkdir(parents=True)
            (inputs / 'pcd').symlink_to(original / 'pcd', target_is_directory=True)
            (root / (scene + '-input-manifest.json')).write_text(json.dumps({
                str(p): {'bytes': p.stat().st_size, 'sha256': sha256(p)} for p in scans}, indent=2) + '\n')
            output = inputs / 'dufomap_output.pcd'
            state['status'] = 'running_' + scene
            save()
            command = [runtime / 'build/dufomap-gcc11/dufomap_run', inputs, source / 'assets/config.toml']
            limited = ['systemd-run', '--user', '--scope', '--unit', 'slam-author-' + args.name + '-' + scene,
                       '-p', 'MemoryMax=4G', '-p', 'MemorySwapMax=6G', '-p', 'CPUQuota=200%', *map(str, command)]
            subprocess.run([sys.executable, str(Path(__file__).with_name('record_command.py')),
                '--output', str(root / (scene + '-mapping')), '--cwd', str(source), '--source', str(source),
                '--method', 'DUFOMap', '--scope', state['scope'] + '; original default config; ' + str(len(scans)) + ' scans',
                '--artifact', str(output), '--timeout', '3600', '--', *limited], check=True)
            # Streaming binary PCD validation avoids loading a large cloud a second time.
            import numpy as np
            with output.open('rb') as stream:
                header = {}
                while True:
                    line = stream.readline().decode('ascii').strip()
                    assert line, 'Unexpected end of PCD header'
                    if line.startswith('#'):
                        continue
                    parts = line.split()
                    header[parts[0]] = parts[1:]
                    if parts[0] == 'DATA':
                        break
                assert header['DATA'] == ['binary']
                counts = list(map(int, header.get('COUNT', ['1'] * len(header['FIELDS']))))
                assert all(count == 1 for count in counts)
                formats = [{'F': 'f', 'U': 'u', 'I': 'i'}[kind] + size for kind, size in zip(header['TYPE'], header['SIZE'])]
                dtype = np.dtype(list(zip(header['FIELDS'], formats)))
                points = int(header['POINTS'][0])
                assert points > 0 and points == int(header['WIDTH'][0]) * int(header['HEIGHT'][0])
                assert output.stat().st_size - stream.tell() == points * dtype.itemsize
                minimum = np.full(3, np.inf)
                maximum = np.full(3, -np.inf)
                remaining = points
                while remaining:
                    take = min(remaining, 262144)
                    values = np.frombuffer(stream.read(take * dtype.itemsize), dtype=dtype)
                    assert len(values) == take
                    xyz = np.column_stack([values[name] for name in ['x', 'y', 'z']])
                    assert np.isfinite(xyz).all()
                    minimum = np.minimum(minimum, xyz.min(axis=0))
                    maximum = np.maximum(maximum, xyz.max(axis=0))
                    remaining -= take
            row = {'status': 'validated', 'input_scans': len(scans), 'output_points': points,
                   'bounds_min_m': minimum.tolist(), 'bounds_max_m': maximum.tolist(),
                   'artifacts': {str(output): {'sha256': sha256(output), 'bytes': output.stat().st_size}},
                   'scope': 'Finite output geometry; no GT, no SA/DA/AA/HA; no claim of correctness from point count'}
            (root / scene).mkdir()
            (root / scene / 'validation.json').write_text(json.dumps(row, indent=2) + '\n')
            state['scenes'][scene] = row
            save()
        state['status'] = 'executed_unlabeled_demonstrations'
        save()
    except Exception as error:
        state.update(status='failed', error_type=type(error).__name__, error=str(error))
        save()
        raise


if __name__ == '__main__':
    main()
