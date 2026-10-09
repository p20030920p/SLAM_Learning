"""Reuse a validated map and the author's committed palette for evaluation only.

An optional hold pauses only our waiting queue supervisor. Its active author
child continues. The queue resumes in finally, after this GPU stage or failure.
"""
import argparse
import hashlib
import json
import math
import os
import re
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--runtime', type=Path, required=True)
parser.add_argument('--reuse-chain', type=Path, required=True)
parser.add_argument('--wait-record', type=Path, required=True)
parser.add_argument('--hold-queue', type=Path, required=True, help='Our public semantic queue outcomes.json')
parser.add_argument('--name', required=True)
args = parser.parse_args()
r = args.runtime.resolve()
root = r / 'runs' / args.name
root.mkdir(parents=True, exist_ok=False)
source = r / 'upstream/hovsg'
boot = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
state = {'status': 'validating_reuse', 'pid': os.getpid(), 'boot_id': boot,
         'reuse_chain': str(args.reuse_chain), 'stages': {},
         'scope': 'Evaluation only; original author palette and evaluator. Reuses 20-frame skip=100 map; not default benchmark.'}
def save():
    (root / 'outcomes.json').write_text(json.dumps(state, indent=2) + '\n')
def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(4 * 1024**2), b''):
            digest.update(block)
    return digest.hexdigest()
save()
held = None
held_start = None
hold = {}
recorder = None
evaluation_unit = 'slam-author-' + args.name + '-evaluation'

def terminate(signum, frame):
    raise InterruptedError('Evaluation handoff received signal ' + str(signum))

