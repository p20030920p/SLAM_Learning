# Group 4 核查报告：标定 / 连续时间（Calibration & Continuous-Time）

- 核查日期：2026-10-05（Asia/Shanghai）
- 范围：5 篇论文 + 1 个库（Kalibr）
- 方法：本地 PDF（`pdftotext -layout`）→ 论文正式版 / arXiv 预印本 → 仓库 README / LICENSE / 提交历史（GitHub API + `git clone --bare --filter=blob:none` + HTML）→ Crossref / OpenAlex 核对 DOI、标题、作者 → 逐个 URL `curl` 取 HTTP 状态码。
- 访问限制（如实记录）：
  - IEEE Xplore 对脚本访问返回 **HTTP 418 / 202（反爬质询页）**，因此 `ieeexplore.ieee.org/document/*` 等论文页无法直接读取正文；这不是死链。Paper 1 的正式排版全文通过 IEEE 开放获取 staging PDF 获取（9 页，与 Xplore 正式版一致）。
  - GitHub REST API 无 token（60 次/小时）在核查中途耗尽，关键结果均在此之前取得；后续改用 `raw.githubusercontent.com`、裸克隆与 HTML 页面补齐，未使用任何未验证数据。
- 结论速览：6 项中 **5 项有作者官方仓库**（其中 Paper 2 是"集成在 VINS-Mono 中"的间接官方代码），**Paper 1 官方代码为 `NONE`**。

---

### 1. Online LiDAR-Camera Extrinsic Calibration Using Selected Semantic Features

| 项 | 内容 |
| :--- | :--- |
| 论文 | Online LiDAR-Camera Extrinsic Calibration Using Selected Semantic Features（Ping-Tzu Lin, Ying-Shiuan Huang, Wen-Chieh Lin, Chieh-Chih Wang, Huei-Yung Lin） |
| DOI / venue | 10.1109/OJITS.2025.3555574 · IEEE Open Journal of Intelligent Transportation Systems (OJ-ITS), vol. 6, pp. 456–464, 2025 |
| 官方代码 | **无** |
| 证据 | 逐页检索作者提供的 IEEE 正式排版全文（9 页，开放获取）：无任何 `github` / `gitlab` / "code available" / "open source" 字样；正文唯一相关句为 "This article has supplementary downloadable material available at https://doi.org/10.1109/OJITS.2025.3555574, provided by the authors."（补充材料托管在 IEEE，需登录，本次无法确认其中是否含代码）。作者机构页（NYCU Academic Hub）"Other files and links" 只列 Scopus，无代码链接。GitHub 上以论文标题、第一作者姓名（Ping-Tzu Lin / PingTzuLin 等变体）检索均无对应仓库；以 "Selected Semantic Features" 精确检索仓库数为 0。 |
| 仓库状态 | 不适用（无仓库）。论文 DOI 页 `curl` 返回 HTTP 202（IEEE 反爬质询，非死链）· 论文许可 CC BY-NC-ND 4.0 · 与论文对应 不适用 |
| 第三方实现 | 无（未检索到任何声称复现本论文的第三方仓库） |
| 复现注意 | 本项是本组最大的复现缺口：**零公开代码**。且方法本身依赖两个第三方预训练模型——相机图像语义分割用 Zhu et al. [33]（SDC-Net [34] 架构），点云语义分割用 **Cylinder3D [37]**（SemanticKITTI 28 类预训练权重）；语义类别需人工选取（KAIST 用 road/traffic sign，KITTI 用 road marking），且 "In the current implementation, semantic classes for feature extraction are manually selected"。因此即使从零实现，也需自行搭起"两路语义分割 + 轮廓 Canny 边缘匹配 + 特征筛选 + SE(3) 边缘对齐优化"的完整链路，并以 KAIST Urban [17] / KITTI [18] 的位姿真值做重复性实验。论文未发布数据集、配置或评测脚本。 |

---

### 2. Online Temporal Calibration for Monocular Visual-Inertial Systems

