# 02-03 · ConceptGraphs — 论文报告值 Paper-reported baseline

| 项 Item | 内容 |
| :--- | :--- |
| 论文 | ConceptGraphs: Open-Vocabulary 3D Scene Graphs for Perception and Planning |
| Venue / 年 | 本地 PDF 为 **arXiv:2309.16650v1**（2023-09-28），正文首页**未标注任何会议/期刊**。同批 PDF 中 Clio（083_Clio.pdf）参考文献 [9] 记为 "IEEE Intl. Conf. on Robotics and Automation, May 2024"（即 ICRA 2024）。本文件以 PDF 正文为准：PDF 内无 venue 声明 |
| 本地 PDF | `Localise/01_task_books/materials/papers_pdf/086_ConceptGraphs.pdf`（结果表在**第 4–5 页**：TABLE I 在 p.4，TABLE II / TABLE III 在 p.5；正文 1–6 页，附录 7–11 页） |
| 官方代码 | PDF 内只给出项目页 `https://concept-graphs.github.io/`；第 3 页脚注仅写 "please see our project website and code"。**全文未出现 github.com 的代码仓库 URL**（已 grep `github.com` 全 11 页，仅命中 concept-graphs.github.io） |
| 任务 | 给定 posed RGB-D 帧序列，用 class-agnostic 分割（SAM）+ 多视图关联构建 object-centric 的 open-vocabulary 3D scene graph，节点由 LVLM 生成 caption、边由 LLM 推断空间关系，再以 LLM 驱动下游导航/操作/检索 |
| 数据集 | **Replica**（room0、room1、room2、office0–office3，共 8 场景）用于场景图精度（TABLE I）与 open-vocab 3D 语义分割（TABLE II）；**REAL Lab 实景扫描**（自采）用于文本检索（TABLE III）与真机导航/操作；**AI2Thor 仿真**（p.5 §III-G）用于定位与地图更新演示 |
| 指标 | **node precision**（节点精度）：对每个节点，3 名 AMT 人工评测者中至少 2 名判定该节点 caption 正确的比例。**valid objects**（有效物体数）：评测者认为该节点是有效物体（human-recognizable objects）的数目。**duplicates**（重复检测数）：冗余检测个数。**edge precision**（边精度）：每条估计的空间关系被人工评测判定正确的比例。**mAcc / F-mIoU**：open-vocabulary 3D 语义分割，沿用 ConceptFusion [17] 的评测协议（把每个 object node 的融合语义特征与 `an image of {class}` 的 CLIP 文本 embedding 比相似度，把该 object 的点云整块打成该类）。**R@1/R@2/R@3**：文本查询物体检索的 top-1/2/3 recall |
| 硬件 | **论文未报告**。全文检索 `GPU`/`RTX`/`A100`/`V100`/`4090`/`VRAM`/`NVIDIA`/`GB of` 均无命中（唯一命中是 "much larger memory footprint" 这类定性描述）。论文只给了模型与超参：SAM [33] 作分割、CLIP image encoder [31] 作特征、**LLaVA-7B** 作 LVLM、**GPT-4 (gpt-4-0613)** 作 LLM；voxel size = 2.5 cm，最近邻阈值 δ_nn = 2.5 cm，关联阈值 δ_sim = 1.1。CG-D 变体另加 RAM [54] 图像打标 + Grounding DINO [34] 开放词表检测 |

## 论文报告的数字 Reported numbers

> 说明：下表 "方法" 列中 **ConceptGraphs (Ours) / ConceptGraphs-Detector (Ours)** 为**论文自身方法**；其余为**论文引用的对比方法**，数值取自被引论文。

