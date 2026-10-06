<div align="center">

# 01-07 DynoSAM

**DynoSAM: Open-Source Smoothing and Mapping Framework for Dynamic SLAM**

在因子图里同时估计相机位姿与物体运动，并开源配套的评测协议。

[![venue](https://img.shields.io/badge/venue-T--RO%202025-22314E)](https://arxiv.org/abs/2501.11893)
![status](https://img.shields.io/badge/status-blocked%3A%20CUDA%20at%20configure-cf222e)
[![code](https://img.shields.io/badge/code-ACFR--RPG%2FDynoSAM-181717?logo=github&logoColor=white)](https://github.com/ACFR-RPG/DynoSAM)
![needs](https://img.shields.io/badge/needs-a%20CUDA%20GPU-6f42c1)

[需求](#需求) &nbsp;•&nbsp; [说明](#说明)

*[索引](../README.md) &nbsp;•&nbsp; [论文报告值](paper_baseline.md) &nbsp;•&nbsp; [复现脚本](reproduce.py)*

</div>

DynoSAM 把动态物体放进因子图一起优化，并附带评测协议。这条复现卡在编译阶段，不是数据或算法问题。

|  |  |
| :--- | :--- |
| 状态 | 本机不可复现 |
| 阻塞 | 上游在 cmake configure 阶段就要求 CUDA 工具链 |
| 证据 | `dynosam_nn/CMakeLists.txt:3` 声明 `LANGUAGES C CXX CUDA`，`:128` 无条件链接 TensorRT 与 cudart |
| 数据 | OMD S4U 开放索引，552 帧约 8.3 GB，免注册 |

---

## 需求

| 需要什么 | 说明 |
| :--- | :--- |
| GPU | 一块 CUDA GPU，运行时开关无法绕过 |
| ROS | ROS 2 工作区，上游对着 Kilted 编写，本机是 Jazzy |

## 说明

- 运行时参数救不了：不用 TensorRT 的路径本来就是默认值，卡点在 configure 阶段。
- 逐文件的证据记在 `work/feasibility.md`。

## 文档

- 论文自报数字与阻塞分析：[`paper_baseline.md`](paper_baseline.md)
- 复现脚本：[`reproduce.py`](reproduce.py)，其中 `require()` 给出上面这条阻塞的可判定版本
- 本文件夹的实测记录：[`work/`](work/)
- 复现区索引：[`../README.md`](../README.md)
