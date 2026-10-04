# 01-05 · DUFOMap — 论文报告值 Paper-reported baseline

| 项 Item | 内容 |
| :--- | :--- |
| 论文 | DUFOMap: Efficient Dynamic Awareness Mapping |
| Venue / 年 | **IEEE Robotics and Automation Letters (RA-L)**，预印本页眉标注 "PREPRINT VERSION. ACCEPTED MARCH 2024"（每页页眉，p.1–p.8）。PDF 未印 DOI（正文写 "Digital Object Identifier (DOI): see top of this page"，但页面上没有给出具体 DOI）。arXiv:2403.01449v2 [cs.RO]，2024-04-12 |
| 本地 PDF | `Localise/01_task_books/materials/papers_pdf/048_DUFOMap.pdf`（结果表在第 5–7 页：表 I、表 II 在第 5 页，表 III 在第 6 页，表 IV 在第 7 页；图 5 在第 6 页，图 6、图 7 在第 7 页） |
| 官方代码 | https://github.com/KTH-RPL/dufomap （p.2 给出）；项目页 https://kth-rpl.github.io/dufomap |
| 任务 | 基于 UFOMap 的**动态感知建图**：用光线投射找出"曾经被观测为空"的 void 区域，凡是落在 void 区域里的点即判为动态；同一套参数同时支持 offline 清理与 online 检测 |
| 数据集 | 定量（表 I）：**KITTI** seq **00**（small town）与 seq **01**（highway），HDL-64E，真值与位姿来自 SemanticKITTI [21]；**Argoverse 2 big city**（两个 VLP-32C）；**Semi-indoor**（16 线 LiDAR）。定性（p.6 §V-B）：**MCD VIRAL** [23]（Leica RTC360 扫描仪，1.3M 点/帧，垂直 FOV 300°，对比 64 线的 0.1M 点与 30°）、**DOALS**（128 线，火车站高动态）、**Livox Mid-360**（两层建筑）、以及项目页上的两个 **RGB-D** 小规模实验。作者声明共用到 **5 种不同传感器**（p.2 贡献点） |
| 指标 | **SA（Static Accuracy, %）**：静态点被正确标注的比例；**DA（Dynamic Accuracy, %）**：动态点被正确标注的比例；**AA = √(SA × DA)**。论文明确：指标取自 [10]（即 DynamicMap_Benchmark），**点级、不把 GT 降采样到体素级**；AA 用**几何平均**，对 SA 与 DA 都要好才高分。另有运行时间（s / point cloud，取总处理时间除以点云数） |
| 硬件 | 台式机 **Intel Core i9-12900KF**；另在机器人上的 **Intel NUC（Intel Core i7-8559U）** 做实时性测试（p.5 §IV-D） |

## 论文报告的数字 Reported numbers

标注约定：**DUFOMap (Ours) / DUFOMap⋆ (Ours) = 论文自己的方法**（⋆ 表示 online：每来一帧就查询、只用当时已有的信息）。其余行为论文复现的**基线方法**，且作者明确：Removert 与 ERASOR 使用 [10] 提供的**逐数据集调优过的参数**，DUFOMap 与 Dynablox 用**同一套参数跑所有实验**——即基线是"调过参"的，本文方法是"没调参"的。

### 表 I：点云地图动态点删除的定量对比（PDF p.5）。最优加粗、次优下划线，单位为百分比

