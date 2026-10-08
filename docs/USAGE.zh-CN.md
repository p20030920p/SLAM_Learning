# 自己操作：D435 与 L2 的本机测试流程

代码分支是 `Personal-Learning-Physical`，不是 `notes/personal-study-guide-20261008`。本流程适用于这台已配置好的 Windows 电脑及 Ubuntu 22.04 WSL。相机实测是 **D435，没有 IMU**；L2 走已供电的 USB 转串口。先运行固定会话，移动测试另行设计。

GitHub 保存脚本、文档、配置与轻量证据；`data/`、`.venv/`、`.cache/` 被忽略。新克隆不会带回本机的旧录制、视频、PCD 或已安装环境，报告中的旧媒体链接在 GitHub 上不能直接播放。

发布说明：现已按用户要求安排推送独立分支；早期实验报告中的“未 push”指当时实验结束状态。主分支仍不合并。

## 1. 进入分支与检查环境

当前电脑直接打开 PowerShell：

```powershell
Set-Location -LiteralPath D:\workspace\be2\Personal-Learning-Physical
git branch --show-current
.venv\Scripts\python.exe --version
.venv\Scripts\python.exe -m pip check
```

分支应显示 `Personal-Learning-Physical`；本机采集环境为 Python 3.12。无需切换主分支。若在另一目录重新下载，选择一个尚不存在的目标目录：

```powershell
git clone --branch Personal-Learning-Physical https://github.com/p20030920p/SLAM_Learning.git Personal-Learning-Physical
```