| 出处（表/图 + 页） | 数据集 / 场景 | 方法 | 指标 | 数值 |
| :--- | :--- | :--- | :--- | ---: |
| TABLE I, p.4 | Replica room0 | **CG（自家）** | node precision / valid objects / duplicates / edge precision | 0.78 / 54 / 3 / 0.91 |
| TABLE I, p.4 | Replica room1 | **CG（自家）** | 同上 | 0.77 / 43 / 4 / 0.93 |
| TABLE I, p.4 | Replica room2 | **CG（自家）** | 同上 | 0.66 / 47 / 4 / 1.0 |
| TABLE I, p.4 | Replica office0 | **CG（自家）** | 同上 | 0.65 / 44 / 2 / 0.88 |
| TABLE I, p.4 | Replica office1 | **CG（自家）** | 同上 | 0.65 / 23 / 0 / 0.9 |
| TABLE I, p.4 | Replica office2 | **CG（自家）** | 同上 | 0.75 / 44 / 3 / 0.82 |
| TABLE I, p.4 | Replica office3 | **CG（自家）** | 同上 | 0.68 / 60 / 5 / 0.79 |
| **TABLE I, p.4** | **Replica 平均** | **CG（自家）** | **node precision / edge precision** | **0.71 / 0.88** |
| TABLE I, p.4 | Replica 平均 | CG-D（自家变体） | node precision / edge precision | 0.61 / 0.91 |
| TABLE I, p.4 | Replica（各场景） | CG-D（自家变体） | node precision 区间 / duplicates 区间 | 0.49–0.71 / 0–4 |
| TABLE II, p.5 | Replica 8 场景 | **ConceptGraphs (Ours)** | **mAcc / F-mIoU** | **40.63 / 35.95** |
| TABLE II, p.5 | Replica 8 场景 | ConceptGraphs-Detector (Ours) | mAcc / F-mIoU | 38.72 / 35.82 |
| TABLE II, p.5 | Replica 8 场景 | ConceptFusion [17]（对比，zero-shot） | mAcc / F-mIoU | 24.16 / 31.31 |
| TABLE II, p.5 | Replica 8 场景 | ConceptFusion [17] + SAM [33]（对比，zero-shot） | mAcc / F-mIoU | 31.53 / 38.70 |
| TABLE II, p.5 | Replica 8 场景 | MaskCLIP [60]（对比，zero-shot） | mAcc / F-mIoU | 4.53 / 0.94 |
| TABLE II, p.5 | Replica 8 场景 | Mask2former + Global CLIP feat（对比） | mAcc / F-mIoU | 10.42 / 13.11 |
| TABLE II, p.5 | Replica 8 场景 | CLIPSeg (rd64-uni) [57]（对比，privileged 微调） | mAcc / F-mIoU | 28.21 / 39.84 |
| TABLE II, p.5 | Replica 8 场景 | LSeg [58]（对比，privileged 微调） | mAcc / F-mIoU | 33.39 / 51.54 |
| TABLE II, p.5 | Replica 8 场景 | OpenSeg [59]（对比，privileged 微调） | mAcc / F-mIoU | 41.19 / 53.74 |
| TABLE III, p.5 | Replica（20 条 query） | CLIP 检索 | Descriptive R@1 / R@2 / R@3 | 0.59 / 0.82 / 0.86 |
| TABLE III, p.5 | Replica（20 条 query） | LLM 检索 | Descriptive R@1 / R@2 / R@3 | 0.61 / 0.64 / 0.64 |
| TABLE III, p.5 | Replica（5 条 query） | CLIP 检索 | Affordance R@1 / R@2 / R@3 | 0.43 / 0.57 / 0.63 |
| TABLE III, p.5 | Replica（5 条 query） | LLM 检索 | Affordance R@1 / R@2 / R@3 | 0.57 / 0.63 / 0.66 |
| TABLE III, p.5 | Replica（5 条 query） | CLIP 检索 | Negation R@1 / R@2 / R@3 | 0.26 / 0.60 / 0.71 |
| **TABLE III, p.5** | **Replica（5 条 query）** | **LLM 检索** | **Negation R@1 / R@2 / R@3** | **0.80 / 0.89 / 0.97** |
| TABLE III, p.5 | REAL Lab（10 条 query） | CLIP / LLM 检索 | Descriptive R@1 | 1.00 / 1.00 |
| TABLE III, p.5 | REAL Lab（10 条 query） | CLIP 检索 | Affordance R@1 / R@2 / R@3 | 0.40 / 0.60 / 0.60 |
| TABLE III, p.5 | REAL Lab（10 条 query） | LLM 检索 | Affordance R@1 / R@2 / R@3 | 1.00 / – / – |
| TABLE III, p.5 | REAL Lab（10 条 query） | CLIP 检索 | Negation R@1 / R@2 / R@3 | 0.00 / – / – |
| TABLE III, p.5 | REAL Lab（10 条 query） | LLM 检索 | Negation R@1 / R@2 / R@3 | 1.00 / – / – |
| §III-G + Fig. 3, p.5–6 | AI2Thor / REAL Lab | ConceptGraphs | 定位与地图更新 | **无数字，仅 supplementary video 演示** |
| §III-F, p.5 | REAL Lab（Spot Arm） | ConceptGraphs | open-vocab pick & place | **无数字**（1 次成功抓取 "cuddly quacker" 鸭子玩偶的定性描述） |

