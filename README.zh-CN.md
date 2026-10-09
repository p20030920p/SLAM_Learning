# 作者原始方法复现

本分支 `reproduce/author-originals` 从空白历史建立，单独运行 DUFOMap、BeautyMap、ConceptGraphs 和 HOV-SG 的作者仓库。原库以固定提交的 Git 子模块保存；实际执行和大文件在这台电脑的 WSL 独立目录。主分支的展示与简化实验不作为这里的复现结果。

**状态：两种 LiDAR 原始入口与作者评价已完成四份公开标注数据，共 1997 帧；CG SAM-only 完成 3 场景、Detect 完成 2 场景的原始语义评价；HOV-SG 20 帧家用地图与原评分完成。尚未完成四篇论文的全部实验。**

新增：[DUFOMap 表 IV 五组消融对照](docs/DUFOMAP_TABLE4.zh-CN.md)，SA/DA/AA 共 15 项与论文两位小数一致。

[BeautyMap 表 III 三组网格消融](docs/KITTI_PAPER_PROTOCOL.zh-CN.md)也已匹配论文 SA/DA/HA 共 9 项，历史／当前预处理结果分别保留。

另完成 [Python 原始点／体素输出对照](docs/DUFOMAP_OUTPUT_AUDIT.zh-CN.md)：同一 Python 参数下，输出表示和评价阈值强烈影响评分，不能把体素低 SA 直接当作静态点误删。

已补下载原始 KITTI 所需 333 帧并完成 01/02 两种原始方法及三组网格参数的评分。[新增结果与论文差距](docs/KITTI_SELECTED_RESULTS.zh-CN.md)。当前预处理与旧发布包存在版本差异，新结果单列。

ConceptGraphs 的[已完成场景表与图](docs/CONCEPTGRAPHS_SCENE_RESULTS.zh-CN.md)给出两种前端的原始分数、混淆矩阵复算及场景行／`all` 行差别。HOV-SG 的[20 帧家用结果](docs/HOVSG_HOME_RESULTS.zh-CN.md)为 mIoU 34.7500%、F-mIoU 62.8725%；默认 200 帧仍未完成。这里有 [60 秒作者三维窗口实录](evidence/videos/conceptgraphs-room0-original-window.mp4)，可查看 RGB、实例颜色和视角操作。

[English](README.md) · [运行与结果](docs/STATUS.zh-CN.md) · [Windows 起步和命令](docs/RUNBOOK.zh-CN.md) · [数据下载与 ScanNet 申请](docs/DATA_ACCESS.zh-CN.md) · [环境](docs/ENVIRONMENT.zh-CN.md) · [原库和复现范围](docs/SCOPE.zh-CN.md) · [执行证据](evidence/README.md)

| 方法 | 作者原库 | 本分支固定提交 |
|---|---|---|
| DUFOMap | [KTH-RPL/dufomap](https://github.com/KTH-RPL/dufomap) | `9e239ddd` |
| BeautyMap | [MKJia/BeautyMap](https://github.com/MKJia/BeautyMap) | `98bce4a9` |
| ConceptGraphs | [concept-graphs/concept-graphs](https://github.com/concept-graphs/concept-graphs) | `93277a02` |
| HOV-SG | [hovsg/HOV-SG](https://github.com/hovsg/HOV-SG) | `d6e65a53` |
| 动态点云评价 | [KTH-RPL/DynamicMap_Benchmark](https://github.com/KTH-RPL/DynamicMap_Benchmark) | `8b60f36a` |

作者源码保持原样。依赖、编译器、数据路径或 API 模型的变化必须单独记录。DeepSeek 只属于替代模型实验，不能算原论文 GPT-4 的复现；本轮费用上限为 1 美元，密钥和大文件不提交 Git。

个人阅读、假设分析、家中测试与手动录制的索引在另一个 [学习文档分支](https://github.com/p20030920p/SLAM_Learning/blob/notes/personal-study-guide-20261008/notes/README.zh-CN.md)。本分支专门保留作者流程与执行证据。
