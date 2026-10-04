# 01-01 · DynamicMap_Benchmark — 论文报告值 Paper-reported baseline

| 项 Item | 内容 |
| :--- | :--- |
| 论文 | A Dynamic Points Removal Benchmark in Point Cloud Maps |
| Venue / 年 | arXiv:2307.07260v1 [cs.RO]，2023-07-14；**正式发表于 IEEE ITSC 2023**（本 PDF 正文只印了 arXiv 编号，未印 venue；ITSC 2023 依据 DUFOMap 参考文献 [10] 的引用条目 "IEEE 26th ITSC, 2023, pp. 608–614"） |
| 本地 PDF | `Localise/01_task_books/materials/papers_pdf/064_Dynamic_Points_Removal_Benchmark_DynamicMap.pdf`（结果表在第 5–7 页：表 I、表 II、图 5 在第 5 页，图 6、图 7 在第 6 页） |
| 官方代码 | https://github.com/KTH-RPL/DynamicMap_Benchmark （论文正文 p.1 给出；同时声明清洗后的扩展数据集也在该仓库） |
| 任务 | 建立统一的动态点删除基准：把 Removert / ERASOR / Octomap 三种传统方法重构成无 ROS 的统一实现，在多种传感器与场景下做**点级**评测，并提出改进版 Octomap |
| 数据集 | 主实验三个：**KITTI**（seq 00、05，动态标签来自 SemanticKITTI [6]）、**Argoverse 2.0 big city**（两个 VLP-32C 传感器）、自采 **Semi-indoor**（16 线 VLP-16）。位姿：KITTI 与 AV2 用数据集自带 GT pose，semi-indoor 用 SLAM 包 simple-ndt [19]。论文另声明贡献了"extended datasets"到代码仓库 |
| 指标 | **SA%（Static Accuracy）**：静态点被正确标注的比例；**DA%（Dynamic Accuracy）**：动态点被正确标注的比例；**AA%（Associated Accuracy）= √(SA × DA)**，论文明确说用**几何平均**而不是 F1 的调和平均，对较小值更敏感。三者均为**点级（point-wise）**评测，"without downsampling the ground truth map to voxel level"。另有距离分布图（图 5）：误标点（false negative）到最近正确动态点的距离分布 |
| 硬件 | 台式机，12th Gen Intel® Core™ i9-12900KF，24 核（p.4 §V 开头） |

## 论文报告的数字 Reported numbers

标注约定：**论文自己的方法 = "Octomap w G" 与 "Octomap w GF"**（论文对 Octomap 的两档改进，p.3 §III-C、p.4 §V-A）；其余行为论文复现的基线方法。带 `*` 的是论文标注的 offline 方法（需要先有 raw global map）。

### 表 I：动态点删除方法定量对比（PDF p.5）

| 出处（表/图 + 页） | 数据集 / 序列 | 方法 | 指标 | 数值 |
| :--- | :--- | :--- | :--- | ---: |
| 表 I, p.5 | KITTI sequence 00 | Removert* [5] | SA / DA / AA | 99.44 / 41.53 / 64.26 |
| 表 I, p.5 | KITTI sequence 00 | ERASOR* [16] | SA / DA / AA | 66.70 / 98.54 / 81.07 |
| 表 I, p.5 | KITTI sequence 00 | Octomap [8] | SA / DA / AA | 68.05 / 99.69 / 82.37 |
| 表 I, p.5 | KITTI sequence 00 | **Octomap w G（本文）** | SA / DA / AA | 85.92 / 98.88 / 92.17 |
| 表 I, p.5 | KITTI sequence 00 | **Octomap w GF（本文）** | SA / DA / AA | 93.06 / 98.67 / 95.83 |
| 表 I, p.5 | KITTI sequence 05 | Removert* [5] | SA / DA / AA | 99.42 / 22.28 / 47.06 |
| 表 I, p.5 | KITTI sequence 05 | ERASOR* [16] | SA / DA / AA | 69.40 / 99.06 / 82.92 |
| 表 I, p.5 | KITTI sequence 05 | Octomap [8] | SA / DA / AA | 66.28 / 99.24 / 81.10 |
| 表 I, p.5 | KITTI sequence 05 | **Octomap w G（本文）** | SA / DA / AA | 86.15 / 98.46 / 92.10 |
| 表 I, p.5 | KITTI sequence 05 | **Octomap w GF（本文）** | SA / DA / AA | 93.54 / 92.48 / 93.01 |
| 表 I, p.5 | AV2.0 big city | Removert* [5] | SA / DA / AA | 98.97 / 31.16 / 55.53 |
| 表 I, p.5 | AV2.0 big city | ERASOR* [16] | SA / DA / AA | 77.51 / 99.18 / 87.68 |
| 表 I, p.5 | AV2.0 big city | Octomap [8] | SA / DA / AA | 65.91 / 96.70 / 79.84 |
| 表 I, p.5 | AV2.0 big city | **Octomap w G（本文）** | SA / DA / AA | 76.38 / 86.26 / 81.17 |
| 表 I, p.5 | AV2.0 big city | **Octomap w GF（本文）** | SA / DA / AA | 82.66 / 82.44 / 82.55 |
| 表 I, p.5 | Semi-indoor | Removert* [5] | SA / DA / AA | 99.96 / 12.15 / 34.85 |
| 表 I, p.5 | Semi-indoor | ERASOR* [16] | SA / DA / AA | 94.90 / 66.26 / 79.30 |
| 表 I, p.5 | Semi-indoor | Octomap [8] | SA / DA / AA | 88.97 / 82.18 / 85.51 |
| 表 I, p.5 | Semi-indoor | **Octomap w G（本文）** | SA / DA / AA | 94.95 / 73.95 / 83.80 |
| 表 I, p.5 | Semi-indoor | **Octomap w GF（本文）** | SA / DA / AA | 96.79 / 73.50 / 84.34 |

