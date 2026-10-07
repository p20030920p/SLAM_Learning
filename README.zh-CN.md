<div align="center">

# SLAM Learning

**地图什么时候应该相信世界发生了变化？**

动态环境稳健建图 · 语义建图与定位 · 共享位姿不确定性

[![CPU reproducibility](https://github.com/p20030920p/SLAM_Learning/actions/workflows/ci.yml/badge.svg)](https://github.com/p20030920p/SLAM_Learning/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.10-3776AB)](pyproject.toml)
[![Papers](https://img.shields.io/badge/author%20cores-4-147D85)](docs/papers/README.zh-CN.md)

[四篇复现](#四篇相关论文复现) &nbsp;•&nbsp; [研究问题](#研究问题) &nbsp;•&nbsp; [实物测试](#d435i-和宇树-l2没有机器人也能做)

[English](README.md) &nbsp;|&nbsp; 中文

</div>

![作者地图实测回放](docs/figures/replication_hero.gif)

*最终地图实测回放：21 个选定扫描，固定世界视角，原始 → 移除 → 保留。绿：移除动态；红：移除静态；蓝：保留动态。GT 只用于评分／着色。[来源与绘制设置](results/reference/reproduction-media-wsl/record.json)。*

本研究通过一个接口连接所选的两个实验室主题：**给定位姿观测 → 空间对应 → 地图决策**。先复现作者流程，核查测量，再提出可检验的假设。本次给定位姿建图运行未估计 SLAM 轨迹。

## 四篇相关论文复现

| 论文 | 实际执行内容 | 报告 | 观看 | PDF |
| --- | --- | --- | --- | --- |
| DUFOMap，2024 | 作者动态点移除，完整 141 扫描 KITTI-00 teaser | [论文卡](docs/papers/dufomap.zh-CN.md) | [MP4](docs/media/dufomap/replay.mp4) / [GIF](docs/media/dufomap/preview.gif) | [EN](output/pdf/dufomap.en.pdf) / [中文](output/pdf/dufomap.zh-CN.pdf) |
| BeautyMap，2024 | 作者地图清理，相同完整 teaser | [论文卡](docs/papers/beautymap.zh-CN.md) | [MP4](docs/media/beautymap/replay.mp4) / [GIF](docs/media/beautymap/preview.gif) | [EN](output/pdf/beautymap.en.pdf) / [中文](output/pdf/beautymap.zh-CN.pdf) |
| ConceptGraphs，ICRA 2024 | SAM／CLIP 及原生关联／融合；40 次给定位姿 Replica 观测，39 对象 | [论文卡](docs/papers/conceptgraphs.zh-CN.md) | [MP4](docs/media/conceptgraphs/replay.mp4) / [GIF](docs/media/conceptgraphs/preview.gif) | [EN](output/pdf/conceptgraphs.en.pdf) / [中文](output/pdf/conceptgraphs.zh-CN.pdf) |
| HOV-SG，RSS 2024 | 原生分段特征建图核心；8 次给定位姿观测，50 分段 | [论文卡](docs/papers/hovsg.zh-CN.md) | [MP4](docs/media/hovsg/replay.mp4) / [GIF](docs/media/hovsg/preview.gif) | [EN](output/pdf/hovsg.en.pdf) / [中文](output/pdf/hovsg.zh-CN.pdf) |

语义运行是**范围明确的核心子集**，完整论文语义 benchmark、完整图推理及导航尚未完成。对象／分段个数不是准确率，两者不能排名。HOV-SG 首次 40 观测中断记录已保留。[范围与失败](docs/SEMANTIC.zh-CN.md)。

| ConceptGraphs：原生观测与最终对象地图 | HOV-SG：原生观测与最终分段地图 |
| --- | --- |
| ![ConceptGraphs 回放](docs/media/conceptgraphs/preview.gif) | ![HOV-SG 回放](docs/media/hovsg/preview.gif) |

*红色是文本查询候选，未标注正确性。两者均为最终世界 XZ 投影；视频属于实测输出回放，不是实时屏幕录制或 FPS 测试。[录制约定与坐标核查](docs/RECORDING.zh-CN.md)。*

## 数字支持什么

| 作者方法 | SA % ↑ | DA % ↑ | 汇总指标 | 与论文表格对齐 |
| --- | ---: | ---: | --- | --- |
| DUFOMap 1.1.1 | 97.9798 | 98.7029 | 几何 AA 98.3407 | 并非全部在 0.01 百分点内 |
| BeautyMap，固定版本 | 96.9529 | 98.3382 | 调和 HA 97.6407 | 并非全部在 0.01 百分点内 |

评价全部 141 扫描及 17,362,230 个标注点，使用 5 cm 地图近邻。Windows、全新 Ubuntu CI、WSL 计数一致。两幅地图的原 PCL 与 SciPy **逐点零分歧**，排除了这些地图上的评价实现差异，但未解释剩余论文表格差距。AA／HA 是不同汇总定义。[完整计数、目标与控制](docs/RESULTS.zh-CN.md)。

只把相同 DUFOMap 保留点从直接身份改成地图近邻评分，SA 就增加 **5.347532 百分点**。这是测量效应，并非算法改进。实际 ConceptGraphs 入口使用绝对位姿，39 个保存相机矩阵确认坐标约定。在研究结论前完成这些核查十分必要。

## 研究问题

**存在静态锚点时，地图更新能否在时间相关位姿误差下保持可靠，同时匹配变化召回、查询覆盖率与更新延迟？**

共性依赖是空间对应，并不意味着四者都忽略噪声或假设静态。DUFOMap 已有容差，BeautyMap 保护被遮挡几何，ConceptGraphs 支持更新，HOV-SG 明确承认静态场景限制。错误对应可能造成误删除或错误语义分配；目前尚未在四者上实证相同失效。

候选 H1 保留一个共享位姿变量及观测来源，延迟含混修改，在位姿修正后重放受影响观测。可先实现有界对象／子图附加模块。需静态锚点；已知协方差属于 oracle 诊断。Khronos 已有联合优化与地图修复，不能把记忆或联合优化本身当作创新。

若简单阈值／可见性基线在相同召回、覆盖和延迟下达到同样风险，或推迟更新只增加过期目标时间，就否定 H1。现有 room0 及合成试验已参与构思，保留为探索性结果。[四篇详细分析](docs/STUDY.zh-CN.md) · [EN PDF](output/pdf/study.en.pdf) / [中文 PDF](output/pdf/study.zh-CN.pdf)。

![实测对应评分效应](docs/figures/metric_correspondence.png)

<!-- MEDIA: bottleneck-diagram / pose-drift-video / risk-coverage -->
*预留研究图：位姿／对应机制、相同误差的漂移视频、留出风险—覆盖—延迟曲线。[输入与发布要求](docs/figures/README.zh-CN.md)。*

## D435i 和宇树 L2：没有机器人也能做

**计划阶段，尚未采集实物数据。** 检验地图决策及对象坐标查询不需要移动机器人。

| 设置 | 区分性实验 | 必要控制 |
| --- | --- | --- |
| 固定 D435i 三脚架 | 不变／遮挡／移动／移除对象，语义身份和目标坐标 | 传感器恒定位姿、背景参考及可见性标注 |
| 固定 L2 三脚架 | 静态几何保留、射线穿过真正空域 | 原始点／时间／ring 与核实的传感器位姿 |
| 手持闭环 | 固定像素／特征，独立与相关位姿误差 | 估计里程计与参考分开，匹配实际位姿 RMS |
| D435i + L2 刚性支架 | 独立几何源是否改善关联 | 外参、时间偏差量测及 RGB-D／LiDAR 干扰控制 |

详细协议给出房间布置、标定、原生／ROS 采集、事件状态、标注、验证／测试会话、失败条件、指标及发布文件。D435i IMU 不是位置真值，也不假设 L2 与相机共享时钟。[可执行实物方案](docs/REAL_WORLD.zh-CN.md) · [EN PDF](output/pdf/real-world.en.pdf) / [中文 PDF](output/pdf/real-world.zh-CN.pdf)。

<!-- MEDIA: physical-capture-video -->
*实物视频位置：真实输入 + 地图决策 + 独立标注／事件视图，显示会话 ID 及位姿来源。此位置没有合成成绩。*

## 快速开始

```bash
uv sync --frozen --python 3.10 --extra methods --extra dev
uv run slam-study fetch
uv run slam-study run --method dufomap
uv run slam-study run --method beautymap
uv run python scripts/verify_evidence.py
uv run python scripts/check_docs.py
```

Linux／WSL CUDA 核心：先 `bash scripts/setup_semantic.sh`，再 `.venv-semantic/bin/python scripts/run_conceptgraphs.py`；先 `bash scripts/setup_hovsg.sh`，再 `.venv-hovsg/bin/python scripts/run_hovsg.py`。独立环境固定依赖并校验权重。[WSL](docs/WSL.zh-CN.md) · [完整复现命令](docs/REPRODUCE.zh-CN.md)。

## 阅读与面试路线

| 阅读 | 用途 |
| --- | --- |
| [四篇论文卡](docs/papers/README.zh-CN.md)／[结果](docs/RESULTS.zh-CN.md) | 实际范围、视频、PDF、数字及失败 |
| [共性研究](docs/STUDY.zh-CN.md)／[文献](docs/LITERATURE.zh-CN.md) | 结构性问题、论文限制、已有解决方案与创新边界 |
| [实验关卡](docs/PLAN.zh-CN.md)／[实物协议](docs/REAL_WORLD.zh-CN.md) | 复现 → 标注 → 冻结假设 → 留出比较 |
| [录制](docs/RECORDING.zh-CN.md)／[媒体索引](docs/figures/README.zh-CN.md) | 重新生成实测视频与双语报告，预留后续图 |
| [提交检查](docs/SUBMISSION.zh-CN.md)／[AI 披露](docs/INTERVIEW.zh-CN.md) | 从主张追溯到图、指标、运行和命令 |
| [实测汇总](results/REPORT.zh-CN.md)／[来源审计](docs/AUDIT.zh-CN.md) | 机器可读来源及历史迁移 |

每篇说明均有独立[英文／中文版本](docs/README.zh-CN.md)。历史内容可在 `af1e58b` 恢复，不贡献当前成绩。
