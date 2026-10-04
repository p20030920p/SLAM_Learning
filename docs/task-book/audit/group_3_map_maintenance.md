# Group 3 · Map Maintenance / Dynamic Point Removal — Official Code Audit

Audit date: 2026-10-05. Every URL below was fetched and returned HTTP 200 at audit time
(`curl -s -o /dev/null -w '%{http_code}' <url>`). "Official" = released by the paper's own authors.
Where the only code is third-party, `官方代码` is **无** and the third-party code is named separately.

---

### DUFOMap
| 项 | 内容 |
| :--- | :--- |
| 论文 | DUFOMap: Efficient Dynamic Awareness Mapping |
| DOI / venue | 10.1109/LRA.2024.3387658 · IEEE RA-L 2024 |
| 官方代码 | https://github.com/KTH-RPL/dufomap |
| 证据 | 本地 PDF `048_DUFOMap.pdf` 正文原文："Our approach is open-source at https://github.com/KTH-RPL/dufomap"（第 132 行）。项目页脚注 1 = https://kth-rpl.github.io/dufomap（HTTP 200）。仓库 README 标题即 "DUFOMap: Efficient Dynamic Awareness Mapping"，作者为 KTH RPL（Daniel Duberg 等）。 |
| 仓库状态 | HTTP 200 · 许可 BSD-3-Clause（LICENSE: "Copyright (c) 2024, Daniel Duberg"）· 与论文对应 是 |
| 第三方实现 | 无（该仓库本身即官方实现；DynamicMap_Benchmark 中另有官方维护的基准适配） |
| 复现注意 | 无 ROS 节点：官方仓库根目录只有 `src/`、`main.py`、`Dockerfile`、`CMakeLists.txt`（`ufomap` 为 submodule），以离线 CLI / Python API（`pip install dufomap`）为主，论文中的 online 场景需自行接 ROS。数据须先转成 DynamicMap_Benchmark 的统一格式；示例数据（KITTI 00, ~384 MB）在 Zenodo。C++ 版要求 gcc-10 / g++-10 + TBB + lz4。 |

### DynPurge
| 项 | 内容 |
| :--- | :--- |
| 论文 | DynPurge: Dynamic Point Removal via Spatiotemporal Distribution Range in Global-Scale LiDAR Maps |
| DOI / venue | 10.1109/LRA.2025.3623005 · IEEE RA-L 2025 |
| 官方代码 | **无**（未发布任何可运行实现） |
| 证据 | (1) 无本地 PDF；(2) 未检索到 arXiv 预印本（arXiv API `all:"DynPurge"` 返回 0 条），故无预印本代码链接可查；(3) IEEE Xplore 文档页 11206482 正文为 JS 渲染/付费墙，web_fetch 只取到页脚，无法确认论文内是否有代码声明——此项未能核实；(4) 全网检索仅命中一个 GitHub 仓库，但其中**只有算法伪代码截图与结果图片，没有代码**（见下）。因此判定：无官方可运行代码。 |
| 仓库状态 | 官方仓库不存在；伪代码页 https://github.com/yutoulu/The-Detail-of-DynPurge HTTP 200 · 许可 无（仓库未声明 LICENSE）· 与论文对应 存疑 |
| 第三方实现 | 无第三方复现。仅有第一作者疑似本人维护的说明页：https://github.com/yutoulu/The-Detail-of-DynPurge（README 自述 "we will introduce the pseudo-code of the method DynPurge…"，内容为伪代码图 + SemanticKITTI/MCD/Argoverse2 结果截图，**不可运行**）。作者身份为推测：该账号另一仓库 `The-code-for-MSD-VMMS-HK-dataset` 对应 ORCID 0009-0007-6642-0568（Shengyu Lu，PolyU LSGI，与 Crossref 记录的 DynPurge 第一作者单位一致）名下的 MSD-VMMS-HK 数据集论文，但仓库页面本身未声明作者身份。 |
| 复现注意 | **无法复现**：无源码、无参数、无预训练权重；只有伪代码流程与定性结果图。论文方法依赖 LiDAR 点云时间戳分布，若自行实现需自备 SemanticKITTI（需注册）/ MCD / Argoverse 2（需同意条款）的逐点时间戳与位姿。 |

