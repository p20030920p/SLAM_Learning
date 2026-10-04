# Group 1 障碍物/透明物体感知 — 官方代码仓库审计

审计日期：2026-10-05（Asia/Shanghai）。所有 URL 均用 `curl -s -o /dev/null -w '%{http_code}' -L` 实测。
判定原则：只认论文作者自己发布的仓库；第三方复现一律不计入「官方代码」。

## 汇总

| 论文 | 官方代码 | 结论 |
| :--- | :--- | :--- |
| TerrainNet (RSS 2023) | 无 | 未开源，无第三方复现 |
| DuLoc (IROS 2025) | 无 | 未开源，私有数据集 |
| LT-mapper (ICRA 2022) | https://github.com/gisbi-kim/lt-mapper | 开源可用，ROS 1 only |
| Trans4Trans (T-ITS 2022) | https://github.com/jamycheung/Trans4Trans | 开源可用，权重/数据分散 |
| Segmenting Transparent Objects in the Wild (ECCV 2020) | https://github.com/xieenze/Segment_Transparent_Objects | 开源可用，锁 torch 1.1.0 |
| Don't Hit Me! Glass Detection (CVPR 2020) | https://github.com/Mhaiyang/CVPR2020_GDNet | 开源可用，数据集需申请 |
| Seeing Through Fog Without Seeing Fog (CVPR 2020) | https://github.com/princeton-computational-imaging/SeeingThroughFog | 只有数据集/评测工具，无融合网络训练代码 |

---

### TerrainNet

| 项 | 内容 |
| :--- | :--- |
| 论文 | TerrainNet: Visual Modeling of Complex Terrain for High-speed, Off-road Navigation |
| DOI / venue | 10.15607/rss.2023.xix.103 · RSS 2023 |
| 官方代码 | **无** |
| 证据 | 无本地 PDF。下载 RSS 官方论文 PDF（http://www.roboticsproceedings.org/rss19/p103.pdf，15.4 MB）后 `pdftotext -layout` 全文检索：`github` 0 次、`gitlab` 0 次、`code is available` 0 次，全文唯一 URL 是项目页 https://sites.google.com/view/visual-terrain-modeling（HTTP 200），该页只有定性结果视频，无任何代码入口。RSS 论文页（https://rss2023.github.io/rss2023-website/program/papers/103/，HTTP 200）的 Links 只有 Supplementary；下载 p103_sup.zip（12.0 MB）确认其内容仅 `p103_sup.pdf` 一个文件，无代码。第一作者主页 https://xymeng.github.io/xymeng/ 的 TerrainNet 条目只有 `[paper]`，而同页 HCG / rmp_nav / semantic_bevnet 都有 `[code]`，说明作者有意未放代码。GitHub 仓库搜索 `terrainnet` 共 5 个结果（Semiott/TerrainNet 是气候+ZKP 项目，其余为无关小项目），没有一个对应本论文。 |
| 仓库状态 | 不适用（无仓库） |
| 第三方实现 | 无（未找到该论文方法的任何第三方复现） |
| 复现注意 | 无代码、无权重、无数据。训练集为自采 20k 帧（4× MultiSense 立体相机 + 3× Velodyne 32 线，Polaris RZR 平台），未公开；语义 GT 由人工标注 6k 帧 LiDAR + Cylinder3D 伪标签生成；训练用 4× A40。想复现必须自建同构传感器平台重采数据，成本极高。项目页视频可作定性对照。 |

### DuLoc

