# 02-07 · AnyLoc — 论文报告值 Paper-reported baseline

| 项 Item | 内容 |
| :--- | :--- |
| 论文 | AnyLoc: Towards Universal Visual Place Recognition |
| Venue / 年 | **IEEE RA-L 2023**（Presented at ICRA 2024）；本机 PDF 为 arXiv:2308.00688v2, 2023-11-29 |
| 来源 | 本地 PDF `/home/qzl/workspace/Localise/01_task_books/materials/papers_pdf/122_AnyLoc.pdf`，共 **10 页**；结果表在 **p.4–p.7**（Table I/II p.4，Table III/IV p.5，Table V/VI p.6，Table VII/VIII p.7）。已逐页 `pdftotext -layout` 核对 |
| 官方代码 | <https://github.com/AnyLoc/AnyLoc>；项目页 <https://anyloc.github.io/> |
| 任务 | 视觉位置识别（VPR）：给定 query 图像，从 reference/database 图像库中检索同一地点图像。**免训练、免微调**——直接用现成自监督基础模型特征 + 无监督聚合 |
| 数据集 | **12 个**数据集，分两类。<br>**Structured（6）**：Baidu Mall、Gardens Point、17 Places、Pittsburgh-30k、St Lucia、Oxford RobotCar。<br>**Unstructured（6）**：Hawkins、Laurel Caverns、Nardo-Air、Nardo-Air R、VP-Air、Mid-Atlantic Ridge |
| 指标 | **Recall@K（R@1 / R@5）**，越高越好。定义（§IV-B, p.4）：top-K 检索结果中存在正确匹配的 query 占比。「正确」由各数据集自己的 GT 判据决定 —— 米制定位半径或帧容差，见下方 Table III 注 |
| 硬件 | §IV-B, p.4 原话：*"All experiments use the same random seed (42) and GPU hardware (**NVIDIA RTX 3090**) for consistency and reproducibility."* 另致谢提到部分算力来自 PSC 的 Bridges-2 集群（NSF ACCESS allocation cis220039p） |

## 论文报告的数字 Reported numbers

### 评估集规模与判据（Table I, p.4；Table III 表头注, p.5）

| 数据集 | NDb（库） | NQ（查询） | 轨迹长度 | 定位半径 / 帧容差 |
| :--- | ---: | ---: | ---: | ---: |
| Baidu Mall | — | — | — | 10 m |
| Gardens Point | 200 | 200 | — | 2 frames |
| 17 Places | 406 | 406 | — | 5 frames |
| Pitts-30k | 10 000 | 6 816 | — | 25 m |
| St Lucia | 1 549 | 1 464 | 9.5 km | 25 m |
| Oxford RobotCar | 213（Overcast Summer） | 251（Autumn Night） | 1.5 km | 25 m |
| Hawkins | 65 | 101 | 282 m | 8 m |
| Laurel Caverns | 141 | 112 | 102 m | 8 m |
| Nardo-Air | 102 | 71 | 700 m / 1 km² | 60 m |
| VP-Air | 12.7k | 2.7k | 100 km | 3 frames |
| Mid-Atlantic Ridge | 65 | 101 | 18 m | 0.3 m |

### 结构化环境 R@1/R@5（Table III, **p.5**）

