# 01-07 · DynoSAM — 论文报告值 Paper-reported baseline

| 项 Item | 内容 |
| :--- | :--- |
| 论文 | DynoSAM: Open-Source Smoothing and Mapping Framework for Dynamic SLAM |
| Venue / 年 | IEEE Transactions on Robotics (T-RO), 2025（**PDF 本身是 arXiv 预印本 arXiv:2501.11893v3, 2025-11-20，页眉页脚未印任何 venue**；T-RO 信息来自官方 repo 的 BibTeX："Accepted Transactions on Robotics (T-RO) Visual SLAM Special Issue, 2025"，DOI 10.1109/TRO.2025.3641813） |
| 本地 PDF | `Localise/01_task_books/materials/papers_pdf/002_DynoSAM.pdf`（结果表在第 13–16 页：Tab. I @p.13；Tab. II / III @p.14；Tab. IV / V / VI @p.15；Tab. VII @p.16） |
| 官方代码 | https://github.com/ACFR-RPG/DynOSAM （BSD License；ROS 2；论文 p.2 给出同一 URL） |
| 任务 | 动态 SLAM 的**因子图后端**框架（基于 GTSAM 4.2）：同时估计相机位姿、静态结构、物体运动/位姿与物体结构；提出 WCME（world-centric motion estimator）与 WCPE（world-centric pose estimator）两种 formulation，以及不依赖物体坐标系定义的 **ME（Motion Error）** 指标 |
| 数据集 | ① KITTI **tracking**（00, 01, 02, 03, 04, 05, 06, 18, 20）；② Outdoor Cluster（ClusterSLAM/CARLA，L1 / L2 / S1 / S2）；③ OMD 的 **S4U**（swinging 4 unconstrained，4 个自由摆动立方体）；④ TartanAir **Shibuya**（Standing Human、Road Crossing Easy、Road Crossing Hard 共 7 段）；⑤ **VIODE**（City Day Mid/High、City Night Mid/High、Parking Lot Mid/High） |
| 指标 | 论文原文定义：**ATE = RMSE(trans(M⁻¹_gt,k M_k))**；**RPE_k = (M⁻¹_gt,k−1 M_gt,k)⁻¹ (M⁻¹_k−1 M_k)**，即**相邻帧之间的相对位姿差**（不是 KITTI 那种按里程累积）——相机用 M = ᵂX_k，物体用 M = ᵂL_k；平移与旋转分量**分别**报 RMSE（rot 取角度）。**ME**（本文新提）= 在 **GT 物体坐标系**中评估的运动误差：ME_k = ᴸgt,k−1 H_gt,k⁻¹ ᴸgt,k−1 H_k，对物体坐标系定义不敏感。另报 runtime（Fig. 10，ms / s） |
| 硬件 | **未找到**。检索关键词 GPU / CPU / NVIDIA / RTX / Intel / GHz / workstation / hardware / implementation detail，PDF 全文**没有任何运行硬件说明**。论文只说明前端需要 **RGB + Depth(or Stereo) + dense optical flow + instance mask** 四路输入，并明示"currently RAFT [58] and YOLOv8 [60] are used to compute dense optical-flow and semantic instance segmentation respectively"（p.13, §V-A） |

> **读表须知**：`WCPE (ours)` / `WCME (ours)` 是本文方法（复现目标）。论文明确指出**两种 formulation 在相机位姿上结果几乎完全相同**（p.14："both proposed DynoSAM formulations demonstrate almost identical performance"），差异只出现在物体运动/位姿上。
> 对比方法的来源（p.13 §VI-A3 原文交代）：**VDO-SLAM 由作者在同一套预处理数据上重跑**；**MVO 的作者私下提供了 S4U 与 KITTI 00 的结果**；**ClusterSLAM 只报全 Outdoor Cluster 的累积平均，论文直接引用 Huang et al. 报的值**；**DynaSLAM II 无源码，只比相机位姿，物体位姿只与其论文自报值比**；**AIRDOS / ORB-SLAM3 / DynaVINS 的数字取自各自论文**。

## 论文报告的数字 Reported numbers

### Tab. I（p.13）—— 相机轨迹 ATE / RPE

列：KITTI `00  01  02  03  04  05  06  18  20` ｜ Outdoor Cluster `L1  L2  S1  S2  avg.` ｜ OMD `S4U`

