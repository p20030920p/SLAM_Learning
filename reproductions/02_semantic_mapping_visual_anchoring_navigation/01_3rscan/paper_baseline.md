# 02-01 · 3RScan / RIO — 论文报告值 Paper-reported baseline

> **本文件的定位**：只记录**原论文报告的数字**（复现目标）。
> 复现过程、工具链坑、A/B 协议、可观测性分层等**已在 [`README.md`](README.md) 与 [`work/protocol.md`](work/protocol.md) 中**，此处不重复，只在必要处交叉引用。
> 本目标**没有本地 PDF** —— 数据全部来自 arXiv 抓取（见「来源」）。

| 项 Item | 内容 |
| :--- | :--- |
| 论文 | RIO: 3D Object Instance Re-Localization in Changing Indoor Environments（论文即 3RScan 数据集的发布论文） |
| Venue / 年 | **ICCV 2019 (Oral)** |
| 来源 | **arXiv 抓取，无本地 PDF**。摘要页 <https://arxiv.org/abs/1908.06109>；正文 PDF <https://arxiv.org/pdf/1908.06109v1>（**v1, 15 页**，含 supplementary）。已 `pdftotext -layout` 逐页核对。**表页码**：Table 1 **p.3**、Table 2 **p.4**、Table 3 **p.7**、Table 4 & 5 **p.8**、Table 6 & 7 **p.12（supplementary）** |
| 官方代码 | 项目页 <https://waldjohannau.github.io/RIO/>（论文首页脚注给出）；数据集读取工具 <https://github.com/WaldJohannaU/3RScan>。**论文本身未给出算法代码仓库链接**，仅发布数据 + benchmark server。后续扩展 benchmark 见 <https://github.com/WaldJohannaU/RIO10>（**该仓库数字本文件未核对**） |
| 任务 | **3D 物体实例重定位（RIO）**：给定源扫描（reference scan）中的一个或多个**已分割物体**，估计它们在同一环境**另一个时间点**的扫描（re-scan）中的**对应 6DoF 位姿**。要求对「物体被移动/移除/新增」以及「部分观测」鲁棒 |
| 数据集 | **3RScan**（本文自己发布，1482 scans / 478 scenes） |
| 指标 | **① 重定位（Table 4/5）**：`Recall` = 平移+旋转误差同时低于阈值的物体占比（**平均 % 正确预测**），两档阈值 **t ≤ 10 cm & r ≤ 10°** 与 **t ≤ 20 cm & r ≤ 20°**；`MRE` = Median Rotation Error（度）；`MTE` = Median Translation Error（米）。**评测时按物体的对称性折算**（§3.4, p.4）<br>**② 关键点匹配（Table 3）**：`F1`、`Accuracy`、`Precision`、`FPR`、`ER`（均在 95% recall 处），以及 `Top-1/3/5/10` = 在 50 个随机负样本中正样本排第一/前三/前五/前十的比例 |
| 硬件 | **未找到**。全文 15 页 grep `GPU\|NVIDIA\|Titan\|GTX\|RTX\|Tesla\|PyTorch\|TensorFlow\|Caffe`，**0 命中** —— 论文从未说明训练/推理硬件。训练超参倒是有（§4.3, p.6）：triplet loss，margin α = 1，**Adam，初始学习率 0.001**；训练策略见 §4.4（先用 static TSDF patch 自监督预训练，再冻结前几层、只微调 multi-scale encoder） |

## 论文报告的数字 Reported numbers

### 一、3RScan 数据集统计（这是后续工作引用最频繁的一组数）

**Table 1, p.3 — 与同期 RGB-D 数据集的横向对比（本行为 3RScan）**

| 出处 | 数据集 | 规模 | 真实 | 采集设备 | Benchmark | 含场景变化 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 表 1, p.3 | **3RScan (Ours)** | **1482 scans of 478 scenes** | ✅ 真实 | Tango | **Object Instance Re-Localization** | ✅ |
| 表 1, p.3 | ScanNet（对比） | 1513 scans, 2.5M images | ✅ | Structure Sensor | Semantic Voxel Labeling | ❌ |
| 表 1, p.3 | Fehr et al.（对比） | 23 scans of 3 scenes | ✅ | Tango | Change Detection | ✅ |

**Table 2, p.4 — 划分统计（论文原文数字）**

