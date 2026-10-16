#!/usr/bin/env bash
set -eo pipefail
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=178
[[ "$1" == dynamic ]] && export ROS_DOMAIN_ID=179
export GALLIUM_DRIVER=d3d12 MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA QT_QPA_PLATFORM=xcb DISPLAY=:0
unset LIBGL_ALWAYS_SOFTWARE MESA_GL_VERSION_OVERRIDE QT_QPA_PLATFORM_PLUGIN_PATH
exec python3 -u "$(dirname "$0")/h1_replay_a.py" "$@"
