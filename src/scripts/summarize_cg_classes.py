"""Describe a validated original single-scene confusion matrix without remapping."""
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
parser.add_argument('--run-root', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True, help='New local directory outside the Git checkout')
args = parser.parse_args()
root = args.run_root.resolve()
output = args.output.resolve()
assert not output.exists()
audit = json.loads((root / 'evaluation-audit/validation.json').read_text())
assert audit['status'] == 'validated_original_csv_against_confusion_matrices'
bound = audit['confusion_matrices']
path = Path(bound['path'])
assert path.stat().st_size == bound['bytes']
assert hashlib.sha256(path.read_bytes()).hexdigest() == bound['sha256']
with path.open('rb') as stream:
    saved = pickle.load(stream)  # Hash-bound local output from the completed author evaluator.
assert set(saved) == {'room0', 'all'}, 'This report is specifically the completed room0 run'
keep = np.asarray(saved['room0']['keep_index'], dtype=np.int64)
raw = saved['room0']['conf_matrix'].numpy()
matrix = raw[np.ix_(keep, keep)].astype(np.float64)
assert np.isfinite(matrix).all() and (matrix >= 0).all()
assert np.equal(matrix, np.floor(matrix)).all()
log = (root / 'evaluation/run.log').read_text()
match = re.findall(r'^\d+ classes remains\. They are:\s+(\[.*\])$', log, re.MULTILINE)
assert len(match) == 1
names = ast.literal_eval(match[0])
assert [pair[0] for pair in names] == keep.tolist()
support = matrix.sum(1)
predicted = matrix.sum(0)
tp = matrix.diagonal()
assert (support > 0).all()
iou = tp / np.maximum(1, support + predicted - tp)
recall = tp / np.maximum(1, support)
precision = tp / np.maximum(1, predicted)
f1 = 2 * precision * recall / np.maximum(1, precision + recall)
expected = next(row for row in audit['rows'] if row['scene_id'] == 'room0')
assert int(matrix.sum()) == expected['scored_reconstructed_points']
assert abs(iou.mean() * 100 - expected['author_csv_percent']['miou']) < 1e-5
weighted = (iou * support / support.sum()).sum() * 100
assert abs(weighted - expected['author_csv_percent']['fmiou']) < 1e-5
rows = []
for index, (class_id, name) in enumerate(names):
    rows.append({'class_index': class_id, 'class_name': name,
        'gt_support_reconstructed_points': int(support[index]),
        'predicted_points': int(predicted[index]), 'intersection': int(tp[index]),
        'iou_percent': float(iou[index] * 100), 'recall_percent': float(recall[index] * 100),
        'precision_percent': float(precision[index] * 100), 'author_f1_percent': float(f1[index] * 100),
        'gt_support_percent': float(support[index] / support.sum() * 100)})
output.mkdir(parents=True)
csv_path = output / 'room0-class-metrics.csv'
with csv_path.open('w', newline='') as stream:
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
    writer.writeheader(); writer.writerows(rows)
ordered = sorted(rows, key=lambda item: item['gt_support_reconstructed_points'], reverse=True)
y = np.arange(len(ordered))
fig, axes = plt.subplots(1, 2, figsize=(10, 8), sharey=True, gridspec_kw={'width_ratios': [1.65, 1]})
axes[0].barh(y, [row['iou_percent'] for row in ordered], color='#2867A8', height=0.72)
axes[0].axvline(iou.mean() * 100, color='#A94929', linestyle='--', linewidth=1.3,
                label=f"Macro mIoU {iou.mean() * 100:.2f}%")
axes[0].set_yticks(y, [row['class_name'] for row in ordered])
axes[0].invert_yaxis(); axes[0].set_xlim(0, 100)
axes[0].set_xlabel('Per-class IoU (%)'); axes[0].legend(loc='lower right', fontsize=9)
axes[1].barh(y, [row['gt_support_percent'] for row in ordered], color='#4B8A70', height=0.72)
axes[1].set_xlabel('GT support on scored surface (%)')
for axis in axes:
    axis.grid(axis='x', color='#DCE1E6', linewidth=0.6)
    axis.set_axisbelow(True)
    axis.spines[['top', 'right']].set_visible(False)
fig.suptitle('ConceptGraphs room0 | original semantic evaluation', x=0.52, fontsize=14)
fig.text(0.52, 0.935,
    f"23 GT-present classes | {int(matrix.sum()):,} scored reconstructed points | weighted IoU {weighted:.2f}%",
    ha='center', fontsize=10)
fig.text(0.52, 0.017, 'One scene, SAM microbatch 16; original GT vocabulary, exclusions and interpolation. Not an eight-scene mean.',
    ha='center', fontsize=9)
fig.tight_layout(rect=(0, 0.04, 1, 0.92))
fig.savefig(output / 'room0-class-metrics.png', dpi=160)
fig.savefig(output / 'room0-class-metrics.svg')
plt.close(fig)
summary = {'status': 'descriptive_decomposition_of_validated_author_matrix', 'scene': 'room0',
    'source_matrix': bound, 'source_log_sha256': hashlib.sha256((root / 'evaluation/run.log').read_bytes()).hexdigest(),
    'class_count': len(rows), 'scored_reconstructed_points': int(matrix.sum()),
    'macro_iou_percent': float(iou.mean() * 100), 'frequency_weighted_iou_percent': float(weighted),
    'zero_iou_classes': [row['class_name'] for row in rows if row['intersection'] == 0],
    'zero_predicted_classes': [row['class_name'] for row in rows if row['predicted_points'] == 0],
    'rows': rows,
    'artifacts': {p.name: {'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
                  for p in sorted(output.iterdir())},
    'scope': 'Descriptive only. Support counts are reconstructed points after original author exclusions, not unique GT mesh points or independent observations. Class imbalance alone does not identify frontend, association or pose causes.'}
(output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps({key: summary[key] for key in ['status', 'zero_iou_classes', 'zero_predicted_classes']}), flush=True)
