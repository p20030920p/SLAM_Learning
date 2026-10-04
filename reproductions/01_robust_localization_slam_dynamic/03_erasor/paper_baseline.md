# 01-03 · ERASOR — 论文报告值 Paper-reported baseline

> ⚠️ **口径警告（必须转达）**：本目录 README.md 的复现对象是 **RA-L 2021 的原始 ERASOR**
> （arXiv:2103.04316，代码 LimHyungTae/ERASOR —— 这两个编号与地址**来自本目录 README.md，不来自本 PDF**）。但本任务指定的本地 PDF
> `055_ERASOR.pdf` 实际是它的后续工作 **ERASOR++**（arXiv:2403.05019）。
> 下面所有数字都来自 **ERASOR++ 这一篇**，它是 ERASOR++ 自报值，同时**同一张表里也给出了原始 ERASOR 的复现值**（作者声明按其开源代码复现）。
> 真正的原始 ERASOR 论文（RA-L 2021）的表格数字**不在本 PDF 中**，需要另找那篇 PDF 才能填。

| 项 Item | 内容 |
| :--- | :--- |
| 论文 | ERASOR++: Height Coding Plus Egocentric Ratio Based Dynamic Object Removal for Static Point Cloud Mapping |
| Venue / 年 | arXiv:2403.05019v1 [cs.CV]，2024-03-08；**PDF 未印任何会议/期刊名**（正文与页眉均无 venue，只有 arXiv 编号） |
| 本地 PDF | `Localise/01_task_books/materials/papers_pdf/055_ERASOR.pdf`（结果表在第 5–6 页：表 I 在第 5 页，表 II 在第 6 页；图 5、图 6 在第 6 页） |
| 官方代码 | **未在 PDF 中找到**（全文检索 "github" / "http" 无代码链接）。论文只说"the previous algorithm was replicated using its open source code"（用上一版 ERASOR 的开源代码做对比复现，p.5），未给出 URL |
| 任务 | 在 ERASOR 基础上做后处理动态点删除的改进：引入 Height Coding Descriptor（HCD），并加 Height Stack Test（HST）、Ground Layer Test（GLT）、Surrounding Points Test（SPT）三个判据 |
| 数据集 | **SemanticKITTI**（p.5 §IV-A）。**只用选定帧段**而非全序列：seq 00 = 4390–4530 帧、seq 01 = 150–250 帧、seq 02 = 860–950 帧、seq 05 = 2350–2670 帧、seq 07 = 630–820 帧。论文注明表中只记序列号，不记帧号范围 |
| 指标 | **PR（Preservation Rate）**："the ratio of preserved static points in all static points"，衡量静态点的保留（即 bad removal 的少发程度）；**RR（Rejection Rate）**："the ratio of removed dynamic points in all dynamic points"，衡量动态点删除效果。论文明确：**两者都是 voxel-wise 计算，voxel size = 0.2**。**F1 score**：PR 与 RR 的组合指标（论文原话 "F1 score is the combination metric of PR and RR"，未给公式） |
| 硬件 | PC，**2.2GHz cores、16GB RAM**，ROS [21]，Ubuntu 18.04（p.5 §IV 开头） |

## 论文报告的数字 Reported numbers

标注约定：**ERASOR++ = 论文自己的方法**；`ERASOR` = 论文按上一版开源代码复现的**基线**；`++ w/o ABC` = 去掉 HCD+GLT+HST 的消融；`++ w/o D` = 去掉 SPT 的消融（p.5 §IV-A 定义）。

### 表 I：KITTI 序列上的实验结果与对比（PDF p.5）

