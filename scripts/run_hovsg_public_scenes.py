"""Continue original Replica stages only after the default first scene succeeds."""
import argparse
import csv
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import time
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--runtime', type=Path, required=True)
parser.add_argument('--wait-first', type=Path, required=True, help='Default room0 chain outcomes, not home sampling')
parser.add_argument('--name', required=True)
args = parser.parse_args()
r = args.runtime.resolve()
root = r / 'runs' / args.name
assert root.resolve().parent == r / 'runs'
assert args.wait_first.resolve().is_relative_to(r / 'runs')
root.mkdir(exist_ok=False)
scripts = Path(__file__).resolve().parent
boot = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
source = r / 'upstream/hovsg'
pin = json.loads((scripts.parent / 'config/upstreams.json').read_text())['repositories']['hovsg']['commit']
assert subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip() == pin
assert not subprocess.check_output(['git', '-C', str(source), 'status', '--porcelain'], text=True).strip()
state = {'status': 'waiting_for_default_room0', 'pid': os.getpid(), 'boot_id': boot,
    'source_commit': pin, 'wait_first': str(args.wait_first), 'scenes': {},
    'scope': 'Eight original single-scene Replica semantic evaluations; default skip=10, SAM microbatch16 compatibility. '
             'First default scene must succeed; no home-map substitution, API calls or HM3D hierarchy claim.'}
checked = {}

def save():
    (root / 'outcomes.json').write_text(json.dumps(state, indent=2) + '\n')

def verify_record(path):
    record = json.loads(path.read_text())
    base = path.parent
    assert record['status'] == 'executed' and record['exit_code'] == 0
    assert record['source_commit'] == pin and not record['source_dirty_before'] and not record['source_dirty_after']
    for key, expected in record['artifacts'].items():
        path = (Path(key) if Path(key).is_absolute() else base / key).resolve()
        assert path.is_relative_to(r)
        if str(path) not in checked:
            digest = hashlib.sha256()
            with path.open('rb') as stream:
                for block in iter(lambda: stream.read(4 * 1024**2), b''):
                    digest.update(block)
            checked[str(path)] = {'bytes': path.stat().st_size, 'sha256': digest.hexdigest()}
        assert checked[str(path)] == expected, str(path)

def verify_scene(chain, scene):
    data = json.loads((chain / 'outcomes.json').read_text())
    assert data['status'] == 'executed_single_scene' and data['skip_frames'] == 10 and data['sam_batch'] == 16
    assert data['stages'] == {'feature_map': 0, 'evaluation': 0}
    assert json.loads((chain / 'validation.json').read_text())['status'] == 'validated'
    verify_record(chain.with_name(chain.name + '-features') / 'record.json')
    verify_record(chain / 'evaluation/record.json')
    report = json.loads((chain / 'metrics.json').read_text())
    assert report['scene'] == scene
    log = (chain / 'evaluation/run.log').read_text()
    metrics = {}
    for key in ['miou', 'fmiou', 'macc', 'pacc']:
        values = re.findall(r'^' + key + r':\s+([0-9.eE+-]+)\s*$', log, re.MULTILINE)
        assert len(values) == 1
        value = float(values[0])
        assert math.isfinite(value) and 0 <= value <= 1 and report['metrics'][key] == value
        metrics[key] = value
    state['scenes'][scene] = {'status': 'verified_complete', 'chain': str(chain), 'metrics_fraction': metrics}
    save()

save()
try:
    while True:
        first = json.loads(args.wait_first.read_text())
        if first.get('boot_id') != boot or first['status'] == 'interrupted':
            raise RuntimeError('First default scene belongs to another boot or was interrupted')
        if first['status'] == 'executed_single_scene':
            break
        if first['status'] in ['failed', 'frontend_not_complete']:
            raise RuntimeError('First default HOV scene failed; remaining seven scenes will not be started')
        time.sleep(10)
    previous = args.wait_first.parent
    state['status'] = 'validating_default_room0'; save()
    verify_scene(previous, 'room0')
    for scene in ['office0', 'office1', 'office2', 'office3', 'office4', 'room1', 'room2']:
        assert os.statvfs(r).f_bavail * os.statvfs(r).f_frsize > 64 * 1024**3, 'Keep at least 64 GiB free before another scene'
        name = args.name + '-' + scene
        state['status'] = 'running_' + scene; save()
        with (root / 'orchestration.log').open('ab') as log:
            code = subprocess.call([sys.executable, str(scripts / 'run_hovsg_stages.py'),
                '--runtime', str(r), '--wait-outcomes', str(previous / 'outcomes.json'), '--name', name,
                '--scene', scene, '--sam-batch', '16', '--skip-frames', '10',
                '--memory-max', '16G', '--swap-max', '48G', '--feature-timeout', '21600', '--evaluation-timeout', '7200'],
                stdout=log, stderr=subprocess.STDOUT)
        if code:
            state['scenes'][scene] = {'status': 'failed', 'exit_code': code, 'chain': str(r / 'runs' / name)}
            raise RuntimeError('Unresolved HOV failure; do not repeat it on remaining scenes: ' + scene)
        previous = r / 'runs' / name
        verify_scene(previous, scene)
    with (root / 'scene-metrics.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=['scene', 'miou', 'fmiou', 'macc', 'pacc'])
        writer.writeheader()
        writer.writerows({'scene': scene, **row['metrics_fraction']} for scene, row in state['scenes'].items())
    (root / 'reuse-validation.json').write_text(json.dumps({'status': 'validated', 'artifacts': checked,
        'scope': 'Streamed hashes of original successful feature/evaluation records. Metrics copied exactly from bound logs, fractions 0..1. '
                 'No independent confusion-matrix audit or cross-method aggregate.'}, indent=2) + '\n')
    state['status'] = 'executed_eight_single_scene_evaluations'; save()
except BaseException as exc:
    state.update(status='stopped_unresolved_failure', error_type=type(exc).__name__, error=str(exc)); save()
    raise
