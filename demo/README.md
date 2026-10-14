# 本机现场演示

当前入口位于 F:\be2演讲\实机脚本；[刷新脚本](refresh_scripts.py)同步规范版本，并只删除已知的旧入口。最新录像见[视频目录](gallery.html)，计算方式见[评分协议](../docs/testing/LIVE.zh-CN.md)。

## 当前入口

- 01 / 02 / 05：静态、动态、新走廊建图 A；真实 Gazebo / RViz / 终端，二维 slam_toolbox 与独立三维点云采集。
- 08：处理最新走廊 A 的点云，执行 Raw / DUFOMap / BeautyMap 并生成共用二维投影。世界模型变化后，必须重新运行 05 → 08 → 23。
- 10 / 11：处理最新静态／动态建图 A，再运行相应定位入口。
- 20 / 21 / 22 / 23：静态、运动障碍、持久变化、走廊观测恢复。三个独立 RViz 窗口，各自显示地图、AMCL 位姿、粒子及隔离显示 TF，同时录三段现场。
- 24：自动重录四场景，分别记录三个方法窗口。
- 31 / 32：作者原库 NDT / GICP 三维固定地图定位，显示实时三维扫描、地图和原生位姿，录制现场。
- 33 / 34 / 35 / 36：相同四种场景，Raw／DUFOMap／BeautyMap三维地图共用原库GICP，分别录三个真实RViz窗口。静态、动态、持久变化90仿真秒，走廊120秒；三维走廊也限制、恢复观测。
- 37：已计算好的三维清理地图结果展示，灰色静态、红色残留动态；不执行新推理。
- 论文-实时-dufomap / beautymap / ir-mcl：重新执行原库，用当前计算状态更新实际 RViz。作者公开数据与 Gazebo 平台测试分开。
- 论文-adam-mcl：一次受限原库试验，自建地图，格为单位。
- 00：查看最新视频；09：正常结束活动仿真。

## 使用

一次启动一个场景。键盘在专用 SLAM-LIVE 终端：i/k 前后、j/l 转向、u/o 横移、空格停车、q 结束；超过 0.4 秒没有按键自动停车。20–23、31–32 自动录制窗口；建图入口保存输入与点云，可通过 [presentation.ps1](presentation.ps1) 的 Record 开关录窗口。

规范入口：[record-methods.ps1](record-methods.ps1)、[presentation.ps1](presentation.ps1)、[original-live.ps1](original-live.ps1)、[original.ps1](original.ps1)、[build-maps.ps1](build-maps.ps1)、[stop-presentation.ps1](stop-presentation.ps1)。

需要本机已配置的 Ubuntu-24.04 ROS Jazzy / Gazebo Harmonic、Sim2Real 编译环境、Ubuntu-22.04 作者环境、Windows Terminal 与 FFmpeg。31–32 还使用独立 /root/slam-alternative-ws/build_ws 编译产物。[算法选择与接入](../docs/testing/LOCALIZERS.zh-CN.md)。

每次运行创建新目录 results/runs/presentation，保留 bag、真值、位姿 CSV、参数与日志。正式小产物封存在 results/reference；录像复制到 F:\be2演讲\屏幕实录\20261014-native-ui，命名含场景、模块、算法和运行 ID。[名称索引](recording-index.json)。

Live execution 是当前计算的窗口实录；Measured result replay 绘制该次保存数据，不重新推理。AMCL 对照只改变地图／扫描条件；NDT/GICP 使用三维输入，不能与二维 AMCL 的数值直接作算法排名。实体机器人测试待测。

## 2D与3D分开看

[视频目录](gallery.html#2d)先列二维AMCL，再列[三维GICP](gallery.html#3d)，每场景只用“方法／地图类型／指标效果”三列。[本轮原因分析与地图点级评分](../docs/testing/MAP-2D-3D.zh-CN.md)。录像镜像按`2D`、`3D`子目录保存；旧录像和较早NDT／GICP单地图试验作为历史保留。

脚本也可指定：`record-methods.ps1 -Scene dynamic -Dimension 3D -Duration 90`。三维地图仍来自给定位姿的建图A，不代表已完成完整三维SLAM。

## 开放问题：假设与简单实验

[假设、对照与实验结果](../docs/testing/HYPOTHESES.zh-CN.md) · [新视频目录](hypotheses.html)。

- 38：采集假设实验地图A，真实二维／三维雷达＋深度相机；四份A分别对应静态、动态、原走廊与高处几何派生对照。
- 39：打开本机假设实验视频目录。
- 40–44：二维雷达＋深度，五场景依次录制；45–49：三维雷达＋深度，对应相同五场景。
- 50：自动完成十组计算、真实窗口录制、位姿／输入检查及本机视频目录更新。地图A缺失时先采集。每次新目录，参数与全部结果保留。
- 51–54：二维／三维原走廊和高处对照的同输入搜索细化；55自动重算四组。视频为新推理后保存输出的结果回放。

规范入口：[record-probes.ps1](record-probes.ps1)、[record-all-probes.ps1](record-all-probes.ps1)、[build-probe-maps.ps1](build-probe-maps.ps1)、[refine-probes.ps1](refine-probes.ps1)。二维B机器人不含三维雷达；三维原型使用XYZ观测、约束地面x/y/yaw。原生AMCL／GICP为同源参照，原型之间才是严格同帧配对。地图冻结，不宣称完整六自由度SLAM或在线更新。

新结果在 `F:\be2演讲\本轮成片\hypotheses`，按2D／3D分开，页面自带可跳转目录和三列表格。录屏准备阶段定位器已开始计算；早于视频的起始误差与接受事件保存在CSV和日志中。

校准版原始会话位于 `F:\be2演讲\原始会话\hypotheses-calibrated`。车体高度由独立建图A位姿与实际URDF外参得到，定位B不读取真值；固定高度只用于本轮平坦地面。首轮高度设置错误的十组与无效细化结果保留为排查档案。
