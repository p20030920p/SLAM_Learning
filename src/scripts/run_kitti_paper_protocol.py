"""Run the author-documented historical benchmark revision on downloaded scans.

The historical extractor and GT/export/scoring code stay original, with only
their documented path/sequence variables configured in copies. Downloaded
SuMa poses are not asserted to equal the paper's unreleased 01/02 inputs.
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

import numpy as np
from validate_kitti_prepared import read_pcd, sha256
from validate_kitti_results import validate_cloud

PAPER_COMMIT = '161b555017608277d21230cd0be0e80589ee8576'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--name', required=True)
    args = parser.parse_args()
    r = args.runtime.resolve()
    root = r / 'runs' / args.name
    root.mkdir(parents=True, exist_ok=False)
    source = r / 'protocol-sources/dynamicmap-dufo-paper'
    state = {'status': 'preparing', 'pid': os.getpid(), 'stages': {},
             'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
             'paper_protocol_source': 'https://github.com/KTH-RPL/DynamicMap_Benchmark/discussions/8',
             'benchmark_commit': PAPER_COMMIT,
             'scope': 'Author-documented DUFOMap historical benchmark revision; unfiltered selected KITTI scans and original C++ GT generation; currently downloadable SuMa poses; paper input equivalence unproven'}

    def save():
        (root / 'outcomes.json').write_text(json.dumps(state, indent=2) + '\n')

    def run(name, canonical, command, method, artifacts=(), scope=None, cwd=None):
        state['status'] = 'running_' + name
        save()
        recorder = [sys.executable, str(Path(__file__).with_name('record_command.py')), '--output', str(root / name),
                    '--cwd', str(cwd or canonical), '--source', str(canonical), '--method', method,
                    '--scope', (scope or state['scope']) + '; 2GiB RAM/6GiB swap, CPU100%; no paper timing claim', '--timeout', '3600']
        for path in artifacts:
            recorder += ['--artifact', str(path)]
        limited = ['systemd-run', '--user', '--scope', '--unit', 'slam-author-' + args.name + '-' + name,
                   '-p', 'MemoryMax=2G', '-p', 'MemorySwapMax=6G', '-p', 'CPUQuota=100%', *map(str, command)]
        code = subprocess.call([*recorder, '--', *limited])
        state['stages'][name] = code
        save()
        if code:
            raise RuntimeError('Original stage failed: ' + name)

    save()
    try:
        inputs = json.loads((r / 'kitti-selected-manifest.json').read_text())
        assert inputs['status'] == 'downloaded_and_verified'
        (root / 'input-manifest.json').write_text(json.dumps(inputs, indent=2) + '\n')
        if not source.exists():
            source.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(['git', 'clone', '--no-hardlinks', '--no-checkout', r / 'upstream/dynamicmap', source], check=True)
            subprocess.run(['git', '-C', source, 'checkout', '--detach', PAPER_COMMIT], check=True)
            subprocess.run(['git', '-C', source, 'remote', 'set-url', 'origin', 'https://github.com/KTH-RPL/DynamicMap_Benchmark.git'], check=True)
        assert subprocess.check_output(['git', '-C', source, 'rev-parse', 'HEAD'], text=True).strip() == PAPER_COMMIT
        assert subprocess.check_output(['git', '-C', source, 'status', '--porcelain'], text=True).strip() == ''
        current = r / 'upstream/dynamicmap'
        audit = {'commit': PAPER_COMMIT, 'author_statement': state['paper_protocol_source'], 'files': {}}
        for filename in ['scripts/py/data/extract_semkitti.py', 'scripts/py/eval/evaluate_all.py',
                         'scripts/py/utils/semkitti_api.py', 'scripts/cpp/export_eval_pcd.cpp', 'scripts/cpp/extract_gtcloud.cpp']:
            old, new = source / filename, current / filename
            audit['files'][filename] = {'historical_sha256': sha256(old), 'current_sha256': sha256(new)}
            diff = ''.join(difflib.unified_diff(old.read_text().splitlines(True), new.read_text().splitlines(True),
                           fromfile='paper-161b555/' + filename, tofile='current-8b60f36/' + filename))
            (root / ('version-' + Path(filename).name + '.diff')).write_text(diff)
        (root / 'source-version.json').write_text(json.dumps(audit, indent=2) + '\n')
        build = root / 'build'
        run('cmake-configure', source, ['cmake', '-S', source / 'scripts', '-B', build], 'Historical-DynamicMap-build')
        run('cmake-build', source, ['cmake', '--build', build, '--target', 'extract_gtcloud', 'export_eval_pcd', '-j1'],
            'Historical-DynamicMap-build', [build / 'extract_gtcloud', build / 'export_eval_pcd'])
        scripts = root / 'author-scripts'
        shutil.copytree(source / 'scripts', scripts)
        original = (source / 'scripts/py/data/extract_semkitti.py').read_text()
        comparisons, artifacts = {}, {}
        for seq, (start, end) in inputs['intervals_inclusive'].items():
            folder = root / 'prepared' / seq
            values = {'ORIGIN_PATH': str(r / 'data/kitti-original') + '/', 'SEQUENCE': seq, 'SaveDataFolder': str(folder / 'pcd')}
            configured = original
            for key, value in values.items():
                configured, count = re.subn(r'^' + key + r'\s*=.*$', key + ' = ' + repr(value), configured, flags=re.MULTILINE)
                assert count == 1
            extractor = scripts / 'py/data' / ('extract_' + seq + '.py')
            extractor.write_text(configured)
            (root / (seq + '-extraction-config.diff')).write_text(''.join(difflib.unified_diff(
                original.splitlines(True), configured.splitlines(True), fromfile='paper/extract_semkitti.py', tofile=extractor.name)))
            run(seq + '-extract', source, [r / 'envs/kitti-prep/bin/python', extractor], 'Historical-DynamicMap-preprocess')
            run(seq + '-gt', source, [build / 'extract_gtcloud', folder / 'pcd'], 'Historical-DynamicMap-GT', [folder / 'gt_cloud.pcd'])
            scans = sorted((folder / 'pcd').glob('*.pcd'))
            assert [p.stem for p in scans] == [f'{n:06d}' for n in range(start, end + 1)]
            count = 0
            comparisons[seq] = {'scans': len(scans), 'released_comparison_performed': seq == '00',
                'same_release_point_count': 0 if seq == '00' else None, 'byte_identical_release_scans': 0 if seq == '00' else None}
            for path in scans:
                header, array = read_pcd(path)
                assert np.isfinite(array).all()
                raw = r / 'data/kitti-original/data_odometry_velodyne/dataset/sequences' / seq / 'velodyne' / (path.stem + '.bin')
                assert len(array) == raw.stat().st_size // 16
                pose = np.asarray(header['VIEWPOINT'], dtype=float)
                assert len(pose) == 7 and abs(np.linalg.norm(pose[3:]) - 1) < 1e-6
                count += len(array)
                artifacts[str(path)] = {'bytes': path.stat().st_size, 'sha256': sha256(path)}
                if seq == '00':
                    release = r / 'data/00-pristine/pcd' / path.name
                    _, old = read_pcd(release)
                    comparisons[seq]['same_release_point_count'] += int(len(old) == len(array))
                    comparisons[seq]['byte_identical_release_scans'] += int(sha256(release) == artifacts[str(path)]['sha256'])
            _, gt = read_pcd(folder / 'gt_cloud.pcd')
            assert len(gt) == count and np.isfinite(gt).all() and np.isin(gt[:, 3], [0, 1]).all()
            comparisons[seq]['gt_points'] = count
            artifacts[str(folder / 'gt_cloud.pcd')] = {'bytes': (folder / 'gt_cloud.pcd').stat().st_size,
                                                       'sha256': sha256(folder / 'gt_cloud.pcd')}
        (root / 'validation.json').write_text(json.dumps({'status': 'validated', 'prepared': comparisons, 'artifacts': artifacts}, indent=2) + '\n')
        metrics = {}
        for seq in ['00', '01', '02']:
            folder = root / 'prepared' / seq
            dataset = root / 'dataset' / seq
            dataset.mkdir(parents=True)
            (dataset / 'gt_cloud.pcd').symlink_to(folder / 'gt_cloud.pcd')
            settings = [('dufomap', None)]
            if seq != '00':
                settings += [('beautymap', 1.0)]
            if seq == '02':
                settings += [('beautymap_xy05', .5), ('beautymap_xy20', 2.0)]
            for method, cell in settings:
                method_source = r / 'upstream' / ('dufomap' if cell is None else 'beautymap')
                work = root / 'inputs' / seq / method
                work.mkdir(parents=True)
                (work / 'pcd').symlink_to(folder / 'pcd', target_is_directory=True)
                (work / 'gt_cloud.pcd').symlink_to(folder / 'gt_cloud.pcd')
                output = work / ('dufomap_output.pcd' if cell is None else 'beautymap_output.pcd')
                command = [r / 'build/dufomap-gcc11/dufomap_run', work, method_source / 'assets/config.toml'] if cell is None else [
                    r / 'envs/lidar/bin/python', method_source / 'main.py', '--data_dir', work, '--dis_range', '40',
                    '--xy_resolution', str(cell), '--h_res', '0.5']
                run(seq + '-' + method, method_source, command, method, [output])
                assert validate_cloud(output) > 0
                (dataset / (method + '_output.pcd')).symlink_to(output)
                run(seq + '-' + method + '-export', source, [build / 'export_eval_pcd', dataset, method + '_output.pcd', '.05'],
                    'Historical-DynamicMap-export', [dataset / 'eval' / (method + '_output_exportGT.pcd')])
            old = (source / 'scripts/py/eval/evaluate_all.py').read_text()
            values = {'Result_Folder': str(dataset.parent), 'algorithms': [item[0] for item in settings], 'all_seqs': [seq]}
            configured = ''.join(next((key + ' = ' + repr(value) + '\n' for key, value in values.items()
                                      if line.startswith(key + ' = ')), line) for line in old.splitlines(True))
            evaluator = scripts / 'py/eval' / (seq + '-scores.py')
            evaluator.write_text(configured)
            (root / (seq + '-evaluation-config.diff')).write_text(''.join(difflib.unified_diff(
                old.splitlines(True), configured.splitlines(True), fromfile='paper/evaluate_all.py', tofile=evaluator.name)))
            run(seq + '-scores', source, [r / 'envs/lidar/bin/python', evaluator], 'Historical-DynamicMap-score')
            log = (root / (seq + '-scores/run.log')).read_text()
            metrics[seq] = {}
            for method, _ in settings:
                rows = [line.split('|') for line in log.splitlines() if re.match(r'^\|\s*' + method + r'\s*\|', line)]
                assert len(rows) == 1
                cells = [c.strip() for c in rows[0][1:-1]]
                metrics[seq][method] = dict(zip(['SA_percent', 'DA_percent', 'AA_percent'], map(float, cells[3:6])))
        (root / 'metrics.json').write_text(json.dumps({'scope': state['scope'], 'metrics': metrics,
            'limits': 'Historical benchmark does not establish identical paper inputs or method checkout. BeautyMap z=.5m chosen from current author README; historical scorer has no HA column.'}, indent=2) + '\n')
        state['status'] = 'executed_historical_protocol'
        save()
        print(json.dumps(metrics, indent=2), flush=True)
    except Exception as error:
        state.update(status='failed', error_type=type(error).__name__, error=str(error))
        save()
        raise


if __name__ == '__main__':
    main()
