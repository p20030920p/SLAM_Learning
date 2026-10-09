# Camera preview and algorithms

English | [中文](CAMERA_GUIDE.zh-CN.md)

The actual SDK model is D435 without IMU. Use Windows PowerShell for the launcher; Bash commands run only after entering WSL. Keep one camera session active at a time.

## 1. Preview and modes

Raw mode displays RGB, aligned depth, IR and the current point cloud; it estimates no trajectory. Stereo uses left/right IR. RGB-D uses aligned color/depth. RGB-D SLAM can publish map updates; map updates do not prove loop closure.

Choose `-Algorithm stereo`, `rgbd` or `rgbd-slam` only after stopping the previous session. `-Record` keeps raw data; `-Video` records an independent RViz view. The recording view and interactive RViz are separate.

## 2. What to inspect

Start with a fixed camera facing textured matte geometry about 1–3 m away. Track actual input rate, valid output coverage, LOST events and excursions. Near objects, screens, weak texture, reflections and dynamic foreground can degrade tracking.

For a declared stationary 60-second test, initial targets are <5 cm translation, <2° rotation and >95% usable tracking. These are project targets, not manufacturer specifications or ATE/RPE. Preserve startup separately. A finite trajectory or LOST=0 alone is insufficient.

## 3. ROS and evidence

Camera domain is 83, localhost-only. Use the matching raw/odom/map RViz configuration. The D435 has no inertial odometry source. Do not invent TF transforms to hide LOST.

Each session retains commands/configuration hashes, raw capture, poses/status and logs. Hardware raw rates, ROS input rate, algorithm compute time and screen-video fps are different quantities. Keep indoor media local. [Test plan](TEST_PLAN.md) · [Latest checks](POSTFALL_LOWLIGHT.md).

The existing preview, algorithm, emitter, topic and RViz commands follow below in original order. [Full display/file reference](CAMERA_GUIDE.zh-CN.md).

## 4. Commands

Use the shell shown by each block. Keep the order, use new output names, and check whether the task has already run before starting it.

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File D:\workspace\be2\Personal-Learning-Physical\scripts\start_live.ps1 -Sensor camera
```

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File D:\workspace\be2\Personal-Learning-Physical\scripts\start_live.ps1 -Sensor camera -Algorithm stereo
```

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File D:\workspace\be2\Personal-Learning-Physical\scripts\start_live.ps1 -Sensor camera -Algorithm stereo -SessionType stationary -Seconds 60 -Record
```

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File D:\workspace\be2\Personal-Learning-Physical\scripts\start_live.ps1 -Sensor camera -Algorithm rgbd
```

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File D:\workspace\be2\Personal-Learning-Physical\scripts\start_live.ps1 -Sensor camera -Algorithm rgbd-slam -SessionType motion -Record
```

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File D:\workspace\be2\Personal-Learning-Physical\scripts\start_live.ps1 -Sensor camera -Algorithm stereo -Emitter off -SessionType motion -Seconds 60 -Record
```

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File D:\workspace\be2\Personal-Learning-Physical\scripts\test_camera_stationary.ps1 -Seconds 20
```

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File D:\workspace\be2\Personal-Learning-Physical\scripts\start_live.ps1 -Sensor camera -Algorithm rgbd -Seconds 30 -Video -Record -NoGui
```

```powershell
wsl -d Ubuntu-22.04
```

```bash
source /opt/ros/humble/setup.bash
```

```bash
export ROS_DOMAIN_ID=83 ROS_LOCALHOST_ONLY=1
```

```bash
ros2 topic list
```

```bash
ros2 topic hz /physical/camera/left/image
```

```bash
ros2 topic echo /physical/status
```

```bash
rviz2 -d /mnt/d/workspace/be2/Personal-Learning-Physical/configs/rviz/camera_raw.rviz
```
