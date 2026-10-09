# 相机：从开机到实时看算法

[English](CAMERA_GUIDE.md) | 中文

适用本机 `D:\workspace\be2\Personal-Learning-Physical`。SDK 实测型号是 **D435，没有 IMU**，不能开启 D435i 的视觉惯性模式。当前电脑已配置 Windows Python、Ubuntu-22.04 WSL、ROS2 Humble、RTAB-Map 和 RViz。新克隆仓库不含这些环境和旧录像，重建见[环境说明](ENVIRONMENT.zh-CN.md)。

## 1. 打开相机和 RViz

1. 相机接 USB 3 口，放在稳定支架上，面向 **1–3 m 的墙角、家具和带字纸箱**。房间开灯；先避开亮屏、直射灯、大面积空白近物。餐巾纸、牛皮纸盒、药片盒可以检查深度边界，但它们填满近景时不适合作为第一段定位场景。
2. 关闭其他占用相机的采集程序。按 **Win+X → 终端或 Windows PowerShell**，确认提示符以 `PS` 开头。
3. 只复制下面这一行，回车。脚本自动打开 WSL 中的 ROS 节点和 RViz；无须先手动进入 Ubuntu。

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File D:\workspace\be2\Personal-Learning-Physical\scripts\start_live.ps1 -Sensor camera
```

约几秒后出现 RViz：RGB、Depth 0-5m 和当前彩色点云。左侧 Displays 可勾选 Left IR、Right IR。终端显示 `LIVE camera / sensor`，这时只有传感器预览，没有定位算法，轨迹为空是正常的。

**停止：** 回到启动它的 PowerShell 按 Ctrl+C，等会话目录打印完成。单独关 RViz 不会停止传感器。换算法时先停止旧会话，再执行下一条；不要同时开两个相机入口。

若已经进入 `qzl@电脑名:...$`，那是 Ubuntu Bash。先输入 `exit` 回车返回 `PS ...>`，再运行上述 Windows 命令。不要把 PowerShell 命令贴进 Bash，也不要把多行教程粘成一条。

## 2. 切换画面，看懂各图

勾选/取消 Displays 中的项目即可切换，不需要重启相机。可先只保留 RGB 和 Depth，拖动面板分隔线放大；再把两幅 IR 打开对照。鼠标左键拖动 3D 视角，滚轮缩放，Views 中 Reset 可复位视角。

| RViz 项目 | 内容和正常现象 | 应排查的现象 |
| --- | --- | --- |
| RGB | 普通彩色图。对准文字，静止后应清楚 | 静止仍持续模糊、大片过曝；先改善照明与距离 |
| Depth 0-5m | 对齐到彩色图的深度伪彩；黑色=无效，颜色表示距离，不表示置信度 | 普通哑光平面大面积持续黑洞、距离突然跳变 |
| Left/Right IR | 左右灰度图有视差；投射器打开时能看到点纹理 | 一路全黑/冻结；两路曝光严重不一致 |
| Current cloud | 当前深度反投影的彩色 3D 点云，截取 0.2–5 m，每 4 像素采一点 | 边缘有空洞/少量离群点可以出现；整面墙伸缩、颜色与几何系统错位需排查 |
| Odometry trajectory | 算法估计的历史轨迹，只有里程计模式才有 | 相机固定但轨迹不断远离、慢走时跳变或冻结 |
| Tracking status | `TRACKING`、`LOST`、`WAITING...` 等状态 | TRACKING 只是算法状态，不能代替尺量精度验收 |
| RGB-D global map | 仅 `rgbd-slam` 默认开启，显示关键帧构成的彩色全局地图 | 只有开了建图节点才期待地图；持续双墙、错误回环后地图折叠异常 |

镜面、透明物、低反射物、遮挡轮廓出现深度空洞很常见。IR 中的亮点是投射纹理。**投射纹理可能使静止双目匹配很好，却不能证明移动时自然特征可靠**；后续必须做投射器开/关对照。

你观察到的运动模糊会影响 RGB-D 特征匹配：先慢移，保证静止文字清楚；改善均匀照明后再比较。脚本默认保持原曝光，不擅自写入手动曝光值，不能用一张清晰 IR 图证明 RGB 也清晰。

## 3. 开启不同算法

每条都是 **Windows PowerShell 单行命令**。同一次启动使用一个算法；RViz 可以实时切换显示内容，算法切换通过停止后重启完成。

### A. 双目视觉里程计：先做这个

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File D:\workspace\be2\Personal-Learning-Physical\scripts\start_live.ps1 -Sensor camera -Algorithm stereo
```

消费左右 IR 和真实内参、约 5 cm 基线；RGB 和深度只作旁观显示。静止应保持原点附近；慢向右移动应生成连续轨迹。

相机光学坐标 **X 向右、Y 向下、Z 向前**，不要按“Z 一定向上”判断方向。稀疏局部地图是正常输出，单独里程计没有全局回环优化。