| 出处 | 数据集 | 方法 | 指标 | 数值 |
| :--- | :--- | :--- | :--- | ---: |
| 表 III, p.5 | Baidu Mall | **AnyLoc-VLAD-DINOv2**（本文最优） | R@1 / R@5 | **75.2 / 87.6** |
| 表 III, p.5 | Baidu Mall | AnyLoc-VLAD-DINO | R@1 / R@5 | 61.2 / 78.3 |
| 表 III, p.5 | Baidu Mall | AnyLoc-GeM-DINOv2 | R@1 / R@5 | 50.1 / 70.6 |
| 表 III, p.5 | Baidu Mall | MixVPR（对比方法） | R@1 / R@5 | 64.4 / 80.3 |
| 表 III, p.5 | Gardens Point | **AnyLoc-VLAD-DINOv2** | R@1 / R@5 | **95.5 / 99.5** |
| 表 III, p.5 | Gardens Point | MixVPR（对比方法） | R@1 / R@5 | 91.5 / 96.0 |
| 表 III, p.5 | 17 Places | **AnyLoc-VLAD-DINOv2** | R@1 / R@5 | **65.0 / 80.5** |
| 表 III, p.5 | 17 Places | MixVPR（对比方法） | R@1 / R@5 | 63.8 / 78.8 |
| 表 III, p.5 | Pitts-30k | **AnyLoc-VLAD-DINOv2** | R@1 / R@5 | **87.7 / 94.7** |
| 表 III, p.5 | Pitts-30k | MixVPR（对比方法） | R@1 / R@5 | 91.5 / 95.5 |
| 表 III, p.5 | Pitts-30k | CosPlace（对比方法） | R@1 / R@5 | 90.4 / 95.7 |
| 表 III, p.5 | St Lucia | **AnyLoc-VLAD-DINOv2** | R@1 / R@5 | **96.2 / 98.8** |
| 表 III, p.5 | St Lucia | MixVPR（对比方法） | R@1 / R@5 | 99.7 / 100 |
| 表 III, p.5 | Oxford | **AnyLoc-VLAD-DINOv2** | R@1 / R@5 | **99.5 / 100** |
| 表 III, p.5 | Oxford | MixVPR（对比方法） | R@1 / R@5 | 92.7 / 99.5 |
| 表 III, p.5 | Oxford | AnyLoc-VLAD-DINO | R@1 / R@5 | 82.2 / 99.0 |
| 表 III, p.5 | **平均（6 集）** | **AnyLoc-VLAD-DINOv2** | **R@1 / R@5** | **86.5 / 93.5** |
| 表 III, p.5 | 平均（6 集） | AnyLoc-VLAD-DINOv2-PCA | R@1 / R@5 | 86.0 / 93.9 |
| 表 III, p.5 | 平均（6 集） | AnyLoc-VLAD-DINO | R@1 / R@5 | 79.0 / 90.2 |
| 表 III, p.5 | 平均（6 集） | AnyLoc-GeM-DINOv2 | R@1 / R@5 | 74.6 / 87.0 |
| 表 III, p.5 | 平均（6 集） | MixVPR（对比方法，次优） | R@1 / R@5 | 83.9 / 91.7 |
| 表 III, p.5 | 平均（6 集） | CosPlace（对比方法） | R@1 / R@5 | 77.0 / 86.8 |
| 表 III, p.5 | 平均（6 集） | NetVLAD（对比方法） | R@1 / R@5 | 62.5 / 79.7 |

### 非结构化环境 R@1/R@5（Table IV, **p.5**）

| 出处 | 数据集 | 方法 | 指标 | 数值 |
| :--- | :--- | :--- | :--- | ---: |
| 表 IV, p.5 | Hawkins | **AnyLoc-VLAD-DINOv2**（本文最优） | R@1 / R@5 | **65.2 / 94.1** |
| 表 IV, p.5 | Hawkins | MixVPR（对比方法） | R@1 / R@5 | 25.4 / 60.2 |
| 表 IV, p.5 | Laurel Caverns | **AnyLoc-VLAD-DINOv2** | R@1 / R@5 | **61.6 / 90.2** |
| 表 IV, p.5 | Laurel Caverns | MixVPR（对比方法） | R@1 / R@5 | 29.5 / 67.0 |
| 表 IV, p.5 | Nardo-Air | **AnyLoc-VLAD-DINOv2** | R@1 / R@5 | **76.1 / 94.4** |
| 表 IV, p.5 | Nardo-Air | CosPlace（对比方法） | R@1 / R@5 | 0 / 1.4（论文称完全失败） |
| 表 IV, p.5 | Nardo-Air R | **AnyLoc-VLAD-DINOv2** | R@1 / R@5 | **85.9 / 100** |
| 表 IV, p.5 | Nardo-Air R | AnyLoc-VLAD-DINO | R@1 / R@5 | 94.4 / 100 |
| 表 IV, p.5 | VP-Air | **AnyLoc-VLAD-DINOv2** | R@1 / R@5 | **66.7 / 79.2** |
| 表 IV, p.5 | VP-Air | MixVPR（对比方法） | R@1 / R@5 | 10.3 / 18.3 |
| 表 IV, p.5 | Mid-Atlantic Ridge | **AnyLoc-VLAD-DINOv2** | R@1 / R@5 | **34.6 / 61.4** |
| 表 IV, p.5 | Mid-Atlantic Ridge | AnyLoc-VLAD-DINO | R@1 / R@5 | 41.6 / 66.3 |
| 表 IV, p.5 | **平均（6 集）** | **AnyLoc-VLAD-DINOv2** | **R@1 / R@5** | **65.0 / 86.5** |
| 表 IV, p.5 | 平均（6 集） | AnyLoc-VLAD-DINO | R@1 / R@5 | 50.5 / 69.0 |
| 表 IV, p.5 | 平均（6 集） | MixVPR（对比方法） | R@1 / R@5 | 33.2 / 57.8 |
| 表 IV, p.5 | 平均（6 集） | CosPlace（对比方法） | R@1 / R@5 | 29.3 / 43.8 |
| 表 IV, p.5 | 平均（6 集） | NetVLAD（对比方法） | R@1 / R@5 | 31.1 / 56.5 |

### 词表消融与跨数据集迁移（Table V, VI, **p.6**）

