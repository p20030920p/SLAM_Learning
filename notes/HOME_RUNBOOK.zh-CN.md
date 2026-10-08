# 在这台电脑上采集和手动录制居家实验

[English](HOME_RUNBOOK.md) | [索引](README.zh-CN.md)

这是个人操作步骤；[公开实验设计](../docs/REAL_WORLD.zh-CN.md)规定条件、对照和否定规则。先做采集检查和四事件探索演示。硬件尚未接入验证，下面涉及设备的成功条件需要你逐项确认；采到视频不等于已经完成假设检验。

## 今天最小可执行安排

| 阶段 | 你做什么 | 留下什么 |
| --- | --- | --- |
| 布置与测量 | 固定手机／三脚架，给椅子／箱子编号，贴初始与 30 cm 位置，测尺量误差 | 房间示意、初末位置、对象 ID、标定／参考照片 |
| D435i 接入 | 先静止录 30 秒并回放 | RGB、深度、IMU、内参、深度尺度、SDK／固件版本、掉帧情况 |
| D435i 四事件 | 每段 80 秒；静止／遮挡／移除／移动 | 4 份原始录制、屏幕视频、手机事件视频、事件表 |
| L2 接入 | 先验 UDP／串口、ROS2 数据和 RViz，再静止录 30 秒 | cloud/IMU、字段清单、实际帧与话题、网络／SDK版本 |
| L2 四事件 | 同样四段 80 秒，分别恢复初始场景 | 4 份 ROS2 录制、RViz 视频和事件表 |
| 核查 | 每份录制回放，检查时间、范围和字段 | manifest、哈希、采集失败也保留 |

一次四事件是 5 分 20 秒，两设备原始演示合计 10 分 40 秒；接线、配置、复位和回放另算时间。先做这个，不必今晚同时完成全部正式会话。

## 目录与事件记录

使用 Git 目录外的 `D:\workspace\be2\SLAM_Home\2026-10-08`。每个会话单独目录，例如 `D435i-A-move-dev01`，不要复用旧目录。

```text
D435i-A-move-dev01/
  capture.json             # 设备、版本、配置、标尺、坐标、状态
  raw/capture.bag 或 .db3  # 按实际 SDK 格式
  calibration/             # 内外参与深度标尺
  events.csv               # 事件实际开始／完成时间
  annotations/             # 物理 ID、可见性与参考表面
  video/screen.mp4
  video/phone.mp4
  checks/                  # 回放检查、帧率、缺帧和哈希
```

`events.csv` 至少包含：`session,sensor_time_s,host_monotonic_s,event,object_id,visibility,x_m,y_m,z_m,reference_uncertainty_m,notes`。原点和轴在 `capture.json` 说明；未测到的值留空，不填假零。手机画面中的口令或手掌敲击作为事件对齐线索，不能宣称精确跨设备同步。

## D435i 原生 Windows 路线