[RTAB-Map 官方里程计说明](https://github.com/introlab/rtabmap_ros/blob/ros2/rtabmap_odom/README.md)。

先固定 60 秒并保存原始数据：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File D:\workspace\be2\Personal-Learning-Physical\scripts\start_live.ps1 -Sensor camera -Algorithm stereo -SessionType stationary -Seconds 60 -Record
```

`stationary` 是你对“整段固定”的声明，不是程序自动检测。录完看 `live-result.json`：最大平移偏离先要求 <0.05 m、最大转角 <2°，lost 应接近 0，稳态位姿输出覆盖 >95%。这只是项目初期目标，过去一段静止通过不保证下一段或移动通过。

### B. RGB-D 视觉里程计

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File D:\workspace\be2\Personal-Learning-Physical\scripts\start_live.ps1 -Sensor camera -Algorithm rgbd
```

消费 RGB 和 **SDK 对齐到 RGB 的深度**，使用彩色相机内参；相机左右 IR 不参与这个前端。应看到轨迹和随位姿运动的当前彩色点云。它本身不生成完整全局彩色地图。近物遮挡、亮屏和运动模糊容易丢失跟踪；出现 LOST 时暂停运动、回到清晰有纹理的区域，记录恢复耗时。

### C. RGB-D SLAM：看房间逐渐建出来

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File D:\workspace\be2\Personal-Learning-Physical\scripts\start_live.ps1 -Sensor camera -Algorithm rgbd-slam -SessionType motion -Record
```

同时开启 RGB-D 里程计与 RTAB-Map 建图。先静止 5 秒，再慢扫墙角、家具，保持相邻视野大幅重叠；最后回到起点和朝向。RGB-D global map 约 1 Hz 更新，输入图像更快；关键帧地图不是每个像素每帧都累计，正常。重访只有成功识别并验证关联时才可能触发回环，不能保证每次都有。

当前轨迹线是 `/odom` 历史轨迹，**不会回写成优化后的历史轨迹**；全局 MapCloud 按位姿图更新。比较回环前后效果要另导出 RTAB-Map 数据库中的优化位姿。`graph_global_closure_links` 只是收到的全局回环边 ID，不能当人工验证正确的回环次数。

建图画面里短时点云消失可能是里程计丢失，RViz 也可能提示 TF 队列满；先看 Tracking 和 odometry.log。不要调大队列隐藏持续跟踪失败。

### D. 投射器对照、录制与离线视频

自然纹理充分时，停掉当前会话，再运行关投射器对照：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File D:\workspace\be2\Personal-Learning-Physical\scripts\start_live.ps1 -Sensor camera -Algorithm stereo -Emitter off -SessionType motion -Seconds 60 -Record
```

`-Emitter on/off` 只在本次运行临时设置，正常退出恢复原值。相同路线和照明下比较 lost、内点数、计算耗时和终点偏差；不能在同一次会话中混改多个参数。无纹理场景关投射器后深度变差可以出现，单独记录。

需要自动生成已有样式的**离线算法视频**时，使用原来的固定测试入口，整段必须固定：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File D:\workspace\be2\Personal-Learning-Physical\scripts\test_camera_stationary.ps1 -Seconds 20
```

它录制→核验原始回放→导出双目→运行离线算法→打开视频，录制时没有实时窗口。

**简单自动录像：** 加 `-Video` 会录制一个独立、固定布局的 RViz 实时视图，保存 `rviz-live.mp4`，结束后自动打开。`-Record` 同时保留原始相机数据；`-NoGui` 用于只录像、减少窗口。最简单的 30 秒 RGB-D 演示命令是：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File D:\workspace\be2\Personal-Learning-Physical\scripts\start_live.ps1 -Sensor camera -Algorithm rgbd -Seconds 30 -Video -Record -NoGui
```

录像显示 RGB、深度、点云、轨迹和真实跟踪状态，无音频。独立录像视图不跟随另一个 RViz 窗口的鼠标操作；开头/结束包括启动和收尾，文件时长会略长于 30 秒数据。`video.json` 保存编码检查；演示不要求复杂场地，近物、空洞和 LOST 如实保留。当前录制示例见[简易录像](SIMPLE_RECORDING.zh-CN.md)。

ORB-SLAM3 Stereo/RGB-D 是后续对照，**本分支还没有安装与实测其入口**。应呈现特征、跟踪状态、轨迹与稀疏关键帧地图，不能期待彩色稠密房间；当前 D435 不具备其惯性输入条件。[官方实现](https://github.com/UZ-SLAMLab/ORB_SLAM3)。

## 4. 如果想自己打开 WSL、RViz 和检查话题

先保持一个 Windows 实时会话运行。另开 PowerShell，输入：

```powershell
wsl -d Ubuntu-22.04
```

看到 `qzl@...$` 后，下面每个 Bash 块各执行一次。相机会话使用 ROS domain 83，雷达用 84；不一致会看不到话题。

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

按 Ctrl+C 停止频率检查。检查里程计状态可运行：

```bash
ros2 topic echo /physical/status
```

若启动时用了 `-NoGui`，现在可以手动开 RViz。原始预览用：

```bash
rviz2 -d /mnt/d/workspace/be2/Personal-Learning-Physical/configs/rviz/camera_raw.rviz
```

stereo/rgbd 改用同目录 `camera_odom.rviz`，rgbd-slam 用 `camera_map.rviz`。手动开的 RViz 由你关闭，启动脚本只管理自己打开的窗口。

| 内容 | ROS 话题 / Fixed Frame |
| --- | --- |
| RGB / 深度伪彩 / 左右 IR | `/physical/camera/color/image`、`/physical/camera/depth_color/image`、`/physical/camera/left/image`、`/physical/camera/right/image` |
| 米制深度输入 | `/physical/camera/depth/image`，16UC1，1 单位=1 mm，0 无效 |
| 当前彩色点云 | `/physical/camera/points`，RViz PointCloud2，Color Transformer=RGB8 |
| 轨迹 / 状态 | `/physical/trajectory`（Path）、`/physical/tracking`（Marker）、`/physical/status`（JSON 字符串） |
| 全局地图 | `/rtabmap/mapData`，RViz 插件 MapCloud |
| Fixed Frame | 原始预览=`camera_left_optical`；里程计=`odom`；全局地图=`map` |

RViz Topic QoS 设 Reliable/Volatile。修改 Fixed Frame 只改变显示参考系，不是对传感器重新标定。重开窗口不会自动开启采集，必须有 Windows 实时入口正在运行。

## 5. 怎样读本次文件和结果

每次终端打印新目录 `D:\workspace\be2\Personal-Learning-Physical\data\live-camera-时间戳`，不会覆盖旧会话。

| 文件 | 用途 |
| --- | --- |
| `live-capture.json` | 实际设备、SDK 标定、投射器、采样数、左右 IR 时间拒绝数、错误 |
| `live-result.json` | ROS 输入率、输出覆盖、lost、计算 p50/p95、最大位姿范围、是否有地图更新 |
| `code-hashes.json` | 本次实际使用的桥接、算法入口和 RViz 配置 SHA-256，便于锁定代码版本 |
| `poses.json` / `status.json` / `input-stamps.json` | 位姿、逐帧状态与输入时间；复查覆盖计算 |
| `odometry.log` / `mapping.log` / `rviz.log` | 定位、建图、显示故障，不能只看终端最后一行 |
| `raw.db3` / `frames.json` / `capture.json` | 仅 `-Record` 时保存；RealSense SDK 原始录像及采集清单，不是通用 ROS bag |
| `rtabmap.db` | 仅 rgbd-slam 建图数据库；不是 RealSense 原始录像 |
| `rviz-live.mp4` / `video.json` | 仅 `-Video`；独立 RViz 实时录像及编码/时长检查 |

本入口四路硬件配置 640×480@30，但桥接主动按 `-FPS 10` **上限**抽样，旧入口在本机短测约 4–6 组/s；改用 ROS 原生字节数组后，最新 15 秒预览约 8.19 组/s，仍不保证达到 10 Hz。RViz 右下角渲染 FPS、ROS 图像输入率和硬件流帧率是三个指标。

要验硬件 30 fps，用独立原始采集和 SDK 回放审核；不能把桥接低帧率直接算成 USB 丢帧。离线 10 Hz 对照及未通过项见[无人值守回放](OFFLINE_REPLAY.zh-CN.md)。

`pose_output_fraction` 包括算法失败位姿，和 lost 一起看；`valid_pose_output_fraction` 剔除原生里程计的失败协方差标记，`...after_first_2s` 将初始化单列。它仍只是算法自报可用性，不能替代独立精度。RGB-D 近似同步可能选 RGB 或深度时间戳，覆盖按两者之一在 1 微秒内一一匹配。

ROS 时间使用 WSL 接收时刻，保留原生流间时间差；SDK 原时间在原始录制/frames.json 中保留。它不构成相机—雷达硬件同步，也不能直接用 Windows/WSL 两套时钟之差当网络延迟。

下一步按[测试计划](TEST_PLAN.zh-CN.md)执行固定→尺量直线→转动→小闭环。需要主分支语义/地图算法时先看[适配与合入要求](MAIN_INTEGRATION.zh-CN.md)和[已完成的真实 RGB-D 输入检查](RGBD_MAIN_INPUT.zh-CN.md)，不能把普通 RGB-D SLAM 地图叫作 ConceptGraphs/HOV-SG 结果。

摔落后四路回放、双目几何筛查、启动停顿和关灯投射器对照见[摔落与弱光实测](POSTFALL_LOWLIGHT.zh-CN.md)。弱光下 RGB 和按 RGB 着色的点云会偏暗；可勾选左右 IR 看双目实际输入，点云切 `FlatColor/AxisColor` 仅改善显示。双设备同时运行步骤及四份实际录像也在该报告中。
