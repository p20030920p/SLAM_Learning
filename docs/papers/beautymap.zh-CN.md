# BeautyMap

[English](beautymap.md) | 中文

**KITTI-00，141 帧雷达扫描。** 通过占据关系去除动态残留，并用恢复步骤保护静态结构。

![BeautyMap](../../results/reference/beautymap/media/preview.gif)

[完整视频](../../results/reference/beautymap/media/replay/replay.mp4) · [原始记录](../../results/reference/beautymap/runs/beautymap-wsl/record.json) · [时间核对](../../results/reference/beautymap/media/timing.json)

## 结果

保留的封装试跑 SA／DA／HA 为 96.9529／98.3382／97.6407%。另一组历史 KITTI-02 Table III 实验在两位小数精度下匹配全部 9 个准确率数值。

[原始代码与论文协议](https://github.com/p20030920p/SLAM_Learning/blob/535a2780af7ca7eb3aa02f722e1340fe90bc2dcf/docs/KITTI_PAPER_PROTOCOL.zh-CN.md)

## 运行

[环境与命令](../guides/REPRODUCE.zh-CN.md) · [源码来源](../guides/ATTRIBUTION.zh-CN.md)

## 范围

使用给定位姿，只检查已声明的建图阶段。视频是保存结果的回放；完整 SLAM、导航与硬件精度未验证。
