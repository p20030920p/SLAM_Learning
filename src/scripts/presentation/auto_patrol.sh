#!/usr/bin/env bash
set -eo pipefail
RUN_DIR="${1:?output directory required}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
while [[ ! -f "$RUN_DIR/recording.started" ]]; do sleep 0.2; done
SCENE="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["scene"])' "$RUN_DIR/runtime.json")"
if [[ "$SCENE" == corridor ]]; then
  CORRIDOR_ROUTE='9.15,-3.1;5.15,-3.1;9.15,-3.1;5.15,-3.1;9.15,-3.1;5.15,-3.1;9.15,-3.1;5.15,-3.1;9.15,-3.1;5.15,-3.1'
  exec python3 "$HERE/patrol_waypoints.py" \
    --ros-args -p use_sim_time:=true -p speed:=0.30 -p hold:=1.0 \
    -p "waypoints:=$CORRIDOR_ROUTE" \
    -p origin_x:=7.15 -p origin_y:=-3.1 -p origin_yaw:=0.0
fi
exec python3 "$HERE/patrol_waypoints.py" \
  --ros-args -p use_sim_time:=true -p speed:=0.30 -p hold:=1.0 \
  -p 'waypoints:=8.5,7.6;5.3,7.6;5.3,6.5;8.2,6.5;8.2,5.2;9.7,5.2;9.7,4.2;6.7,4.2' \
  -p origin_x:=8.0727 -p origin_y:=7.5312 -p origin_yaw:=-1.5708
