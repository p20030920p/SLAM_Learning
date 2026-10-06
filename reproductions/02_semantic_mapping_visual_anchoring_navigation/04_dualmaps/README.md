<div align="center">

# 02-04 DualMap

**DualMap: Online Open-Vocabulary Semantic Mapping for Natural Language Navigation**

会自我编辑的开放词汇地图：检测变化、修订语义，再用于语言导航。

[![venue](https://img.shields.io/badge/venue-RA--L%202025-22314E)](https://arxiv.org/abs/2506.01950)
![status](https://img.shields.io/badge/status-blocked%3A%20needs%20an%20RTX%204090-cf222e)
[![code](https://img.shields.io/badge/code-Eku127%2FDualMap-181717?logo=github&logoColor=white)](https://github.com/Eku127/DualMap)
![needs](https://img.shields.io/badge/needs-RTX%204090%20class%20GPU-6f42c1)

[需求](#需求) &nbsp;•&nbsp; [说明](#说明)

*[索引](../README.md) &nbsp;•&nbsp; [论文报告值](paper_baseline.md) &nbsp;•&nbsp; [复现脚本](reproduce.py)*

</div>

DualMap 让地图在运行中修订语义，属于开放词汇地图里少数会自我编辑的实现。

|  |  |
| :--- | :--- |
| 状态 | 本机不可复现 |
| 阻塞 | 论文主实验用 NVIDIA RTX 4090，附录用 RTX 3080 Laptop |
| 数据 | Replica，公开 |
| 排位 | 四篇底座里硬件要求写得最清楚的一篇 |

---

## 需求

| 需要什么 | 说明 |
| :--- | :--- |
| GPU | RTX 4090 级别的显卡 |
| 代码 | MIT 许可，可直接 clone |

## 说明

- GroundingDINO 与 SAM 在 CPU 上能跑，但每帧几十秒，论文的序列是几千帧，差两三个数量级。
- 换机器时，这一篇应该第一个排上。

## 文档

- 论文自报数字与阻塞分析：[`paper_baseline.md`](paper_baseline.md)
- 复现脚本：[`reproduce.py`](reproduce.py)，其中 `require()` 给出上面这条阻塞的可判定版本
- 本文件夹的实测记录：[`work/`](work/)
- 复现区索引：[`../README.md`](../README.md)