| 出处 | 数据集 / 域 | 方法 | 指标 | 数值 |
| :--- | :--- | :--- | :--- | ---: |
| 表 V, p.6 | Indoor 域均值 | AnyLoc-VLAD-DINOv2 + **Domain-Specific** 词表 | R@1 | 78.6 |
| 表 V, p.6 | Indoor 域均值 | 同上 + Global 词表 | R@1 | 77.0 |
| 表 V, p.6 | Urban 域均值 | Domain-Specific 词表 | R@1 | 94.4 |
| 表 V, p.6 | Aerial 域均值 | Domain-Specific 词表 | R@1 | 76.2 |
| 表 V, p.6 | Aerial 域均值 | Global 词表 | R@1 | 57.1 |
| 表 VI, p.6 | 词表 VP-Air → 评测 Nardo-Air | Map-Specific / Vocab-Transfer | R@1 | 57.8 / 64.8 |
| 表 VI, p.6 | 词表 VP-Air → 评测 Nardo-Air R | Map-Specific / Vocab-Transfer | R@1 | 70.4 / 88.7 |
| 表 VI, p.6 | 词表 Pitts-30k → 评测 Oxford | Map-Specific / Vocab-Transfer | R@1 | 94.8 / 99.0 |
| 表 VI, p.6 | 词表 Baidu Mall → 评测 17 Places | Map-Specific / Vocab-Transfer | R@1 | 64.5 / 63.8 |

### 设计选择与描述子维度（Table VII, VIII, **p.7**）

| 出处 | 数据集 | 方法 | 指标 | 数值 |
| :--- | :--- | :--- | :--- | ---: |
| 表 VII, p.7 | Baidu / Oxford | DINOv2 + GeM（无词表） | R@1 / R@1 / Dim | 50.1 / 92.2 / 1536 |
| 表 VII, p.7 | Baidu / Oxford | DINOv2 + Hard-Assignment VLAD | R@1 / R@1 / Dim | 71.5 / 94.8 / 49152 |
| 表 VIII, p.7 | Indoor / Urban / Aerial / SubT&D / Underwater | ViT-G AnyLoc-VLAD-DINOv2 | R@1（5 域） | 78.0 / 92.3 / 62.9 / 63.4 / 34.6 |
| 表 VIII, p.7 | Indoor / Urban / Aerial / SubT&D / Underwater | ViT-B CosPlace（VPR 监督，对比方法） | R@1（5 域） | 62.9 / 80.7 / 26.3 / 26.5 / 18.8 |

**模型配置（§IV-B.2, p.4，复现必须对齐）**：命名格式 `AnyLoc-<aggregation>-<model>`。
- `AnyLoc-VLAD-DINO`：DINO **ViT-S8 layer 9 key facet**，VLAD **128 clusters**。
- `AnyLoc-GeM-DINOv2` 与 `AnyLoc-VLAD-DINOv2`：DINOv2 **ViT-G14 layer 31 value facet**，VLAD **32 clusters**。
- PCA 变体：域特定数据库上做 PCA-whitening，描述子从 49k 降到 512（论文称 100× 更小）。

## 关键结论（论文自己声称的）

- **免训练即可通用**：AnyLoc 不做任何 VPR 训练/微调，在 12 个数据集上工作；相比既有方法最高 **4×** 的 Recall@1 提升（Abstract, p.1；§VI, p.7）。
- **结构化环境**：AnyLoc-VLAD-DINOv2 平均 **R@1 86.5**，比次优的 MixVPR（83.9）高约 5%、比 CosPlace 高约 20%（§V-A.1, p.5）。
- **非结构化环境是论文的主战场**：AnyLoc-VLAD-DINOv2 平均 **R@1 65.0**，MixVPR 仅 33.2、DINOv2-CLS 47.2；即「专为 VPR 训练的方法在分布外崩溃」——CosPlace 在 Nardo-Air 上 **R@1 = 0**（§V-A.2/A.4, p.5）。
- **域特定词表带来额外增益**：用 PCA 划分出的领域词表比全局词表在 Aerial 域 **+19%**（76.2 vs 57.1，§V-B.1, p.6）；论文摘要称整体 **+6%**。
- **自监督 > VPR 监督**：ViT-G AnyLoc-VLAD-DINOv2 全面超过 ViT-B CosPlace-VLAD，后者在 Aerial 仅 26.3（Table VIII, p.7）。

## 内容变化（物体移动/移除）下的表现：论文报告了什么

**论文未报告。**

论文的「anytime」定义里**确实点名**了 transient objects —— p.1 §I 原话：*"anytime (robust to temporal changes in the scene, such as day-night or seasonal variations, **or to transient objects**)"* —— 但这只是**声称的能力**，不是被测量的量。12 个评估数据集**没有任何一个**包含「同一地点两次访问之间物体被移动/移除」的标注或评测协议。

