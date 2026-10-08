# 个人学习、操作与分析索引

[English](README.md) | 中文

本分支 `notes/personal-study-guide-20261008` 用于你自己走通流程、对照原库和修改研究判断。给老师的入口仍是 [main 分支](https://github.com/p20030920p/SLAM_Learning/tree/main)。这里的手册不合并到 main；分支发布后同样可公开访问，完整录屏和设备原始数据仍留本机。

## 按什么顺序看

| 顺序 | 文档 | 解决什么问题 |
| --- | --- | --- |
| 1 | [实验室要求与分析提纲](LAB_ANALYSIS.zh-CN.md) | 选方向 1、2 后，已有证据满足什么、缺什么；怎样写开放问题和可否证假设 |
| 2 | [从 Windows 开始操作](WINDOWS_START.zh-CN.md) | 打开什么、进入哪个目录、每条命令在哪执行、输出怎么找 |
| 3 | [作者原库与本库对照](UPSTREAM_COMPARISON.zh-CN.md) | 四个原库、固定版本、调用入口、补丁、资源适配和未复现部分 |
| 4 | [手动复现与录屏](MANUAL_RECORDING.zh-CN.md) | 先运行作者核心，再打开 RViz 看保存结果；自己怎样录制 |
| 5 | [居家设备操作](HOME_RUNBOOK.zh-CN.md) | D435i／L2 接入、四事件采集、回放检查和后续适配 |

第一次建议先看 1 的证据边界，然后照 2 跑一次 DUFOMap，再照 4 打开 RViz；理解流程后再运行两个语义核心。方法串行运行，尤其不要让两个 SAM／CLIP 任务同时占用这张 12 GiB GPU。

## 研究材料按用途找

| 我现在要做什么 | 入口 |
| --- | --- |
| 直接阅读已填写的开放问题和假设 | [完整论证稿](OPEN_QUESTION_AND_HYPOTHESIS.zh-CN.md)：简洁正文、证据与反例、H1-R/H1-U、对照实验和否定条件 |
| 搞清四篇各自做了什么 | [四篇论文卡](../docs/papers/README.zh-CN.md) |
| 对照近期工作、已有解决机制与反例 | [文献分析](../docs/LITERATURE.zh-CN.md)；其中其余工作属于阅读比较，不能说都复现过 |
| 理解复现与 H1 的关系 | [独立研究分析](../docs/STUDY.zh-CN.md) |
| 看新增完整作者流程怎样改变判断 | [四份公开数据与假设边界](AUTHOR_RESULTS_ANALYSIS.zh-CN.md)；新运行与旧子集记录分开阅读 |
| 补下载论文原始数据 | [KITTI 帧段、原始预处理与 ScanNet 本人申请步骤](https://github.com/p20030920p/SLAM_Learning/blob/reproduce/author-originals/docs/DATA_ACCESS.zh-CN.md) |
| 核对新增消融与评价协议 | [BeautyMap 表 III：9 项匹配及历史协议](https://github.com/p20030920p/SLAM_Learning/blob/reproduce/author-originals/docs/KITTI_PAPER_PROTOCOL.zh-CN.md)、[DUFOMap Python 输出／阈值对照](https://github.com/p20030920p/SLAM_Learning/blob/reproduce/author-originals/docs/DUFOMAP_OUTPUT_AUDIT.zh-CN.md) |
| 看作者表格与我们的数值差距 | [LiDAR 结果](../docs/RESULTS.zh-CN.md)、[语义范围](../docs/SEMANTIC.zh-CN.md) |
| 理解零误差／打乱／漂移如何构造 | [配对协议](../docs/PAIRED_PROTOCOL.zh-CN.md) |
| 看 76 主单元、21 探索对照和强基线 | [配对结果](../docs/PAIRED_RESULTS.zh-CN.md)、[分析记录](../results/reference/paired-pose/record.json) |
| 找数字绑定的原始日志与配置 | [证据审计](../docs/AUDIT.zh-CN.md)、[轻量记录目录](../results/reference)；完整地图在 WSL `results/runs/` |
| 区分视频究竟证明了什么 | [公开录制说明](../docs/RECORDING.zh-CN.md)、[手动录屏](MANUAL_RECORDING.zh-CN.md) |
| 用家里的设备补实验 | [公开实验协议](../docs/REAL_WORLD.zh-CN.md)＋[本机操作步骤](HOME_RUNBOOK.zh-CN.md) |
| 检查引用、许可和 AI 使用 | [来源与许可](../docs/ATTRIBUTION.zh-CN.md)、[AI 与人工核验边界](../docs/DISCLOSURE.zh-CN.md) |

## 本机目录不要混淆

| 路径 | 用途 |
| --- | --- |
| `D:\workspace\be2\SLAM_Learning` | Windows 的 main 工作目录，老师展示内容 |
| `D:\workspace\be2\SLAM_Personal_Guide` | 当前个人文档分支，阅读／编辑手册 |
| `D:\workspace\be2\SLAM_Author_Originals` | 新的独立原始复现分支，固定原库与运行证据 |
| `/home/qzl/projects/SLAM_Author_Originals` | 新原始流程的独立 WSL 环境、完整公开数据与大文件结果 |
| `/home/qzl/projects/SLAM_Learning` | WSL 实际运行仓库，已有三个 Python 环境、数据与作者代码缓存 |
| `D:\workspace\be2\SLAM_Recordings\2026-10-08` | 已有完整终端录屏；`rviz-review-v3/` 是图形录制原片 |
| `D:\workspace\be2\SLAM_Home` | 自己采集的设备数据与视频，单独保存 |
| `D:\workspace\be2\SLAM_Private\2026-10-08\original-docs` | 整理前旧手册，只作历史参考，以当前文档为准 |

`local/full-notes-20261008` 是整理前本地留档分支；这份新分支基于 main 的 `6deb08a`，另外整理入口和对照说明，没有替换运行代码或旧证据。文档中的“本机已存在”以 2026-10-08 核查为准。

## 交付前自己回答

能用自己的话说明一个反例、一个指标分母、一次真实命令与产物，以及一个会让你放弃 H1 的结果。[分析提纲](LAB_ANALYSIS.zh-CN.md)末尾已填入简稿，[完整稿](OPEN_QUESTION_AND_HYPOTHESIS.zh-CN.md)展开论证；核对原文和运行记录后再决定将哪些内容整理到 main。
