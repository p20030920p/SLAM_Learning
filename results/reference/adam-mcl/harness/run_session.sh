#!/usr/bin/env bash
# AdaM_MCL reproduction harness -- step 4: the recorded evaluation session.
#
# Runs the released global-localization / kidnapping evaluation entry point
# (Main.py --operation test_MCL) through a live dashboard of the released
# program's own output. Nothing is re-implemented: the child process is the
# released Main.py and its complete stdout is preserved by repro/live_eval.py.
set -euo pipefail

CODE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_DIR="${ADAM_REPO:-/mnt/d/workspace/be2/slam_learning_updated}"
PY="${ADAM_PYTHON:-$HOME/.venvs/adam-mcl/bin/python}"
TRIALS="${ADAM_TRIALS:-10}"
SUBDATASET="${ADAM_SUBDATASET:-0}"
PARTICLES="${ADAM_PARTICLES:-200}"
MODEL="${ADAM_MODEL:?set ADAM_MODEL to a trained DSOM checkpoint}"
OUT="${ADAM_OUT:-/mnt/d/workspace/be2/tmp/repro/adam-logs}"

mkdir -p "$OUT"
cd "$CODE_DIR"

echo "AdaM_MCL (RA-L 2021, DOI 10.1109/LRA.2021.3061339) reproduction session"
echo "upstream commit: $(git -C "$CODE_DIR/.." rev-parse HEAD)"
echo "python: $("$PY" -V 2>&1)"
"$PY" - <<'PYCODE'
import torch
print("torch", torch.__version__, "cuda", torch.cuda.is_available(),
      torch.cuda.get_device_name(0) if torch.cuda.is_available() else "")
PYCODE
echo "compatibility patch applied to the upstream checkout:"
git -C "$CODE_DIR/.." --no-pager diff --stat | sed 's/^/  /'
echo "dataset: Dataset/simulation, $(find ../Dataset/simulation/Data_Transformed/2/train/scan -name '*.png' | wc -l) authored training scans"
echo "evaluation sequence: Dataset/simulation/Data_Transformed/Test_MCL/$SUBDATASET, $(wc -l < "../Dataset/simulation/Data_Transformed/Test_MCL/$SUBDATASET/gt_pose.txt") frames"
echo "checkpoint: $MODEL"
echo "particles: $PARTICLES   trust threshold w_cut: 0.6   trials: $TRIALS"
echo

"$PY" repro/live_eval.py \
  --python "$PY" \
  --subdataset "$SUBDATASET" \
  --particles "$PARTICLES" \
  --model "$MODEL" \
  --trials "$TRIALS" \
  --log "$OUT/eval-full-output.log"

echo
echo "complete released output: $OUT/eval-full-output.log"
echo "per-trial logs: $CODE_DIR/logs4MCL/simulation/$SUBDATASET/"
