"""Explicit SAM microbatch variant for this 12GB GPU, preserving author checkout.

Only points_per_batch is changed in a separate copy of the original entry.
All 144 grid prompts (12x12), weights, thresholds and frames are retained.
This is a resource compatibility run, not an unchanged-default execution.
"""
import argparse
import difflib
import os
import subprocess
import sys
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--runtime', type=Path, required=True)
parser.add_argument('--name', required=True)
parser.add_argument('--scene', default='room0')
parser.add_argument('--sam-batch', type=int, default=16)
args = parser.parse_args()
assert args.sam_batch > 0
r = args.runtime.resolve()
if subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],text=True).strip():
    raise RuntimeError('A CUDA process is already active')
source = r / 'upstream/conceptgraphs'
variant = r / 'variants' / args.name
variant.mkdir(parents=True, exist_ok=False)
text = (source / 'conceptgraph/scripts/generate_gsa_results.py').read_text()
old = 'points_per_batch=144,'
assert text.count(old) == 1
edited = text.replace(old, 'points_per_batch=' + str(args.sam_batch) + ',', 1)
entry = variant / 'generate_gsa_results.py'
entry.write_text(edited)
diff = variant / 'sam-batch-compatibility.diff'
diff.write_text(''.join(difflib.unified_diff(text.splitlines(True), edited.splitlines(True),
    fromfile='author/generate_gsa_results.py', tofile='compatibility/generate_gsa_results.py')))
os.environ.pop('PYTORCH_CUDA_ALLOC_CONF', None)
os.environ.update(OMP_NUM_THREADS='8', OPENBLAS_NUM_THREADS='8', MKL_NUM_THREADS='8', WANDB_MODE='disabled',
    HF_HUB_CACHE=str(r / 'cache/huggingface/hub'), GSA_PATH=str(r / 'dependencies/Grounded-Segment-Anything'))
scene = r / 'data/replica-full/Replica' / args.scene
for name in ['gsa_detections_none', 'gsa_vis_none', 'gsa_classes_none.json']:
    if (scene / name).exists():raise FileExistsError('Preserve previous output before new frontend: ' + name)
scope = 'Full 2000-frame '+args.scene+', stride 5 = 400 frames; original source copy with ONLY SAM points_per_batch=144->'+str(args.sam_batch)+'; all 12x12 prompts, weights and thresholds retained. Explicit resource compatibility variant; not original batch-default result.'
command = [r / 'envs/conceptgraphs/bin/python', entry, '--dataset_root', scene.parent,
    '--dataset_config', source / 'conceptgraph/dataset/dataconfigs/replica/replica.yaml',
    '--scene_id', args.scene, '--class_set', 'none', '--stride', '5']
recorder = [sys.executable, str(Path(__file__).with_name('record_command.py')),
    '--output', str(r / 'runs' / args.name), '--cwd', str(source / 'conceptgraph'), '--source', str(source),
    '--method', 'ConceptGraphs-SAM-microbatch', '--scope', scope, '--timeout', '7200',
    '--artifact', str(entry), '--artifact', str(diff), '--artifact', str(scene / 'gsa_classes_none.json')]
limited = ['systemd-run', '--user', '--scope', '--unit', 'slam-author-' + args.name,
    '-p', 'MemoryMax=14G', '-p', 'MemorySwapMax=2G', *map(str, command)]
raise SystemExit(subprocess.call([*recorder, '--', *limited]))