## 关键结论（论文自己声称的）

- **节点标签约 70% 正确、空间关系约 90% 正确**：TABLE I 平均 node precision = **0.71**、edge precision = **0.88**；论文明确说 "The node labels are accurate about 70% of the time; most of the errors are incurred due to errors made by the LVLM employed (LLaVA [55])"，即错误主要来自 LLaVA 而非几何。
- **Open-vocabulary 语义分割追平/超过 ConceptFusion**：TABLE II 上 ConceptGraphs **mAcc 40.63 / F-mIoU 35.95**，对比 ConceptFusion 24.16 / 31.31、+SAM 变体 31.53 / 38.70；论文措辞为 "performs comparably with or better than ConceptFusion, which has a much larger memory footprint"（注意：F-mIoU 上 OpenSeg 53.74、LSeg 51.54 更高，但那是 privileged 微调方法）。
- **LLM 检索擅长复杂/否定查询，CLIP 只擅长描述性查询**：TABLE III 上 Negation 查询 LLM R@1 = **0.80**（Replica）/ **1.00**（Lab），而 CLIP 仅 0.26 / 0.00；论文举的反例是 CLIP 会把 "broken zipper" 误检索成 backpack，而 LLM 正确找到 roll of tape。
- **真机可用**：在 REAL Lab 用 Clearpath Jackal（VLP-16 LiDAR + RealSense D435i）与 Boston Dynamics Spot Arm 完成 open-vocabulary 导航、可通行性估计与 "cuddly quacker" 抓取，但**全部是定性演示，无成功率数字**。

## 跨会话身份 / 地图修订：论文报告了什么

**论文未报告任何跨会话身份或地图修订的量化指标。**

论文确实存在相关章节 —— §III-G "Localization and Map Updates"（p.5–6）：在 AI2Thor 仿真中用粒子滤波做 3-DoF (x, y, yaw) 定位，把机器人当前检测按假设位姿与地图中的物体匹配，聚合为 observation score；并写明 "previously observed objects are removed if they are not observed by the robot and new objects can also be added"。但该节的实验结论原句是 "We provide a demonstration of this localization and map updating approach in the supplementary video material." —— **既无表格也无数字**。附录 A1（p.7）也只提到作者 "spearheaded the implementation of the object-based mapping, localization and map update system"，同样无量化结果。

我为此检索的关键词（全 11 页，含附录）：`cross-session`、`multi-session`、`across session`、`revisit`、`second visit`、`repeat visit`、`long-term`、`identity`、`re-identify`、`reidentify`、`same object`、`change detection`、`map maintenance`、`map update`、`relocaliz`。命中仅：摘要/引言的 "allows easy map maintenance"（定性）、§III-G 上述演示、以及参考文献 [POCD: probabilistic object-level change detection ...] —— 该文献只在参考文献列表里，正文未做对比实验。

