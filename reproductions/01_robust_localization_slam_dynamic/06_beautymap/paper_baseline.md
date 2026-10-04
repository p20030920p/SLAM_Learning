# 01-06 · BeautyMap — 论文报告值 Paper-reported baseline

| 项 Item | 内容 |
| :--- | :--- |
| 论文 | BeautyMap: Binary-Encoded Adaptable Ground Matrix for Dynamic Points Removal in Global Maps |
| Venue / 年 | **IEEE Robotics and Automation Letters (RA-L)**，预印本页眉标注 "PREPRINT VERSION. ACCEPTED APRIL 2024"（每页页眉，p.1–p.8）。PDF 未印具体 DOI（写 "see top of this page" 但页面无 DOI）。arXiv:2405.07283v1 [cs.RO]，2024-05-12 |
| 本地 PDF | `Localise/01_task_books/materials/papers_pdf/047_BeautyMap.pdf`（结果表在第 6–7 页：表 I 在第 6 页；表 II、表 III、表 IV 在第 7 页；图 8 在第 6 页） |
| 官方代码 | https://github.com/MKJia/BeautyMap （p.1 与 p.2 均给出） |
| 任务 | 把全局地图与每一帧扫描都编码成**二值矩阵**（binary-encoded matrix），用位运算做矩阵比对找出潜在动态区域，再用"可适应地面"分层处理与静态点恢复模块，产出干净的全局地图 |
| 数据集 | **KITTI**（VLP-64），动态真值来自 **SemanticKITTI** [34]；沿用 [10][12] 的设置，取 **KITTI sequences 00、01、02、05** 中"动态最多"的**部分帧**（p.5 与 p.6 说明）。另有 **semi-indoor** 数据集（VLP-16，来自 [10]）。位姿：KITTI 用 **SuMa** [35]，semi-indoor 用 **simple-ndt** [36]。注意 **Table III 用的是 sequence 02**，而表 I 里没有 02 |
| 指标 | **SA（Static Accuracy）**、**DA（Dynamic Accuracy）**：**点级**，且**不把 GT 降采样**（"at the point level without downsampling the ground truth map"）。综合指标**不用** benchmark [10] 的 AA，而是**自创 HA（Harmonic Accuracy）= 2 × SA × DA / (SA + DA)**（p.5 公式，写在两栏之间）。另有 Runtime / point cloud [s] |
| 硬件 | 台式机 **Intel Core i9-12900KF**（p.5 末） |

## 论文报告的数字 Reported numbers

标注约定：**BeautyMap (Ours) = 论文自己的方法**；`†` = 数据驱动方法（论文标注）；其余为论文在公开基准 [10] 之上复现/引用的**基线方法**。
**重要口径差异**：本文把基准的 AA 换成了 **HA（调和平均）**，所以本表的 HA 列与 DUFOMap / DynamicMap_Benchmark 论文里的 AA 列**不能直接比较**——同一组 SA、DA 下调和平均 ≤ 几何平均。

### 表 I：动态点删除方法定量对比（PDF p.6）。最优加粗、次优下划线，单位为百分比

