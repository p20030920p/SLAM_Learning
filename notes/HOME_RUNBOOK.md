# Capture and manually record home experiments on this computer

English | [中文](HOME_RUNBOOK.zh-CN.md) | [Index](README.md)

The [public protocol](../docs/REAL_WORLD.md) defines comparisons and rejection rules. This guide covers operations. Basic hardware checks are on the [physical branch](https://github.com/p20030920p/SLAM_Learning/tree/notes/personal-study-guide-20261008/physical); this controlled H1 protocol remains unfinished. The SDK-reported D435 has no IMU. Begin with capture/playback and four exploratory events. Captured video alone is not hypothesis validation.

## 1. Minimum session

Fix each sensor separately. Label a chair/two boxes, mark initial and30cm positions, measure uncertainty and fix a phone showing both sensor and scene. For each sensor record static, occluded, removed and moved conditions,80seconds each:0–20static,20–25action,25–60hold,60–80restore. The static control stays unchanged. Record actual event boundaries.

Four events total5min20s per sensor,10min40s for both, excluding setup/checks. Formal development/test counts and layouts are in the public protocol; one demonstration is not the full study.

Save outside Git under `D:\workspace\be2\SLAM_Home\2026-10-08`, one unique directory per session:

```text
D435i-A-move-dev01/
  capture.json
  raw/capture.bag or capture.db3
  calibration/
  events.csv
  annotations/
  video/screen.mp4
  video/phone.mp4
  checks/
```

Record device/configuration/versions, calibration/depth scale, object IDs, coordinate axes, reference uncertainty and file hashes. Event columns include session, sensor_time_s, host_monotonic_s, event, object_id, visibility, x_m/y_m/z_m, reference_uncertainty_m, notes. Leave unmeasured values blank. A clap/verbal cue is alignment evidence, not precise cross-device synchronization.

## 2. D435 on Windows

1. Connect directly with a reliable USB3 cable. Use official RealSense Viewer; if missing, obtain a supported build from [official releases](https://github.com/realsenseai/librealsense/releases), recording the version. Viewer was not found in common local install paths. Keep USB on Windows initially.
2. Enable RGB/depth, initially640×480 at30Hz, plus the actual supported accel/gyro profiles. Save the actual settings. Avoid two applications claiming the camera.
3. Capture a stationary ruler/background. Inspect invalid depth, units and frame rate. Keep raw depth/calibration, not only a colored depth video.
4. Record raw streams through Viewer. Older SDKs use `.bag`; current documentation uses `.db3`. Use the installed version's supported format, not a renamed extension.
5. Stop recording/streams. Add Source→Load Recorded Sequence. Verify RGB/depth/motion streams and beginning/middle/end timestamps. Prefer matching SDK playback; ROS2 compatibility depends on version/encoding.

[Official recording/playback](https://github.com/realsenseai/librealsense/blob/master/doc/record-and-playback.md), [Viewer instructions](https://github.com/realsenseai/librealsense/blob/master/tools/realsense-viewer/readme.md).

`scripts/capture_realsense.py` defaults to legacy bag and supports `--recording-format db3`. Only syntax/help were checked, not real-device capture. It does not open a Viewer window, and simultaneous device access is unsuitable for filming. Start with the Viewer route for visible capture.

## 3. L2 networking and ROS2

Humble/RViz2 exists in WSL; no L2 SDK checkout or connected hardware was found in the inspected locations. Current WSL networking is NAT: receiving UDP on Windows does not prove WSL receives clouds. Ping alone is insufficient.

Keep the current device mode. For UDP use a dedicated wired adapter, retaining Wi-Fi internet. Check the actual device/host addresses and ports; SDK default host target192.168.1.2 is not the LiDAR's own address. Change only the dedicated adapter and record its old settings.

If NAT prevents binding/reception, supported Windows11 systems can use mirrored networking. First save all WSL/GPU work, back up `C:\Users\qzl\.wslconfig`, add `networkingMode=mirrored` to the existing `[wsl2]` section while retaining memory/processors/swap, and manually restart WSL. `wsl --shutdown` terminates all WSL jobs. Configure narrow UDP firewall rules for actual SDK ports; TCP portproxy is not UDP forwarding. [Microsoft networking reference](https://learn.microsoft.com/windows/wsl/networking). No network settings were changed here.

Alternatively, an L2 already operating in serial mode can use deliberate USB passthrough. Do not switch device modes merely to rush the test. Get30seconds of usable data in its current mode first.

**WSL Bash, a separate hardware workspace:**

```bash
mkdir -p /home/qzl/hardware
cd /home/qzl/hardware
git clone https://github.com/unitreerobotics/unilidar_sdk2.git
cd unilidar_sdk2
git rev-parse HEAD
```

Record this commit. Inspect `unitree_lidar_ros2/src/unitree_lidar_ros2/launch/launch.py` for actual addresses, ports and mode. The [official SDK](https://github.com/unitreerobotics/unilidar_sdk2) lists Foxy for ROS2 validation; Humble must be built/tested locally.

```bash
source /opt/ros/humble/setup.bash
cd /home/qzl/hardware/unilidar_sdk2/unitree_lidar_ros2
colcon build --parallel-workers 2
source install/setup.bash
ros2 launch unitree_lidar_ros2 launch.py
```

The official launch configures RViz. If absent, start `rviz2`; Fixed Frame must match the actual PointCloud2 header, default `unilidar_lidar`. Add `/unilidar/cloud`; inspect QoS, often requiring Best Effort for sensor streams. A fixed sensor needs no fabricated world trajectory.

In another **WSL Bash** tab:

```bash
source /opt/ros/humble/setup.bash
source /home/qzl/hardware/unilidar_sdk2/unitree_lidar_ros2/install/setup.bash
ros2 topic list -t
ros2 topic info /unilidar/cloud -v
ros2 topic echo /unilidar/cloud --once --field fields
ros2 topic echo /unilidar/cloud --once --field header
ros2 topic hz /unilidar/cloud
```

Keep actual fields such as xyz/intensity/time/ring and inspect IMU. Replace default topic names if different. Stop `hz` with Ctrl+C before recording:

```bash
ros2 bag record -o /mnt/d/workspace/be2/SLAM_Home/2026-10-08/L2-A-static-dev01/raw \
  /unilidar/cloud /unilidar/imu /tf /tf_static
```

Stop with Ctrl+C, inspect `ros2 bag info` for duration/counts and disclose absent TF. Stop live publication before `ros2 bag play .../raw --clock`; enable RViz simulation time and retain the correct frame. Do not mix live and recorded streams.

## 4. Record visible evidence and check it

Show Viewer RGB/depth/3D for D435; RViz clouds for L2. Keep a wide and a close inspection view, session ID and small bag-path/rate terminal. The phone shows that the sensor stayed still and whether the object moved. In the occlusion clip the chair stays in place; in removal the old location/background must become visible.

Replay every raw capture and both videos. In **PowerShell**, hash an actual file:

```powershell
Get-FileHash -Algorithm SHA256 -LiteralPath 'D:\workspace\be2\SLAM_Home\2026-10-08\YOUR_SESSION\raw\YOUR_FILE.bag'
```

## 5. Turn captures into hypothesis tests

The current author runners accept the specified public inputs; device adapters are pending. Do not pass a new bag to `run_conceptgraphs.py` and claim a completed experiment.

Required adaptation:

1. D435: align depth using real calibration/scale; keep raw data, timestamps and units; export posed RGB-D. Freeze source indexes, masks and per-mask features.
2. L2: decode actual PointCloud2 fields and time slices. Fixed-sensor identity poses are valid within the stated local frame; preserve ray origins and unlabeled XYZ/VIEWPOINT. Moving scans need deskew/estimated poses; IMU integration is not position ground truth.
3. Annotate independent visible surfaces, physical IDs and events; reserve evaluation frames outside the mapper. Sessions, not pixels/seeds, are the sampling units.
4. Run visibility controls first. Freeze the prescribed pose-error window8–15 and correction deliveries16/24/36. Compare native/simple/geometry-only/full-replay before implementing H1.

Report full source-cache cost, replay latency, outside-window failure and abstention coverage. Without these adaptations, the valid deliverable is a hardware capture demonstration rather than H1 results. Before formal testing freeze layouts/session IDs, annotation rules, source selection, event/correction timing, thresholds, budgets and rejection criteria. Raw identifiable home recordings remain local; main receives checked lightweight evidence.