| 项 | 内容 |
| :--- | :--- |
| 论文 | Online Temporal Calibration for Monocular Visual-Inertial Systems（Tong Qin, Shaojie Shen；IROS 2018 **Best Student Paper Award**） |
| DOI / venue | 10.1109/IROS.2018.8593603 · IEEE/RSJ IROS 2018 |
| 官方代码 | **https://github.com/HKUST-Aerial-Robotics/VINS-Mono** （作者未发布本论文的独立仓库；代码以集成形式存在于 VINS-Mono 中） |
| 证据 | ①**论文自身**（arXiv:1808.00692 全文）摘要末尾与脚注 1 明确写："The source code of temporal calibration is integrated into our public project, VINS-Mono. 1 https://github.com/HKUST-Aerial-Robotics/VINS-Mono"；贡献列表第三条亦为 "Open-source code integrated into the public project."。②**仓库侧**：VINS-Mono README 第 37 行的论文列表第一项即本论文（注明 best student paper award，链接 `ieeexplore.ieee.org/abstract/document/8593603`），第 6 行 News 写 "29 Dec 2017: New features: Add ... online temporal calibration function"，README §5.4 "Temporal calibration" 说明设 `estimate_td=1` 在线估计时延。③**代码侧**（在线抓取源文件确认）：`vins_estimator/src/parameters.cpp` 读取 `td` / `estimate_td`，`vins_estimator/src/estimator.cpp` 构造 `ProjectionTdFactor`（参数块 `para_Td`、`cur_td`、`velocity`）——这正是论文第 III-C 节的"带时偏的视觉因子"实现。④已枚举 HKUST-Aerial-Robotics 组织全部仓库（该组织公开仓库共 76 个），**不存在**以本论文命名的独立仓库。 |
| 仓库状态 | HTTP **200** · 许可 **GPL-3.0** · 与论文对应 **是（但非专属仓库：VINS-Mono 是完整 VIO 系统，本论文方法作为 `ProjectionTdFactor` 集成其中）** |
| 第三方实现 | 无针对本论文的第三方复现；另有独立实现（非本文作者发布、非本论文代码）：**OpenVINS** https://github.com/rpng/open_vins （HTTP 200）提供 `calib_camimu_dt` / `timeshift_cam_imu` 相机-IMU 时延在线标定，配置文件项见 `ov_msckf/src/core/VioManagerOptions.h`。 |
| 复现注意 | ①**论文与代码不是一对一关系**：IROS 2018 的论文是方法论文，官方"代码发布"就是 VINS-Mono 的 `estimate_td` 功能（2017-12-29 加入），没有任何以本论文标题命名的 repo，也没有论文专用分支、仿真脚本或 EuRoC 人工加时偏的评测脚本——论文中"与 Kalibr 对比、5 档曝光时间、±40ms 扫描"等实验无法用公开代码一键复现。②使用时需在配置文件设 `estimate_td: 1` 并给出 td 初值（`td:`，单位 s，语义为"图像时钟 + td = 真实图像时钟（IMU 时钟）"），并要求充分旋转/加速激励，否则时偏不可观测。③VINS-Mono 为 GPL-3.0（传染性），且仓库最近一次推送 2024-08-14，维护基本停止。 |

---

### 3. SR-LIVO

| 项 | 内容 |
| :--- | :--- |
| 论文 | SR-LIVO: LiDAR-Inertial-Visual Odometry and Mapping With Sweep Reconstruction（Zikang Yuan, Jie Deng, Ruiye Ming, Fengtian Lang, Xin Yang） |
| DOI / venue | 10.1109/LRA.2024.3389415 · IEEE Robotics and Automation Letters (RA-L), 2024 |
| 官方代码 | **https://github.com/ZikangYuan/sr_livo** |
| 证据 | ①**论文自身**：arXiv:2312.16800 预印本正文脚注 1 直接给出 `https://github.com/ZikangYuan/sr_livo`，并写明 "We have released the source code of ..."（正文两处提到已开源）。②仓库 README 的 "Related Work" 第一条即本论文（标题、作者列表与 Crossref 记录完全一致），仓库 Owner `ZikangYuan` 就是论文第一作者。③Crossref 核对：该 DOI 标题/作者与仓库描述 "A LiDAR-inertial-visual odometry and mapping system based on the sweep reconstruction method" 一致。 |
| 仓库状态 | HTTP **200** · 许可 **GPL-2.0** · 与论文对应 **是** |
| 第三方实现 | 官方之外存在衍生仓库：https://github.com/chengwei920412/sr_livo-laser_slam （HTTP 200），第三方把 SR-LIVO 代码适配到 `laser_slam` 框架的分支式衍生，**非官方发布**，不要当作官方代码引用。（上游依赖 R3LIVE 亦为第三方框架。） |
| 复现注意 | ①代码建立在 HKU-MARS 的 **R3LIVE** 框架之上（论文与 README 均自述），必须按 R3LIVE 的依赖链编译（ROS1 + Eigen + OpenCV + PCL 等）。②仓库只提供两组配置：`config/ntu.yaml`（Ouster）与 `config/r3live.yaml`（Livox），场景外推需要自行调参与相机-IMU-雷达标定。③仓库最近提交 2025-02-21，此后无更新；GPL-2.0 与上游 R3LIVE 的许可一致，商用需注意。 |