| 出处（表/图 + 页） | 数据集 / 序列 | 方法 | 指标 | 数值 |
| :--- | :--- | :--- | :--- | ---: |
| 表 I, p.5 | KITTI small town (00) | Removert [8] | SA / DA / AA | 99.44 / 41.53 / 64.26 |
| 表 I, p.5 | KITTI small town (00) | ERASOR [9] | SA / DA / AA | 66.70 / 98.54 / 81.07 |
| 表 I, p.5 | KITTI small town (00) | OctoMap [16] | SA / DA / AA | 68.05 / 99.69 / 82.37 |
| 表 I, p.5 | KITTI small town (00) | Dynablox [17] | SA / DA / AA | 96.76 / 90.68 / 93.67 |
| 表 I, p.5 | KITTI small town (00) | **DUFOMap (Ours)** | SA / DA / AA | 97.96 / 98.72 / 98.34 |
| 表 I, p.5 | KITTI small town (00) | **DUFOMap⋆ (Ours, online)** | SA / DA / AA | 98.37 / 92.37 / 95.31 |
| 表 I, p.5 | KITTI highway (01) | Removert [8] | SA / DA / AA | 97.81 / 39.56 / 62.20 |
| 表 I, p.5 | KITTI highway (01) | ERASOR [9] | SA / DA / AA | 98.12 / 90.94 / 94.46 |
| 表 I, p.5 | KITTI highway (01) | OctoMap [16] | SA / DA / AA | 55.55 / 99.59 / 74.38 |
| 表 I, p.5 | KITTI highway (01) | Dynablox [17] | SA / DA / AA | 96.33 / 68.01 / 80.94 |
| 表 I, p.5 | KITTI highway (01) | **DUFOMap (Ours)** | SA / DA / AA | 98.09 / 94.20 / 96.12 |
| 表 I, p.5 | KITTI highway (01) | **DUFOMap⋆ (Ours, online)** | SA / DA / AA | 98.48 / 81.34 / 89.50 |
| 表 I, p.5 | Argoverse 2 big city | Removert [8] | SA / DA / AA | 98.97 / 31.16 / 55.53 |
| 表 I, p.5 | Argoverse 2 big city | ERASOR [9] | SA / DA / AA | 77.51 / 99.18 / 87.68 |
| 表 I, p.5 | Argoverse 2 big city | OctoMap [16] | SA / DA / AA | 69.04 / 97.50 / 82.04 |
| 表 I, p.5 | Argoverse 2 big city | Dynablox [17] | SA / DA / AA | 96.08 / 92.87 / 94.46 |
| 表 I, p.5 | Argoverse 2 big city | **DUFOMap (Ours)** | SA / DA / AA | 96.67 / 88.90 / 92.70 |
| 表 I, p.5 | Argoverse 2 big city | **DUFOMap⋆ (Ours, online)** | SA / DA / AA | 98.66 / 73.98 / 85.43 |
| 表 I, p.5 | Semi-indoor | Removert [8] | SA / DA / AA | 99.96 / 12.15 / 34.85 |
| 表 I, p.5 | Semi-indoor | ERASOR [9] | SA / DA / AA | 94.90 / 66.26 / 79.30 |
| 表 I, p.5 | Semi-indoor | OctoMap [16] | SA / DA / AA | 88.97 / 82.18 / 85.51 |
| 表 I, p.5 | Semi-indoor | Dynablox [17] | SA / DA / AA | 98.81 / 36.49 / 60.05 |
| 表 I, p.5 | Semi-indoor | **DUFOMap (Ours)** | SA / DA / AA | 99.64 / 83.00 / 90.94 |
| 表 I, p.5 | Semi-indoor | **DUFOMap⋆ (Ours, online)** | SA / DA / AA | 99.94 / 54.76 / 73.98 |

### 表 II：运行时间对比（PDF p.5）

| 出处（表/图 + 页） | 数据集 / 序列 | 方法 | 指标 | 数值 |
| :--- | :--- | :--- | :--- | ---: |
| 表 II, p.5 | KITTI highway | Removert [8] | Run time per point cloud [s] ↓ | 0.134 ± 0.004 |
| 表 II, p.5 | KITTI highway | ERASOR [9] | Run time per point cloud [s] ↓ | 0.718 ± 0.039 |
| 表 II, p.5 | KITTI highway | OctoMap [16] | Run time per point cloud [s] ↓ | 2.981 ± 0.952 |
| 表 II, p.5 | KITTI highway | Dynablox [17] | Run time per point cloud [s] ↓ | 0.141 ± 0.022 |
| 表 II, p.5 | KITTI highway | **DUFOMap (Ours)** | Run time per point cloud [s] ↓ | 0.062 ± 0.014 |
| 表 II, p.5 | Semi-indoor | Removert [8] | Run time per point cloud [s] ↓ | 0.515 ± 0.024 |
| 表 II, p.5 | Semi-indoor | ERASOR [9] | Run time per point cloud [s] ↓ | 0.064 ± 0.011 |
| 表 II, p.5 | Semi-indoor | OctoMap [16] | Run time per point cloud [s] ↓ | 1.048 ± 0.256 |
| 表 II, p.5 | Semi-indoor | Dynablox [17] | Run time per point cloud [s] ↓ | 0.046 ± 0.008 |
| 表 II, p.5 | Semi-indoor | **DUFOMap (Ours)** | Run time per point cloud [s] ↓ | 0.019 ± 0.003 |

### 表 III：位姿来源的影响（KITTI Sequence 00，PDF p.6）

