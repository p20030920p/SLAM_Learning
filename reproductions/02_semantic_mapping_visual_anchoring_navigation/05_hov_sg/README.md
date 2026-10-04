# 02-05 · HOV-SG

| 项 Item | 内容 |
| :--- | :--- |
| 论文 | Hierarchical Open-Vocabulary 3D Scene Graphs for Language-Grounded Robot Navigation |
| Venue | **RSS 2024** |
| 论文链接 | [arXiv:2403.17846](https://arxiv.org/abs/2403.17846) |
| 论文报告值 | [`paper_baseline.md`](paper_baseline.md) —— 原论文自报结果与复现阻塞分析 |
| 代码 | [hovsg/HOV-SG](https://github.com/hovsg/HOV-SG) ✅ 实测 200 |
| 数据 | Replica / HM3D-Semantics（公开） |
| 方向 | D2 · 语义建图、视觉定位与导航 |
| 任务书对应 | §0 地图层；D2 的「导航」那一段 |
| 复现状态 | ⬜ 未开始（论文报告值已记录） |

| 复现顺序 | 15 |
| 能否复现 | ⛔ 本机不能：要 GPU（OpenCLIP + SAM + habitat-sim），HM3DSem 数据也很大。 |
| 复现完成 | ⛔ 本机不可复现（无 GPU） |

## 它做了什么 What it does

构建**分层**的开放词汇 3D 场景图（楼层 / 房间 / 物体），并在这个图上做**语言接地的导航**：说一句「去厨房的桌子旁边」就能规划。

## 为什么复现它 Why

一举覆盖 D2 的两段：语义建图 **和** 导航。任务书在导航这一段是空的（决策层只有「停车」），HOV-SG 是补上「目标级导航」最直接的入口；同时它每个场景只建一张静态图，修订能力缺失 —— 又是一个对照样本。

## 复现目标（可验收）Goals

- [ ] 在一个 Replica/HM3D 场景上跑通，得到分层场景图
- [ ] 跑通一次语言导航查询，记录它如何把语言映射到图上节点
- [ ] 明确写出：同一场景二次建图时，节点与身份是否保持（预计不保持）
- [ ] 产出：场景图 + 一次导航查询的复现记录

## 步骤 Steps

```bash
git clone https://github.com/hovsg/HOV-SG code/
# 依赖 Habitat / Replica / HM3D，流水线较长；按仓库 README 分步验证
```

## 坑与注意 Pitfalls

- 流水线长、依赖多，**按阶段验收**（先出场景图，再出导航），不要一次跑到底。
- 它自带仿真环境（Habitat），与本仓库的 Gazebo 是两套东西，不要混。

## 记录 Log

> 复现时在这里补：实际命令、参数、跑出来的数字、与论文不一致的地方、失败原因。
> 不要只留在终端历史里。

| 日期 | 做了什么 | 结果 / 数字 | 结论 |
| :--- | :--- | :--- | :--- |
| | | | |