### 表 II：运行时间与参数量（PDF p.5）

| 出处（表/图 + 页） | 数据集 / 序列 | 方法 | 指标 | 数值 |
| :--- | :--- | :--- | :--- | ---: |
| 表 II, p.5 | 未标注序列（runtime 对比） | Removert* [5] | Runtime/frame [s] / #Parameters | 0.044 ± 0.002 / 6 |
| 表 II, p.5 | 未标注序列 | ERASOR* [16] | Runtime/frame [s] / #Parameters | 0.718 ± 0.039 / 18 |
| 表 II, p.5 | 未标注序列 | Octomap [8] | Runtime/frame [s] / #Parameters | 2.985 ± 0.961 / 5 |
| 表 II, p.5 | 未标注序列 | **Octomap w G（本文）** | Runtime/frame [s] / #Parameters | 3.054 ± 0.966 / 8 |
| 表 II, p.5 | 未标注序列 | **Octomap w GF（本文）** | Runtime/frame [s] / #Parameters | 2.147 ± 0.468 / 10 |

### 图 5（PDF p.5）：误差分布

| 出处（表/图 + 页） | 数据集 / 序列 | 方法 | 指标 | 数值 |
| :--- | :--- | :--- | :--- | ---: |
| 图 5, p.5（正文 p.5 复述） | KITTI sequence 05 | 所有方法 | 误标点（false negative）到最近正确动态点的距离 | 全部方法的 false negative 落在真值 **10 cm – 30 cm** 范围内；Removert 的尺度差异最大 |

## 关键结论（论文自己声称的）

- **改进版 Octomap（w GF）整体最优**：在 KITTI 00 把 AA 从 82.37 提到 **95.83**、SA 从 68.05 提到 93.06；KITTI 05 从 81.10 提到 93.01（表 I, p.5）。作者称这是"incorporating ground fitting into the pipeline"的结果。
- **速度也有收益**：加入噪声滤波后（w GF 相对 w G）取得 **20% − 30% 的加速**，对应 3.054 s → 2.147 s（表 II 与正文 p.5）。
- **精度与速度是权衡**：AA 最低的方法（Removert）单帧处理最快；Octomap 系列"prohibitively slow"（2.985 s/帧）。Removert 还需多分辨率才能出好结果，会进一步增加耗时（正文 p.5）。
- **失败模式的共性**：false negative 大多紧贴 true positive（10–30 cm），作者建议用"以 true positive 为中心做聚类"来补救（图 5 与正文 p.5）。
- **稀疏 LiDAR 是新暴露的短板**：semi-indoor（VLP-16）上所有方法 DA 明显下降——ERASOR 66.26、Octomap 82.18、Removert 12.15，即使改进版 Octomap w GF 也只有 73.50（表 I, p.5）。

## 对我们的复现意味着什么

- **可复现的前提**：
  - 代码与"extended datasets"都在 https://github.com/KTH-RPL/DynamicMap_Benchmark ，无需 GPU（全部方法为 CPU/传统算法）。
  - **KITTI 需在 KITTI 官网注册后下载**；动态点真值来自 **SemanticKITTI，同样需要注册**才能拿到标签与位姿。这是本方向所有方法共同的入口依赖。
  - **Argoverse 2.0 需要在其官网注册/同意条款**才能下载（论文只说"latest Argoverse 2.0 dataset [7]"，未提下载流程）。
  - 论文未给具体 commit、未给依赖版本；仓库 README 是唯一权威步骤来源。
  - 判据口径：AA 用**几何平均 √(SA×DA)**，**不是** F1；如果我们的评测脚本用 F1 或先降采样到体素级，数字**不可比**。
- **目标数字**：若要验收"我们跑通了基准并复现出论文里某一个方法的数字"，最小目标是 **KITTI sequence 00 上 Octomap w GF 的 SA / DA / AA = 93.06 / 98.67 / 95.83**（表 I, p.5）——因为它是论文自己的方法且在同一行里给出了同数据集的三个基线（Removert* 99.44/41.53/64.26、ERASOR* 66.70/98.54/81.07、Octomap 68.05/99.69/82.37）可供交叉校验。验收容差建议 ±1 个百分点。
- **对不上的可能原因**：
  - **AA 的定义**（几何平均 vs 调和平均/F1）；GT 是否被降采样到体素级。
  - 带 `*` 的方法需要 raw global map 作先验，而"raw map 长什么样"取决于上游 SLAM 位姿；KITTI 用自带 GT pose，semi-indoor 用 simple-ndt——位姿不同则数字不同（DUFOMap 论文的表 III 已证明位姿对结果影响可达数个百分点）。
  - KITTI 用的是选定的"dynamic 最多的"帧段而非全序列，且论文**没有写明** seq 00 / 05 具体用了哪些帧（只写了"KITTI sequence 00 / 05"）——这是一个真实的不可复现点。
  - 参数：Octomap 的 occupancy 阈值、SOR 与 SAC 地面分割参数在论文里未逐项列出（只说"benchmark link includes all the parameters"）。
- **阻塞风险**：
  - **KITTI / SemanticKITTI 必须注册下载**（邮箱注册 + 条款同意），无直链；这是硬阻塞，需先申请。
  - 数据体积：KITTI odometry raw + SemanticKITTI 标签合计 **数十 GB 量级**（论文未给具体 GB 数，属我们侧估计）。
  - Argoverse 2.0 Sensor 数据集体积同样很大，且需注册。
  - semi-indoor 自采数据集依赖仓库发布物；若仓库链接失效，**semi-indoor 一列（含 4 个方法 12 个数）无法复现**。
