<div align="center">

# 02-03 · ConceptGraphs

**开放词汇 3D 场景图的底座（SAM + CLIP + LLaVA-7B + GPT-4）—— 四件套里光 LLaVA-7B 一项就要约 14 GB 显存。**

[![venue](https://img.shields.io/badge/venue-ICRA%202024-0b7285)](https://arxiv.org/abs/2309.16650)
![blocked](https://img.shields.io/badge/blocked-needs%2016--24%20GB%20VRAM%20%2B%20GPT--4%20key-cf222e)
[![code](https://img.shields.io/badge/code-concept--graphs%2Fconcept--graphs-181717?logo=github&logoColor=white)](https://github.com/concept-graphs/concept-graphs)
![data](https://img.shields.io/badge/data-Replica%20%2F%20ScanNet%20%C2%B7%20public-1c7ed6)
![needs](https://img.shields.io/badge/needs-a%2016--24%20GB%20GPU%20%2B%20paid%20API-6f42c1)

[结论](#一句话-verdict) &nbsp;•&nbsp; [怎么跑](#怎么跑-how-to-run) &nbsp;•&nbsp; [坑与注意](#坑与注意-pitfalls) &nbsp;•&nbsp; [记录](#记录-log)

*[← 复现区索引](../README.md) &nbsp;•&nbsp; [论文报告值](paper_baseline.md) &nbsp;•&nbsp; [复现脚本](reproduce.py)*

</div>

---

## 一句话 Verdict

| | |
| :--- | :--- |
| **阻塞点** | 流水线要跑 SAM（ViT-H）+ CLIP image encoder + **LLaVA-7B**；LLaVA 的 fp16 权重就约 14 GB，工程上一般要 **16–24 GB 显存**；CG-D 变体还要再加 RAM + Grounding DINO |
| **另一道门** | LLM 那一步要**付费的 GPT-4（`gpt-4-0613`）** API key —— 这不是算力，是账号 |
| **实测证据** | 本机无 GPU（`nvidia-smi` 不存在），15 GB 内存连 LLaVA-7B 权重都放不下。论文本身**没写硬件**（全文 grep `GPU`/`RTX`/`A100`/`V100` 无命中），门槛是按它点名的模型推出来的 |
| **要什么才能跑** | 一块 ≥16–24 GB 显存的 GPU + GPT-4 API key。数据（Replica / HM3D）是公开的 |

## 关键设定 Settings

| 项 | 内容 |
| :--- | :--- |
| 怎么才能跑 | ≥16–24 GB 显存的 GPU + 付费 GPT-4（`gpt-4-0613`）API key；Replica / HM3D 数据公开 |
| 论文 | ConceptGraphs: Open-Vocabulary 3D Scene Graphs for Perception and Planning |
| 论文链接 | [arXiv:2309.16650](https://arxiv.org/abs/2309.16650) |
| 论文报告值 | [`paper_baseline.md`](paper_baseline.md) —— 原论文自报结果与复现阻塞分析 |
| 代码 | [concept-graphs/concept-graphs](https://github.com/concept-graphs/concept-graphs) ✅ 实测 200 |
| 数据 | Replica / ScanNet（仓库含处理脚本） |
| 方向 | D2 · 语义建图、视觉定位与导航 |
| 任务书对应 | §0 地图层「关键帧稀疏语义」；§2 难点 5 |
| 复现顺序 | 17 |
| 能否复现 | ⛔ 按论文规模不现实：CPU 上 PyTorch3D 与 SAM/CLIP/LLaVA 都能装能跑，但论文是对 Replica/ScanNet 整段序列建图，CPU 吞吐差两三个数量级；另外 LLaVA-7B 光权重就 ~14 GB（本机 15 GB 内存）。 |
| 复现完成 | ⛔ 本机不可复现（无 GPU） |

---

## 它做了什么 What it does

从 RGB-D 序列增量构建**开放词汇 3D 场景图**：物体是节点，空间/语义关系是边，标签由 CLIP 类的开放词汇模型给出。

## 为什么复现它 Why

**语义建图的底座。** 变化检测的操作对象就是「物体节点」，而 ConceptGraphs 提供了这个表示。它同时也是被批评的典型：**建一次永不更新**，阈值会产生虚假节点且没有置信度标定 —— 这正是空缺所在。

## 复现目标（可验收）Goals

- [ ] 在一个 Replica 场景上跑通，得到物体节点 + 关系的场景图
- [ ] 记录它如何决定「一个物体」的粒度（聚类阈值是多少、改阈值会怎样）
- [ ] 明确写出：同一场景跑两次，物体 ID 是否一致（**大概率不一致** —— 这是重要证据）
- [ ] 产出：场景图 + 一份「身份不稳定」的实测记录

## 怎么跑 How to run

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