"""Reuse completed author stages after a reboot or explicit failed-frontend retry."""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--runtime', type=Path, required=True)
parser.add_argument('--previous-queue', type=Path, required=True)
parser.add_argument('--room0-cg', type=Path, required=True)
parser.add_argument('--name', required=True)
parser.add_argument('--retry-failed-frontend', action='store_true', help='Explicitly retry a failed frontend after diagnosing its cause; preserve its real exit code')
parser.add_argument('--detect-allocator-conf', default='', help='Explicit PyTorch allocator environment for new Detect runs only')
parser.add_argument('--detect-model-offload', action='store_true', help='Disclosed sequential GPU model-residency variant for new Detect frontends')
parser.add_argument('--detect-timeout', type=int, default=7200, help='Recorded wall-time limit for each new Detect frontend')
args = parser.parse_args()
assert not (args.detect_allocator_conf and args.detect_model_offload), 'Isolate resource variants'
assert args.detect_timeout > 0
r = args.runtime.resolve()
old = args.previous_queue.resolve()
assert old.is_relative_to(r / 'runs')
previous = json.loads((old / 'outcomes.json').read_text())
boot = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
assert ((previous['status'] == 'interrupted' and previous['boot_id'] != boot)
        or (args.retry_failed_frontend and previous['status'] == 'failed'))
root = r / 'runs' / args.name
assert root.resolve().parent == r / 'runs', 'Use a single new run-directory name inside this runtime'
root.mkdir(parents=True, exist_ok=False)
scripts = Path(__file__).resolve().parent
source = r / 'upstream/conceptgraphs'
commit = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
assert commit == json.loads((scripts.parent / 'config/upstreams.json').read_text())['repositories']['conceptgraphs']['commit']
assert not subprocess.check_output(['git', '-C', str(source), 'status', '--porcelain'], text=True).strip()
state = {'status': 'validating_prior_results', 'pid': os.getpid(), 'boot_id': boot,
         'previous_queue': str(old), 'scenes': {}, 'source_commit': commit,
         'retry_failed_frontend_enabled': args.retry_failed_frontend,
         'detect_allocator_conf': args.detect_allocator_conf,
         'detect_model_offload': args.detect_model_offload,
         'detect_timeout_seconds': args.detect_timeout,
         'scope': 'Resume all eight CG SAM-only and author Detect scenes; preserve prior completed stages and interrupted outputs. No HOV default substitution or API calls.'}
checked = {}
def save():
    (root / 'outcomes.json').write_text(json.dumps(state, indent=2) + '\n')
def identity(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(4 * 1024**2), b''):
            digest.update(block)
    return {'bytes': path.stat().st_size, 'sha256': digest.hexdigest()}
def verify_artifacts(items, base):
    for key, expected in items.items():
        path = (Path(key) if Path(key).is_absolute() else base / key).resolve()
        assert path.is_relative_to(r), str(path)
        if path not in checked:
            checked[path] = identity(path)
        assert checked[path] == expected, str(path)
def verify_record(path):
    item = json.loads(path.read_text())
    assert item['status'] == 'executed' and item['exit_code'] == 0, str(path)
    assert item['source_commit'] == commit and not item['source_dirty_before'] and not item['source_dirty_after']
    verify_artifacts(item['artifacts'], path.parent)
    return item
def completed(chain, scene):
    outcome = chain / 'outcomes.json'
    if not outcome.exists():
        return False
    data = json.loads(outcome.read_text())
    if data['status'] != 'executed_single_scene':
        return False
    for path in chain.rglob('record.json'):
        verify_record(path)
    validation = json.loads((chain / 'validation.json').read_text())
    assert validation['status'] == 'validated' and validation['processed_frames'] == 400
    verify_artifacts(validation['artifacts'], chain)
    validation = json.loads((chain / 'map-validation/validation.json').read_text())
    assert validation['status'] == 'validated' and validation['scene'] == scene
    verify_artifacts(validation['artifacts'], chain)
    if 'rgb_reference' in data:
        verify_record(Path(data['rgb_reference']['record']))
    if 'mapping_reference' in data:
        verify_record(Path(data['mapping_reference']['record']))
    return True
