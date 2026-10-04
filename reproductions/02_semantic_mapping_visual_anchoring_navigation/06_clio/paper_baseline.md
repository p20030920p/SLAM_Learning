# 02-06 · Clio — 论文报告值 Paper-reported baseline

| 项 Item | 内容 |
| :--- | :--- |
| 论文 | Clio: Real-time Task-Driven Open-Set 3D Scene Graphs |
| Venue / 年 | **IEEE Robotics and Automation Letters (RA-L), 2024**，vol. 9, no. 10, pp. 8921–8928，DOI `10.1109/LRA.2024.3451395`（PDF 首页版权页直接给出；页眉写 "PREPRINT VERSION. ACCEPTED AUGUST, 2024"） |
| 本地 PDF | `Localise/01_task_books/materials/papers_pdf/083_Clio.pdf`（结果表在第 **7–8** 页与第 **13** 页：TABLE I 在 p.7，TABLE II / TABLE III 在 p.7，Fig. 6 grasp 分解在 p.8，TABLE IV 在 p.13 附录 H；正文 p.1–9，附录 p.10–13） |
| 官方代码 | `https://github.com/MIT-SPARK/Clio`（**PDF 正文明确给出**，p.4 §I 引言末 "…source at https://github.com/MIT-SPARK/Clio along with our…"）——本批四篇中**唯一在 PDF 里直接写了代码仓库 URL 的** |
| 任务 | 给定一串自然语言任务列表 Y，用 Information Bottleneck（Agglomerative IB）把 task-agnostic 的 3D 图元（FastSAM+CLIP 的物体段、Hydra 风格的 place 段）聚合成"任务相关"的物体与区域，实时在线构建层级式 open-set 3D scene graph |
| 数据集 | **自采 4 个数据集**：Office（33 个目标物体）、Apartment（28 个）、Cubicle（18 个）、Building（5 层大学楼，含机加工车间/教室/休息室/会议室/飞机库；仅做区域聚类与定性）。前三个数据集**人工标注了任务相关物体的 3D GT 包围盒**。传感器 Intel RealSense D455（附录 C）。**Replica**（8 场景）用于 closed-set 语义分割验证（TABLE II）。**真实机器人**：Boston Dynamics Spot + 机械臂/夹爪（TABLE 未列，见 Fig. 6 与 §VI-D）。**注意：Clio 未使用 HM3D / ScanNet** |
| 指标 | **osR (open-set Recall)**：对每个任务查询 n 个最优物体（n = 该任务 GT 相关物体数），报 `正确检测数 / GT 物体数`。**osP (open-set Precision)**：`总正确检测数 / 总检测数`，其中参与统计的检测须与某任务余弦相似度 ≥ 0.90 且为该物体最相似的任务。**strict**：估计包围盒包含 GT 包围盒质心 **且** GT 包围盒包含估计包围盒质心；**relaxed**：上述两个条件满足其一即可。**F1** = osR 与 osP 的调和平均。另报 **IOU**（top-n 最相关估计物体的平均 IoU）、**Objs**（估计物体总数，越小越紧凑）、**TPF [s]**（每帧处理时间）。**TABLE II** 用 `mAcc`（class-mean recall）与 `F-mIOU`（frequency-weighted mIoU），沿用 [8,9] 在 Replica 上的协议。**TABLE III** 用几何房间分割的 `Precision / Recall / F1`（沿用 Hydra [7] 的指标），5 次试验取均值并报标准差 |
| 硬件 | **主实验：NVIDIA RTX 3090 GPU + Intel i9-12900K CPU**（p.6 §VI-A，CLIP 用 **ViT-L/14**）。**附录 H**（TABLE IV，OpenCLIP **ViT-H-14**）同样 "Results generated with 3090 GPU and Intel i9-12900K"。**Spot 真机**：可机载的笔记本，**Intel i9-13950HX（24 核）+ 64 GB RAM + NVIDIA GeForce RTX 4090 Laptop GPU**（p.8 §VI-D）。**论文只给 GPU 型号，未给显存占用数值**（检索 `VRAM`/`GB of memory` 无命中；`64GB` 是 Spot 笔记本的系统 RAM） |

## 论文报告的数字 Reported numbers

> 说明：**Clio-batch / Clio-online（自家）** = 论文自身方法（batch = 全场景图元一次性聚类；online = 增量 IB，实时流式）；**CG [9]（ConceptGraphs）、Khronos [61]、Clio-Prim、以及 *-task 变体** = 论文复现/构造的对比方法。表中 "Shaded methods are informed by the list of tasks"，即 `CG-task / Khronos-task / Clio-*` 是任务感知方法。

