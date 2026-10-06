<div align="center">

# 01-08 NGD-SLAM

**NGD-SLAM: Towards Real-Time Dynamic SLAM without GPU**

不用 GPU 的实时动态 SLAM：光流与深度方差替代逐帧神经网络分割。

[![venue](https://img.shields.io/badge/venue-IROS%202025-22314E)](https://arxiv.org/abs/2405.07392)
![result](https://img.shields.io/badge/result-ATE%200.0157%20vs%200.015-2ea043)
[![code](https://img.shields.io/badge/code-yuhaozhang7%2FNGD--SLAM-181717?logo=github&logoColor=white)](https://github.com/yuhaozhang7/NGD-SLAM)
![compute](https://img.shields.io/badge/compute-CPU%20only-6f42c1)

[快速开始](#快速开始) &nbsp;•&nbsp; [结果](#结果) &nbsp;•&nbsp; [说明](#说明)

*[索引](../README.md) &nbsp;•&nbsp; [论文报告值](paper_baseline.md) &nbsp;•&nbsp; [复现脚本](reproduce.py) &nbsp;•&nbsp; [回测基线](baselines.json)*

</div>

NGD-SLAM 的目标是在没有 GPU 的机器上做实时动态 SLAM。它用光流与深度方差判断动态，让追踪不必等待神经网络。

|  |  |
| :--- | :--- |
| 结果 | TUM fr3/walking_xyz ATE 0.0157 m（论文 0.015 m） |
| RPE | 平移 0.0201 m/s（论文 0.020） |
| 数据 | TUM RGB-D，官方直链，免注册 |
| 复现 | `python3 reproductions/run_all.py --only 01-08` |

---

## 快速开始

| 依赖 | 版本 |
| :--- | :--- |
| 构建 | 官方 C++ 自编 + `.venvs/dmb` |
| 数据 | TUM fr3/walking_xyz |

```bash
python3 reproductions/run_all.py --only 01-08
```

## 结果

| 指标 | 本文件夹 | 论文 |
| :--- | ---: | ---: |
| ATE | 0.0157 m | 0.015 m |
| RPE 平移 | 0.0201 m/s | 0.020 m/s |
| RPE 旋转 | 0.604 °/s（RMSE） | 0.470 °/s（统计量未说明） |

旋转一项未对齐：论文没有说明用的是 RMSE 还是均值。

## 说明

- 读官方代码纠正了计划里的一条判断：它仍然使用 YOLO 语义，省掉的是「追踪等网络」，不是语义本身。
- 旋转 RPE 的差异属于报告口径缺失，不是实现错误。

## 文档

- 论文自报数字与出处：[`paper_baseline.md`](paper_baseline.md)
- 复现脚本与回测基线：[`reproduce.py`](reproduce.py) · [`baselines.json`](baselines.json)
- 本文件夹的脚本与实测记录：[`work/`](work/)
- 复现区索引：[`../README.md`](../README.md)