| 出处（表/图 + 页） | 数据集 / 序列 | 方法 | 指标 | 数值 |
| :--- | :--- | :--- | :--- | ---: |
| 表 I, p.13 | KITTI 00 / 01 / 02 / 03 / 04 / 05 / 06 / 18 / 20 | DynaSLAM II | ATE (m) | 1.29 / 2.31 / 0.91 / 0.69 / 1.42 / 1.34 / 0.19 / 1.09 / 1.36 |
| 表 I, p.13 | KITTI 同上 9 条 | VDO-SLAM | ATE (m) | 3.37 / 6.74 / 2.47 / 2.12 / 4.53 / 3.80 / 0.45 / 9.94 / 7.82 |
| 表 I, p.13 | Outdoor Cluster（累积平均） | ClusterSLAM | ATE (m) | 0.53 |
| 表 I, p.13 | KITTI 00 / OMD S4U | MVO | ATE (m) | 1.53 / 0.05 |
| **表 I, p.13** | **KITTI 00 / 01 / 02 / 03 / 04 / 05 / 06 / 18 / 20** | **WCPE (ours)** | **ATE (m)** | **0.82 / 2.00 / 0.73 / 0.82 / 2.01 / 1.58 / 0.31 / 1.84 / 1.26** |
| **表 I, p.13** | **Outdoor Cluster L1 / L2 / S1 / S2 / avg.** | **WCPE (ours)** | **ATE (m)** | **0.61 / 0.52 / 0.09 / 0.13 / 0.34** |
| **表 I, p.13** | **OMD S4U** | **WCPE (ours)** | **ATE (m)** | **0.11** |
| **表 I, p.13** | **KITTI 00 / 01 / 02 / 03 / 04 / 05 / 06 / 18 / 20** | **WCME (ours)** | **ATE (m)** | **0.82 / 2.00 / 0.73 / 0.82 / 2.01 / 1.58 / 0.31 / 1.84 / 1.26**（与 WCPE 逐项相同） |
| **表 I, p.13** | **Outdoor Cluster L1 / L2 / S1 / S2 / avg.** | **WCME (ours)** | **ATE (m)** | **0.61 / 0.52 / 0.09 / 0.13 / 0.34** |
| **表 I, p.13** | **OMD S4U** | **WCME (ours)** | **ATE (m)** | **0.11** |
| 表 I, p.13 | KITTI 9 条 | DynaSLAM II | RPE_r (°) | 0.06 / 0.04 / 0.02 / 0.06 / 0.06 / 0.03 / 0.04 / 0.02 / 0.04 |
| 表 I, p.13 | KITTI 9 条 / OMD S4U | VDO-SLAM | RPE_r (°) | 0.08 / 0.05 / 0.03 / 0.03 / 0.06 / 0.03 / 0.10 / 0.03 / 0.04 ｜ 0.77 |
| 表 I, p.13 | Outdoor Cluster（累积平均） | ClusterSLAM | RPE_r (°) | 1.15 |
| 表 I, p.13 | KITTI 00 / OMD S4U | MVO | RPE_r (°) | 0.19 ｜ 0.76 |
| **表 I, p.13** | **KITTI 9 条** | **WCPE (ours)** | **RPE_r (°)** | **0.05 / 0.03 / 0.02 / 0.05 / 0.06 / 0.06 / 0.05 / 0.04 / 0.04** |
| **表 I, p.13** | **Cluster L1 / L2 / S1 / S2 / avg. ｜ OMD S4U** | **WCPE (ours)** | **RPE_r (°)** | **0.02 / 0.02 / 0.01 / 0.02 / 0.02 ｜ 0.69** |
| **表 I, p.13** | **KITTI 9 条** | **WCME (ours)** | **RPE_r (°)** | **0.04 / 0.03 / 0.02 / 0.05 / 0.06 / 0.05 / 0.05 / 0.04 / 0.04** |
| **表 I, p.13** | **Cluster L1 / L2 / S1 / S2 / avg. ｜ OMD S4U** | **WCME (ours)** | **RPE_r (°)** | **0.02 / 0.02 / 0.01 / 0.02 / 0.02 ｜ 0.69** |
| 表 I, p.13 | KITTI 9 条 | DynaSLAM II | RPE_t (m) | 0.04 / 0.05 / 0.04 / 0.04 / 0.07 / 0.06 / 0.02 / 0.05 / 0.07 |
| 表 I, p.13 | KITTI 9 条 / OMD S4U | VDO-SLAM | RPE_t (m) | 0.09 / 0.15 / 0.05 / 0.09 / 0.14 / 0.11 / 0.04 / 0.09 / 0.30 ｜ 0.12 |
| 表 I, p.13 | Outdoor Cluster（累积平均） | ClusterSLAM | RPE_t (m) | 1.10 |
| 表 I, p.13 | KITTI 00 / OMD S4U | MVO | RPE_t (m) | 0.07 ｜ 0.004 |
| **表 I, p.13** | **KITTI 9 条** | **WCPE (ours)** | **RPE_t (m)** | **0.04 / 0.04 / 0.03 / 0.05 / 0.07 / 0.05 / 0.01 / 0.04 / 0.04** |
| **表 I, p.13** | **Cluster L1 / L2 / S1 / S2 / avg. ｜ OMD S4U** | **WCPE (ours)** | **RPE_t (m)** | **0.04 / 0.02 / 0.01 / 0.02 / 0.02 ｜ 0.006** |
| **表 I, p.13** | **KITTI 9 条** | **WCME (ours)** | **RPE_t (m)** | **0.04 / 0.04 / 0.03 / 0.05 / 0.06 / 0.05 / 0.01 / 0.04 / 0.02** |
| **表 I, p.13** | **Cluster L1 / L2 / S1 / S2 / avg. ｜ OMD S4U** | **WCME (ours)** | **RPE_t (m)** | **0.04 / 0.01 / 0.01 / 0.02 / 0.02 ｜ 0.006** |

