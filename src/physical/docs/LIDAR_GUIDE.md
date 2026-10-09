# L2 preview, odometry and LIO prerequisites

English | [中文](LIDAR_GUIDE.zh-CN.md)

L2 needs independent power and the physical USB/UART adapter. The launcher resolves the physical GLOBALROOT path; do not hardcode an old COM/Serial number. Default UART is 4,000,000 baud, 8N1, no flow control.

## 1. Preview and odometry

Raw mode shows points without localization. Fifty line packets form a software cloud at about 4.3 Hz from roughly 216 line packets/s; this is not a physical 50-beam sensor or an exact revolution. No per-point deskew is performed.

RTAB-Map ICP uses point-to-plane registration, 8 cm voxels, 30 iterations and 30 cm correspondence distance. KISS uses a separate environment, 0.2–20 m range and 8 cm voxels. Both consume XYZ without calibrated IMU. Earlier declared-stationary runs failed drift targets.

KISS exposes no usable LOST/quality API here: keep those fields null. Finite poses and 100% output do not certify accuracy. Fixed 60-second project targets are <5 cm, <2° and >95% usable output; motion excursion is not stationary error.

## 2. Before Point-LIO or fusion

The linked Unitree Point-LIO uses ROS1 Noetic; this host uses ROS2 Humble, without a validated port. Device elapsed time advances at about half host rate. Verify clock behavior, IMU units/axes/bias, rigid extrinsics and per-point time/ring before LIO. Preserve raw timestamps; multiplying them by two is not validation.

L2 domain is 84, separate from camera domain 83. Two `/odom` streams have separate origins and are not fused. Raw IMU remains diagnostic text, not a calibrated `sensor_msgs/Imu`.

## 3. Recording and interpretation

`-Record` keeps UART and host receipt times; `-Video` saves an independent RViz view. CRC-rejected packets never enter the algorithm. Keep sequence losses, failures, pose/status/logs and code hashes. Only the current session's processes are stopped.

[Test plan](TEST_PLAN.md) · [Current recovery](POSTFALL_LOWLIGHT.md) · [Full topic/file reference](LIDAR_GUIDE.zh-CN.md). Commands below preserve the original shell and order.

## 4. Commands

Use the shell shown by each block. Keep the order, use new output names, and check whether the task has already run before starting it.

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File D:\workspace\be2\Personal-Learning-Physical\scripts\start_live.ps1 -Sensor lidar
```

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File D:\workspace\be2\Personal-Learning-Physical\scripts\start_live.ps1 -Sensor lidar -Algorithm icp
```

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File D:\workspace\be2\Personal-Learning-Physical\scripts\start_live.ps1 -Sensor lidar -Algorithm icp -SessionType stationary -Seconds 60 -Record
```

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File D:\workspace\be2\Personal-Learning-Physical\scripts\start_live.ps1 -Sensor lidar -Algorithm kiss
```

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File D:\workspace\be2\Personal-Learning-Physical\scripts\start_live.ps1 -Sensor lidar -Algorithm kiss -SessionType motion -Seconds 60 -Record
```

```powershell
wsl -d Ubuntu-22.04
```

```bash
source /opt/ros/humble/setup.bash
```

```bash
export ROS_DOMAIN_ID=84 ROS_LOCALHOST_ONLY=1
```

```bash
ros2 topic hz /physical/lidar/points
```

```bash
ros2 topic echo /physical/lidar/imu_diagnostic
```

```bash
rviz2 -d /mnt/d/workspace/be2/Personal-Learning-Physical/configs/rviz/lidar_raw.rviz
```