### 主表：TABLE I, p.7（CLIP **ViT-L/14**，三个自采数据集，Strict / Relaxed 两组）

| 出处（表/图 + 页） | 数据集 / 场景 | 方法 | 指标 | 数值 |
| :--- | :--- | :--- | :--- | ---: |
| TABLE I, p.7 | **Cubicle** | **Clio-online（自家）** | Strict osR / osP / F1；Relaxed osR / osP / F1；IOU / Objs / TPF | **0.89 / 0.48 / 0.62**；0.89 / 0.48 / **0.63**；0.22 / 92 / 0.30 s |
| TABLE I, p.7 | Cubicle | Clio-batch（自家） | Strict osR / osP / F1；Relaxed osR / osP / F1；IOU / Objs / TPF | 0.83 / 0.33 / 0.47；1.0 / 0.40 / 0.57；0.17 / 48 / 0.31 s\* |
| TABLE I, p.7 | Cubicle | CG [9]（对比） | Strict osR / osP / F1；Relaxed F1；IOU / Objs / TPF | 0.44 / 0.17 / 0.25；0.39；0.06 / 181 / 2.0 s |
| TABLE I, p.7 | Cubicle | Khronos [61]（对比） | Strict osR / osP / F1；Relaxed F1；IOU / Objs / TPF | 0.78 / 0.12 / 0.21；0.20；0.17 / 628 / 0.31 s |
| TABLE I, p.7 | Cubicle | Clio-Prim（消融基线） | Strict osR / osP / F1；Relaxed F1；IOU / Objs / TPF | 0.72 / 0.09 / 0.16；0.17；0.18 / 1070 / 0.28 s |
| TABLE I, p.7 | Cubicle | CG-task（对比） | Strict osR / osP / F1；Relaxed F1；IOU / Objs / TPF | 0.44 / 0.38 / 0.41；0.55；0.06 / 26 / 2.0 s |
| TABLE I, p.7 | Cubicle | Khronos-task（对比） | Strict osR / osP / F1；Relaxed F1；IOU / Objs / TPF | 0.78 / 0.14 / 0.24；0.24；0.17 / 133 / 0.31 s |
| TABLE I, p.7 | **Office** | **Clio-online（自家）** | Strict osR / osP / F1；Relaxed osR / osP / F1；IOU / Objs / TPF | **0.55 / 0.65 / 0.60**；0.61 / 0.69 / **0.65**；0.12 / 49 / 0.29 s |
| TABLE I, p.7 | Office | Clio-batch（自家） | Strict osR / osP / F1；Relaxed osR / osP / F1；IOU / Objs / TPF | 0.64 / 0.45 / 0.53；0.76 / 0.55 / 0.64；0.13 / 84 / 0.30 s\* |
| TABLE I, p.7 | Office | CG [9]（对比） | Strict osR / osP / F1；Relaxed F1；IOU / Objs / TPF | 0.24 / 0.09 / 0.13；0.25；0.07 / 751 / 8.1 s |
| TABLE I, p.7 | Office | CG-task（对比） | Strict F1；Relaxed F1；Objs / TPF | 0.25；0.50；40 / 8.1 s |
| TABLE I, p.7 | Office | Khronos [61]（对比） | Strict F1；Relaxed F1；Objs / TPF | 0.35；0.36；1202 / 0.31 s |
| TABLE I, p.7 | Office | Clio-Prim（消融基线） | Strict F1；Relaxed F1；Objs / TPF | 0.29；0.30；1883 / 0.27 s |
| TABLE I, p.7 | **Apartment** | **Clio-online（自家）** | Strict osR / osP / F1；Relaxed osR / osP / F1；IOU / Objs / TPF | **0.35 / 0.31 / 0.33**；0.52 / 0.42 / 0.46；0.07 / 99 / 0.26 s |
| TABLE I, p.7 | Apartment | Clio-batch（自家） | Strict osR / osP / F1；Relaxed osR / osP / F1；IOU / Objs / TPF | 0.52 / 0.34 / 0.41；0.72 / 0.45 / 0.55；0.11 / 90 / 0.23 s\* |
| TABLE I, p.7 | Apartment | CG [9]（对比） | Strict F1；Relaxed F1；IOU / Objs / TPF | 0.23；0.35；0.07 / 339 / 2.2 s |
| TABLE I, p.7 | Apartment | Khronos [61]（对比） | Strict F1；Relaxed F1；Objs / TPF | 0.14；0.21；1093 / 0.26 s |
| TABLE I, p.7 | Apartment | Khronos-task（对比） | Strict F1；Relaxed F1；IOU / Objs / TPF | 0.22；0.32；0.11 / 162 / 0.26 s |

