#!/usr/bin/env bash
set -eo pipefail
SCENE="${1:?usage: build_maps.sh static|dynamic}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../../.." && pwd)"
PYTHON_BIN=/home/qzl/projects/SLAM_Author_Originals/envs/lidar/bin/python
export PYTHONPATH=/mnt/d/workspace/be2/SLAM-Physical/src
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2
SOURCE_RUN="$(python3 - "$REPO/.cache/presentation/mapping-$SCENE-latest.json" <<'PY'
import json,subprocess,sys
path=json.load(open(sys.argv[1]))['path']
print(subprocess.check_output(['wslpath','-u',path],text=True).strip() if ':' in path else path)
PY
)"
MAPS="$SOURCE_RUN/author-maps-$(date +%Y%m%d-%H%M%S)"
echo "EXECUTING: native DUFOMap + BeautyMap on $SOURCE_RUN/mapping-clouds.npz"
"$PYTHON_BIN" -u "$HERE/build_maps.py" --recording "$SOURCE_RUN" --output "$MAPS" \
  2>&1 | tee "$SOURCE_RUN/author-maps.log"
python3 - "$REPO/.cache/presentation/maps-$SCENE-latest.json" "$MAPS" <<'PY'
import json,sys
from pathlib import Path
Path(sys.argv[1]).write_text(json.dumps({'path':sys.argv[2]},indent=2)+'\n')
PY
echo "MAPS READY: $MAPS"
