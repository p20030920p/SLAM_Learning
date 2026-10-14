# 本机现场演示

当前入口位于 F:\be2演讲\实机脚本；[刷新脚本](refresh_scripts.py)同步规范版本，并只删除已知的旧入口。最新录像见[视频目录](gallery.html)，计算方式见[评分协议](../docs/testing/LIVE.zh-CN.md)。

## 当前入口

- 01 / 02 / 05：静态、动态、新走廊建图 A；真实 Gazebo / RViz / 终端，二维 slam_toolbox 与独立三维点云采集。
- 08：处理最新走廊 A 的点云，执行 Raw / DUFOMap / BeautyMap 并生成共用二维投影。世界模型变化后，必须重新运行 05 → 08 → 23。
- 10 / 11：处理最新静态／动态建图 A，再运行相应定位入口。
- 20 / 21 / 22 / 23：静态、运动障碍、持久变化、走廊观测恢复。三个独立 RViz 窗口，各自显示地图、AMCL 位姿、粒子及隔离显示 TF，同时录三段现场。
- 24：自动重录四场景，分别记录三个方法窗口。
- 31 / 32：作者原库 NDT / GICP 三维固定地图定位，显示实时三维扫描、地图和原生位姿，录制现场。
- 论文-实时-dufomap / beautymap / ir-mcl：重新执行原库，用当前计算状态更新实际 RViz。作者公开数据与 Gazebo 平台测试分开。
- 论文-adam-mcl：一次受限原库试验，自建地图，格为单位。
- 00：查看最新视频；09：正常结束活动仿真。

## 使用

一次启动一个场景。键盘在专用 SLAM-LIVE 终端：i/k 前后、j/l 转向、u/o 横移、空格停车、q 结束；超过 0.4 秒没有按键自动停车。20–23、31–32 自动录制窗口；建图入口保存输入与点云，可通过 [presentation.ps1](presentation.ps1) 的 Record 开关录窗口。

规范入口：[record-methods.ps1](record-methods.ps1)、[presentation.ps1](presentation.ps1)、[original-live.ps1](original-live.ps1)、[original.ps1](original.ps1)、[build-maps.ps1](build-maps.ps1)、[stop-presentation.ps1](stop-presentation.ps1)。

需要本机已配置的 Ubuntu-24.04 ROS Jazzy / Gazebo Harmonic、Sim2Real 编译环境、Ubuntu-22.04 作者环境、Windows Terminal 与 FFmpeg。31–32 还使用独立 /root/slam-alternative-ws/build_ws 编译产物。[算法选择与接入](../docs/testing/LOCALIZERS.zh-CN.md)。

每次运行创建新目录 results/runs/presentation，保留 bag、真值、位姿 CSV、参数与日志。正式小产物封存在 results/reference；录像复制到 F:\be2演讲\屏幕实录\20261014-native-ui，命名含场景、模块、算法和运行 ID。[名称索引](recording-index.json)。

Live execution 是当前计算的窗口实录；Measured result replay 绘制该次保存数据，不重新推理。AMCL 对照只改变地图／扫描条件；NDT/GICP 使用三维输入，不能与二维 AMCL 的数值直接作算法排名。实体机器人测试待测。