\* 该行的 TPF 是 **Clio-batch 的"总耗时按图像帧数归一化"**（脚注原文：Total time for Clio-batch normalized by number of images）；**batch 模式对整图只跑一次聚类，约需 30 秒**，故不适合在线使用。

### TABLE II, p.7 — Closed-set 语义分割（Replica，8 场景）

| 出处（表/图 + 页） | 数据集 / 场景 | 方法 | 指标 | 数值 |
| :--- | :--- | :--- | :--- | ---: |
| TABLE II, p.7 | Replica 8 场景 | **Clio-batch（自家）** | **mAcc / F-mIOU** | **37.95 / 36.98** |
| TABLE II, p.7 | Replica 8 场景 | ConceptGraphs [9]（对比，数值取自 [9]） | mAcc / F-mIOU | 40.63 / 35.95 |
| TABLE II, p.7 | Replica 8 场景 | ConceptFusion [8]（对比） | mAcc / F-mIOU | 24.16 / 31.31 |
| TABLE II, p.7 | Replica 8 场景 | ConceptFusion [8] + SAM（对比） | mAcc / F-mIOU | 31.53 / 38.70 |
| TABLE II, p.7 | Replica 8 场景 | OpenMask3D [50]（对比） | mAcc / F-mIOU | 39.54 / 49.26 |
| TABLE II, p.7 | Replica 8 场景 | ConceptGraphs-Detector [9]（对比） | mAcc / F-mIOU | 38.72 / 35.82 |
| TABLE II, p.7 | Replica 8 场景 | MaskCLIP [32]（对比） | mAcc / F-mIOU | 4.53 / 0.94 |
| TABLE II, p.7 | Replica 8 场景 | Mask2former [33] + Global CLIP feat（对比） | mAcc / F-mIOU | 10.42 / 13.11 |

### TABLE III, p.7 — 几何房间分割（5 次试验均值 ± 标准差）

| 出处（表/图 + 页） | 数据集 / 场景 | 方法 | 指标 | 数值 |
| :--- | :--- | :--- | :--- | ---: |
| TABLE III, p.7 | Apartment | Hydra [7]（对比，纯几何） | Precision / Recall / F1 | 0.93 ± 0.01 / 0.87 ± 0.01 / 0.90 ± 0.00 |
| TABLE III, p.7 | Apartment | Clio (closest) | Precision / Recall / F1 | 0.87 ± 0.06 / 0.78 ± 0.02 / 0.82 ± 0.01 |
| TABLE III, p.7 | Apartment | **Clio (average)（自家）** | Precision / Recall / F1 | **0.98 ± 0.02 / 0.54 ± 0.00 / 0.69 ± 0.00** |
| TABLE III, p.7 | Office | Hydra [7]（对比） | Precision / Recall / F1 | 0.61 ± 0.03 / 0.84 ± 0.03 / 0.70 ± 0.01 |
| TABLE III, p.7 | Office | Clio (closest) | Precision / Recall / F1 | 0.67 ± 0.03 / 0.79 ± 0.01 / 0.72 ± 0.01 |
| TABLE III, p.7 | Office | **Clio (average)（自家）** | Precision / Recall / F1 | 0.73 ± 0.01 / 0.80 ± 0.00 / **0.76 ± 0.01** |
| TABLE III, p.7 | Building | Hydra [7]（对比） | Precision / Recall / F1 | 0.87 ± 0.01 / 0.71 ± 0.02 / 0.78 ± 0.01 |
| TABLE III, p.7 | Building | Clio (closest) | Precision / Recall / F1 | 0.72 ± 0.04 / 0.82 ± 0.01 / 0.77 ± 0.02 |
| TABLE III, p.7 | Building | **Clio (average)（自家）** | Precision / Recall / F1 | 0.79 ± 0.02 / 0.84 ± 0.01 / **0.81 ± 0.01** |

### TABLE IV, p.13（附录 H）— OpenCLIP **ViT-H-14** 复跑（仅 Clio-batch，因算力更高不跑 online）

