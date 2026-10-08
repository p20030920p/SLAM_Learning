# Manually reproduce the cores and record the graphical side

English | [中文](MANUAL_RECORDING.zh-CN.md) | [Index](README.md)

This is a personal-branch runbook. Research conclusions are in [STUDY](../docs/STUDY.md); hardware steps in [HOME_RUNBOOK](HOME_RUNBOOK.md).

## What the existing videos show

| Media | Actual content | Evidential scope |
| --- | --- | --- |
| Original four full-session MP4s | Real private Xvfb xterm/PTY from command start to exit0, monotonic-clock capture at5fps | Commands completed; no 3D GUI or throughput benchmark |
| Homepage GIFs/short map videos | Python display of saved final maps and queries | Measured outputs, not live inference |
| RViz clips | Actual RViz showing saved native clouds, ConceptGraphs snapshots, query candidates and observations | Graphical inspection; mapper inference was not rerun during recording |

Terminal originals: `D:\workspace\be2\SLAM_Recordings\2026-10-08\VIDEO_INDEX.md`. Graphical originals: `D:\workspace\be2\SLAM_Recordings\2026-10-08\rviz-review-v3\VIDEO_INDEX.md`.

The original pipeline had no Gazebo scene and no automatic RViz publisher. Gazebo is a simulator; a newly invented scene would not reproduce these recorded papers. The added RViz viewer inspects real saved outputs.

## Native execution

From **PowerShell**, `wsl -d Ubuntu-22.04 -u qzl`; then **WSL Bash**, run individually:

```bash
cd /home/qzl/projects/SLAM_Learning
git status --short
nvidia-smi
.venv/bin/python -m slam_learning.cli run --method dufomap
.venv/bin/python -m slam_learning.cli run --method beautymap
.venv-semantic/bin/python scripts/run_conceptgraphs.py
.venv-hovsg/bin/python scripts/run_hovsg.py
```

Keep each fresh run path. Watch its actual log from another terminal; verify exit/status, scope and outputs. Do not overwrite paired v1. ConceptGraphs40 and HOV-SG8 are supplied-pose subsets, not complete SLAM/navigation. See [Windows steps](WINDOWS_START.md) for exit codes and artifact checks.

## Inspect saved maps

The [Windows guide](WINDOWS_START.md) gives a complete two-terminal ConceptGraphs RViz workflow using an existing audited baseline. Preparation uses each method's Python; ROS publication uses system Python after Humble setup, with both terminals on ROS domain71/local-only.

Other preparation commands, **WSL Bash**:

```bash
.venv-hovsg/bin/python scripts/prepare_visual_review.py hovsg \
  results/runs/hovsg-0206da9f0145/record.json --output results/runs/my-hov-visual-01
.venv/bin/python scripts/prepare_visual_review.py dufomap \
  results/runs/evaluation-check-6489fe584ba2/record.json \
  --dataset .cache/datasets/00 --output results/runs/my-dufo-visual-01
.venv/bin/python scripts/prepare_visual_review.py beautymap \
  results/runs/evaluation-check-6489fe584ba2/record.json \
  --dataset .cache/datasets/00 --output results/runs/my-beauty-visual-01
```

Use the matching existing config under `rviz-review-v3/METHOD/data/review.rviz`, then publish the corresponding new manifest with `--seconds-per-step 10 --cycles 0`. Rotate/zoom and pause for inspection. Replica's `(x,y,z)→(x,z,-y)` conversion is display-only.

LiDAR displays the same sampled points from21 selected scans, classified by the final-map PCL evaluator; full scores use141 scans. HOV-SG has no available incremental map history here: it displays the final segments and query changes. ConceptGraphs uses actual historical snapshots plus final queries.

For a fresh semantic run, use its own complete `record.json`. For fresh LiDAR maps, first create a new `slam-study cross-check` record for those maps; never bind an old evaluator to a new run. Exact arguments are in the command help and the [Windows guide](WINDOWS_START.md).

Replace both placeholders with your new complete run records, **WSL Bash**:

```bash
.venv/bin/python -m slam_learning.cli cross-check \
  results/runs/YOUR_DUFO_RUN/record.json \
  results/runs/YOUR_BEAUTY_RUN/record.json
```

Pass its new printed `evaluation-check-.../record.json` to LiDAR visual preparation. Semantic preparation takes your own complete native record directly.

## Your manual recording

Use a familiar recorder. OBS is optional and was not found in common installation locations during preparation; that is not a complete installed-app inventory. Start with a ten-second clip and replay it to check WSLg capture and text.

Suggested output:1920×1080,30fps,H.264, or1280×720 if needed. Give about70% of the frame to RViz/RGB-D/3D,20% to observation/query/event labels, and a small area to commands. Playback speed is not algorithm FPS.

1. Record the fresh command, directory, real log, exit and artifacts. Keep an uncut original; label edits in shorter presentations.
2. Announce that saved outputs are now being inspected. Open the graphical window, rotate/zoom and point out static loss/dynamic leakage or semantic/coordinate errors.
3. Compare audited zero-error/shuffled/drift cells at fixed view and colors. Explain that drift is not always worse. Threshold tuning is not H1.

Bind graphics to the actual source run. The viewer does not update while the mapper is inferring; live snapshot watching would require another interface.

## How automated GUI capture worked

`prepare_visual_review.py` verifies local records, reads measured outputs, deterministically thins display points and binds source hashes; ConceptGraphs snapshot poses are checked. `view_measured_rviz.py` publishes PointCloud2 and opens a source/observation panel. `record_visual_review.sh` opens RViz on `record_session.py`'s private Xvfb screen, so the right-hand graphical window is captured without recording the user's desktop.

Software OpenGL avoids CUDA competition. Full videos were decoded and graphical stages inspected, with duration/status checks. Failed/debug v1/v2 material remains local and is excluded from the final index. This does not constitute independent human scientific review.

To reuse automated GUI capture after preparing `my-cg-visual-01`, close other domain71 viewers, then run in **WSL Bash**:

```bash
.venv/bin/python scripts/record_session.py \
  --output /mnt/d/workspace/be2/SLAM_Recordings/2026-10-08/manual-cg-review-01 \
  --cwd /home/qzl/projects/SLAM_Learning --fps 5 -- \
  bash scripts/record_visual_review.sh results/runs/my-cg-visual-01/manifest.json
```

The output directory must not exist. Open its `full-session.mp4` afterwards. This captures automatically opened RViz on a private X screen. Use the manual desktop-recording route to capture your own mouse interaction.

Keep concise research evidence on main, operational guides here, and full recordings/raw home captures locally. Older local snapshots are on `local/full-notes-20261008`; historical copies are under `D:\workspace\be2\SLAM_Private\2026-10-08\original-docs`.
