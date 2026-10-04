# 01-04 · Removert — 论文报告值 Paper-reported baseline

> ⚠️ **这一份是唯一没有拿到原文的。** 本仓库其余 16 个复现对象都有原文（本地 PDF 或已取回），
> 只有 Removert 拿不到，原因见下。本文件因此**不含 Removert 自报的数字**，
> 只记录"别人替它测的数"——那些数**不能当作 Removert 的论文报告值**使用。

| 项 Item | 内容 |
| :--- | :--- |
| 论文 | Remove, then Revert: Static Point Cloud Map Construction using Multiresolution Range Images |
| Venue / 年 | **IEEE/RSJ IROS 2020**（Giseop Kim, Ayoung Kim；KAIST） |
| DOI | [10.1109/IROS45743.2020.9340856](https://doi.org/10.1109/IROS45743.2020.9340856) |
| 本地 PDF | **无** |
| 官方代码 | https://github.com/irapkaist/removert （仓库可达，README 里的论文链接指向 `irap.kaist.ac.kr`，见下） |

## 为什么没有原文（可复核的取证过程）

| 尝试 | 结果 |
| :--- | :--- |
| 作者 README 给出的唯一链接 `https://irap.kaist.ac.kr/publications/gskim-2020-iros.pdf` | ❌ **DNS 无法解析**（`Could not resolve host: irap.kaist.ac.kr`），本机与 web_fetch 两条路径均失败 |
| 本仓库既有的抓取流水线 `Localise/tools/download_papers.py` | ❌ 已记录为"未能下载"之一：arXiv 最佳标题覆盖率仅 **0.08**，IEEE Xplore 返回 HTTP 202 反爬墙 |
| Semantic Scholar Graph API | ❌ 返回 403 Forbidden |
| **OpenAlex**（`api.openalex.org/works/doi:10.1109/iros45743.2020.9340856`） | ✅ 明确回答：`is_oa: false`，`oa_status: "closed"`，`oa_url: null`，`any_repository_has_fulltext: false` |

**结论：这篇论文是闭源的，没有开放获取版本，作者给的镜像站也不通了。**
要拿原文只能走 IEEE Xplore 订阅（机构账号）或馆际互借——**这不是技术问题，是权限问题**。

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

- **可复现的前提**：代码（`irapkaist/removert`）与数据（SemanticKITTI）都可获得；**只有论文原文取不到**。
- **目标数字**：**暂时没有 Removert 的自报值**。
  可选的两条路：(a) 走机构订阅拿到 IROS 2020 原文，补齐自报表格；
  (b) 明确声明"01-04 复现的是 DynamicMap_Benchmark 里的 Removert 重实现"，
  目标数取 **KITTI 00 的 SA/DA/AA = 99.44/41.53/64.26**——这条路现在就能开工，且口径与本目录 01-01/01-05 一致。
- **建议**：选 (b) 作为主线，把 (a) 记为待补。理由是并行实验 H1′ 需要的是**同一口径下的可比数字**，
  而 Removert 自报的 voxel-wise 数字本来就没法和基准的点级数字比。
- **阻塞风险**：论文原文闭源（IEEE 订阅墙）；但**不阻塞复现本身**——代码、数据、第三方数字都在手上。