**因此**：ConceptGraphs 没有 "同一物体跨 revisit 保持 identity" 的指标，也没有 "物体没动但标签应改" 的指标。它只有 §III-A 的**静态单次建模** node/edge 精度，以及 TABLE III 的**同一张图内**的文本检索 recall。Fig. 3 中 "grey shirt / red-white sneakers 被移动后 LLM 重新推理新位置" 是**定性故事**，不是评测。

## 对我们的复现意味着什么

- **可复现的前提**：
  - **GPU（硬性）**：无 GPU 不可行。论文虽未写硬件，但流水线需要跑 SAM（ViT-H）、CLIP image encoder、**LLaVA-7B**；仅 LLaVA-7B 的 fp16 权重就约 14 GB，工程上一般要 **≥ 16–24 GB 显存**的卡。CG-D 变体还要额外跑 RAM + Grounding DINO。
  - **付费 API**：主结果与 TABLE III 依赖 **GPT-4 (gpt-4-0613)** 做 caption 汇总（appendix Listing 1）与边关系推断，需要 OpenAI API key；`gpt-4-0613` 已被新版本取代，属于**随时可能失效的依赖**。
  - **数据**：Replica 需自行下载（8 个场景）；REAL Lab 与 AI2Thor 定位实验的结果无法复现（前者是自采数据 + 真机，后者只有视频）。
  - **代码**：PDF 内无 GitHub 地址，仓库 README 指向 `github.com/concept-graphs/concept-graphs`（本文件的 "官方代码" 行已说明 PDF 只给了项目页）。
- **目标数字**（建议作为验收线，全部来自 TABLE II，Replica 8 场景）：
  - `ConceptGraphs mAcc = 40.63`、`F-mIoU = 35.95`
  - 辅助线：TABLE I 平均 `node precision = 0.71`、`edge precision = 0.88`（**但 TABLE I 靠 AMT 人工评测，本地不可复现，只能作为参考**）
  - 最具本地可复现性的单点目标是 **TABLE II 的 mAcc 40.63 / F-mIoU 35.95**。
- **对不上的可能原因**：
  - 论文**未给出** Replica 的帧采样率、输入图像分辨率、mask 过滤规则，这些直接决定 mAcc/F-mIoU。
  - 只写 "CLIP image encoder"，**未指明 CLIP checkpoint**（ViT-B/16 vs ViT-H/14 差异巨大）；SAM 也只写 [33]，未指明 ViT-H/L/B。
  - LLaVA / GPT-4 的版本漂移会改变 caption，从而改变 node precision（论文自承错误主要来自 LLaVA）。
  - **GPT-4 输出非确定性**，同一 prompt 不同次运行结果不同；论文未做多次运行方差报告。
  - 关联阈值 δ_sim = 1.1 无敏感性分析；附录脚注承认还试过 Hungarian 匹配但选了 greedy，属于实现细节。
  - AMT 人工评测（TABLE I）本质上不可重复。
- **阻塞风险**：
  - **本机无 GPU → 完全阻塞**（SAM + CLIP + LLaVA-7B 这套组合无法 CPU 跑出可用速度）。
  - **GPT-4 API 成本与可用性**：构建一张 Replica 场景图要对每个 object 调 LVLM（每物体最多 10 个 view）+ GPT-4 汇总 + 每对相邻节点调 LLM 判关系，调用量随物体数二次增长；论文无成本数字。
  - **无官方代码 URL 写在 PDF 里**，且论文是 arXiv v1（2023-09），仓库与论文版本可能已漂移。
  - 论文自列的两个 failure mode：**遗漏小而薄的物体**、**产生重复检测**（TABLE I duplicates 0–5/场景）——这正好是我们关心的 "物体身份" 问题的同源症状，可作为我们工作的动机引用。
