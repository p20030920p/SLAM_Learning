# 论文复现状态与保留子集

[English](README.md) | 中文

共享接口为：给定位姿观测 → 空间对应 → 地图决策。四篇 2024 年工作连接动态稳健建图与语义建图／定位。任务及输出定义不同，不组成统一排行榜。

| 论文 | 已执行范围 | 报告 | 录制 | PDF |
| --- | --- | --- | --- | --- |
| DUFOMap | 完整 141 扫描公开 teaser，动态点移除 | [论文卡](dufomap.zh-CN.md) | [MP4](../media/dufomap/replay.mp4) / [GIF](../../results/reference/media-previews-v3/dufomap.gif) | [EN](../pdf/dufomap.en.pdf) / [中文](../pdf/dufomap.zh-CN.pdf) |
| BeautyMap | 相同完整 teaser，作者地图清理 | [论文卡](beautymap.zh-CN.md) | [MP4](../media/beautymap/replay.mp4) / [GIF](../../results/reference/media-previews-v3/beautymap.gif) | [EN](../pdf/beautymap.en.pdf) / [中文](../pdf/beautymap.zh-CN.pdf) |
| ConceptGraphs | 40 次给定位姿 Replica 观测，SAM／CLIP 及对象融合 | [论文卡](conceptgraphs.zh-CN.md) | 完整 69.6 秒 [MP4](../media/rviz/conceptgraphs.mp4) / [GIF](../../results/reference/conceptgraphs-full-media/conceptgraphs-rviz.gif) | [EN](../pdf/conceptgraphs.en.pdf) / [中文](../pdf/conceptgraphs.zh-CN.pdf) |
| HOV-SG | **未复现**；默认 200 帧及论文完整实验未完成 | [状态](hovsg.zh-CN.md) | 已撤下交付展示 | 仅保留历史子集 PDF |

这些 GIF、论文卡和 PDF 对应早期给定位姿子集。后续作者原流程已有论文表格核查和限定语义评分，见 [535a278 范围](https://github.com/p20030920p/SLAM_Learning/blob/535a2780af7ca7eb3aa02f722e1340fe90bc2dcf/docs/SCOPE.zh-CN.md)。完整 SLAM、完整 benchmark、场景图推理和导航仍未完成。

[docs/pdf](../pdf) 保留录制时的生成快照，包括早期研究／实物文本，不代替当前提交叙述。当前问题与决策见 [STUDY](../research/STUDY.zh-CN.md) 和 [PLAN](../research/PLAN.zh-CN.md)。失败与资源适配继续保留。

依据[录制说明](../guides/RECORDING.zh-CN.md)从校验后的本地输出重新生成媒体／报告。[paper_suite.json](../../src/configs/paper_suite.json)绑定所选论文、原生记录、命令及语言版本。
