#!/usr/bin/env bash
# Rebuild preview.gif + timing.json from the published recording.
set -euo pipefail
CODE=/mnt/d/workspace/be2/tmp/repro/AdaM_MCL/code
REPO=/mnt/d/workspace/be2/slam_learning_updated
REF=$REPO/results/reference/adam-mcl
cd "$CODE"
"$HOME/.venvs/adam-mcl/bin/python" repro/make_preview.py \
  --reference "$REF" \
  --crop crop=700:782:0:0 \
  --scale-width 640 \
  --colors 32 \
  --interval 8.5:6 \
  --interval 31.5:6 \
  --record "$REF/runs/adam-mcl-wsl/record.json" \
  --record-label results/reference/adam-mcl/runs/adam-mcl-wsl/record.json
"$HOME/.venvs/adam-mcl/bin/python" repro/publish_evidence.py --repo "$REPO" index