### Tab. II（p.14）—— TartanAir (Shibuya) 相机 ATE (m)

列：`I  II` = Standing Human；`III IV V` = Road Crossing (Easy)；`VI VII` = Road Crossing (Hard)

| 出处（表/图 + 页） | 数据集 / 序列 | 方法 | 指标 | 数值 |
| :--- | :--- | :--- | :--- | ---: |
| 表 II, p.14 | TartanAir Shibuya I–VII | AirDOS（with mask） | ATE (m) | 0.06 / 0.02 / 0.10 / 0.03 / 0.02 / 0.22 / 0.56 |
| 表 II, p.14 | TartanAir Shibuya I–VII | VDO-SLAM | ATE (m) | 0.10 / 0.61 / 0.38 / 0.39 / 0.22 / 0.24 / 0.66 |
| **表 II, p.14** | **TartanAir Shibuya I–VII** | **WCPE (ours)** | **ATE (m)** | **0.03 / 0.03 / 0.02 / 0.02 / 0.03 / 0.04 / 0.18** |
| **表 II, p.14** | **TartanAir Shibuya I–VII** | **WCME (ours)** | **ATE (m)** | **0.02 / 0.04 / 0.02 / 0.02 / 0.04 / 0.03 / 0.19** |

### Tab. III（p.14）—— VIODE 相机 ATE / RPE（DynoSAM 融合 IMU）

列：City Day Mid ｜ City Day High† ｜ City Night Mid ｜ City Night High† ｜ Parking Lot Mid† ｜ Parking Lot High†

| 出处（表/图 + 页） | 数据集 / 序列 | 方法 | 指标 | 数值 |
| :--- | :--- | :--- | :--- | ---: |
| 表 III, p.14 | VIODE 6 条 | DynaVINS | ATE (m) | 0.104 / 0.150 / 0.194 / 0.147 / 0.056 / 0.065 |
| 表 III, p.14 | VIODE 6 条 | ORB-SLAM3（IMU 模式） | ATE (m) | 0.217 / **\*** / 1.693 / 3.006 / **\*** / **\*** |
| 表 III, p.14 | VIODE 6 条 | WCPE (ours) | ATE (m) | 2.515 / 2.128 / 1.360 / 2.560 / 1.377 / 0.764 |
| 表 III, p.14 | VIODE 6 条 | WCME (ours) | ATE (m) | 2.515 / 2.128 / 1.360 / 2.560 / 1.377 / 0.764 |
| 表 III, p.14 | VIODE 6 条 | DynaVINS | RPE_r (°) | 0.024 / 0.027 / 0.019 / 0.023 / 0.019 / 0.015 |
| **表 III, p.14** | **VIODE 6 条** | **WCPE (ours)** | **RPE_r (°)** | **0.008 / 0.014 / 0.015 / 0.020 / 0.006 / 0.005** |
| **表 III, p.14** | **VIODE 6 条** | **WCME (ours)** | **RPE_r (°)** | **0.008 / 0.014 / 0.015 / 0.020 / 0.006 / 0.005** |
| 表 III, p.14 | VIODE 6 条 | DynaVINS | RPE_t (m) | 0.087 / 0.090 / 0.102 / 0.096 / 0.126 / 0.111 |
| **表 III, p.14** | **VIODE 6 条** | **WCPE (ours)** | **RPE_t (m)** | **0.049 / 0.105 / 0.070 / 0.190 / 0.036 / 0.040** |
| **表 III, p.14** | **VIODE 6 条** | **WCME (ours)** | **RPE_t (m)** | **0.049 / 0.105 / 0.070 / 0.190 / 0.036 / 0.040** |

