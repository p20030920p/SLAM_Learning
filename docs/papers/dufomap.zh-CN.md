# DUFOMap

[English](dufomap.md) | 中文

**KITTI-00，141 帧雷达扫描。** 利用观测到的空闲空间识别动态点，并用位姿裕量保护静态结构。

![DUFOMap](../../results/reference/dufomap/media/preview.gif)

[完整视频](../../results/reference/dufomap/media/replay/replay.mp4) · [原始记录](../../results/reference/dufomap/runs/dufomap-wsl/record.json) · [时间核对](../../results/reference/dufomap/media/timing.json)

## 结果

保留的封装试跑 SA／DA／AA 为 97.9798／98.7029／98.3407%。另一组原始 C++ Table IV 实验在两位小数精度下匹配全部 15 个准确率数值。

[原始代码与论文协议](https://github.com/p20030920p/SLAM_Learning/blob/535a2780af7ca7eb3aa02f722e1340fe90bc2dcf/docs/DUFOMAP_TABLE4.zh-CN.md)

## 运行

[环境与命令](../guides/REPRODUCE.zh-CN.md) · [源码来源](../guides/ATTRIBUTION.zh-CN.md)

## 范围

使用给定位姿，只检查已声明的建图阶段。视频是保存结果的回放；完整 SLAM、导航与硬件精度未验证。
