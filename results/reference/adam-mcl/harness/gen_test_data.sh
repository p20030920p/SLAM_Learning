#!/usr/bin/env bash
# AdaM_MCL reproduction harness -- step 2: released evaluation sequences.
#
# Generate_Path.py plans two A* legs per sequence on
# Dataset/simulation/Data_Transformed/Test_MCL/global_map.png, ray-traces a
# 360-beam scan along each leg, and concatenates the two legs with a zero
# odometry entry at the junction: the pose jumps while the odometry says the
# robot did not move, which is the kidnapping event the paper evaluates.
set -euo pipefail

CODE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="${ADAM_PYTHON:-$HOME/.venvs/adam-mcl/bin/python}"

cd "$CODE_DIR/src"
"$PY" Generate_Path.py

cd "$CODE_DIR"
echo
echo "== released evaluation sequences =="
for sequence in ../Dataset/simulation/Data_Transformed/Test_MCL/*/; do
  [ -f "$sequence/gt_pose.txt" ] || continue
  printf '%-8s frames=%s\n' "$(basename "$sequence")" "$(wc -l < "$sequence/gt_pose.txt")"
done