1. 使用可靠 USB3 线直接连接这台电脑。打开官方 RealSense Viewer；本轮未在常见安装目录找到它，如尚未安装，从[官方 SDK 发布页](https://github.com/realsenseai/librealsense/releases)获取受支持版本并记录版本号。先不把 USB 透传给 WSL，避免同时争用设备。
2. 打开 RGB 和深度，先选 640×480、30 Hz。打开该设备实际支持的加速度计／陀螺仪流，保存屏幕中的实际 profile。避免同时开多个应用抢同一摄像头。
3. 固定相机，拍静态背景和卷尺，检查深度无效像素、单位和帧率。深度和彩色原始分辨率／标定分别保留，不能只保存彩色化深度视频。
4. 在设备菜单选择 Record to File，记录原始流。旧 SDK 保存 `.bag`，当前官方文档使用 `.db3`；让已安装的 Viewer 决定合法格式，不靠改扩展名转换。
5. 停止所有流并结束录制，使用 Add Source → Load Recorded Sequence 重新打开。确认颜色、深度和运动流确实存在，检查首／中／末段和时间戳。SDK 格式与普通 ROS2 bag 的兼容性依版本和压缩设置而定，使用配套 Viewer 回放优先。

官方步骤：[录制与回放](https://github.com/realsenseai/librealsense/blob/master/doc/record-and-playback.md)，[Viewer](https://github.com/realsenseai/librealsense/blob/master/tools/realsense-viewer/readme.md)。

仓库 `capture_realsense.py` 默认是 legacy `.bag` 路线，只做过语法／帮助检查，尚未接设备。若使用支持 `.db3` 的 SDK，传 `--recording-format db3`。Python 采集时不会自动打开 Viewer，也不能同时让另一应用占用同一设备；要拍可见图像，先选 Viewer 路线。

## L2 与 WSL 的关键区别

本机 WSL 有 ROS2 Humble／RViz2，但尚未发现 L2 SDK checkout 或已连接硬件。现有 `.wslconfig` 是 NAT 路线，**Windows 网卡收到 UDP 不保证 WSL 自动收到**。不要只因为 `ping` 成功就当点云连通。

优先沿用设备当前工作模式。若是默认 UDP，用专用有线网卡接 L2，Wi-Fi 继续联网；先看官方配置和实际设备地址。SDK 默认电脑目标地址为 `192.168.1.2`，要区分它与雷达自身地址。只给专用有线网卡设匹配地址，别改 Wi-Fi；记录原设置方便还原。

若 WSL 无法绑定或收包，可在支持的 Windows 11 上使用 mirrored networking。先保存所有 WSL／GPU 工作，再备份 `C:\Users\qzl\.wslconfig`，在已有 `[wsl2]` 节添加 `networkingMode=mirrored`，保留原来的 memory／processors／swap 等项。手动执行 `wsl --shutdown` 后重启 Ubuntu；这会终止所有 WSL 任务。按实际 SDK 端口配置窄范围 UDP 防火墙规则，不关闭整个防火墙，也不把 TCP portproxy 当 UDP 转发。[微软 WSL 网络说明](https://learn.microsoft.com/windows/wsl/networking)。本轮没有修改你的网络。

如不切换网络，另一条路线是当前已处于串口模式的 L2，经明确 USB 透传接 WSL；不要为赶时间直接改设备模式。先用当前模式完成一段 30 秒数据。

## L2 官方 ROS2 包准备

在 WSL 新建独立硬件目录，不改语义环境：

```bash
mkdir -p /home/qzl/hardware
cd /home/qzl/hardware
git clone https://github.com/unitreerobotics/unilidar_sdk2.git
cd unilidar_sdk2
git rev-parse HEAD
```

将这个提交号记入会话，再检查 `unitree_lidar_ros2/src/unitree_lidar_ros2/launch/launch.py` 的实际设备／本机地址、端口、工作模式。官方公开 ROS2 验证平台是 Foxy；Humble 需要本机编译与接入确认。不要假装本轮已经跑通。

```bash
source /opt/ros/humble/setup.bash
cd /home/qzl/hardware/unilidar_sdk2/unitree_lidar_ros2
colcon build --parallel-workers 2
source install/setup.bash
ros2 launch unitree_lidar_ros2 launch.py
```

官方 launch 会配置 RViz；若没有自动出现，再开 `rviz2`。将 Fixed Frame 设为实际 PointCloud2 的 `header.frame_id`（默认 `unilidar_lidar`），添加 PointCloud2 `/unilidar/cloud`；QoS 按发布器选择，传感器流通常要检查 Best Effort。雷达固定时不必人为发布虚构的 world 位姿。

另开同环境终端检查：

```bash
source /opt/ros/humble/setup.bash
source /home/qzl/hardware/unilidar_sdk2/unitree_lidar_ros2/install/setup.bash
ros2 topic list -t
ros2 topic info /unilidar/cloud -v
ros2 topic echo /unilidar/cloud --once --field fields
ros2 topic echo /unilidar/cloud --once --field header
ros2 topic hz /unilidar/cloud
```

保留 x/y/z/intensity/time/ring 等**实际**字段清单；只有 XYZ 的截图不能替代完整原始数据。IMU 同样检查 `/unilidar/imu`。若话题名称不同，后面的命令用实际名称。

```bash
ros2 bag record -o /mnt/d/workspace/be2/SLAM_Home/2026-10-08/L2-A-static-dev01/raw \
  /unilidar/cloud /unilidar/imu /tf /tf_static
```

录制结束 `Ctrl+C`，检查 `ros2 bag info` 中消息数量和时长；没有 TF 消息就照实记录。回放时停止实时雷达发布器，再执行 `ros2 bag play .../raw --clock`，RViz 打开 `use_sim_time` 并保持相同 Fixed Frame。不能让实时与回放两个同名话题同时混在画面里。

## 怎么摆放屏幕与拍摄

D435i：主画面给 Viewer 的 RGB＋深度或三维点云；手机拍“传感器没动、椅子有没有动”。L2：主画面给 RViz 点云，固定一个全景视角与一个近景检查视角；终端留小块显示本次 bag 路径与数据率。先拍会话编号和初始卷尺位置，再执行事件。

每段 0–20 秒不动，20–25 秒操作，25–60 秒保持，60–80 秒恢复。静止控制整段不动。手机口述“遮挡开始／完成”“移动完成”等；录后补准确事件区间。遮挡片保持椅子原位，移除片必须能看到其原位置的背景。

录屏不能代替原始数据；录完先确认两份视频和原始文件可回放。PowerShell 对实际文件计算哈希：

```powershell
Get-FileHash -Algorithm SHA256 -LiteralPath 'D:\workspace\be2\SLAM_Home\2026-10-08\实际会话\raw\实际文件.bag'
```

## 采完怎样真正检验假设

当前仓库的作者入口只接指定的公开数据；硬件采集到建图之间的适配尚未实现。不能把新 bag 文件路径塞给 `run_conceptgraphs.py` 并宣称已跑。下一步适配必须：

1. D435i 按真实内外参把深度投到彩色相机坐标（保留原深度和标尺），导出带原时间戳的 RGB-D 与单位／参考位姿；固定源索引，不用采样帧号冒充源时间。生成 SAM／CLIP 一次后固定前端。
2. L2 用 PointCloud2 的实际字段布局解码，按时间切扫描；固定传感器用单位位姿，转换每点世界坐标并给正确射线原点，算法输入只 XYZ／VIEWPOINT。手持片要先去畸变和提供估计位姿，不靠 IMU 积分当位置真值。
3. 按公开协议标独立可见表面、物理 ID 与事件。预留评价帧不进入 mapper；时间邻近仍相关，按完整会话统计。
4. 先用静止和四事件验证可见性，然后在同一批观测上冻结 8–15 帧的受控位姿偏差，在第 16／24／36 帧送达历史修正。先比较原核心／简单保护／冻结关联但修正几何／oracle 全量回放，再决定是否实现 H1。

完整源缓存预算、回放成本、窗口外不可恢复、拒答覆盖损失都要报告。没有这些适配和指标，只能交付“硬件采集演示”，这本身是有效的新增材料，但还不是 H1 实验结果。

## 正式测试前冻结清单

独立测试布局／会话编号、物理 ID、标注人、标注规则、源帧选择、事件实际时间、修正计划、阈值选择规则、预算、失败判据、全部比较条件。开发会话用于调参，冻结后不再按测试结果改阈值。主分支发布的是冻结协议和核验后的测量；原始家庭录制先留本地。
