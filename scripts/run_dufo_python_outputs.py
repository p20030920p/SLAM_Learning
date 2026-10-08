"""Check the author's Python raw/voxel output flag with original scoring.

Reuse the hash-checked completed voxel run. Run unchanged main.py with only
voxel_map=False, preserving its hardcoded d_p=2, range and binding version.
The 0.10m export is a separately labelled threshold sensitivity experiment.
"""
import argparse
import difflib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from validate_kitti_prepared import sha256
from validate_kitti_results import validate_cloud


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--name', required=True)
    args = parser.parse_args()
    r = args.runtime.resolve()
    root = r / 'runs' / args.name
    root.mkdir(parents=True, exist_ok=False)
    source = r / 'upstream/dufomap'
    benchmark = r / 'upstream/dynamicmap'
    state = {'status': 'preparing', 'pid': os.getpid(), 'stages': {},
             'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
             'scope': 'Author Python entry: same 141 released 00 scans, d_p=2, d_s=.2m, voxel=.1m, range .2..50m; voxel_map=False versus completed voxel_map=True; not C++ d_p=1 or paper table reproduction'}

    def save():
        (root / 'outcomes.json').write_text(json.dumps(state, indent=2) + '\n')

    def run(name, command, cwd, canonical, method, scope):
        state['status'] = 'running_' + name
        save()
        limited = ['systemd-run', '--user', '--scope', '--unit', 'slam-author-' + args.name + '-' + name,
                   '-p', 'MemoryMax=2G', '-p', 'MemorySwapMax=6G', '-p', 'CPUQuota=100%', *map(str, command)]
        code = subprocess.call([sys.executable, str(Path(__file__).with_name('record_command.py')),
                                '--output', str(root / name), '--cwd', str(cwd), '--source', str(canonical),
                                '--method', method, '--scope', scope + '; 2GiB RAM/6GiB swap, CPU100%; no timing claim',
                                '--timeout', '1800', '--', *limited])
        state['stages'][name] = code
        save()
        if code:
            raise RuntimeError('Stage failed: ' + name)

    save()
    try:
        prior_path = r / 'runs/dufomap-python-original-01/record.json'
        prior = json.loads(prior_path.read_text())
        assert prior['status'] == 'executed' and prior['source_dirty_after'] == ''
        assert prior['source_commit'] == subprocess.check_output(['git', '-C', source, 'rev-parse', 'HEAD'], text=True).strip()
        voxel = prior_path.parent / 'dufomap_output_voxel.pcd'
        assert sha256(voxel) == prior['artifacts'][voxel.name]['sha256']
        scans = sorted((r / 'data/00-pristine/pcd').glob('*.pcd'))
        assert len(scans) == 141
        (root / 'input-manifest.json').write_text(json.dumps({str(p): {'bytes': p.stat().st_size, 'sha256': sha256(p)}
            for p in [*scans, r / 'data/00-pristine/gt_cloud.pcd']}, indent=2) + '\n')
        state['voxel_reference'] = {'record': str(prior_path), 'sha256': sha256(voxel)}
        save()
        raw_work = root / 'raw-mapping'
        run('raw-mapping', [r / 'envs/lidar/bin/python', source / 'main.py', '--data_dir', r / 'data/00-pristine',
                           '--voxel_map', 'False'], raw_work, source, 'DUFOMap-Python-raw', state['scope'])
        raw_paths = list(raw_work.glob('*.pcd'))
        assert len(raw_paths) == 1, raw_paths
        raw = raw_paths[0]
        raw_record = json.loads((raw_work / 'record.json').read_text())
        assert sha256(raw) == raw_record['artifacts'][raw.name]['sha256']
        validation = {'status': 'validated', 'maps': {}, 'artifacts': {}}
        for name, path in [('raw', raw), ('voxel', voxel)]:
            validation['maps'][name] = {'points': validate_cloud(path), 'path': str(path)}
            validation['artifacts'][str(path)] = {'bytes': path.stat().st_size, 'sha256': sha256(path)}
        (root / 'validation.json').write_text(json.dumps(validation, indent=2) + '\n')
        scripts = root / 'author-scripts'
        shutil.copytree(benchmark / 'scripts', scripts)
        metrics = {}
        for threshold in [0.05, 0.10]:
            label = 'threshold_' + str(round(threshold * 100)) + 'cm'
            dataset = root / label / 'dataset/00'
            dataset.mkdir(parents=True)
            (dataset / 'gt_cloud.pcd').symlink_to(r / 'data/00-pristine/gt_cloud.pcd')
            for name, path in [('raw', raw), ('voxel', voxel)]:
                output = dataset / (name + '_output.pcd')
                output.symlink_to(path)
                run(label + '-' + name + '-export', [r / 'build/dynamicmap/export_eval_pcd', dataset, output.name, str(threshold)],
                    benchmark, benchmark, 'DynamicMap-export', state['scope'] + '; NN threshold=' + str(threshold) + 'm')
            original = (benchmark / 'scripts/py/eval/evaluate_all.py').read_text()
            values = {'Result_Folder': str(dataset.parent), 'algorithms': ['raw', 'voxel'], 'all_seqs': ['00']}
            configured = ''.join(next((key + ' = ' + repr(value) + '\n' for key, value in values.items()
                                      if line.startswith(key + ' = ')), line) for line in original.splitlines(True))
            score = scripts / 'py/eval' / (label + '.py')
            score.write_text(configured)
            (root / (label + '.diff')).write_text(''.join(difflib.unified_diff(original.splitlines(True), configured.splitlines(True),
                fromfile='author/evaluate_all.py', tofile=label + '.py')))
            run(label + '-scores', [r / 'envs/lidar/bin/python', score], benchmark, benchmark, 'DynamicMap-score',
                state['scope'] + '; NN threshold=' + str(threshold) + 'm' + ('; additional sensitivity, not paper metric' if threshold != .05 else ''))
            log = (root / (label + '-scores/run.log')).read_text()
            metrics[label] = {}
            for name in ['raw', 'voxel']:
                rows = [line.split('|') for line in log.splitlines() if re.match(r'^\|\s*' + name + r'\s*\|', line)]
                assert len(rows) == 1
                cells = [c.strip() for c in rows[0][1:-1]]
                metrics[label][name] = dict(zip(['SA_percent', 'DA_percent', 'AA_percent', 'HA_percent'], map(float, cells[3:7])))
        (root / 'metrics.json').write_text(json.dumps({'scope': state['scope'], 'metrics': metrics,
            'limits': 'Two separate original-entry executions, no repeated-run variance; d_p differs from C++ default. Threshold .10m is additional analysis.'}, indent=2) + '\n')
        state['status'] = 'executed_output_audit'
        save()
        print(json.dumps(metrics, indent=2), flush=True)
    except Exception as error:
        state.update(status='failed', error_type=type(error).__name__, error=str(error))
        save()
        raise


if __name__ == '__main__':
    main()