| 出处（表/图 + 页） | 数据集 / 场景 | 方法 | 指标 | 数值 |
| :--- | :--- | :--- | :--- | ---: |
| TABLE IV, p.13 | Cubicle | **Clio-batch（自家）** | Strict osR / osP / F1；Relaxed osR / osP / F1；IOU / Objs / TPF | 0.78 / 0.28 / 0.41；0.94 / 0.31 / 0.47；0.17 / 96 / 1.16 s\* |
| TABLE IV, p.13 | Cubicle | CG [9]（对比） | Strict F1；Relaxed F1；Objs / TPF | 0.46；0.65；231 / 3.15 s |
| TABLE IV, p.13 | Office | **Clio-batch（自家）** | Strict osR / osP / F1；Relaxed F1；IOU / Objs / TPF | 0.58 / 0.35 / **0.44**；0.57；0.12 / 224 / 1.15 s\* |
| TABLE IV, p.13 | Office | CG [9]（对比） | Strict F1；Relaxed F1；Objs / TPF | 0.20；0.33；908 / 12.33 s |
| TABLE IV, p.13 | Apartment | **Clio-batch（自家）** | Strict F1；Relaxed F1；IOU / Objs / TPF | 0.23；0.40；0.10 / 222 / 1.01 s\* |
| TABLE IV, p.13 | Apartment | CG [9]（对比） | Strict F1；Relaxed F1；Objs / TPF | 0.18；0.29；908 / 3.54 s |

附录 H 说明：ViT-H-14 对相关/不相关配对都会给出更高余弦相似度，因此把 null task 值与阈值 **α 从 0.23 提到 0.26**（对 Clio、Khronos-task、ConceptGraphs-task 一致）。

### Fig. 6, p.8 — Spot 真机抓取（21 次抓取尝试）

| 出处（图 + 页） | 数据集 / 场景 | 方法 | 指标 | 数值 |
| :--- | :--- | :--- | :--- | ---: |
| Fig. 6, p.8 | Spot 真机（两房间 + 走廊） | Clio | Success（含 Full + Partial） | **71.4%** |
| Fig. 6, p.8 | Spot 真机 | Clio | Failure | 28.6% |
| Fig. 6, p.8 | Spot 真机 | Clio | Full Success | 38.1% |
| Fig. 6, p.8 | Spot 真机 | Clio | Partial Success | 33.3% |
| Fig. 6, p.8 | Spot 真机 | Clio | Success (retry) | 14.3% |
| Fig. 6, p.8 | Spot 真机 | Clio | Spot Failure / Planning Issue / Navigation Issue / Detection Failure / Wrong Object | 19.0% / 23.8% / 14.3% / 9.5% / 4.8% |
| §VI-D 正文, p.8 | Spot 真机 | Clio | 抓取成功率（论文文字表述） | "**57%** success rate for the grasps"，"**71%** success rate if we disregard the cases where Spot failed to actually grasp a correctly identified object" |
| §VI-D 正文, p.8 | Spot 真机 | Clio | 选错目标的次数 | **仅 1 次**（"Clio was only unable to select the correct target object in the scene graph once"），对应 Fig. 6 的 Wrong Object 4.8% |

> **歧义提示（复现时需注意）**：Fig. 6 中 "Success 71.4% / Failure 28.6%" 两个主分支下的各个子类百分比**加起来不闭合**（Failures 子项 19.0+23.8+14.3+9.5+4.8 = 71.4%，该列与主分支标签的层级关系在 PDF 排版中不明确）。按 21 次试验折算，1 次 = 4.76%，只有 Wrong Object 4.8% 与 Navigation Issue 14.3%（3 次）能干净对上。正文的 "57%" 也无法由 38.1% + 14.3% 直接得出。**建议以正文的 57% / 71% 两个数字作为对外引用口径，Fig. 6 的子项仅作定性归因。**

## 关键结论（论文自己声称的）

