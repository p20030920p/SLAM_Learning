# 02-05 · HOV-SG — 论文报告值 Paper-reported baseline

| 项 Item | 内容 |
| :--- | :--- |
| 论文 | Hierarchical Open-Vocabulary 3D Scene Graphs for Language-Grounded Robot Navigation |
| Venue / 年 | 本地 PDF 为 **arXiv:2403.17846v2 [cs.RO]（2024-06-03）**，首页**未标注会议**。同批 PDF 中 DualMap（079）参考文献 [5] 与 Clio（083）参考文献 [51] 均记其为 **Robotics: Science and Systems (RSS), 2024**。本文件以 PDF 正文为准：PDF 内无 venue 声明 |
| 本地 PDF | `Localise/01_task_books/materials/papers_pdf/080_Hierarchical_Open_Vocabulary_3D_Scene.pdf`（结果表在第 **6–11** 页：TABLE I 在 p.6，TABLE II 在 p.7，TABLE III 在 p.8，TABLE IV 在 p.9，TABLE V / VI 在 p.10，TABLE VII / VIII 在 p.11；补充材料 p.14–20，TABLE S.1 / S.2 / S.3 在 p.15–16） |
| 官方代码 | PDF 内给出 `https://hovsg.github.io`（p.1 "We provide code and trial video data at"，p.10 "we make the code publicly available at"）。**PDF 内未出现 github.com 仓库 URL**（仓库 README 指向 `github.com/hovsg/HOV-SG`） |
| 任务 | 用 RGB-D + odometry，先做 open-vocabulary 的 3D segment-level 语义建图（SAM + CLIP），再自底向上构建 floor → room → object 三级场景图，并生成跨楼层 Voronoi 导航图，支持 "find the bean bag in the office on floor 1" 这类多级语言查询与真机导航 |
| 数据集 | **Replica**（office0–office4、room0–room2）与 **ScanNet**（scene0011_00、scene0050_00、scene0231_00、scene0378_00、scene0518_00）用于 open-vocab 3D 语义分割（TABLE I）与消融（TABLE VIII）；**HM3DSem**（Habitat-Matterport 3D Semantics，自录 8 个场景随机游走：00824、00829、00843、00861、00862、00873、00877、00890，含单层/双层/三层）用于场景图评测（TABLE II/III/IV/V/VII）；**真实世界**：Freiburg 一栋两层办公楼（Spot 四足 + Azure Kinect RGB-D + 3D LiDAR）用于 TABLE VI |
| 指标 | **3D 语义分割**（补充材料 eq. 1–3，逐点评测、把每个 GT 点用其 5 个最近邻预测点的多数标签赋值）：`mIOU = (1/N)Σ TPi/(TPi+FPi+FNi)`、`F-IOU = 1/Σni · Σ ni·TPi/(TPi+FPi+FNi)`（ni = 类别 i 的 GT 点数）、`mAcc = (1/N)Σ TPi/(TPi+FPi)`。**Acc_F**：楼层数预测正确率（阈值 0.5 m）。**Regions Precision / Recall**：沿用 Hydra [19] 的 region 分割指标。**Acc=**：预测房间类别与 GT 文本完全相等的比例；**Acc≈**：人工判定的语义正确（同义词也算对，用于缓解房间类别本身不可判定 + LLM 幻觉）。**AUCtop_k**（论文新提出）：top-k 准确率曲线下的面积，k 按标签集大小归一化；同时报 top5/top10/top25/top100/top250/top500 的具体准确率。**Retrieval-SR10 / Navigation-SR**：见下 |
| 硬件 | **论文未报告 GPU 型号与显存**。全文检索 `GPU`/`RTX`/`A100`/`V100`/`VRAM`/`NVIDIA`/`workstation` 均无硬件命中（唯一 NVIDIA 命中是致谢里的 "an academic grant from NVIDIA"）。论文对算力只给了**定性警告**：结论节写 "the construction process of HOV-SG is **time-consuming, rendering the method unsuitable for real-time mapping**"，且 "necessitates a large number of hyperparameters"。**整个 PDF 未给出任何建图耗时数字 —— 未找到** |

## 论文报告的数字 Reported numbers

