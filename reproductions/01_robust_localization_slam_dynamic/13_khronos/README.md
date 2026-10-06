<div align="center">

# 01-13 Khronos

**Khronos: A Unified Approach for Spatio-Temporal Metric-Semantic SLAM**

4D 时空度量语义地图：物体、动态与变化都进场景图。

[![venue](https://img.shields.io/badge/venue-RSS%202024-22314E)](https://arxiv.org/abs/2402.13817)
![status](https://img.shields.io/badge/status-blocked%3A%20more%20than%2013.5%20GB%20RAM-cf222e)
[![code](https://img.shields.io/badge/code-MIT--SPARK%2FKhronos-181717?logo=github&logoColor=white)](https://github.com/MIT-SPARK/Khronos)
![needs](https://img.shields.io/badge/needs-20%20GB%2B%20free%20RAM-6f42c1)

[需求](#需求) &nbsp;•&nbsp; [说明](#说明)

*[索引](../README.md) &nbsp;•&nbsp; [论文报告值](paper_baseline.md) &nbsp;•&nbsp; [复现脚本](reproduce.py)*

</div>

Khronos 把物体、动态与变化统一进一张时空场景图。工作区、数据与无头驱动都已就绪，卡点只有一个：这台机器的内存不够。

|  |  |
| :--- | :--- |
| 状态 | 本机不可复现 |
| 阻塞 | khronos_node 以约 250 MB/s 持续增长，五次内存上限尝试全部被 OOM 杀掉 |
| 已就绪 | 29 个包编译通过，10.3 GB 模拟 bag 与四份真值已下载 |
| 证据 | 采样显示 20 秒内 1.34 → 6.02 GB，同期 bag 播放器不在前列 |

---

## 需求

| 需要什么 | 说明 |
| :--- | :--- |
| 内存 | 可用内存 20 GB 以上的机器 |
| 系统 | Ubuntu 24.04 与 ROS 2 Jazzy，本机系统版本正好命中 |

## 说明

- 系统的 `require()` 按 `/proc/meminfo` 判定可用内存，换机器即可直接跑完整流程。
- 要在这台机器上跑只能降分辨率或截断 bag，那会改变实验口径，因此没有擅自采用。
- 上游 README 自己写着 ROS 2 版本仍在开发中且不稳定，这条无界增长与之一致。

## 文档

- 论文自报数字与阻塞分析：[`paper_baseline.md`](paper_baseline.md)
- 复现脚本：[`reproduce.py`](reproduce.py)，其中 `require()` 给出上面这条阻塞的可判定版本
- 本文件夹的实测记录：[`work/`](work/)
- 复现区索引：[`../README.md`](../README.md)
