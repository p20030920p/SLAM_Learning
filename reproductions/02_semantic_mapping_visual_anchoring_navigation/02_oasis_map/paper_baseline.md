# 02-02 · OASIS-Map — 论文报告值 Paper-reported baseline

| 项 Item | 内容 |
| :--- | :--- |
| 论文 | OASIS-Map: Object-Level Change Detection in Multi-Session Mapping using Semantic Correspondence Matching |
| Venue / 年 | **arXiv:2607.14899v1 [cs.RO]，2026-07-16，under review**（Oxford, Dynamic Robot Systems Group；作者 Haedam Oh, Yifu Tao, Nived Chebrolu, Maurice Fallon） |
| 本地 PDF | `Localise/01_task_books/materials/papers_pdf/145_OASIS_Map.pdf`（表 I 在第 8 页，表 II/III 在第 9 页）—— 本仓库此前没有这篇，2026-10-05 从 arXiv 取回后入库 |
| 官方代码 | 项目页 https://dynamic.robots... （论文摘要给出）；截至取回时**仍未发布**（"Code Soon"），因此本复现只能按论文复现 |
| 任务 | 多会话物体级变化检测：用**稠密 patch 级语义对应**（DINO 特征互相关）判断场景哪里变了，并把物体**增量关联**到跨会话身份上，输出时空一致的物体级地图 |
| 数据集 | 三个真实场景：**3RScan**（物体被移动 indoor rearrangement）· **Car Park**（外观相似的车被替换）· **Outdoor Market**（大范围场景变化）。3RScan 是公开数据集，另两个是自采 |
| 指标 | 逐变化类别（static / appear-disappear / replaced / moved）的 **Precision / Recall / F1**；另有物体检测（TP/FN/FP, P/R/F1）与**跨会话物体关联**（表 III） |
| 硬件 | 论文未报告 |

## 论文报告的数字 Reported numbers

### 表 I（第 8 页）：3D 变化检测。`Obj.` = 方法是否表示物体，`Assoc.` = **是否维持跨会话物体身份**

| 出处 | 数据集 | 方法 | Obj. | Assoc. | Static P/R/F1 | Appear·Disappear P/R/F1 | Moved P/R/F1 |
| :--- | :--- | :--- | :-: | :-: | :--- | :--- | :--- |
| 表 I, p.8 | **3RScan** | LT-Mapper | ✗ | ✗ | 0.714 / 0.904 / **0.798** | 0.204 / 0.686 / 0.314 | – （无物体信息） |
| 表 I, p.8 | **3RScan** | ConceptGraphs | ✓ | ✗ | 0.686 / 0.476 / 0.562 | 0.177 / 0.362 / 0.238 | 0.359 / 0.272 / 0.309 |
| 表 I, p.8 | **3RScan** | Where's-my-glasses | ✓ | ✓ | 0.427 / 0.301 / 0.353 | 0.142 / 0.348 / 0.201 | 0.345 / 0.116 / 0.173 |
| 表 I, p.8 | **3RScan** | **OASIS-Map（本文）** | ✓ | ✓ | 0.761 / 0.587 / **0.663** | 0.195 / 0.314 / **0.241** | 0.699 / 0.236 / **0.353** |
| 表 I, p.8 | Car Park | **OASIS-Map（本文）** | ✓ | ✓ | 0.699 / 0.788 / **0.736** | 0.682 / 0.616 / **0.592** | N.A. |
| 表 I, p.8 | Car Park | **OASIS-Map, Replaced（本文）** | ✓ | ✓ | — | — | 0.924 / 0.732 / **0.783** |

> 摘要写的是 "**0.783 F1 on change detection in a car replacement scenario** in a car park and **0.667 F1 on moved object association in 3RScan**"。
> ⚠️ 注意 **0.667 与表 I 的 0.663 对不上**（差 0.004）：摘要说的是 "moved object *association*"，表 I 那一列是 moved 的检测 F1，
> 两者不是同一个量。引用时**必须写清楚是哪一个**，否则会像论文自己一样自相矛盾。

