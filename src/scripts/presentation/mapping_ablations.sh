#!/usr/bin/env bash
# Each changes one factor; retain every configuration and do not replace the baseline marker.
set -eo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN="${1:?measured mapping A required}"
PYTHON_BIN=/home/qzl/projects/SLAM_Author_Originals/envs/lidar/bin/python
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2
for name in visibility12 allscans dufo02; do
  options=()
  if [[ "$name" == visibility12 ]]; then options=(--beauty-range 12); fi
  if [[ "$name" == allscans ]]; then options=(--max-scans 0); fi
  if [[ "$name" == dufo02 ]]; then options=(--dufo-resolution .2); fi
  "$PYTHON_BIN" -u "$HERE/build_maps.py" --recording "$RUN" --output "$RUN/ablation-$name" "${options[@]}" \
    > "$RUN/ablation-$name.log" 2>&1
  "$PYTHON_BIN" "$HERE/score_map_labels.py" "$RUN" "$RUN/ablation-$name" \
    > "$RUN/ablation-$name-scores.log" 2>&1
  echo "Completed single-factor map ablation: $name"
done
