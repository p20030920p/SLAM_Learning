# Mapping-core inputs and future integration

English | [中文](MAIN_INTEGRATION.zh-CN.md)

Baseline main is `354b02d69ccc90304174f6d36010d25043d739ca`. Its mapping cores consume supplied poses; plugging in a sensor does not create a trajectory-estimating SLAM system.

## 1. Input contract

Record device/firmware/source commits, raw hashes, calibration, units/frames, timestamps, pose source, events and failures. Align depth to the chosen color camera using SDK calibration; retain invalid pixels and original files. Keep L2 raw UART, verified geometry and truthful point time/ring conventions.

Identity poses are allowed only for a genuinely fixed session explicitly declared by the operator. Moving sessions need a validated pose source. Independent references remain evaluation inputs.

## 2. Executed adapters

DUFOMap processed 40 fixed real observations. Original BeautyMap hit a small-map boundary error; a separate padding control processes 40/40, but full boundary/KITTI regression remains open. Neither establishes SA/DA without labels.

Real RGB-D export and both native semantic loaders passed 8/8 frames. SAM/CLIP, object mapping and queries have not run. [RGB-D input](RGBD_MAIN_INPUT.md). Main and author caches remain unchanged.

## 3. Controlled experiments

Use static, occluded, removed-visible and 30 cm moved events. Each lasts 80 s; record actual action times. Use ≥3 validation and ≥5 independent test sessions per class after freezing settings. Sessions, not points, are the statistical units.

Measure mapping quality and query/identity recovery separately from trajectory quality. Future late-correction tests must freeze observations/frontends and distinguish coordinate correction, reassociation and full replay. Proposed replay is not already implemented.

## 4. Merge gate

Select reusable hardware modules, branch from clean main in an independent worktree, run original KITTI/Replica and hardware regressions, review the PR, then obtain explicit owner approval. This orphan branch must not be merged wholesale. The commands below are adapter/review recipes, not authorization to merge. [Full interface and gates](MAIN_INTEGRATION.zh-CN.md).

## 5. Commands

Use the shell shown by each block. Keep the order, use new output names, and check whether the task has already run before starting it.

```powershell
wsl -d Ubuntu-22.04
```

```bash
cd /mnt/d/workspace/be2/Personal-Learning-Physical
```

```bash
OPENBLAS_NUM_THREADS=2 /home/qzl/projects/SLAM_Learning/.venv/bin/python scripts/run_main_dufomap.py data/l2-official-static-50 --main-repo /mnt/d/workspace/be2/SLAM_Learning --fixed-sensor-session --output data/manual-dufomap-01
```

```bash
python3 scripts/render_dufomap_smoke.py data/manual-dufomap-01
```

```bash
OPENBLAS_NUM_THREADS=2 /home/qzl/projects/SLAM_Learning/.venv/bin/python scripts/run_main_beautymap.py data/manual-dufomap-01 --main-repo /mnt/d/workspace/be2/SLAM_Learning --upstream /home/qzl/projects/SLAM_Learning/.cache/upstream/beautymap --fixed-sensor-session --output data/manual-beautymap-original-01
```

```bash
OPENBLAS_NUM_THREADS=2 /home/qzl/projects/SLAM_Learning/.venv/bin/python scripts/run_main_beautymap.py data/manual-dufomap-01 --main-repo /mnt/d/workspace/be2/SLAM_Learning --upstream /home/qzl/projects/SLAM_Learning/.cache/upstream/beautymap --fixed-sensor-session --pad-small-map-control --output data/manual-beautymap-control-01
```

```bash
python3 scripts/render_dufomap_smoke.py data/manual-beautymap-control-01
```

```powershell
git -C D:\workspace\be2\SLAM_Learning worktree add -b integrate/physical-sensors D:\workspace\be2\Physical-Integration main
# 在新工作树内导入审核通过的 hardware/ 模块和轻量证据。
# 按主分支 docs/REPRODUCE.zh-CN.md 执行测试与证据检查。
# 审阅 diff、创建 PR，等待用户决定是否合并。
```
