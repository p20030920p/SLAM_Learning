# Group 5 审计：优化 / 主动感知方向（Items 1–10）

审计日期：2026-10-05（Asia/Shanghai）
审计范围：任务书 Group 5 引用的 9 篇论文 + 3 个库（其中 g2o/GTSAM/Ceres 为库，非论文）。
方法：优先本地 PDF 全文（`pdftotext -layout`），其次出版方/项目页/作者实验室页，最后网络检索；每个报告的 URL 均以 `curl -s -o /dev/null -w '%{http_code}' -L` 实测 HTTP 状态。
所有 URL 实测时间：2026-10-05。

---

### 1. Kimera-Multi
| 项 | 内容 |
| :--- | :--- |
| 论文 | Kimera-Multi: Robust, Distributed, Dense Metric-Semantic SLAM for Multi-Robot Systems |
| DOI / venue | 10.1109/TRO.2021.3137751 · IEEE Transactions on Robotics (T-RO) 2022 |
| 官方代码 | https://github.com/MIT-SPARK/Kimera-Multi |
| 证据 | 本地 PDF `066_Kimera_Multi.pdf` 全文检索无任何 github/代码链接，补充材料仅给出视频 https://youtu.be/G7I3JubdU8E。官方仓库经作者实验室（MIT SPARK Lab，Luca Carlone 组）项目页确认：该页对本文的 BibTeX 内含 `\linkToWeb{https://github.com/MIT-SPARK/Kimera-Multi}`；仓库 README 描述的系统与摘要逐条对应，并链接本文 arXiv:2106.14386。 |
| 仓库状态 | HTTP 200 · 许可 **未标注**（index repo，根目录无 LICENSE；下载清单 `kimera_multi.repos` 内的子仓库各自带许可）· 与论文对应 **是** |
| 第三方实现 | 无（`MIT-SPARK/Kimera-Distributed`、`MIT-SPARK/Kimera-Multi-LCD` 为同实验室的组成模块，非第三方） |
| 复现注意 | 仓库是 index repo，必须 `vcs import` 递归拉取多个子仓库才能构建；README 明确论文实验在 Ubuntu 18.04 + ROS Melodic，仓库现已改为假设 Ubuntu 20.04 + ROS Noetic（版本漂移）；需专用 CMake 选项（`-DGTSAM_TANGENT_PREINTEGRATION=OFF`、`GTSAM_BUILD_WITH_MARCH_NATIVE=OFF`、`OPENGV_BUILD_WITH_MARCH_NATIVE=OFF`）；数据集在 `MIT-SPARK/Kimera-Multi-Data`；最后推送 2025-01-28。 |

---

### 2. D²SLAM
| 项 | 内容 |
| :--- | :--- |
| 论文 | D²SLAM: Decentralized and Distributed Collaborative Visual-Inertial SLAM System for Aerial Swarm |
| DOI / venue | 10.1109/TRO.2024.3422003 · IEEE Transactions on Robotics (T-RO) 2024（仓库 citation 给出 vol. 40, pp. 3445–3464） |
| 官方代码 | https://github.com/HKUST-Aerial-Robotics/D2SLAM |
| 证据 | 无本地 PDF。作者（HKUST Aerial Robotics，Shaojie Shen 组）仓库 README 原文：“This is open-source code for **$D^2$SLAM**...”，并直接给出本文 T-RO DOI `10.1109/TRO.2024.3422003` 与 IEEE 链接。检索时先命中的 `UAV-Swarm/perception-D2SLAM` 经 GitHub API 的 `fork: true` / `parent: HKUST-Aerial-Robotics/D2SLAM` 证实**只是 fork**，不能当官方仓库。 |
| 仓库状态 | HTTP 200 · 许可 **未标注**（根目录无 LICENSE 文件，`raw.../main/LICENSE` 返回 404）· 与论文对应 **是** |
| 第三方实现 | 未发现独立第三方实现；仅有上述 fork：https://github.com/UAV-Swarm/perception-D2SLAM （14 stars，最后推送 2024-07-04，内容与上游同源） |
| 复现注意 | 前端加速强依赖 CUDA/TensorRT，官方推荐用仓库自带 Docker 镜像（PC 与 Jetson Xavier NX 两套）；CNN 模型需从 Dropbox 单独下载，链接易失效；无许可证意味着默认保留全部权利，商用/再分发需联系作者；最后推送 2024-12-13。 |

