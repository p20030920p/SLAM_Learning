#!/usr/bin/env bash
set -eo pipefail
METHOD="${1:?method}"; RUN="${2:?fresh run directory}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p "$RUN"
export MPLBACKEND=Agg PYTHONUNBUFFERED=1
export ADAM_TRIALS="${3:-10}"
if [[ "${4:-false}" == true ]]; then export SLAM_AUTHOR_LIVE="$RUN/live"; fi
python=/home/qzl/projects/SLAM_Learning/.venv/bin/python
[[ "$METHOD" == ir-mcl ]] && python=/home/qzl/.venvs/ir-mcl/bin/python
[[ "$METHOD" == adam-mcl ]] && python=/home/qzl/.venvs/adam-mcl/bin/python
"$python" -u "$HERE/run_original.py" "$METHOD" "$RUN" | tee "$RUN/terminal.log"
echo "Native run finished. This terminal contains the actual author's output."
for attempt in $(seq 1 600); do
  [[ -f "$RUN/capture.finished" ]] && break
  printf 'RECORDER WAIT: native execution finished; waiting for video encoder (%s)\r' "$attempt"
  sleep 0.2
done
