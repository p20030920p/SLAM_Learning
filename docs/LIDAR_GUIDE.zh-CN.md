# L2 雷达：实时点云、定位对照与后续惯性定位

适用本机已单独供电、通过 CH343 USB 转串口连接的 **宇树 YS-L2**。当前链路为 Windows 串口接收→本机回环 TCP→WSL ROS2→RViz/算法。SDK 和原生解码交叉核验过程保留在[历史诊断](archive/DIAGNOSTICS_ROUND3.zh-CN.md)。

2026-10-09 重新供电后已恢复点云与 IMU，已完成关灯条件下双设备共存和 ICP/KISS 有效 RViz 录像；旧的 32 字节无点云会话仍保留。最新指标、异常及录像位置见[摔落与弱光实测](POSTFALL_LOWLIGHT.zh-CN.md)。

## 1. 接线、开机和实时显示

1. L2 独立供电，USB 转串口接电脑。底座平放固定，视野包含墙角、地面、家具；先避免只看到一面空白平墙。不要通过转动外壳来代替传感器内部扫描。
2. 按 **Win+X → 终端或 Windows PowerShell**，确认 `PS ...>`。关掉其他占用雷达串口的程序。
3. 执行下面这一行；脚本自动找实体 CH343、打开串口、启动 WSL 和 RViz。

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File D:\workspace\be2\Personal-Learning-Physical\scripts\start_live.ps1 -Sensor lidar
```

正常应看到不断刷新的房间点云、1 m 网格和 `LIVE SENSOR PREVIEW`。此时没有定位算法，轨迹为空正常。Windows 终端约每 20 份聚合点云打印数量和 CRC 拒绝数。

默认串口 4,000,000 baud、8N1、无流控。实体与虚拟串口可能重名，因此脚本通过当前 PnP 和注册表解析 `GLOBALROOT` 实体路径，**不要照抄历史 COM3 或 Serial2**。2026-10-09 重新插接后实体已变为 Serial3，入口能自动适配。

停止时回启动窗口按 Ctrl+C，等会话保存完成。换算法前停止原会话；只关 RViz 不等于关串口。脚本只查询版本，不发送电机模式、待机或固件设置命令。

## 2. RViz 中切换和判断点云

Displays 中勾选 Current cloud，选择 Color Transformer=Intensity；鼠标拖动转动、滚轮缩放。Views 可切换 Orbit/TopDownOrtho，看 3D、俯视和侧面。先保持传感器固定，改变屏幕视角不算传感器运动。

| 要看什么 | 正常预期 | 需要停止定位验收并排查 |
| --- | --- | --- |
| 当前点云 | 点是稀疏的，跨几个聚合组逐渐覆盖更多位置；墙、地面基本形成一致平面 | 固定时全房间不断缩放/旋转、墙有系统性双层、坐标出现 NaN |
| 近处家具和墙角 | 多方向平面约束较充分，桌椅边缘可能稀疏 | 遮住主要视野后只有单一平面，ICP 可能退化 |
| 强度 | 回波强弱不同，和颜色/语义没有一一对应 | 不能把亮点直接当特殊材质识别结果 |
| 点云积累 | Current cloud 的 Decay Time=0 只显示当前组；临时改成 1 s 能看扫描覆盖 | 有限时间叠加属于显示累积，不是已完成 SLAM 地图，也可能放大运动重影 |
| 定位轨迹 | 固定时贴近原点，慢移动时连续响应 | 固定时持续绕圈、慢走时跳几米，即使状态 TRACKING 也异常 |

默认把 **50 个线包软件聚合**为一份点云。当前约 216 线包/s，因此约 4.3 cloud/s、每组跨约 0.23 s；不是“50 线物理雷达”，也不保证每组严格对应完整一转。改 `-Lines 18` 会提高组频率但减少每组几何约束。先固定 50，再把聚合长度作为单独对照变量，不把频率变化误认作精度改进。

## 3. 实时运行算法

下面命令在 Windows PowerShell 中执行。原始点云、轨迹和状态可在 RViz 实时切换；切算法要停掉前一次启动。

### A. RTAB-Map ICP 里程计

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File D:\workspace\be2\Personal-Learning-Physical\scripts\start_live.ps1 -Sensor lidar -Algorithm icp
```

