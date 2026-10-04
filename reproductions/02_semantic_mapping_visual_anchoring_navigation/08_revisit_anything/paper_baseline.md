# 02-08 · Revisit Anything — 论文报告值 Paper-reported baseline

| 项 Item | 内容 |
| :--- | :--- |
| 论文 | Revisit Anything: Visual Place Recognition via Image Segment Retrieval |
| Venue / 年 | **ECCV 2024**（Comments 字段原文：*"Presented at ECCV 2024; Includes supplementary; 29 pages; 8 figures"*） |
| 来源 | 本地 PDF `/home/qzl/workspace/Localise/01_task_books/materials/papers_pdf/124_Revisit_Anything.pdf`，共 **29 页**（含 supplementary）；主文结果表 **p.9–p.13**，补充表 **p.16–p.20**。已逐页 `pdftotext -layout` 核对；arXiv:2409.18049v1 元数据亦已核对 |
| 官方代码 | <https://github.com/AnyLoc/Revisit-Anything> |
| 任务 | 视觉位置识别（VPR）：先用 **SAM 开放集分割**把图像切成片段，把「一个片段 + 它的邻居片段」建成 **SuperSegment** 子图，再对每个 SuperSegment 做 VLAD 聚合与检索；最后把片段级命中融合回图像级。号称 "revisit anything"，并额外做 **Object-of-Interest（OOI）实例检索** |
| 数据集 | **室外**：Pitts30k、AmsterTime、MSLS（CPH / SF）、SF-XL (Val)、Revisited Oxford5K (RO5k)、Revisited Paris6k (RP6k)、**VPAir**。<br>**室内**：Baidu Mall（含扩展的 220 个 OOI 标注）、17Places、InsideOut。规模见下方 Table 12 |
| 指标 | **Recall@K（R@1 / R@5）**。定义（§4, p.8）：对每个 query **片段**检索 top K′ = **50** 个片段，再按相似度加权频率（式 4）折算出 top K = 5 张**图像**，命中即算对。GT 判据各数据集不同（GPS 半径或帧间隔） |
| 硬件 | **未找到**。我在全文 29 页（含 supplementary）grep 了 `GPU|NVIDIA|RTX|A100|V100`，**0 命中** —— 论文从未说明训练/推理硬件。仅在 §10.2（p.19）说明微调设置，未提算力 |

## 论文报告的数字 Reported numbers

### 室外街景数据集 R@1/R@5（Table 1, **p.9**）

| 出处 | 数据集 | 方法 | 指标 | 数值 |
| :--- | :--- | :--- | :--- | ---: |
| 表 1, p.9 | Pitts-30K | **SegVLAD-FineT (M)**（本文最优） | R@1 / R@5 | **93.1 / 96.8** |
| 表 1, p.9 | Pitts-30K | SegVLAD-PreT (D) | R@1 / R@5 | 86.7 / 94.2 |
| 表 1, p.9 | Pitts-30K | AnyLoc（对比方法） | R@1 / R@5 | 87.7 / 94.7 |
| 表 1, p.9 | Pitts-30K | MixVPR（对比方法） | R@1 / R@5 | 91.5 / 95.5 |
| 表 1, p.9 | MSLS SF | **SegVLAD-FineT (D)**（本文最优） | R@1 / R@5 | **93.4 / 97.1** |
| 表 1, p.9 | MSLS CPH | **SegVLAD-FineT (D)** | R@1 / R@5 | **91.8 / 96.4** |
| 表 1, p.9 | SF-XL Val | **SegVLAD-FineT (M)** | R@1 / R@5 | **95.6 / 98.2** |
| 表 1, p.9 | RO5k Med | **SegVLAD-PreT (M)** | R@1 / R@5 | **92.9 / 95.7** |
| 表 1, p.9 | RO5k Hard | **SegVLAD-PreT (M)**（提升最大处） | R@1 / R@5 | **61.4 / 81.4** |
| 表 1, p.9 | RO5k Hard | AnyLoc（对比方法） | R@1 / R@5 | 40.0 / 58.6 |
| 表 1, p.9 | RO5k Hard | EigenPlaces（对比方法，次优） | R@1 / R@5 | 42.8 / 57.1 |
| 表 1, p.9 | RP6k Med | **SegVLAD-PreT (D)** | R@1 / R@5 | **98.5 / 100** |
| 表 1, p.9 | RP6k Hard | **SegVLAD-PreT (D)** | R@1 / R@5 | **18.6 / 55.7** |
| 表 1, p.9 | RP6k Hard | SALAD（对比方法，次优） | R@1 / R@5 | 14.3 / 58.6 |