---

### 4. Traj-LO

| 项 | 内容 |
| :--- | :--- |
| 论文 | Traj-LO: In Defense of LiDAR-Only Odometry Using an Effective Continuous-Time Trajectory（Xin Zheng, Jianke Zhu） |
| DOI / venue | 10.1109/LRA.2024.3352360 · IEEE Robotics and Automation Letters (RA-L), vol. 9, no. 2, pp. 1961–1968, 2024 |
| 官方代码 | **https://github.com/kevin2431/Traj-LO** |
| 证据 | ①**arXiv 元数据（作者本人提交）**：arXiv:2309.13842 摘要页 comments 字段写明 "Video ... and **Project site https://github.com/kevin2431/Traj-LO**"。②仓库 README 的 BibTeX 与本论文完全一致（`author={Zheng, Xin and Zhu, Jianke}`，`doi={10.1109/LRA.2024.3352360}`）。③仓库 LICENSE 版权人 "Copyright (c) 2023 **Xin Zheng**" = 论文第一作者；README 中 "my latest work, Traj-LIO" 为第一人称作者口吻。 |
| 仓库状态 | HTTP **200** · 许可 **MIT** · 与论文对应 **是** |
| 第三方实现 | 无（未发现声称复现 Traj-LO 的第三方仓库；同作者的后续工作 Traj-LIO 属另一条工作线，不构成本论文的第三方实现） |
| 复现注意 | ①README 自述 "Traj-LO is currently in **beta version**"，并且 "Currently, the released code only supports **one LiDAR configuration**" —— 官方代码尚不支持多雷达，论文中的多 LiDAR 泛化结论无法直接复现。②ROS 集成"Still working on it"（只提供 ROSbag 数据加载器，非完整 ROS 节点）。③必须 `git clone --recursive`（依赖 Sophus/ImGui/GLM 等 third-party 子模块），另需 Eigen、oneTBB、Boost，Mac 上依赖 Homebrew 的 `install_deps.sh`。④作者在 M2 Mac（macOS 14.4.1）上测试；支持 NTU VIRAL / Hilti 2021–2023 / R3LIVE / Point-LIO / New College / SubT-MRS 数据集，但 README 明确要求 "you will need to fine-tune the parameters"。⑤纯 LiDAR 方法在长时间缺乏有效点的狭窄空间会失败（作者自述）。⑥仓库最近提交 2024-07-12。 |

---

### 5. DLIO (Direct LiDAR-Inertial Odometry)

