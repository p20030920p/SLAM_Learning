"""Plot validated printed author ablation scores without recomputing metrics."""
import argparse
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument('--run-root', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
metrics = json.loads((args.run_root/'metrics.json').read_text())
record = json.loads((args.run_root/'scores/record.json').read_text())
assert record['status'] == 'executed'
log_hash = hashlib.sha256((args.run_root/'scores/run.log').read_bytes()).hexdigest()
assert log_hash == metrics['original_score_log_sha256'] == record['artifacts']['run.log']['sha256']
order = ['no_ds_no_dp', 'ds_only', 'dp_only', 'coarse_voxel', 'full']
assert list(metrics['rows']) == order
matched = sum(round(row[key], 2) == row['paper_SA_DA_AA_percent'][i]
              for row in metrics['rows'].values() for i,key in enumerate(['SA_percent','DA_percent','AA_percent']))
assert matched == 15, 'Do not describe mismatching values as a matched table'
args.output.mkdir(parents=True, exist_ok=True)
fig, ax = plt.subplots(figsize=(9, 4.9))
labels = ['No margins\nv=0.1 m', 'Range margin\nv=0.1 m', 'Pose margin\nv=0.1 m', 'Both margins\nv=0.2 m', 'Both margins\nv=0.1 m']
x = np.arange(5)
for index,(key,label,color) in enumerate([
    ('SA_percent','Static preservation (SA)','#166c93'),
    ('DA_percent','Dynamic rejection (DA)','#b7662c'),
    ('AA_percent','Geometric balance (AA)','#73838c')]):
    y = [metrics['rows'][name][key] for name in order]
    bars = ax.bar(x+(index-1)*.25, y, width=.23, color=color, label=label)
    ax.bar_label(bars, labels=[f'{value:.2f}' for value in y], fontsize=7, padding=3, rotation=90)
ax.set_ylim(0,118)
ax.set_yticks(np.arange(0,101,20))
ax.set_ylabel('Original author score (%)')
ax.set_xticks(x, labels)
ax.set_axisbelow(True)
ax.grid(axis='y', alpha=.2)
ax.spines[['top','right']].set_visible(False)
fig.suptitle('DUFOMap Table IV: all 15 values match at two decimals', fontsize=12, y=.98)
fig.legend(*ax.get_legend_handles_labels(), loc='upper center', bbox_to_anchor=(.5,.925), ncol=3, frameon=False, fontsize=8)
fig.text(.5,.025,'141 public sequence-00 scans; supplied poses; original C++ and PCL/Python scoring (0.05 m).\nSingle accuracy runs; CPU quota and concurrent work exclude runtime comparisons.',ha='center',fontsize=8)
fig.subplots_adjust(left=.08,right=.99,bottom=.23,top=.82)
fig.savefig(args.output/'dufomap-table4.png',dpi=180)
fig.savefig(args.output/'dufomap-table4.pdf')
(args.output/'dufomap-table4.json').write_text(json.dumps({
    'metrics':str(args.run_root/'metrics.json'), 'original_log_sha256':log_hash,
    'matched_at_paper_two_decimal_precision':matched,'rows':metrics['rows']},indent=2)+'\n')
print('Plot written; 15/15 original printed metrics match the paper precision')