新克隆需要按 [README 的环境配置](../README.zh-CN.md#操作入口)重新创建 Windows 环境及固定版本 Unitree SDK。后文 WSL 命令还依赖 ROS2 Humble／RTAB-Map、系统 NumPy／SciPy／Matplotlib／OpenCV／ffmpeg 和独立 KISS 环境；它们不包含在 Windows `requirements.txt` 中。主分支接口命令使用本机已有的专用运行环境，不能直接换成 Windows `.venv`。

## 2. 固定设备并同时录制

相机前方移开黑色立柱、白布等近物，朝向约 1–3 m 的有纹理墙角、家具或纸箱，避开直射灯和亮屏。L2 底座平稳、周围无遮挡，视野包含不同方向的平面。两台设备在整段录制中保持不动；先记录这一事实，才可把结果作为静止测试。

```powershell
.\scripts\capture_pair.ps1 -Seconds 60 -Session static-manual
```

脚本会重新查找 CH343 实体串口，绕开本机虚拟／实体 COM3 同名问题。结束时显示新目录，如 `data\static-manual-YYYYMMDD-HHMMSS`；只发送 L2 版本查询，不修改固件或时钟。两设备同时录制不代表硬件同步。

找到刚生成的目录并核验：

```powershell
$taskSession = (Get-ChildItem -LiteralPath data -Directory -Filter 'static-manual-*' | Sort-Object LastWriteTime -Descending | Select-Object -First 1).FullName
$taskSession
.venv\Scripts\python.exe scripts\verify_camera_recording.py "$taskSession\camera\raw.db3"
.venv\Scripts\python.exe scripts\analyze_static.py $taskSession
```

`capture_pair.ps1` 已自动运行 `audit_l2.py`。`analyze_static.py` 仅用于上述实际固定、超过 10 秒的会话，它不会自动判断设备是否被移动。

| 看哪个文件 | 应看什么 |
| --- | --- |
| `camera/capture.json` | 型号、四路帧率、帧号缺失、深度有效比例及中央深度；收流应约 30 fps，项目检查目标为无帧号缺失 |
| `camera/playback-v2.json` | `status=verified`、SQLite／SDK 图像数量一致、实时帧号均被保留；原始启动帧可比实时帧组多 |
| `l2/capture.json`、`l2/audit.json` | 点云和 IMU 均有数据，CRC／序号缺失目标为 0；本机曾测得约 215 线包/s、250 IMU 包/s，线包不等于完整一圈 |
| `static-audit.json` | 固定会话的深度与原始 IMU 统计；未加入卷尺参考，不能称测距精度或惯性定位通过 |
| 两路 `preview.mp4` | 实际视野是否合适、点云是否成形；采集视频没有运行定位算法 |

若收到 `Camera exit`、`L2 exit` 或脚本报错，先读对应 `capture.json` 的 `error`。相机被其他查看器占用时先关闭查看器。串口枚举不明确时运行 `Get-PnpDevice -PresentOnly -Class Ports` 查看，不要把默认 `Serial2` 当作每次插拔后都正确的地址。

## 3. 导出算法输入

以下以首次运行的 `manual-*-01` 为输出名。以后把同一轮的所有 `01` 一起改为 `02`，保留旧结果；导出及运行目录必须尚不存在。

PowerShell 导出相机左右 IR：

```powershell
.venv\Scripts\python.exe scripts\export_stereo.py "$taskSession\camera\raw.db3" --output data\manual-stereo-01
```

然后打开 **WSL Ubuntu 22.04**。把下面 `task_session` 改成第 2 步实际显示的目录名，使用 `/`：

```bash
cd /mnt/d/workspace/be2/Personal-Learning-Physical
task_session=data/static-manual-YYYYMMDD-HHMMSS
g++ -O2 -std=c++17 scripts/decode_sdk_lines.cpp \
  -I.cache/unilidar_sdk2/unitree_lidar_sdk/include -o .cache/decode_sdk_lines_checked
python3 scripts/export_l2_clouds.py "$task_session/l2" --lines 50 \
  --sdk-decoder .cache/decode_sdk_lines_checked --output data/manual-l2-01
```

正常输出为 `stereo.json`／`clouds.json` 和各帧文件，`status=exported`。默认跳过前 2 秒；相机每 3 帧取一对，L2 每 50 线聚合一次。L2 使用已记录的主机接收时间，不做 IMU 融合或去畸变；原始设备时间仍保留。

## 4. 运行定位并看视频

仍在 WSL 中，先检查已有 ROS 环境：

```bash
source /opt/ros/humble/setup.bash
ros2 pkg prefix rtabmap_odom
python3 scripts/run_odometry_baseline.py data/manual-stereo-01 --output data/manual-stereo-run-01
python3 scripts/run_odometry_baseline.py data/manual-l2-01 --mode lidar --output data/manual-icp-run-01
python3 scripts/render_odometry_video.py data/manual-stereo-01 data/manual-stereo-run-01
python3 scripts/render_odometry_video.py data/manual-l2-01 data/manual-icp-run-01
```

独立运行 KISS-ICP。本机已有 `.cache/kiss-venv`；新克隆时先运行下面两行建立环境，已有环境直接使用：

```bash
python3 -m venv .cache/kiss-venv
.cache/kiss-venv/bin/python -m pip install -r requirements-kiss-wsl.txt
```

```bash
OPENBLAS_NUM_THREADS=2 .cache/kiss-venv/bin/python scripts/run_kiss_baseline.py \
  data/manual-l2-01 --output data/manual-kiss-run-01
python3 scripts/render_odometry_video.py data/manual-l2-01 data/manual-kiss-run-01
```

每个运行目录保存 `result.json`、`poses.json`、`status.json`；渲染后有 `preview.mp4`。在 Windows 中直接打开这些文件。ROS 测试顺序执行，默认通信域为 83。

| 算法 | 正常视频效果 | 本项目静止目标与现有结果 |
| --- | --- | --- |
| RTAB-Map Stereo | 真实左右 IR 上方显示，下方轨迹贴近起点、局部地图稳定 | 位姿／状态覆盖 ≥99%、lost=0、最大平移 ≤5 cm、转角 ≤2°；旧固定会话通过，但移动、回环未验 |
| RTAB-Map ICP／KISS-ICP | 原始点云与估计轨迹同屏；固定设备的地图不能持续旋转或错位 | 同样检查 5 cm／2°；KISS 没有 lost 标志，有限位姿不代表对齐正确。旧真实会话两者均失败 |
| DUFOMap／BeautyMap | 下面的接口测试显示输入、输出和缺失坐标；墙与家具应保留，受控动态拖影应减少 | 还需要标注静态保留率 SA、动态清除率 DA、误删和耗时；输出／输入点数比不是 SA |

5 cm／2°是项目排查目标，不是厂商规格、ATE 或测距精度。视频是已保存算法输出的回放，并非实时运行画面。KISS 关闭速度外推及重复同一帧属于额外诊断，命令和解释见 [第三轮报告](DIAGNOSTICS_ROUND3.zh-CN.md)，不能替换默认基线。

## 5. 使用主分支的原适配器

以下只适用于**确实固定的 60 秒会话**。原地图算法消费点云和给定位姿，不负责从传感器直接估计轨迹；这里明确使用固定单位位姿。命令读取 main 的固定 Git 提交，不修改 main。

在本机 WSL、仍位于本分支目录：

```bash
OPENBLAS_NUM_THREADS=2 /home/qzl/projects/SLAM_Learning/.venv/bin/python scripts/run_main_dufomap.py \
  data/manual-l2-01 --main-repo /mnt/d/workspace/be2/SLAM_Learning \
  --fixed-sensor-session --output data/manual-dufomap-01
python3 scripts/render_dufomap_smoke.py data/manual-dufomap-01

OPENBLAS_NUM_THREADS=2 /home/qzl/projects/SLAM_Learning/.venv/bin/python scripts/run_main_beautymap.py \
  data/manual-dufomap-01 --main-repo /mnt/d/workspace/be2/SLAM_Learning \
  --upstream /home/qzl/projects/SLAM_Learning/.cache/upstream/beautymap \
  --fixed-sensor-session --output data/manual-beautymap-original-01
```

查看 `record.json`、`worker.log` 和输出 `cleaned.pcd`。旧数据的 DUFOMap 原入口可执行；BeautyMap 原入口因小地图边界越界失败，以上第二条可能返回非零，失败应保留。局部扩域诊断用**新目录**另外运行：

```bash
OPENBLAS_NUM_THREADS=2 /home/qzl/projects/SLAM_Learning/.venv/bin/python scripts/run_main_beautymap.py \
  data/manual-dufomap-01 --main-repo /mnt/d/workspace/be2/SLAM_Learning \
  --upstream /home/qzl/projects/SLAM_Learning/.cache/upstream/beautymap \
  --fixed-sensor-session --pad-small-map-control --output data/manual-beautymap-control-01
python3 scripts/render_dufomap_smoke.py data/manual-beautymap-control-01
```

`comparison.png` 的红色只表示输入 XYZ 未出现在输出中，可能包含静态误删；扩域控制也有适用边界，不能称主分支已修复。ConceptGraphs／HOV-SG 的实物 RGB-D 接口尚未完成，不能直接拿本次录制宣称运行通过。下一阶段的受控事件、移动定位、标定与质量指标见 [完整测试计划](TEST_PLAN.zh-CN.md)和 [主分支集成流程](MAIN_INTEGRATION.zh-CN.md)。

## 6. 保存自己的修改和同步

PowerShell 中确认仍在独立分支，选择源码、文档和轻量证据后提交：

```powershell
git branch --show-current
git status --short
git add -- README.zh-CN.md docs scripts evidence
git diff --cached --stat
git commit -m "Record my physical sensor experiment"
git push origin Personal-Learning-Physical
```

没有修改时不需要 commit；这组命令不会上传被忽略的 `data/`。以后同步已发布分支可运行 `git pull --ff-only`，有本地改动时先整理自己的提交。不要在学习分支执行整分支合并到 main；它是 orphan 历史。正式集成应从 main 建新分支、筛选移植、运行原回归和实物验收、审阅后再决定合并。