---

### 3. Swarm-SLAM
| 项 | 内容 |
| :--- | :--- |
| 论文 | Swarm-SLAM: Sparse Decentralized Collaborative Simultaneous Localization and Mapping Framework for Multi-Robot Systems |
| DOI / venue | 10.1109/lra.2023.3333742 · IEEE Robotics and Automation Letters (RA-L) 2024 |
| 官方代码 | https://github.com/MISTLab/Swarm-SLAM |
| 证据 | **本地 PDF 直接给出**：`050_Swarm_SLAM.pdf` 摘要末尾原文 “Our code is publicly available: https://github.com/MISTLab/Swarm-SLAM”。作者为 Pierre-Yves Lajoie、Giovanni Beltrame（MISTLab, Polytechnique Montréal），仓库 README 与论文标题/系统描述一致并链接 IEEE 页面。 |
| 仓库状态 | HTTP 200 · 许可 **MIT License**（`LICENSE.md`：“MIT License, Copyright (c) 2022 Pierre-Yves Lajoie”）· 与论文对应 **是** |
| 第三方实现 | 无 |
| 复现注意 | ROS 2 系统，主仓库需配合 `cslam.repos` 拉取子包（`lajoiepy/cslam`、`lajoiepy/cslam_interfaces` 等挂在个人账号下，不是 MISTLab 组织）；官方文档 https://lajoiepy.github.io/cslam_documentation/html/index.html （HTTP 200）；最后推送 2025-04-10。 |

---

### 4. GNC（Graduated Non-Convexity for Robust Spatial Perception）
| 项 | 内容 |
| :--- | :--- |
| 论文 | Graduated Non-Convexity for Robust Spatial Perception: From Non-Minimal Solvers to Global Outlier Rejection |
| DOI / venue | 10.1109/LRA.2020.2965893 · IEEE Robotics and Automation Letters (RA-L) 2020（作者仓库 BibTeX：vol. 5, no. 2, pp. 1127–1134） |
| 官方代码 | https://github.com/MIT-SPARK/GNC-and-ADAPT |
| 证据 | 无本地 PDF。arXiv 1909.08605 全文（https://arxiv.org/pdf/1909.08605 ，HTTP 200）检索**无** github/代码链接。通过作者实验室 MIT-SPARK 组织仓库清单定位到 `GNC-and-ADAPT`，其 README 明确把本文（H. Yang, P. Antonante, V. Tzoumas, L. Carlone, RA-L 2020，含完整 BibTeX）列为该仓库实现的三篇论文之一，仓库属作者所在 MIT SPARK 实验室。另有作者本人贡献的 C++ 实现：`borglab/gtsam` 的 `gtsam/nonlinear/GncOptimizer.h` 头注释写明 “Implementation of the paper: Yang, Antonante, Tzoumas, Carlone, Graduated Non-Convexity for Robust Spatial Perception...”，作者署名 Luca Carlone。 |
| 仓库状态 | HTTP 200 · 许可 **BSD-2-Clause**（GitHub license API 识别）· 与论文对应 **是**（但为 MATLAB 实现，不是论文中全部实验的完整复现包） |
| 第三方实现 | 无。（GTSAM 的 `GncOptimizer` 由论文作者 Luca Carlone 本人贡献，属作者官方 C++ 实现，**不算第三方**：https://github.com/borglab/gtsam ，HTTP 200） |
| 复现注意 | `GNC-and-ADAPT` 是 MATLAB 代码，创建于 2021-01-20、最后推送 2021-01-22，此后未再更新；仓库同时包含 ADAPT（IROS 2019）与另一篇 outlier-robust estimation 论文的代码，易与本文混淆；实用 C++ 复现应改用 GTSAM 的 `GncOptimizer`；论文中的 shape alignment（SOS）部分依赖额外求解器，仓库未包含端到端脚本。 |

---