消费 XYZ 点云，不使用 L2 IMU。配置为点到平面 ICP、8 cm 体素、30 次迭代、30 cm 对应距离，不去畸变。应显示 Current cloud 随估计位姿放入 `odom`，黄色轨迹连续增长，Tracking status 给出 TRACKING/LOST。可勾选 Odometry local map；只有算法发布对应话题时才有局部地图。

固定 60 秒、保存 UART 与指标的命令：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File D:\workspace\be2\Personal-Learning-Physical\scripts\start_live.ps1 -Sensor lidar -Algorithm icp -SessionType stationary -Seconds 60 -Record
```

目标：最大静止偏离 <5 cm、旋转 <2°、稳态输出覆盖 >95%，lost 接近 0。**之前确认固定的官方点云上 ICP 未过漂移门槛**，不能因为这次能显示轨迹就改写结论。初始一帧通常用于建局部地图，启动阶段和稳态分开统计。

### B. KISS-ICP 对照

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File D:\workspace\be2\Personal-Learning-Physical\scripts\start_live.ps1 -Sensor lidar -Algorithm kiss
```

使用独立 KISS 环境，不污染主分支 Python。输入同样的聚合点云，距离截取 0.2–20 m、8 cm 体素，当前不启用去畸变/IMU。应看到轨迹和变换后的当前点云；本入口没有另发 KISS 内部局部地图，Odometry local map 为空正常。默认里程计没有全局回环保证。[KISS-ICP 官方实现](https://github.com/PRBonn/kiss-icp)。

状态显示 **KISS POSE / QUALITY UNVERIFIED**：KISS API 未提供这里可用的 lost/可信协方差，JSON 中 lost 为 null，不能把有限矩阵或初始化后的占位协方差当“跟踪正确”。之前固定实测有明显旋转漂移；先解决固定漂移，再进入移动测试。

做移动对照时换成下面一行，起止各固定 5 秒，慢走尺量路线：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File D:\workspace\be2\Personal-Learning-Physical\scripts\start_live.ps1 -Sensor lidar -Algorithm kiss -SessionType motion -Seconds 60 -Record
```

`motion` 下最大位姿范围是运动范围，不是静止误差。没有独立参考时不计算 ATE/RPE。50 线组跨 0.23 s，快速转动会有明显组内运动，未去畸变时不要期待墙面始终锐利。

### C. Point-LIO：先满足输入条件

官方 [Unitree Point-LIO](https://github.com/unitreerobotics/point_lio_unilidar) 支持 L2，但其说明使用 ROS1 Noetic；本机当前为 ROS2 Humble，尚未完成明确的版本适配和实测入口，**不要把 ROS1 roslaunch 命令贴进本机 ROS2 终端**。

当前 L2 原始设备时间约以主机时间一半速度前进，本次短测比例仍约 2；IMU 单位/轴/偏置也未完成受控验收。因此当前只发布 `/physical/lidar/imu_diagnostic` 原始数值诊断字符串，不伪造成已校准的 `sensor_msgs/Imu`，不接入 LIO。

接下来的顺序是：核查原始设备时间与官方解析选项→确认 IMU 单位、轴和重力→刚性外参及采样时间标定→固定初始化→小范围平移/转动→对照去畸变。不得简单把所有时间乘 2 并覆盖原始值。通过后，视频预期为重力方向稳定、转动时墙面更直、轨迹连续；Z 轴振荡、地图扭曲或静止旋转持续增长均需排查。平滑轨迹本身不证明 LIO 正确。

## 4. 手动开 Ubuntu、看话题和 RViz

先保持 Windows 入口运行。另开 PowerShell：

```powershell
wsl -d Ubuntu-22.04
```

看到 `qzl@...$` 后，每个 Bash 块分别执行：

```bash
source /opt/ros/humble/setup.bash
```

```bash
export ROS_DOMAIN_ID=84 ROS_LOCALHOST_ONLY=1
```

```bash
ros2 topic hz /physical/lidar/points
```

Ctrl+C 停止频率检查；原始 IMU 诊断用：

```bash
ros2 topic echo /physical/lidar/imu_diagnostic
```

如果 Windows 启动加了 `-NoGui`，手动打开原始点云配置：

```bash
rviz2 -d /mnt/d/workspace/be2/Personal-Learning-Physical/configs/rviz/lidar_raw.rviz
```

ICP/KISS 使用同目录 `lidar_odom.rviz`。原始模式 Fixed Frame=`physical_lidar`，定位模式=`odom`；QoS Reliable/Volatile。相机 domain=83，雷达 domain=84，所以另开相机窗口时不会互相覆盖 `/odom`；这也意味着当前两条链路**不是融合系统**。

| 内容 | ROS 话题 |
| --- | --- |
| XYZI 当前点云 | `/physical/lidar/points`；米，`physical_lidar` 坐标系 |
| 原始 IMU 数值 | `/physical/lidar/imu_diagnostic`；含设备时间和未经标定的 SDK 数值 |
| 位姿 / 历史轨迹 | `/odom`、`/physical/trajectory` |
| 状态文字 / JSON | `/physical/tracking`、`/physical/status` |
| ICP 局部地图 | `/odom_local_map`，需节点实际发布；KISS 本入口不发布 |

## 5. 保存什么、怎样判断通过

目录打印为 `D:\workspace\be2\Personal-Learning-Physical\data\live-lidar-时间戳`。

| 文件 | 内容 |
| --- | --- |
| `live-capture.json` | 版本、实体端口、CRC、序号缺失、原始包率、主机/设备时间比例 |
| `live-result.json` | ROS 点云率、位姿覆盖、lost（KISS=null）、静止/运动范围、ICP 计算耗时 |
| `code-hashes.json` | 本次实际脚本与 RViz 配置 SHA-256 |
| `poses.json` / `status.json` | 逐帧位姿/状态，可对照原始视频检查异常 |
| `odometry.log` / `kiss-worker.log` / `rviz.log` | 算法与显示错误；退出码正常不能代替质量检查 |
| `uart.bin` / `receive.csv` / `capture.json` | 仅 `-Record`；原始 UART、每块主机接收时刻、清单 |
| `rviz-live.mp4` / `video.json` | 加 `-Video` 自动录制独立 RViz 视图；本轮已有 ICP/KISS 有效点云与轨迹录像，位置见弱光实测报告 |

点云桥接采用经过官方几何对照的 Python 解码，并保留原始 UART 供原生 SDK 重解码。不是把实时 Python 解码冒充原生 SDK。CRC 不合格包不会进入算法；记录队列满等采集错误直接判链路失败。

初期原始链路目标：CRC 理想为 0，拒绝/序号缺失各 <0.1%，无时间倒退；约 216 线包/s、250 IMU 包/s 是这台当前设备的历史实测参考，不是厂家所有工况保证。4.3 cloud/s 是 50 线软件聚合频率，不能和线包率或电机转速混用。

`pose_output_fraction` 包括失败位姿；ICP 的 `valid_pose_output_fraction` 另剔除失败协方差标记。KISS 没有可靠的失败状态，两项 valid/lost 均留空；`kiss_worker_compute_ms` 是隔离进程往返计算耗时，不是完整端到端延迟。

当前 ROS 时间使用 WSL 收到完整聚合组的时刻，没有逐点去畸变，也没有硬件同步。实时点云只有 XYZI；需要逐点 time/ring 的 LIO 输入必须走后续专门适配，不能直接重命名话题冒充兼容。

完整动作、指标和主分支测试顺序见[测试计划](TEST_PLAN.zh-CN.md)与[主分支适配](MAIN_INTEGRATION.zh-CN.md)。当前先用雷达独立基线定位问题，相机—雷达融合需刚性安装和共同时间/外参验证后再做。