| 出处（表/图 + 页） | 数据集 / 序列 | 方法 | 指标 | 数值 |
| :--- | :--- | :--- | :--- | ---: |
| 表 I, p.6 | KITTI sequence 00 | 4DMOS† [23] | SA / DA / HA | - / - / -（论文标 "-"：训练集含 KITTI 0–10，故不报 KITTI） |
| 表 I, p.6 | KITTI sequence 00 | MapMOS† [16] | SA / DA / HA | - / - / -（同上） |
| 表 I, p.6 | KITTI sequence 00 | DeFlow† [17] | SA / DA / HA | 99.43 / 81.68 / 89.69 |
| 表 I, p.6 | KITTI sequence 00 | Removert [11] | SA / DA / HA | 99.44 / 41.53 / 58.59 |
| 表 I, p.6 | KITTI sequence 00 | ERASOR [12] | SA / DA / HA | 66.70 / 98.54 / 79.55 |
| 表 I, p.6 | KITTI sequence 00 | Octomap [7] | SA / DA / HA | 68.05 / 99.69 / 80.89 |
| 表 I, p.6 | KITTI sequence 00 | Octomap w GF [10] | SA / DA / HA | 93.06 / 98.67 / 95.78 |
| 表 I, p.6 | KITTI sequence 00 | dynablox [20] | SA / DA / HA | 96.76 / 90.68 / 93.62 |
| 表 I, p.6 | KITTI sequence 00 | **BeautyMap (Ours)** | SA / DA / HA | 96.76 / 98.38 / 97.56 |
| 表 I, p.6 | KITTI sequence 01 | 4DMOS† [23] / MapMOS† [16] | SA / DA / HA | - / - / -（同上，不报 KITTI） |
| 表 I, p.6 | KITTI sequence 01 | DeFlow† [17] | SA / DA / HA | 99.19 / 81.25 / 89.33 |
| 表 I, p.6 | KITTI sequence 01 | Removert [11] | SA / DA / HA | 97.81 / 39.56 / 56.33 |
| 表 I, p.6 | KITTI sequence 01 | ERASOR [12] | SA / DA / HA | 98.12 / 90.94 / 94.39 |
| 表 I, p.6 | KITTI sequence 01 | Octomap [7] | SA / DA / HA | 55.55 / 99.60 / 71.28 |
| 表 I, p.6 | KITTI sequence 01 | Octomap w GF [10] | SA / DA / HA | 80.64 / 97.27 / 88.18 |
| 表 I, p.6 | KITTI sequence 01 | dynablox [20] | SA / DA / HA | 96.33 / 68.01 / 79.73 |
| 表 I, p.6 | KITTI sequence 01 | **BeautyMap (Ours)** | SA / DA / HA | 99.17 / 92.99 / 95.98 |
| 表 I, p.6 | KITTI sequence 05 | DeFlow† [17] | SA / DA / HA | 99.48 / 50.85 / 67.30 |
| 表 I, p.6 | KITTI sequence 05 | Removert [11] | SA / DA / HA | 99.42 / 22.28 / 36.40 |
| 表 I, p.6 | KITTI sequence 05 | ERASOR [12] | SA / DA / HA | 69.40 / 99.06 / 81.62 |
| 表 I, p.6 | KITTI sequence 05 | Octomap [7] | SA / DA / HA | 66.28 / 99.24 / 79.48 |
| 表 I, p.6 | KITTI sequence 05 | Octomap w GF [10] | SA / DA / HA | 93.54 / 92.48 / 93.01 |
| 表 I, p.6 | KITTI sequence 05 | dynablox [20] | SA / DA / HA | 97.80 / 88.68 / 93.02 |
| 表 I, p.6 | KITTI sequence 05 | **BeautyMap (Ours)** | SA / DA / HA | 96.34 / 98.29 / 97.31 |
| 表 I, p.6 | Semi-indoor | 4DMOS† [23] | SA / DA / HA | 99.99 / 10.60 / 27.59 |
| 表 I, p.6 | Semi-indoor | MapMOS† [16] | SA / DA / HA | 99.99 / 4.75 / 9.07 |
| 表 I, p.6 | Semi-indoor | DeFlow† [17] | SA / DA / HA | 99.99 / 2.02 / 3.95 |
| 表 I, p.6 | Semi-indoor | Removert [11] | SA / DA / HA | 99.96 / 12.15 / 21.67 |
| 表 I, p.6 | Semi-indoor | ERASOR [12] | SA / DA / HA | 94.90 / 66.26 / 78.04 |
| 表 I, p.6 | Semi-indoor | Octomap [7] | SA / DA / HA | 88.97 / 82.18 / 85.44 |
| 表 I, p.6 | Semi-indoor | Octomap w GF [10] | SA / DA / HA | 96.79 / 73.50 / 83.55 |
| 表 I, p.6 | Semi-indoor | dynablox [20] | SA / DA / HA | 98.81 / 36.49 / 53.30 |
| 表 I, p.6 | Semi-indoor | **BeautyMap (Ours)** | SA / DA / HA | 93.69 / 90.67 / 92.16 |

### 表 II：运行时间对比（KITTI sequence 01，PDF p.7）

