# Open the guides, run methods and inspect results from Windows

English | [中文](WINDOWS_START.zh-CN.md) | [Index](README.md)

Runtime commands below refer to the retained older WSL checkout, which was not migrated here. For this branch’s current `src/` layout and a new environment, follow [Setup](../guides/REPRODUCE.md).

These instructions target **this already configured machine**. Windows handles reading, recording and devices; author methods run inside WSL Ubuntu-22.04. Copy each block only into its labeled shell.

## 1. Open the guide branch

Open Windows Terminal with a **PowerShell** tab:

```powershell
Set-Location 'D:\workspace\be2\SLAM_Personal_Guide'
git branch --show-current
Get-Content -Encoding utf8 .\docs\notes\README.md
explorer.exe 'D:\workspace\be2\SLAM_Personal_Guide\docs\notes'
```

Expect `notes/personal-study-guide-20261008`. GitHub renders `docs/notes/README.md` with clickable links; locally use an available Markdown editor. The separate Windows `SLAM_Learning` checkout stays on main.

## 2. Enter the runtime Ubuntu checkout

**PowerShell:**

```powershell
wsl --list --verbose
wsl -d Ubuntu-22.04 -u qzl
```

The prompt becomes similar to `qzl@...:~$`. Continue in **WSL Bash**:

```bash
cd /home/qzl/projects/SLAM_Learning
pwd
git branch --show-current
git status --short
ls .venv/bin/python .venv-semantic/bin/python .venv-hovsg/bin/python
nvidia-smi
```

All three interpreters should exist. The cached runtime checkout remains on main; this guide branch contains the learning notes and hardware project. Check GPU activity before launching semantic inference and leave other windows' experiments running.

Windows `D:\...` maps to `/mnt/d/...` in WSL. Open Linux files from a second **PowerShell** tab:

```powershell
explorer.exe '\\wsl.localhost\Ubuntu-22.04\home\qzl\projects\SLAM_Learning'
```

VS Code is optional, not a prerequisite.

## 3. Select the right environment

| Interpreter | Purpose |
| --- | --- |
| `.venv/bin/python` | LiDAR, evaluation, paired scheduling, documentation checks |
| `.venv-semantic/bin/python` | ConceptGraphs and its SAM/CLIP frontend |
| `.venv-hovsg/bin/python` | Native HOV-SG core |
| System `python3` after ROS setup | ROS2 publisher and RViz review |

Explicit interpreter paths avoid activation. Do not install the CPU lock into either CUDA environment. Data/weights/author sources are under `.cache/`; fresh outputs go to `results/runs/`.

**WSL Bash, without inference:**

```bash
.venv/bin/python -m slam_learning.cli doctor
.venv/bin/python -m slam_learning.cli --help
```

`doctor` reports CPU environment versions and data presence; it does not validate a full run, semantic weights or hardware connectivity.

## 4. Run native cores serially

Keep `/home/qzl/projects/SLAM_Learning` as the working directory. Finish each run before starting the next:

```bash
# Full 141-scan DUFOMap teaser
.venv/bin/python -m slam_learning.cli run --method dufomap
echo $?

# Full 141-scan BeautyMap teaser
.venv/bin/python -m slam_learning.cli run --method beautymap
echo $?

# Forty supplied-pose ConceptGraphs observations
.venv-semantic/bin/python scripts/run_conceptgraphs.py
echo $?

# Eight supplied-pose HOV-SG observations
.venv-hovsg/bin/python scripts/run_hovsg.py
echo $?
```

Run the blocks individually. `echo $?` must immediately follow the corresponding command. Ordinary exit0 means successful execution, not exact paper agreement. LiDAR `--frames 10` is smoke-only; `--strict-paper` returns2 on a paper-tolerance mismatch.

Record each newly printed run directory. Replace the placeholders below; do not substitute an old result for your run:

```bash
cat results/runs/YOUR_NEW_RUN/record.json
ls -lh results/runs/YOUR_NEW_RUN
tail -n 30 results/runs/YOUR_NEW_RUN/run.log
```

LiDAR uses `run.log`; ConceptGraphs `segmentation.log` and `mapping.log`; HOV-SG `mapping.log`. In a second WSL tab, `cd` to the same root and `tail -f` your actual log. `Ctrl+C` there stops log viewing. Quiet frontend stdout does not imply a stalled run.

| Method | Artifacts to inspect | Checks |
| --- | --- | --- |
| LiDAR | `cleaned.pcd`, `metrics.json`, `worker.json`, log, record | Executed status, exit0, full scope, metric definitions |
| ConceptGraphs | `objects.pkl.gz`, `summary.json`, native snapshots, logs, patch | Forty observations, object count, absolute poses, hashes |
| HOV-SG | `map.ply`, `objects/*.ply`, `segment_features.npy`, summary/config | Eight observations, source indexes, calibration scaling, status |