- **任务驱动的 IB 聚类能在大幅压缩地图的同时提升精度**：TABLE I 上任务感知方法保留的物体数少一个数量级（Office 里 Clio-online `Objs = 49` vs Clio-Prim `1883`、CG `751`），同时 osP 显著提升；论文总结 Clio-batch / Clio-online "ranking first or second in all but 2 cases"（例外是 Office 的 IOU 与 strict osR）。
- **实时性比 ConceptGraphs 快约 6 倍**：TPF 上 Clio ~0.26–0.30 s vs CG 2.0–8.1 s（Office 场景 0.29 s vs 8.1 s）；论文原句 "Clio is able to run in a fraction of a second and is around **6 times faster** than ConceptGraphs"。
- **closed-set 场景不退化**：TABLE II 上 Clio-batch `mAcc 37.95 / F-mIOU 36.98`，与 ConceptGraphs（40.63 / 35.95）相当；论文承认 OpenMask3D 的 F-mIOU 49.26 更高，但那需要完整 3D 重建，**不适合实时**。
- **区域（房间）聚类在语义房间上优于纯几何方法**：TABLE III 的 Office 场景 Clio (average) F1 **0.76** vs Hydra 0.70；Building **0.81** vs Hydra 0.78。但在 Apartment（几何上本就分明的房间）上 Hydra 反而更好（F1 0.90 vs 0.69），论文归因于 Clio 过分割。
- **真机可用**：Spot 上 21 次抓取尝试，正文给 **57%** 抓取成功率（排除 Spot 自身抓取失败后 **71%**），且"选错目标物体只发生了 1 次"，说明 scene graph 的检索环节本身很可靠。

## 跨会话身份 / 地图修订：论文报告了什么

**论文未报告。**

Clio 的增量（incremental）机制是**单次建图会话内**的：Algorithm 2 让 Agglomerative IB 只对"受最新测量影响的连通分量"重新聚类（eq. 6 的 re-weighted δ），目的是让**在线**建图跟得上图像流，而不是跨会话地维护/修订地图。全文检索 `cross-session`、`multi-session`、`across session`、`revisit`、`second visit`、`repeat visit`、`identity`、`re-identify`、`reidentify`、`same object`、`change detection`、`map maintenance`、`map update`、`relocaliz`、`long-term`，**均无跨会话实验或指标**。

唯一沾边的两处，都**不是**我们关心的东西：

1. **p.5 脚注 1**（原句）："Note that this threshold is only used to **re-identify and track segments over time**, while we use our task-driven clustering to group primitives." —— 这里 `θ_track`（配合最小 3D IoU γ）只是**帧间/时间窗 τ 内**的短期 track 关联（"if a track has not been associated for τ seconds, it is terminated"），属于同一会话内的跟踪，**论文未给 τ、θ_track、γ 的具体数值**，更没有任何跨会话 re-ID 指标。可用的数值只在对比方法描述里：Khronos 用 `θ_track = 0.7, γ = 0.4`，Clio-Prim 用 `θ_track = 0.9, γ = 0.6`。
2. **§VII Limitations 第三条**：Clio 会把"应该分成两个物体"的图元过聚类（fork vs knife 的例子）—— 这是**单会话内的粒度问题**，不是标签修订问题。

因此：
- **无跨会话物体身份指标**：没有"同一物体在多次访问间保持同一 ID"的成功率/一致性度量。
- **无地图修订/编辑指标**：没有"物体没动但标签应改"的评测，也没有物体被移动后的地图更新成功率。
- **无长期（multi-session / lifelong）实验**：所有 4 个自采数据集都是单次采集、单次建图。

（值得注意：Clio 的 TABLE I 里有 **IOU** 与 **Objs** 两个指标，前者衡量估计包围盒与 GT 的重合度，后者衡量地图紧凑度 —— 这两个是**最接近**"物体身份是否稳定"的代理量，但它们是在单次会话的最终地图上算的，不涉及时间维度。）

## 对我们的复现意味着什么

- **可复现的前提**：
  - **GPU（硬性）**：主实验 **RTX 3090（24 GB）**；Spot 机载用 **RTX 4090 Laptop GPU（16 GB）+ i9-13950HX + 64 GB RAM**。论文未给显存占用数值，但系统需同时跑 FastSAM + CLIP ViT-L/14（或 ViT-H-14），且声明能**实时在线**跑在笔记本级 GPU 上 —— 是本批四篇里**算力门槛描述得最具体**的一篇。**本机无 GPU → 完全阻塞**。
  - **数据**：**Office / Apartment / Cubicle / Building 四个数据集都是作者自采的**，PDF 未给出下载地址（代码仓库里是否附带需自行确认）；只有 **Replica**（用于 TABLE II）是公开数据集。这是复现的最大数据障碍 —— **TABLE I、III、IV 和 Fig. 6 全都建立在自采数据上**。
  - **GT 标注**：Office/Apartment/Cubicle 的物体 GT 3D 包围盒**人工标注**，论文未提供标注文件说明。
  - **依赖**：FastSAM [27] + CLIP [11] + 沿用 Khronos [61] 的 3D mesh 与 object primitive 重建 + Hydra [7] 的 place 子图（Generalized Voronoi Diagram）。注意 **Clio 完整复现等于同时复现 Khronos 与 Hydra 两个 MIT-SPARK 系统**，工程量远大于表面。
  - **超参**：`α = 0.23`（null task 阈值，房间聚类时设 α = 0 关闭）；ViT-H-14 时改为 `α = 0.26`。**δ̄（IB 压缩停止阈值）在 PDF 中未给出具体数值 —— 未找到**（检索 `δ̄` 全 13 页，只有符号定义："δ̄ regulates the amount of compression where a value of 0 returns the original set of primitives and a value of 1 returns fully merged primitives"）。**τ（track 超时秒数）、θ_track、γ 的 Clio 自身取值也未给出 —— 未找到**（只有对比方法的 0.7/0.4 与 0.9/0.6）。
  - **代码**：`https://github.com/MIT-SPARK/Clio`（PDF 内明确给出，MIT-SPARK 组织，配套 Hydra/Khronos 生态）。