| 出处（表/图 + 页） | 数据集 / 序列 | 方法 | 指标 | 数值 |
| :--- | :--- | :--- | :--- | ---: |
| 表 II, p.7 | KITTI sequence 01 | Removert [11] | Runtime / point cloud [s] ↓ | 0.134 ± 0.004 |
| 表 II, p.7 | KITTI sequence 01 | ERASOR [12] | Runtime / point cloud [s] ↓ | 0.718 ± 0.039 |
| 表 II, p.7 | KITTI sequence 01 | Octomap [7] | Runtime / point cloud [s] ↓ | 2.981 ± 0.952 |
| 表 II, p.7 | KITTI sequence 01 | Octomap w GF [10] | Runtime / point cloud [s] ↓ | 2.147 ± 0.468 |
| 表 II, p.7 | KITTI sequence 01 | Dynablox [20] | Runtime / point cloud [s] ↓ | 0.141 ± 0.022 |
| 表 II, p.7 | KITTI sequence 01 | **BeautyMap (Python)（本文）** | Runtime / point cloud [s] ↓ | **0.046 ± 0.011** |

### 表 III：不同 cell size 的权衡（KITTI sequence 02，PDF p.7）

| 出处（表/图 + 页） | 数据集 / 序列 | 方法 | 指标 | 数值 |
| :--- | :--- | :--- | :--- | ---: |
| 表 III, p.7 | KITTI sequence 02，cell 0.5 m | **BeautyMap（本文）** | SA / DA / HA / Runtime per point cloud [s] | 83.92 / 84.14 / 84.03 / 0.132 ± 0.034 |
| 表 III, p.7 | KITTI sequence 02，cell 1.0 m | **BeautyMap（本文）** | SA / DA / HA / Runtime per point cloud [s] | 83.40 / 82.41 / 82.90 / 0.031 ± 0.039 |
| 表 III, p.7 | KITTI sequence 02，cell 2.0 m | **BeautyMap（本文）** | SA / DA / HA / Runtime per point cloud [s] | 74.92 / 88.83 / 81.28 / 0.018 ± 0.010 |

### 表 IV：功能模块消融（KITTI sequence 01，PDF p.7）

| 出处（表/图 + 页） | 数据集 / 序列 | 方法 | 指标 | 数值 |
| :--- | :--- | :--- | :--- | ---: |
| 表 IV, p.7 | KITTI 01，无 Ground module、无 Static restoration | **BeautyMap（消融）** | SA / DA / HA | 59.55 / 96.47 / 75.79 |
| 表 IV, p.7 | KITTI 01，仅 Ground module | **BeautyMap（消融）** | SA / DA / HA | 59.04 / 99.01 / 76.46 |
| 表 IV, p.7 | KITTI 01，仅 Static restoration | **BeautyMap（消融）** | SA / DA / HA | 99.38 / 77.81 / 87.94 |
| 表 IV, p.7 | KITTI 01，Ground module + Static restoration（完整） | **BeautyMap（完整）** | SA / DA / HA | 99.17 / 92.99 / 96.03 |

> ⚠️ 表 IV 最后一行（KITTI 01，完整模块）为 **HA = 96.03**，而表 I 中 KITTI 01 的 BeautyMap 为 **HA = 95.98**；SA/DA 两处完全一致（99.17 / 92.99）。这是**论文自身两处表格之间的 0.05 不一致**，复现时以表 I 为准还是表 IV 为准需要自行决定，验收容差应覆盖这一点。

## 关键结论（论文自己声称的）

- **在四个数据集上都优于所有对比方法**：作者原话 "outperforms all other methods in all four datasets in Table I"（p.6）；代表值——KITTI 00 HA **97.56**（次优 Octomap w GF 95.78）、KITTI 01 HA **95.98**、KITTI 05 HA **97.31**（次优 dynablox 93.02）、Semi-indoor HA **92.16**（次优 Octomap 85.44）（表 I, p.6）。
- **最快**：**0.046 ± 0.011 s/帧**（KITTI 01），比第二快的 Removert（0.134 s）快约 3 倍，比 Octomap（2.981 s）快约 65 倍；作者归因于二值编码矩阵结构（表 II, p.7 + 正文 p.7）。
- **静态恢复模块是保 SA 的关键**：只用矩阵比对时 SA = **59.55**，加上 static restoration 后 SA 提到 **99.38**（正文称"SA is higher around 40% than the other two and near 100%"）；地面模块主要提升 DA（96.47 → 99.01）（表 IV, p.7）。
- **cell size 是速度/精度的旋钮**：0.5 m 对 HA 提升有限但耗时增到 0.132 s；2.0 m 更快（0.018 s）但 SA 掉到 74.92、DA 升到 88.83；**1.0 m 是默认且综合最优**（表 III, p.7）。
- **数据驱动方法在 16 线稀疏 LiDAR 上失效**：semi-indoor 上 4DMOS / MapMOS / DeFlow 的 DA 仅 **10.60 / 4.75 / 2.02**，因为它们训练于 64 线（KITTI）与 32 线（AV2）；Removert 与 dynablox 同样差（12.15 / 36.49），原因是 range image 分辨率受限（正文 p.6）。
- **4DMOS 与 MapMOS 不在 KITTI 上报数**：其训练集包含 KITTI 序列 0–10，"No results are therefore presented for the KITTI sequences as these methods have seen ground truth data"（p.5——作者明说是因为**训练集泄漏**）。

