# 论文报告值 Paper Baselines

> **这份文件存在的理由**：复现的前提是**先知道要复现出什么数**。
> 在 2026-10-05 之前，本仓库 17 个复现文件夹里只有"论文标题 + 计划"，
> **没有一篇记录原论文到底做出了什么数字**——于是"复现"没有验收标准，
> 跑通了也只能说"它能跑"，不能说"复现了"。
>
> 这一页把每篇原文的**自报结果**集中列出，并指出**能不能在这台机器上复现它**。
> 每个文件夹里的 `paper_baseline.md` 是详细版（含表号、页码、消融、参数、阻塞分析）。

**核对日期**：2026-10-05 · **原文来源**：本地 `Localise/01_task_books/materials/papers_pdf/`（134 篇）
+ 本次补取 3 篇（RIO/3RScan、原始 ERASOR、OASIS-Map）· **覆盖 16/17，缺 1 篇（Removert，闭源）**

---

## 一、总表：每篇论文自报的头号数字

| # | 复现对象 | Venue | 论文自报的头号结果 | 本机可行性 | 详细 |
| :-- | :--- | :--- | :--- | :--- | :--- |
| **01-01** | DynamicMap_Benchmark | ITSC 2023 | KITTI 00，Octomap w GF：SA/DA/AA = **93.06 / 98.67 / 95.83** | 🟢 数据已到手（Zenodo 直链） | [→](01_robust_localization_slam_dynamic/01_dynamicmap_benchmark/paper_baseline.md) |
| **01-02** | KISS-ICP | RA-L 2023 | KITTI 00–10 相对平移误差 **0.50%** | 🟡 CPU 可跑，但 KITTI 需注册 | [→](01_robust_localization_slam_dynamic/02_kiss_icp/paper_baseline.md) |
| **01-03** | ERASOR | RA-L 2021 | SemanticKITTI 00，voxel-wise PR/RR/F1 = **93.980 / 97.081 / 0.955** | 🟡 CPU 可跑，数据需注册 | [→](01_robust_localization_slam_dynamic/03_erasor/paper_baseline.md) |
| **01-04** | Removert | IROS 2020 | ⚠️ **论文闭源，取不到原文** — 见下 | 🔴 无自报值 | [→](01_robust_localization_slam_dynamic/04_removert/paper_baseline.md) |
| **01-05** | DUFOMap | RA-L 2024 | KITTI 00，SA/DA/AA = **97.96 / 98.72 / 98.34** | ✅ **已复现（精确命中）** | [→](01_robust_localization_slam_dynamic/05_dufomap/paper_baseline.md) |
| **01-06** | BeautyMap | RA-L 2024 | KITTI 01，SA/DA/HA = **99.17 / 92.99 / 95.98** | 🟡 CPU 可跑，数据需注册 | [→](01_robust_localization_slam_dynamic/06_beautymap/paper_baseline.md) |
| **01-07** | DynoSAM | T-RO 2025 | OMD (S4U) 相机 ATE **0.11 m** | 🔴 需 CUDA + TensorRT | [→](01_robust_localization_slam_dynamic/07_dynosam/paper_baseline.md) |
| **01-08** | NGD-SLAM | IROS 2025 | TUM f3/w xyz **ATE 0.015 m**，CPU 16.72 ms/帧 | 🟢 **纯 CPU、数据免注册** — 次优入口 | [→](01_robust_localization_slam_dynamic/08_ngd_slam/paper_baseline.md) |
| **01-09** | LT-mapper | ICRA 2022 | delta map **85.7 MB vs 213.6 MB**，**9.8 s vs 87/160 s** | 🟡 ROS 1（EOL），关键序列需联系作者 | [→](01_robust_localization_slam_dynamic/09_lt_mapper/paper_baseline.md) |
| **02-01** | 3RScan / RIO | ICCV 2019 | 1482 scans / 478 场景 / 1004 rescan；RIO-D Recall@<0.2m,20° = **23.76** | 🟡 本机已有 1 对（32 物体）；全量需申请 | [→](02_semantic_mapping_visual_anchoring_navigation/01_3rscan/paper_baseline.md) |
| **02-02** | OASIS-Map | arXiv 2026-07 | 3RScan **moved F1 0.353** / static F1 0.663；Car Park Replaced F1 **0.783** | 🔴 代码未发布 | [→](02_semantic_mapping_visual_anchoring_navigation/02_oasis_map/paper_baseline.md) |
| **02-03** | ConceptGraphs | ICRA 2024 | Replica **mAcc 40.63 / F-mIoU 35.95** | 🔴 需 GPU + 付费 GPT-4 | [→](02_semantic_mapping_visual_anchoring_navigation/03_concept_graphs/paper_baseline.md) |
| **02-04** | DualMap | RA-L 2025 | 地图修订后 SR **60.3%**（未修订 47.2%）；Replica FmIoU 0.5207 | 🔴 需 RTX 4090 | [→](02_semantic_mapping_visual_anchoring_navigation/04_dualmaps/paper_baseline.md) |
| **02-05** | HOV-SG | RSS 2024 | ScanNet **mIOU 0.222 / F-mIoU 0.303 / mAcc 0.431** | 🔴 需 GPU | [→](02_semantic_mapping_visual_anchoring_navigation/05_hov_sg/paper_baseline.md) |
| **02-06** | Clio | RA-L 2024 | Replica **mAcc 37.95 / F-mIoU 36.98** | 🔴 需 RTX 3090 | [→](02_semantic_mapping_visual_anchoring_navigation/06_clio/paper_baseline.md) |
| **02-07** | AnyLoc | RA-L 2023 | Baidu Mall **R@1 75.2** | 🔴 需 GPU（ViT-G14） | [→](02_semantic_mapping_visual_anchoring_navigation/07_anyloc/paper_baseline.md) |
| **02-08** | Revisit Anything | ECCV 2024 | Baidu Mall **R@1 78.5**（SegVLAD-PreT） | 🔴 需 GPU + 6.65 GB 描述子库 | [→](02_semantic_mapping_visual_anchoring_navigation/08_revisit_anything/paper_baseline.md) |