### 5. ActLoc
| 项 | 内容 |
| :--- | :--- |
| 论文 | ActLoc: Learning to Localize on the Move via Active Viewpoint Selection |
| DOI / venue | https://proceedings.mlr.press/v305/li25b.html · CoRL 2025（PMLR vol. 305），无 DOI |
| 官方代码 | https://github.com/cvg/ActLoc |
| 证据 | 作者项目页 https://boysun045.github.io/ActLoc-Project/ （HTTP 200）中 “Code” 链接即指向该仓库；仓库 README 的标题、作者列表（Jiajie Li, Boyang Sun, Luca Di Giammarino, Hermann Blum, Marc Pollefeys）与 “CoRL 2025” 标注同论文完全一致，仓库归属 `cvg`（ETH Zürich Computer Vision and Geometry Lab，作者 Pollefeys/Sun 所在实验室）。PMLR 论文页 HTTP 200。 |
| 仓库状态 | HTTP 200 · 许可 **未标注**（`raw.../main/LICENSE` 返回 404）· 与论文对应 **是** |
| 第三方实现 | 无。相关但不同：作者组的 benchmark 仓库 `rvp-group/actloc_benchmark`（Active Localization Benchmark），不是本文方法实现。 |
| 复现注意 | 2025-09-21 才 “Initial code release”，最后推送 2025-09-21，代码很新且 README 顶部仍留有被注释掉的 “Work in Progress” 标记；README 声明仅在 Ubuntu 22.04 + RTX 4090(24GB) + CUDA 12.4 上测过；无 LICENSE，学术复用前需确认授权；有 HuggingFace 在线 demo（外部依赖）。 |

---

### 6. Active Neural Topological Mapping for Multi-Agent Exploration
| 项 | 内容 |
| :--- | :--- |
| 论文 | Active Neural Topological Mapping for Multi-Agent Exploration |
| DOI / venue | 10.1109/LRA.2023.3331892 · IEEE Robotics and Automation Letters (RA-L)，**vol. 9, no. 1, pp. 303–310**；见下方年份裁定 |
| 官方代码 | https://github.com/yang-xy20/mantm |
| 证据 | 无本地 PDF。作者项目网站 https://sites.google.com/view/mantm （HTTP 200）中的 “Github” 链接指向 `github.com/yang-xy20/mantm`；仓库 README 原文 “This is a PyTorch implementation of the paper: Active Neural Topological Mapping for Multi-Agent Exploration (arXiv 2311.00252)”，并给出与 Crossref 作者列表一致的作者（Xinyi Yang, Yuxiang Yang, Chao Yu, ..., Yu Wang，清华 + 美团）。arXiv 页面 Comments 字段为 “Accepted by Robotics and Automation Letters”。 |
| 仓库状态 | HTTP 200 · 许可 **MIT License** · 与论文对应 **是** |
| 第三方实现 | 无 |
| 复现注意 | README 大标题仍用论文旧题 “Learning Efficient Multi-Agent Cooperative Visual Exploration”，只认标题容易误判为别的论文；依赖极旧（`torch==1.5.1+cu101`、`scikit-image==0.17.2`、`attrs==19.1.0`），现代环境基本需重建；必须编译仓库 fork 的修改版 habitat-sim / habitat-lab（`git submodule update --init --recursive`）并自行准备 Gibson 数据集；预训练模型托管在 Google Drive 直链上，易失效；最后推送 2024-04-12。 |

**Item 6 年份裁定（任务书 33 条引用中唯一的 venue/year 不一致）：**

| 来源 | 日期 | 说明 |
| :--- | :--- | :--- |
| Crossref `published-print` / `issued` | **2024-01** | 正式期号（vol. 9, no. 1, pp. 303–310） |
| Crossref `created` | 2023-11-10 | 早期在线/early access 上线时间 |
| OpenAlex `publication_date` / `publication_year` | 2023-11-10 / 2023 | OpenAlex 取“最早发布日期”，即 early access |
| IEEE Xplore 页面 | **不可达** | `https://ieeexplore.ieee.org/document/10314737` 返回 HTTP **202 且响应体为空**（反爬），DOI 解析也落到该页（同样 202）。无法读出页面的 Date of Publication，已如实记录未取得该证据。 |

**结论：应以 2024 为年份记录（year of record）。** 理由：该文正式发表于 RA-L 第 9 卷第 1 期（2024 年 1 月），Crossref 的 `issued`/`published-print` 均为 2024-01，正式引用应写作 “IEEE RA-L, vol. 9, no. 1, pp. 303–310, Jan. 2024”。任务书的 “RA-L 2023” 并非错误到不可辩护——它对应 2023-11-10 的 early access 上线日，也正是 DOI 字符串含 `2023` 的原因（IEEE 在录用/在线阶段即铸造 DOI）；但若要求与期刊卷期一致的“正式年份”，**2024 才是可辩护的答案**，2023 只是在线优先日期。建议任务书改为 “RA-L 2024 (online 2023-11-10)”。