| 划分 | #scenes | #re-scans | #scans |
| :--- | ---: | ---: | ---: |
| test | 46 | 101 | 147 |
| train | 385 | 793 | 1178 |
| validation | 47 | 110 | 157 |
| **total** | **478** | **1004** | **1482** |

> ✅ **与本地实测一致**：本目录 [`work/protocol.md`](work/protocol.md) §1 从 `3RScan.json` 解析出的「478 场景 / 1004 次 rescan」与论文 Table 2 **完全吻合**，可放心作为协议基准。

**补充材料 p.11–p.12 — 标注与变化统计**

| 出处 | 项 | 数值 |
| :--- | :--- | ---: |
| §7 补充, p.11 | 已标注实例总数 | **48k instances** |
| §7 补充, p.11 | 唯一语义标签数 | **534 unique labels** |
| §7 补充, p.11 | RGB-D 图像总数 | **约 363k** 张 |
| §7 补充, p.11 | 实例分割覆盖率 | 几乎全部扫描 **> 90%**，平均场景覆盖 **> 98%** |
| §7 补充, p.12 | 提供的变化变换总数 | **3289 instance transformations** |
| §7 补充, p.12 | 涉及的**不同物体**数 | **1947 different objects** |
| §7 补充, p.12 | 变化物体的标注类别数 | **187 different categories** |
| §7 补充, p.12 | 记录时间跨度 | **> 12 个月** |
| §7 补充, p.12 | 采集人力 | **45+ 人**，**13+ 国** |
| §7 补充, p.12 | 场景重访次数 | 每场景 **2 – 12** 次 3D 快照 |
| 表 6, p.12 | 对称性分布 | none **1513** / C₂ **220** / C₄ **82** / C∞ **132**（合计 1947）；论文称 **22% 的物体具有对称性** |
| §3.3.1, p.4 | 语义分割平均标注覆盖率 | **98.5%** |

> ⚠️ **表 6 的表头在原文中写的是 `# scans`，但四行合计恰为 1947 = 上述「不同物体数」**，且正文说「22% 的**物体**有对称性」（(220+82+132)/1947 = 22.3%）→ 该行实为**物体数**，表头疑似笔误。引用时建议写明「1947 个变化物体中 434 个有对称性」。
>
> ⚠️ **另一处不一致**：补充 p.12 正文说「这些变化物体类别被映射到 **9 个** class（见 Table 7）」，但 **Table 7 与 Table 5 都只列出 7 类**（seating / table-cabinet / bed-sofa / appliances / cushions / items / structure）。本文件按实际表格报 **7 类**。

### 二、重定位 benchmark —— 这就是「数据集基线」（Table 4, p.8）

> 这是后续工作引用 3RScan 时最常引的一张表，也是我们的对照目标。
> 「本文方法」= `RIO-multiscale`；其余为对比方法。

| 出处 | 方法 | 训练数据 | Recall <0.1m, 10° | MRE [deg] | MTE [m] | Recall <0.2m, 20° | MRE [deg] | MTE [m] |
| :--- | :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| 表 4, p.8 | FPFH（对比，手工特征） | — | 2.61 | 7.25 | 0.0645 | 8.36 | 10.57 | 0.0776 |
| 表 4, p.8 | SHOT（对比，手工特征） | — | 6.79 | 5.35 | 0.0268 | 12.27 | 8.18 | 0.0393 |
| 表 4, p.8 | 3DMatch（对比，学习式） | dynamic | 5.48 | 5.81 | 0.0542 | 13.05 | 7.30 | 0.0708 |
| 表 4, p.8 | **RIO-multiscale（本文）** | static | 9.92 | 4.33 | 0.0425 | 17.75 | 6.39 | 0.0545 |
| 表 4, p.8 | **RIO-multiscale（本文）** | **dynamic** | **15.14** | 4.75 | 0.0437 | **23.76** | 6.08 | 0.0547 |

### 三、按物体类别的重定位精度（Table 5, p.8；阈值 <0.2 m, 20°）

