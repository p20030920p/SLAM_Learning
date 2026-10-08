"""Plot the numbers printed by the original evaluator; never recalculate scores."""
import argparse
import hashlib
import json
import re
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument('--log', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
text = re.sub(r'\x1b\[[0-9;]*[A-Za-z]', '', args.log.read_text())
scores = {}
sequence = None
for line in text.splitlines():
    match = re.search(r'Evaluation results in seq (\w+)', line)
    if match:
        sequence = match[1];scores[sequence] = {}
    if line.startswith('| dufomap') or line.startswith('| beautymap'):
        cells = [cell.strip() for cell in line.strip('|').split('|')]
        assert sequence is not None and len(cells) == 7
        scores[sequence][cells[0]] = dict(zip(['SA', 'DA', 'AA', 'HA'], map(float, cells[3:])))
assert list(scores) == ['00', '05', 'av2', 'semindoor'], scores
assert all(set(value) == {'dufomap', 'beautymap'} for value in scores.values())
args.output.mkdir(parents=True, exist_ok=True)
result = {'source_log': str(args.log), 'source_log_sha256': hashlib.sha256(args.log.read_bytes()).hexdigest(),
          'protocol': 'Original PCL export_eval_pcd, 0.05m; original evaluate_all.py; printed precision', 'scores': scores}
(args.output / 'lidar-scores.json').write_text(json.dumps(result, indent=2) + '\n')
fig, axes = plt.subplots(1, 3, figsize=(10.6, 4.1), sharey=True)
colors = ['#166c93', '#b7662c']
labels = ['00 teaser', '05 release', 'AV2 release', 'Semi-indoor']
for ax, metric in zip(axes, ['SA', 'DA', 'HA']):
    x = np.arange(4)
    for index, method in enumerate(['dufomap', 'beautymap']):
        y = [scores[seq][method][metric] for seq in scores]
        ax.bar(x + (index - .5) * .36, y, width=.34, color=colors[index], label=method)
    ax.set_xticks(x, labels, rotation=27, ha='right')
    ax.set_title({'SA':'Static preservation (SA)', 'DA':'Dynamic rejection (DA)', 'HA':'Harmonic balance (HA)'}[metric])
    ax.set_ylim(0, 100)
    ax.set_axisbelow(True);ax.grid(axis='y', alpha=.2)
axes[0].set_ylabel('Author metric (%)')
fig.legend(*axes[0].get_legend_handles_labels(),loc='upper center',bbox_to_anchor=(.5,.91),ncol=2,frameon=False)
fig.suptitle('Original methods on all four public labeled releases', fontsize=13, y=.98)
fig.text(.5, .04, 'GT poses / prior maps; NN threshold 0.05m. AV2 BeautyMap uses transferred outdoor settings.\nSingle runs; no uncertainty estimates.',
         ha='center', fontsize=8)
fig.subplots_adjust(left=.065,right=.99,bottom=.28,top=.73,wspace=.17)
fig.savefig(args.output / 'lidar-scores.png', dpi=180)
fig.savefig(args.output / 'lidar-scores.pdf')
print(json.dumps(scores, indent=2))
