# 02-04 · DualMap

| 项 Item | 内容 |
| :--- | :--- |
| 论文 | DualMap: Online Open-Vocabulary Semantic Mapping for Natural Language Navigation in Dynamic Changing Scenes |
| Venue | **RA-L 2025** |
| 论文链接 | [arXiv:2506.01950](https://arxiv.org/abs/2506.01950) |
| 论文报告值 | [`paper_baseline.md`](paper_baseline.md) —— 原论文自报结果与复现阻塞分析 |
| 代码 | [Eku127/DualMap](https://github.com/Eku127/DualMap) ✅ 实测 200（带 ROS 支持） |
| 数据 | 公开数据集 + 自采集（见仓库） |
| 方向 | D2 · 语义建图、视觉定位与导航 |
| 任务书对应 | §4.1「修订语义」；§2 难点 5 |
| 复现状态 | ⬜ 未开始（论文报告值已记录） |

| 复现顺序 | 18 |
| 能否复现 | ⛔ 按论文规模不现实：GroundingDINO + SAM 在 CPU 上能跑但每帧几十秒，论文的 Replica 序列是几千帧；本机内存 15 GB 也吃紧。 |
| 复现完成 | ⛔ 本机不可复现（无 GPU） |

## 它做了什么 What it does

在线开放词汇语义地图，支持自然语言查询导航，并且能**自我编辑**：物体被移走就删掉、出现就加上，地图随场景变化更新。

## 为什么复现它 Why

**少数会修订的地图**，因而是衡量「修订质量」最合适的对照。它的边界很清楚：只支持**整物体增删**，**不支持语义重标注**（物体还在原位但标签该改了）—— 那个空隙就是可以做的事。

## 复现目标（可验收）Goals

- [ ] 跑通，确认它的「自我编辑」具体触发条件是什么
- [ ] 验证边界：物体移位但类别不变时它怎么处理？标签错了能改吗？
- [ ] 记录它修改地图时是否给出置信度（若无，这就是「未标定」的又一例证）
- [ ] 产出：`work/dualmaps_edit_policy.md`

## 步骤 Steps

```bash
git clone https://github.com/Eku127/DualMap code/
# 仓库带 ROS 支持，注意它与本仓库的 ROS 2 Jazzy 版本关系，必要时用 docker 隔离
```

## 坑与注意 Pitfalls

- 带 ROS 依赖，**不要**直接扔进本仓库的 `src/` 一起 colcon build（版本可能冲突），
  用独立 docker 或独立工作空间。
- 「能改地图像什么」和「改得对不对」是两件事：前者看它的 demo，后者要自己设计检验。

## 记录 Log

> 复现时在这里补：实际命令、参数、跑出来的数字、与论文不一致的地方、失败原因。
> 不要只留在终端历史里。

| 日期 | 做了什么 | 结果 / 数字 | 结论 |
| :--- | :--- | :--- | :--- |
| | | | |