表注：`†` 表示 DynoSAM **不融合 IMU 时会发散**的序列；`*` 表示 ORB-SLAM3 完全失败。论文正文说明 **DynoSAM 不融合 IMU 时在 VIODE 上全部发散**，故未列数值。

### Tab. IV（p.15）—— 物体运动 ME 与物体位姿 RPE

列：KITTI `00  01  02  03  04  05  06  18  20` ｜ Outdoor Cluster `L1  L2  S1  S2  avg.` ｜ OMD `S4U`

| 出处（表/图 + 页） | 数据集 / 序列 | 方法 | 指标 | 数值 |
| :--- | :--- | :--- | :--- | ---: |
| 表 IV, p.15 | KITTI 9 条 / OMD S4U | VDO-SLAM | ME_r (°) | 1.38 / 2.15 / 1.68 / 0.39 / 2.80 / 0.48 / 2.80 / 0.36 / 0.47 ｜ 0.96 |
| 表 IV, p.15 | KITTI 00 / OMD S4U | MVO | ME_r (°) | 3.36 ｜ 1.1 |
| 表 IV, p.15 | Outdoor Cluster / 全部 | ClusterSLAM | ME_r / ME_t | 未报（"-"；ClusterSLAM 不报 ME） |
| **表 IV, p.15** | **KITTI 9 条** | **WCPE (ours)** | **ME_r (°)** | **1.23 / 0.91 / 0.95 / 0.27 / 0.76 / 0.56 / 2.80 / 1.15 / 0.39** |
| **表 IV, p.15** | **Cluster L1 / L2 / S1 / S2 / avg. ｜ OMD S4U** | **WCPE (ours)** | **ME_r (°)** | **0.86 / 0.74 / 0.68 / 2.40 / 1.17 ｜ 1.6** |
| **表 IV, p.15** | **KITTI 9 条** | **WCME (ours)** | **ME_r (°)** | **1.29 / 0.86 / 1.06 / 0.26 / 1.01 / 0.49 / 0.39 / 0.60 / 0.33** |
| **表 IV, p.15** | **Cluster L1 / L2 / S1 / S2 / avg. ｜ OMD S4U** | **WCME (ours)** | **ME_r (°)** | **0.82 / 0.70 / 0.69 / 2.36 / 1.14 ｜ 0.71** |
| 表 IV, p.15 | KITTI 9 条 / OMD S4U | VDO-SLAM | ME_t (m) | 0.11 / 0.35 / 0.43 / 0.15 / 0.38 / 0.19 / 0.11 / 0.16 / 0.57 ｜ 0.02 |
| 表 IV, p.15 | KITTI 00 / OMD S4U | MVO | ME_t (m) | 0.27 ｜ 0.03 |
| **表 IV, p.15** | **KITTI 9 条** | **WCPE (ours)** | **ME_t (m)** | **0.09 / 0.40 / 0.73 / 0.15 / 0.10 / 0.14 / 0.22 / 0.31 / 0.39** |
| **表 IV, p.15** | **Cluster L1 / L2 / S1 / S2 / avg. ｜ OMD S4U** | **WCPE (ours)** | **ME_t (m)** | **0.07 / 0.08 / 0.03 / 0.13 / 0.08 ｜ 0.07** |
| **表 IV, p.15** | **KITTI 9 条** | **WCME (ours)** | **ME_t (m)** | **0.15 / 0.34 / 0.40 / 0.15 / 0.09 / 0.13 / 0.11 / 0.20 / 0.05** |
| **表 IV, p.15** | **Cluster L1 / L2 / S1 / S2 / avg. ｜ OMD S4U** | **WCME (ours)** | **ME_t (m)** | **0.08 / 0.06 / 0.04 / 0.15 / 0.08 ｜ 0.02** |
| 表 IV, p.15 | KITTI 9 条 / OMD S4U | VDO-SLAM | RPE_r (°) | 1.40 / 1.25 / 1.34 / 0.32 / 1.04 / 0.64 / 1.49 / 0.38 / 0.47 ｜ 3.3 |
| 表 IV, p.15 | Outdoor Cluster（累积平均） | ClusterSLAM | RPE_r (°) | 10.3 |
| 表 IV, p.15 | KITTI 00 / OMD S4U | MVO | RPE_r (°) | 2.7 ｜ 3.1 |
| **表 IV, p.15** | **KITTI 9 条** | **WCPE (ours)** | **RPE_r (°)** | **1.27 / 0.89 / 1.02 / 0.27 / 0.74 / 0.60 / 3.00 / 1.38 / 0.37** |
| **表 IV, p.15** | **Cluster L1 / L2 / S1 / S2 / avg. ｜ OMD S4U** | **WCPE (ours)** | **RPE_r (°)** | **1.7 / 2.34 / 0.61 / 2.07 / 1.68 ｜ 4.1** |
| **表 IV, p.15** | **KITTI 9 条** | **WCME (ours)** | **RPE_r (°)** | **1.38 / 0.80 / 1.06 / 0.27 / 1.04 / 0.62 / 2.74 / 1.16 / 0.33** |
| **表 IV, p.15** | **Cluster L1 / L2 / S1 / S2 / avg. ｜ OMD S4U** | **WCME (ours)** | **RPE_r (°)** | **1.3 / 2.28 / 0.67 / 2.00 / 1.56 ｜ 3.2** |
| 表 IV, p.15 | KITTI 9 条 / OMD S4U | VDO-SLAM | RPE_t (m) | 0.28 / 0.34 / 0.30 / 0.20 / 0.94 / 0.17 / 0.46 / 0.13 / 0.09 ｜ 0.06 |
| 表 IV, p.15 | Outdoor Cluster（累积平均） | ClusterSLAM | RPE_t (m) | 8.65 |
| 表 IV, p.15 | KITTI 00 / OMD S4U | MVO | RPE_t (m) | 0.28 ｜ 0.05 |
| **表 IV, p.15** | **KITTI 9 条** | **WCPE (ours)** | **RPE_t (m)** | **0.43 / 1.18 / 2.00 / 0.67 / 1.28 / 2.60 / 1.84 / 2.17 / 0.09** |
| **表 IV, p.15** | **Cluster L1 / L2 / S1 / S2 / avg. ｜ OMD S4U** | **WCPE (ours)** | **RPE_t (m)** | **1.84 / 0.74 / 0.99 / 1.63 / 1.33 ｜ 0.06** |
| **表 IV, p.15** | **KITTI 9 条** | **WCME (ours)** | **RPE_t (m)** | **0.27 / 0.32 / 0.79 / 0.19 / 0.92 / 0.16 / 0.48 / 0.20 / 0.12** |
| **表 IV, p.15** | **Cluster L1 / L2 / S1 / S2 / avg. ｜ OMD S4U** | **WCME (ours)** | **RPE_t (m)** | **1.9 / 0.72 / 0.94 / 1.50 / 1.27 ｜ 0.04** |