> 说明：**HOV-SG (ours)** = 论文自身方法；**ConceptFusion [13]、ConceptGraphs [14]、VLMaps [10]、Hydra [19]、MinkowskiNet [50]** = 对比方法。TABLE I 中 MinkowskiNet 是 privileged 全监督上界。

| 出处（表/图 + 页） | 数据集 / 场景 | 方法 | 指标 | 数值 |
| :--- | :--- | :--- | :--- | ---: |
| **TABLE I, p.6** | **Replica（8 场景）** | **HOV-SG (ours), ViT-H-14** | **mIOU / F-mIOU / mAcc** | **0.231 / 0.386 / 0.304** |
| TABLE I, p.6 | Replica | HOV-SG (ours), OVSeg | mIOU / F-mIOU / mAcc | 0.144 / 0.255 / 0.212 |
| TABLE I, p.6 | Replica | ConceptGraphs [14], ViT-H-14（对比） | mIOU / F-mIOU / mAcc | 0.18 / 0.23 / 0.30 |
| TABLE I, p.6 | Replica | ConceptGraphs [14], OVSeg（对比） | mIOU / F-mIOU / mAcc | 0.13 / 0.27 / 0.21 |
| TABLE I, p.6 | Replica | ConceptFusion [13], ViT-H-14（对比） | mIOU / F-mIOU / mAcc | 0.10 / 0.18 / 0.17 |
| TABLE I, p.6 | Replica | ConceptFusion [13], OVSeg（对比） | mIOU / F-mIOU / mAcc | 0.10 / 0.21 / 0.16 |
| **TABLE I, p.6** | **ScanNet（5 场景）** | **HOV-SG (ours), ViT-H-14** | **mIOU / F-mIOU / mAcc** | **0.222 / 0.303 / 0.431** |
| TABLE I, p.6 | ScanNet | HOV-SG (ours), OVSeg | mIOU / F-mIOU / mAcc | 0.214 / 0.258 / 0.420 |
| TABLE I, p.6 | ScanNet | ConceptGraphs [14], ViT-H-14（对比） | mIOU / F-mIOU / mAcc | 0.16 / 0.20 / 0.28 |
| TABLE I, p.6 | ScanNet | ConceptGraphs [14], OVSeg（对比） | mIOU / F-mIOU / mAcc | 0.15 / 0.18 / 0.23 |
| TABLE I, p.6 | ScanNet | ConceptFusion [13], ViT-H-14（对比） | mIOU / F-mIOU / mAcc | 0.11 / 0.12 / 0.21 |
| TABLE I, p.6 | ScanNet | ConceptFusion [13], OVSeg（对比） | mIOU / F-mIOU / mAcc | 0.08 / 0.11 / 0.15 |
| TABLE I, p.6 | ScanNet | **MinkowskiNet [50]**（privileged 全监督上界） | mIOU / F-mIOU / mAcc | 0.42 / 0.47 / 0.56 |
| **TABLE II, p.7** | **HM3DSem（8 场景）** | **HOV-SG (ours)** | **Acc_F / Regions Precision / Recall** | **100% / 84.10% / 83.59%** |
| TABLE II, p.7 | HM3DSem | Hydra [19]（对比） | Acc_F / Regions Precision / Recall | – / 86.18% / 77.55% |
| **TABLE III, p.8** | **HM3DSem（8 场景）** | **HOV-SG（view embeddings）** | **Acc= / Acc≈** | **73.93% / 84.10%** |
| TABLE III, p.8 | HM3DSem | GPT-3.5 w/ GT object categories（privileged） | Acc= / Acc≈ | 66.89% / 81.49% |
| TABLE III, p.8 | HM3DSem | GPT-4 w/ GT object categories（privileged） | Acc= / Acc≈ | 79.86% / 84.25% |
| TABLE III, p.8 | HM3DSem | GPT-3.5 w/ predicted object categories（unprivileged） | Acc= / Acc≈ | 28.48% / 42.95% |
| TABLE III, p.8 | HM3DSem | GPT-4 w/ predicted object categories（unprivileged） | Acc= / Acc≈ | 59.47% / 62.55% |
| **TABLE IV, p.9** | **HM3DSem（8 场景，1624 类）** | **HOV-SG (ours)** | **top5 / top10 / top25 / top100 / top250 / top500 / AUCtop_k** | **18.43 / 25.73 / 36.41 / 56.46 / 69.95 / 80.86 / 84.88** |
| TABLE IV, p.9 | HM3DSem | ConceptGraphs [14]（对比） | top5 / top10 / top25 / top100 / top250 / top500 / AUCtop_k | 18.11 / 24.01 / 33.00 / 55.17 / 70.85 / 81.55 / 84.07 |
| TABLE IV, p.9 | HM3DSem | VLMaps [10]（对比） | top5 / top10 / top25 / top100 / top250 / top500 / AUCtop_k | 0.05 / 0.17 / 0.54 / 15.32 / 26.01 / 40.02 / 56.20 |
| TABLE V, p.10 | HM3DSem, query type **(o, r, f)**（40.63 trials 均值） | ConceptGraphs [14]（对比，加 privileged floor 信息） | Retrieval-SR10 | 16.31% |
| **TABLE V, p.10** | HM3DSem, query type **(o, r, f)** | **HOV-SG (ours)** | **Retrieval-SR10 / Navigation-SR** | **28.00% / 37.32%** |
| TABLE V, p.10 | HM3DSem, query type **(o, r)**（34.88 trials 均值） | ConceptGraphs [14]（对比） | Retrieval-SR10 | 29.26% |
| **TABLE V, p.10** | HM3DSem, query type **(o, r)** | **HOV-SG (ours)** | **Retrieval-SR10 / Navigation-SR** | **31.48% / 40.41%** |
| **TABLE VI, p.10** | **真实世界两层办公楼 — Object 查询（41 trials）** | **HOV-SG (ours)** | **Graph Querying 成功数 / SR；Goal Navigation 成功数 / SR** | **29 / 70.7%；23 / 56.1%** |
| TABLE VI, p.10 | 真实世界 — Room 查询（9 trials） | HOV-SG (ours) | 同上 | 5 / 55.6%；5 / 55.6% |
| TABLE VI, p.10 | 真实世界 — Floor 查询（2 trials） | HOV-SG (ours) | 同上 | 2 / 100%；2 / 100% |
| TABLE VII, p.11 | HM3DSem 8 场景 | VLMaps [10]（对比） | 表示存储大小合计 (MB) | 6068 |
| TABLE VII, p.11 | HM3DSem 8 场景 | ConceptGraphs [14]（对比） | 表示存储大小合计 (MB) | 1638 |
| **TABLE VII, p.11** | **HM3DSem 8 场景** | **HOV-SG (ours)** | **表示存储大小合计 (MB)** | **1493** |
| TABLE VII, p.11 | HM3DSem 单场景（HOV-SG） | HOV-SG (ours) | MB（00824/00829/00843/00861/00862/00873/00877/00890） | 143 / 99 / 125 / 225 / 479 / 129 / 131 / 162 |
| TABLE VIII, p.11 | Replica | **HOV-SG (ours) 完整版** | mIOU / F-mIoU / mAcc | 0.231 / 0.386 / 0.304 |
| TABLE VIII, p.11 | Replica | w/o DBSCAN（消融） | mIOU / F-mIoU / mAcc | 0.212 / 0.340 / 0.290 |
| TABLE VIII, p.11 | Replica | w/o L-CLIP（消融） | mIOU / F-mIoU / mAcc | 0.136 / 0.178 / 0.170 |
| TABLE VIII, p.11 | Replica | w/o M-CLIP（消融） | mIOU / F-mIoU / mAcc | 0.215 / 0.337 / 0.298 |
| Fig. S.2, p.15 | HM3DSem 场景 00824 | HOV-SG | AUCtop_k（单场景曲线值） | 86.52 |
| TABLE S.1, p.15 | HM3DSem 逐场景 | HOV-SG (ours) | Acc_F 区间 / Regions Precision 区间 / Recall 区间 | 1.0（全部 8 场景）/ 72.65–95.63% / 67.71–92.30% |
| TABLE S.1, p.15 | HM3DSem 逐场景 | Hydra [19]（对比） | Regions Precision 区间 / Recall 区间 | 77.23–96.87% / 62.82–88.86% |
| §IV-D 正文, p.11 | HM3DSem | HOV-SG vs VLMaps | 表示大小降幅 | **减少约 75%**（摘要亦写 "a 75% reduction in representation size"） |
| §IV-B4 正文, p.9 | HM3DSem | HOV-SG vs ConceptGraphs（(o,r,f) 查询） | Retrieval-SR10 提升 | **+11.69%** |
| §IV-B4 正文, p.9 | HM3DSem | HOV-SG vs ConceptGraphs（(o,r) 查询） | Retrieval-SR10 提升 | **+2.2%** |