| 项 | 内容 |
| :--- | :--- |
| 论文 | Direct LiDAR-Inertial Odometry: Lightweight LIO with Continuous-Time Motion Correction（Kenny Chen, Ryan Nemiroff, Brett T. Lopez） |
| DOI / venue | 10.1109/ICRA48891.2023.10160508 · IEEE ICRA 2023 |
| 官方代码 | **https://github.com/vectr-ucla/direct_lidar_inertial_odometry** |
| 证据 | ①仓库归属 **vectr-ucla** = 论文作者单位 "Verifiable and Control-Theoretic Robotics Laboratory, University of California Los Angeles"（论文首页脚注原文）。②README 标题与论文标题逐字一致，并给出 `[IEEE ICRA](https://ieeexplore.ieee.org/document/10160508)` 与 arXiv 2203.03749；README 的 BibTeX 为 `doi={10.1109/ICRA48891.2023.10160508}`，与本任务 DOI **精确匹配**。③LICENSE 版权人 = "Kenny J. Chen, Ryan Nemiroff, and Brett T. Lopez"，即论文三位作者；提交历史中最新提交由第一作者 **Kenny Chen** 署名。④Crossref 核对 Xplore 10160508 ↔ DOI 10.1109/ICRA48891.2023.10160508 ↔ 本论文标题一致。<br>**注意证据方向**：本地 `061_DLIO.pdf` 是 arXiv v4（2203.03749v4），其正文与 arXiv comments **都不含代码链接**（检索 "github/code available/open source" 仅命中参考文献中 evo 的链接）。因此本项的官方性证据来自仓库侧（README/README BibTeX/LICENSE/提交者），而非 PDF 侧。 |
| 仓库状态 | HTTP **200** · 许可 **MIT** · 与论文对应 **是** |
| 第三方实现 | 未发现论文之外的第三方复现。ROS 2 支持由社区 contributor 提交 PR #16 后**并入官方仓库**（`feature/ros2` 分支，HTTP 200），仍属官方；Livox `CustomMsg` 支持在官方 `feature/livox-support` 分支（HTTP 200）。 |
| 复现注意 | ①默认 `master` 是 **ROS 1 / Ubuntu 20.04 Noetic**；ROS 2 必须切 `feature/ros2` 分支，Livox 原生 `livox_ros_driver2::CustomMsg` 必须切 `feature/livox-support` 分支（master 只吃 `sensor_msgs::PointCloud2`，需 `xfer_format: 0`）。②README 明确："the LiDAR and IMU sensors *need* to be properly time-synchronized, otherwise DLIO will not work" —— 时间同步是硬前提。③`cfg/dlio.yaml` 必须填 LiDAR-IMU 外参（无精确值可用粗略值但精度下降）与 IMU 内参。④依赖 OpenMP / PCL ≥ 1.10 / Eigen ≥ 3.3.7 / C++14 / CMake ≥ 3.12.4，用 catkin_tools 构建。⑤master 最近提交 2024-11-08（仓库 `pushed_at` 2026-04-03，说明其他分支仍有推送），stars ≈ 1050。 |

---

### 6. Kalibr（库，非论文）

| 项 | 内容 |
| :--- | :--- |
| 论文 | 非论文，是 ETH Zurich ASL 的标定工具箱 "Kalibr — The Kalibr visual-inertial calibration toolbox"；其方法出处（README References）包括 Furgale, Rehder, Siegwart, "Unified Temporal and Spatial Calibration for Multi-Sensor Systems", IROS 2013 等 5 篇 |
| DOI / venue | 无 DOI；托管于 GitHub（task book 称其为"相机-IMU 标定的事实标准工具"——**属实**，见下） |
| 官方代码 | **https://github.com/ethz-asl/kalibr** |
| 证据 | 仓库真实存在且属 **ETH Zurich ASL 官方组织** `ethz-asl`：README 标题 "The Kalibr visual-inertial calibration toolbox"，作者列表含 Paul Furgale / Jérôme Maye / Jörn Rehder / Thomas Schneider（ETH ASL、Skybotix，与 LICENSE 版权人一致）；stars **5750**、forks **1612**（2026-10-05 查询），是社区事实标准；支持多相机、相机-IMU（时空联合）、IMU-IMU、卷帘相机四类标定；README 顶部挂 ROS1 Ubuntu 16.04/18.04/20.04 三个 CI badge；wiki 提供 Docker 与源码两种安装方式。 |
| 仓库状态 | HTTP **200** · 许可 **BSD**（README 明写 "License (BSD)"；LICENSE 文本是含 "All advertising materials ... must display the following acknowledgement" 的 4 条款式 BSD，因此 GitHub API 归类为 `NOASSERTION`/Other，而非标准 SPDX 标识）· 与论文对应 不适用（工具库） |
| 第三方实现 | 不适用（本项即官方仓库）。提示：社区存在大量 fork 与非官方 ROS 2 移植，本审计不背书任何第三方移植。 |
| 复现注意（含"是否活跃维护"的核实结论） | ①**维护状态：真实但已进入低维护/停滞，不能称为"活跃维护"**。以完整裸克隆统计：master 共 359 次提交；按年 2018=87、2021=50、2022=62、2023=**11**、2024=**7**、2025=**0**、2026=**0**；**master 最后提交 = 2024-03-08**（`1f60227`，merge PR #673 "Add an AprilTag option for svg"）；全部 17 个分支中最新的提交也就是这一条（其余分支止于 2023 或更早）；`git ls-remote --tags` 为空 —— **无任何 release / tag**，只能按 master 安装。距离核查日（2026-10-05）已约 2.5 年无提交。②**环境限 ROS 1**：Ubuntu 16.04/18.04/20.04 + ROS Kinetic/Melodic/Noetic，catkin_tools 构建；无官方 ROS 2 支持；2022-05 起才支持 Python 3，老教程/脚本里的 Python 2 写法是常见踩坑点。③官方 Docker 路径：`docker build -t kalibr -f Dockerfile_ros1_20_04 .`，容器内需 `source devel/setup.bash`，并挂载 `/data` 数据目录。④标定本身是**离线批优化**：需要标定靶（AprilTag/棋盘 yaml）、需要覆盖全部自由度的充分旋转与加速激励，结果对激励质量敏感；这正是 Paper 2（在线时偏标定）拿来对比的基线。 |

