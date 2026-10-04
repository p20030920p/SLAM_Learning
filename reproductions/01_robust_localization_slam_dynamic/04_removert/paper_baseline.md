# 01-04 · Removert — 论文报告值 Paper-reported baseline

> ⚠️ **原文已经拿到了 —— 在作者自己的代码仓库里。** 我先前判断它"闭源、取不到"，**那个判断是错的**：
> `irapkaist/removert` 仓库根目录就放着 `gkim-2020-iros.pdf`。已存档为本机
> `Localise/.../papers_pdf/072b_Removert_IROS2020_from_authors_repo.pdf`。
>
> 但拿到之后出现了一个更有意思的结论：**这篇论文没有一张编号表格。**
> 全文检索 `TABLE` 命中 **0** 次；它的"quantitative analysis"（§IV-B）指的是
> **图 8 / 图 9 的 TP/FP/FN 随迭代变化的曲线**，不是能直接对标的数字表。
> 所以**它并没有一个可以拿来当验收标准的具体数** —— 见 §2。

| 项 Item | 内容 |
| :--- | :--- |
| 论文 | Remove, then Revert: Static Point Cloud Map Construction using Multiresolution Range Images |
| Venue / 年 | **IEEE/RSJ IROS 2020**（Giseop Kim, Ayoung Kim；KAIST） |
| DOI | [10.1109/IROS45743.2020.9340856](https://doi.org/10.1109/IROS45743.2020.9340856) |
| 本地 PDF | ✅ `Localise/.../papers_pdf/072b_Removert_IROS2020_from_authors_repo.pdf`（**作者仓库自带**，4.76 MB） |
| 官方代码 | https://github.com/irapkaist/removert （仓库可达，README 里的论文链接指向 `irap.kaist.ac.kr`，见下） |

## 原文获取过程（含一次我自己犯的错）

| 尝试 | 结果 |
| :--- | :--- |
| 作者 README 给出的链接 `irap.kaist.ac.kr/publications/gskim-2020-iros.pdf` | ❌ DNS 无法解析 |
| 本仓库既有的抓取流水线 | ❌ arXiv 覆盖率 0.08，IEEE 返回 202 反爬 |
| Semantic Scholar Graph API | ❌ 403 |
| **OpenAlex** | ✅ `is_oa: false`、`oa_status: "closed"`、`any_repository_has_fulltext: false` |
| 我据此下的结论 | ❌ **"取不到"——错了** |
| **克隆作者自己的仓库** | ✅ **`gkim-2020-iros.pdf` 就在仓库根目录，4.76 MB** |

**教训**：OpenAlex 的 `is_oa` 描述的是**出版商侧的开放获取**，它不覆盖
"作者把 PDF 放进自己 GitHub 仓库"这种分发方式。**先克隆仓库，再下结论。**

## 2 · 原文里到底有什么（这才是关键）

| 项 | 值 |
| :--- | :--- |
| 数据集 | KITTI（位姿用 SuMa），真值来自 SemanticKITTI |
| 评测口径 | TP = 估计为静态的点在 SemanticKITTI 真值图里**最近邻 0.1 m 内**存在；FP = 不存在；FN = 真值静态点在预测图里找不到邻居 |
| 定量结果的形式 | **图 8 / 图 9**：KITTI **03**（帧 6–199）上 TP/FP/FN 数量随 revert 迭代次数的变化曲线；另有 KAIST 02（MulRan） |
| **编号表格数量** | **0** |
| 论文自述 | "qualitatively competes or outperforms the human-labeled data" —— **措辞本身就是定性的** |

→ **结论：Removert 这篇论文没有给出可对标的 PR/RR/F1 数字。**
本文件夹因此只能以**第三方复现值**为验收目标，这不是因为我们拿不到原文，
而是因为**原文自己没报**。

## 我们手上有的替代数字（⚠️ 均为第三方复现，非 Removert 自报）

| 出处 | 数据集 | 谁测的 | 指标 | Removert 的数值 |
| :--- | :--- | :--- | :--- | ---: |
| DynamicMap_Benchmark 论文 表 I, p.5（`064_…DynamicMap.pdf`） | KITTI 00 | 基准作者重实现 | 点级 SA / DA / AA | 99.44 / 41.53 / 64.26 |
| DUFOMap 论文 表 I, p.5（`048_DUFOMap.pdf`） | KITTI 00 | DUFOMap 作者 | 点级 SA / DA / AA | 99.44 / 41.53 / 64.26（与上一行同源） |
| 原始 ERASOR 论文 表 II, p.8（`069b_ERASOR_original_RA_L2021.pdf`） | SemanticKITTI 00 | ERASOR 作者 | voxel-wise（0.2）PR / RR / F1 | RM3：85.502 / 99.354 / 0.919；RM3+RV1：86.829 / 90.617 / 0.887 |
| 原始 ERASOR 论文 表 III, p.8 | SemanticKITTI 01 | ERASOR 作者 | 单次迭代耗时 | 0.8307 s |

> **这三行不属于同一套口径，也不能混用**：前两行是点级 SA/DA/AA，第三行是 voxel-wise PR/RR/F1。
> 唯一的共同点是它们都不是 Removert 作者自己报的数。

## 一个已经浮现的、不需要原文就能用的观察

同一个 Removert，在两套口径下的"静态点保留"差了 **13.6 个百分点**：

| 口径 | 静态点保留 | 动态点删除 |
| :--- | ---: | ---: |
| DynamicMap_Benchmark（点级 SA/DA） | **99.44** | 41.53 |
| 原始 ERASOR 作者重实现（voxel-wise PR/RR） | **85.502** | 99.354 |

再叠加 [01-03 ERASOR](../03_erasor/paper_baseline.md) 那边的情况（ERASOR 自报 93.98 → 基准里 66.70，
而 Removert 在基准里是 99.44），**"Removert 静态保留最好 / ERASOR 静态保留最好"这两个结论，
完全取决于用谁的口径**。这正是任务书 §6 并行实验 H1′ 要检验的排序稳定性问题。

## 对我们的复现意味着什么

- **可复现的前提**：代码（`irapkaist/removert`）与数据（SemanticKITTI）都可获得。原文也已拿到，
  但**原文本体不含数字表**，所以验收目标只能取第三方复现值。
- **目标数字**：**原文没有给出数字表**，因此没有"自报值"可用。
  可选的两条路：(a) 走机构订阅拿到 IROS 2020 原文，补齐自报表格；
  (b) 明确声明"01-04 复现的是 DynamicMap_Benchmark 里的 Removert 重实现"，
  目标数取 **KITTI 00 的 SA/DA/AA = 99.44/41.53/64.26**——这条路现在就能开工，且口径与本目录 01-01/01-05 一致。
- **建议**：选 (b) 作为主线，把 (a) 记为待补。理由是并行实验 H1′ 需要的是**同一口径下的可比数字**，
  而 Removert 自报的 voxel-wise 数字本来就没法和基准的点级数字比。
- **阻塞风险**：**没有**——原文、代码、第三方数字现在都在手上。
  真正剩下的阻塞是**环境**：作者仓库是 **ROS 1 catkin 包**（`CMakeLists.txt:8` `find_package(catkin ...)`、
  `package.xml` 依赖 `roscpp`/`rospy`），而本机是 ROS 2 Jazzy、无 Docker、无 sudo。
  **原始代码不能直接在这台机器上跑**——这是 01-04 与 01-03 共同的、尚未解决的问题。
