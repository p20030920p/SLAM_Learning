"""Plot audited scene rows without treating partial runs as a full benchmark."""
import argparse
import ast
import csv
import hashlib
import json
import pickle
import re
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument('--run-root', type=Path, action='append', required=True)
parser.add_argument('--output', type=Path, required=True, help='Fresh local report directory')
args = parser.parse_args()
assert not args.output.exists()

def identity(path):
    return {'path': str(path), 'bytes': path.stat().st_size,
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}

rows = []
sources = []
class_rows = []
for root in args.run_root:
    state = json.loads((root / 'outcomes.json').read_text())
    assert state['status'] == 'executed_single_scene'
    audit_path = root / 'evaluation-audit/validation.json'
    audit = json.loads(audit_path.read_text())
    assert audit['status'] == 'validated_original_csv_against_confusion_matrices'
    for name in ['csv', 'confusion_matrices']:
        item = audit[name]
        assert identity(Path(item['path'])) == item
    actual = [row for row in audit['rows'] if row['scene_id'] != 'all']
    assert len(actual) == 1
    row = actual[0]
    scene = row['scene_id']
    frontend = json.loads(Path(state['frontend_record']).read_text())
    assert frontend['status'] == 'executed' and frontend['exit_code'] == 0
    variant = 'Detect' if frontend['method'] == 'cg-detect' else 'SAM-only (batch 16)'
    assert frontend['method'] in ['cg-detect', 'ConceptGraphs-SAM-microbatch']
    assert not any(old['scene'] == scene and old['frontend'] == variant for old in rows)
    log = root / 'evaluation/run.log'
    record = json.loads((root / 'evaluation/record.json').read_text())
    assert identity(log)['sha256'] == record['artifacts']['run.log']['sha256']
    names = re.findall(r'^\d+ classes remains\. They are:\s+(\[.*\])$', log.read_text(), re.MULTILINE)
    assert len(names) == 1
    names = ast.literal_eval(names[0])
    with Path(audit['confusion_matrices']['path']).open('rb') as stream:
        saved = pickle.load(stream)[scene]  # Completed local author output, SHA-bound above.
    keep = np.asarray(saved['keep_index'], dtype=np.int64)
    assert [pair[0] for pair in names] == keep.tolist()
    matrix = saved['conf_matrix'].numpy()[np.ix_(keep, keep)].astype(np.float64)
    assert np.isfinite(matrix).all() and (matrix >= 0).all()
    support, predicted, tp = matrix.sum(1), matrix.sum(0), matrix.diagonal()
    assert int(matrix.sum()) == row['scored_reconstructed_points']
    iou = tp / np.maximum(1, support + predicted - tp)
    assert abs(iou.mean() * 100 - row['author_csv_percent']['miou']) < 1e-5
    for i, (class_id, name) in enumerate(names):
        class_rows.append({'scene': scene, 'frontend': variant, 'class_index': class_id,
            'class_name': name, 'gt_support_points': int(support[i]),
            'predicted_points': int(predicted[i]), 'intersection': int(tp[i]),
            'iou_percent': float(iou[i] * 100)})
    rows.append({'scene': scene, 'frontend': variant, **row['author_csv_percent'],
        'evaluated_classes': len(keep), 'scored_reconstructed_points': int(matrix.sum()),
        'zero_gt_support_classes': int((support == 0).sum()),
        'zero_iou_classes': int((tp == 0).sum()),
        'zero_predicted_classes': int((predicted == 0).sum())})
    sources.append({'run': str(root), 'audit': identity(audit_path),
        'original_csv': audit['csv'], 'confusion_matrices': audit['confusion_matrices'],
        'original_log': identity(log), 'evaluation_record': identity(root / 'evaluation/record.json')})

args.output.mkdir(parents=True)
for name, items in [('scene-metrics.csv', rows), ('class-metrics.csv', class_rows)]:
    with (args.output / name).open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(items[0]))
        writer.writeheader()
        writer.writerows(items)
labels = [row['scene'] + '\n' + ('Detect' if row['frontend'] == 'Detect' else 'SAM-only') for row in rows]
colors = ['#B85C38' if row['frontend'] == 'Detect' else '#2867A8' for row in rows]
fig, axes = plt.subplots(1, 2, figsize=(11, 4.6), sharey=True)
for axis, metric, title in zip(axes, ['miou', 'fmiou'], ['Macro IoU', 'Frequency-weighted IoU']):
    values = [row[metric] for row in rows]
    bars = axis.bar(np.arange(len(rows)), values, color=colors, width=0.65)
    axis.bar_label(bars, labels=[f'{v:.2f}' for v in values], padding=3, fontsize=9)
    axis.set_xticks(np.arange(len(rows)), labels, fontsize=9)
    axis.set_ylim(0, max(60, max(values) * 1.18))
    axis.set_title(title)
    axis.grid(axis='y', color='#DCE1E6', linewidth=0.6)
    axis.set_axisbelow(True)
    axis.spines[['top', 'right']].set_visible(False)
axes[0].set_ylabel('Original scene-row score (%)')
fig.suptitle('ConceptGraphs | completed single-scene evaluations', fontsize=14)
fig.text(0.5, 0.018, 'Stride 5, 400 frames per run; scene rows only. Partial coverage, no eight-scene aggregate or H1 test.',
         ha='center', fontsize=9)
fig.tight_layout(rect=(0, 0.055, 1, 0.93))
fig.savefig(args.output / 'scene-metrics.png', dpi=160)
fig.savefig(args.output / 'scene-metrics.svg')
plt.close(fig)
report = {'status': 'descriptive_summary_of_audited_completed_scene_rows', 'rows': rows,
    'sources': sources,
    'artifacts': {path.name: {key: value for key, value in identity(path).items() if key != 'path'}
                  for path in sorted(args.output.iterdir())},
    'scope': 'No averaging of single-scene all rows, no full benchmark claim. '
             'Scene class subsets can include classes with zero reconstructed GT support. '
             'Macro IoU counts those zero-IoU classes; the original all row uses another subset. '
             'Different author frontend/mapping configurations do not isolate one component or establish causality.'}
(args.output / 'summary.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'status': report['status'], 'rows': rows}), flush=True)
