#!/usr/bin/env bash
# AdaM_MCL reproduction harness -- step 1: authored input layout + released generator.
#
# Everything here is a wrapper around the released upstream commands; the only
# upstream-file changes are the ones captured in repro/compatibility.patch.
set -euo pipefail

CODE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="${ADAM_PYTHON:-$HOME/.venvs/adam-mcl/bin/python}"
GEN_SAMPLES="${ADAM_GEN_SAMPLES_PER_SUBSET:-4000}"

cd "$CODE_DIR"

echo "== 1. author the simulation layouts the released generator expects =="
"$PY" repro/make_maps.py --maps 21

echo
echo "== 2. create the output directories the released generator writes into =="
for subset in train val; do
  for kind in scan pmap map rotation; do
    mkdir -p "../Dataset/simulation/Data_Transformed/2/$subset/$kind"
  done
done

echo
echo "== 3. run the released RS-2020 generator (bounded to $GEN_SAMPLES samples per subset) =="
echo "   upstream bug: Data_processor/synthetic_dataset.py calls sys.exit() after the"
echo "   first scan, so an unpatched checkout emits exactly one sample; see compatibility.patch"
cd Data_processor
ADAM_GEN_SAMPLES_PER_SUBSET="$GEN_SAMPLES" "$PY" synthetic_dataset.py
cd "$CODE_DIR"

echo
echo "== 4. generated sample counts =="
for subset in train val; do
  printf '%-6s scans=%s pmaps=%s maps=%s rotations=%s\n' "$subset" \
    "$(find "../Dataset/simulation/Data_Transformed/2/$subset/scan" -name '*.png' | wc -l)" \
    "$(find "../Dataset/simulation/Data_Transformed/2/$subset/pmap" -name '*.png' | wc -l)" \
    "$(find "../Dataset/simulation/Data_Transformed/2/$subset/map" -name '*.png' | wc -l)" \
    "$(find "../Dataset/simulation/Data_Transformed/2/$subset/rotation" -name '*.txt' | wc -l)"
done