## 关键结论（论文自己声称的）

- **Open-vocabulary 语义分割大幅领先同期开放词表基线**：TABLE I 上 Replica `mIOU 0.231 / F-mIOU 0.386 / mAcc 0.304`（ConceptGraphs 0.18/0.23/0.30、ConceptFusion 0.10/0.18/0.17），ScanNet `mIOU 0.222 / F-mIOU 0.303 / mAcc 0.431`。论文归因于两点：合并 segment 特征时用 **DBSCAN 求主导特征**（而非 ConceptGraphs 的均值）、以及融合 "带背景的 masked image" 与 "无背景的 masked image" 两路 CLIP embedding（TABLE VIII 证明两者都去掉会掉到 mIOU 0.136 / 0.215）。
- **层级结构带来检索增益**：TABLE V 上 HOV-SG 在 (o, r, f) 三级查询的 Retrieval-SR10 = **28.00%** 对比 ConceptGraphs 16.31%（**+11.69%**）；(o, r) 查询 31.48% vs 29.26%（**+2.2%**）。导航成功率（37.32% / 40.41%）甚至高于检索成功率，论文解释为"机器人常能走到预测物体附近，虽然 mask 不完美"。
- **表示紧凑**：TABLE VII 上 HOV-SG 8 场景合计 **1493 MB**（ConceptGraphs 1638 MB、VLMaps 6068 MB），相对稠密表示 VLMaps **减少约 75%**。
- **真机多楼层语言导航可行**：真实两层办公楼中，41 次 object 查询检索 SR **70.7%**、导航 SR **56.1%**；room 查询 9 次 55.6%/55.6%；floor 查询 2 次 100%/100%。房间检索失败主要来自 "meeting room / seminar room / dining room" 视觉相似。
- **楼层判定 100% 正确**：TABLE II 的 Acc_F = **100%**（单层与多层场景），region 分割 precision 84.10% / recall 83.59%，recall 明显高于 Hydra 的 77.55%（precision 略低 86.18%）。

