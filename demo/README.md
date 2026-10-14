# 本机实时演示

这些入口连接公开 [SLAM-Physical](https://github.com/p20030920p/SLAM-Physical) 仓库。实验代码位于本库同级的 `SLAM-Physical` 文件夹；首次缺失时自动克隆。当前本机算法环境已准备，先双击 `00_check.cmd`。

| 双击文件 | 功能 |
|---|---|
| 00_check.cmd | 检查本机环境 |
| 00_setup.cmd | 安装专用仿真环境和固定版本资产 |
| 01_reproduce.cmd | 菜单选择四个算法，重新计算并显示 RViz |
| 02_experiment.cmd | 静态 BeautyMap C1/C2/C4 实验 |
| 04_departure_experiment.cmd | 首个物体离场实验 |
| 03_stop.cmd | 停止本次运行 |
| 90_update.cmd | 更新 SLAM-Physical main，保留本地结果 |
| 10_amcl_keyboard.cmd | Windows 键盘驾驶、AMCL 实时偏移与自动录制 |
| 11_build_localization_maps.cmd | 用一次驾驶生成论文方法的定位地图 |
| 12_amcl_choose_map.cmd | 选算法地图后键盘驾驶与观看偏移 |
| 13_compare_localization.cmd | 用另一录制，在各地图上回放同一输入进行定位对照 |
| 14_static_keyboard.cmd | 纯静态场景，真实录制地图，键盘测试并自动录制 |
| 15_dynamic_keyboard.cmd | 动态场景，选择原始/论文地图，键盘测试并自动录制 |
| 16_record_static_dynamic.cmd | 自动录制两种场景、运行论文算法、重复定位对比及导出数据回放视频 |

窗口内显示实际命令及进度；完成后按 Enter 关闭。结果写入 `SLAM-Physical/runs/`。源代码、实验协议与已实跑结果见实验仓库 README。

入口面向当前 Windows / WSL2 / CUDA 机器，依赖已准备的 Ubuntu-22.04 作者环境；`00_setup.cmd` 只安装 Ubuntu-24.04 仿真侧，不能替代全部算法、数据与权重安装。现有私有库不需要公开或复制到这里。
## 本轮真正的 Gazebo＋RViz＋终端

2026-10-14 新入口在 `F:\be2演讲\实机脚本`，规范版本为 [presentation.ps1](presentation.ps1)、[original.ps1](original.ps1)、[build-maps.ps1](build-maps.ps1)及[stop-presentation.ps1](stop-presentation.ps1)。依赖本机已编译的 Ubuntu-24.04 ROS Jazzy／Gazebo Harmonic Sim2Real 环境、Ubuntu-22.04 原作者环境、Windows Terminal 和 Windows FFmpeg；不是在未配置电脑上双击就自动安装全部论文依赖。

| 双击文件 | 行为 |
| --- | --- |
| 00-查看本轮视频.bat | 打开现场／本次结果成对的视频页面 |
| 01-静态建图与三维点云.bat | 原生二维 SLAM＋独立三维点云，手动键盘 |
| 02-动态建图与三维点云.bat | 三个运动障碍物，同上 |
| 03-静态定位对照.bat | 三种地图、相同 AMCL，手动键盘 |
| 04-动态定位与论文地图对照.bat | 六组同时定位，手动键盘 |
| 05-走廊点云建图.bat | 匹配走廊的独立建图 A，手动键盘 |
| 06-退化定位与观测恢复.bat | 走廊完整／受限扫描对照；开始后50个仿真秒恢复完整扫描 |
| 07-持久结构变化定位.bat | 新结构＋旧静态地图，手动键盘 |
| 08-处理最新走廊地图.bat | 用最新走廊 A 真实点云执行原生 DUFOMap／BeautyMap与共用投影 |
| 09-正常停止仿真.bat | 给本轮活动仿真发正常结束标记 |
| 重录-动态.bat / 重录-退化.bat | 自动驾驶、真实窗口录制、保存输入 bag 和评分；每次新目录 |
| 重录-四类场景.bat | 依次录制静态、动态、持久变化、走廊退化 |
| 论文-dufomap.bat / 论文-beautymap.bat / 论文-ir-mcl.bat / 论文-adam-mcl.bat | 重新执行原作者入口，实际 Windows终端录像，保留原始输出 |

键盘在专用 `SLAM-LIVE` 终端：i/k前后、j/l转向、u/o横移、空格停止、q结束。按住键靠键盘重复触发，超过0.4秒未收到按键自动停止。手动入口默认不录窗口，但保存实际ROS输入和评分；“重录”入口自动录制窗口。走廊键盘模式需要在恢复后继续运动，AMCL运动阈值会使完全静止时没有新的位姿更新。

现有最新地图标记优先；没有标记时可用仓库已封存的对应场景地图。若要用自己新采集的地图，先完成建图并按相应 `build-maps.ps1 -Scene static|dynamic|corridor` 处理，再运行定位。原算法、训练权重、数据与上游依赖各自保留本机路径；论文录制不把KITTI/Bonn真实数据伪装成Gazebo场景。AdaM默认10次试验，快速现场可用 `original.ps1 -Method adam-mcl -Trials 1 -Record`，单位为格。

场景世界和巡航脚本已放入本库，区分固定原机器人与本地场景适配。完整录像、bag与算法大产物留在 `results/runs/presentation`；公开小产物见 `results/reference/robot-*` 和 `desktop-*`。每条录像的计算口径与限制见[本机协议](../docs/testing/LIVE.zh-CN.md)。

现场录像命名为 `场景__模块__算法或地图处理__日期时间-运行ID.mp4`，本轮15段的名称与证据对应见[录像索引](recording-index.json)。本机目录另附 `视频名称对照.csv/json`，明确标出正式执行、额外采集、诊断及启动测试。A-建图使用 slam_toolbox 和给定位姿三维点云采集；B-定位统一使用 AMCL，Raw／DUFOMap／BeautyMap 表示地图处理。首页每种方法的结果回放从同场景保存数据单独导出，现场录像为同一次并行执行。重新导出命令：`python src/scripts/presentation/package_case_replays.py results/reference/robot-static results/reference/robot-dynamic results/reference/robot-large-change results/reference/robot-degradation`。

## 逐方法独立 RViz 现场对照

本轮每类环境分别启动 Raw、DUFOMap、BeautyMap 的原生 AMCL 和三个真实 RViz 窗口。每个窗口订阅自己的地图、位姿、粒子和隔离的显示 TF；同一场景共享实时传感器与轮速。`record-methods.ps1 -Scene static|dynamic|large-change|degradation` 自动驾驶并同时录制三段独立现场视频；加 `-Keyboard -Duration 86400` 使用键盘演示。走廊窗口展示受限→恢复扫描实例，完整扫描控制组也运行并保存评分。

本机新增 `20–23-*_三方法独立RViz实时.bat` 四个键盘入口、`24-自动重录四场景_逐方法实时.bat` 和 `论文-实时-dufomap/beautymap/ir-mcl.bat`。规范脚本：[record-methods.ps1](record-methods.ps1)、[original-live.ps1](original-live.ps1)。原库入口通过本次原生计算的只读状态显示器实时更新 RViz，不载入历史结果冒充执行；作者原数据与 Gazebo 平台适配分开。完整状态保留在本次 `results/runs/presentation/*-author-live-*`；点/粒子只在显示时稀疏采样，观察器开销不用于论文运行时间比较。请先正常结束一个同类现场演示再开下一场。

本轮15段新现场视频与此前15段归档见[录像索引](recording-index.json)。主页、[本地视频页](gallery.html)均逐场景、逐方法展示；旧视频页保留为[历史页](archive-20261014.html)。
