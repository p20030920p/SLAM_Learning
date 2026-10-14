#!/usr/bin/env bash
# AdaM_MCL reproduction harness -- record the complete evaluation session.
#
# src/scripts/media/record_session.py opens its own authenticated X server on a
# free TCP port (never the user's :0, and not a fixed :98/:99 that another
# recording could already own), runs the command through a real PTY in xterm and
# encodes the whole session live with ffmpeg at the requested frame rate.
set -euo pipefail

CODE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_DIR="${ADAM_REPO:-/mnt/d/workspace/be2/slam_learning_updated}"
PY="${ADAM_PYTHON:-$HOME/.venvs/adam-mcl/bin/python}"
TRIALS="${ADAM_TRIALS:-10}"
OUT="${ADAM_RECORD_OUT:-$REPO_DIR/results/reference/adam-mcl/media/replay}"

MODEL="${ADAM_MODEL:-}"
if [ -z "$MODEL" ]; then
  MODEL="$(ls -t "$CODE_DIR"/../Trained_models/simulation_2_*/model_train_*epochs.pth | head -1)"
fi
export ADAM_MODEL="$MODEL"
export ADAM_TRIALS="$TRIALS"
export ADAM_OUT="${ADAM_OUT:-/mnt/d/workspace/be2/tmp/repro/adam-logs}"

rm -rf "$CODE_DIR/logs4MCL"
rm -rf "$OUT"
cd "$REPO_DIR"
exec nice -n 5 "$PY" src/scripts/media/record_session.py \
  --output "$OUT" \
  --cwd "$REPO_DIR" \
  --fps "${ADAM_FPS:-12}" \
  -- bash "$CODE_DIR/repro/run_session.sh"
