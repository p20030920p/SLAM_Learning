<div align="center">

# SLAM Learning

**地图什么时候应该相信世界发生了变化？**

动态环境稳健建图 · 语义建图与定位

[![CPU reproducibility](https://github.com/p20030920p/SLAM_Learning/actions/workflows/ci.yml/badge.svg)](https://github.com/p20030920p/SLAM_Learning/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.10-3776AB)](pyproject.toml)

[English](README.md) | 中文

[研究分析](docs/STUDY.zh-CN.md) · [实验结果](docs/PAIRED_RESULTS.zh-CN.md) · [居家验证设计](docs/REAL_WORLD.zh-CN.md)

</div>

> **进行中：** [room2 身份与候选预算实验](docs/IDENTITY_BUDGET.zh-CN.md)使用 AI 标注。28 个原生单元已运行，分析待完成；H1 未验证。

![作者地图实测回放](docs/figures/replication_hero.gif)

*保存地图回放，非实时推理；GT 用于评价与着色。[来源](results/reference/reproduction-media-wsl/record.json)。*

复现四篇 2024 年工作的建图核心，再做位姿误差对照。当前使用给定位姿，不估计轨迹。

## 方向选择与分析

**我选择：**

- 动态环境中的鲁棒定位与 SLAM；
- 语义建图、视觉锚定与导航。

**分析：**

SLAM 即 **同时定位与建图（Simultaneous Localization and Mapping）**：*智能体利用传感器数据，在构建初始未知环境地图的同时，估计自身运动。*

两个相互耦合的任务是定位与建图。实时处理是在线 SLAM 的目标；实际系统也可以使用先验信息。

```text
传感器数据 → 前端 → 后端（优化） → 地图构建
              ↓       ↑
           回环检测 ──┘
```

**方向 1——世界在动，几何仍要可靠。** [DUFOMap](https://arxiv.org/html/2403.01449v1)利用曾观测为空的空间，[BeautyMap](https://arxiv.org/html/2405.07283v1)比较占据并恢复被遮挡的静态区域。两者清理地图，为定位提供支持；本次复现都不估计轨迹。

**方向 2——把“是什么”和“在哪里”连接起来。** [ConceptGraphs](https://arxiv.org/html/2309.16650v1)关联对象几何与语言特征；[HOV-SG](https://arxiv.org/html/2403.17846v2)把分段组织为楼层、房间、对象，服务语言导航。当前运行检查建图与检索，未测试闭环导航。

| SLAM 要素 | 方向 1：动态鲁棒性 | 方向 2：语义锚定 |
| --- | --- | --- |
| 传感器数据 | 运动、遮挡与稀疏回波 | RGB-D 对齐与语义观测 |
| 前端 | 稳定对应与自身运动估计 | 分割、特征与对象关联 |
| 后端 | 鲁棒位姿约束 | 融合语义使用一致坐标 |
| 回环检测 | 场景变化后仍识别重访 | 重识别地点／对象，刷新锚点 |
| 地图构建 | 保留静态几何，剔除动态点 | 维护身份、含义与目标坐标 |

所选四篇主要研究**地图构建及其空间对应接口**。后端和回环修正引出我们的问题，这些 SLAM 模块本身尚未复现；导航使用其输出。

## 开放研究问题

**历史位姿迟到修正后，只移动地图几何，能否恢复对象身份和查询坐标，还是必须重新考虑此前的关联？**

| 工作 | 已有保护与剩余问题 |
| --- | --- |
| [DUFOMap，III-B／V-C／V-E](https://arxiv.org/html/2403.01449v1) | 已考虑位姿与测距容差；位姿质量和从未观测为空的空间仍限制分类。 |
| [BeautyMap，III／我们的网格复现](https://arxiv.org/html/2405.07283v1) | 已恢复视野外的静态区域；占据对应，以及静态保留与动态剔除的取舍仍然重要。 |
| [ConceptGraphs，II-A／III-H](https://arxiv.org/html/2309.16650v1) | 支持地图更新，但报告薄小物体漏检、重复和描述错误。位姿修正后的关联恢复是我们提出的问题，不能写成作者报告的普遍失效。 |
| [HOV-SG，III-A／V](https://arxiv.org/html/2403.17846v2) | 使用准确里程计投影；明确假设静态场景，并指出建图耗时。在线语义恢复不在当前复现核心中。 |

共性依赖是**位姿 → 空间对应 → 地图决策**，尚非已证实的共同失效。[Khronos](https://arxiv.org/html/2402.13817v2)已有优化后的地图协调，[DovSG](https://arxiv.org/html/2410.11989v2)已有局部语义记忆更新；两者仅作文献对照，未复现为实验基线。“保存历史”或“支持动态更新”本身不构成我们的新颖性主张。

## 相关工作

四篇相关工作发表于 2024 年，ConceptGraphs 预印本始于 2023 年。以下四个 GIF 展示**我们实测核心输出与已保存最终地图的回放**。LiDAR 的绿／红／蓝分别表示正确移除动态点／误删静态点／遗漏动态点；语义图中的红色候选不代表已验证正确。[媒体来源](docs/RECORDING.zh-CN.md)。

| DUFOMap | BeautyMap |
| --- | --- |
| ![DUFOMap 核心回放](docs/media/dufomap/preview.gif) | ![BeautyMap 核心回放](docs/media/beautymap/preview.gif) |
| **思路：**用曾观测为空的空间分类点。**看到：**动态回波被移除，道路／建筑保留，同时可见静态误删。teaser 全部 141 扫描参与评分。[核心与视频](docs/papers/dufomap.zh-CN.md)。 | **思路：**二进制占据、地面适配与静态恢复。**看到：**地图清理后的移除／保留点，恢复机制仍有误差。同一 141 扫描 teaser。[核心与视频](docs/papers/beautymap.zh-CN.md)。 |

| ConceptGraphs | HOV-SG |
| --- | --- |
| ![ConceptGraphs 核心回放](docs/media/conceptgraphs/preview.gif) | ![HOV-SG 核心回放](docs/media/hovsg/preview.gif) |
| **思路：**把 SAM／CLIP 观测投到三维，再关联融合对象。**看到：**掩码、最终对象地图与文本查询候选。40 个给定位姿帧、39 个表示，不等于 39 个正确身份。[核心与视频](docs/papers/conceptgraphs.zh-CN.md)。 | **思路：**先合并三维分段、筛选语义特征，再构建层级。**看到：**分割与最终特征地图中的查询候选。8 个给定位姿帧、50 分段，未运行层级／导航。[核心与视频](docs/papers/hovsg.zh-CN.md)。 |

独立的 [`reproduce/author-originals`](https://github.com/p20030920p/SLAM_Learning/tree/reproduce/author-originals) 分支运行固定版本的作者原库。快照 **`3b0b9a8`** 新增：

| 工作 | 作者流程的实际进度 | 证据 |
| --- | --- | --- |
| DUFOMap | 四份有标签发布包，共 1,997 扫描；表 IV 的 15 项 SA／DA／AA 均匹配论文两位小数 | [表 IV](https://github.com/p20030920p/SLAM_Learning/blob/3b0b9a88ac7c77431268b6c869c369e01bd19b3e/docs/DUFOMAP_TABLE4.zh-CN.md) |
| BeautyMap | 同四份发布包；历史 KITTI-02 预处理、三种网格复现表 III 全部 9 项 SA／DA／HA | [表 III](https://github.com/p20030920p/SLAM_Learning/blob/3b0b9a88ac7c77431268b6c869c369e01bd19b3e/docs/KITTI_PAPER_PROTOCOL.zh-CN.md) |
| ConceptGraphs | room0：400 帧、77 对象记录；原语义评价经独立重算；原版查看器已录制 | [结果](https://github.com/p20030920p/SLAM_Learning/blob/3b0b9a88ac7c77431268b6c869c369e01bd19b3e/docs/CONCEPTGRAPHS_ROOM0_RESULTS.zh-CN.md) |
| HOV-SG | 额外 20 帧采样完成 156 分段、399,663 全局点，评分待完成；默认 200 帧融合超时 | [范围与失败](https://github.com/p20030920p/SLAM_Learning/blob/3b0b9a88ac7c77431268b6c869c369e01bd19b3e/docs/HOVSG_HOME_RESULTS.zh-CN.md) |

上面的 GIF 对应早期核心子集，并非这些更大运行。论文表格匹配仅指列明的精度项目，不代表全部论文实验完成。

<details>
<summary>另外五个 GIF：保存结果的真实三维窗口录像</summary>

| DUFOMap RViz | BeautyMap RViz |
| --- | --- |
| ![DUFOMap RViz 录像](results/reference/homepage-media/dufomap-rviz.gif) | ![BeautyMap RViz 录像](results/reference/homepage-media/beautymap-rviz.gif) |

| ConceptGraphs RViz | HOV-SG RViz |
| --- | --- |
| ![ConceptGraphs RViz 录像](results/reference/homepage-media/conceptgraphs-rviz.gif) | ![HOV-SG RViz 录像](results/reference/homepage-media/hovsg-rviz.gif) |

RViz 检查早期核心输出，是真实图形窗口查看，不是新推理。完整视频：[DUFOMap](docs/media/rviz/dufomap.mp4) · [BeautyMap](docs/media/rviz/beautymap.mp4) · [ConceptGraphs](docs/media/rviz/conceptgraphs.mp4) · [HOV-SG](docs/media/rviz/hovsg.mp4)。

![ConceptGraphs 作者原版查看器](results/reference/homepage-media/conceptgraphs-author-viewer.gif)

**400 帧作者运行**的原版 Open3D 查看器：RGB／实例颜色切换与旋转。属于保存地图的窗口录像，不含文本查询或关系图展示。[完整 60 秒视频](https://github.com/p20030920p/SLAM_Learning/blob/3b0b9a88ac7c77431268b6c869c369e01bd19b3e/evidence/videos/conceptgraphs-room0-original-window.mp4) · [衍生哈希与片段时刻](results/reference/homepage-media/record.json)。

</details>

**已测指标：**

![分开的 LiDAR 核心与原始语义指标](results/reference/homepage-media/baseline-metrics.png)

| 运行 | 指标 | 实测 |
| --- | --- | ---: |
| DUFOMap，141 扫描核心 | 静态保留 SA／动态剔除 DA | 97.9798%／98.7029% |
| BeautyMap，同核心输入 | SA／DA | 96.9529%／98.3382% |
| ConceptGraphs，作者 room0 | mIoU／类别频率加权 IoU | 21.3460%／50.1379% |
| HOV-SG，作者 20 帧变体 | 语义精度 | 待完成 |

LiDAR 使用 5 cm 地图近邻评分。ConceptGraphs 排除指定类别后，使用 23 个有效类别、4,085,377 个重建计分点。协议分开，不作四方法排名。数量描述执行规模，不代表准确率；AA 为几何均值，HA 为调和均值。[作图输入](results/reference/homepage-media/record.json) · [生成脚本](scripts/build_homepage_media.py)。

<details>
<summary>早期核心范围、命令与双语报告</summary>

| 工作 | 实际完成范围 | 查看结果 | 双语报告 |
| --- | --- | --- | --- |
| DUFOMap | 作者 1.1.1；KITTI teaser 全部 141 扫描、17,362,230 点 | [论文卡](docs/papers/dufomap.zh-CN.md) · [视频](docs/media/dufomap/replay.mp4) · [RViz](docs/media/rviz/dufomap.mp4) | [EN](output/pdf/dufomap.en.pdf) / [中文](output/pdf/dufomap.zh-CN.pdf) |
| BeautyMap | 同一 teaser 的作者地图清理；GT 不输入算法 | [论文卡](docs/papers/beautymap.zh-CN.md) · [视频](docs/media/beautymap/replay.mp4) · [RViz](docs/media/rviz/beautymap.mp4) | [EN](output/pdf/beautymap.en.pdf) / [中文](output/pdf/beautymap.zh-CN.pdf) |
| ConceptGraphs | Replica room0，40 次观测的 SAM／CLIP 与关联融合，39 对象 | [论文卡](docs/papers/conceptgraphs.zh-CN.md) · [视频](docs/media/conceptgraphs/replay.mp4) · [RViz](docs/media/rviz/conceptgraphs.mp4) | [EN](output/pdf/conceptgraphs.en.pdf) / [中文](output/pdf/conceptgraphs.zh-CN.pdf) |
| HOV-SG | 同场景 8 次观测的分段特征建图，50 分段 | [论文卡](docs/papers/hovsg.zh-CN.md) · [视频](docs/media/hovsg/replay.mp4) · [RViz](docs/media/rviz/hovsg.mp4) | [EN](output/pdf/hovsg.en.pdf) / [中文](output/pdf/hovsg.zh-CN.pdf) |

语义部分是明确限定的核心子集；完整语义 benchmark、LLM 图推理、楼层／房间层级与导航未完成。HOV-SG 的 40 观测中断尝试保留。[范围与失败](docs/SEMANTIC.zh-CN.md)。

</details>

## 假设

**候选 H1：**保留有界观测来源与位姿版本。修正后先把受影响的查询结果标为过期，再重放相关贡献观测与关联。这可能恢复仅修正坐标无法恢复的身份；收益和内存代价尚未验证。

![恢复表现与暴露候选代价](results/reference/homepage-media/recovery-cost.png)

room1 的反例必须保留：30 cm RMS 下，修正几何但固定关联的恢复率为 **11.1%**，oracle 重新关联为 **66.7%**，降低固定关联组的支持门槛后却达到 **100%**。暴露候选从 **8.3 增至 117.0**，oracle 为 **25.0**。这些是三个种子的均值，使用部分 AI 标注；支持门槛 1 是事后分析，候选上限不同。[分数与定义](docs/DELAYED_RESULTS.zh-CN.md)。

因此 room2 在**相同候选上限**下比较固定关联、阈值 1.0、可见性保护和全量回放。28 个原生单元已运行，独立分析待完成。固定 RMS／支持门槛后，只有 oracle 在两个有限上限下均比每个简单对照高 ≥10 个百分点、≥2/3 种子改善且已标身份错误不增加，才推进原型计划，仍不确认 H1。相同候选上限不等于相同内存。[冻结实验](docs/IDENTITY_BUDGET.zh-CN.md)。

**个人学习：**[`notes/personal-study-guide-20261008`](https://github.com/p20030920p/SLAM_Learning/blob/71a2e7556e231c1d0e6814febb085bea9d225f44/notes/OPEN_QUESTION_AND_HYPOTHESIS.zh-CN.md)保存论文比较、论证稿与否定条件；[`Personal-Learning-Physical`](https://github.com/p20030920p/SLAM_Learning/blob/4e5a5e8b703e5072ca5e11cf6893d03bca244473/README.zh-CN.md)完成 D435／L2 收流、RTAB-Map 双目／RGB-D、ICP／KISS 试跑与录像，两套语义加载器各通过 8 帧真实 RGB-D 输入检查。SDK 确认设备为 **D435，无 IMU**。旧固定雷达里程计漂移超标；LIO、跨设备融合及语义建图质量尚未验收。硬件输入检查不验证 H1；室内原始录像留本机。

<details>
<summary>早期配对与迟到修正证据</summary>

## 结果怎样改变了问题

![配对测量与种子范围](results/reference/paired-pose/figures/paired-results.png)

**76 个主单元 + 21 个探索参数对照**表明：30 cm RMS 下，单调漂移比打乱误差保留更多 LiDAR 静态点，但 ConceptGraphs 的部分表面覆盖更低。“时间相关误差总是更坏”被这组结果否定；“共享位姿不确定性是共同主导瓶颈”仍未证实。简单阈值变化已改善部分结果。

同一 DUFOMap 输出仅改变评分对应方式，SA 就相差 **5.347532 个百分点**。该差值属于测量定义，不能当算法提升。一个 teaser、一个静态房间与未经独立人工审核的四个部分表面，限制了结论范围。

**收窄后的开放问题：** 后续位姿修正改变历史对应时，怎样让对象身份与查询坐标恢复有效，并明确告知用户哪些结果仍然过期？候选 H1 保留观测来源、位姿版本和有界重放；尚未实现或验证收益。

[独立分析：达到什么、未达到什么、指标与 H1 的关系](docs/STUDY.zh-CN.md) · [完整配对结果](docs/PAIRED_RESULTS.zh-CN.md) · [协议](docs/PAIRED_PROTOCOL.zh-CN.md) · [配对报告 EN](output/pdf/paired-study.en.pdf) / [中文](output/pdf/paired-study.zh-CN.pdf)

## 新场景的迟到修正实验

**35 个冻结 room1 主单元 + 6 个独立事后对照**改变了诊断。30 cm 下，修正刚发生时，固定历史关联的几何修正恢复率为 11.1%，oracle 重新关联为 66.7%；支持门槛从 3 降至 1 后，固定历史组恢复率升至 100%，同时暴露候选从 8.3 增至 117.0。标注是部分表面，尚待独立人工复核。重新关联的必要性仍未证实；先比较身份质量与相同候选预算，再决定是否实现 H1。[新结果与决策](docs/DELAYED_RESULTS.zh-CN.md) · [报告 EN](output/pdf/delayed-study.en.pdf) / [中文](output/pdf/delayed-study.zh-CN.pdf)。

[居家实验设计](docs/REAL_WORLD.zh-CN.md)先区分静止、遮挡、移动与移除，再做手持重访。个人硬件分支已有输入／里程计试跑，**尚无通过验收的实物语义地图或导航分数。**

</details>

## 核查与复现

[最少复现命令](docs/REPRODUCE.zh-CN.md) · [论文与原始结果](docs/papers/README.zh-CN.md) · [可视化说明](docs/RECORDING.zh-CN.md) · [文档索引](docs/README.zh-CN.md)

`src/`、`scripts/`、`configs/` 提供研究代码和固定设置；`results/reference/` 提供轻量原始证据与失败记录；`output/pdf/` 提供 16 份报告快照。完整数据、权重、地图和个人操作手册不进入主分支。

[AI 使用与研究边界](docs/DISCLOSURE.zh-CN.md) · [来源与许可](docs/ATTRIBUTION.zh-CN.md) · [引用](CITATION.cff) · [License](LICENSE)
