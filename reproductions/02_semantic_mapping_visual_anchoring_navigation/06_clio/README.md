<div align="center">

# 02-06 Clio

**Clio: Real-time Task-Driven Open-Set 3D Scene Graphs**

机载实时分层场景图，算力受限路线的代表。

[![venue](https://img.shields.io/badge/venue-RA--L%202024-22314E)](https://arxiv.org/abs/2404.13696)
![status](https://img.shields.io/badge/status-blocked%3A%20needs%20an%20RTX%203090-cf222e)
[![code](https://img.shields.io/badge/code-MIT--SPARK%2FClio-181717?logo=github&logoColor=white)](https://github.com/MIT-SPARK/Clio)
![needs](https://img.shields.io/badge/needs-RTX%203090%20%2F%204090%20Laptop-6f42c1)

[需求](#需求) &nbsp;•&nbsp; [说明](#说明)

*[索引](../README.md) &nbsp;•&nbsp; [论文报告值](paper_baseline.md) &nbsp;•&nbsp; [复现脚本](reproduce.py)*

</div>

Clio 按当前任务决定场景图的粒度，目标是在机载算力下实时构建分层开放集场景图。

|  |  |
| :--- | :--- |
| 状态 | 本机不可复现 |
| 阻塞 | 主实验用 RTX 3090，机载档位是 Spot 上的 RTX 4090 Laptop |
| 注意 | TensorRT 是可选的，卡点是 CPU 吞吐而不是有没有显卡 |
| 数据 | Replica，公开 |

---

## 需求

| 需要什么 | 说明 |
| :--- | :--- |
| GPU | RTX 3090 级别，或 16 GB 显存的移动卡 |
| 说明 | 真实机器人档位是 i9 加 64 GB 内存加 4090 Laptop |

## 说明

- FastSAM 与 CLIP 在 CPU 上每分钟只能处理少量帧，而论文对整段序列建图。
- 这条还有一个概念上的价值：粒度随任务变化意味着物体身份本身不固定，与跨会话身份一致率天然冲突，是很好的反例样本。

## 文档

- 论文自报数字与阻塞分析：[`paper_baseline.md`](paper_baseline.md)
- 复现脚本：[`reproduce.py`](reproduce.py)，其中 `require()` 给出上面这条阻塞的可判定版本
- 本文件夹的实测记录：[`work/`](work/)
- 复现区索引：[`../README.md`](../README.md)
