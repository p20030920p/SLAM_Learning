"""Run the unmodified author PCL exporter and author Python score formulas.

The author README asks users to edit three dataset configuration variables.
This script edits only those variables in a separate copy and saves the diff.
"""
from __future__ import annotations
import argparse
import difflib
import json
import shutil
import subprocess
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--name', default='lidar-evaluation-01')
    args = parser.parse_args()
    runtime = args.runtime.resolve()
    output = runtime / 'runs' / args.name
    output.mkdir(parents=True, exist_ok=False)
    seq = output / 'dataset/00'
    seq.mkdir(parents=True)
    files = {
        'gt_cloud.pcd': runtime / 'data/00-pristine/gt_cloud.pcd',
        'beautymap_output.pcd': runtime / 'runs/beautymap-original-01/input/00/beautymap_output.pcd',
        'dufomap_output.pcd': runtime / 'runs/dufomap-cpp-original-01/input/00/dufomap_output.pcd',
        'dufomap_python_output.pcd': runtime / 'runs/dufomap-python-original-01/dufomap_output_voxel.pcd',
    }
    for name, source in files.items():
        if not source.is_file(): raise FileNotFoundError(source)
        shutil.copy2(source, seq / name)
    record = Path(__file__).with_name('record_command.py')
    upstream = runtime / 'upstream/dynamicmap'
    algorithms = ['beautymap', 'dufomap', 'dufomap_python']
    for algorithm in algorithms:
        subprocess.run(['python3', str(record), '--output', str(output / ('export-' + algorithm)),
            '--cwd', str(upstream), '--method', 'DynamicMap-export',
            '--scope', 'Official PCL nearest-neighbor evaluator, threshold 0.05m; public 00 teaser',
            '--artifact', str(seq / 'eval' / (algorithm + '_output_exportGT.pcd')),
            '--', str(runtime / 'build/dynamicmap/export_eval_pcd'), str(seq), algorithm + '_output.pcd', '0.05'], check=True)
    copy = output / 'author-scripts'
    shutil.copytree(upstream / 'scripts', copy)
    score = copy / 'py/eval/evaluate_all.py'
    original = score.read_text()
    lines = original.splitlines(keepends=True)
    settings = {'Result_Folder': str(output / 'dataset'), 'algorithms': algorithms, 'all_seqs': ['00']}
    edited = ''.join(next((key + ' = ' + repr(value) + '\n' for key, value in settings.items()
                           if line.startswith(key + ' = ')), line) for line in lines)
    score.write_text(edited)
    (output / 'evaluation-config.diff').write_text(''.join(difflib.unified_diff(
        original.splitlines(True), edited.splitlines(True), fromfile='upstream/evaluate_all.py', tofile='configured/evaluate_all.py')))
    (output / 'inputs.json').write_text(json.dumps({key: str(value) for key, value in files.items()}, indent=2) + '\n')
    subprocess.run(['python3', str(record), '--output', str(output / 'scores'), '--cwd', str(upstream),
        '--method', 'DynamicMap-score', '--scope', 'Author SA/DA/AA/HA formulas; only three README configuration variables edited',
        '--', str(runtime / 'envs/lidar/bin/python'), str(score)], check=True)

if __name__ == '__main__': main()
