"""Use author extraction, DUFOMap/BeautyMap, and author scores on missing intervals.

Only uncomment the author's selected 01/02 ranges and set README path/CLI
parameters. The first extracted 00 interval is checked against the released
data. Cell-size runs vary the public XY resolution, retaining z=0.5m and
range=40m; this explicit choice is not an undocumented paper configuration.
"""
import argparse
import difflib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--name', default='kitti-author-selected-01')
    parser.add_argument('--download-name', default='kitti-selected-inputs-01')
    args = parser.parse_args()
    runtime = args.runtime.resolve()
    root = runtime / 'runs' / args.name
    root.mkdir(parents=True, exist_ok=False)
    upstream = runtime / 'upstream/dynamicmap'
    record = Path(__file__).with_name('record_command.py')
    state = {'status': 'waiting_for_download', 'pid': os.getpid(), 'stages': {},
             'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
             'scope': 'Author selected intervals 01:150-250,02:860-950 inclusive; original SuMa-pose preprocessing and original postprocessing methods'}

    def save():
        (root / 'outcomes.json').write_text(json.dumps(state, indent=2) + '\n')

    def run(name, source, method, command, artifacts=(), scope=None):
        state['status'] = 'running_' + name
        save()
        cmd = [sys.executable, str(record), '--output', str(root / name), '--cwd', str(source), '--source', str(source),
               '--method', method, '--scope', scope or state['scope'], '--timeout', '3600']
        for path in artifacts:
            cmd += ['--artifact', str(path)]
        limited = ['systemd-run', '--user', '--scope', '--unit', 'slam-author-' + args.name + '-' + name,
                   '-p', 'MemoryMax=4G', '-p', 'MemorySwapMax=6G', '-p', 'CPUQuota=200%', *map(str, command)]
        subprocess.run([*cmd, '--', *limited], check=True)
        state['stages'][name] = 'executed'
        save()

    save()
    try:
        prior = runtime / 'runs' / args.download_name / 'outcomes.json'
        while True:
            data = json.loads(prior.read_text())
            if data['status'] == 'failed':
                raise RuntimeError('Input download failed: ' + data.get('error', ''))
            if data['status'] == 'downloaded_and_verified':
                break
            time.sleep(10)
        env = runtime / 'envs/kitti-prep/bin/python'
        subprocess.run([env, '-c', 'from av2.geometry.se3 import SE3; import pandas, numpy, scipy, fire, tqdm'], check=True)
        frozen = subprocess.check_output([Path.home() / '.local/bin/uv', 'pip', 'freeze', '--python', env], text=True)
        (runtime / 'kitti-prep-environment.txt').write_text(frozen)
        (root / 'input-manifest.json').write_text(json.dumps(data, indent=2) + '\n')
        scripts = root / 'author-scripts'
        shutil.copytree(upstream / 'scripts', scripts)
        extraction = scripts / 'py/data/extract_semkitti.py'
        original = extraction.read_text()
        edited = original
        for seq, start, end in [('01', 150, 250), ('02', 860, 950)]:
            edited, count = re.subn(r'#\s*("' + seq + r'": \[' + str(start) + ', ' + str(end) + r'\],)', r'\1', edited)
            assert count == 1
        extraction.write_text(edited)
        (root / 'extraction-config.diff').write_text(''.join(difflib.unified_diff(
            original.splitlines(True), edited.splitlines(True), fromfile='author/extract_semkitti.py', tofile='configured/extract_semkitti.py')))
        for seq, (start, end) in data['intervals_inclusive'].items():
            folder = root / 'prepared' / seq
            run(seq + '-extract', upstream, 'DynamicMap-preprocess', [env, extraction,
                '--original_path', runtime / 'data/kitti-original', '--sequence', repr(seq),
                '--save_data_folder', root / 'prepared', '--gt_cloud', 'True'], [folder / 'gt_cloud.pcd'])
            command = [runtime / 'envs/lidar/bin/python', Path(__file__).with_name('validate_kitti_prepared.py'),
                       '--folder', folder, '--start', start, '--end', end,
                       '--output', root / (seq + '-validation/validation.json')]
            if seq == '00':
                command += ['--compare-release', runtime / 'data/00-pristine']
            run(seq + '-validation', upstream, 'Input-validation', command)
        score_data = root / 'dataset'
        for seq in ['01', '02']:
            folder = root / 'prepared' / seq
            destination = score_data / seq
            destination.mkdir(parents=True)
            (destination / 'gt_cloud.pcd').symlink_to(folder / 'gt_cloud.pcd')
            settings = [('dufomap', None), ('beautymap', 1.0)]
            if seq == '02':
                settings += [('beautymap_xy05', 0.5), ('beautymap_xy20', 2.0)]
            for method, cell in settings:
                inputs = root / 'inputs' / seq / method
                inputs.mkdir(parents=True)
                (inputs / 'pcd').symlink_to(folder / 'pcd', target_is_directory=True)
                (inputs / 'gt_cloud.pcd').symlink_to(folder / 'gt_cloud.pcd')
                source = runtime / 'upstream' / ('dufomap' if cell is None else 'beautymap')
                actual = inputs / ('dufomap_output.pcd' if cell is None else 'beautymap_output.pcd')
                if cell is None:
                    command = [runtime / 'build/dufomap-gcc11/dufomap_run', inputs, source / 'assets/config.toml']
                else:
                    command = [runtime / 'envs/lidar/bin/python', source / 'main.py', '--data_dir', inputs,
                               '--dis_range', '40', '--xy_resolution', str(cell), '--h_res', '0.5']
                run(seq + '-' + method, source, method, command, [actual])
                output = destination / (method + '_output.pcd')
                output.symlink_to(actual)
                run(seq + '-' + method + '-export', upstream, 'DynamicMap-export',
                    [runtime / 'build/dynamicmap/export_eval_pcd', destination, output.name, '0.05'],
                    [destination / 'eval' / (method + '_output_exportGT.pcd')])
        metrics = {}
        for seq in ['01', '02']:
            algorithms = ['dufomap', 'beautymap'] + (['beautymap_xy05', 'beautymap_xy20'] if seq == '02' else [])
            score = scripts / 'py/eval' / (seq + '-evaluate_all.py')
            original = (upstream / 'scripts/py/eval/evaluate_all.py').read_text()
            values = {'Result_Folder': str(score_data), 'algorithms': algorithms, 'all_seqs': [seq]}
            configured = ''.join(next((key + ' = ' + repr(value) + '\n' for key, value in values.items()
                                      if line.startswith(key + ' = ')), line) for line in original.splitlines(True))
            score.write_text(configured)
            (root / (seq + '-evaluation-config.diff')).write_text(''.join(difflib.unified_diff(
                original.splitlines(True), configured.splitlines(True), fromfile='author/evaluate_all.py', tofile=seq + '-evaluate_all.py')))
            run(seq + '-scores', upstream, 'DynamicMap-score', [runtime / 'envs/lidar/bin/python', score])
            log = (root / (seq + '-scores/run.log')).read_text()
            for method in algorithms:
                rows = [line.split('|') for line in log.splitlines() if re.match(r'^\|\s*' + method + r'\s*\|', line)]
                assert len(rows) == 1
                cells = [c.strip() for c in rows[0][1:-1]]
                scores = list(map(float, cells[3:7]))
                metrics.setdefault(seq, {})[method] = dict(zip(['SA_percent', 'DA_percent', 'AA_percent', 'HA_percent'], scores))
        (root / 'metrics.json').write_text(json.dumps({'scope': state['scope'], 'metrics': metrics,
            'cell_size_variant': 'XY=0.5/1/2m; fixed author README z=0.5m and range=40m; no runtime comparison'}, indent=2) + '\n')
        state['status'] = 'executed_selected_intervals'
        save()
    except Exception as error:
        state.update(status='failed', error_type=type(error).__name__, error=str(error))
        save()
        raise


if __name__ == '__main__':
    main()
