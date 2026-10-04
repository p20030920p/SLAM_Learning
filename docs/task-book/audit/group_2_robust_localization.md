# Group 2 · 鲁棒定位 / LiDAR(-Inertial-Visual) 里程计 — 官方代码仓库审计

审计日期：2026-10-05（Asia/Shanghai）
审计范围：7 篇论文的**官方**代码仓库（作者本人发布）。第三方复现单独列出，不计入官方代码。
所有报告的 URL 均在审计时用 `curl -s -o /dev/null -w '%{http_code}'` 实测；结论仅基于实际抓取到的页面/PDF 文本。

---

### X-ICP
| 项 | 内容 |
| :--- | :--- |
| 论文 | X-ICP: Localizability-Aware LiDAR Registration for Robust Localization in Extreme Environments |
| DOI / venue | 10.1109/TRO.2023.3335691 · IEEE Transactions on Robotics (T-RO) 2024, Vol. 40 |
| 官方代码 | **无** |
| 证据 | 本地 PDF `043_X_ICP.pdf` 全文检索：正文唯一的 GitHub 链接是脚注 3 的 `https://github.com/MichaelGrupp/evo`（第三方评测工具，非本文代码）；脚注 1 为视频 `https://youtu.be/SviLl7q69aA`，脚注 2 为项目页 `https://sites.google.com/leggedrobotics.com/x-icp`（实测 200）。项目页已抓取全文：仅有 PDF / "Additional Data (WIll be shared upon acceptance)" / Supplementary Video / Talk / 结果图与引用，**没有任何代码链接**。GitHub 仓库检索 `x-icp in:name` 无相关 SLAM 仓库；`https://github.com/leggedrobotics/x-icp`、`/X-ICP`、`/x-icp-localizability` 均返回 404。 |
| 仓库状态 | 无仓库（不适用）· 与论文对应 N/A |
| 第三方实现 | 无第三方复现。但存在**同作者（Tuna、Nubert 等 X-ICP 作者）后续论文**的官方仓库 `https://github.com/leggedrobotics/perfectlyconstrained`（HTTP 200 · MIT），其 README 明写 "including the degeneracy detection method of X-ICP"，即只包含 X-ICP 的**退化检测模块**、且嵌入在 open3d_slam/libpointmatcher 框架中，不是 X-ICP 系统本身，无法复现 X-ICP 论文数值。 |
| 复现注意 | 官方未发布任何 X-ICP 代码，需自行实现；依赖 ANYbotics 版 libpointmatcher 与 open3d_slam；实验平台为 ANYmal + VLP-16/OS0-128（Seemühle 洞穴等）；项目页承诺的 "Additional Data" 至今未提供链接。 |

---

### LOG-LIO
| 项 | 内容 |
| :--- | :--- |
| 论文 | LOG-LIO: A LiDAR-Inertial Odometry with Efficient Local Geometric Information Estimation |
| DOI / venue | 10.1109/LRA.2023.3332020 · IEEE Robotics and Automation Letters (RA-L) 2024, Vol. 9, No. 1, pp. 459–466 |
| 官方代码 | https://github.com/tiev-tongji/LOG-LIO |
| 证据 | 本地 PDF `045_LOG_LIO.pdf` 摘要直接给出："Our open source implementation is available at https://github.com/tiev-tongji/LOG-LIO"；贡献列表再次给出同一链接，并给出配套法向量估计工具 `https://github.com/tiev-tongji/RingFalsNormal`。仓库 README 的 BibTeX 引用（Huang, Zhao, Zhu, Ye, Feng, RA-L）与论文标题/作者一致。 |
| 仓库状态 | HTTP 200 · GPL-2.0（仓库根目录 `LICENSE` = GNU GPL v2）· 与论文对应 **是** |
| 第三方实现 | 未发现第三方复现。官方同组后续工作（非第三方）：`https://github.com/tiev-tongji/LOG-LIO2`（HTTP 200）。 |
| 复现注意 | 仅 ROS1 + `catkin_make`（Ubuntu ≥ 16.04，PCL/Eigen 用系统默认即可），无 ROS2 分支；**必须先用另一个仓库 `tiev-tongji/RingFalsNormal` 编译法向量估计器**，否则无法运行；官方只提供 M2DGR 与 NTU VIRAL 的 launch/yaml，换数据集需自行标定与写配置；README 特别提示 NTU VIRAL 时间戳为**帧结束时刻**；README 自称"更详细的说明即将补充"（文档较薄）。 |

---