---

### 7. Control Barrier Functions: Theory and Applications
| 项 | 内容 |
| :--- | :--- |
| 论文 | Control Barrier Functions: Theory and Applications（**综述/tutorial 论文，非方法论文**，作者 Aaron D. Ames, Samuel Coogan, Magnus Egerstedt, Gennaro Notomista, Koushil Sreenath, Paulo Tabuada） |
| DOI / venue | 10.23919/ECC.2019.8796030 · European Control Conference (ECC) 2019 |
| 官方代码 | **NONE** |
| 证据 | 无本地 PDF；取 arXiv:1903.11199 全文（https://arxiv.org/pdf/1903.11199 ，HTTP 200）逐页检索 `github`/`code`/`open-source`/`software`：无任何代码仓库链接，全文唯一与产出物相关的表述是实验视频 “A video of the experiments is available online”。作者（Ames 等）未为这篇综述发布代码仓库——综述性论文属正常情况，本身也不需要代码。 |
| 仓库状态 | 无仓库可测。DOI 解析到 IEEE Xplore 返回 HTTP **202（空响应，反爬）**，未能读取 IEEE 页面，但不影响“作者未发布代码”这一判断。 |
| 第三方实现 | 未发现针对**本综述**的第三方实现（综述无可复现算法）。检索到的仅是第三方 CBF 资源，与本文无对应关系，均标注为非官方：https://github.com/tayalmanan28/Safety-Critical-Controls （CBF 论文清单，HTTP 200）、https://github.com/ersindas/Quadrotor_CBF （四旋翼 CBF 安全过滤器，HTTP 200）。 |
| 复现注意 | 本文是综述，无方法可复现，不应作为代码交付项。若任务书需要可运行实现，应改引具体方法论文（如 Ames 等的 CBF-QP / 安全滤波器工作）；评测该综述只需引用，无复现阻塞点。 |

---

### 8. g2o（**库，非论文**）
| 项 | 内容 |
| :--- | :--- |
| 论文 | 库（非论文）：g2o: A General Framework for Graph Optimization（其原始论文为 IROS 2011，本次仅审计库） |
| DOI / venue | https://github.com/RainerKuemmerle/g2o · 库（无 DOI） |
| 官方代码 | https://github.com/RainerKuemmerle/g2o |
| 证据 | 任务书给出的 URL 即官方仓库（作者 Rainer Kümmerle 账号下的项目主页），HTTP 200，3.5k stars，非 fork（`fork: false`）。 |
| 仓库状态 | HTTP 200 · 许可：**BSD License**，但为混合许可 —— README “License” 节原文 “g2o is licensed under the BSD License. However, some libraries are available under different license terms.”：`csparse_extension` 为 LGPL v2.1+，`g2o_viewer`、`g2o_incremental`、`slam2d_g2o` 为 GPL3+；根目录无 `LICENSE` 文件（故 GitHub API 未能识别为 BSD）· 与论文对应 N/A（库） |
| 第三方实现 | 无（Ubuntu/Debian 的 `g2o` 包是下游打包，非替代实现） |
| 复现注意 | 库许可混杂：链接 `g2o_viewer` 等 GPL3+ 组件会影响闭源分发；README 另警告若链接 Ubuntu/Debian 自带 CHOLMOD，可能因其 GPL 特性而受 GPL 约束（建议自行重编 CHOLMOD）。活跃维护：最近提交 **2026-09-26**（master）。 |

---