### Ephemerality meets LiDAR-based Lifelong Mapping (ELite)
| 项 | 内容 |
| :--- | :--- |
| 论文 | Ephemerality meets LiDAR-based Lifelong Mapping |
| DOI / venue | 10.1109/ICRA55743.2025.11127618 · IEEE ICRA 2025 |
| 官方代码 | https://github.com/dongjae0107/ELite |
| 证据 | 本地 PDF `041_Ephemerality_meets_LiDAR_Lifelong_Mapping.pdf` 摘要原文："The source code is publicly available for the robotics community: https://github.com/dongjae0107/ELite."（第 29 行）。仓库 README 标题 "ELite: Ephemerality meets LiDAR-based Lifelong Mapping"，作者列表与论文完全一致（Hyeonjae Gil, Dongjae Lee, Giseop Kim, Ayoung Kim），Contact 邮箱为 dongjae0107@gmail.com（= 仓库 owner）。 |
| 仓库状态 | HTTP 200 · 许可 MIT（"Copyright (c) 2026 Dongjae Lee"）· 与论文对应 是 |
| 第三方实现 | 无 |
| 复现注意 | 多 session 对齐需要**人工给出初始变换**：README 明确要求"用 CloudCompare 做 ICP，填入变换矩阵"，论文中的全局定位（Scan Context）版本尚未发布（"In near future, we are planning to automate this process"）；因此第一帧对齐质量直接决定结果。示例数据（ParkingLot 序列 01/02）通过 Google Drive 分发（`scripts/download_parkinglot.sh`），大文件需自备云盘访问。CUDA 加速匹配需额外编译 `pygicp`/fast_gicp，否则退化为 CPU 匹配。环境为 conda + Python 3.10（无 ROS 依赖）。 |

### Khronos
| 项 | 内容 |
| :--- | :--- |
| 论文 | Khronos: A Unified Approach for Spatio-Temporal Metric-Semantic SLAM in Dynamic Environments |
| DOI / venue | 10.15607/RSS.2024.XX.081 · Robotics: Science and Systems (RSS) 2024 |
| 官方代码 | https://github.com/MIT-SPARK/Khronos |
| 证据 | 本地 PDF `013_Khronos.pdf` 正文："We release our implementation and datasets open-source.¹"，脚注 1："Released upon acceptance at https://github.com/MIT-SPARK/Khronos."（第 84、126 行）。仓库 README 引用同一论文并列出 DOI 10.15607/RSS.2024.XX.081，作者为 MIT SPARK Lab（Schmid, Abate, Chang, Carlone）。 |
| 仓库状态 | HTTP 200 · 许可 BSD-3-Clause（"Copyright (c) 2024, Massachusetts Institute of Technology"）· 与论文对应 是 |
| 第三方实现 | 无 |
| 复现注意 | 环境要求苛刻：README 声明 "tested on Ubuntu 24.04 & ROS2 Jazzy"，**ROS2 Iron 以下无法编译**；ROS2 版本仍标注 "in active development and is unstable and may not fully be feature-complete"（2025-10 才发布 ROS2 版）。依赖需 `vcs import` 拉取多个 MIT-SPARK 仓库。数据集（`tesse_cd` 仿真序列 + `khronos_real` mezzanine rosbag）通过 Google Drive 分发，且 **ROS2 bag 是目录而非单文件**，解压方式易错。开放集分割需额外编译 `semantic_inference`，无 TensorRT 时只能用开放集；首次运行会自动下载模型权重。 |

### A Dynamic Points Removal Benchmark in Point Cloud Maps (DynamicMap_Benchmark)
| 项 | 内容 |
| :--- | :--- |
| 论文 | A Dynamic Points Removal Benchmark in Point Cloud Maps |
| DOI / venue | arXiv:2307.07260（任务书未给 DOI；仓库引用给出 10.1109/ITSC57777.2023.10422094）· IEEE ITSC 2023 |
| 官方代码 | https://github.com/KTH-RPL/DynamicMap_Benchmark |
| 证据 | 本地 PDF `064_Dynamic_Points_Removal_Benchmark_DynamicMap.pdf` 正文原文："We contribute the benchmark implementation and extended datasets to the research community at https://github.com/KTH-RPL/DynamicMap_Benchmark."（第 62 行附近）。仓库 README 标题与论文同名，且 Cite 段落给出该论文的 ITSC 2023 条目；作者为 KTH RPL（Qingwen Zhang 等）。 |
| 仓库状态 | HTTP 200 · 许可 BSD-3-Clause（"Copyright (c) 2024, Robotics, Perception and Learning @KTH"）· 与论文对应 是 |
| 第三方实现 | 无（仓库内的各方法子模块部分是第三方方法，但由本基准作者改造并置于其下：dynablox→ethz-asl、ERASOR→LimHyungTae、Removert→irapkaist、octomap→OctoMap；README 明确要求"check the LICENSE of each method in their official link"） |
| 复现注意 | 仓库持续更新，**与 ITSC'23 论文快照不一致**：论文发布 5 个方法 / 3 个数据集，当前 `methods/` 已含 8 个（BeautyMap、DeFlow、ERASOR、dufomap、dynablox、octomap、removert 等），复现论文表格需固定 commit。必须 `git clone --recurse-submodules`（漏掉 submodule 会缺数据/方法）。数据集版权各自独立：SemanticKITTI 需注册下载、Argoverse 2 需同意条款，仅有 KITTI 00 等部分序列以统一格式放在 Zenodo。项目 wiki：https://kth-rpl.github.io/DynamicMap_Benchmark/（HTTP 200）。 |