---

## 二、本机可行性：17 个里只有 4 个能真跑

这台机器**没有 GPU**（`nvidia-smi` 不存在，20 核 CPU / 15 GB RAM / 381 GB 空闲）。

| 类别 | 数量 | 哪些 |
| :--- | ---: | :--- |
| ✅ **已经复现成功** | 1 | **01-05 DUFOMap**（SA/DA/AA 与论文 2 位小数完全一致） |
| 🟢 **CPU + 数据可得，能直接做** | 2 | 01-01 DynamicMap_Benchmark（数据已在手）· 01-08 NGD-SLAM（TUM/BONN 免注册） |
| 🟡 **CPU 但数据要注册** | 3 | 01-02 KISS-ICP · 01-03 ERASOR · 01-06 BeautyMap（+ 01-09 要 ROS 1） |
| 🔴 **需要 GPU** | 7 | 01-07 DynoSAM · 02-03 ConceptGraphs · 02-04 DualMap · 02-05 HOV-SG · 02-06 Clio · 02-07 AnyLoc · 02-08 Revisit Anything |
| ⚫ **别的阻塞** | 2 | 01-04 Removert（论文闭源）· 02-02 OASIS-Map（代码未发布） |

> **这解释了一件事**：任务书 §0.3 把 S（语义建图）排在第 1 位，理由是"不需要新硬件"。
> 但从**论文报告值**看，S 线的四个底座（ConceptGraphs / DualMap / HOV-SG / Clio）**全都要 GPU**。
> 真正"不需要新硬件"的是 **D 线的 CPU 部分**。这个结论在只看 README 计划时是看不出来的。

---

## 三、三处只有对着原文才会发现的坑

### 3.1 ⚠️ 同一个方法，换一套口径，结论反过来

| 方法 | 它自己论文里的静态点保留 | 在 DynamicMap_Benchmark 里的点级 SA |
| :--- | ---: | ---: |
| **ERASOR** | **93.98 %**（voxel-wise PR，SemanticKITTI 00） | **66.70 %**（KITTI 00） |
| **Removert** | **85.50 %**（voxel-wise PR，SemanticKITTI 00） | **99.44 %**（KITTI 00） |

**ERASOR 自报最好，在基准里却最差；Removert 自报较差，在基准里却最好。**
两边的差异都不是噪声，是**指标定义**（voxel-wise vs 点级）与**数据/帧段**的差异。

