# 四篇相关论文复现

[English](README.md) | 中文

共享接口为：给定位姿观测 → 空间对应 → 地图决策。四篇 2024 年工作连接动态稳健建图与语义建图／定位。任务及输出定义不同，不组成统一排行榜。

| 论文 | 已执行范围 | 报告 | 录制 | PDF |
| --- | --- | --- | --- | --- |
| DUFOMap | 完整 141 扫描公开 teaser，动态点移除 | [论文卡](dufomap.zh-CN.md) | [MP4](../media/dufomap/replay.mp4) / [GIF](../media/dufomap/preview.gif) | [EN](../../output/pdf/dufomap.en.pdf) / [中文](../../output/pdf/dufomap.zh-CN.pdf) |
| BeautyMap | 相同完整 teaser，作者地图清理 | [论文卡](beautymap.zh-CN.md) | [MP4](../media/beautymap/replay.mp4) / [GIF](../media/beautymap/preview.gif) | [EN](../../output/pdf/beautymap.en.pdf) / [中文](../../output/pdf/beautymap.zh-CN.pdf) |
| ConceptGraphs | 40 次给定位姿 Replica 观测，SAM／CLIP 及对象融合 | [论文卡](conceptgraphs.zh-CN.md) | [MP4](../media/conceptgraphs/replay.mp4) / [GIF](../media/conceptgraphs/preview.gif) | [EN](../../output/pdf/conceptgraphs.en.pdf) / [中文](../../output/pdf/conceptgraphs.zh-CN.pdf) |
| HOV-SG | 8 次给定位姿观测，分段特征建图核心 | [论文卡](hovsg.zh-CN.md) | [MP4](../media/hovsg/replay.mp4) / [GIF](../media/hovsg/preview.gif) | [EN](../../output/pdf/hovsg.en.pdf) / [中文](../../output/pdf/hovsg.zh-CN.pdf) |

全部使用给定位姿。完整 SLAM、语义论文 benchmark、场景图推理及导航未完成。保留失败和资源适配。[四篇共性分析](../STUDY.zh-CN.md)与 [D435i／L2 实物方案](../REAL_WORLD.zh-CN.md)另有双语 PDF，见 [output/pdf](../../output/pdf)。

依据[录制说明](../RECORDING.zh-CN.md)从校验后的本地输出重新生成媒体／报告。[paper_suite.json](../../configs/paper_suite.json)绑定所选论文、原生记录、命令及语言版本。