### 表 II（第 9 页）：3RScan 物体检测（S0 = 前一次会话，S1 = 重访）

| 出处 | 会话 | 方法 | TP | FN | FP | P | R | F1 |
| :--- | :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| 表 II, p.9 | S0 (N_gt=32) | ConceptGraphs | 21 | 11 | 13 | 0.618 | 0.656 | 0.636 |
| 表 II, p.9 | S0 | Where's-my-glasses | 22 | 10 | 21 | 0.512 | 0.688 | 0.587 |
| 表 II, p.9 | S0 | **OASIS-Map（本文）** | 29 | 3 | 21 | 0.580 | **0.906** | **0.707** |
| 表 II, p.9 | S1 (N_gt=21) | ConceptGraphs | 13 | 8 | 11 | 0.542 | 0.619 | 0.578 |
| 表 II, p.9 | S1 | Where's-my-glasses | 11 | 10 | 5 | **0.688** | 0.524 | **0.595** |
| 表 II, p.9 | S1 | **OASIS-Map（本文）** | 13 | 8 | 15 | 0.464 | 0.619 | 0.531 |

> **N_gt：S0 有 32 个物体，S1 只有 21 个。** 这个数与我们在本机那一对 3RScan 上算出的
> **32 个物体**（`results/ab_pair.json`）完全一致 —— 强烈提示 OASIS-Map 用的就是
> **我们手上这一对会话**（或同一 scene 的同一次 rescan）。若成立，我们的 A/B 协议与它的评测口径可以直接对齐。

## 关键结论（论文自己声称的）

- **跨会话身份（Assoc.=✓）是它相对 ConceptGraphs 的核心增量**：表 I 里 ConceptGraphs 是 `Assoc. ✗`，OASIS-Map 是 `✓`；
  表 III 专门测 "object identity is preserved between S0 and S1"。
- 3RScan 上它**静态物体 F1 最高（0.663）**，但 **moved 只有 0.353** —— 移动物体的检测是它自己承认的弱项。
- 它自述的弱点写在摘要里：*"reliable object association across revisits remains a key challenge, especially under
  **partial views, occlusion, and imperfect segmentation**"* —— 是**关联可靠性**，不是缺少"不确定"输出。
- 它的 3D 变化检测靠 **dense patch-level semantic correspondence**，不需要几何先验，因此在"外观相似的车被替换"这种
  几何上几乎无变化的场景里仍然有效（Replaced F1 0.783）。

## 跨会话身份 / 地图修订：论文报告了什么

**报告了，而且是它的主线。** 与 02-03 ConceptGraphs、02-05 HOV-SG、02-06 Clio 那三篇不同，
OASIS-Map 明确把 `Assoc.`（是否维持跨会话物体身份）当作对比维度列进表 I，并在表 III 单列一节评测。

→ 对我们的意义：**不能再把"缺少跨会话身份评测"当作空白点**。可用的差异点只剩任务书 §0.3 说的那条：
把**可观测性做成可标定的量**并**分层测量**（可观测性分层 F1 / 未观测区分率 / ECE），
并检验它的关联在低可观测性样本上是否真的可靠。

## 对我们的复现意味着什么

- **可复现的前提**：**代码未发布**，只能按论文复现；3RScan 数据可公开示例（本机已有 1 对，32 物体 —— 与它表 II 的 N_gt 一致）；
  另两个数据集（Car Park / Outdoor Market）是自采，**无下载途径**，那两列无法复现。
- **目标数字**：3RScan 上 **moved F1 = 0.353、static F1 = 0.663、S0 检测 F1 = 0.707**。
  这三个是我们在同一对会话上可以直接对标的数。
- **对不上的可能原因**：
  - 它的 GT 分割/关联口径未完全公开（"GT objects" 如何定义、重叠物体如何算）；
  - 3RScan 有 478 个场景，它只用了其中一个；若用的不是我们这一对，数字不可比；
  - 稠密对应的阈值（论文中的 confidence 阈值）未逐项给出。
- **阻塞风险**：代码未发布（硬阻塞）；Car Park / Outdoor Market 数据不可得（那两列永久不可复现）。
