<div align="center">

# 02-02 · OASIS-Map

**OASIS-Map: Object-Level Change Detection in Multi-Session Mapping**

用语义对应匹配做物体级变化检测，表 I 专门有 `Assoc.` 列、表 III 专测身份保持。

[![venue](https://img.shields.io/badge/venue-arXiv%202026--07%20%C2%B7%20under%20review-0b7285)](https://arxiv.org/abs/2607.14899)
![blocked](https://img.shields.io/badge/blocked-no%20upstream%20code%20released-cf222e)
[![code](https://img.shields.io/badge/code-project%20page%20says%20%E2%80%9CCode%20Soon%E2%80%9D-181717)](https://dynamic.robots.ox.ac.uk/projects/oasis-map/)
![data](https://img.shields.io/badge/data-3RScan%20%C2%B7%20car%20park%20%C2%B7%20outdoor%20market-1c7ed6)
![needs](https://img.shields.io/badge/needs-the%20authors%20to%20publish-6e7781)

[Requirements](#requirements) &nbsp;•&nbsp; [Why not reproduced](#why-not-reproduced) &nbsp;•&nbsp; [Notes](#notes)

*[← 复现区索引](../README.md) &nbsp;•&nbsp; [论文报告值](paper_baseline.md)*

</div>

前端建几何地图 + 物体地图；后端计算**稠密的 patch 级语义对应**——对应置信度低 = 变化区域，置信度高 = 持续存在的物体；再据此做物体关联与变化判定（Appear / Disappear / Static / Moved），并保持跨会话的物体身份。

**直接对手，几乎与我们同题。** 它把「语义对应」这条路走通了，
            报告 F1 = 0.783（停车场换车）与 0.667（3RScan 移动物体关联），
            并自述 *reliable object association across revisits remains a key challenge,
            especially under partial views, occlusion, and imperfect segmentation*。

|  |  |
| :--- | :--- |
| **Status** | ⛔ 无可复现对象 —— 上游代码至今未发布（项目页仍写 Code Soon） |

---

## Requirements

| 需要什么 | 说明 |
| :--- | :--- |
| 代码 | 作者尚未发布 —— 项目页标注 *Code Soon*（2026-10-05 实测） |
| 规则 | 本仓库的规则是「**有库才复现**」：没有上游代码就不自己照着论文写一份 |
| 已产出 | 论文精读 [`paper_baseline.md`](paper_baseline.md)：3RScan moved-F1 0.353 / static-F1 0.663；Car Park replaced-F1 0.783 |

## Why not reproduced

| | |
| :--- | :--- |
| **阻塞点** | 项目页（2026-10-05 实测）仍写 **Code Soon**，没有仓库链接；论文本身也还在 under review |
| **为什么不能绕** | 本仓库的规则是「**有库就用别人的库，没库就不复现**」—— 自己照着论文写一份，出来的数字既不是它的也不是我们的 |
| **它仍然贡献了什么** | 论文精读已落地：[`paper_baseline.md`](paper_baseline.md) 记录了它的头号数字（3RScan moved-F1 0.353 / static-F1 0.663；Car Park replaced-F1 0.783），并**修正了一处判断** —— 它有 Unknown 类，所以「加一个弃权类」不能当作我们的差异点 |
| **要什么才能跑** | 作者发布代码。届时本文件夹的 `reproduce.py` 就是放真实 `run()` 的地方 |

## Notes

- [ ] **精读全文**，画出它的 pipeline，标出每一步的输入输出
- [ ] 逐条核对它未解决的部分是否真的没解决（这决定题目还值不值得做）
- [ ] 把它的 **Unknown 判定**与我们设想的可观测性估计做逐条对照（见下方「坑」）
- [ ] 列出它报告的指标与消融，指出缺哪一项（例如可观测性分层 F1、ECE）
- [ ] 产出：`work/oasis_map_notes.md` + 一句话差异声明

- ⚠️ **一处必须修正的判断**：关于它的论证不能写成「它无法区分'没看到'与'没有'」。
  项目页实际写的是 *"If an object is not seen in one of the sessions, it remains **Unknown**"*
  —— **它有一个 Unknown 类**。自述的弱点是**关联可靠性**（部分视角 / 遮挡 / 分割不完美），
  不是缺少弃权类。
  → 差异点必须改成：把**可观测性做成可标定的量**并**分层测量**（可观测性分层 F1 / ECE /
  未观测区分率），并验证它的 Unknown 判定在低可观测性样本上是否真的可靠。
- 代码未发布 → 不要排「跑它的代码」的工期。

项目页（论文摘要给出）标注 **"Code Soon"**，截至 2026-10-05 仍**没有可克隆的仓库**。
按既定规则「没有库的先不复现」，本文件夹**只保留论文报告值**（[`paper_baseline.md`](paper_baseline.md)），
不写 `reproduce.py`，也不进流水线。

它的价值仍然在：**这是我们那道题的直接对手**，表 I 的对比维度（`Obj.` / `Assoc.`）正好定义了
我们要超越什么，表 II 在 3RScan 上的 `N_gt = 32` 与本机那一对会话的物体数完全一致。

> 复现时在这里补：实际命令、参数、跑出来的数字、与论文不一致的地方、失败原因。
> 不要只留在终端历史里。

| 日期 | 做了什么 | 结果 / 数字 | 结论 |
| :--- | :--- | :--- | :--- |
| | | | |

目前**只能读论文**（代码未发布）。建议顺序：

1. 读摘要 + 方法 + 实验三节，先把 pipeline 复述出来
2. 抄下它所有数字与消融项，做成表
3. 明确写出：如果代码一直不发布，我们的 baseline 用什么替代
   （候选：自己实现 patch 级语义对应；或用 ConceptGraphs 的物体节点 + 几何 IoU 做弱化版）

## Documentation

- 论文自报数字与阻塞分析：[`paper_baseline.md`](paper_baseline.md)
- `reproduce.py`：`require()` 给出上面这条阻塞的**可判定**版本（满足即通过）
- 本文件夹的实测记录：[`work/`](work/)
- 复现区索引与约定：[`../README.md`](../README.md)

<!-- run_all.py 读下面这几行生成索引表，改动请保持同样的 | 键 | 值 | 形式 -->

| 元数据 | 内容 |
| :--- | :--- |
| 项 | 内容 |
| 怎么才能跑 | 等作者发布代码（项目页现写 Code Soon）；本仓库的规则是「没库就不复现」 |
| 论文 | OASIS-Map: Object-Level Change Detection in Multi-Session Mapping using Semantic Correspondence Matching |
| 论文链接 | [arXiv:2607.14899](https://arxiv.org/abs/2607.14899) · [项目页](https://dynamic.robots.ox.ac.uk/projects/oasis-map/) |
| 论文报告值 | [`paper_baseline.md`](paper_baseline.md) —— 原论文自报结果与复现阻塞分析 |
| 代码 | ❌ **未发布** —— 项目页标注 *Code Soon*（实测：页面可达，无仓库链接） |
| 数据 | 3RScan（室内 RGB-D）· 停车场换车（室外 RGB-LiDAR）· 户外市场 |
| 方向 | D2 · 语义建图、视觉定位与导航 |
| 任务书对应 | §4.1 删除判据「可观测性」；§5 H3；物体级变化检测题目 |
| 复现顺序 | 21 |
| 能否复现 | ⛔ 不能复现：代码未发布（项目页仍写 Code Soon），没有库可跑。 |
| 复现完成 | ⛔ 无库可复现 |
