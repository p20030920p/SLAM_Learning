"""Create new Linux-native author checkouts without changing existing projects."""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--cache', type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    repositories = json.loads((root / 'src/configs/upstreams.json').read_text())['repositories']
    args.runtime.mkdir(parents=True, exist_ok=True)
    for name, spec in repositories.items():
        target = args.runtime / 'upstream' / name
        if not target.exists():
            target.parent.mkdir(exist_ok=True)
            cached = args.cache / name if args.cache else None
            source = str(cached) if cached and cached.is_dir() else spec['url']
            subprocess.run(['git', 'clone', '--no-hardlinks', source, str(target)], check=True)
            subprocess.run(['git', '-C', str(target), 'remote', 'set-url', 'origin', spec['url']], check=True)
            subprocess.run(['git', '-C', str(target), 'checkout', '--detach', spec['commit']], check=True)
        actual = subprocess.check_output(['git', '-C', str(target), 'rev-parse', 'HEAD'], text=True).strip()
        dirty = subprocess.check_output(['git', '-C', str(target), 'status', '--porcelain'], text=True).strip()
        if actual != spec['commit'] or dirty:
            raise RuntimeError(f'Refusing non-pristine runtime checkout: {target}')
        print(f'{name}: verified {actual}', flush=True)
    (args.runtime / 'workspace.json').write_text(json.dumps({
        'documentation_checkout': str(root), 'repositories': repositories,
        'scope': 'Independent pristine author sources; no results inherited from prior wrappers',
    }, indent=2) + '\n')


if __name__ == '__main__':
    main()
