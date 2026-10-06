<div align="center">

# 01-11 ELite

**Ephemerality meets LiDAR-based Lifelong Mapping**

给每个体素维护临时性标签，决定新会话的点该合并、该局部保留、还是该丢弃。

[![venue](https://img.shields.io/badge/venue-ICRA%202025-22314E)](https://arxiv.org/abs/2502.13452)
![result](https://img.shields.io/badge/result-AC%200.971%20vs%200.969-2ea043)
[![code](https://img.shields.io/badge/code-dongjae0107%2FELite-181717?logo=github&logoColor=white)](https://github.com/dongjae0107/ELite)
![compute](https://img.shields.io/badge/compute-CPU%20%C2%B7%20%E7%BA%A6%203%20h-6f42c1)

[快速开始](#快速开始) &nbsp;•&nbsp; [结果](#结果) &nbsp;•&nbsp; [说明](#说明)

*[索引](../README.md) &nbsp;•&nbsp; [论文报告值](paper_baseline.md) &nbsp;•&nbsp; [复现脚本](reproduce.py) &nbsp;•&nbsp; [回测基线](baselines.json)*

</div>

ELite 为每个体素估计临时性，用它决定多会话地图更新时每个点的去留。官方流程分两段：先建第一段会话的地图，再把第二段会话对齐并更新进去。

|  |  |
| :--- | :--- |
| 结果 | AC 0.9708 / RMSE 0.0678 m / CD 0.0902 m（论文表 I 0.969 / 0.090 / 0.133） |
| 对照 | 同表 ICP 0.962 / 0.117 / 0.194，LT-mapper 0.968 / 0.121 / 0.175 |
| 数据 | 作者的 ParkingLot 多会话数据集 |
| 耗时 | 两段 config 合计约 3 h（CPU） |
| 复现 | `python3 reproductions/run_all.py --only 01-11` |

---

## 快速开始

| 依赖 | 版本 |
| :--- | :--- |
| Python | `.venvs/elite`：python 3.10 + open3d 0.18 + numpy<2 |
| 数据 | ParkingLot，Google Drive，需要分块请求绕开配额页 |

```bash
python3 reproductions/tools/gdrive_range_fetch.py <file-id> code/ELite/data/parkinglot/01.zip
python3 reproductions/run_all.py --only 01-11
```

## 结果

| 指标 | 本文件夹 | 论文表 I | 同表 ICP / LT-mapper |
| :--- | ---: | ---: | ---: |
| AC | 0.9708 | 0.969 | 0.962 / 0.968 |
| RMSE | 0.0678 m | 0.090 | 0.117 / 0.121 |
| CD | 0.0902 m | 0.133 | 0.194 / 0.175 |

论文没有说明 Table I 比对的是哪两张点云。换用合并后的 lifelong 图是 0.9989 / 0.0833 / 0.1377，两种配对都记录在 `results/` 下。

## 说明

- 多会话对齐需要一个人工给出的初始变换，作者的 README 说全局定位器仍在计划中，所以这条链不是端到端自动的。
- 两条长任务必须串行运行，并发会被系统 OOM 杀掉（实测过一次，日志显示倒在 scan 331）。
- Open3D 0.18 需要 numpy<2，且 `combined += pcd` 的逐帧累加会段错误，补丁改成一次性 vstack。

## 文档

- 论文自报数字与出处：[`paper_baseline.md`](paper_baseline.md)
- 复现脚本与回测基线：[`reproduce.py`](reproduce.py) · [`baselines.json`](baselines.json)
- 本文件夹的脚本与实测记录：[`work/`](work/)
- 复现区索引：[`../README.md`](../README.md)
