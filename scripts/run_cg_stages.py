"""Run original ConceptGraphs mapping, RGB fusion and evaluation after 2D extraction.

The only evaluator copy adjustment selects the requested scene(s); a diff is
saved. All formulas, GT alignment and nearest-neighbor operations stay original.
This records a single-scene evaluation, never the full eight-scene benchmark.
"""
import argparse
import difflib
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--runtime', type=Path, required=True)
parser.add_argument('--wait-record', type=Path, required=True)
parser.add_argument('--name', required=True)
parser.add_argument('--scene', default='room0')
parser.add_argument('--variant', choices=['none', 'detect'], default='none')
parser.add_argument('--rgb-record', type=Path, help='Completed same-scene original RGB fusion record to verify and reuse')
parser.add_argument('--animation-checkpoints', action='store_true', help='Author optional deep-copy snapshots; high RAM use, disabled in the README mapping command')
parser.add_argument('--memory-max', default='17G')
parser.add_argument('--swap-max', default='10G')
parser.add_argument('--wait-outcomes', type=Path, help='Serialize retry after another recorded original chain reaches a terminal state')
args = parser.parse_args()
r = args.runtime.resolve()
root = r / 'runs' / args.name
root.mkdir(parents=True, exist_ok=False)
os.environ.update(OMP_NUM_THREADS='8', OPENBLAS_NUM_THREADS='8', MKL_NUM_THREADS='8', WANDB_MODE='disabled',
                  HF_HUB_CACHE=str(r / 'cache/huggingface/hub'),
                  GSA_PATH=str(r / 'dependencies/Grounded-Segment-Anything'))