### Tab. V（p.15）—— DynoSAM 相对 SOTA 的平均提升百分比（绿=提升，红=略差）

| 出处（表/图 + 页） | 数据集 / 序列 | 方法 | 指标 | 数值 |
| :--- | :--- | :--- | :--- | ---: |
| 表 V, p.15 | 全部 | DynoSAM vs **VDO-SLAM** | ME_r / ME_t / RPE_r / RPE_t | +28% / +9% / **−9%（变差）** / +4% |
| 表 V, p.15 | 全部 | DynoSAM vs **ClusterSLAM** | RPE_r / RPE_t | +660% / +681% |
| 表 V, p.15 | 全部 | DynoSAM vs **MVO** | ME_r / ME_t / RPE_r / RPE_t | +49% / +39% / **−9%（变差）** / +12% |

### Tab. VI（p.15）—— OMD (S4U) 逐物体结果（用 WCME）

物体编号：1 = top left，2 = top right，3 = bottom left，4 = bottom right

| 出处（表/图 + 页） | 数据集 / 序列 | 方法 | 指标 | 数值（obj 1 / 2 / 3 / 4） |
| :--- | :--- | :--- | :--- | ---: |
| 表 VI, p.15 | OMD S4U | VDO-SLAM | ME_r (°) | 1.256 / 0.770 / 0.907 / 0.927 |
| 表 VI, p.15 | OMD S4U | MVO | ME_r (°) | 0.542 / 0.843 / 1.648 / 0.854 |
| **表 VI, p.15** | **OMD S4U** | **DynoSAM (ours, WCME)** | **ME_r (°)** | **1.138 / 0.544 / 0.443 / 0.474** |
| 表 VI, p.15 | OMD S4U | VDO-SLAM | ME_t (m) | 0.0243 / 0.0234 / 0.0148 / 0.0293 |
| 表 VI, p.15 | OMD S4U | MVO | ME_t (m) | 0.0169 / 0.0269 / 0.0232 / 0.0309 |
| **表 VI, p.15** | **OMD S4U** | **DynoSAM (ours, WCME)** | **ME_t (m)** | **0.0214 / 0.0233 / 0.0086 / 0.0291** |
| 表 VI, p.15 | OMD S4U | DynaSLAM II | ATE (m) | 0.41 / 0.37 / 1.09 / 0.28 |
| **表 VI, p.15** | **OMD S4U** | **DynoSAM (ours)** | **ATE (m)** | **0.09 / 0.21 / 0.08 / 0.15** |