def wait_gpu():
    while subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid', '--format=csv,noheader'], text=True).strip():
        time.sleep(10)
def run(script, arguments):
    with (root / 'orchestration.log').open('ab') as log:
        code = subprocess.call([sys.executable, str(scripts / script), *map(str, arguments)], stdout=log, stderr=subprocess.STDOUT)
    if code:
        raise RuntimeError(script + ' exited ' + str(code))
def preserve_interrupted(scene, variant, record_path):
    item = json.loads(record_path.read_text())
    assert item['source_commit'] == commit
    if item['status'] == 'interrupted':
        assert item['boot_id'] != boot and item['exit_code'] is None
    else:
        assert args.retry_failed_frontend and item['status'] == 'failed' and item['exit_code'] != 0
        assert not item['source_dirty_before'] and not item['source_dirty_after']
    scene_root = (r / 'data/replica-full/Replica' / scene).resolve()
    target = root / 'preserved-interrupted' / (scene + '-' + variant)
    target.mkdir(parents=True, exist_ok=False)
    entries = []
    for name in ['gsa_detections_' + variant, 'gsa_vis_' + variant, 'gsa_classes_' + variant + '.json']:
        path = (scene_root / name).resolve()
        assert path.parent == scene_root and path.is_relative_to(r / 'data')
        if not path.exists():
            continue
        files = sorted(path.rglob('*')) if path.is_dir() else [path]
        bindings = {str(file.relative_to(scene_root)): identity(file) for file in files if file.is_file()}
        destination = target / name
        assert destination.resolve().is_relative_to(root) and not destination.exists()
        path.rename(destination)
        for key, expected in bindings.items():
            assert identity(target / key) == expected
        entries.append({'original_path': str(path), 'preserved_path': str(destination), 'artifacts': bindings})
    (target / 'preservation.json').write_text(json.dumps({'status': 'preserved_unsuccessful_outputs_before_fresh_full_frontend',
        'old_record': str(record_path), 'old_record_identity': identity(record_path), 'old_boot_id': item['boot_id'],
        'current_boot_id': boot, 'old_status': item['status'], 'old_exit_code': item['exit_code'],
        'exit_code_unknown': item['exit_code'] is None, 'entries': entries,
        'scope': 'Neither partial outputs nor a 400/400 log replace a successful exit receipt. '
                 'Preserve any known nonzero exit as recorded. Fresh author frontend reruns all 400 frames.'}, indent=2) + '\n')