| 出处（表/图 + 页） | 数据集 / 序列 | 方法 | 指标 | 数值 |
| :--- | :--- | :--- | :--- | ---: |
| 表 I, p.5 | SemanticKITTI seq 00 | ERASOR（基线） | PR[%] / RR[%] / F1 / Avg. Time[s] | 92.1498 / 97.206 / 0.946104 / 0.125032 |
| 表 I, p.5 | SemanticKITTI seq 00 | **ERASOR++（本文）** | PR[%] / RR[%] / F1 / Avg. Time[s] | 96.8261 / 96.1009 / 0.964621 / 0.124875 |
| 表 I, p.5 | SemanticKITTI seq 00 | ++ w/o ABC（消融） | PR[%] / RR[%] / F1 / Avg. Time[s] | 95.8274 / 96.0592 / 0.959432 / 0.115372 |
| 表 I, p.5 | SemanticKITTI seq 00 | ++ w/o D（消融） | PR[%] / RR[%] / F1 / Avg. Time[s] | 93.5736 / 96.789 / 0.951542 / 0.135319 |
| 表 I, p.5 | SemanticKITTI seq 01 | ERASOR（基线） | PR[%] / RR[%] / F1 / Avg. Time[s] | 91.8967 / 94.5626 / 0.932106 / 0.132209 |
| 表 I, p.5 | SemanticKITTI seq 01 | **ERASOR++（本文）** | PR[%] / RR[%] / F1 / Avg. Time[s] | 98.9919 / 93.6401 / 0.962471 / 0.13711 |
| 表 I, p.5 | SemanticKITTI seq 01 | ++ w/o ABC（消融） | PR[%] / RR[%] / F1 / Avg. Time[s] | 97.3527 / 93.8679 / 0.955785 / 0.126481 |
| 表 I, p.5 | SemanticKITTI seq 01 | ++ w/o D（消融） | PR[%] / RR[%] / F1 / Avg. Time[s] | 94.9805 / 94.139 / 0.945579 / 0.143876 |
| 表 I, p.5 | SemanticKITTI seq 02 | ERASOR（基线） | PR[%] / RR[%] / F1 / Avg. Time[s] | 80.896 / 99.2045 / 0.891197 / 0.161044 |
| 表 I, p.5 | SemanticKITTI seq 02 | **ERASOR++（本文）** | PR[%] / RR[%] / F1 / Avg. Time[s] | 87.8949 / 98.9015 / 0.930739 / 0.135772 |
| 表 I, p.5 | SemanticKITTI seq 02 | ++ w/o ABC（消融） | PR[%] / RR[%] / F1 / Avg. Time[s] | 82.6932 / 99.2045 / 0.901995 / 0.154411 |
| 表 I, p.5 | SemanticKITTI seq 02 | ++ w/o D（消融） | PR[%] / RR[%] / F1 / Avg. Time[s] | 85.9189 / 98.9015 / 0.919542 / 0.13935 |
| 表 I, p.5 | SemanticKITTI seq 05 | ERASOR（基线） | PR[%] / RR[%] / F1 / Avg. Time[s] | 86.9621 / 97.9208 / 0.921167 / 0.121533 |
| 表 I, p.5 | SemanticKITTI seq 05 | **ERASOR++（本文）** | PR[%] / RR[%] / F1 / Avg. Time[s] | 96.5283 / 97.6666 / 0.970941 / 0.10012 |
| 表 I, p.5 | SemanticKITTI seq 05 | ++ w/o ABC（消融） | PR[%] / RR[%] / F1 / Avg. Time[s] | 91.2505 / 97.7049 / 0.943673 / 0.113161 |
| 表 I, p.5 | SemanticKITTI seq 05 | ++ w/o D（消融） | PR[%] / RR[%] / F1 / Avg. Time[s] | 94.4625 / 98.1019 / 0.962478 / 0.10433 |
| 表 I, p.5 | SemanticKITTI seq 07 | ERASOR（基线） | PR[%] / RR[%] / F1 / Avg. Time[s] | 93.4848 / 98.8887 / 0.961109 / 0.090536 |
| 表 I, p.5 | SemanticKITTI seq 07 | **ERASOR++（本文）** | PR[%] / RR[%] / F1 / Avg. Time[s] | 98.5774 / 98.6509 / 0.986141 / 0.101062 |
| 表 I, p.5 | SemanticKITTI seq 07 | ++ w/o ABC（消融） | PR[%] / RR[%] / F1 / Avg. Time[s] | 96.6388 / 98.768 / 0.976918 / 0.088366 |
| 表 I, p.5 | SemanticKITTI seq 07 | ++ w/o D（消融） | PR[%] / RR[%] / F1 / Avg. Time[s] | 97.583 / 98.6935 / 0.981351 / 0.105337 |

### 表 II：时间开销与 R-GPF 调用次数（PDF p.6）

| 出处（表/图 + 页） | 数据集 / 序列 | 方法 | 指标 | 数值 |
| :--- | :--- | :--- | :--- | ---: |
| 表 II, p.6 | SemanticKITTI seq 05 | ERASOR（基线） | R-GPF Count / Time[s] | 577.9 / 0.121533 |
| 表 II, p.6 | SemanticKITTI seq 05 | **ERASOR++（本文）** | R-GPF Count / Time[s] | 368.875 / 0.10012 |
| 表 II, p.6 | SemanticKITTI seq 07 | ERASOR（基线） | R-GPF Count / Time[s] | 531.632 / 0.090536 |
| 表 II, p.6 | SemanticKITTI seq 07 | **ERASOR++（本文）** | R-GPF Count / Time[s] | 390.053 / 0.101062 |

