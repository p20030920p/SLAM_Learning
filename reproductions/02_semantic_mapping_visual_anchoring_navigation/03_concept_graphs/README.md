# 02-03 · ConceptGraphs

| 项 Item | 内容 |
| :--- | :--- |
| 论文 | ConceptGraphs: Open-Vocabulary 3D Scene Graphs for Perception and Planning |
| Venue | **ICRA 2024** |
| 论文链接 | [arXiv:2309.16650](https://arxiv.org/abs/2309.16650) |
| 论文报告值 | [`paper_baseline.md`](paper_baseline.md) —— 原论文自报结果与复现阻塞分析 |
| 代码 | [concept-graphs/concept-graphs](https://github.com/concept-graphs/concept-graphs) ✅ 实测 200 |
| 数据 | Replica / ScanNet（仓库含处理脚本） |
| 方向 | D2 · 语义建图、视觉定位与导航 |
| 任务书对应 | §0 地图层「关键帧稀疏语义」；§2 难点 5 |
| 复现状态 | ⬜ 未开始（论文报告值已记录） |

| 复现顺序 | 17 |
| 能否复现 | ⛔ 本机不能：要 CUDA（PyTorch + PyTorch3D），本机没有 GPU。 |
| 复现完成 | ⛔ 本机不可复现（无 GPU） |

## 它做了什么 What it does

从 RGB-D 序列增量构建**开放词汇 3D 场景图**：物体是节点，空间/语义关系是边，标签由 CLIP 类的开放词汇模型给出。

## 为什么复现它 Why

**语义建图的底座。** 变化检测的操作对象就是「物体节点」，而 ConceptGraphs 提供了这个表示。它同时也是被批评的典型：**建一次永不更新**，阈值会产生虚假节点且没有置信度标定 —— 这正是空缺所在。

## 复现目标（可验收）Goals

- [ ] 在一个 Replica 场景上跑通，得到物体节点 + 关系的场景图
- [ ] 记录它如何决定「一个物体」的粒度（聚类阈值是多少、改阈值会怎样）
- [ ] 明确写出：同一场景跑两次，物体 ID 是否一致（**大概率不一致** —— 这是重要证据）
- [ ] 产出：场景图 + 一份「身份不稳定」的实测记录

## 步骤 Steps

```bash
git clone https://github.com/concept-graphs/concept-graphs code/
# 需要 GPU + 预训练权重（SAM / CLIP 等）；按仓库 README 装环境
```

## 坑与注意 Pitfalls

- 模型权重体积大，先确认显存与磁盘。
- 「跑两次 ID 是否一致」这个实验**成本极低但结论很硬**，建议优先做——
  它直接支撑「跨会话身份一致性无人报告」这个空白。

## 记录 Log

> 复现时在这里补：实际命令、参数、跑出来的数字、与论文不一致的地方、失败原因。
> 不要只留在终端历史里。

| 日期 | 做了什么 | 结果 / 数字 | 结论 |
| :--- | :--- | :--- | :--- |
| | | | |
