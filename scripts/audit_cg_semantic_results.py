"""Independently audit a completed author CSV against its saved confusion matrices."""
import argparse
import csv
import hashlib
import json
import pickle
from pathlib import Path

import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument('--run-root', type=Path, required=True)
parser.add_argument('--output', type=Path, help='Fresh audit path; never overwrite the original audit')
args = parser.parse_args()
root = args.run_root.resolve()
record = json.loads((root / 'evaluation/record.json').read_text())
assert record['status'] == 'executed' and record['exit_code'] == 0
assert not record['source_dirty_before'] and not record['source_dirty_after']
csv_paths = [Path(p) for p in record['artifacts'] if p.endswith('replica_ex6_results.csv')]
assert len(csv_paths) == 1
csv_path = csv_paths[0]
matrix_path = csv_path.with_name('replica_ex6_conf_matrices.pkl')
def identity(path):
    return {'path': str(path), 'bytes': path.stat().st_size,
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
csv_identity = identity(csv_path)
for path in [csv_path, matrix_path]:
    actual = identity(path)
    expected = record['artifacts'].get(str(path))
    if expected is None:
        # This run's recorder selected CSV artifacts only. Repeat audits bind the
        # local matrix to the archived original audit before deserializing it.
        original_audit = json.loads((root / 'evaluation-audit/validation.json').read_text())
        expected = original_audit['confusion_matrices']
        assert expected['path'] == str(path)
    assert actual['sha256'] == expected['sha256'] and actual['bytes'] == expected['bytes']
with matrix_path.open('rb') as stream:
    matrices = pickle.load(stream)  # This local file was produced by the completed author command.
rows = list(csv.DictReader(csv_path.open()))
assert {row['scene_id'] for row in rows} == set(matrices)
results = []
for row in rows:
    saved = matrices[row['scene_id']]
    raw = saved['conf_matrix'].numpy()
    keep = np.asarray(saved['keep_index'], dtype=np.int64)
    assert np.isfinite(raw).all() and (raw >= 0).all()
    assert np.equal(raw, np.floor(raw)).all()
    matrix = raw[np.ix_(keep, keep)].astype(np.float64)
    support = matrix.sum(1)
    predicted = matrix.sum(0)
    tp = matrix.diagonal()
    assert matrix.sum() > 0
    iou = tp / np.maximum(1, support + predicted - tp)
    recall = tp / np.maximum(1, support)
    precision = tp / np.maximum(1, predicted)
    author_f1 = 2 * precision * recall / np.maximum(1, precision + recall)
    standard_f1 = np.divide(2 * precision * recall, precision + recall,
                            out=np.zeros_like(precision), where=(precision + recall) > 0)
    recomputed = {'miou': iou.mean() * 100, 'mrecall': recall.mean() * 100,
                  'mprecision': precision.mean() * 100, 'mf1score': author_f1.mean() * 100,
                  'fmiou': (iou * support / support.sum()).sum() * 100}
    differences = {key: abs(float(row[key]) - value) for key, value in recomputed.items()}
    assert max(differences.values()) < 1e-5, (row['scene_id'], differences)
    results.append({'scene_id': row['scene_id'], 'evaluated_classes': len(keep),
        'class_indices': keep.tolist(), 'scored_reconstructed_points': int(matrix.sum()),
        'author_csv_percent': {key: float(row[key]) for key in recomputed},
        'max_csv_recalculation_difference_pp': max(differences.values()),
        'standard_macro_f1_percent_supplemental': float(standard_f1.mean() * 100)})
report = {'status': 'validated_original_csv_against_confusion_matrices',
    'csv': csv_identity, 'confusion_matrices': identity(matrix_path), 'rows': results,
    'scope': 'Single-scene author evaluation. CSV and formulas unchanged. '
             'Float64 recalculation tolerance 1e-5 percentage points accounts for original float32 rounding. '
             'Author F1 uses max(1, precision+recall), unlike standard harmonic F1 for small sums; '
             'supplemental standard F1 is explicitly separate and never replaces the original CSV. '
             'The aggregate all row uses its original nonzero-GT-support class subset.'}
output = args.output.resolve() if args.output else root / 'evaluation-audit/validation.json'
assert not output.exists()
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report), flush=True)
