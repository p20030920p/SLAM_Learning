"""Run the five settings in DUFOMap Table IV using unchanged author binaries.

Only the three documented TOML research parameters change. The original
default run is hash-checked and reused. Author PCL export and score formulas
are used, with their three README configuration variables set in a copy.
This is accuracy reproduction on the released 141-scan 00 interval, not a
runtime comparison, online variant, or pose-source experiment.
"""
import argparse
import difflib
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--name', required=True)
    parser.add_argument('--memory-max', default='4G')
    parser.add_argument('--swap-max', default='6G')
    args = parser.parse_args()
    runtime = args.runtime.resolve()
    root = runtime / 'runs' / args.name
    root.mkdir(parents=True, exist_ok=False)
    source = runtime / 'upstream/dufomap'
    benchmark = runtime / 'upstream/dynamicmap'
    recorder = Path(__file__).with_name('record_command.py')
    state = {'status': 'preparing', 'pid': os.getpid(), 'settings': {},
             'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
             'paper': 'https://arxiv.org/html/2403.01449v1#S5.T4',
             'scope': 'Table IV accuracy settings; all 141 public 00 scans; original C++/PCL/Python; no performance or online claim'}

    def save():
        (root / 'outcomes.json').write_text(json.dumps(state, indent=2) + '\n')

    def run(name, command, cwd, method, artifacts):
        limited = ['systemd-run', '--user', '--scope', '--unit', 'slam-author-' + args.name + '-' + name,
                   '-p', 'MemoryMax=' + args.memory_max, '-p', 'MemorySwapMax=' + args.swap_max,
                   '-p', 'CPUQuota=200%', *map(str, command)]
        record = [sys.executable, str(recorder), '--output', str(root / name), '--cwd', str(cwd),
                  '--source', str(source if method == 'DUFOMap' else benchmark), '--method', method,
                  '--scope', state['scope'] + '; ' + name + '; CPU quota 200%, not timing reproduction', '--timeout', '1800']
        for artifact in artifacts:
            record += ['--artifact', str(artifact)]
        subprocess.run([*record, '--', *limited], check=True)

    save()
    inputs = runtime / 'data/00-pristine'
    scans = sorted((inputs / 'pcd').glob('*.pcd'))
    assert len(scans) == 141
    (root / 'input-manifest.json').write_text(json.dumps({
        str(p): {'sha256': sha256(p), 'bytes': p.stat().st_size}
        for p in [*scans, inputs / 'gt_cloud.pcd']}, indent=2) + '\n')
    seq = root / 'dataset/00'
    seq.mkdir(parents=True)
    shutil.copy2(inputs / 'gt_cloud.pcd', seq / 'gt_cloud.pcd')
    original = (source / 'assets/config.toml').read_text()
    settings = [
        ('no_ds_no_dp', 0.1, 0.0, 0, [14.89, 99.99, 38.58]),
        ('ds_only', 0.1, 0.2, 0, [30.29, 99.99, 55.03]),
        ('dp_only', 0.1, 0.0, 1, [91.89, 98.97, 95.37]),
        ('coarse_voxel', 0.2, 0.2, 1, [92.97, 98.24, 95.57]),
        ('full', 0.1, 0.2, 1, [97.96, 98.72, 98.34]),
    ]
    try:
        for name, voxel, ds, dp, paper in settings:
            state['status'] = 'running_' + name
            state['settings'][name] = {'voxel_m': voxel, 'ds_m': ds, 'dp': dp, 'paper_SA_DA_AA_percent': paper}
            save()
            destination = seq / (name + '_output.pcd')
            if name == 'full':
                previous = runtime / 'runs/dufomap-cpp-original-command-01/record.json'
                record = json.loads(previous.read_text())
                assert record['status'] == 'executed' and record['source_dirty_after'] == ''
                output = runtime / 'runs/dufomap-cpp-original-01/input/00/dufomap_output.pcd'
                assert sha256(output) == record['artifacts'][str(output)]['sha256']
                assert record['source_commit'] == subprocess.check_output(
                    ['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
                assert sha256(source / 'assets/config.toml') == hashlib.sha256(original.encode()).hexdigest()
                shutil.copy2(output, destination)
                state['settings'][name]['mapping'] = {'verified_original_record': str(previous), 'sha256': sha256(output)}
            else:
                work = root / 'inputs' / name
                work.mkdir(parents=True)
                (work / 'pcd').symlink_to(inputs / 'pcd', target_is_directory=True)
                values = {'resolution': voxel, 'inflate_hits_dist': ds, 'inflate_unknown': dp}
                edited = original
                for key, value in values.items():
                    edited, count = re.subn(r'^' + key + r'\s*=\s*[^#\n]+', key + ' = ' + str(value) + ' ', edited, flags=re.MULTILINE)
                    assert count == 1
                config = root / (name + '.toml')
                config.write_text(edited)
                (root / (name + '.diff')).write_text(''.join(difflib.unified_diff(
                    original.splitlines(True), edited.splitlines(True), fromfile='author/assets/config.toml', tofile=name + '.toml')))
                output = work / 'dufomap_output.pcd'
                run(name + '-mapping', [runtime / 'build/dufomap-gcc11/dufomap_run', work, config], source, 'DUFOMap', [output, config])
                shutil.copy2(output, destination)
                state['settings'][name]['mapping'] = 'executed'
            run(name + '-export', [runtime / 'build/dynamicmap/export_eval_pcd', seq, destination.name, '0.05'],
                benchmark, 'DynamicMap-export', [seq / 'eval' / (name + '_output_exportGT.pcd')])
            state['settings'][name]['export'] = 'executed'
            save()
        scripts = root / 'author-scripts'
        shutil.copytree(benchmark / 'scripts', scripts)
        score = scripts / 'py/eval/evaluate_all.py'
        text = score.read_text()
        values = {'Result_Folder': str(root / 'dataset'), 'algorithms': [item[0] for item in settings], 'all_seqs': ['00']}
        configured = ''.join(next((key + ' = ' + repr(value) + '\n' for key, value in values.items()
                                  if line.startswith(key + ' = ')), line) for line in text.splitlines(True))
        score.write_text(configured)
        (root / 'evaluation-config.diff').write_text(''.join(difflib.unified_diff(
            text.splitlines(True), configured.splitlines(True), fromfile='author/evaluate_all.py', tofile='configured/evaluate_all.py')))
        run('scores', [runtime / 'envs/lidar/bin/python', score], benchmark, 'DynamicMap-score', [])
        log = (root / 'scores/run.log').read_text()
        metrics = {}
        for name, voxel, ds, dp, paper in settings:
            rows = [line.split('|') for line in log.splitlines() if re.match(r'^\|\s*' + name + r'\s*\|', line)]
            assert len(rows) == 1
            cells = [cell.strip() for cell in rows[0][1:-1]]
            measured = [float(item) for item in cells[3:7]]
            assert len(measured) == 4
            metrics[name] = {'SA_percent': measured[0], 'DA_percent': measured[1], 'AA_percent': measured[2],
                             'HA_percent': measured[3], 'paper_SA_DA_AA_percent': paper,
                             'difference_percentage_points': [measured[i] - paper[i] for i in range(3)]}
        (root / 'metrics.json').write_text(json.dumps({'scope': state['scope'], 'source': str(root / 'scores/record.json'),
            'original_score_log_sha256': sha256(root / 'scores/run.log'), 'units': 'percent; printed author precision',
            'rows': metrics}, indent=2) + '\n')
        state['status'] = 'executed_five_settings'
        save()
    except Exception as error:
        state.update(status='failed', error_type=type(error).__name__, error=str(error))
        save()
        raise


if __name__ == '__main__':
    main()
