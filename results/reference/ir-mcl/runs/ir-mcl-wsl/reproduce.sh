#!/usr/bin/env bash
# IR-MCL end-to-end reproduction: native-config global localization on the released
# IPBLab sequence, then the upstream GIF export. Everything below is measured live.
#
#   upstream   : https://github.com/PRBonn/ir-mcl  @ aab8c91b37e59f94442d8eddfa2f920ab1ecc4c5
#   entry point: main.py --config_file ./config/global_localization/loc_config_test1.yml
#   patch      : runs/ir-mcl-wsl/compatibility.patch (two source lines)
#   build fix  : the C++ extension is compiled against the environment's own pybind11
#                (>= 2.12, NumPy-2 aware) instead of the distribution's pybind11 2.9.1
#
# Override IR_MCL_ROOT / IR_MCL_DELIVERY / IR_MCL_VENV to relocate.
set -euo pipefail

IR_MCL_ROOT=${IR_MCL_ROOT:-/mnt/d/workspace/be2/tmp/repro/ir-mcl}
IR_MCL_DELIVERY=${IR_MCL_DELIVERY:-/mnt/d/workspace/be2/slam_learning_updated/results/reference/ir-mcl}
VENV=${IR_MCL_VENV:-$HOME/.venvs/ir-mcl}
PY="$VENV/bin/python"
RUN_DIR="$IR_MCL_DELIVERY/runs/ir-mcl-wsl"
LOG="$RUN_DIR/run.log"

export PYTHONPATH="$IR_MCL_ROOT/mcl/srrg_utils:$IR_MCL_ROOT/mcl"
export MPLBACKEND=Agg
mkdir -p "$IR_MCL_DELIVERY/media/replay" "$RUN_DIR"
cd "$IR_MCL_ROOT"
: > "$LOG"

say() { echo "$@" | tee -a "$LOG"; }

say "=== IR-MCL reproduction ==="
say "started          : $(date -Is)"
say "upstream         : $(git config --get remote.origin.url) @ $(git rev-parse HEAD)"
say "working copy     : $IR_MCL_ROOT"
say "delivery         : $IR_MCL_DELIVERY"
say "python           : $("$PY" -V 2>&1)"

say ""
say "--- environment (the versions this run actually used) ---"
"$PY" - <<'PYEOF' 2>&1 | tee -a "$LOG"
import platform
import evo, matplotlib, numpy, pybind11, pytorch_lightning, scipy, torch
print(f"python               : {platform.python_version()} ({platform.system()} {platform.release()}, glibc {platform.libc_ver()[1]})")
print(f"numpy                : {numpy.__version__}")
print(f"torch                : {torch.__version__} (cuda {torch.version.cuda}, available {torch.cuda.is_available()})")
print(f"gpu                  : {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'cpu'}")
print(f"pytorch-lightning    : {pytorch_lightning.__version__}")
print(f"evo                  : {evo.__version__}")
print(f"scipy / matplotlib   : {scipy.__version__} / {matplotlib.__version__}")
print(f"pybind11 (build time): {pybind11.__version__}")
PYEOF

say ""
say "--- compiled particle-filter extension ---"
say "note: CMake's find_package(pybind11) prefers the distribution's pybind11 2.9.1,"
say "      which predates NumPy 2 and misreads PyArray_Descr; the extension is therefore"
say "      rebuilt with -Dpybind11_DIR pointing at this environment's own pybind11."
say "extension sha256 : $(sha256sum mcl/srrg_utils/pf_library/pybind/pf_library_pybind.cpython-310-x86_64-linux-gnu.so | cut -d' ' -f1)"
say "extension size   : $(stat -c%s mcl/srrg_utils/pf_library/pybind/pf_library_pybind.cpython-310-x86_64-linux-gnu.so) bytes"

say ""
say "=== stage 1/2: global localization (native config, 100000 particles) ==="
S1=$(date +%s)
"$PY" -u main.py --config_file ./config/global_localization/loc_config_test1.yml 2>&1 | tee -a "$LOG"
S2=$(date +%s)
say "stage 1 wall time: $((S2 - S1)) s"

say ""
say "=== stage 2/2: GIF export with the upstream loc_demo.py ==="
S3=$(date +%s)
"$PY" -u loc_demo.py \
    --loc_results results/ipblab/loc_test/test1/loc_results.npz \
    --occ_map data/ipblab/occmap.npy \
    --map_size -15 17.5 -12.5 5 \
    --output_gif "$IR_MCL_DELIVERY/media/preview.gif" 2>&1 | tee -a "$LOG"
S4=$(date +%s)
say "stage 2 wall time: $((S4 - S3)) s"

say ""
say "=== artifacts ==="
for f in \
    "$IR_MCL_DELIVERY/media/preview.gif" \
    results/ipblab/loc_test/test1/loc_results.npz \
    results/ipblab/loc_test/test1/IRMCL.txt ; do
    if [ -f "$f" ]; then
        say "$(sha256sum "$f" | cut -d' ' -f1)  $(stat -c%s "$f") bytes  $f"
    else
        say "MISSING $f"
    fi
done
say "finished         : $(date -Is)"
