#!/usr/bin/env bash
# AdaM_MCL reproduction harness -- step 3: released DSOM training entry point.
#
#   python Main.py --operation train --dataset simulation --subdataset 2 ...
#
# The released default (cfg.DSOM_training_iters = 7200*4 iterations per epoch,
# 100 epochs) needs 23 million generated samples; we pass explicit iteration
# counts instead, which the released CLI accepts.
set -euo pipefail
export PYTHONUNBUFFERED=1

CODE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="${ADAM_PYTHON:-$HOME/.venvs/adam-mcl/bin/python}"
ITERS="${ADAM_TRAIN_ITERS_PER_EPOCH:-64}"
EPOCHS="${ADAM_TRAIN_EPOCHS:-51}"
DEVICE="${ADAM_TRAIN_DEVICE:-cuda}"

cd "$CODE_DIR"
# --save_per_x_epoch and --val_per_x_iters are NOT passed: Main.py forwards them
# to train() without int(), so argparse's str breaks `epoch % save_per_x_epoch`.
"$PY" Main.py --operation train --dataset simulation --subdataset 2 \
  --device "$DEVICE" \
  --num_epochs "$EPOCHS" \
  --num_iters_per_epoch_train "$ITERS" \
  --num_iters_per_epoch_val 4