### 分布外 / 室内数据集 R@1/R@5（Table 2, **p.9**）

| 出处 | 数据集 | 方法 | 指标 | 数值 |
| :--- | :--- | :--- | :--- | ---: |
| 表 2, p.9 | Baidu Mall | **SegVLAD-PreT (M)**（本文最优） | R@1 / R@5 | **80.4 / 94.0** |
| 表 2, p.9 | Baidu Mall | SegVLAD-PreT (D) | R@1 / R@5 | 78.5 / 93.8 |
| 表 2, p.9 | Baidu Mall | AnyLoc（对比方法） | R@1 / R@5 | 75.2 / 87.6 |
| 表 2, p.9 | AmsterTime | **SegVLAD-FineT (M)**（本文最优） | R@1 / R@5 | **60.2 / 78.2** |
| 表 2, p.9 | AmsterTime | AnyLoc（对比方法） | R@1 / R@5 | 50.3 / 73.0 |
| 表 2, p.9 | InsideOut | **SegVLAD-FineT (M)**（本文最优） | R@1 / R@5 | **7.2 / 17.2** |
| 表 2, p.9 | InsideOut | AnyLoc（对比方法） | R@1 / R@5 | 2.4 / 8.0 |
| 表 2, p.9 | 17Places | SegVLAD-PreT (D)/(M)（并列最高） | R@1 / R@5 | 95.3 / 98.0（(M) 为 95.3/98.0） |
| 表 2, p.9 | 17Places | AnyLoc（对比方法） | R@1 / R@5 | 95.3 / 97.3 |
| 表 2, p.9 | VPAir | **SegVLAD-PreT (D)**（本文最优） | R@1 / R@5 | **69.8 / 83.7** |
| 表 2, p.9 | VPAir | AnyLoc（对比方法） | R@1 / R@5 | 66.7 / 79.2 |

### Object-of-Interest 实例检索 R@1（Table 3, **p.10**；Baidu 扩展集，**220 个 OOI**）

| 出处 | 数据集 | 方法 | 指标 | 数值 |
| :--- | :--- | :--- | :--- | ---: |
| 表 3, p.10 | Baidu OOI (220) | **SegVLAD（本文，带邻域）** | R@1 | **92.7** |
| 表 3, p.10 | Baidu OOI (220) | SegVLAD NoNbrAgg（本文，无邻域） | R@1 | 64.1 |
| 表 3, p.10 | Baidu OOI (220) | Global-to-Global（整图基线） | R@1 | 86.4 |
| 表 3, p.10 | Baidu OOI (220) | Segment-to-Global（片段查整图） | R@1 | 30.0 |

> **注意区分**：Table 3 是**物体实例检索**（query 是 OOI 片段），与 Table 1/2 的**地点检索**不是同一个任务，数字不可直接比较。论文明确说这对应 InstanceImageNav 场景。

### 消融：邻域阶数、排序方式、patch 对照（Table 4/5 **p.11**；Table 6 **p.13**）

