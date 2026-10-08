"""Record a direct author command and hashes without importing algorithm code."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import signal
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--cwd', type=Path, required=True)
    parser.add_argument('--method', required=True)
    parser.add_argument('--scope', required=True)
    parser.add_argument('--source', type=Path)
    parser.add_argument('--timeout', type=float, default=3600)
    parser.add_argument('--artifact', type=Path, action='append', default=[])
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    if not command:
        parser.error('A command after -- is required')
    args.output.mkdir(parents=True, exist_ok=False)
    source = args.source or args.cwd
    record = {
        'schema_version': 1, 'method': args.method, 'scope': args.scope, 'status': 'running',
        'started_at': datetime.now(timezone.utc).isoformat(), 'command': command,
        'cwd': str(args.cwd.resolve()), 'source': str(source.resolve()),
        'source_commit': subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip(),
        'source_dirty_before': subprocess.check_output(['git', '-C', str(source), 'status', '--porcelain'], text=True).strip(),
        'exit_code': None, 'artifacts': {},
        'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
    }
    record_path = args.output / 'record.json'
    record_path.write_text(json.dumps(record, indent=2) + '\n')
    started = time.monotonic()
    print(f"Running {args.method}; log: {args.output / 'run.log'}", flush=True)
    with (args.output / 'run.log').open('wb') as log:
        try:
            process = subprocess.Popen(command, cwd=args.cwd, stdout=log, stderr=subprocess.STDOUT,
                                       start_new_session=True, env=dict(os.environ, PYTHONUNBUFFERED='1', PYTHONDONTWRITEBYTECODE='1'))
            record['pid'] = process.pid
            record_path.write_text(json.dumps(record, indent=2) + '\n')
            record['exit_code'] = process.wait(timeout=args.timeout)
            record['status'] = 'executed' if record['exit_code'] == 0 else 'failed'
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            record.update(status='timed_out', timeout_seconds=args.timeout)
        except OSError as exc:
            record.update(status='spawn_failed', exit_code=127, error_type=type(exc).__name__)
    record['elapsed_seconds'] = time.monotonic() - started
    record['source_dirty_after'] = subprocess.check_output(
        ['git', '-C', str(source), 'status', '--porcelain'], text=True).strip()
    for path in sorted(args.output.rglob('*')):
        if path.is_file() and path != record_path:
            record['artifacts'][path.relative_to(args.output).as_posix()] = {
                'sha256': sha256(path), 'bytes': path.stat().st_size,
            }
    for path in args.artifact:
        if not path.is_file():
            record.setdefault('missing_artifacts', []).append(str(path.resolve()))
        else:
            record['artifacts'][str(path.resolve())] = {'sha256': sha256(path), 'bytes': path.stat().st_size}
    if record.get('missing_artifacts') and record['status'] == 'executed':
        record['status'] = 'missing_artifacts'
        record['exit_code'] = 125
    record_path.write_text(json.dumps(record, indent=2) + '\n')
    print(f"{args.method}: {record['status']} -> {record_path}", flush=True)
    return record['exit_code'] if record['exit_code'] is not None else 124


if __name__ == '__main__':
    raise SystemExit(main())
