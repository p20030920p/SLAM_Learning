# ConceptGraphs

[English](conceptgraphs.md) | 中文

**Replica room0，40 次 RGB-D 观测。** 使用给定位姿，将 SAM／CLIP 观测关联并融合成物体表示。

![ConceptGraphs](../../results/reference/conceptgraphs/media/preview.gif)

[完整视频](../../results/reference/conceptgraphs/media/replay/replay.mp4) · [原始记录](../../results/reference/conceptgraphs/runs/conceptgraphs-wsl/record.json) · [时间核对](../../results/reference/conceptgraphs/media/timing.json)

## 结果

该子集生成 39 个物体表示，查询正确性未验证。另一组 400 次观测的 room0 实验完成原始语义评分，范围不等于原文完整基准。

[原始代码与论文协议](https://github.com/p20030920p/SLAM_Learning/blob/535a2780af7ca7eb3aa02f722e1340fe90bc2dcf/docs/CONCEPTGRAPHS_ROOM0_RESULTS.zh-CN.md)

## 运行

[环境与命令](../guides/REPRODUCE.zh-CN.md) · [源码来源](../guides/ATTRIBUTION.zh-CN.md)

## 范围

使用给定位姿，只检查已声明的建图阶段。视频是保存结果的回放；完整 SLAM、导航与硬件精度未验证。

## 补充视频

主 GIF 保留原来的 13.33 秒总结。

- RViz: 69.6 s. [MP4](../../results/reference/conceptgraphs/media/rviz/review.mp4) · [GIF](../../results/reference/conceptgraphs/media/conceptgraphs-rviz.gif).
- Author viewer: 60 s. [GIF](../../results/reference/conceptgraphs/media/conceptgraphs-author-viewer.gif).

[完整录像来源与时间](../../results/reference/conceptgraphs/media/full-timing.json)