| 出处 | 数据集 | 方法 | 指标 | 数值 |
| :--- | :--- | :--- | :--- | ---: |
| 表 4, p.11 | Baidu | SegVLAD, order 3（本文最优） | R@1 / R@5 | 77.7 / 92.6 |
| 表 4, p.11 | Baidu | SegVLAD, order 0（无邻域） | R@1 / R@5 | 73.1 / 89.9 |
| 表 4, p.11 | Baidu | SAP, order 0 | R@1 / R@5 | 74.6 / 91.1 |
| 表 4, p.11 | Baidu | SAP, order 3 | R@1 / R@5 | 49.8 / 78.0 |
| 表 5, p.11 | Baidu / AmsterTime | 本文相似度加权频率（Ours） | R@1 / R@5 | 78.5 / 93.8 · 54.4 / 76.3 |
| 表 5, p.11 | Baidu / AmsterTime | MaxSeg | R@1 / R@5 | 78.5 / 93.9 · 53.9 / 70.4 |
| 表 5, p.11 | Baidu / AmsterTime | MaxSim | R@1 / R@5 | 65.2 / 92.7 · 34.4 / 62.4 |
| 表 6, p.13 | AmsterTime | **SegVLAD**（105 seg/img, 129 637 db seg） | R@1 / R@5 | **56.8 / 77.7** |
| 表 6, p.13 | AmsterTime | Patch 64×64（16 seg/img） | R@1 / R@5 | 52.0 / 75.1 |
| 表 6, p.13 | AmsterTime | Patch 16×16（256 seg/img） | R@1 / R@5 | 35.7 / 62.1 |

### 补充材料：存储/时间、检索粒度、SAM 替换、backbone 替换（**p.16–p.18**）

| 出处 | 数据集 | 方法 | 指标 | 数值 |
| :--- | :--- | :--- | :--- | ---: |
| 表 7, p.16 | AmsterTime / Pitts30K | SegVLAD（ψ = 1.0，全量） | R@1 / R@5 | 58.9 / 79.3 · 93.2 / 96.8 |
| 表 7, p.16 | AmsterTime | SegVLAD（ψ = 0.4 IOU 过滤，省 80% 片段） | 存储 GB / 时间 ms | 0.05 / 3.1（全量 0.98 / 42.3） |
| 表 7, p.16 | Pitts30K | SALAD（整图基线，对比方法） | 存储 GB / 时间 ms | 0.62 / 25.1 |
| 表 8, p.17 | Baidu / AmsterTime | **Segment (SegVLAD)** | R@1 / R@5 | 78.5 / 93.8 · 56.8 / 77.7 |
| 表 8, p.17 | Baidu / AmsterTime | Global (AnyLoc)（对比方法） | R@1 / R@5 | 75.2 / 87.6 · 50.3 / 73.0 |
| 表 8, p.17 | Baidu / AmsterTime | Local (Pixel/Point)（对比方法） | R@1 / R@5 | 69.1 / 88.2 · 42.2 / 66.1 |
| 表 9, p.17 | Baidu | SegVLAD + SAM（分割耗时 3.5 s） | R@1 / R@5 | 78.5 / 93.8 |
| 表 9, p.17 | Baidu | SegVLAD + FastSAM（0.28 s，13× 快） | R@1 / R@5 | 76.2 / 91.9 |
| 表 10, p.18 | AmsterTime / Pitts30K | HardVLAD（本文默认） | R@1 / R@5 | 58.9 / 79.3 · 93.2 / 96.8 |
| 表 10, p.18 | AmsterTime / Pitts30K | SoftVLAD (NetVLAD) | R@1 / R@5 | 60.2 / 78.8 · 93.0 / 96.9 |
| 表 11, p.18 | AmsterTime | SegVLAD + DINOv2 ViT-G/14 (1.1B) | R@1 / R@5 | 56.8 / 77.7 |
| 表 11, p.18 | AmsterTime | AnyLoc + DINOv2 ViT-G/14 (1.1B)（对比方法） | R@1 / R@5 | 50.3 / 73.0 |

### 数据集规模（Table 12, **p.20**；补充 §10.3, p.20–21）

| 数据集 | 图像数 (Ref / Qry) | 片段数 (Ref / Qry) | 平均片段/图 | 分辨率 |
| :--- | :--- | :--- | :--- | :--- |
| Baidu | 689 / 2292 | 92K / 295K | 134 / 129 | 480×640 |
| AmsterTime | 1231 / 1231 | 129K / 119K | 105 / 96 | 256×256 |
| Pitts30K | 10K / 6816 | 873K / 592K | 87 / 86 | 480×640 |
| MSLS CPH | 6315 / 242 | 578K / 23K | 91 / 96 | 480×640 |
| MSLS SF | 12556 / 498 | 1.1M / 43K | 89 / 87 | 480×640 |
| SF-XL (Val) | 8015 / 7993 | 648K / 646K | 81 / 81 | 512×512 |
| InsideOut | 10886 / 500 | 821K / 52K | 75 / 106 | 480×640 |
| 17Places | 406 / 406 | 34K / 34K | 84 / 86 | 480×640 |

