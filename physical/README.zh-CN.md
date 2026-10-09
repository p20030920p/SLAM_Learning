<div align="center">

# Personal-Learning-Physical

[English](README.md) | 中文

</div>

本机 D435 与宇树 L2 的实物学习分支。工作目录：`D:\workspace\be2\Personal-Learning-Physical`。

本项目已与学习笔记合并到 `notes/personal-study-guide-20261008` 的 `physical/` 目录；原始提交历史保留，main 未修改。下方绝对路径指仍保留的本地设备工作区；新克隆请以本目录作为项目根目录。

## 1. 测试背景与目标

盒子被遮住、搬走或换位置，以及历史位姿被修正，都会影响地图中的空间对应。我们要测稳定几何是否保留、查询目标坐标是否有效，以及简单保护与重新关联各自能恢复多少目标。

同一房间录制一次，在同任务方法间重放：DUFOMap／BeautyMap 比较地图清理，ConceptGraphs／HOV-SG 比较语义目标；固定输入、位姿、事件和预算，分开评分。[同场景跨仓库对比设计](METHOD_COMPARISON.zh-CN.md)列出背景、四事件、视频预期、指标、预算和失败判据。它是待执行协议；现有收流与加载检查尚未完成质量比较。

## 2. 从这里开始

| 你现在想做什么 | 指南 |
| --- | --- |
| 用盒子、水杯、纸质笔记本和鼠标，从开终端到逐段录制与检查 | [逐步实验操作](docs/TABLETOP_WALKTHROUGH.zh-CN.md) |
| 明确研究问题，在相同背景与输入上比较不同仓库 | [对比实验设计](METHOD_COMPARISON.zh-CN.md) |
| 打开相机，实时切 RGB/深度/IR/点云，运行双目、RGB-D 与建图 | [相机操作](docs/CAMERA_GUIDE.zh-CN.md) |
| 打开雷达，实时看点云，运行 ICP/KISS，了解 Point-LIO 条件 | [雷达操作](docs/LIDAR_GUIDE.zh-CN.md) |
| 按步骤拿着设备测试，知道正常画面和合格指标 | [测试计划与预期](docs/TEST_PLAN.zh-CN.md) |
| 测主分支 DUFOMap/BeautyMap/ConceptGraphs/HOV-SG，以后准备合入 | [主分支适配与合入门槛](docs/MAIN_INTEGRATION.zh-CN.md) |
| 复现真实 RGB-D 导出和两套作者加载器检查 | [RGB-D 实物输入](docs/RGBD_MAIN_INPUT.zh-CN.md) |
| 环境丢失、Shell/串口/RViz 出错 | [环境与排错](docs/ENVIRONMENT.zh-CN.md) |
| 查本次确实运行了什么 | [实时入口验证](docs/LIVE_VALIDATION.zh-CN.md) |
| 查相机固定对照、动态干扰与最新雷达收流复查 | [实物第四轮](docs/CAMERA_TEST_ROUND4.zh-CN.md) |
| 一行自动录制相机算法视频 | [简易录像](docs/SIMPLE_RECORDING.zh-CN.md) |
| 不需现场配合，用原录像自动对照送帧性能和里程计 | [无人值守回放](docs/OFFLINE_REPLAY.zh-CN.md) |
| 查摔落后检查、关灯对照、双设备并行算法和录像 | [摔落与弱光实测](docs/POSTFALL_LOWLIGHT.zh-CN.md) |
| 查整理范围、旧实验和脚本用途 | [清理记录](docs/CLEANUP.zh-CN.md)、[历史资料](docs/archive/INDEX.zh-CN.md) |

## 3. 最短启动方式

按 Win+X 打开 Windows PowerShell，确认提示符 `PS ...>`。每次执行一行；同一设备只运行一个会话。脚本自动打开 WSL 和 RViz，回到 PowerShell 按 Ctrl+C 停止。

相机预览：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File D:\workspace\be2\Personal-Learning-Physical\scripts\start_live.ps1 -Sensor camera
```

雷达预览（独立供电、USB 转串口已接）：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File D:\workspace\be2\Personal-Learning-Physical\scripts\start_live.ps1 -Sensor lidar
```

图像/点云预览没有定位。按指南换 `-Algorithm stereo`、`rgbd`、`rgbd-slam`、`icp`、`kiss`；算法切换需先停止再重启。`-Record` 保存原始录制，`-Seconds 60` 自动停止，`-SessionType stationary/motion` 记录你的实际动作声明。

## 4. 当前结论

| 设备/算法 | 状态 |
| --- | --- |
| 相机 | SDK 实测 **D435，没有 IMU**；摔落后四路原始回放、稳态约 30 Hz、双目几何初检通过；有启动停顿，绝对测距精度尚未复验。旧确认固定双目基线保留 |
| 相机实时 | 修复 ROS 逐字节赋值开销；本轮弱光并行 RGB-D/stereo 输入约 8.11/8.17 Hz、有效覆盖 97.51%/98.14%。原录像离线送帧达到 10 Hz，但严格覆盖 98.8% 未过 99% 门槛。旧固定结果及动态干扰失败保留，完全静态/移动精度仍待完成 |
| L2 | 本轮重新供电后点云/IMU 恢复；弱光双设备三段收流正常，并已录下有效 ICP/KISS RViz 视频。旧 32 字节失败记录保留 |
| L2 定位 | 旧确认固定的 ICP/KISS 漂移均超标；新并行预览仍有大幅估计位姿游走；原始设备时间比例约 2，IMU/Point-LIO/跨设备融合尚未验收 |
| 主分支算法 | DUFOMap 固定输入接口已跑；BeautyMap 原边界失败、局部扩域对照保留；真实 RGB-D 导出及 ConceptGraphs/HOV-SG 原生加载器各 8/8 帧通过；语义核心及 SA/DA 等正式质量指标未验 |

目录分工：`scripts/` 可执行采集/算法/诊断；`configs/rviz/` 实时显示配置；`docs/` 当前指南；`docs/archive/` 历史实验；`evidence/` 轻量数字证据。`data/` 原始录制/视频、`.venv/`、`.cache/` 留本机，不上传；新克隆不能直接播放旧本地媒体。