signal.signal(signal.SIGTERM, terminate)
try:
    chain = json.loads((args.reuse_chain / 'outcomes.json').read_text())
    assert chain['skip_frames'] == 100 and chain['stages']['feature_map'] == 0
    validation = json.loads((args.reuse_chain / 'validation.json').read_text())
    assert validation['status'] == 'validated'
    features = args.reuse_chain.with_name(args.reuse_chain.name + '-features')
    record = json.loads((features / 'record.json').read_text())
    assert record['status'] == 'executed' and record['exit_code'] == 0
    commit = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
    assert commit == record['source_commit']
    assert not subprocess.check_output(['git', '-C', str(source), 'status', '--porcelain'], text=True).strip()
    checked = {}
    for key, item in record['artifacts'].items():
        path = Path(key) if Path(key).is_absolute() else features / key
        if path in checked:
            assert checked[path] == item
            continue
        assert path.stat().st_size == item['bytes'] and sha(path) == item['sha256'], str(path)
        checked[path] = item
    palette = source / 'hovsg/labels/class_id_colors.json'
    colors = json.loads(palette.read_text())
    assert '0' in colors and '-1' in colors
    (root / 'reuse-validation.json').write_text(json.dumps({'status': 'validated',
        'artifacts_verified': len(checked), 'original_feature_record': str(features / 'record.json'),
        'feature_validation': validation, 'author_palette': str(palette), 'palette_sha256': sha(palette),
        'source_commit': commit, 'scope': 'Source/map unchanged; author palette includes background and ignored class colors.'}, indent=2) + '\n')
    queue = json.loads(args.hold_queue.read_text())
    assert queue['boot_id'] == boot and queue['status'] == 'running_room0_detect_frontend'
    candidate = queue['pid']
    assert candidate != os.getpid()
    argv = Path('/proc', str(candidate), 'cmdline').read_bytes().decode().split('\0')
    assert any(p.endswith('/scripts/run_public_semantics.py') for p in argv)
    assert args.hold_queue.parent.name in argv
    held_start = Path('/proc', str(candidate), 'stat').read_text().rsplit(')', 1)[1].split()[19]
    held = candidate
    os.kill(held, signal.SIGSTOP)
    hold = {'status': 'queue_supervisor_held', 'queue_pid': held, 'boot_id': boot,
            'held_at': datetime.now(timezone.utc).isoformat(), 'wait_record': str(args.wait_record),
            'scope': 'Only the queue supervisor is paused; its running Detect author stage continues.'}
    (root / 'queue-hold.json').write_text(json.dumps(hold, indent=2) + '\n')
    state['status'] = 'waiting_for_detect_frontend'; save()
    deadline = time.monotonic() + 7500
    while True:
        waiting = json.loads(args.wait_record.read_text())
        assert waiting['boot_id'] == boot
        if waiting['status'] != 'running':
            break
        if time.monotonic() > deadline:
            raise TimeoutError('Detect prerequisite did not finish within its recorded budget')
        time.sleep(10)
    state['wait_record_terminal_status'] = waiting['status']
    state['status'] = 'waiting_for_gpu'; save()
    while subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid', '--format=csv,noheader'], text=True).strip():
        if time.monotonic() > deadline:
            raise TimeoutError('GPU remained busy after prerequisite')
        time.sleep(10)
    work = root / 'evaluation-work'; work.mkdir()
    gt = json.loads((r / 'replica-original-manifest.json').read_text())
    assert gt['gzip_crc'] == 'verified'
    alias = gt['scenes']['room0']['original_scene_name']
    os.environ.update(OMP_NUM_THREADS='8', OPENBLAS_NUM_THREADS='8', MKL_NUM_THREADS='8', WANDB_MODE='disabled')
    state['status'] = 'running_evaluation'; save()
    command = [r / 'envs/hovsg/bin/python', source / 'application/eval/evaluate_sem_seg.py',
        'main.dataset=replica', 'main.scene_name=' + alias,
        'main.feature_map_path=' + str(features / 'artifacts/replica'),
        'main.replica_dataset_gt_path=' + gt['root'], 'main.replica_color_map=' + str(palette),
        'models.clip.checkpoint=' + str(r / 'weights/laion2b_s32b_b79k.bin'),
        'hydra.run.dir=' + str(work / 'hydra')]
    limited = ['systemd-run', '--user', '--scope', '--unit', evaluation_unit,
               '-p', 'MemoryMax=12G', '-p', 'MemorySwapMax=48G', *map(str, command)]
    recorder = subprocess.Popen([sys.executable, str(Path(__file__).with_name('record_command.py')),
        '--output', str(root / 'evaluation'), '--cwd', str(work), '--source', str(source),
        '--method', 'HOV-SG-semantic-evaluation', '--scope', state['scope'], '--timeout', '7200', '--', *limited])
    code = recorder.wait()
    state['stages']['evaluation'] = code
    if code:
        raise RuntimeError('Original HOV-SG evaluation retry failed')
    log = (root / 'evaluation/run.log').read_text()
    metrics = {}
    for metric in ['miou', 'fmiou', 'macc', 'pacc']:
        found = re.findall(r'^' + metric + r':\s+([0-9.eE+-]+)\s*$', log, re.MULTILINE)
        assert len(found) == 1
        metrics[metric] = float(found[0])
        assert math.isfinite(metrics[metric]) and 0 <= metrics[metric] <= 1
    (root / 'metrics.json').write_text(json.dumps({'scene': 'room0', 'gt_scene': alias,
        'units': 'fraction (0..1)', 'metrics': metrics, 'skip_frames': 100, 'scope': state['scope']}, indent=2) + '\n')
    state['status'] = 'executed_single_scene'; save()
except BaseException as exc:
    state.update(status='failed', error_type=type(exc).__name__, error=str(exc)); save()
    raise
finally:
    # Stop only this retry's unique scope before releasing the queue on cancellation.
    # Let the recorder finish so the original stage receives a truthful terminal record.
    if recorder is not None and recorder.poll() is None:
        subprocess.run(['systemctl', '--user', 'kill', '--kill-whom=all', '--signal=TERM', evaluation_unit + '.scope'],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            recorder.wait(timeout=15)
        except subprocess.TimeoutExpired:
            subprocess.run(['systemctl', '--user', 'kill', '--kill-whom=all', '--signal=KILL', evaluation_unit + '.scope'],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            recorder.wait(timeout=15)
    if held is not None:
        try:
            current_start = Path('/proc', str(held), 'stat').read_text().rsplit(')', 1)[1].split()[19]
            if current_start != held_start:
                raise ProcessLookupError('Queue PID was reused; do not signal the new process')
            os.kill(held, signal.SIGCONT)
            hold.update(status='queue_supervisor_resumed', resumed_at=datetime.now(timezone.utc).isoformat())
        except (ProcessLookupError, FileNotFoundError):
            hold.update(status='queue_supervisor_already_exited')
        (root / 'queue-hold.json').write_text(json.dumps(hold, indent=2) + '\n')
