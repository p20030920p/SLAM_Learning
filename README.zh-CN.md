<div align="center">

# SLAM Learning

**位姿修正后，地图也修复了吗？**

动态环境稳健建图 · 语义建图与定位

[![CPU reproducibility](https://github.com/p20030920p/SLAM_Learning/actions/workflows/ci.yml/badge.svg)](https://github.com/p20030920p/SLAM_Learning/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.10-3776AB)](pyproject.toml)

[English](README.md) | 中文

[分析](docs/STUDY.zh-CN.md) · [结果](docs/PAIRED_RESULTS.zh-CN.md) · [实物计划](docs/REAL_WORLD.zh-CN.md)

</div>

> **room2：**28 单元已运行，分析待完成。使用 AI 标注，H1 未验证。[实验](https://github.com/p20030920p/SLAM_Learning/blob/4361d4f353a7449c7d6964887643915d2fc72a11/docs/IDENTITY_BUDGET.zh-CN.md)。

![作者地图实测回放](docs/figures/replication_hero.gif)

*保存地图回放；GT 仅用于评价／着色。[来源](results/reference/reproduction-media-wsl/record.json)。*

复现四篇 2024 年工作的建图核心，使用给定位姿；当前运行不含轨迹估计与导航。

## 1. 开放研究问题

相同候选上限下，重算关联能否改善迟到位姿修正后的目标恢复？

## 2. 问题是如何形成的

- **动态环境 SLAM：**物体运动时，保留稳定几何。
- **语义建图、视觉定位与导航：**把对象连接到可靠坐标。

SLAM 同时估计运动与构建地图。

```text
传感器数据 → 前端 → 后端（优化） → 地图构建
              ↓       ↑
           回环检测 ──┘
```

| SLAM 要素 | 动态鲁棒性 | 语义锚定 |
| --- | --- | --- |
| 传感器数据 | 运动、遮挡 | RGB-D 对齐 |
| 前端 | 稳定对应 | 掩码、特征、关联 |
| 后端 | 鲁棒位姿约束 | 一致坐标 |
| 回环检测 | 变化后识别重访 | 刷新对象锚点 |
| 地图构建 | 消除动态残影 | 维护身份与目标 |

四个核心都依赖**位姿 → 对应 → 地图决策**。DUFOMap 与 BeautyMap 过滤几何，ConceptGraphs 与 HOV-SG 关联语义证据。这引出共同问题，尚未证明共同失效。[分析](docs/STUDY.zh-CN.md)。

## 3. 假设

记录观测来源与位姿版本，修正后在有界缓存内重放受影响的关联，将比固定关联保护恢复更多有效目标。**H1 仍是候选假设。**

当前实验先检验是否需要重算关联，尚未测试有界缓存实现。

## 4. 为什么可能成立

固定关联对照修正坐标后，仍保留旧对象成员与融合特征。这些决策可能需要重算，但阈值与支持门槛也可能已经足够。

[Khronos](https://arxiv.org/html/2402.13817v2) 与 [DovSG](https://arxiv.org/html/2410.11989v2) 已有地图协调或记忆更新；重放本身不构成创新。

## 5. 方法对照

GIF 回放核心输出：LiDAR 颜色表示移除结果，语义高亮为未验证的查询候选。[媒体说明](docs/RECORDING.zh-CN.md)。

| [DUFOMap](docs/papers/dufomap.zh-CN.md) | [BeautyMap](docs/papers/beautymap.zh-CN.md) |
| --- | --- |
| ![DUFOMap 核心回放](docs/media/dufomap/preview.gif) | ![BeautyMap 核心回放](docs/media/beautymap/preview.gif) |
| 自由空间判定，移除动态回波。**141 扫描。** | 二进制占据与静态恢复，清理地图。**141 扫描。** |

| [ConceptGraphs](docs/papers/conceptgraphs.zh-CN.md) | [HOV-SG](docs/papers/hovsg.zh-CN.md) |
| --- | --- |
| ![ConceptGraphs 核心回放](docs/media/conceptgraphs/preview.gif) | ![HOV-SG 核心回放](docs/media/hovsg/preview.gif) |
| SAM／CLIP 关联，生成对象与查询候选。**40 帧、39 个表示。** | 分段融合，生成可查询特征地图。**8 帧、50 分段；未运行层级／导航。** |

更大规模作者运行位于 [`reproduce/author-originals`](https://github.com/p20030920p/SLAM_Learning/tree/reproduce/author-originals)，快照 **`3b0b9a8`**；以上四个 GIF 对应早期子集。

| 工作 | 作者运行证据 | 剩余问题 |
| --- | --- | --- |
| DUFOMap | 1,997 扫描；[表 IV](https://github.com/p20030920p/SLAM_Learning/blob/3b0b9a88ac7c77431268b6c869c369e01bd19b3e/docs/DUFOMAP_TABLE4.zh-CN.md)：15 项精度匹配两位小数 | 已有容差仍受位姿影响；需要观测到空域 |
| BeautyMap | 1,997 扫描；历史 KITTI-02 [表 III](https://github.com/p20030920p/SLAM_Learning/blob/3b0b9a88ac7c77431268b6c869c369e01bd19b3e/docs/KITTI_PAPER_PROTOCOL.zh-CN.md)：9 项匹配两位小数 | 已有恢复仍有配准与网格尺度取舍 |
| ConceptGraphs | [room0](https://github.com/p20030920p/SLAM_Learning/blob/3b0b9a88ac7c77431268b6c869c369e01bd19b3e/docs/CONCEPTGRAPHS_ROOM0_RESULTS.zh-CN.md)：400 帧，语义评分完成 | 漏检／重复对象、描述错误 |
| HOV-SG | [20 帧变体](https://github.com/p20030920p/SLAM_Learning/blob/3b0b9a88ac7c77431268b6c869c369e01bd19b3e/docs/HOVSG_HOME_RESULTS.zh-CN.md)：156 分段，待评分；200 帧融合超时 | 静态场景假设、建图耗时 |

<details>
<summary>另外五个 GIF：真实三维窗口录像</summary>

| DUFOMap RViz | BeautyMap RViz |
| --- | --- |
| ![DUFOMap RViz 录像](https://raw.githubusercontent.com/p20030920p/SLAM_Learning/4361d4f353a7449c7d6964887643915d2fc72a11/results/reference/homepage-media/dufomap-rviz.gif) | ![BeautyMap RViz 录像](https://raw.githubusercontent.com/p20030920p/SLAM_Learning/4361d4f353a7449c7d6964887643915d2fc72a11/results/reference/homepage-media/beautymap-rviz.gif) |

| ConceptGraphs RViz | HOV-SG RViz |
| --- | --- |
| ![ConceptGraphs RViz 录像](https://raw.githubusercontent.com/p20030920p/SLAM_Learning/4361d4f353a7449c7d6964887643915d2fc72a11/results/reference/homepage-media/conceptgraphs-rviz.gif) | ![HOV-SG RViz 录像](https://raw.githubusercontent.com/p20030920p/SLAM_Learning/4361d4f353a7449c7d6964887643915d2fc72a11/results/reference/homepage-media/hovsg-rviz.gif) |

RViz 查看早期核心的保存地图，未重新推理。完整视频：[DUFOMap](docs/media/rviz/dufomap.mp4) · [BeautyMap](docs/media/rviz/beautymap.mp4) · [ConceptGraphs](docs/media/rviz/conceptgraphs.mp4) · [HOV-SG](docs/media/rviz/hovsg.mp4)。

![ConceptGraphs 作者原版查看器](https://raw.githubusercontent.com/p20030920p/SLAM_Learning/4361d4f353a7449c7d6964887643915d2fc72a11/results/reference/homepage-media/conceptgraphs-author-viewer.gif)

400 帧作者地图：RGB／实例颜色与旋转，未展示查询／关系图。[60 秒视频](https://github.com/p20030920p/SLAM_Learning/blob/3b0b9a88ac7c77431268b6c869c369e01bd19b3e/evidence/videos/conceptgraphs-room0-original-window.mp4) · [来源](https://github.com/p20030920p/SLAM_Learning/blob/4361d4f353a7449c7d6964887643915d2fc72a11/results/reference/homepage-media/record.json)。

</details>

## 6. 引出问题的观察

![分开的 LiDAR 核心与原始语义指标](https://raw.githubusercontent.com/p20030920p/SLAM_Learning/4361d4f353a7449c7d6964887643915d2fc72a11/results/reference/homepage-media/baseline-metrics.png)

| 运行 | 指标 | 结果 |
| --- | --- | ---: |
| DUFOMap，141 扫描 | 静态保留 SA／动态剔除 DA | 97.9798%／98.7029% |
| BeautyMap，同输入 | SA／DA | 96.9529%／98.3382% |
| ConceptGraphs，作者 room0 | mIoU／类别频率加权 IoU | 21.3460%／50.1379% |
| HOV-SG，作者 20 帧 | 语义精度 | 待完成 |

协议分开：LiDAR 使用 5 cm 地图近邻；room0 使用 23 类、4,085,377 计分点。数量不等于精度。[定义／来源](https://github.com/p20030920p/SLAM_Learning/blob/4361d4f353a7449c7d6964887643915d2fc72a11/results/reference/homepage-media/record.json) · [生成脚本](https://github.com/p20030920p/SLAM_Learning/blob/4361d4f353a7449c7d6964887643915d2fc72a11/scripts/build_homepage_media.py)。

![恢复表现与暴露候选代价](https://raw.githubusercontent.com/p20030920p/SLAM_Learning/4361d4f353a7449c7d6964887643915d2fc72a11/results/reference/homepage-media/recovery-cost.png)

room1，30 cm 修正刚发生时：固定关联恢复 **11.1%**，oracle **66.7%**，事后支持门槛 1 为 **100%**；对应候选 **8.3／25／117**。三个种子均值、部分 AI 标注、上限未匹配。[结果](docs/DELAYED_RESULTS.zh-CN.md)。

降低支持门槛消除了所选目标的恢复缺口，但暴露更多候选；后续观测也能修复部分损失。因此需要相同上限对照，不能宣称关联损失不可逆。

## 7. 最小假设检验

在 room2 固定前端与五个 AI 标注实例。第八次观测后，向固定关联、阈值 1.0、可见性保护与 oracle 回放四组交付相同精确历史位姿修正。

离线比较支持门槛 1／2／3、候选上限 25／50／100／不限，报告恢复、查询命中、重复／混合及修正成本。相同上限不等于相同内存。

同一 RMS 与支持门槛下，仅当 oracle 在两个有限上限均比所有简单对照高至少 10 个百分点、至少 2／3 配对种子同向且每个种子均不增加已标重复／混合，才考虑原型。简单方法追平将削弱 H1。[冻结协议与完整决策规则](https://github.com/p20030920p/SLAM_Learning/blob/4361d4f353a7449c7d6964887643915d2fc72a11/docs/IDENTITY_BUDGET.zh-CN.md)。

28 个建图单元已运行，独立分析待完成；AI 标注不能确认 H1。

## 分支导航

| 分支 | 做了什么 |
| --- | --- |
| [`study/identity-budget-v2`](https://github.com/p20030920p/SLAM_Learning/tree/study/identity-budget-v2) | 迟到位姿修正与候选预算对照；H1 未验证。 |
| [`reproduce/author-originals`](https://github.com/p20030920p/SLAM_Learning/tree/reproduce/author-originals) | 四篇论文的作者原库复现、指标核对与录像。 |
| [`notes/personal-study-guide-20261008`](https://github.com/p20030920p/SLAM_Learning/tree/notes/personal-study-guide-20261008) | [研究笔记：H1 与否定条件](https://github.com/p20030920p/SLAM_Learning/blob/71a2e7556e231c1d0e6814febb085bea9d225f44/notes/OPEN_QUESTION_AND_HYPOTHESIS.zh-CN.md)。 |
| [`Personal-Learning-Physical`](https://github.com/p20030920p/SLAM_Learning/tree/Personal-Learning-Physical) | [D435／L2 收流、建图试跑与 8 帧语义加载检查](https://github.com/p20030920p/SLAM_Learning/blob/4e5a5e8b703e5072ca5e11cf6893d03bca244473/README.zh-CN.md)。 |

D435 无 IMU；雷达里程计漂移超标，融合与语义质量未验收。

[AI 使用](docs/DISCLOSURE.zh-CN.md) · [来源／许可](docs/ATTRIBUTION.zh-CN.md) · [引用](CITATION.cff) · [License](LICENSE)
