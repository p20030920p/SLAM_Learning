#!/usr/bin/env bash
set -euo pipefail
runtime=$(realpath "$1")
uv_bin=$(command -v uv || true)
uv_bin=${UV_BIN:-${uv_bin:-"$HOME/.local/bin/uv"}}
"$uv_bin" venv --python /usr/bin/python3 "$runtime/envs/lidar"
"$uv_bin" pip install --python "$runtime/envs/lidar/bin/python" \
  dufomap==1.1.1 numpy==1.26.4 scipy==1.14.1 open3d==0.18.0 \
  matplotlib==3.9.2 tqdm==4.66.5 dztimer==1.1.1 fire==0.7.0 tabulate==0.9.0
"$uv_bin" pip freeze --python "$runtime/envs/lidar/bin/python" > "$runtime/lidar-environment.txt"