### GenZ-ICP
| 项 | 内容 |
| :--- | :--- |
| 论文 | GenZ-ICP: Generalizable and Degeneracy-Robust LiDAR Odometry Using an Adaptive Weighting |
| DOI / venue | 10.1109/LRA.2024.3498779 · IEEE Robotics and Automation Letters (RA-L) 2025 |
| 官方代码 | https://github.com/cocel-postech/genz-icp |
| 证据 | 网络检索命中该仓库；抓取 README（master 分支）确认其徽章直接指向 `https://ieeexplore.ieee.org/document/10753079`，徽章文本为 `DOI-10.1109/LRA.2024.3498779`（与本题 DOI 完全一致），并链接 arXiv 2411.06766；arXiv 页面作者为 Daehan Lee、Hyungtae Lim、Soohee Han（POSTECH），与仓库所属组织 `cocel-postech`（POSTECH COCEL 实验室）一致。README 标题 "GenZ-ICP: SOTA robust LiDAR odometry (IEEE RA-L 2025)" 与论文对应。 |
| 仓库状态 | HTTP 200 · MIT（根目录 `LICENSE` = MIT License）· 与论文对应 **是** |
| 第三方实现 | `https://github.com/ali-pahlevani/GenZ_ICP_Optimized`（HTTP 200）— 第三方 CPU 优化版，**非官方**。 |
| 复现注意 | 仅提供 ICP/里程计前端（C++ 与 Python 两套实现 + ROS1/ROS2 封装），**不含建图/回环等完整 SLAM 后端**，复现论文精度需自建评测流水线；支持 `pip install genz-icp`（仓库 2026-05 仍在更新，命令行/API 可能已与 RA-L 投稿版有差异）；示例数据下载链接在 `ros/README.md`，需自行准备 KITTI 等点云序列。 |

---

### Switch-SLAM
| 项 | 内容 |
| :--- | :--- |
| 论文 | Switch-SLAM: Switching-Based LiDAR-Inertial-Visual SLAM for Degenerate Environments |
| DOI / venue | 10.1109/LRA.2024.3421792 · IEEE Robotics and Automation Letters (RA-L) 2024, Vol. 9, No. 8, pp. 7270–7277 |
| 官方代码 | **无** |
| 证据 | (1) 第一作者 Junwoon Lee 个人主页 `https://junwoonlee.github.io/`（HTTP 200）逐条列出该文，仅有 [paper] 与 [video]，**无 code 链接**；同页其它工作（如 LatentAM）明确给出 code 链接，说明作者有发布代码的习惯而本文没有。(2) 作者所属东京大学 i-Construction 讲座（Yamashita/Asama 组）论文页 `https://www.i-con.t.u-tokyo.ac.jp/publications/` 中该条目同样只有 [doi] 与 [Video]。(3) GitHub 仓库检索 `switch-slam`、`switchslam`、`switch+slam+lidar+visual` 均无对应仓库；猜测地址 `github.com/JunwoonLee/Switch-SLAM`、`/switch-slam`、`/SwitchSLAM`、`/RenKomatsu/Switch-SLAM` 等全部 404。 |
| 仓库状态 | 无仓库（不适用）· 与论文对应 N/A |
| 第三方实现 | 未发现任何第三方复现。 |
| 复现注意 | 无代码，需从零实现：视觉前端=VINS-Mono，激光前端=LOAM 系（scan-to-map + LM），后端=iSAM2 + Scan Context 回环；论文给出非启发式退化阈值 λ_t = [0.12, 0.27, 0.48]（卡方检验，95% 置信）。评测依赖模拟数据与第三方数据集（手持序列、DARPA SubT Cerberus、SubT-MRS），部分需申请/体量大。另：尝试下载东大机构库的学位论文 PDF（`https://repository.dl.itc.u-tokyo.ac.jp/record/2013872/files/K-09824-a.pdf`，可能含更多实现细节）**两次均在超时前未完成下载**（服务器响应极慢），此项未能核实。 |

---

### FAST-LIVO2
| 项 | 内容 |
| :--- | :--- |
| 论文 | FAST-LIVO2: Fast, Direct LiDAR-Inertial-Visual Odometry |
| DOI / venue | 10.1109/TRO.2024.3502198 · IEEE Transactions on Robotics (T-RO) 2025 |
| 官方代码 | https://github.com/hku-mars/FAST-LIVO2 |
| 证据 | 仓库 README（main 分支）News 明确写 "2025-01-23: Code released!"、"Accepted by T-RO '24"，并在 §1.2 链接论文 arXiv 2408.14035《FAST-LIVO2: Fast, Direct LiDAR-Inertial-Visual Odometry》；开发者 Chunran Zheng（HKU-MARS），与论文作者一致。 |
| 仓库状态 | HTTP 200 · GPL-2.0（根目录 `LICENSE` = GNU GPL v2，README §5 亦声明 GPLv2）· 与论文对应 **是** |
| 第三方实现 | 第三方 ROS2 移植：`https://github.com/davidakhihiero/FAST-LIVO2-ROS2`（200）、`https://github.com/v4rl-ucy/FAST-LIVO2-ROS2`（200）、`https://github.com/SuperLDG/FASTLIVO2_ROS2`（200）— 均非官方。 |
| 复现注意 | 官方仓库**只有 ROS1（catkin）**：Ubuntu 18.04–20.04、PCL ≥ 1.8、Eigen ≥ 3.3.4、OpenCV ≥ 4.2；Sophus 必须用**非模板化**版本（`git checkout a621ff` 后编译安装）；Vikit 必须用作者 fork `https://github.com/xuankuzcr/rpg_vikit`（**与 FAST-LIVO v1 所用的不同**）；数据集走 HKU OneDrive/SharePoint 链接（非 Git），硬件平台开源在 `LIV_handhold`。GPLv2，商用需联系作者。切勿与更早的纯 LiDAR-惯性工作 FAST-LIO2 混淆：后者仓库是 `https://github.com/hku-mars/FAST_LIO`（HTTP 200），而 `github.com/hku-mars/FAST-LIO2` 为 404。 |

