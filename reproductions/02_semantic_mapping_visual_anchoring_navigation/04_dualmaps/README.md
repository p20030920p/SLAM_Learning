<div align="center">

# 02-04 · DualMap

**DualMap: Online Open-Vocabulary Semantic Mapping for Natural Language Navigation**

少数会「自我编辑」的开放词汇地图：检测变化、修订语义、再用于语言导航。

[![venue](https://img.shields.io/badge/venue-RA--L%202025-0b7285)](https://arxiv.org/abs/2506.01950)
![blocked](https://img.shields.io/badge/blocked-needs%20an%20RTX%204090%20%28paper%27s%20GPU%29-cf222e)
[![code](https://img.shields.io/badge/code-Eku127%2FDualMap-181717?logo=github&logoColor=white)](https://github.com/Eku127/DualMap)
![data](https://img.shields.io/badge/data-Replica%20%C2%B7%20public-1c7ed6)
![needs](https://img.shields.io/badge/needs-RTX%204090--class%20GPU-6f42c1)

[Requirements](#requirements) &nbsp;•&nbsp; [Why not reproduced](#why-not-reproduced) &nbsp;•&nbsp; [Notes](#notes)

*[← 复现区索引](../README.md) &nbsp;•&nbsp; [论文报告值](paper_baseline.md)*

</div>

在线开放词汇语义地图，支持自然语言查询导航，并且能**自我编辑**：物体被移走就删掉、出现就加上，地图随场景变化更新。

**少数会修订的地图**，因而是衡量「修订质量」最合适的对照。它的边界很清楚：只支持**整物体增删**，**不支持语义重标注**（物体还在原位但标签该改了）—— 那个空隙就是可以做的事。

|  |  |
| :--- | :--- |
| **Status** | ⛔ 本机不可复现 —— 论文主实验用 RTX 4090 |

---

## Requirements

| 需要什么 | 说明 |
| :--- | :--- |
| GPU | **RTX 4090**（论文主实验；附录用 RTX 3080 Laptop） |
| 数据 | Replica，公开；代码 MIT，可直接 clone |
| 排位 | 四篇 D2 底座里**硬件要求写得最清楚**的一篇，换机器时第一个该排上 |

## Why not reproduced

| | |
| :--- | :--- |
| **阻塞点** | 论文主实验：**NVIDIA RTX 4090**（p.6 §V-A-4）；附录补充实验用 RTX 3080 Laptop；长时建图实验用 RTX 4090 Desktop |
| **实测证据** | 本机无 GPU。GroundingDINO + SAM 在 CPU 上**能**跑，但每帧几十秒，而论文的 Replica 序列是几千帧 —— 差两三个数量级；本机 15 GB 内存也吃紧 |
| **要什么才能跑** | RTX 4090 级 GPU。数据（Replica）公开，代码 MIT 可直接 clone |
| **排位** | 四篇 D2 底座里**硬件要求写得最清楚**的一篇，换机器时第一个该排上 |

## Notes

- [ ] 跑通，确认它的「自我编辑」具体触发条件是什么
- [ ] 验证边界：物体移位但类别不变时它怎么处理？标签错了能改吗？
- [ ] 记录它修改地图时是否给出置信度（若无，这就是「未标定」的又一例证）
- [ ] 产出：`work/dualmaps_edit_policy.md`

- 带 ROS 依赖，**不要**直接扔进本仓库的 `src/` 一起 colcon build（版本可能冲突），
  用独立 docker 或独立工作空间。
- 「能改地图像什么」和「改得对不对」是两件事：前者看它的 demo，后者要自己设计检验。

> 复现时在这里补：实际命令、参数、跑出来的数字、与论文不一致的地方、失败原因。
> 不要只留在终端历史里。

| 日期 | 做了什么 | 结果 / 数字 | 结论 |
| :--- | :--- | :--- | :--- |
| | | | |

```bash
git clone https://github.com/Eku127/DualMap code/
# 仓库带 ROS 支持，注意它与本仓库的 ROS 2 Jazzy 版本关系，必要时用 docker 隔离
```

## Documentation

- 论文自报数字与阻塞分析：[`paper_baseline.md`](paper_baseline.md)
- `reproduce.py`：`require()` 给出上面这条阻塞的**可判定**版本（满足即通过）
- 本文件夹的实测记录：[`work/`](work/)
- 复现区索引与约定：[`../README.md`](../README.md)

<!-- run_all.py 读下面这几行生成索引表，改动请保持同样的 | 键 | 值 | 形式 -->

| 元数据 | 内容 |
| :--- | :--- |
| 项 | 内容 |
| 怎么才能跑 | RTX 4090 级 GPU（论文主实验用的就是它）；Replica 数据公开，代码 MIT |
| 论文 | DualMap: Online Open-Vocabulary Semantic Mapping for Natural Language Navigation in Dynamic Changing Scenes |
| 论文链接 | [arXiv:2506.01950](https://arxiv.org/abs/2506.01950) |
| 论文报告值 | [`paper_baseline.md`](paper_baseline.md) —— 原论文自报结果与复现阻塞分析 |
| 代码 | [Eku127/DualMap](https://github.com/Eku127/DualMap) ✅ 实测 200（带 ROS 支持） |
| 数据 | 公开数据集 + 自采集（见仓库） |
| 方向 | D2 · 语义建图、视觉定位与导航 |
| 任务书对应 | §4.1「修订语义」；§2 难点 5 |
| 复现顺序 | 18 |
| 能否复现 | ⛔ 按论文规模不现实：GroundingDINO + SAM 在 CPU 上能跑但每帧几十秒，论文的 Replica 序列是几千帧；本机内存 15 GB 也吃紧。 |
| 复现完成 | ⛔ 本机不可复现（无 GPU） |
