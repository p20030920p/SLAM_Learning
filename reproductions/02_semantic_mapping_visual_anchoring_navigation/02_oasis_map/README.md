# 02-02 · OASIS-Map

| 项 Item | 内容 |
| :--- | :--- |
| 论文 | OASIS-Map: Object-Level Change Detection in Multi-Session Mapping using Semantic Correspondence Matching |
| Venue | **arXiv 2026-07，under review**（Oxford, Dynamic Robot Systems Group） |
| 论文链接 | [arXiv:2607.14899](https://arxiv.org/abs/2607.14899) · [项目页](https://dynamic.robots.ox.ac.uk/projects/oasis-map/) |
| 论文报告值 | [`paper_baseline.md`](paper_baseline.md) —— 原论文自报结果与复现阻塞分析 |
| 代码 | ❌ **未发布** —— 项目页标注 *Code Soon*（实测：页面可达，无仓库链接） |
| 数据 | 3RScan（室内 RGB-D）· 停车场换车（室外 RGB-LiDAR）· 户外市场 |
| 方向 | D2 · 语义建图、视觉定位与导航 |
| 任务书对应 | §4.1 删除判据「可观测性」；§5 H3；物体级变化检测题目 |
| 复现状态 | ⛔ **按规则排除**：论文/项目页标 **Code Soon**，至今未发布代码；「没有库的先不复现」 |
| 复现顺序 | 17 |
| 能否复现 | ⛔ 不能复现：代码未发布（项目页仍写 Code Soon），没有库可跑。 |
| 复现完成 | ⛔ 无库可复现 |

## 它做了什么 What it does

前端建几何地图 + 物体地图；后端计算**稠密的 patch 级语义对应**——对应置信度低 = 变化区域，置信度高 = 持续存在的物体；再据此做物体关联与变化判定（Appear / Disappear / Static / Moved），并保持跨会话的物体身份。

## 为什么复现它 Why

**直接对手，几乎与我们同题。** 它把「语义对应」这条路走通了，
            报告 F1 = 0.783（停车场换车）与 0.667（3RScan 移动物体关联），
            并自述 *reliable object association across revisits remains a key challenge,
            especially under partial views, occlusion, and imperfect segmentation*。

## 复现目标（可验收）Goals

- [ ] **精读全文**，画出它的 pipeline，标出每一步的输入输出
- [ ] 逐条核对它未解决的部分是否真的没解决（这决定题目还值不值得做）
- [ ] 把它的 **Unknown 判定**与我们设想的可观测性估计做逐条对照（见下方「坑」）
- [ ] 列出它报告的指标与消融，指出缺哪一项（例如可观测性分层 F1、ECE）
- [ ] 产出：`work/oasis_map_notes.md` + 一句话差异声明

## 步骤 Steps

目前**只能读论文**（代码未发布）。建议顺序：

1. 读摘要 + 方法 + 实验三节，先把 pipeline 复述出来
2. 抄下它所有数字与消融项，做成表
3. 明确写出：如果代码一直不发布，我们的 baseline 用什么替代
   （候选：自己实现 patch 级语义对应；或用 ConceptGraphs 的物体节点 + 几何 IoU 做弱化版）

## 坑与注意 Pitfalls

- ⚠️ **一处必须修正的判断**：关于它的论证不能写成「它无法区分'没看到'与'没有'」。
  项目页实际写的是 *"If an object is not seen in one of the sessions, it remains **Unknown**"*
  —— **它有一个 Unknown 类**。自述的弱点是**关联可靠性**（部分视角 / 遮挡 / 分割不完美），
  不是缺少弃权类。
  → 差异点必须改成：把**可观测性做成可标定的量**并**分层测量**（可观测性分层 F1 / ECE /
  未观测区分率），并验证它的 Unknown 判定在低可观测性样本上是否真的可靠。
- 代码未发布 → 不要排「跑它的代码」的工期。

## ⛔ 为什么这个文件夹先不复现

项目页（论文摘要给出）标注 **"Code Soon"**，截至 2026-10-05 仍**没有可克隆的仓库**。
按既定规则「没有库的先不复现」，本文件夹**只保留论文报告值**（[`paper_baseline.md`](paper_baseline.md)），
不写 `reproduce.py`，也不进流水线。

它的价值仍然在：**这是我们那道题的直接对手**，表 I 的对比维度（`Obj.` / `Assoc.`）正好定义了
我们要超越什么，表 II 在 3RScan 上的 `N_gt = 32` 与本机那一对会话的物体数完全一致。

## 记录 Log

> 复现时在这里补：实际命令、参数、跑出来的数字、与论文不一致的地方、失败原因。
> 不要只留在终端历史里。

| 日期 | 做了什么 | 结果 / 数字 | 结论 |
| :--- | :--- | :--- | :--- |
| | | | |