→ 这正是任务书 **§6 并行实验 H1′**（F1 排名 vs 定位效用排名是否一致）要问的问题，
而它**已经出现了一次，且不需要任何新数据**。这是本次最值得往下列的一条线。

### 3.2 ⚠️ 上游示例的参数与论文不一致（已用数字证明）

`DynamicMap_Benchmark/methods/dufomap/main.py` 写的是 `dufomap(0.1, 0.2, 2)`，
注释说 `# resolution, d_s, d_p same with paper`。**但论文的默认值是 `d_p = 1`**（表 IV, p.7）。

| 配置 | SA | DA | AA |
| :--- | ---: | ---: | ---: |
| `d_p=2`（上游示例写的） | 99.8853 | 96.6338 | 98.2461 |
| **`d_p=1`（论文的默认）** | **97.9635** | **98.7196** | **98.3408** |
| **论文表 I, p.5** | **97.96** | **98.72** | **98.34** |

**只有 `d_p=1` 才命中论文。** 而 `d_p=2` 的 AA（98.25）看起来也只差 0.09 —— 因为
**AA 是几何平均，而动态点只占 0.55%，所以 AA 几乎就是 SA**，它区分不出"保守的清理器"和"激进的清理器"。
换句话说：**如果只看 AA，我们会误以为上游示例是对的。**

### 3.3 ⚠️ 任务书 §0.2 的判断需要再收窄一次

任务书 §0.2 / README 里写的切入角度是"内容变化下的定位/识别没有被评测过"。
对着原文核实后，**这个说法一半对一半错**：

| 论文 | 内容变化（物体被移动/替换）下的表现 | 核实方式 |
| :--- | :--- | :--- |
| AnyLoc（02-07） | `论文未报告` | 10 页全文检索 furniture/rearrang/removed/added/layout/content，仅 2 处无关命中 |
| Revisit Anything（02-08） | `论文未报告` | 29 页含补充材料，零命中；其 Table 3 的 220 个 Baidu OOI 是**同一次访问**的部件-整体匹配，物体没动 |
| **RIO / 3RScan（02-01）** | ✅ **报告了**：静态→动态 RIO-D Recall@<0.2m,20° **17.75 → 23.76**，F1 **85.58 → 94.37** | 原文 §3.4 / §5.2，表 3/4/5 |

→ **准确表述**：*内容变化的 **3D 重定位**评测存在（RIO），但内容变化下的 **VPR（图像检索）**评测不存在* ——
没有人用 AnyLoc/SegVLAD 这类检索方法跑过 3RScan 的 A/B 会话。
这比原来的说法**更窄、更难被反驳**，也更接近可执行的实验。

### 3.4 跨会话物体身份：只有 OASIS-Map 在正式评测它

| 论文 | 是否评测"跨会话物体身份" |
| :--- | :--- |
| ConceptGraphs（02-03）· HOV-SG（02-05）· Clio（02-06） | `论文未报告`（HOV-SG 更是明说"假设静态环境、无法处理动态环境"） |
| DualMap（02-04） | 报的是**单次在线会话内**的物体搬迁恢复（SR 47.2% → 60.3%），仍非跨会话 |
| **OASIS-Map（02-02）** | ✅ 表 I 专门有 `Assoc.` 列 + 表 III 专测身份保持；ConceptGraphs 在该列是 `✗` |

→ 任务书 §0.3 那条修正因此成立：**不能把"缺少跨会话身份"当空白点**（OASIS-Map 有），
只能把**可观测性变成可标定的量并分层测量**当作差异点。

---

## 四、还缺什么

| 缺口 | 状态 |
| :--- | :--- |
| **01-04 Removert 原文** | 🔴 闭源（OpenAlex: `is_oa: false`），作者镜像站 DNS 不通。需机构订阅 |
| 其余 16 篇原文 | ✅ 全部在手（15 篇本地 + RIO/ERASOR 原版/OASIS-Map 本次补取） |
| KITTI / SemanticKITTI / Argoverse 2 原始数据 | 🟡 需注册。**但 01-01/01-05 已用 Zenodo 直链绕过**（KITTI 00 + GT，385 MB，免注册） |
| 各复现的 `reproduce.py` | 1/17（只有 02-01）；01-05 本次补上 |
