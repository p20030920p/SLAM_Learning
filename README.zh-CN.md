# Personal-Learning-Physical

本机 D435 与宇树 L2 的实物学习分支。工作目录：`D:\workspace\be2\Personal-Learning-Physical`。独立 orphan 分支；主分支未修改、未合并。推送到 [SLAM_Learning / Personal-Learning-Physical](https://github.com/p20030920p/SLAM_Learning/tree/Personal-Learning-Physical)，不是 `notes/personal-study-guide-20261008`。

## 从这里开始

| 你现在想做什么 | 指南 |
| --- | --- |
| 打开相机，实时切 RGB/深度/IR/点云，运行双目、RGB-D 与建图 | [相机操作](docs/CAMERA_GUIDE.zh-CN.md) |
| 打开雷达，实时看点云，运行 ICP/KISS，了解 Point-LIO 条件 | [雷达操作](docs/LIDAR_GUIDE.zh-CN.md) |
| 按步骤拿着设备测试，知道正常画面和合格指标 | [测试计划与预期](docs/TEST_PLAN.zh-CN.md) |
| 测主分支 DUFOMap/BeautyMap/ConceptGraphs/HOV-SG，以后准备合入 | [主分支适配与合入门槛](docs/MAIN_INTEGRATION.zh-CN.md) |
| 环境丢失、Shell/串口/RViz 出错 | [环境与排错](docs/ENVIRONMENT.zh-CN.md) |
| 查本次确实运行了什么 | [实时入口验证](docs/LIVE_VALIDATION.zh-CN.md) |
| 查相机固定对照、动态干扰与最新雷达收流复查 | [实物第四轮](docs/CAMERA_TEST_ROUND4.zh-CN.md) |
| 一行自动录制相机算法视频 | [简易录像](docs/SIMPLE_RECORDING.zh-CN.md) |
| 查整理范围、旧实验和脚本用途 | [清理记录](docs/CLEANUP.zh-CN.md)、[历史资料](docs/archive/INDEX.zh-CN.md) |

## 最短启动方式

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

## 当前结论

| 设备/算法 | 状态 |
| --- | --- |
| 相机 | SDK 实测 **D435，没有 IMU**；四路收流正常。旧确认固定双目基线通过初期目标，移动精度未验 |
| 相机实时 | 四图与点云及定位入口可运行，桥接约 4–6 Hz。前景干扰段曾超标；最新固定相机、动态背景段 RGB-D 2.06 mm/0.387°、双目 1.66 mm/0.249°，数值在目标内，完全静态对照仍待完成 |
| L2 | 历史点云／IMU及 ICP/KISS 已运行；最新复查实体串口仍在，但仅收到 32 字节、无有效点云，待检查独立供电／接线 |
| L2 定位 | 旧确认固定的 ICP/KISS 漂移均超标；原始设备时间比例约 2，IMU/Point-LIO 尚未验收 |
| 主分支算法 | DUFOMap 固定输入接口已跑；BeautyMap 原边界失败、局部扩域对照保留；语义实物接口和 SA/DA 等正式质量指标未验 |

目录分工：`scripts/` 可执行采集/算法/诊断；`configs/rviz/` 实时显示配置；`docs/` 当前指南；`docs/archive/` 历史实验；`evidence/` 轻量数字证据。`data/` 原始录制/视频、`.venv/`、`.cache/` 留本机，不上传；新克隆不能直接播放旧本地媒体。