save()
try:
    wait_gpu()
    for scene in ['room0', 'office0', 'office1', 'office2', 'office3', 'office4', 'room1', 'room2']:
        row = {}; state['scenes'][scene] = row; save()
        for variant in ['none', 'detect']:
            suffix = 'cg' if variant == 'none' else 'detect'
            prior = args.room0_cg if scene == 'room0' and variant == 'none' else r / 'runs' / (old.name + '-' + scene + '-' + suffix + '-stages')
            previous_stage = previous.get('scenes', {}).get(scene, {}).get(suffix)
            if isinstance(previous_stage, dict) and previous_stage.get('chain'):
                prior = Path(previous_stage['chain']).resolve()
                assert prior.is_relative_to(r / 'runs'), 'Completed references must stay in this runtime'
            if completed(prior, scene):
                row[suffix] = {'status': 'verified_reuse', 'chain': str(prior)}; save()
                continue
            assert not (prior / 'outcomes.json').exists(), 'Inspect incomplete mapping before retry: ' + str(prior)
            name = args.name + '-' + scene + '-' + suffix
            frontend = r / 'runs' / (name + '-frontend')
            old_frontend = r / 'runs' / (old.name + '-' + scene + '-' + suffix + '-frontend')
            if (old_frontend / 'record.json').exists():
                old_record = json.loads((old_frontend / 'record.json').read_text())
                if old_record['status'] == 'executed':
                    verify_record(old_frontend / 'record.json'); frontend = old_frontend
                else:
                    preserve_interrupted(scene, 'none' if variant == 'none' else 'ram_withbg_allclasses', old_frontend / 'record.json')
            if frontend != old_frontend:
                state['status'] = 'running_' + scene + '_' + suffix + '_frontend'; save(); wait_gpu()
                if variant == 'none':
                    run('run_cg_resource_frontend.py', ['--runtime', r, '--scene', scene, '--name', frontend.name, '--sam-batch', '16'])
                else:
                    options = ['--runtime', r, '--scene', scene, '--name', frontend.name, '--timeout', str(args.detect_timeout)]
                    entry = 'run_cg_offloaded_frontend.py' if args.detect_model_offload else 'run_semantic_entry.py'
                    if not args.detect_model_offload:
                        options += ['--mode', 'cg-detect']
                    if args.detect_allocator_conf:
                        options += ['--allocator-conf', args.detect_allocator_conf]
                    run(entry, options)
            state['status'] = 'running_' + scene + '_' + suffix + '_stages'; save()
            chain = r / 'runs' / (name + '-stages')
            arguments = ['--runtime', r, '--scene', scene, '--variant', variant, '--wait-record', frontend / 'record.json', '--name', chain.name]
            if variant == 'detect':
                rgb_chain = Path(row['cg']['chain'])
                rgb_outcome = json.loads((rgb_chain / 'outcomes.json').read_text())
                rgb_record = Path(rgb_outcome['rgb_reference']['record']) if 'rgb_reference' in rgb_outcome else rgb_chain / 'rgb-fusion/record.json'
                arguments += ['--rgb-record', rgb_record]
            run('run_cg_stages.py', arguments)
            assert completed(chain, scene)
            row[suffix] = {'status': 'executed_single_scene', 'chain': str(chain)}; save()
    (root / 'reuse-validation.json').write_text(json.dumps({'status': 'validated', 'unique_artifacts_verified': len(checked),
        'scope': 'Streamed SHA-256 checks of completed records, all 400-frame frontend contracts, maps and RGB references'}, indent=2) + '\n')
    for variant, exp in [('cg', 'none_overlap_maskconf0.95_simsum1.2_dbscan.1_merge20_masksub'),
                         ('detect', 'ram_withbg_allclasses_overlap_maskconf0.25_simsum1.2_dbscan.1')]:
        state['status'] = 'running_unmodified_eight_scene_' + variant + '_evaluation'; save(); wait_gpu()
        work = root / (variant + '-full-evaluation-work'); work.mkdir()
        os.environ.update(HF_HUB_CACHE=str(r / 'cache/huggingface/hub'), OMP_NUM_THREADS='8', OPENBLAS_NUM_THREADS='8', MKL_NUM_THREADS='8')
        csv = work / 'results' / exp / 'replica_ex6_results.csv'
        command = [r / 'envs/conceptgraphs/bin/python', source / 'conceptgraph/scripts/eval_replica_semseg.py',
            '--replica_root', r / 'data/replica-full/Replica', '--replica_semantic_root', r / 'data/Replica-semantic', '--n_exclude', '6', '--pred_exp_name', exp]
        limited = ['systemd-run', '--user', '--scope', '--unit', 'slam-author-' + args.name + '-' + variant + '-eight-scene-evaluation',
            '-p', 'MemoryMax=12G', '-p', 'MemorySwapMax=48G', *map(str, command)]
        run('record_command.py', ['--output', root / (variant + '-eight-scene-evaluation'), '--cwd', work, '--source', source,
            '--method', 'ConceptGraphs-original-eight-scene-evaluation', '--scope', 'UNMODIFIED author evaluator, all eight scenes, original GT; ' + variant + '; completed stages verified after restart',
            '--timeout', '7200', '--artifact', csv, '--artifact', csv.with_name('replica_ex6_conf_matrices.pkl'), '--', *limited])
        state[variant + '_eight_scene_evaluation_exit'] = 0; save()
    state['status'] = 'executed_eight_scene_evaluations'; save()
except BaseException as error:
    state.update(status='failed', error_type=type(error).__name__, error=str(error)); save()
    raise