| 出处 | 类别 | FPFH | SHOT | 3DMatch | **RIO-S（本文, static）** | **RIO-D（本文, dynamic）** |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: |
| 表 5, p.8 | seating | 5.08 | 12.71 | 6.78 | 14.41 | 21.19 |
| 表 5, p.8 | table | 9.33 | 5.33 | 21.33 | 25.33 | 29.33 |
| 表 5, p.8 | items | 5.06 | 13.92 | 7.59 | 11.39 | 16.46 |
| 表 5, p.8 | bed / sofa | 56.52 | 21.74 | 34.78 | 34.78 | 47.83 |
| 表 5, p.8 | cushion（**最难**） | **0.00** | 15.52 | 8.62 | 8.62 | **10.34** |
| 表 5, p.8 | appliances | 11.11 | 16.67 | 33.33 | 44.44 | 55.56 |
| 表 5, p.8 | structure | 0.00 | 0.00 | 8.33 | 16.67 | 33.33 |
| 表 5, p.8 | **avg.（论文摘要引用的 30.58%）** | 12.44 | 12.27 | 17.25 | 22.23 | **30.58** |

> ✅ **Abstract 里的 "achieving an accuracy of 30.58%"（p.1）就是 Table 5 最后一行 RIO-D 的 avg. 值**，两者已对上。

### 四、关键点匹配（Table 3, p.7；在 95% recall 处）

| 出处 | 方法（训练） | F1 | Accuracy | Precision | FPR | ER | Top-1 | Top-3 | Top-5 | Top-10 |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 表 3, p.7 | RIO-singlescale 60cm (static) | 71.54 | 62.21 | 57.37 | 70.60 | 75.59 | 2.17 | 4.12 | 5.96 | 17.56 |
| 表 3, p.7 | RIO-singlescale 120cm (static) | 74.17 | 66.92 | 60.83 | 61.18 | 66.16 | 3.94 | 4.58 | 8.21 | 20.38 |
| 表 3, p.7 | RIO-singlescale 120cm (dynamic) | 78.71 | 74.29 | 67.17 | 46.43 | 51.41 | 6.26 | 7.26 | 9.58 | 27.82 |
| 表 3, p.7 | **RIO-multiscale (static)** | 85.58 | 83.98 | 77.82 | 27.09 | 32.04 | 30.73 | 53.48 | 69.61 | 89.03 |
| 表 3, p.7 | **RIO-multiscale (dynamic)**（最优） | **94.37** | 94.33 | 93.61 | 6.50 | 11.35 | 64.10 | 86.20 | 93.40 | 98.30 |

**网络规格（§4.1, p.4；复现必须对齐）**：输入为 **TSDF patch**，两个尺度各 **32×32×32** 体素网格，空间范围 **(1.2 m)³** 与 **(0.6 m)³**，对应体素大小 **1.875 cm** 与 **3.75 cm**。两分支**不共享权重**，分别经过 SSE 后拼接送入 multi-scale encoder（MSE）。

## 关键结论（论文自己声称的）

- **数据集本身是首要贡献**：首个**真实**的、含**时序不连续**的大规模室内 RGB-D 数据集 —— **1482 scans / 478 scenes / 1004 re-scans**，且**每个物体有固定 ID，跨扫描保持一致**（§3.1, §6, p.4/p.8）。
- **变化是真实且多样**：包含**物体被移动（几厘米到几米）**、**被移除或新增**，以及窗帘/毯子等**非刚体**变化和光照变化（§3.2, p.4）；共 **3289 条变换、1947 个不同物体**、**187 个类别**（补充 p.12）。
- **多尺度显著优于单尺度**：即使只用 static 数据训练，multiscale 的 F1 = **85.58** 就已超过所有单尺度架构（最高 78.71）（§5.1, Table 3, p.7）。
- **加上 dynamic 微调再涨一大截**：F1 **85.58 → 94.37**，Top-1 **30.73 → 64.10**（Table 3, p.7）；重定位 avg. Recall@<0.2m,20° 从 **17.75 → 23.76**，平均准确率 **30.58%**，大幅超过 SHOT（12.27）与 3DMatch（13.05）（Table 4/5, p.8）。
- **最难的是软物体**：`cushion` 类 FPFH 完全失败（**0.00**），本文方法也只有 **10.34**；`structure`（门窗）同样困难（Table 5, p.8）。

## 内容变化（物体移动/移除）下的表现：论文报告了什么

### ✅ **这篇是全球三个目标里唯一真正报告了「内容变化下性能」的论文。**

这非常重要，也是我们项目论点的**关键反例/正例**，必须写清楚：

