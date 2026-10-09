"""Run original current HA scoring on the completed historical 02 exports.

The author-documented historical benchmark reports AA, while BeautyMap's
Table III reports HA. Reuse verified original maps/GT/exported labels and run
the unchanged current evaluator with only its three README variables set.
"""
import argparse
import difflib
import json
import math
import re
import shutil
import subprocess
import sys
from pathlib import Path

from validate_kitti_prepared import sha256


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--historical-run', type=Path, required=True)
    parser.add_argument('--name', required=True)
    args = parser.parse_args()
    r = args.runtime.resolve()
    historical = args.historical_run.resolve()
    assert historical.is_relative_to(r / 'runs')
    root = r / 'runs' / args.name
    root.mkdir(parents=True, exist_ok=False)
    previous = json.loads((historical / 'outcomes.json').read_text())
    assert previous['status'] == 'executed_historical_protocol'
    source = r / 'upstream/dynamicmap'
    algorithms = ['beautymap_xy05', 'beautymap', 'beautymap_xy20']
    references = {}
    for name in [*(f'02-{algo}-export' for algo in algorithms), '02-gt']:
        record_path = historical / name / 'record.json'
        record = json.loads(record_path.read_text())
        assert record['status'] == 'executed' and record['exit_code'] == 0
        assert record['source_dirty_before'] == '' and record['source_dirty_after'] == ''
        for filename, expected in record['artifacts'].items():
            path = Path(filename) if Path(filename).is_absolute() else record_path.parent / filename
            assert path.stat().st_size == expected['bytes'] and sha256(path) == expected['sha256']
        references[name] = {'record': str(record_path), 'sha256': sha256(record_path)}
    (root / 'input-manifest.json').write_text(json.dumps({'historical_run': str(historical),
        'benchmark_commit': previous['benchmark_commit'], 'verified_references': references}, indent=2) + '\n')
    scripts = root / 'author-scripts'
    shutil.copytree(source / 'scripts/py', scripts)
    original = (source / 'scripts/py/eval/evaluate_all.py').read_text()
    values = {'Result_Folder': str(historical / 'dataset'), 'algorithms': algorithms, 'all_seqs': ['02']}
    configured = ''.join(next((key + ' = ' + repr(value) + '\n' for key, value in values.items()
                              if line.startswith(key + ' = ')), line) for line in original.splitlines(True))
    script = scripts / 'eval/evaluate_all.py'
    script.write_text(configured)
    (root / 'evaluation-config.diff').write_text(''.join(difflib.unified_diff(original.splitlines(True), configured.splitlines(True),
        fromfile='current-author/evaluate_all.py', tofile='configured/evaluate_all.py')))
    code = subprocess.call([sys.executable, str(Path(__file__).with_name('record_command.py')),
        '--output', str(root / 'scores'), '--cwd', str(source), '--source', str(source), '--method', 'BeautyMap-TableIII-original-HA-score',
        '--scope', 'Original current evaluator including HA; hash-verified original historical 02 GT/exports; unchanged BeautyMap .5/1/2m cells, z=.5m, range40m; original PCL threshold .05m; not runtime comparison',
        '--timeout', '600', '--', 'systemd-run', '--user', '--scope', '--unit', 'slam-author-' + args.name,
        '-p', 'MemoryMax=2G', '-p', 'MemorySwapMax=6G', '-p', 'CPUQuota=100%', str(r / 'envs/lidar/bin/python'), str(script)])
    assert code == 0
    log = (root / 'scores/run.log').read_text()
    paper = {'beautymap_xy05': [83.92, 84.14, 84.03], 'beautymap': [83.40, 82.41, 82.90],
             'beautymap_xy20': [74.92, 88.83, 81.28]}
    metrics = {}
    for name in algorithms:
        rows = [line.split('|') for line in log.splitlines() if re.match(r'^\|\s*' + name + r'\s*\|', line)]
        assert len(rows) == 1
        cells = [c.strip() for c in rows[0][1:-1]]
        measured = list(map(float, cells[3:7]))
        assert len(measured) == 4 and all(math.isfinite(v) for v in measured)
        compared = [measured[0], measured[1], measured[3]]
        metrics[name] = dict(zip(['SA_percent', 'DA_percent', 'AA_percent', 'HA_percent'], measured))
        metrics[name].update(paper_SA_DA_HA_percent=paper[name],
            difference_percentage_points=[compared[i] - paper[name][i] for i in range(3)],
            all_match_two_decimals=all(f'{compared[i]:.2f}' == f'{paper[name][i]:.2f}' for i in range(3)))
    result = {'status': 'evaluated', 'paper': 'https://arxiv.org/html/2405.07283v1#S4.T3',
        'metrics': metrics, 'matched_values_at_two_decimals': sum(3 for row in metrics.values() if row['all_match_two_decimals']),
        'original_score_log_sha256': sha256(root / 'scores/run.log'),
        'scope': 'BeautyMap Table III accuracy only, historical original preprocessing/GT/export plus original current HA scorer; method source unchanged. Matching numbers do not prove all unreported paper settings or pose versions identical.'}
    (root / 'metrics.json').write_text(json.dumps(result, indent=2) + '\n')
    (root / 'outcomes.json').write_text(json.dumps({'status': 'executed_table3_accuracy',
        'historical_run': str(historical), 'matched_values_at_two_decimals': result['matched_values_at_two_decimals']}, indent=2) + '\n')
    print(json.dumps(result, indent=2), flush=True)


if __name__ == '__main__':
    main()