**模型配置（§10.2, p.19，复现必须对齐）**：
- `SegVLAD-PreT`：DINOv2 **ViT-G**，**layer 31 value facet**（沿用 AnyLoc 默认），Hard-VLAD。
- `SegVLAD-FineT`：DINOv2 **ViT-B**，**只微调最后 4 层**，在 **GSV 数据集**上训，输入 **224×224**，**NetVLAD 64 clusters**（用 GSV 训练图像随机初始化）。
- 两者都把 VLAD 描述子用 PCA 降到 **1024 维**，PCA 在**各数据集自己的 database 图像**上训练（map-specific）。
- SAM 用 **ViT-H** 默认参数，32×32 点提示网格，按 IOU + stability 过滤。
- 评测分辨率：DINOv2 编码器 **640×480**，SAM **320×240**；AmsterTime 两者都用 **256×256**。
- 词表两种：map-specific **(M)** 与 domain-specific **(D)**。

## 关键结论（论文自己声称的）

- **片段级检索 > 整图检索**：SegVLAD 在多数数据集上刷新 SOTA；Baidu Mall 上比 AnyLoc **+3～5% R@1、约 +6% R@5**（§5.1, p.9）。在 RO5k Hard 上整图方法普遍崩（AnyLoc 40.0），SegVLAD-PreT (M) 达 **61.4**。
- **瓶颈是"重叠部分被非重叠部分淹没"**：论文把整图描述符的失败归因于 viewpoint shift 下非重叠区域主导相似度（Abstract, p.1）。
- **邻域上下文关键**：SegVLAD 去掉邻域从 92.7 掉到 64.1（Table 3, p.10）；反过来 SAP 加邻域从 74.6 掉到 49.8（Table 4, p.11）—— 两种聚合对邻域的响应方向相反。
- **物体实例检索是新增能力**：用 OOI 片段当 query 时 SegVLAD 92.7，而 Segment-to-Global 只有 30.0、Global-to-Global 86.4（Table 3, p.10），论文称这是现有 VPR 方法不具备的 open-set 能力（§6, p.14）。

## 内容变化（物体移动/移除）下的表现：论文报告了什么

**论文未报告。**

我在全文 **29 页（含 supplementary）** grep 了 `3RScan|furniture|rearrang|object.*mov|mov.*object|removed|change detection|content change|layout`，**零命中**。论文评测的变化维度只有：

| 论文实际测的变化 | 出处 | 是不是内容变化 |
| :--- | :--- | :--- |
| 视角 / 大幅视点漂移 | Abstract p.1；Table 1/2 p.9 | ❌ 外观+几何视角 |
| 光照、昼夜、季节、临时行人车辆 | §10.3 p.20（Baidu "pedestrians"、17Places "lighting conditions"） | ❌ 外观 |
| 长时程历史影像（AmsterTime 灰度老照片 vs 现代 RGB） | §10.3 p.20 | ❌ 模态+外观，建筑结构未变 |
| 室内外视角（InsideOut 透过窗户看街景） | §10.3 p.21 | ❌ 视角 |
| **Baidu OOI 物体实例检索（220 个 OOI）** | Table 3 p.10 | ⚠️ **最接近，但不是** |

关于最后一条，必须说清楚：Table 3 的 OOI 任务**不是**"物体被移动后还能否认出"。它的协议是（§5.2, p.10）：*"we use the original query images of the Baidu Mall dataset as the database and the images with OOI as the queries"* —— 即**把同一批 Baidu 图像换个用法**，query 从"整图"换成"图上的一个物体 mask"，考的是**部分-整体匹配能力**，而不是跨会话的布局改变。数据里物体没有动。论文原文也只说 OOI 覆盖 "logos, brand names, posters" 这类**可辨识区域**。