For a complete local LiDAR record:

```bash
.venv/bin/python -m slam_learning.cli verify results/runs/YOUR_LIDAR_RUN/record.json --full
```

Public `results/reference` contains portable evidence, not complete native maps. Use `--full` only where the actual local artifacts exist.

## 5. Open RViz and inspect the graphical side

The reproduction commands do not automatically open Gazebo/RViz. RViz reviews saved outputs separately. Start with an existing audited ConceptGraphs baseline, **WSL Bash**:

```bash
cd /home/qzl/projects/SLAM_Learning
.venv-semantic/bin/python scripts/prepare_visual_review.py conceptgraphs \
  results/runs/conceptgraphs-7795d7b47007/record.json \
  --output results/runs/my-cg-visual-01
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID=71
export ROS_LOCALHOST_ONLY=1
rviz2 -d /mnt/d/workspace/be2/SLAM_Recordings/2026-10-08/rviz-review-v3/conceptgraphs/data/review.rviz
```

Use a new output name if `my-cg-visual-01` already exists. The final command opens a WSLg window on the Windows desktop. In a second **WSL Bash** tab:

```bash
cd /home/qzl/projects/SLAM_Learning
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID=71
export ROS_LOCALHOST_ONLY=1
python3 scripts/view_measured_rviz.py \
  results/runs/my-cg-visual-01/manifest.json --seconds-per-step 10 --cycles 0
```

Inspect the point cloud and source/stage panel, rotate with the left mouse button and zoom with the wheel. `--cycles 0` loops; stop with `Ctrl+C`, then close RViz. Look for fragments and plausible query highlights.

If the old `.rviz` file has moved, start `rviz2`, set Fixed Frame=`map`, Add PointCloud2 `/study/cloud`, Color Transformer=`RGB8`, and Marker `/study/label`. Adjust the viewpoint after publishing and save your own configuration. See the [recording guide](MANUAL_RECORDING.md) for the other methods and new-output binding.

**PowerShell, existing videos:**

```powershell
explorer.exe 'D:\workspace\be2\SLAM_Recordings\2026-10-08\rviz-review-v3'
```

The [public clips](../media/rviz) have full local `capture/full-session.mp4` originals and a `VIDEO_INDEX.md` in that directory. Viewing needs no new inference.

## 6. Original code and home hardware

Use [the upstream comparison](UPSTREAM_COMPARISON.md) to read fixed READMEs, entry points, patches and run records. Do not edit author caches directly.

For D435/L2, read [the public experimental protocol](../guides/REAL_WORLD.md) and [device runbook](HOME_RUNBOOK.md). Start with fixed-sensor capture/playback. Hardware adapters and H1 remain pending; recording a bag is not hypothesis validation.

## 7. Locate failures

| Symptom | Check |
| --- | --- |
| Missing path/command | `pwd`; use the WSL runtime checkout, not the Windows documentation worktree |
| Missing semantic interpreter | Check the directory before rebuilding an environment |
| Quiet semantic terminal | Inspect that run's logs and GPU activity; do not start duplicate jobs |
| Exit137 | Preserve partial records/logs/resource state; the code alone does not prove CUDA OOM |
| Blank RViz | Both domains71; `ros2 topic list`; `ros2 topic echo /study/cloud --once --field header`; frame/topic/viewpoint |
| Broken/black graphics | Close and restart RViz with `export LIBGL_ALWAYS_SOFTWARE=1`; verify a ten-second recording |
| `--full` missing artifacts | Use the complete local record rather than its portable public copy |
| Paper mismatch | Compare versions, parameters, inputs and scoring; preserve the discrepancy |

## 8. Rebuild only missing components

WSL, three environments, ROS2 Humble/RViz2, data and native baselines were found on this machine on 2026-10-08. Skip installation for normal use. Check local modifications before setup; do not discard them with reset/clean.

**WSL Bash, select only what is missing:**

```bash
uv --version
bash scripts/setup_linux.sh
.venv/bin/python -m slam_learning.cli fetch
bash scripts/setup_semantic.sh
bash scripts/setup_hovsg.sh
```

HOV-SG relies on prepared semantic data/weights. On a genuinely new Windows machine, `wsl --install -d Ubuntu-22.04` in administrator PowerShell follows [Microsoft's installation instructions](https://learn.microsoft.com/windows/wsl/install); reboot/create the account as prompted. A new user/path is not automatically qzl. Install missing uv following [its official guide](https://docs.astral.sh/uv/getting-started/installation/). CUDA, RViz and devices need new-machine verification.
