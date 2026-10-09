#!/usr/bin/env bash
set -euo pipefail
STUDY_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$STUDY_ROOT"
command -v uv >/dev/null || { echo 'Install uv and run setup_linux.sh first.' >&2; exit 1; }
if [ ! -d .venv-semantic ]; then uv venv .venv-semantic --python 3.10.12; fi
# Earlier setup attempts may have installed both OpenCV distributions, which share files.
uv pip uninstall --python .venv-semantic/bin/python opencv-python-headless opencv-python
uv pip install --python .venv-semantic/bin/python -r src/configs/environments/semantic/requirements.txt --extra-index-url https://download.pytorch.org/whl/cu118 --index-strategy unsafe-best-match
src/.venv/bin/python - <<'PY'
import json, subprocess
from pathlib import Path
config=json.loads(Path('src/configs/semantic.json').read_text())
for name,spec in config['upstreams'].items():
    path=Path('.cache/upstream') / name
    if not path.exists(): subprocess.run(['git','clone',spec['url'],str(path)],check=True)
    status=subprocess.check_output(['git','-C',str(path),'status','--porcelain'],text=True).strip()
    if status: raise ValueError(f'Refuse to reset changed upstream {name}')
    subprocess.run(['git','-C',str(path),'checkout','--detach',spec['commit']],check=True)
PY
uv pip install --python .venv-semantic/bin/python --no-deps -e .cache/upstream/gradslam -e .cache/upstream/conceptgraphs
src/.venv/bin/python src/scripts/setup/install_semantic_binary.py
src/.venv/bin/python src/scripts/methods/fetch_replica_subset.py
.venv-semantic/bin/python - <<'PY'
import json, subprocess
from pathlib import Path
config=json.loads(Path('src/configs/semantic.json').read_text())
for weight in config['weights']:
    directory=Path('.cache/semantic-weights') / weight['local'].split('/')[0]
    subprocess.run(['.venv-semantic/bin/hf','download',weight['repo'],weight['filename'],
                    '--revision',weight['revision'],'--local-dir',str(directory)],check=True)
import torch
import conceptgraph.slam.mapping
if not torch.cuda.is_available(): raise RuntimeError('CUDA unavailable in semantic environment')
print('Semantic environment ready:',torch.__version__,torch.cuda.get_device_name(0))
PY
echo 'Run: .venv-semantic/bin/python src/scripts/methods/run_conceptgraphs.py'
