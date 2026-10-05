<div align="center">

# 02-06 · Clio

**机载实时分层场景图，算力受限路线的代表 —— 论文给的是 RTX 3090，或 Spot 背上那块 4090 Laptop。**

[![venue](https://img.shields.io/badge/venue-RA--L%202024-0b7285)](https://arxiv.org/abs/2404.13696)
![blocked](https://img.shields.io/badge/blocked-needs%20an%20RTX%203090%20for%20real--time-cf222e)
[![code](https://img.shields.io/badge/code-MIT--SPARK%2FClio-181717?logo=github&logoColor=white)](https://github.com/MIT-SPARK/Clio)
![data](https://img.shields.io/badge/data-Replica%20%C2%B7%20public-1c7ed6)
![needs](https://img.shields.io/badge/needs-RTX%203090%20%2824%20GB%29%20%2F%204090%20Laptop-6f42c1)

[结论](#一句话-verdict) &nbsp;•&nbsp; [怎么跑](#怎么跑-how-to-run) &nbsp;•&nbsp; [坑与注意](#坑与注意-pitfalls) &nbsp;•&nbsp; [记录](#记录-log)

*[← 复现区索引](../README.md) &nbsp;•&nbsp; [论文报告值](paper_baseline.md) &nbsp;•&nbsp; [复现脚本](reproduce.py)*

</div>

---

## 一句话 Verdict

| | |
| :--- | :--- |
| **阻塞点** | 主实验 **RTX 3090（24 GB）**，且系统要**同时**跑 FastSAM + CLIP ViT-L/14（附录换成 ViT-H-14），论文自称能在笔记本级 GPU 上实时在线跑 |
| **一处要点名的细节** | TensorRT 是**可选**的（上游 README 明说不是必须）—— 所以卡住的不是「有没有 GPU」这一句话，而是 **CPU 的吞吐**：FastSAM + CLIP 在 CPU 上每分钟只能处理少量帧，而论文是对整段 Replica 序列建图 |
| **真实机器人那一档** | Spot 机载：i9-13950HX（24 核）+ 64 GB RAM + **RTX 4090 Laptop（16 GB）** —— 说明它的门槛是"16 GB 显存的移动卡"这个量级 |
| **要什么才能跑** | RTX 3090 级 GPU；数据（Replica）公开 |

## 关键设定 Settings

| 项 | 内容 |
| :--- | :--- |
| 怎么才能跑 | RTX 3090（24 GB）级 GPU，或 Spot 上那块 4090 Laptop（16 GB）；Replica 数据公开 |
| 论文 | Clio: Real-time Task-Driven Open-Set 3D Scene Graphs |
| 论文链接 | [arXiv:2404.13696](https://arxiv.org/abs/2404.13696) |
| 论文报告值 | [`paper_baseline.md`](paper_baseline.md) —— 原论文自报结果与复现阻塞分析 |
| 代码 | [MIT-SPARK/Clio](https://github.com/MIT-SPARK/Clio) ✅ 实测 200 |
| 数据 | 自采集 / 公开数据集（见仓库） |
| 方向 | D2 · 语义建图、视觉定位与导航 |
| 任务书对应 | §2 难点 5 算力受限下的稀疏表示 + 语义 |
| 复现顺序 | 14 |
| 能否复现 | ⛔ 按论文规模不现实：FastSAM + CLIP ViT-L 在 CPU 上每分钟只能处理少量帧，而论文是对整段 Replica 序列建图。**注意**：TensorRT 是可选的（README 明说不是必须），所以卡住的不是「有没有 GPU」这一句话，而是 CPU 的吞吐。 |
| 复现完成 | ⛔ 本机不可复现（无 GPU） |

---

## 它做了什么 What it does

用信息瓶颈做**任务驱动的聚类**，按当前任务决定场景图的粒度，在机载算力下实时构建分层开放集场景图。

## 为什么复现它 Why

算力受限路线的代表，正对应任务书「稀疏/半稠密 + 语义并行」的设定。更重要的是它的**副作用**：粒度随任务变 → **物体身份本身不固定**，这和「跨会话身份一致率」天然冲突，是一个极好的反例样本。

## 复现目标（可验收）Goals

- [ ] 跑通，观察粒度如何随任务变化
- [ ] 记录：同一场景换任务后，物体节点是否被重新聚类（身份是否漂移）
- [ ] 产出：一份「身份不固定」的实测记录 —— 用于证明身份一致性指标的必要性

## 怎么跑 How to run

```bash
git clone https://github.com/MIT-SPARK/Clio code/
# 依赖 ROS + 视觉前端；按仓库 README 装环境
```

## 坑与注意 Pitfalls

- 与 DualMap 同样有 ROS 依赖，**独立环境**，不要混进本仓库的 colcon 工作空间。
- 「身份不固定」是它的设计选择，不是 bug —— 写作时要表述准确，不要说成缺陷。

## 记录 Log

> 复现时在这里补：实际命令、参数、跑出来的数字、与论文不一致的地方、失败原因。
> 不要只留在终端历史里。

| 日期 | 做了什么 | 结果 / 数字 | 结论 |
| :--- | :--- | :--- | :--- |
| | | | |