| 项 | 内容 |
| :--- | :--- |
| 论文 | DuLoc: Life-Long Dual-Layer Localization in Changing and Dynamic Expansive Scenarios |
| DOI / venue | 10.1109/IROS60139.2025.11246422 · IROS 2025 |
| 官方代码 | **无** |
| 证据 | 本地 PDF `040_DuLoc.pdf`（= arXiv 2507.23660v1）全文检索：`github` 0 次、`gitlab` 0 次；无 code availability 段落，唯一的 "source code" 出现在「we compare ... using the source code provided by their respective authors」（指基线方法），无任何代码/数据链接。arXiv abs 页（https://arxiv.org/abs/2507.23660，HTTP 200）无 Code 链接、Comments 字段为空；仅存在 v1（v2 → HTTP 404），即后续版本也没有补链接；ar5iv 全文 HTML 中同样 0 个代码链接。GitHub 仓库搜索 `duloc`（28 个结果，全为蛋白亚细胞定位、Swift 加密库、CK2 mod 等无关项目）、`duloc localization`（1 个无关）、`DuLoc LiDAR` 与 `dual-layer localization lidar`（均 0 个）— 均无对应仓库。IEEE Xplore 的 IROS 正式版为付费墙，未能核验 camera-ready 是否新增代码声明（已如实说明）。HKUST 机构库记录（hdl.handle.net/1783.1/169432）重定向死循环，无法访问。 |
| 仓库状态 | 不适用（无仓库） |
| 第三方实现 | 无 |
| 复现注意 | 数据集私有：论文自述「we conduct comprehensive experiments on our private datasets」，为某集装箱港口 32 台 IGV、2,856 小时运行数据，测试区域约 100 万 m²，GT 来自 RTK 融合（50 Hz），16 线 LiDAR×2（10 Hz）+ IMU（100 Hz）。硬件/场景均不可得，无任何可复现路径。 |

### LT-mapper

| 项 | 内容 |
| :--- | :--- |
| 论文 | LT-mapper: A Modular Framework for LiDAR-based Lifelong Mapping |
| DOI / venue | 10.1109/ICRA46639.2022.9811916 · ICRA 2022 |
| 官方代码 | https://github.com/gisbi-kim/lt-mapper |
| 证据 | 论文 PDF 正文脚注 1 直接给出：`1 The code is available at https://github.com/gisbi-kim/lt-mapper.`，并在正文引用了同地址的脚注 2（另脚注 3 指向配套的 https://github.com/gisbi-kim/SC-LIO-SAM）。仓库 README 首行标题为 “LT-mapper: A Modular Framework for LiDAR-based Lifelong Mapping”，README 的 BibTeX 明确引用 ICRA 2022 LT-mapper（Kim & Kim），与论文一致。 |
| 仓库状态 | HTTP 200 · MIT License（Copyright (c) 2025 Giseop Kim，`LICENSE` 实测）· 与论文对应：是（标题、BibTeX、三大模块 LT-SLAM / LT-removert / LT-map 均一致；550 stars，最后 push 2025-02-18） |
| 第三方实现 | 无（仅有 fork；官方仓库本身即完整实现） |
| 复现注意 | ① **仅 ROS 1**：README 明确 “ROS (tested with Melodic and Noetic)”，用 `catkin build ltslam removert`，无 ROS 2 分支/说明；② 依赖 GTSAM 4.0.x（需加 borglab PPA）；③ **前序数据不自带**：必须先跑外部 saver（SC-LIO-SAM / SC-A-LOAM / FAST_LIO_SLAM 的 saver 工具）生成关键帧点云 + Scan Context 描述子 + pose graph，才能进 LT-mapper；④ 示例 ParkingLot 数据集通过 bit.ly 短链分发（非 GitHub Release，链接长期性存疑）；⑤ 已提供 Docker 镜像 `dongjae0107/lt-mapper:latest`，是较省事的路径。 |

### Trans4Trans

| 项 | 内容 |
| :--- | :--- |
| 论文 | Trans4Trans: Efficient Transformer for Transparent Object and Semantic Scene Segmentation in Real-World Navigation Assistance |
| DOI / venue | 10.1109/tits.2022.3161141 · T-ITS 2022 |
| 官方代码 | https://github.com/jamycheung/Trans4Trans |
| 证据 | GitHub 检索论文题目得到第一作者 Jiaming Zhang 的仓库（jamycheung）；README 同时给出会议版（ICCVW 2021, arXiv 2107.03172）与**期刊版**（T-ITS, arXiv 2108.09174）链接，Citations 段落给出 `@article{zhang2022trans4trans, ... journal={IEEE Transactions on Intelligent Transportation Systems}, year={2022}}`，与本次审计的 T-ITS 2022 论文为同一篇（arXiv 2108.09174 即 T-ITS 版）。 |
| 仓库状态 | HTTP 200 · Apache-2.0（`LICENSE` 实测为 Apache License 2.0；README 补充「For commercial use, please contact with the authors」）· 与论文对应：是 |
| 第三方实现 | 无（README 的 References 里 SegmenTron / Trans2Seg / mmsegmentation 均为其代码依赖，非复现） |
| 复现注意 | ① 权重不随仓库分发：Trans10K-v2 与 COCO-Stuff 权重（`model_trans.pth`、`model_cocostuff.pth`）在 Google Drive 文件夹，需手工放置；② 训练/评测数据集全部需另行获取且多为注册制：Cityscapes（注册+协议）、ACDC、DensePASS、Stanford2D3D、Trans10K；③ 助盲演示依赖硬件 **Intel RealSense R200 + librealsense legacy(v1) 分支 + pyrealsense==2.2**，现代 librealsense2 不代表可直接跑；④ 环境锁定 python 3.7 / torch 1.8.0 / cudatoolkit 11.1；⑤ 需先备好 PVT 系列 ImageNet 预训练权重。 |