---

## 汇总表

| # | 名称 | 官方代码 | 仓库 HTTP | 许可 | 与论文对应 | 最大复现坑 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Online LiDAR-Camera Extrinsic Calibration (OJ-ITS 2025) | **无（NONE）** | — | 论文 CC BY-NC-ND 4.0 | 不适用 | 零公开代码；还需自备 Cylinder3D + 图像分割两套预训练模型 |
| 2 | Online Temporal Calibration (IROS 2018) | https://github.com/HKUST-Aerial-Robotics/VINS-Mono （集成，非专属仓库） | 200 | GPL-3.0 | 是（集成式） | 论文实验无独立代码/脚本；只能开 `estimate_td: 1` 用集成功能 |
| 3 | SR-LIVO (RA-L 2024) | https://github.com/ZikangYuan/sr_livo | 200 | GPL-2.0 | 是 | 依赖 R3LIVE 框架；仅 NTU/R3LIVE 两组配置 |
| 4 | Traj-LO (RA-L 2024) | https://github.com/kevin2431/Traj-LO | 200 | MIT | 是 | 官方代码 beta、只支持单一 LiDAR 配置，多雷达结论不可复现 |
| 5 | DLIO (ICRA 2023) | https://github.com/vectr-ucla/direct_lidar_inertial_odometry | 200 | MIT | 是 | 默认 ROS1；LiDAR-IMU 必须严格时间同步，否则不工作 |
| 6 | Kalibr（库） | https://github.com/ethz-asl/kalibr | 200 | BSD（4 条款式；GitHub 记 NOASSERTION） | 不适用 | 仅 ROS1、无 tag/release；master 停更于 2024-03-08（2025–2026 零提交） |

## 附录：本次实际 `curl` 的 URL 与状态码

| URL | HTTP |
| :--- | :--- |
| https://github.com/ZikangYuan/sr_livo | 200 |
| https://github.com/kevin2431/Traj-LO | 200 |
| https://github.com/vectr-ucla/direct_lidar_inertial_odometry | 200 |
| https://github.com/HKUST-Aerial-Robotics/VINS-Mono | 200 |
| https://github.com/ethz-asl/kalibr | 200 |
| https://github.com/chengwei920412/sr_livo-laser_slam （第三方衍生） | 200 |
| https://github.com/rpng/open_vins （第三方独立实现，非本论文代码） | 200 |
| https://github.com/vectr-ucla/direct_lidar_inertial_odometry/tree/feature/ros2 | 200 |
| https://github.com/vectr-ucla/direct_lidar_inertial_odometry/tree/feature/livox-support | 200 |
| https://ieeexplore.ieee.org/abstract/document/8593603 （Paper 2 论文页） | 200 |
| https://ieeexplore.ieee.org/document/10160508 · /10387726 · /10501952 · https://doi.org/10.1109/OJITS.2025.3555574 | 202（IEEE 反爬质询，非死链） |
| https://xplorestaging.ieee.org/ielx8/8784355/10847631/10944781.pdf （Paper 1 正式版开放获取全文，9 页，已用于证据检索） | 200 |

*本文件为唯一新增交付物；所有 URL 均实际抓取过，未报告任何未验证链接。*