**1. 整个 benchmark 的定义就是内容变化。** §3.4, p.4 原话：*"Given one or multiple objects in a segmented source scene, we want to estimate the corresponding 6DoF poses in a target scan of the same environment taken at a different point in time."* 评测集**专门由「被移动的物体」构成** —— §5.2 p.7 明确说 Table 3 评的是 *"the ability of different methods to match **dynamic patches around keypoints on annotated changed objects**"*。

**2. 有直接的「变化 vs 未变化」对照实验**，这正是最有价值的数字：

| 对照 | 出处 | 数字 | 含义 |
| :--- | :--- | :--- | :--- |
| 只在**静态**数据上训 vs 加**动态**数据微调（重定位 avg. Recall@<0.2m,20°） | 表 4 & 5, p.8 | **17.75 → 23.76**（+6.01） | 内容变化下，专门用变化数据训练能显著提升 |
| 同上（F1） | 表 3, p.7 | **85.58 → 94.37**（+8.79） | 特征层面的同向增益 |
| 同上（Top-1） | 表 3, p.7 | **30.73 → 64.10**（+33.37，翻倍还多） | 未用动态数据时，正样本在 50 个负样本里排第一的能力**不到一半** |
| 按**类别**看内容变化难度 | 表 5, p.8 | cushion **10.34**、structure **33.33** vs appliances **55.56**、bed/sofa **47.83** | 内容变化下的性能**强烈依赖物体类型** |

**3. 为什么 RIO 能做而 VPR 论文不能？** 因为 RIO **有 3D GT**：每个变化物体都带 `T_GT = R_GT + t_GT`（§3.1, p.4），并且**标注了对称性**用于评测折算。视觉 VPR 论文（02-07 / 02-08）只有「同一地点」的图像对，**没有物体级的位移真值**，因此结构上就测不了「家具被挪走了多少」。

### ⚠️ 但必须承认三点限制（这决定了它**不能直接**支撑我们的 VPR 论点）

1. **任务不同**：RIO 是 **3D 物体 6DoF 重定位**（输入是 TSDF patch / 点云），**不是图像检索式 VPR**。它的 30.58% 不能拿来当 "VPR 在内容变化下的 Recall@1" 用。
2. **不是「地点识别」**：它假定**已经知道**要在目标扫描里找哪个物体（给定 source object 的分割），考的是**位姿估计精度**，而不是「能不能认出这是同一个地方」。
3. **图像级 / 序列级的内容变化 VPR 指标：论文未报告。** 3RScan 有 RGB-D 序列，但 RIO 论文**没有**做「用重访图像做地点检索」的实验。**我查过的地方**：全文 15 页 grep `image retrieval|place recognition|Recall@|loop closure`，均无 VPR 式评测。若要这个数字，只能自己用 3RScan 的 A/B 会话构造 —— 这正是本目录 [`work/protocol.md`](work/protocol.md) §7 在做的事。

> **结论的准确表述**：不能说「内容变化下的评测不存在」—— **3RScan/RIO 就是反例**。
> 准确的说法是：**「内容变化下的 VPR（图像检索）评测不存在」**。3RScan 提供了**唯一现成的、带物体位移真值的重访数据**，但社区（包括 RIO 自己）只用它测 3D 重定位，**从未用它测过 VPR**。这恰恰是我们那道题目的空白所在，也是 3RScan 成为我们数据瓶颈的原因。

## 对我们的复现意味着什么

- **可复现的前提**：
  - **代码**：<https://github.com/WaldJohannaU/3RScan>（**仓库本体不含数据，只有读取工具**）。本目录 [`README.md`](README.md) 已记录三个二进制 `rio_example` / `align_poses` / `rio_renderer_render_all` 全部跑通，以及两个编译坑（`render_mode` 必须传 `0` 才输出 occlusion；`GLEW_LIBRARY` 单复数问题）。
  - **数据（关键）**：
    - **公开示例数据：无需申请** —— `setup.sh` 可直接拉，本目录 README 记录为 `3RScan.json` 3.1 MB + `3RScan.v2.zip` 39.9 MB。**目前本机只有这 1 对会话。**
    - **全量数据集：需同意 3RScan Terms of Use**（项目页 <https://waldjohannau.github.io/RIO/> 的下载表单），**不是 clone 就能用**。
  - **权重**：论文**未发布** RIO 的预训练模型（项目页只发布数据与 benchmark）。要复现 Table 3/4/5 必须**自己按 §4.3/§4.4 训练**（static 预训练 + dynamic 微调，triplet loss，Adam，lr 0.001）。**这是与 02-07/02-08（免训练）最大的不同：RIO 的复现成本高一个量级。**
  - **硬件**：论文**未说明** → `未找到`。但 3D 稀疏卷积网络 + 全量 3RScan 训练，GPU 是硬门槛。
  - **benchmark server**：论文提供 **hidden test set + 自动 server 端评测脚本**（§3.4, p.4）。要用官方划分对比，**必须走 server**（这也是能拿到唯一权威 test 数字的路径）。
