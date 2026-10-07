#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
# Shared pinned dataset/checkpoints; independent installed distributions.
bash scripts/setup_semantic.sh
if [ ! -d .venv-hovsg ]; then
  uv venv .venv-hovsg --python 3.10.12
fi
uv pip install --python .venv-hovsg/bin/python --extra-index-url https://download.pytorch.org/whl/cu118 \
  --index-strategy unsafe-best-match -r environments/hovsg/requirements.txt
if [ ! -d .cache/upstream/hovsg/.git ]; then
  git clone https://github.com/hovsg/HOV-SG.git .cache/upstream/hovsg
fi
git -C .cache/upstream/hovsg checkout d6e65a53c8be6faec3f01f00d1644d967f89e605
uv pip install --python .venv-hovsg/bin/python --no-deps --editable .cache/upstream/hovsg
.venv-hovsg/bin/python -c 'from hovsg.graph.graph import Graph; import torch; assert torch.cuda.is_available(); print("HOV-SG import and CUDA available")'
