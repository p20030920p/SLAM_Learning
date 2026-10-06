<div align="center">

# 01-02 KISS-ICP

**KISS-ICP: In Defense of Point-to-Point ICP**

只用点对点 ICP 的 LiDAR 里程计，在官方 KITTI 00–10 全量上跑。

[![venue](https://img.shields.io/badge/venue-RA--L%202023-22314E)](https://doi.org/10.1109/LRA.2023.3236571)
![result](https://img.shields.io/badge/result-0.53%25%20vs%200.50%25%20paper-2ea043)
[![code](https://img.shields.io/badge/code-PRBonn%2Fkiss--icp-181717?logo=github&logoColor=white)](https://github.com/PRBonn/kiss-icp)
![compute](https://img.shields.io/badge/compute-CPU%20%C2%B7%20PyPI-6f42c1)

[快速开始](#快速开始) &nbsp;•&nbsp; [结果](#结果) &nbsp;•&nbsp; [说明](#说明)

*[索引](../README.md) &nbsp;•&nbsp; [论文报告值](paper_baseline.md) &nbsp;•&nbsp; [复现脚本](reproduce.py) &nbsp;•&nbsp; [回测基线](baselines.json)*

</div>

KISS-ICP 主张朴素点对点 ICP 配上正确的实现细节就能达到 SOTA 精度。这里在官方 KITTI 00–10 全量上复核，并把它当作下游定位器，检验清理后的地图是否真的更好用。

|  |  |
| :--- | :--- |
| 结果 | 23,201 帧平均相对平移误差 0.53 %（论文 0.50 %） |
| 数据 | KITTI odometry 00–10，从官方 84.8 GB 包里按字节区间只取 11 条序列 |
| 下游 | 6 张清理地图 × 141 帧 × 4 档初值误差的配准实验 |
| 复现 | `python3 reproductions/run_all.py --only 01-02` |

---

## 快速开始

| 依赖 | 版本 |
| :--- | :--- |
| Python | PyPI `kiss-icp==1.3.0` + `.venvs/dmb` |
| 数据 | KITTI 00–10，43 GB，免注册 |

```bash
python3 reproductions/run_all.py --only 01-02
```

## 结果

逐序列数字与作者发布的已执行 notebook 同表，均值 0.53 %，论文表 II 是 0.50 %。

下游可用性：ρ(归一化 AA, 定位效用) = 0.78，ρ(提交口径 AA) = 0.38，两者不一致（图见 [`results/h1prime.png`](results/h1prime.png)）。

## 说明

- 数据下载是一条一条按字节区间取的，脚本见 `work/fetch_kitti_odometry.py`。
- H1′ 的两种排名在这里第一次被算出来，后续 01-01 的量表用它做下游检验。

## 文档

- 论文自报数字与出处：[`paper_baseline.md`](paper_baseline.md)
- 复现脚本与回测基线：[`reproduce.py`](reproduce.py) · [`baselines.json`](baselines.json)
- 本文件夹的脚本与实测记录：[`work/`](work/)
- 复现区索引：[`../README.md`](../README.md)