### 9. GTSAM（**库，非论文**）
| 项 | 内容 |
| :--- | :--- |
| 论文 | 库（非论文）：GTSAM — Georgia Tech Smoothing and Mapping library |
| DOI / venue | https://github.com/borglab/gtsam · 库（无 DOI；官方站点 https://gtsam.org ，HTTP 200） |
| 官方代码 | https://github.com/borglab/gtsam |
| 证据 | 官方仓库归属 `borglab`（作者 Frank Dellaert 的 Borglab @ Georgia Tech），README/description 与官网 https://gtsam.org 、文档站 https://borglab.github.io/gtsam/ （HTTP 200）一致；任务书未给 URL，此为经官方站点确认的官方地址。 |
| 仓库状态 | HTTP 200 · 许可：**Simplified BSD**（`LICENSE` 原文 “GTSAM is released under the simplified BSD license, reproduced in the file LICENSE.BSD in this directory.”，`LICENSE.BSD` 版权方 Georgia Tech Research Corporation；GitHub 归类为 “Other”）· 与论文对应 N/A（库） |
| 第三方实现 | 无（库本身；其 `GncOptimizer` 是 GNC 论文作者贡献的官方实现，见 Item 4） |
| 复现注意 | 整体非单一许可：内含第三方组件各有其许可（CCOLAMD 为 BSD-3、Eigen 3.4 为 MPL2 等），法律审查需逐个看；活跃维护，最近提交 **2026-10-02**（develop）；对 SLAM 复现很关键——Kimera-Multi 等要求特定 CMake 选项编译 GTSAM。 |

---

### 10. Ceres Solver（**库，非论文**）
| 项 | 内容 |
| :--- | :--- |
| 论文 | 库（非论文）：Ceres Solver — A large scale non-linear optimization library |
| DOI / venue | https://github.com/ceres-solver/ceres-solver · 库（无 DOI；官网 http://ceres-solver.org/ ，HTTP 200） |
| 官方代码 | https://github.com/ceres-solver/ceres-solver |
| 证据 | 官方仓库 `ceres-solver/ceres-solver`（组织即项目名，非 fork），repo 的 homepage 字段指向 http://ceres-solver.org/ ；官网许可页 http://ceres-solver.org/license.html 原文 “New BSD license, whose terms are as follows.”（HTTP 200）。 |
| 仓库状态 | HTTP 200 · 许可：**New BSD license（BSD-3-Clause）**（官网 license 页；GitHub 归类为 “Other”）· 与论文对应 N/A（库） |
| 第三方实现 | 无（库本身；Android/AOSP 等下游镜像非替代实现） |
| 复现注意 | 库依赖（Eigen、glog、gflags、SuiteSparse 等）在不同发行版上版本差异大，容易成为 SLAM 复现的构建阻塞点；活跃维护：最近提交 **2026-10-01**（master）。 |

---

## 汇总

| # | 名称 | 官方代码 | 最大注意点 |
| :--- | :--- | :--- | :--- |
| 1 | Kimera-Multi (T-RO 2022) | https://github.com/MIT-SPARK/Kimera-Multi | index repo 无 LICENSE，需 `vcs import` 拉子仓库；文档已从 Melodic 漂到 Noetic |
| 2 | D²SLAM (T-RO 2024) | https://github.com/HKUST-Aerial-Robotics/D2SLAM | 无 LICENSE；需 CUDA/TensorRT + Dropbox 模型；检索首个命中的是 fork |
| 3 | Swarm-SLAM (RA-L 2024) | https://github.com/MISTLab/Swarm-SLAM | MIT；子包挂在个人账号下，需 `cslam.repos` |
| 4 | GNC (RA-L 2020) | https://github.com/MIT-SPARK/GNC-and-ADAPT | 仅 MATLAB 且 2021 年后停更；实用版在 GTSAM `GncOptimizer` |
| 5 | ActLoc (CoRL 2025) | https://github.com/cvg/ActLoc | 2025-09 才首发、无 LICENSE、README 仍标 WIP |
| 6 | Active Neural Topological Mapping (RA-L) | https://github.com/yang-xy20/mantm | 年份应为 **2024**（2023 只是 online 日期）；README 用旧题；torch 1.5.1 |
| 7 | CBF: Theory and Applications (ECC 2019) | **NONE**（综述，作者未发布代码） | 无可复现代码，属正常；IEEE 页 202 不可达 |
| 8 | g2o（库） | https://github.com/RainerKuemmerle/g2o | 混合许可（部分 GPL3+）；最近提交 2026-09-26 |
| 9 | GTSAM（库） | https://github.com/borglab/gtsam | Simplified BSD 但内含多许可第三方组件；最近提交 2026-10-02 |
| 10 | Ceres Solver（库） | https://github.com/ceres-solver/ceres-solver | New BSD；依赖版本差异是主要复现阻塞；最近提交 2026-10-01 |
