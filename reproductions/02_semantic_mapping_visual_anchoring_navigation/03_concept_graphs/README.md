<div align="center">

# 02-03 ConceptGraphs

**ConceptGraphs: Open-Vocabulary 3D Scene Graphs for Perception and Planning**

开放词汇 3D 场景图的底座：SAM、CLIP、LLaVA-7B 与 GPT-4。

[![venue](https://img.shields.io/badge/venue-ICRA%202024-22314E)](https://arxiv.org/abs/2309.16650)
![status](https://img.shields.io/badge/status-blocked%3A%20needs%2016--24%20GB%20VRAM%20and%20an%20API%20key-cf222e)
[![code](https://img.shields.io/badge/code-concept--graphs%2Fconcept--graphs-181717?logo=github&logoColor=white)](https://github.com/concept-graphs/concept-graphs)
![needs](https://img.shields.io/badge/needs-16--24%20GB%20GPU-6f42c1)

[需求](#需求) &nbsp;•&nbsp; [说明](#说明)

*[索引](../README.md) &nbsp;•&nbsp; [论文报告值](paper_baseline.md) &nbsp;•&nbsp; [复现脚本](reproduce.py)*

</div>

ConceptGraphs 是开放词汇场景图的代表作，管线把 SAM、CLIP、LLaVA-7B 与 GPT-4 串在一起。

|  |  |
| :--- | :--- |
| 状态 | 本机不可复现 |
| 阻塞 | LLaVA-7B 的 fp16 权重约 14 GB，工程上需要 16 至 24 GB 显存 |
| 另需 | LLM 那一步需要付费的 GPT-4 API key |
| 数据 | Replica 与 ScanNet，公开 |

---

## 需求

| 需要什么 | 说明 |
| :--- | :--- |
| GPU | 16 至 24 GB 显存 |
| API | GPT-4 key（gpt-4-0613） |

## 说明

- 论文全文没有写硬件要求，门槛是按它点名的模型推算的。
- 本机没有 GPU，15 GB 内存也放不下 LLaVA-7B 的权重。

## 文档

- 论文自报数字与阻塞分析：[`paper_baseline.md`](paper_baseline.md)
- 复现脚本：[`reproduce.py`](reproduce.py)，其中 `require()` 给出上面这条阻塞的可判定版本
- 本文件夹的实测记录：[`work/`](work/)
- 复现区索引：[`../README.md`](../README.md)