我查过的地方（全文 10 页，`pdftotext -layout` 后 grep `furniture|rearrang|object.*mov|mov.*object|removed|added|change detection|layout change|content|3RScan|ScanNet`）：
- 唯一命中 `content` 的是 ViT 术语 *"summary of the image content"*（p.3 脚注 1）。
- 唯一命中 `furniture` 的是 §V-B.2 p.6 对 VLAD 聚类可视化的定性描述：*"there is intra-place consistency for the text signs and furniture"* —— 这是**特征聚类图**的解释，不是内容变化实验。
- 论文实际评测的变化类型只有两类：**外观/时间**（Oxford RobotCar 的 Overcast Summer vs Autumn Night 跨季 + 昼夜，1.5 km；17 Places 的光照变化；Gardens Point 的昼夜；Nardo-Air 的 2022 vs 2023；Mid-Atlantic Ridge 的 2015 vs 2020）与**视角**（>< 90°、180° 反向，见 Fig. 1）。这些都是**同一套静态结构**下的像素级外观漂移，家具位置没有变。

> **这正是我们项目的论点所在**：AnyLoc 号称"anytime/anywhere/anyview"，但 `anytime` 只覆盖了光照与季节，**不覆盖布局改变**。论文没有给出任何可以用来回答"物体被挪走后 R@1 掉多少"的数字。

## 对我们的复现意味着什么

- **可复现的前提**：
  - **代码**：`git clone https://github.com/AnyLoc/AnyLoc`。免训练，无权重需训。
  - **权重**：只需 DINOv2 ViT-G14（`facebookresearch/dinov2` torch.hub，公开可下，约 4.5 GB）与 DINO ViT-S8（公开）。**无 gated 权重**。
  - **数据**：官方用 `VPR-datasets-downloader`，拉到的是**外部链接**（多为 Google Drive / 学校服务器），不是自托管 —— 存在链接失效风险，README 也已注明「先小规模验证一条」。
  - **硬件**：论文用 **RTX 3090**。ViT-G14 是 1.1B 参数、输入 480×640 上下，全量 Pitts-30k（10k 库 + 6.8k 查询）在 24 GB 卡上跑得动但会很吃显存与时间；只跑单数据集子集是稳妥起步。
  - **提交/版本**：论文 = arXiv:2308.00688v2；仓库无固定 commit 记录在论文里，复现时**须自己记 commit hash**。
- **目标数字**：优先打 **Baidu Mall R@1 = 75.2 / R@5 = 87.6（Table III, p.5）** —— 室内、数据量小（689 库 / 2292 查询）、且它同时是 02-08 Revisit Anything 的对比基准，一箭双雕。次选 Pitts-30k **87.7 / 94.7**（Table III, p.5）作为大规模校验点。若要做域泛化，取 VP-Air **66.7 / 79.2**（Table IV, p.5）。
- **对不上的可能原因**：
  1. **backbone 版本**：ViT-G14 只有一版，但 DINOv2 的 torch.hub 接口与论文 2023 年用的可能不同（层数索引 31、value facet 取法极易错位）；用 ViT-L 代替会直接掉点（Fig. 5a, p.7）。
  2. **层/facet/聚类数**：DINOv2 必须 **layer 31 + value facet + 32 clusters**；DINO 必须 **layer 9 + key facet + 128 clusters**。取错一层就全盘偏。
  3. **PCA 变换**：论文明确只用 database 图像训练 PCA（p.5 脚注 2），若误用 query 会虚高。
  4. **数据集版本与判据**：Oxford 用的是 subsample 后的 Overcast Summer（213 帧）/ Autumn Night（251 帧），GT 半径 25 m（Appendix A3, p.8）；Pitts-30k 若误用 250k 版本结果完全不同。**注意：本目录 README 写的 "Pitts250k / Tokyo24-7" 并不在论文的 12 个数据集里** —— 论文只用 Pitts-**30k**，Tokyo24-7 根本没出现，规划时要改。
  5. **随机性**：论文固定 seed 42；VLAD 的 k-means 初始化对结果有扰动。
- **阻塞风险**：
  - **中**：数据集下载器依赖外链，可能已失效；需先验证一条。
  - **中**：ViT-G14 的显存/时长，若本机无 ≥24 GB GPU 则只能跑子集，平均 R@1 无法复核。
  - **低**：权重与代码均公开，无 gated 内容。
  - **高（对项目目标而言）**：**「内容变化 split」不存在，必须自造**。论文给不出任何基线，我们造出来的数字**没有论文可对照** —— 只能拿静态条件（Baidu / Pitts-30k）的 75.2 / 87.7 当"变化前"锚点，自己测"变化后"。这部分必须写进报告的局限里。
