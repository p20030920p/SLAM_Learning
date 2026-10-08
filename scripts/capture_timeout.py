"""Explain an already recorded wall-time limit without reclassifying it as OOM."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--run-root', type=Path, required=True)
parser.add_argument('--memory-observations', type=Path)
args = parser.parse_args()
root = args.run_root.resolve()
record_path = root / 'record.json'
record = json.loads(record_path.read_text())
assert record['status'] == 'timed_out', 'Only diagnose an explicitly recorded timeout'
assert record['timeout_seconds'] > 0
output = root / 'diagnostics/timeout-diagnosis.json'
assert not output.exists(), 'Preserve prior diagnostics'

def identity(path):
    return {'path': str(path), 'bytes': path.stat().st_size,
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}

diagnosis = {
    'status': 'confirmed_recorder_wall_time_limit',
    'recorded_at': datetime.now(timezone.utc).isoformat(),
    'method': record['method'], 'source_commit': record['source_commit'],
    'timeout_seconds': record['timeout_seconds'],
    'elapsed_seconds': record['elapsed_seconds'],
    'record': identity(record_path), 'log': identity(root / 'run.log'),
    'missing_artifacts': record.get('missing_artifacts', []),
    'scope': 'The recorder terminated this command at its configured elapsed-time limit. '
             'This is not an OOM diagnosis or an accuracy result. No missing final map '
             'is counted as completed; the original record and log are unchanged.'}
if args.memory_observations:
    memory = json.loads(args.memory_observations.read_text())
    assert memory['status'] != 'observing', 'Wait for monitoring to finish'
    diagnosis['memory_observations'] = identity(args.memory_observations)
    diagnosis['observed_max_memory_bytes'] = memory['observed_max_memory_bytes']
    diagnosis['observed_max_swap_bytes'] = memory['observed_max_swap_bytes']
    diagnosis['memory_scope'] = memory['scope']
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(diagnosis, indent=2) + '\n')
print(json.dumps(diagnosis), flush=True)