## 跨会话身份 / 地图修订：论文报告了什么

**论文未报告。完全没有。**

HOV-SG 不只是"没测"，而是**明确声明不支持动态环境**。结论节（p.11）原句：

> "the construction process of HOV-SG is **time-consuming, rendering the method unsuitable for real-time mapping**. Furthermore, it **assumes a static environment and thus cannot handle dynamic environments**. Future research directions may involve developing an open-vocabulary dynamic representation of the environment..."

我为此检索的关键词（全 20 页，含补充材料）：`cross-session`、`multi-session`、`across session`、`revisit`、`second visit`、`repeat visit`、`identity`、`re-identify`、`reidentify`、`same object`、`change detection`、`map maintenance`、`map update`、`relocaliz`、`long-term`。**全部零命中**（唯一沾边的是 §S.1-B "Semantic Localization"，用粒子滤波在图中做 floor/room 级定位，10 帧内收敛，属于单会话内的定位，且同样是**无数字的定性描述**）。

因此：
- **无跨会话物体身份指标**（没有 "同一物体在多次访问间保持同一 ID" 的评测）。
- **无地图修订/编辑指标**（没有 "物体没动但标签应改" 的评测，也没有物体移动后的重定位成功率）。
- **无建图耗时数字**（论文只说 "time-consuming"，连"几小时"这种量级都没给）。

这一条对我们的课题是**强 gap 证据**：HOV-SG 是这个方向里语义层级做得最完整的系统之一，却把动态环境整个划到 future work。

## 对我们的复现意味着什么