---

### Active Illumination for Visual Ego-Motion Estimation in the Dark
| 项 | 内容 |
| :--- | :--- |
| 论文 | Active Illumination for Visual Ego-Motion Estimation in the Dark |
| DOI / venue | 10.1109/ICRA55743.2025.11127536 · IEEE ICRA 2025 |
| 官方代码 | **无** |
| 证据 | 论文全文（arXiv:2502.13708 v2，2025-09-08 修订，即 ICRA 版本）在 `arxiv.org/html/2502.13708v2` 与 ar5iv 镜像 `ar5iv.labs.arxiv.org/html/2502.13708` 两处全文抽取，**除引用第三方评测工具 `https://github.com/MichaelGrupp/evo` 外没有任何代码/仓库链接**，也无项目页。作者 GitHub 排查：`github.com/francescocrocetti`、`/albertodionigi`、`/AlbertoDionigi` 均 404；GitHub 用户检索 "crocetti"、"dionigi" 无匹配的机器人/视觉研究者账号；所属单位组织 `github.com/unipg` 显示 "This organization has no public repositories"。未能核实的页面（访问受限，非"无"的证据）：CatalyzeX 论文页与佩鲁贾大学 IRIS 机构库记录页均返回 **HTTP 403**（Cloudflare 拦截），无法确认其是否登记了代码链接。 |
| 仓库状态 | 无仓库（不适用）· 与论文对应 N/A |
| 第三方实现 | 未发现第三方复现。论文使用的第三方增强网络为 EnlightenGAN：`https://github.com/VITA-Group/EnlightenGAN`（HTTP 200），属依赖而非本文实现。 |
| 复现注意 | 无代码、无权重、无数据集：管线 = EnlightenGAN 增强网络 + 特征丰富度检测器 + pan-tilt 云台灯光控制，需要**物理云台光源**与自采的黑暗环境序列（论文未公开）；即使自建，也需自行训练/获取 EnlightenGAN 预训练权重，并自备 evo 做精度评测。 |

---

### R3LIVE
| 项 | 内容 |
| :--- | :--- |
| 论文 | R3LIVE: A Robust, Real-time, RGB-colored, LiDAR-Inertial-Visual tightly-coupled state Estimation and mapping package |
| DOI / venue | 10.1109/ICRA46639.2022.9811935 · IEEE ICRA 2022 |
| 官方代码 | https://github.com/hku-mars/r3live |
| 证据 | 仓库 README（master 分支）§1.1 "Our paper has been accepted to ICRA2022"，指向 `https://ieeexplore.ieee.org/document/9811935`（与本题 DOI 尾号一致）并在仓库内提供论文 PDF；作者 Jiarong Lin、Fu Zhang（HKU-MARS），README 明确 "we open source R3LIVE on our Github, including all of our codes, software utilities, and the mechanical design of our device"。 |
| 仓库状态 | HTTP 200 · GPL-2.0（根目录 `LICENCE` 文件 = GNU GPL v2；README §License 声明 "released under GPLv2 license. We only allow it free for personal and academic usage"）· 与论文对应 **是** |
| 第三方实现 | 未发现第三方复现。同作者的官方配套资源（非第三方）：数据集 `https://github.com/ziv-lin/r3live_dataset`（HTTP 200）、手持设备硬件设计仓库 `ziv-lin/rxlive_handheld`。 |
| 复现注意 | 仅 ROS1（catkin）；README 用大段警告 + issue #11/#20/#23 强调 **OpenCV 版本必须"编译时与运行时一致"**，版本不匹配会导致启动即崩溃，这是最常见的复现失败原因（要求 OpenCV ≥ 3.3，可选 CGAL/pcl_viewer）；评测数据为 9 个 rosbag，托管在 Google Drive / 百度网盘（非 Git，国内/海外各有一侧不便）；代码为 GPLv2 且附加"仅限个人与学术使用"条款，商用需单独授权；系统含光度法 VIO，实时性低于纯 LiDAR 方案。 |

---

## 汇总

| 论文 | 官方仓库 | HTTP |
| :--- | :--- | :--- |
| X-ICP | **无** | — |
| LOG-LIO | https://github.com/tiev-tongji/LOG-LIO | 200 |
| GenZ-ICP | https://github.com/cocel-postech/genz-icp | 200 |
| Switch-SLAM | **无** | — |
| FAST-LIVO2 | https://github.com/hku-mars/FAST-LIVO2 | 200 |
| Active Illumination (ICRA 2025) | **无** | — |
| R3LIVE | https://github.com/hku-mars/r3live | 200 |

未决/受限事项（诚实记录）：CatalyzeX 与佩鲁贾大学 IRIS 页面返回 403，无法排查；东大机构库学位论文 PDF 下载超时，未能核实；除上述外，未发现任何被报告的 URL 失效。
