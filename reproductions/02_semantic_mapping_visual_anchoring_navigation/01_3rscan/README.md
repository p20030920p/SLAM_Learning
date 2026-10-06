<div align="center">

# 02-01 3RScan

**3RScan / RIO: 3D Object Instance Re-Localization in Changing Indoor Environments**

同一房间多次扫描、物体被搬动的标准数据集与官方工具。

[![venue](https://img.shields.io/badge/venue-ICCV%202019%20dataset-22314E)](https://arxiv.org/abs/1908.06109)
![result](https://img.shields.io/badge/result-protocol%20%2B%20observability-2ea043)
[![code](https://img.shields.io/badge/code-WaldJohannaU%2F3RScan-181717?logo=github&logoColor=white)](https://github.com/WaldJohannaU/3RScan)
![compute](https://img.shields.io/badge/compute-CPU-6f42c1)

[快速开始](#快速开始) &nbsp;•&nbsp; [结果](#结果) &nbsp;•&nbsp; [说明](#说明)

*[索引](../README.md) &nbsp;•&nbsp; [论文报告值](paper_baseline.md) &nbsp;•&nbsp; [复现脚本](reproduce.py) &nbsp;•&nbsp; [回测基线](baselines.json)*

</div>

3RScan 是多会话重访场景的标准数据集。这里用官方工具箱把 A/B 会话协议与可观测性判据落地，为物体级变化检测提供可用的评测口径。

|  |  |
| :--- | :--- |
| 数据 | 1 对 A/B 会话（51 帧，32 个物体）；全量需要申请 |
| 协议 | 对齐容差 1.0 m，由实测噪声 0.639 m 标定而来 |
| 可观测性 | 9 个可见 / 4 个被遮挡 / 16 个在视场外 |
| 复现 | `python3 reproductions/run_all.py --only 02-01` |

---

## 快速开始

| 依赖 | 版本 |
| :--- | :--- |
| 工具 | 官方三个 C++ 二进制 |
| 数据 | 公开示例对，无需申请表 |

```bash
python3 reproductions/02_semantic_mapping_visual_anchoring_navigation/01_3rscan/work/build_ab_pair.py
python3 reproductions/run_all.py --only 02-01
```

## 结果

官方渲染器给出的可见性分数与自写 OBB 估计器在 31 个物体里 22 个一致，分歧处官方正确（它渲染真 mesh）。

一条硬结论：物体的最小真实位移 0.265 m 小于最大对齐噪声 0.639 m，纯几何分不开「移动」与「噪声」。

## 说明

- 库对「已消失物体」保持沉默，跨扫描渲染才是那一格的解。
- 本机只有 1 对会话，统计上不足以支撑任何 F1 结论，因此这一条目报的是协议与判据，不是分数。

## 文档

- 论文自报数字与出处：[`paper_baseline.md`](paper_baseline.md)
- 复现脚本与回测基线：[`reproduce.py`](reproduce.py) · [`baselines.json`](baselines.json)
- 本文件夹的脚本与实测记录：[`work/`](work/)
- 复现区索引：[`../README.md`](../README.md)