### 图（PDF p.6）

| 出处（表/图 + 页） | 数据集 / 序列 | 方法 | 指标 | 数值 |
| :--- | :--- | :--- | :--- | ---: |
| 图 6, p.6（正文 p.5 复述） | SemanticKITTI seq 05、07 | ERASOR vs ERASOR++ | PR–RR 随 frame skip interval 参数变化 | **只给了趋势曲线，未给表格数字（未找到具体数值）** |
| 图 3（caption）, p.4 | — | 原版 ERASOR 的 SRT | SRT 的高度差比值阈值 | **0.2**（原文 "threshold is a constant value and empirically set to 0.2 in [3]"） |

## 关键结论（论文自己声称的）

- **在所有 5 个序列上 PR 与 F1 都一致提升，RR 只轻微下降**：例如 seq 07 的 F1 从 0.961109 → **0.986141**，seq 05 从 0.921167 → **0.970941**，seq 01 的 PR 从 91.8967 → **98.9919**（表 I, p.5）。
- **seq 02 是唯一有明显缺陷的场景**：作者归因于 Z 轴位姿不确定性，PR 只有 87.8949（虽仍高于基线的 80.896）（正文 p.5）。
- **效率不降反升**：R-GPF 调用次数从 577.9 降到 **368.875**（seq 05），因此"equivalent or even faster execution time"；并称上一版 ERASOR 已比其他方法快至少十倍（表 II, p.6 + 正文 p.6 §IV-C）。
- **每一部分都有贡献**：消融后 PR 一致下降，"++ w/o ABC" 与 "++ w/o D" 都不如完整版，说明 HCD/HST/GLT 与 SPT 各自减少了不同类型的 bad removal（正文 p.6 §IV-D）。
- **外部参数 frame skip interval 会影响 PR/RR**，但 ERASOR++ 的结果始终位于高值一侧（图 6, p.6）。

## 对我们的复现意味着什么

- **可复现的前提**：
  - **需要 ROS + Ubuntu 18.04 语义的环境**（论文的跑测环境）；本仓库是 ROS 2 Jazzy，**必须另开 ROS 1 工作空间或用 docker**。
  - **论文没有给出 ERASOR++ 的代码地址**——按本 PDF 无法直接复现 ERASOR++（这是一个真实的可行性缺口）。可复现的是**基线 ERASOR**（README.md 记的 LimHyungTae/ERASOR）。
  - **SemanticKITTI 需注册下载**（标签 + 位姿），KITTI odometry 同样需注册。
  - 判据口径：PR/RR 是 **voxel-wise、voxel size = 0.2**；若我们按 DynamicMap_Benchmark 的点级 SA/DA/AA 评，**数字不可比**。
  - 必须用**指定帧段**：seq 00 = 4390–4530、01 = 150–250、02 = 860–950、05 = 2350–2670、07 = 630–820。帧段不同则数字不同。
- **目标数字**：若以本 PDF 为验收依据，**最稳的单点目标是 SemanticKITTI seq 00 上 ERASOR++ 的 PR / RR / F1 = 96.8261 / 96.1009 / 0.964621**（表 I, p.5），同一行旁边就有基线 ERASOR 的 92.1498 / 97.206 / 0.946104 可做交叉校验。
  **但要注意**：本目录真正要复现的 ERASOR（RA-L 2021）的目标数字应取那篇论文自己的表格，**本文件不含**。
- **对不上的可能原因**：
  - **版本错配**（最大风险）：目录里放的是 ERASOR++ 的 PDF，代码是 ERASOR 的代码；跑 ERASOR 代码去对 ERASOR++ 的数字必然对不上。**正确做法是明确我们复现的是哪一版**。
  - 位姿来源不同（论文用 SemanticKITTI 提供的位姿）；Z 轴位姿误差是作者自己承认影响 seq 02 的主因。
  - voxel size 0.2 与体素化方式（点落入体素的判定）差异。
  - 参数：论文说基线 ERASOR 参数"remained unchanged"，但**没有列出具体参数值**。
  - 硬件不同：论文是 2.2GHz 16GB 的机器，我们机器更快会显得"我们更快"，Time[s] 不能直接比。
  - 图上数字（图 6 的 PR–RR 曲线）**未找到表格数值**，无法作为验收点。