| 出处（表/图 + 页） | 数据集 / 序列 | 方法 | 指标 | 数值 |
| :--- | :--- | :--- | :--- | ---: |
| 表 III, p.6 | KITTI 00，位姿 = KITTI GT poses [20] | Removert [8] | SA / DA / AA | 99.18 / 41.71 / 64.32 |
| 表 III, p.6 | KITTI 00，位姿 = KITTI GT poses | ERASOR [9] | SA / DA / AA | 63.83 / 98.35 / 79.23 |
| 表 III, p.6 | KITTI 00，位姿 = KITTI GT poses | Octomap [16] | SA / DA / AA | 54.81 / 99.56 / 73.87 |
| 表 III, p.6 | KITTI 00，位姿 = KITTI GT poses | Dynablox [17] | SA / DA / AA | 95.50 / 89.34 / 92.37 |
| 表 III, p.6 | KITTI 00，位姿 = KITTI GT poses | **DUFOMap (Ours)** | SA / DA / AA | 92.57 / 98.52 / 95.50 |
| 表 III, p.6 | KITTI 00，位姿 = SuMa [21],[25] | Removert [8] | SA / DA / AA | 99.44 / 41.53 / 64.26 |
| 表 III, p.6 | KITTI 00，位姿 = SuMa [21],[25] | ERASOR [9] | SA / DA / AA | 66.70 / 98.54 / 81.07 |
| 表 III, p.6 | KITTI 00，位姿 = SuMa [21],[25] | Octomap [16] | SA / DA / AA | 68.05 / 99.69 / 82.37 |
| 表 III, p.6 | KITTI 00，位姿 = SuMa [21],[25] | Dynablox [17] | SA / DA / AA | 96.76 / 90.68 / 93.67 |
| 表 III, p.6 | KITTI 00，位姿 = SuMa [21],[25] | **DUFOMap (Ours)** | SA / DA / AA | 97.96 / 98.72 / 98.34 |
| 表 III, p.6 | KITTI 00，位姿 = KISS-ICP [26] | Removert [8] | SA / DA / AA | 99.55 / 41.45 / 64.23 |
| 表 III, p.6 | KITTI 00，位姿 = KISS-ICP [26] | ERASOR [9] | SA / DA / AA | 67.86 / 98.68 / 81.83 |
| 表 III, p.6 | KITTI 00，位姿 = KISS-ICP [26] | Octomap [16] | SA / DA / AA | 62.28 / 99.85 / 78.85 |
| 表 III, p.6 | KITTI 00，位姿 = KISS-ICP [26] | Dynablox [17] | SA / DA / AA | 98.31 / 90.97 / 94.57 |
| 表 III, p.6 | KITTI 00，位姿 = KISS-ICP [26] | **DUFOMap (Ours)** | SA / DA / AA | 99.33 / 98.73 / 99.03 |

### 表 IV：消融（KITTI sequence 00，PDF p.7）。v = voxel size [m]

| 出处（表/图 + 页） | 数据集 / 序列 | 方法 | 指标 | 数值 |
| :--- | :--- | :--- | :--- | ---: |
| 表 IV, p.7 | KITTI 00，w/o d_s, d_p, v = 0.1 | **DUFOMap（消融）** | SA [%] / DA [%] / AA [%] | 14.89 / 99.99 / 38.58 |
| 表 IV, p.7 | KITTI 00，d_s = 0.2, v = 0.1 | **DUFOMap（消融）** | SA [%] / DA [%] / AA [%] | 30.29 / 99.99 / 55.03 |
| 表 IV, p.7 | KITTI 00，d_p = 1, v = 0.1 | **DUFOMap（消融）** | SA [%] / DA [%] / AA [%] | 91.89 / 98.97 / 95.37 |
| 表 IV, p.7 | KITTI 00，d_s = 0.2, d_p = 1, v = 0.2 | **DUFOMap（消融）** | SA [%] / DA [%] / AA [%] | 92.97 / 98.24 / 95.57 |
| 表 IV, p.7 | KITTI 00，d_s = 0.2, d_p = 1, v = 0.1（默认） | **DUFOMap（默认配置）** | SA [%] / DA [%] / AA [%] | 97.96 / 98.72 / 98.34 |

### 正文中的其他数字（非表格）

| 出处（表/图 + 页） | 数据集 / 序列 | 方法 | 指标 | 数值 |
| :--- | :--- | :--- | :--- | ---: |
| 正文 §IV-C, p.5 | Semi-indoor，量程缩到 20 m，Intel NUC 4 核 | **DUFOMap (Ours)** | 处理频率 | **20 Hz** |
| 正文 §IV-C, p.5 | 同上设置 | Dynablox [17] | 处理频率 | **< 10 Hz** |
| 正文 §V-A1, p.5 | 全部数据集 | Removert | DA 区间 | **20 – 40 %**（作者对表 I 的概括） |
| 正文 §IV-C, p.5 | KITTI | OctoMap | 单帧集成耗时 | 约 **3 s**（即表 II 的 2.981 s） |

## 关键结论（论文自己声称的）