### Tab. VII（p.16）—— full-batch vs sliding window（平均物体 ME）

| 出处（表/图 + 页） | 数据集 / 序列 | 方法 | 指标 | 数值 |
| :--- | :--- | :--- | :--- | ---: |
| 表 VII, p.16 | KITTI 00 | Full-Batch | ME_r (°) / ME_t (m) | 1.11 / 0.072 |
| 表 VII, p.16 | KITTI 00 | Sliding Window | ME_r (°) / ME_t (m) | 1.039 / 0.065 |
| 表 VII, p.16 | OMD (S4U) | Full-Batch | ME_r (°) / ME_t (m) | 0.729 / 0.022 |
| 表 VII, p.16 | OMD (S4U) | Sliding Window | ME_r (°) / ME_t (m) | 0.659 / 0.021 |

### 仅在正文、无表格的数字

| 出处（表/图 + 页） | 数据集 / 序列 | 方法 | 指标 | 数值 |
| :--- | :--- | :--- | :--- | ---: |
| 正文 p.13 | KITTI（相机位姿） | DynoSAM vs DynaSLAM II | 物体位姿提升 | 旋转 **91%**、平移 **36%** |
| 正文 p.15 | 全部 | DynoSAM vs DynaSLAM II | 物体 ATE 平均提升 | **445%** |
| 正文 p.15 | OMD（ME 口径） | DynoSAM vs VDO-SLAM | 精度提升 | 旋转 **34%**、平移 **21%** |
| 正文 p.14 | 全部 | WCME vs WCPE | 平均差异 | 平移 **0.06 m**、旋转 **0.11°**；14 条序列中仅 3 条（KITTI 03、06、20）差异 > 1σ |
| 正文 p.14 | KITTI / TartanAir / VIODE | DynoSAM 相机位姿 | RPE 最大劣势 | 旋转 **0.02°**、平移 **0.02 m** |
| 正文 p.16（Fig. 10） | — | 前端 feature tracking | 耗时 | **< 50 ms** |
| 正文 p.16（Fig. 10） | — | 运动估计模块（相机位姿 + 全部物体运动） | 每帧平均耗时 | **100 ms** |
| 正文 p.16 | — | 物体运动精化（Object Motion Refinement） | 每物体耗时 | **约 250 ms** |
| 正文 p.16 | — | full-batch 优化 | 总耗时 | **80 s – 700 s**（随因子图规模） |
| 正文 p.16 | — | sliding window（窗口 20） | 平均优化耗时 | **约 16 s** |

## 关键结论（论文自己声称的）

