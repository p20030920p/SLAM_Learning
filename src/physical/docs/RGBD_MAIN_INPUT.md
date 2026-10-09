# Real RGB-D native-input checks

English | [中文](RGBD_MAIN_INPUT.zh-CN.md)

Both ConceptGraphs and HOV-SG native loaders passed 8/8 real D435 frames. This is CPU input/geometry validation; no hardware SAM/CLIP, object fusion or text query ran.

## 1. Fixed input

Source: `data/live-camera-20261009-014327-492/raw.db3`, about 3–10 s, eight observations. The operator declared the camera fixed; the complete recording has dynamic background and is not a clean-static acceptance session.

SDK `rs.align(color)` aligns depth to RGB and uses RGB intrinsics. Depth remains uint16 with about 0.0010000000475 m/unit; author scale is its inverse, about 1000. Zero stays invalid. PNG originals remain; required JPEG views use quality 95.

`replica-layout` names a file layout, not the dataset. `T_world_color=I` follows the fixed-camera declaration, with optical x-right/y-down/z-forward in metres; it is not an estimated or independent GT trajectory. Paired RGB/depth offsets are 9.14–9.61 ms, not proven hardware synchronization.

## 2. Rerun and next stage

Use new output names. Export from Windows, enter WSL, then run both frozen native loaders; expect `loader_check_passed`, eight frames. Do not assign identity poses to moving footage. [Numeric evidence](../evidence/rgbd-main-input-and-l2-independent-20261009.json).

Next, freeze masks/features, execute semantic cores when resources permit, annotate real instances and query candidates, then test measured object motion. Loader success is not semantic accuracy. [Test plan](TEST_PLAN.md).

## 3. Historical L2 failure

A ROS-independent 10.04 s UART check received only 32 bytes, zero packets/points. It did not identify power/wiring/device state as the unique cause. Later [post-fall/low-light checks](POSTFALL_LOWLIGHT.md) recovered streaming; the failure record remains unchanged.

Same-recording RGB-D performance tests are separate odometry evidence. [Replay](OFFLINE_REPLAY.md). Raw indoor data stays local; main is untouched.

## 4. Commands

Use the shell shown by each block. Keep the order, use new output names, and check whether the task has already run before starting it.

```powershell
D:\workspace\be2\Personal-Learning-Physical\.venv\Scripts\python.exe D:\workspace\be2\Personal-Learning-Physical\scripts\export_rgbd.py D:\workspace\be2\Personal-Learning-Physical\data\live-camera-20261009-014327-492\raw.db3 --fixed-sensor-session --frames 8 --output D:\workspace\be2\Personal-Learning-Physical\data\manual-rgbd-input-01
```

```powershell
wsl -d Ubuntu-22.04
```

```bash
cd /mnt/d/workspace/be2/Personal-Learning-Physical
```

```bash
CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 /home/qzl/projects/SLAM_Learning/.venv-semantic/bin/python scripts/check_main_rgbd.py data/manual-rgbd-input-01 --method conceptgraphs --main-repo /mnt/d/workspace/be2/SLAM_Learning --runtime /home/qzl/projects/SLAM_Learning --output data/manual-rgbd-input-01/check-conceptgraphs
```

```bash
CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 /home/qzl/projects/SLAM_Learning/.venv-hovsg/bin/python scripts/check_main_rgbd.py data/manual-rgbd-input-01 --method hovsg --main-repo /mnt/d/workspace/be2/SLAM_Learning --runtime /home/qzl/projects/SLAM_Learning --output data/manual-rgbd-input-01/check-hovsg
```