### Segmenting Transparent Objects in the Wild

| 项 | 内容 |
| :--- | :--- |
| 论文 | Segmenting Transparent Objects in the Wild |
| DOI / venue | 10.1007/978-3-030-58601-0_41 · ECCV 2020 |
| 官方代码 | https://github.com/xieenze/Segment_Transparent_Objects |
| 证据 | 该仓库为第一作者 Enze Xie 名下；README 原文 “This repository contains the data and code for ECCV2020 paper [Segmenting Transparent Objects in the Wild](https://arxiv.org/abs/2003.13948)”，并指向 Trans10K 数据集官网 https://xieenze.github.io/projects/TransLAB/TransLAB.html（HTTP 200）。仓库 description 亦为 “Data and code for ECCV2020 paper 'Segmenting Transparent Objects in the Wild'”。 |
| 仓库状态 | HTTP 200 · Apache-2.0 · 与论文对应：是（113 stars，最后 push 2022-12-10） |
| 第三方实现 | 无第三方实现；但需注意作者本人的 **IJCAI 2021 后续工作** 仓库 https://github.com/xieenze/Trans2Seg（HTTP 200，README 自称 IJCAI 2021 “Segmenting transparent object in the wild with transformer”，Trans10K-v2），它是同组官方扩展、**不是** ECCV 2020 这篇的仓库，别混用。 |
| 复现注意 | ① README 明确警告 **torch 必须为 1.1.0**：“>1.1.0 will cause performance drop, we can't find the reason”——用新版 PyTorch 会掉点；② 数据与权重都不在仓库内：Trans10K 数据经数据集官网（Google Drive / 百度网盘，提取码 oqms）分发，TransLab 预训练权重在 Google Drive；③ 代码基于 Segmentron 框架，需 `python setup.py develop`；④ 网盘链接长期有效性需自行确认。 |

### Glass Detection in Real-World Scenes ("Don't Hit Me!")

| 项 | 内容 |
| :--- | :--- |
| 论文 | Don't Hit Me! Glass Detection in Real-World Scenes |
| DOI / venue | 10.1109/CVPR42600.2020.00374 · CVPR 2020 |
| 官方代码 | https://github.com/Mhaiyang/CVPR2020_GDNet |
| 证据 | 论文官方项目页 https://mhaiyang.github.io/CVPR2020_GDNet/index.html（HTTP 200）显式给出 [Code] 链接即该仓库；项目页作者列表与论文完全一致（Haiyang Mei, Xin Yang, ... Rynson W.H. Lau，大连理工等）。仓库 README 标题 `CVPR2020_GDNet` + 副标题 “Don't Hit Me! Glass Detection in Real-world Scenes” + 完整作者与 CVPR 2020 BibTeX，与论文一一对应。 |
| 仓库状态 | HTTP 200 · 自定义 BSD 3-Clause 风格许可（`License.txt`：「Copyright (c) 2020, All rights reserved. School of Computer Science and Technology, Dalian University of Technology」+ 三条款 BSD 正文；GitHub 侧识别为 “Other / NOASSERTION”）· 与论文对应：是 |
| 第三方实现 | 无独立第三方复现；仅有第三方**镜像/封装**：https://github.com/Charmve/Mirror-Glass-Detection （内含 CVPR2020_GDNet 副本，HTTP 200）、https://github.com/prime-slam/glass-detection-dockers （把玻璃分割算法打包成 Docker，HTTP 200）。 |
| 复现注意 | ① **GDD 数据集为申请制**：官方数据集页 http://iccddlut.com/dataset/gdd（HTTP 200）正文末尾写着 “Please enter your application information for dataset”，即需提交申请信息才能下载，非直接开放；② 训练好的 `GDNet.pth` 与 ResNeXt-101 主干权重经项目页 Google Drive 链接分发（实测 200），主干需自行下载后放置；③ 依赖第三方仓库 `Mhaiyang/dss_crf`（需另 `git clone` + `setup.py install`）；④ 环境锁 PyTorch 1.0.0 / TorchVision 0.2.1 / CUDA 10.0，现代环境需自行迁移；⑤ 仓库只提供 `infer.py` 推理脚本，训练流程未在 README 中给出。 |

### Seeing Through Fog Without Seeing Fog

| 项 | 内容 |
| :--- | :--- |
| 论文 | Seeing Through Fog Without Seeing Fog: Deep Multimodal Sensor Fusion in Unseen Adverse Weather |
| DOI / venue | 10.1109/cvpr42600.2020.01170 · CVPR 2020 |
| 官方代码 | https://github.com/princeton-computational-imaging/SeeingThroughFog |
| 证据 | 论文官方项目页 https://www.cs.princeton.edu/~fheide/AdverseWeatherFusion/（HTTP 200）的链接栏为 [Paper] [Supplement] [Bibtex] **[Code]** [Dataset]，其中 **[Code]** 指向该仓库；仓库 README 首段即给出本论文 PDF 链接与 CVPR 2020 的 BibTeX（`@InProceedings{Bijelic_2020_STF, ...}`），作者列表一致，确认是作者自己的官方发布。 |
| 仓库状态 | HTTP 200 · MIT License（仓库代码；`LICENSE` 实测 “MIT License Copyright (c) 2020”）· 与论文对应：**部分是** —— 该仓库是论文的官方「数据集 + 评测/可视化工具」仓库，**不含**论文提出的 entropy-steered 多模态融合网络的训练代码或权重。实测：下载 master 分支 tar 包（204.6 MB）遍历全部文件，`tools/` 下只有 CreateTFRecords、DatasetViewer、DatasetFoggification、DatasetStatisticsTools、ProjectionTools、Raw2LUTImages，全仓库仅 `splits/*` 与 `camera_model.py` 命中 train/model 关键字，无任何 fusion/network/train 的训练实现。（385 stars，最后 push 2025-06-05） |
| 第三方实现 | 未找到对该融合方法的第三方复现（论文方法代码似未公开）。 |
| 复现注意 | ① **能复现的只有数据集与评测**，论文核心方法（measurement-entropy 驱动的单阶段自适应融合）需自行重新实现，无权重可下载；② 数据集有独立使用条款：`terms_of_use.txt` 限定「permanent, royalty-free and non-exclusive for own research and teaching purposes」，**禁止商业使用与向第三方再分发**，且需从 https://light.princeton.edu/datasets/automated_driving_dataset/ 下载分卷 zip（SeeingThroughFogCompressed.zXX）后 `7z` 解压两次并用仓库内 sha256sum 校验；③ 训练代码缺失意味着论文所谓的「仅用晴天数据训练」这一关键设定无法直接照搬；④ 数据集为 DENSE 项目（欧盟 H2020）数据，含 GDPR 相关约束。 |

---

## 方法与可核验性说明

- 本地 PDF：`/home/qzl/workspace/Localise/01_task_books/materials/papers_pdf/040_DuLoc.pdf`、`068_LT_mapper.pdf`，用 `pdftotext -layout` 抽取全文后按 `github|gitlab|code|available|http` 等关键词逐行检索。
- 无本地 PDF 的论文：检索出版社/项目页 + 全文 PDF（TerrainNet 用 RSS 官方 proceedings PDF；DuLoc 用 arXiv v1 全文 + ar5iv HTML）+ GitHub 仓库搜索。
- 所有上报 URL 均实测返回 200（含仓库主页、项目页、数据集页、Google Drive 权重链接）；未能访问的资源已在上文逐条注明（IEEE Xplore 付费墙、HKUST 机构库重定向死循环）。
- 复核时间点：2026-10-05；仓库 star 数/最后 push 为该时点快照。