- **相机位姿上达到或超过 SOTA，且两种 formulation 结果几乎相同**：Tab. I 中 WCPE 与 WCME 的 ATE / RPE_r / RPE_t **逐项完全相同**；论文称"In cases where we perform worse, the difference is marginal with the maximum error difference being 0.02° in rotation and 0.02 m in translation"（p.14）。
- **TartanAir Shibuya 上显著优于 VDO-SLAM，并多数优于 AirDOS**：Tab. II 中 WCME 的 ATE 为 0.02 / 0.04 / 0.02 / 0.02 / 0.04 / 0.03 / **0.19** m，对比 VDO-SLAM 的 0.10 / 0.61 / 0.38 / 0.39 / 0.22 / 0.24 / **0.66** m；论文原文："we perform better than VDO-SLAM in all cases and AirDOS in most sequences"（p.14）。
- **物体运动/位姿上优于 VDO-SLAM / MVO / ClusterSLAM，但在 KITTI 05/06/18 上不如 VDO-SLAM**：Tab. V 给出 ME_r +28%、ME_t +9%（vs VDO-SLAM），但对 ClusterSLAM 的 RPE 提升达 **+660% / +681%**（"upwards of 6 times more accurate"）。论文坦承："there remains some situations such as KITTI 05, 06 and 18 where VDO-SLAM performs better... the difference on KITTI 05 is marginal, 06 and 18 exhibit larger performance differences"（p.15）。
- **VIODE 上必须融合 IMU**：Tab. III 中 DynoSAM 的 RPE 全面优于 DynaVINS（如 RPE_t 0.049 vs 0.087），但 **ATE 明显更差**（2.515 vs 0.104 等），论文归因于"DynaVINS produces the best ATE, likely due to its comprehensive mechanism that rejects dynamic object features using IMU-informed pose priors... more robust during the transition phase of total occlusion"；且**不融合 IMU 时 DynoSAM 在所有 VIODE 序列上发散**（p.14）。
- **新指标 ME 的动机**：物体 RPE 依赖物体坐标系定义，不同系统之间不可比；ME 通过把估计运动表达在 **GT 物体坐标系**中消除了这一歧义（p.12–13, §VI-B2）。
- **效率**：前端接近实时（feature tracking < 50 ms、运动估计 100 ms/帧），但 **full-batch 后端需 80–700 s**；换用窗口 20 的 sliding window 后约 **16 s**，且精度还略好（Tab. VII：KITTI 00 ME_t 0.065 vs 0.072）（p.16，§VI-F）。

## 对我们的复现意味着什么

- **可复现的前提**：
  - **GPU 是最大前提**。论文本身未写硬件，但官方 repo 明确：前端做 **CUDA 加速**、**TensorRT** 做目标检测与跟踪；YOLOv8 检测"accelerated using CUDA and TensorRT"（外部核实：<https://github.com/ACFR-RPG/DynOSAM>）。论文用的稠密光流是 **RAFT**（GPU 网络），而 repo 注明 **"For dense optical flow ... we use RAFT. Currently this pre-processing code is not available."** —— 即 **RAFT 预处理代码未公开**。
  - **关键的绕行路线（值得核实）**：官方把**预处理好的数据集**托管在 <https://data.acfr.usyd.edu.au/rpg/>，用 `wget -m -np -nH --cut-dirs=4 -R "index.html*" https://data.acfr.usyd.edu.au/rpg/dynosam/<Dataset>/<Subset>` 直接下载，**无需注册**。这些数据自带 **dense optical flow + 与 GT 对齐的 instance mask 跟踪标签**。repo 说明：`prefer_provided_optical_flow: true` 时直接用输入光流，`prefer_provided_object_detection` 相应设置后可直接用数据集里的 mask → **理论上存在一条不跑 RAFT/YOLOv8 的路径**，但 repo 未承诺可在纯 CPU 上运行，**标为待核实**（这是本机无 GPU 的唯一希望）。
  - 环境：**ROS 2**（README 徽章为 ROS2 Kilted）、Docker 镜像、**BSD License**、C++ + GTSAM 4.2（LM 求解）。论文实验除 §VI-E 外**全部使用 full-batch 优化**，且**未实现回环**。
  - 官方复现脚本：`dynosam_utils/src/run_experiments_tro.py`（repo 明确"Scripts for reproducing experiments: TRO 2025 experiments"，但同时警告"minor differences may arise due to ongoing development"）。
  - 数据集 ID：KITTI Tracking = 0；Virtual KITTI 2 = 1；Cluster-SLAM (CARLA) = 2；OMD = 3；TartanAir Shibuya = 5；VIODE = 6。
  - 数据许可 / 注册（已核实）：
    - **DynoSAM 官方预处理数据集：免费、免注册**（ACFR `data.acfr.usyd.edu.au`，直接 wget）。
    - **OMD 原站**：数据在 Google Drive，"**no sign-in required**"，licence **CC BY-SA 4.0**；但官网当前挂着公告 —— "**The Oxford Multimotion Dataset (OMD) is temporarily unavailable while it is moved to a new hosting service**"（<https://robotic-esp.com/datasets/omd/>）。→ **必须用 DynoSAM 托管的 "Modified 2024 version"**（dataset ID 3）。
    - **Outdoor Cluster / ClusterSLAM 数据集**：官方页面提供 Google Drive 直链，**免费**；licence **CC BY-NC-SA 4.0**（<https://huangjh-pub.github.io/page/clusterslam-dataset/>）。
    - **TartanAir**：**免费**，licence **CC BY 4.0**（<https://tartanair.org/>）。
    - **VIODE**：**免费**，托管在 Zenodo（record 4568610，<https://zenodo.org/records/4568610>）。
    - **KITTI tracking**：走 KITTI 官网，**需要注册**（同 KISS-ICP 那条的注册限制）；但用 ACFR 的预处理版可绕开。