### NGD-SLAM
| 项 | 内容 |
| :--- | :--- |
| 论文 | NGD-SLAM: Towards Real-Time Dynamic SLAM without GPU |
| DOI / venue | 10.1109/IROS60139.2025.11246202 · IEEE/RSJ IROS 2025 |
| 官方代码 | https://github.com/yuhaozhang7/NGD-SLAM |
| 证据 | 任务书已确认（论文正文声明）；本地 PDF `007_NGD_SLAM.pdf` 第 35–36 行同样原文："we make our code publicly available at: https://github.com/yuhaozhang7/NGD-SLAM"。README 标题、作者（Yuhao Zhang, Mihai Bujanca, Mikel Luján）、BibTeX 中的 DOI 10.1109/IROS60139.2025.11246202 与论文完全一致。 |
| 仓库状态 | HTTP 200 · 许可 GPL-3.0（LICENSE = GNU GPL v3）· 与论文对应 是 |
| 第三方实现 | 无（其上游 ORB-SLAM3 = UZ-SLAMLab/ORB_SLAM3 为基础框架，非本论文的复现） |
| 复现注意 | 基于 ORB-SLAM3 衍生的 C++ 工程，需 Pangolin + OpenCV ≥ 4.4 + Eigen ≥ 3.1.0 + C++11；README 声明测试于 Ubuntu 20.04 / 22.04。**权重已随仓库发布**（YOLO-fastest 配置与权重在 `Thirdparty/`，无 GPU 需求），但 DBoW2/g2o 为修改版内嵌，勿用系统版覆盖。许可证为 GPL-3.0（继承 ORB-SLAM3），闭源商用受限。示例评测走 TUM RGB-D 序列（如 freiburg3_walking_xyz），Bonn 动态序列需自行下载。 |

### Mobile-Seed
| 项 | 内容 |
| :--- | :--- |
| 论文 | Mobile-Seed: Joint Semantic Segmentation and Boundary Detection for Mobile Robots |
| DOI / venue | 10.1109/LRA.2024.3373235 · IEEE RA-L 2024 |
| 官方代码 | https://github.com/WHU-USI3DV/Mobile-Seed |
| 证据 | 无本地 PDF。arXiv:2311.12651 摘要与 Comments 均写明 "Code, pre-trained models and additional results are available at https://whu-usi3dv.github.io/Mobile-Seed/"（HTTP 200），该 DOI 由 arXiv 明确关联到 10.1109/LRA.2024.3373235；项目页对应的 GitHub 组织 WHU-USI3DV 即作者课题组（武汉大学 USI3DV）。仓库 README 开头自述 "This is the official PyTorch implementation of the following publication"，作者列表与论文一致（Liao, Kang, Li, Liu, Liu, Dong, Yang, Chen）。 |
| 仓库状态 | HTTP 200 · 许可 BSD-2-Clause（"Copyright (c) 2023, WHU-USI3DV"）· 与论文对应 是 |
| 第三方实现 | 无 |
| 复现注意 | 代码框架为 MMSegmentation 风格（`tools/dist_test.sh`、configs）。**预训练权重与 ImageNet 主干权重放在 OneDrive 及百度网盘**（含提取码），中国大陆以外/无网盘账号者下载不便；Cityscapes 数据需在官网注册后下载（gtFine/leftImg8bit）。基线 AFFormer 权重需另行下载才能公平对比。评测需 GPU（论文速度基线为 RTX 2080 Ti 23.9 FPS）。 |

### Clio
| 项 | 内容 |
| :--- | :--- |
| 论文 | Clio: Real-time Task-Driven Open-Set 3D Scene Graphs |
| DOI / venue | 10.1109/LRA.2024.3451395 · IEEE RA-L 2024 |
| 官方代码 | https://github.com/MIT-SPARK/Clio |
| 证据 | 本地 PDF `083_Clio.pdf` 正文原文："We release Clio open-source at https://github.com/MIT-SPARK/Clio along with our custom datasets."（第 172 行）。仓库 README 引用同一论文，BibTeX 中 doi=10.1109/LRA.2024.3451395，作者为 MIT SPARK Lab（Maggio, Chang, Hughes, …, Carlone）。 |
| 仓库状态 | HTTP 200 · 许可 BSD-2-Clause（"Copyright (c) 2024, Massachusetts Institute of Technology"）· 与论文对应 是 |
| 第三方实现 | 无 |
| 复现注意 | **ROS1（catkin）工程**：README 指导 `catkin init` / `catkin build`，只提供 "python-only" 的离线场景图聚类路径，不装 ROS 就跑不了在线建图。依赖 `semantic_inference` 默认按 NVIDIA TensorRT 编译，无 TensorRT 时需 `catkin config -a -DSEMANTIC_INFERENCE_USE_TRT=OFF`（否则编译/运行受限，只能用开放集部分）。自定义数据集（Office/Apartment/Cubicle/Building）与预构建场景图均托管在 **Dropbox 分享目录**，非稳定镜像；每个场景含 rosbag + COLMAP 稠密重建。 |