state = {'status': 'waiting_for_frontend', 'frontend_record': str(args.wait_record), 'stages': {},
         'pid': os.getpid(), 'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip()}
def save():
    (root / 'outcomes.json').write_text(json.dumps(state, indent=2) + '\n')
def on_exception(kind, value, traceback):
    state.update(status='failed', error_type=kind.__name__, error=str(value));save()
    sys.__excepthook__(kind, value, traceback)
sys.excepthook=on_exception
save()
if args.wait_outcomes:
    state.update(status='waiting_for_previous_chain', wait_outcomes=str(args.wait_outcomes));save()
    while True:
        previous = json.loads(args.wait_outcomes.read_text())
        if previous['status'] in ['executed_single_scene', 'failed', 'frontend_not_complete', 'interrupted']:break
        if previous.get('pid') and not Path('/proc', str(previous['pid'])).exists():
            previous.update(status='failed', failure_reason='Supervisor exited before recording a terminal state; not a successful algorithm run')
            args.wait_outcomes.write_text(json.dumps(previous, indent=2) + '\n')
            break
        time.sleep(10)
while True:
    frontend = json.loads(args.wait_record.read_text())
    if frontend['status'] != 'running':break
    if frontend.get('boot_id') != Path('/proc/sys/kernel/random/boot_id').read_text().strip():
        raise RuntimeError('Frontend belongs to a previous boot; inspect interrupted execution first')
    time.sleep(10)
if frontend['status'] != 'executed':
    state.update(status='frontend_not_complete', frontend_status=frontend['status']);save()
    raise RuntimeError('Original frontend did not complete; refusing partial mapping/evaluation')
state['frontend_scope'] = frontend['scope'];save()
python = r / 'envs/conceptgraphs/bin/python'
scripts = Path(__file__).resolve().parent
source = r / 'upstream/conceptgraphs'
scene = r / 'data/replica-full/Replica' / args.scene
variant = 'none' if args.variant == 'none' else 'ram_withbg_allclasses'
subprocess.run([str(python), str(scripts / 'validate_cg_frontend.py'), '--scene-root', str(scene), '--variant', variant,
                '--output', str(root / 'validation.json')], check=True)
suffix = ('overlap_maskconf0.95_simsum1.2_dbscan.1_merge20_masksub' if args.variant == 'none'
          else 'overlap_maskconf0.25_simsum1.2_dbscan.1')
experiment = variant + '_' + suffix
post = scene / 'pcd_saves' / ('full_pcd_' + experiment + '_post.pkl.gz')
if post.exists():raise FileExistsError('Refusing to overwrite an existing original 3D map')

def run(name, command, artifacts, cwd=None, scope=''):
    while subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid', '--format=csv,noheader'], text=True).strip():
        time.sleep(10)
    state.update(status='running_' + name);save()
    recorder = [sys.executable, str(scripts / 'record_command.py'), '--output', str(root / name),
                '--cwd', str(cwd or source / 'conceptgraph'), '--source', str(source), '--method', 'ConceptGraphs-' + name,
                '--scope', scope, '--timeout', '7200']
    for artifact in artifacts:recorder += ['--artifact', str(artifact)]
    limited = ['systemd-run', '--user', '--scope', '--unit', 'slam-author-' + args.name + '-' + name,
               '-p', 'MemoryMax=' + args.memory_max, '-p', 'MemorySwapMax=' + args.swap_max, *map(str, command)]
    code = subprocess.call([*recorder, '--', *limited])
    state['stages'][name] = code;save()
    if code:
        state.update(status='failed',failed_stage=name);save()
        raise RuntimeError('Original author stage failed: ' + name)

mapping = [python, 'slam/cfslam_pipeline_batch.py',
    'dataset_root=' + str(scene.parent), 'dataset_config=' + str(source / 'conceptgraph/dataset/dataconfigs/replica/replica.yaml'),
    'stride=5', 'scene_id=' + args.scene, 'spatial_sim_type=overlap',
    'mask_conf_threshold=' + ('0.95' if args.variant == 'none' else '0.25'),
    'match_method=sim_sum', 'sim_threshold=1.2', 'dbscan_eps=0.1', 'gsa_variant=' + variant,
    'skip_bg=' + ('True' if args.variant == 'none' else 'False'), 'max_bbox_area_ratio=0.5', 'save_suffix=' + suffix,
    'save_objects_all_frames=' + str(args.animation_checkpoints), 'hydra.run.dir=' + str(root / 'mapping-hydra')]
if args.variant == 'none':
    mapping += ['class_agnostic=True', 'merge_interval=20', 'merge_visual_sim_thresh=0.8', 'merge_text_sim_thresh=0.8']
run('mapping', mapping, [post],
    scope='Full 2000-frame '+args.scene+'; stride 5 (400 frames); exact README '+args.variant+' mapping parameters; optional animation checkpoints='+str(args.animation_checkpoints)+'; RAM/swap cgroup '+args.memory_max+'/'+args.swap_max+'. Frontend provenance: '+str(args.wait_record))
validation = [str(python), str(scripts / 'validate_cg_map.py'), '--scene-root', str(scene),
              '--experiment', experiment, '--output', str(root / 'map-validation/validation.json')]
if not args.animation_checkpoints:validation += ['--without-animation-checkpoints']
subprocess.run(validation, check=True)
rgb_artifacts = [scene / 'rgb_cloud/pointclouds/pc_points.h5', scene / 'rgb_cloud/pointcloud.pcd']
if args.rgb_record:
    rgb = json.loads(args.rgb_record.read_text())
    assert rgb['status'] == 'executed' and rgb['method'] == 'ConceptGraphs-rgb-fusion'
    assert rgb['source_commit'] == frontend['source_commit']
    command = rgb['command']
    assert command[command.index('--scene_id') + 1] == args.scene
    for path in rgb_artifacts:
        digest = hashlib.sha256()
        with path.open('rb') as stream:
            for block in iter(lambda: stream.read(4*1024*1024), b''):digest.update(block)
        assert digest.hexdigest() == rgb['artifacts'][str(path)]['sha256']
    state['rgb_reference'] = {'record': str(args.rgb_record), 'status': 'verified_reuse_of_original_same_scene_surface'};save()
else:
    if any(path.exists() for path in rgb_artifacts):raise FileExistsError('Existing RGB surface needs an explicit successful --rgb-record')
    run('rgb-fusion', [python, 'scripts/run_slam_rgb.py', '--dataset_root', scene.parent,
        '--dataset_config', source / 'conceptgraph/dataset/dataconfigs/replica/replica.yaml',
        '--scene_id', args.scene, '--image_height', '480', '--image_width', '640', '--stride', '5', '--save_pcd'],
        rgb_artifacts, scope='Original RGB PointFusion; author sanity-check dimensions/stride; GT odometry; needed as evaluator reference surface')

original = source / 'conceptgraph/scripts/eval_replica_semseg.py'
text = original.read_text()
marker = '\ndef get_parser():'
alias = args.scene[:-1] + '_' + args.scene[-1]
configured = text.replace(marker, '\n# Explicit single-scene evaluation configuration (not eight-scene benchmark).\n'
    + 'REPLICA_SCENE_IDS = ' + repr([args.scene]) + '\nREPLICA_SCENE_IDS_ = ' + repr([alias]) + '\n' + marker, 1)
assert configured != text
copy = root / 'eval_replica_semseg_scene.py'
copy.write_text(configured)
(root / 'evaluation-config.diff').write_text(''.join(difflib.unified_diff(
    text.splitlines(True), configured.splitlines(True), fromfile='author/eval_replica_semseg.py', tofile='configured/eval_replica_semseg_scene.py')))
csv = root / 'results' / experiment / 'replica_ex6_results.csv'
run('evaluation', [python, copy, '--replica_root', scene.parent, '--replica_semantic_root', r / 'data/Replica-semantic',
    '--n_exclude', '6', '--pred_exp_name', experiment], [csv], cwd=root,
    scope='Original semantic evaluator and exact author HDF5 GT; ONLY '+args.scene+' selected in explicit configuration copy; n_exclude=6')
state['status'] = 'executed_single_scene';save()
print('Original ConceptGraphs mapping/RGB fusion/single-scene evaluation completed', flush=True)