- **目标数字**（建议按此顺序验收）：
  1. **OMD (S4U)：ATE = 0.11 m，ME_t = 0.02 m，ME_r = 0.71°（WCME）**（Tab. I + Tab. IV, p.13/15）——这是论文的主战场，且**数据集只有 1 条序列、免费可得**，最适合作为单一验收点。
  2. **KITTI 00：ATE = 0.82 m，RPE_r = 0.04°，RPE_t = 0.04 m**（Tab. I, p.13）。
  3. **TartanAir Shibuya VII：ATE = 0.18 m（WCPE）/ 0.19 m（WCME）**（Tab. II, p.14）。
  4. 若做在线化：**Tab. VII 的 sliding-window 数字（KITTI 00 ME_t 0.065、S4U ME_t 0.021）** 才是我们实际能跑出来的口径，full-batch 是离线结果。
- **对不上的可能原因**：
  - **WCME 与 WCPE 的差异极小但对少数序列超 1σ**（论文点出 KITTI 03、06、20）；必须明确说明我们复现的是哪一个 formulation，否则数字对不上会误判。
  - **后端模式不同**：论文默认 full-batch（一次优化全部测量），我们若用 sliding window 或 incremental，应比对 Tab. VII 而不是 Tab. I/IV。repo 的 `backend_updater_enum` 默认/推荐值已经变了（README 把 `PARALLEL_HYBRID` 标为 "Recommended for speed"，那是**另一篇 RA-L 2025 论文**的 formulation，**不是本文的 WCME/WCPE**）——这是极易踩的坑：要复现本文数字必须显式设 `backend_updater_enum = 0 (WCME)` 或 `1 (WCPE)`。
  - **ME 指标是论文自创的**：若我们用常见的"物体 RPE"去比 Tab. IV 的 ME 列，会系统性对不上（论文 §VI-B2 专门解释这个歧义）；Tab. IV 里 ME 与 RPE 是**两组不同的列**。
  - **对比方法的数字来源不齐**：VDO-SLAM 是作者重跑（可对齐），MVO 是作者私下提供，ClusterSLAM 与 DynaSLAM II 是引用原论文的累积平均 / 部分物体值 → **这些 baseline 我们不保证能复现**，验收应以 `ours` 列为准。
  - **VIODE 必须融合 IMU**，且论文未给不融合 IMU 的数值（只说发散）——不要试图在 VIODE 上做无 IMU 复现。
  - **前端 NN 版本敏感**：不同 YOLOv8 权重 / 不同 mask 会改变物体跟踪质量，进而改变 ME；论文自己也说 KITTI 06/18 的落后"merit further investigation"，与 object tracking 策略有关。
- **阻塞风险**：
  - **需要 GPU（CUDA + TensorRT）** —— 本机无 GPU，这是最高风险。可行的缓解路径是"使用官方预处理数据集（自带 flow + mask）+ 关闭在线检测"，但 repo 未声明支持纯 CPU 运行，**必须先做可行性验证再排期**。
  - **RAFT 预处理代码未公开** → 若官方预处理数据集缺少我们需要的那条序列，就**无法自行生成输入**（不能改用其他光流网络，否则与论文口径不一致）。
  - **OMD 原站暂时下线** → 依赖 ACFR 的 modified 2024 版本，需确认其与论文所用版本一致。
  - **full-batch 优化 80–700 s/序列**，加上前端约 100 ms/帧 + 250 ms/物体，KITTI 20 条序列的总机时会很长；且论文明确"the back-end is currently solved in a full-batch manner"，不适合作为在线系统验收。
  - KITTI tracking 原版需注册；ClusterSLAM / OMD 为 **NC（非商业）** 或 **SA** 条款，需确认项目用途合规。