## 对我们的复现意味着什么

- **可复现的前提**：
  - 代码开源：https://github.com/MKJia/BeautyMap （注意上游 links.md 记的 `KTH-RPL/BeautyMap` 是 404，**正确地址是 MKJia**）。实现语言为 **Python**（表 II 行名 "BeautyMap (Python)"）。
  - **KITTI 与 SemanticKITTI 需注册下载**（动态真值来自 SemanticKITTI）；**semi-indoor 数据集来自 [10]（DynamicMap_Benchmark 仓库）**。
  - 位姿：KITTI 用 **SuMa**、semi-indoor 用 **simple-ndt**——不是 KITTI 官方 GT pose，换位姿会改结果。
  - 默认参数：**cell size 1 × 1 m²（所有 KITTI 序列）**、**0.5 × 0.5 m²（semi-indoor）**。
  - 只取部分帧："selected partial frames from the KITTI sequences 00, 01, 02, and 05 which present the most dynamics" —— **论文没有给出帧号范围**。
  - 指标口径：**HA = 2·SA·DA/(SA+DA)**，与 benchmark 的 AA 不同，验收脚本必须实现 HA。
- **目标数字**：**KITTI sequence 01 上 BeautyMap 的 SA / DA / HA = 99.17 / 92.99 / 95.98**（表 I, p.6）。选它的理由：① 同一页有 6 个基线可比；② 表 II 的 runtime（0.046 s）与表 IV 的消融都在 sequence 01 上，**同一序列三张表可以互校**；③ 论文正文引用的三个"关键结论"数字（0.046 s、SA 99.38、HA 96%）都落在 sequence 01 上。
  验收容差建议 ±1 个百分点（HA），并把表 IV 的 96.03 vs 表 I 的 95.98 都视为合格区间。
- **对不上的可能原因**：
  - **帧段未公开**（最大不确定性）：论文只说"选了动态最多的部分帧"，没给帧号，与 ERASOR++ 明确列出帧段形成对比。我们选的帧不同，SA/DA/HA 都会变。
  - **指标定义**：若我们按 benchmark 用 AA（几何平均），数字**必然高于**论文的 HA，不能判为"复现成功"。
  - **cell size**：0.5 / 1.0 / 2.0 m 三档差异巨大（HA 84.03 / 82.90 / 81.28，SA 83.92 / 83.40 / 74.92），用错一档就对不上。
  - **位姿来源**：SuMa 而非 GT pose。
  - **论文内部不一致**：表 I（95.98）与表 IV（96.03）在 KITTI 01 的 HA 上有 0.05 差。
  - **数据驱动基线不可复跑**：4DMOS / MapMOS 在 KITTI 上论文自己就没报；DeFlow 需要 Argoverse 2 训练。
  - 表格里 KITTI 00 上 BeautyMap 与 dynablox 的 SA 完全相同（都是 96.76），疑似引用自同一来源，交叉校验时注意。
- **阻塞风险**：
  - **KITTI / SemanticKITTI 必须注册下载**（硬阻塞，需先申请）。
  - **数据体积**：KITTI odometry raw + SemanticKITTI 为**数十 GB 量级**（论文未给 GB 数，属我们侧估计）。
  - **semi-indoor 自采数据集**依赖 DynamicMap_Benchmark 仓库发布；拿不到则表 I 第 4 列（含 BeautyMap 的 93.69 / 90.67 / 92.16）无法复现。
  - 论文**未给代码 commit、未给 Python 依赖版本**，仓库若已更新可能漂移。
  - Python 实现的 0.046 s/帧是在 i9-12900KF 上测的，我们的机器/解释器不同则耗时不可直接比。
