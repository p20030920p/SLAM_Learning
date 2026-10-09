# 历史资料索引

这些文件保留当时的设备状态、原始失败、修正依据和复现命令。文中“本次未推送”“仍待执行”等是当时状态；当前使用以[相机](../CAMERA_GUIDE.zh-CN.md)、[雷达](../LIDAR_GUIDE.zh-CN.md)和[实时验证](../LIVE_VALIDATION.zh-CN.md)为准。

| 文件 | 用途 |
| --- | --- |
| [硬件发现](HARDWARE_STATUS.zh-CN.md) | 型号、USB/串口、收流与时间问题 |
| [首轮基线](BASELINE_RESULTS.zh-CN.md) | 采集与最初测量，含无独立参考的限制 |
| [第二轮](DIAGNOSTICS_ROUND2.zh-CN.md) | SDK 原生几何、双目/ICP/KISS、DUFOMap、回放审计 |
| [第三轮](DIAGNOSTICS_ROUND3.zh-CN.md) | KISS 速度预测对照、BeautyMap 边界失败/扩域回归 |
| [旧使用流程](USAGE.zh-CN.md) | 并发采集、核验、导出、离线算法 |
| [旧相机教程](CAMERA_WALKTHROUGH.zh-CN.md) | 从 WSL 到离线视频，原始步骤追溯 |
| [旧测试计划](TEST_PLAN.zh-CN.md) | 前一版计划，对照当前目标变更 |

`../../data/` 链接仅当前电脑存在，GitHub 不含录像。`../../evidence/` 数字证据跟随仓库。历史指标不重算成“通过”，新会话另保存证据。