- **阻塞风险**：
  - **KITTI / SemanticKITTI 必须注册下载**（硬阻塞，需先申请账号）。
  - **数据体积**：SemanticKITTI + KITTI odometry raw 为**数十 GB 量级**（论文未给 GB 数，属我们侧估计）。
  - **ERASOR++ 无公开代码**（PDF 内未找到链接）：如果验收目标定为 ERASOR++ 的数字，则**在只有本 PDF 的情况下不可达成**，需先确认上游是否另有仓库。
  - ROS 1（Ubuntu 18.04 时代）与本仓库 ROS 2 Jazzy 的环境冲突，需独立容器化。

---

## 补：原始 ERASOR（RA-L 2021）论文报告值

**来源**：arXiv:2103.04316（RA-L 2021），2026-10-05 取回，存于
`Localise/01_task_books/materials/papers_pdf/069b_ERASOR_original_RA_L2021.pdf`。
这是本目录真正要复现的那一篇；上面几节全部是 ERASOR++。

| 项 | 内容 |
| :--- | :--- |
| 论文 | ERASOR: Egocentric Ratio of Pseudo Occupancy-based Dynamic Object Removal for Static 3D Point Cloud Map Building |
| Venue | **IEEE RA-L 2021**（Lim Hyungtae, Hwang Sungwon, Myung Hyun） |
| 代码 | https://github.com/LimHyungTae/ERASOR |
| 数据 | SemanticKITTI；**手动挑出"动态物体出现最多"的 top-5 帧**做定量评测（p.5 §III-A） |
| 指标 | **PR / RR / F1，全部 voxel-wise，voxel size = 0.2**（p.7 §III-B）。注意与任务书 §6 要用的点级 SA/DA/AA **不是一套口径** |

### 表 II（p.8）：SemanticKITTI 上与 SOTA 的对比

| 序列 | 方法 | PR [%] | RR [%] | F1 |
| :--- | :--- | ---: | ---: | ---: |
| **00** | OctoMap-0.05 [12] | 76.731 | 99.124 | 0.865 |
| **00** | OctoMap-0.2 [12] | 34.568 | 99.979 | 0.514 |
| **00** | Peopleremover [14] | 37.523 | 89.116 | 0.528 |
| **00** | Removert RM3 [15] | 85.502 | 99.354 | 0.919 |
| **00** | Removert RM3+RV1 [15] | 86.829 | 90.617 | 0.887 |
| **00** | **ERASOR（本文）** | **93.980** | **97.081** | **0.955** |
| 01 | **ERASOR（本文）** | 91.487 | 95.383 | 0.934 |
| 02 | **ERASOR（本文）** | 87.731 | 97.008 | 0.921 |
| 05 | **ERASOR（本文）** | 88.730 | 98.262 | 0.933 |
| 07 | **ERASOR（本文）** | 90.624 | 99.271 | 0.948 |
| 07 | Removert RM3 [15] | 80.689 | 98.822 | 0.888 |
| 07 | Removert RM3+RV1 [15] | 82.038 | 95.504 | 0.883 |

### 表 III（p.8）：单次迭代耗时（SemanticKITTI seq 01）

| 方法 | Runtime/iteration [s] |
| :--- | ---: |
| OctoMap [12] | 1.077 |
| Peopleremover [14] | 1.000 |
| Removert [15] | 0.8307 |
| **ERASOR（本文）** | **0.0732** |

### 这一节带来的两个新结论

1. **验收目标数字确定了**：本目录应复现的是 **SemanticKITTI seq 00 的 PR / RR / F1 = 93.980 / 97.081 / 0.955**（表 II, p.8），
   voxel size 0.2。之前那一节写的 96.8261 / 96.1009 / 0.964621 是 **ERASOR++（2024）** 的数字，**不是**本目录的目标。
2. ⚠️ **同一个 ERASOR，两套口径下差了 27 个百分点**：
   - 它自己论文里（voxel-wise PR，SemanticKITTI 00）：**93.98**
   - 在 DynamicMap_Benchmark 里被重实现后（**点级 SA**，KITTI 00）：**66.70**（本目录 [01-01](../01_dynamicmap_benchmark/paper_baseline.md) 表 I、DUFOMap 论文表 I 都是这个数）
   - 而同一个基准里 Removert 的 SA 却是 **99.44**
   → 也就是说，**换一套评测口径，ERASOR 从"静态点保留最好的方法"变成"保留最差的之一"，而 Removert 反过来**。
   这正好是任务书 §6 并行实验 H1′ 要问的问题（排名是否稳定），而且它在这里**已经出现了一次**，且不依赖任何新数据。