- **在全部场景与传感器上拿到最高 AA**，SA 与 DA 都"最高或与最好者相当"：KITTI 00 的 AA = **98.34**（次优 Dynablox 93.67），KITTI 01 的 AA = **96.12**（次优 ERASOR 94.46），Semi-indoor 的 AA = **90.94**（次优 Octomap 85.51）（表 I, p.5）。
- **唯一例外是 Argoverse 2**：DUFOMap 的 AA = 92.70 只能排第二（Dynablox 94.46），作者归因于"长距离 + 稀疏"下保守的 void 判据导致 DA 偏低（88.90）（正文 p.5 §V-A1 与 p.8 §V-E Limitations）。
- **最快**：KITTI highway 0.062 s/帧（Octomap 2.981 s）、Semi-indoor 0.019 s/帧，均为表中最低；且在 Intel NUC 上 20 Hz，而 Dynablox < 10 Hz（表 II, p.5 + 正文 p.5）。
- **免调参**：所有实验共用 voxel size 0.1 m、d_s = 0.2 m、d_p = 1 三个参数，未按数据集调参；而 Removert 与 ERASOR 用的是逐数据集调优参数（p.5 §IV-C 参数设置）。
- **位姿误差会显著影响结果**：同一方法换位姿来源，AA 变化可达数个百分点（DUFOMap 95.50 → 98.34 → 99.03）；作者据此认为 KISS-ICP 在短序列上优于 KITTI GT 位姿与 SuMa（表 III, p.6）。
- **消融显示 d_p（定位误差建模）影响最大**：去掉 d_s、d_p 后 SA 崩到 14.89，AA 仅 38.58；只加 d_s 也只到 30.29/55.03；加 d_p 后回到 95.37（表 IV, p.7）。

## 对我们的复现意味着什么

- **可复现的前提**：
  - 代码开源：https://github.com/KTH-RPL/dufomap （C++17，非 ROS 依赖，正文 p.2 声明 open-source）。**论文未给具体 commit**，需自行锁定一个 commit 并记录。
  - **KITTI / SemanticKITTI 需注册下载**（论文用其标签与位姿）；**Argoverse 2 也需注册**。
  - 判据口径必须对齐：**点级** SA/DA，**AA = √(SA×DA)**，**不降采样 GT 到体素**。与 ERASOR 的 voxel-wise PR/RR(voxel 0.2) **不可混用**。
  - 默认参数必须照抄：voxel size **0.1 m**、d_s（sensor noise）**0.2 m**、d_p（subvoxel localization error）**1**。其他方法也用 **0.1 m** voxel。
  - 输入是"点云 + 位姿"对，位姿来源会改变结果（表 III 已量化），必须记录我们用的是哪一套位姿。
- **目标数字**：**KITTI sequence 00 上 DUFOMap（offline）的 SA / DA / AA = 97.96 / 98.72 / 98.34**（表 I, p.5）。选它的理由：① 是论文自己的方法；② 同一数据集同页有 4 个基线可交叉校验（Removert 99.44/41.53/64.26、ERASOR 66.70/98.54/81.07、OctoMap 68.05/99.69/82.37、Dynablox 96.76/90.68/93.67）；③ 消融表（表 IV, p.7）最后一行给了同一配置的同一组数，**内部自洽**，方便查错。
  次选目标（更能体现"免调参"卖点）：**Semi-indoor 上 DUFOMap = 99.64 / 83.00 / 90.94** 与 **0.019 ± 0.003 s/帧**。
- **对不上的可能原因**：
  - **数据集版本/帧段**：论文只写 "sequences 00 and 01"，**没有给出用的帧段范围**（对比：ERASOR++ 明确写了帧段）。作者说其他 KITTI 序列见项目页——即完整序列结果不在论文里。
  - **位姿来源**：GT pose / SuMa / KISS-ICP 三选一，AA 可差 ~3 个点（表 III）。
  - **GT 是否被降采样**：论文特意强调"without downsampling"；我们若用 benchmark 默认的 voxel-wise 评测会系统性偏移。
  - **参数**：基线的参数取自 [10]（DynamicMap_Benchmark）的逐数据集调优值，我们若用各方法作者默认参数，基线数字会不同。
  - **硬件**：Time 是 i9-12900KF 上的结果，与我们的机器不可直接比。
  - Argoverse 2 的 "big city" 具体用哪条序列、多少个 sensor 未写明。
- **阻塞风险**：
  - **KITTI / SemanticKITTI 必须注册下载**（硬阻塞，需先申请）；**Argoverse 2 同样需注册**——即表 I 的第 3 列整体不可复现，除非先拿到 AV2。
  - **数据体积大**：KITTI odometry raw + SemanticKITTI 为**数十 GB 量级**，AV2 Sensor 更大（论文未给 GB 数，属我们侧估计）。
  - **Semi-indoor 自采数据集**依赖作者发布（论文提到 extended datasets 与项目页）；若拿不到，表 I 第 4 列（含 DUFOMap 的 99.64/83.00/90.94）不可复现。
  - 论文**未给代码 commit / 版本号**，DUFOMap 仓库仍在演进，日后复跑可能与本文数字漂移。