- **可复现的前提**：
  - **GPU（硬性，且需求很可能比 DualMap 更高）**：论文**未报告硬件**，但系统要跑 SAM（生成所有 3D segment 的 mask）+ 三种 CLIP 编码（global RGB、masked-with-background、masked-without-background，ViT-H-14，1024 维特征）+ DBSCAN 聚类。TABLE VII 显示单场景表示就有 99–479 MB 的特征存储，**建图过程需要处理全场景的逐像素 CLIP 特征**，属于本批四篇里计算最重的一类。**本机无 GPU → 完全阻塞**。
  - **数据**：Replica 与 ScanNet 可直接下载；**HM3DSem 需要自录 RGB-D 随机游走**（论文是自己录的 8 个场景）+ Matterport 的 access agreement；真实世界实验（Spot + Azure Kinect + LiDAR + FAST-LIO2）无法复现。
  - **LLM 依赖**：层级查询解析用 **GPT-3.5**，房间分类基线用 GPT-3.5 / GPT-4 —— TABLE III / V 的部分结果依赖付费 API（附录 p.15 已给出完整 few-shot prompt，这点对复现友好）。
  - **代码**：`https://hovsg.github.io`（README 指向 `github.com/hovsg/HOV-SG`）。
- **目标数字**（建议验收线，优先级从高到低）：
  1. **TABLE I, p.6, ScanNet**：`mIOU = 0.222`、`F-mIOU = 0.303`、`mAcc = 0.431`（ViT-H-14）——数据集最容易拿到，建议作为主验收线。
  2. **TABLE I, p.6, Replica**：`mIOU = 0.231`、`F-mIOU = 0.386`、`mAcc = 0.304`。
  3. **TABLE VII, p.11**：8 场景表示大小合计 `≈1493 MB`（检验表示紧凑性，且不依赖人工评测）。
  4. **TABLE IV, p.9**：`AUCtop_k = 84.88`（HM3DSem，需自录数据，优先级最低）。
- **对不上的可能原因**：
  - **DBSCAN 参数未给**：TABLE VIII 证明 DBSCAN 是最大的单点贡献（去掉后 mIOU 0.231→0.212），但论文未给 eps / min_samples，只能试。
  - **三种 CLIP embedding 的融合权重未给**（L-CLIP 与 M-CLIP 的加权和方式未具体化），而 TABLE VIII 显示去掉 L-CLIP 会掉到 mIOU 0.136 —— **这是最大的复现风险点**。
  - **CLIP backbone 版本**：主结果用 ViT-H-14（1024 维），另一组用 OVSeg 微调的 ViT-L-14，两组数字差很多，不能混用。
  - **点云评测的最近邻策略**："对每个 GT 点找 5 个最近邻预测点取多数标签" 是论文自定义的实现细节（p.6），换一种 assignment 就会得到不同的 mIoU。
  - **HM3DSem 的 8 个场景是论文自己录的随机游走**，帧序列不可复刻；GT 建图用 "accurate odometry 融合 RGB-D + panoptic 后体素化到 0.02 cm"（注意：原文写 "0.02 cm"，单位疑似笔误，应为 0.02 m 量级的体素）——这个体素尺寸本身就有歧义。
  - **Acc≈ 靠人工判定语义正确**（p.8 明确说 "we manually filter all outputs across the set of eight scenes"），本质不可重复。
  - **GPT-3.5/4 版本漂移**会改变 Acc=。
- **阻塞风险**：
  - **本机无 GPU → 完全阻塞**；且论文未给硬件与耗时，**连"需要多大卡"都无法从论文估计**，只能靠表 VII 的特征规模推断（预计不低于 DualMap 的 24 GB 级别）。
  - **HM3DSem 需要 Matterport access agreement + 自录数据**，TABLE II/III/IV/V/VII（论文一半以上的结果）全部建立在其上。
  - **论文自承 "not suitable for real-time mapping"**：即便复现出来，也无法给出有意义的"实时性"数字，这与我们项目里其它在线系统的对比会不对等。
  - **论文自承超参众多**（"necessitates a large number of hyperparameters"），但 PDF 里给全的只有 prompt，**关键数值超参（DBSCAN、CLIP 融合）缺失**，调参成本高。
  - 大量结果依赖人工评测（Acc≈）与付费 LLM（Acc=），不利于自动化验收。
