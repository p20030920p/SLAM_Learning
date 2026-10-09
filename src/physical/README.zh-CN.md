# 实物练习

[English](README.md) | 中文

D435／Unitree L2 采集、里程计试跑与建图输入检查。

## 手册

| 任务 | 入口 |
| --- | --- |
| 环境与采集 | [环境](docs/ENVIRONMENT.zh-CN.md) · [相机](docs/CAMERA_GUIDE.zh-CN.md) · [雷达](docs/LIDAR_GUIDE.zh-CN.md) |
| 受控实验 | [逐步操作](docs/TABLETOP_WALKTHROUGH.zh-CN.md) · [设计](METHOD_COMPARISON.zh-CN.md) |
| 建图与回放 | [集成](docs/MAIN_INTEGRATION.zh-CN.md) · [RGB-D](docs/RGBD_MAIN_INPUT.zh-CN.md) · [回放](docs/OFFLINE_REPLAY.zh-CN.md) |
| 已有检查 | [验证](docs/LIVE_VALIDATION.zh-CN.md) · [最新检查](docs/POSTFALL_LOWLIGHT.zh-CN.md) · [归档](docs/archive/INDEX.md) |

## 运行

完成[环境配置](docs/ENVIRONMENT.zh-CN.md)后，在仓库根目录的 PowerShell 执行：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File src/physical/scripts/start_live.ps1 -Sensor camera
powershell.exe -NoProfile -ExecutionPolicy Bypass -File src/physical/scripts/start_live.ps1 -Sensor lidar
```

每个传感器使用一个终端；Ctrl+C 保存会话。内部脚本以 `src/physical/` 为项目根目录。详细记录中的原始机器路径保留作历史信息。

## 状态

D435 不带 IMU。采集与 8/8 帧语义加载检查通过；实物语义建图仍在复现中。L2 数据流已恢复，早期 ICP／KISS 漂移检查失败。完整录像、SDK 缓存与环境留在本地。
