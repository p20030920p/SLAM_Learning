<div align="center">

# SLAM Learning

**地图什么时候应该相信世界发生了变化？**

动态环境稳健建图 · 语义建图与定位

[![CPU reproducibility](https://github.com/p20030920p/SLAM_Learning/actions/workflows/ci.yml/badge.svg)](https://github.com/p20030920p/SLAM_Learning/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.10-3776AB)](pyproject.toml)

[English](README.md) | 中文

[研究分析](docs/STUDY.zh-CN.md) · [实验结果](docs/PAIRED_RESULTS.zh-CN.md) · [居家验证设计](docs/REAL_WORLD.zh-CN.md)

</div>

![作者地图实测回放](docs/figures/replication_hero.gif)

*实测最终地图的回放，GT 仅用于评价与着色；不是实时算法演示。[来源](results/reference/reproduction-media-wsl/record.json)。*

本研究从四篇 2024 年工作出发，分析 **给定位姿观测 → 空间对应 → 地图决策** 的共同依赖。先复现作者核心，再用受控实验修订假设。当前运行使用给定位姿，不估计 SLAM 轨迹。

## 复现了什么

| 工作 | 实际完成范围 | 查看结果 | 双语报告 |
| --- | --- | --- | --- |
| DUFOMap | 作者 1.1.1；KITTI teaser 全部 141 扫描、17,362,230 点 | [论文卡](docs/papers/dufomap.zh-CN.md) · [视频](docs/media/dufomap/replay.mp4) · [RViz](docs/media/rviz/dufomap.mp4) | [EN](output/pdf/dufomap.en.pdf) / [中文](output/pdf/dufomap.zh-CN.pdf) |
| BeautyMap | 同一 teaser 的作者地图清理；GT 不输入算法 | [论文卡](docs/papers/beautymap.zh-CN.md) · [视频](docs/media/beautymap/replay.mp4) · [RViz](docs/media/rviz/beautymap.mp4) | [EN](output/pdf/beautymap.en.pdf) / [中文](output/pdf/beautymap.zh-CN.pdf) |
| ConceptGraphs | Replica room0，40 次观测的 SAM／CLIP 与关联融合，39 对象 | [论文卡](docs/papers/conceptgraphs.zh-CN.md) · [视频](docs/media/conceptgraphs/replay.mp4) · [RViz](docs/media/rviz/conceptgraphs.mp4) | [EN](output/pdf/conceptgraphs.en.pdf) / [中文](output/pdf/conceptgraphs.zh-CN.pdf) |
| HOV-SG | 同场景 8 次观测的分段特征建图，50 分段 | [论文卡](docs/papers/hovsg.zh-CN.md) · [视频](docs/media/hovsg/replay.mp4) · [RViz](docs/media/rviz/hovsg.mp4) | [EN](output/pdf/hovsg.en.pdf) / [中文](output/pdf/hovsg.zh-CN.pdf) |

语义部分是明确限定的核心子集；完整语义 benchmark、LLM 图推理、楼层／房间层级与导航未完成。HOV-SG 的 40 观测中断尝试保留。[范围与失败](docs/SEMANTIC.zh-CN.md)。

| ConceptGraphs 对象地图 | HOV-SG 分段地图 |
| --- | --- |
| ![ConceptGraphs](docs/media/conceptgraphs/preview.gif) | ![HOV-SG](docs/media/hovsg/preview.gif) |

*红色表示文本查询候选，不表示已判正确。均为保存输出的回放。*

## 结果怎样改变了问题

![配对测量与种子范围](results/reference/paired-pose/figures/paired-results.png)

**76 个主单元 + 21 个探索参数对照**表明：30 cm RMS 下，单调漂移比打乱误差保留更多 LiDAR 静态点，但 ConceptGraphs 的部分表面覆盖更低。“时间相关误差总是更坏”被这组结果否定；“共享位姿不确定性是共同主导瓶颈”仍未证实。简单阈值变化已改善部分结果。

同一 DUFOMap 输出仅改变评分对应方式，SA 就相差 **5.347532 个百分点**。该差值属于测量定义，不能当算法提升。一个 teaser、一个静态房间与未经独立人工审核的四个部分表面，限制了结论范围。

**收窄后的开放问题：** 后续位姿修正改变历史对应时，怎样让对象身份与查询坐标恢复有效，并明确告知用户哪些结果仍然过期？候选 H1 保留观测来源、位姿版本和有界重放；尚未实现或验证收益。

[独立分析：达到什么、未达到什么、指标与 H1 的关系](docs/STUDY.zh-CN.md) · [完整配对结果](docs/PAIRED_RESULTS.zh-CN.md) · [协议](docs/PAIRED_PROTOCOL.zh-CN.md) · [配对报告 EN](output/pdf/paired-study.en.pdf) / [中文](output/pdf/paired-study.zh-CN.pdf)

## 新场景的迟到修正实验

**35 个冻结 room1 主单元 + 6 个独立事后对照**改变了诊断。30 cm 下，修正刚发生时，固定历史关联的几何修正恢复率为 11.1%，oracle 重新关联为 66.7%；支持门槛从 3 降至 1 后，固定历史组恢复率升至 100%，同时暴露候选从 8.3 增至 117.0。标注是部分表面，尚待独立人工复核。重新关联的必要性仍未证实；先比较身份质量与相同候选预算，再决定是否实现 H1。[新结果与决策](docs/DELAYED_RESULTS.zh-CN.md) · [报告 EN](output/pdf/delayed-study.en.pdf) / [中文](output/pdf/delayed-study.zh-CN.pdf)。

D435i／Unitree L2 的[居家实验设计](docs/REAL_WORLD.zh-CN.md)从固定传感器的静止、遮挡、移动、移除开始，再测试手持重访。**尚无实物验证成绩。**

## 核查与复现

[最少复现命令](docs/REPRODUCE.zh-CN.md) · [论文与原始结果](docs/papers/README.zh-CN.md) · [可视化说明](docs/RECORDING.zh-CN.md) · [文档索引](docs/README.zh-CN.md)

`src/`、`scripts/`、`configs/` 提供研究代码和固定设置；`results/reference/` 提供轻量原始证据与失败记录；`output/pdf/` 提供 16 份报告快照。完整数据、权重、地图和个人操作手册不进入主分支。

[AI 使用与研究边界](docs/DISCLOSURE.zh-CN.md) · [来源与许可](docs/ATTRIBUTION.zh-CN.md) · [引用](CITATION.cff) · [License](LICENSE)