> **这正是我们项目的论点**：02-08 是本仓库里与"分割级检索"最强相关的已发表工作，它把 VPR 从"整图"推进到"片段/物体级"，但**依然只在静态布局下评测**。它证明了"用物体片段检索"有增益，**没有**证明这种增益在"家具被重新摆放"时是否还成立。我们的 08 号复现目标（构造"同一地点物体被移动"的查询对）在论文里**找不到任何可对照的基线数字**。

## 对我们的复现意味着什么

- **可复现的前提**：
  - **代码**：`git clone https://github.com/AnyLoc/Revisit-Anything`。
  - **权重**：DINOv2 ViT-G/14 与 ViT-B（公开，torch.hub）+ **SAM ViT-H**（公开，约 2.4 GB）。`SegVLAD-FineT` 需要**自己微调**（GSV 数据集 + 只训 4 层），论文未发布微调后的 checkpoint（截至本记录未核实仓库是否提供，复现时须先查）。
  - **数据**：与 AnyLoc 共用 `VPR-datasets-downloader` 拉外链；AmsterTime、InsideOut、SF-XL、MSLS 各有独立申请/下载入口，**并非全部一键可下**。
  - **硬件**：论文**未说明**。但 ViT-G (1.1B) + SAM ViT-H + 每图约 100 个片段 × 每数据集几十万片段 —— 存储与显存开销都很大（Table 7 显示 Pitts30K 全量需 **6.65 GB** 描述子、检索 **251 ms/query**）。**GPU 是硬门槛**。
  - **版本**：arXiv:2409.18049v1（2024-09-26）；无固定 commit，须自己记录。
- **目标数字**：优先打 **Baidu Mall：AnyLoc 75.2/87.6 → SegVLAD-PreT 78.5/93.8（Table 2, p.9）**，因为同一数据集上 AnyLoc（02-07）有对应数字，可以直接验证"分割级 vs 整图"的增益是否复现。次选 AmsterTime **50.3/73.0 → 56.8/77.7**（Table 2 + Table 8, p.9/p.17）。若要核对训练部分，用 Pitts-30K SegVLAD-FineT (M) **93.1/96.8**（Table 1, p.9）。
- **对不上的可能原因**：
  1. **SAM 版本/提示网格**：论文用 32×32 点提示 + IOU/stability 过滤；换成 FastSAM 或别的分割器 R@1 掉约 2%（Table 9, p.17）。分割质量直接决定片段数，片段数又直接决定 R@1（Table 6, p.13）。
  2. **分辨率**：DINOv2 编码器 640×480、SAM 320×240；AmsterTime 必须 256×256。分辨率改动会显著改变结果（Table 9 显示 FastSAM 提高分辨率反而更好）。
  3. **词表来源 (M) vs (D)** 与 **PCA 是否 map-specific**：同一方法两种词表差最多 11 个百分点（SegVLAD-PreT 在 RO5k Hard：61.4 vs 47.1）。
  4. **邻域阶数**：论文默认 order 3；写成 order 0 会掉到 73.1（Table 4, p.11）—— 这是最容易踩的默认值坑。
  5. **微调复现**：ViT-B 只训最后 4 层、GSV 数据、224×224、64 clusters 随机初始化 —— 随机种子未给，FineT 数字比 PreT 更难对齐。
  6. **数据集划分**：MSLS 只用 validation 的 2 个城市；InsideOut 是作者**自己裁剪的子集**（500 查询 / 10886 参考，50 m 半径）—— 这个子集**不在原始 InsideOut 发布里**，必须用作者的划分。
- **阻塞风险**：
  - **高**：**GPU + 存储**。ViT-G + SAM ViT-H 推理，加上每数据集几十万片段的描述子库（Pitts30K 全量 6.65 GB）。
  - **中**：`SegVLAD-FineT` 的微调 checkpoint 与 GSV 训练数据可得性未确认；论文未给训练超参与种子。
  - **中**：数据集外链失效风险（与 02-07 同）。
  - **高（对项目目标而言）**：与 02-07 完全相同的缺口 —— **"物体被移动"的评测 split 不存在**。论文给不出基线，我们只能拿 Baidu 的 78.5/93.8 当"内容未变"的锚点，自己造变化条件并自己承担没有对照的风险。