- **目标数字**（建议验收线，优先级从高到低）：
  1. **TABLE II, p.7, Replica**：`Clio-batch mAcc = 37.95`、`F-mIOU = 36.98` —— **唯一建立在公开数据集上的数字**，应作为主验收线。
  2. **TABLE III, p.7**：若只做区域聚类，对齐 Office `F1 = 0.76 ± 0.01`、Building `F1 = 0.81 ± 0.01`（但需自采数据）。
  3. **TABLE I, p.7**：TPF 量级 —— Office `0.29 s` vs CG `8.1 s`（实时性是 Clio 最核心的卖点，且是唯一"不需自采数据即可验证方向"的指标）。
  4. **TABLE I, p.7**：Office `Clio-online strict F1 = 0.60 / relaxed F1 = 0.65`（需自采数据 + 人工 GT，优先级中等）。
- **对不上的可能原因**：
  - **CLIP backbone 差异被论文自己量化了**：ViT-L/14（TABLE I）与 OpenCLIP ViT-H/14（TABLE IV）结果差异明显（Office Clio-batch strict F1 0.53 vs 0.44），且 ViT-H-14 必须改 `α = 0.23 → 0.26`。**用错 backbone 或忘记同步改 α，结果必然对不上。**
  - **δ̄ 与 τ/θ_track/γ 缺失**：IB 的压缩程度和 track 的持续时长直接决定 Objs 与 osP，而**这四个关键超参论文都没给数值**。
  - **自采数据不可得**：Office/Apartment/Cubicle 的场景布局、光照、物体摆放、任务列表（附录 D–G 给全了任务列表，但场景本身没有）都无法复刻。
  - **osP 的 0.90 相似度门槛**是一个论文自定义的截断（"detections that have at least 90% cosine similarity score to a task"），换阈值会显著改变 osP。
  - **strict/relaxed 的判定依赖包围盒质心包含关系**，对 bbox 估计的微小差异很敏感 —— 这是为什么论文要同时报两套。
  - **FastSAM 的分割非确定性** + GPU 浮点差异 → track 关联与聚类结果逐帧漂移。
  - **TABLE II 的数值标注为 "Baseline results reported from [9]"**，即 Clio 直接引用了 ConceptGraphs 的数字而非自己重跑（对比 DualMap 是把基线全部重跑一遍的），**跨论文比较存在协议差异风险**。
- **阻塞风险**：
  - **本机无 GPU → 完全阻塞**（FastSAM + CLIP 需要实时的 GPU 推理）。
  - **四个自采数据集没有公开下载途径**（PDF 内未见数据链接）→ **TABLE I / III / IV / Fig. 6 全部不可复现**，只剩 TABLE II 的 Replica 部分可做。
  - **完整复现需要引入 Khronos + Hydra 两个外部系统**（3D mesh 重建、object primitive、广义 Voronoi 图），依赖链长、版本敏感。
  - **Spot 真机实验**（Fig. 6）显然无法复现。
  - 论文自带 DISTRIBUTION STATEMENT A / MIT Lincoln Laboratory 背景，**代码开源但数据与实验平台受机构限制**。
  - 论文自列限制：对 prompt 调参脆弱、"merging two primitives 时直接平均 CLIP 向量"、会把应分开的物体（fork/knife）过聚类、只支持简单单步任务 —— 这些正是我们"物体标签应改/身份应保持"课题要解决的问题，可作为对照引用。