### FAST-LIO2
| 项 | 内容 |
| :--- | :--- |
| 论文 | FAST-LIO2: Fast Direct LiDAR-Inertial Odometry |
| DOI / venue | 10.1109/TRO.2022.3141876 · IEEE Transactions on Robotics (T-RO) 2022 |
| 官方代码 | https://github.com/hku-mars/FAST_LIO |
| 证据 | 本地 PDF `042_FAST_LIO2.pdf` 脚注 2/3（第 74–76 行）："https://github.com/hku-mars/FAST_LIO"（ikd-Tree）；正文第 116–117 行："The new system is termed as FAST-LIO2 and is open-sourced at Github²"；第 46 行："data structure ikd-Tree are both open-sourced on Github²,³"。仓库 README 含 "FAST-LIO 2.0 (2021-07-05 Update)" 章节并附 FAST-LIO2 视频与 pipeline 图，作者为 HKU MARS Lab。 |
| 仓库状态 | HTTP 200 · 许可 GPL-2.0（LICENSE = GNU GPL v2）· 与论文对应 是 |
| 第三方实现 | 无（论文另一贡献 ikd-Tree 单独开源于 https://github.com/hku-mars/ikd-Tree ，HTTP 200，官方同一课题组） |
| 复现注意 | 仓库同时包含 FAST-LIO 1 与 2，需按 README 的 "FAST-LIO 2.0" 章节操作；**ROS1 工程**（ROS ≥ Melodic，Ubuntu ≥ 16.04；Ubuntu 18.04+ 用系统默认 PCL/Eigen 即可）。许可证为 GPL-2.0。支持旋转式（Velodyne/Ouster）与固态（Livox Avia/Horizon/MID-360）LiDAR，但不同雷达的 extrinsics/时间同步配置差异大；`ikd-Tree` 为独立仓库（本仓库已内含副本），改代码时注意两处不同步。关于该系统的第三方工程化改写（如 FAST_LIO_SAM 等）不属于官方范围，未在此审计。 |

---

## Summary

| # | Paper | Official repo | HTTP | License | Biggest reproduction caveat |
| :-- | :--- | :--- | :--- | :--- | :--- |
| 1 | DUFOMap | https://github.com/KTH-RPL/dufomap | 200 | BSD-3-Clause | 官方仓库无 ROS 节点，只有离线 CLI/Python API；数据须转统一格式 |
| 2 | DynPurge | **无** | — | — | 完全没有可运行代码，仅第一作者疑似账号的伪代码页 |
| 3 | ELite | https://github.com/dongjae0107/ELite | 200 | MIT | 多 session 需手工 CloudCompare ICP 初值，全局定位版本未发布 |
| 4 | Khronos | https://github.com/MIT-SPARK/Khronos | 200 | BSD-3-Clause | 仅 Ubuntu 24.04 + ROS2 Jazzy（≥Iron），ROS2 版官方标注不稳定 |
| 5 | DynamicMap_Benchmark | https://github.com/KTH-RPL/DynamicMap_Benchmark | 200 | BSD-3-Clause | 仓库已超出 ITSC'23 论文快照（8 vs 5 方法），需固定 commit + 递归 submodule |
| 6 | NGD-SLAM | https://github.com/yuhaozhang7/NGD-SLAM | 200 | GPL-3.0 | 权重随仓库发布，但 GPL-3.0 许可 + 依赖修改版 DBoW2/g2o |
| 7 | Mobile-Seed | https://github.com/WHU-USI3DV/Mobile-Seed | 200 | BSD-2-Clause | 预训练权重在 OneDrive/百度网盘，Cityscapes 需注册下载 |
| 8 | Clio | https://github.com/MIT-SPARK/Clio | 200 | BSD-2-Clause | ROS1/catkin + 需关 TensorRT 才能编译；数据集在 Dropbox |
| 9 | FAST-LIO2 | https://github.com/hku-mars/FAST_LIO | 200 | GPL-2.0 | ROS1 工程、同仓库混装 FAST-LIO 1/2；GPL-2.0 传染性 |

**Bottom line:** 8 of 9 papers have an official author-released repository, all live (HTTP 200). Only **DynPurge** has no official code — treat it as non-reproducible from released artifacts.