- **目标数字**（按投入产出排序）：
  1. **数据集统计对齐（零成本，先做）**：Table 2 的 **478 / 1004 / 1482** —— 与 [`work/protocol.md`](work/protocol.md) §1 的本地解析**已吻合**，可当作已验证项。
  2. **全量统计核对（拿到全量数据后）**：**48k instances / 534 labels / 3289 transformations / 1947 objects / 187 categories**（补充 p.11–12）。本地目前只有 1 对会话（32 个物体），**统计上不足以支撑任何 F1 结论**（README 已指出）。
  3. **重定位主指标（需自己训练）**：`RIO-multiscale (dynamic)` 的 **avg. Recall@<0.2m,20° = 30.58**、`<0.1m,10° = 15.14`（Table 4/5, p.8）。这是最终目标，但**依赖训练**。
  4. **最省力的中间校验点**：关键点匹配 **F1 = 94.37 / Top-1 = 64.10**（Table 3, p.7）—— 比完整 6DoF 流程少一层 RANSAC + SVD，适合先验证网络与数据管线。
  5. **我们真正要的那一格（论文给不了）**：**内容变化下的 VPR Recall@1** —— 论文未报告，必须自造。
- **对不上的可能原因**：
  1. **数据划分**：必须用论文 Table 2 的 **test 46 scenes / 101 re-scans**。3RScan 后续有 v1/v2/v3 版本差异，标注会变；本机拉的是 `3RScan.v2.zip`，**版本必须记进报告**。
  2. **对称性折算**：论文明确「评测时考虑对称性」（§3.4, p.4；补充 p.12 表 6）。不做对称折算会**系统性低估**（把「转了个身」算成错）。本目录 [`work/protocol.md`](work/protocol.md) §6 已记录 id 13 / 19 是对称物体（symmetry=3 / 1）。
  3. **static vs dynamic 模型混淆**：Table 3/4/5 都同时给 RIO-S 与 RIO-D 两列，**引用时必须写明是哪一列**（22.23 vs 30.58 差 8.35 个百分点）。
  4. **训练策略**：先 static 预训练再**冻结前几层只微调 MSE**（§4.4, p.6）。跳过第二阶段就退化成 RIO-S 的数字。
  5. **负样本构造**：论文的负样本「随机取自另一个训练场景，**并且包含已移除物体上的 TSDF patch**」（§4.4, p.6）—— 这个细节若漏掉，动态物体的判别力会掉。
  6. **TP/FP 定义差异**：`Recall` 是**按物体**（不是按关键点）统计的百分比，别和 Table 3 的 patch 级 F1 混淆。
  7. **MTE / MRE 是"仅对成功预测"统计的中位数**，还是对全部预测 —— 论文表述为 "Median Translation Error"，未在正文明确样本集合，**复现时须注意**（此处标注为不确定，不臆测）。
- **阻塞风险**：
  - **🔴 高 —— 数据 gated**：全量 3RScan 需填 Terms of Use 表单审批，且**本机目前只有 1 对会话（51 帧前缀，会话 B 实际 753 帧）**。这是本目标**第一位的阻塞项**，README「下一步」也已把它列为第 1 条。
  - **🔴 高 —— 需自己训练**：官方**未发布** RIO 权重，Table 3/4/5 的任何数字都要自己训。相比 02-07/02-08 的免训练复现，成本高一个量级。
  - **🟡 中 —— hidden test set**：官方 test 数字只能通过 server 端脚本获取，本地无法离线复核 30.58。
  - **🟡 中 —— 硬件未说明**：论文未给 GPU，无法预估算力预算。
  - **🟢 低 —— 工具链**：读取/渲染工具已跑通（见 README），无阻塞。
