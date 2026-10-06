<div align="center">

# 01-10 GenZ-ICP

**GenZ-ICP: Generalizable and Degeneracy-Robust LiDAR Odometry**

按残差稀疏与稠密程度自适应加权的退化鲁棒 LiDAR 里程计。

[![venue](https://img.shields.io/badge/venue-RA--L%202025-22314E)](https://arxiv.org/abs/2411.06766)
![result](https://img.shields.io/badge/result-0.52%25%20vs%200.51%25-2ea043)
[![code](https://img.shields.io/badge/code-cocel--postech%2Fgenz--icp-181717?logo=github&logoColor=white)](https://github.com/cocel-postech/genz-icp)
![compute](https://img.shields.io/badge/compute-CPU%20%C2%B7%20PyPI-6f42c1)

[快速开始](#快速开始) &nbsp;•&nbsp; [结果](#结果) &nbsp;•&nbsp; [说明](#说明)

*[索引](../README.md) &nbsp;•&nbsp; [论文报告值](paper_baseline.md) &nbsp;•&nbsp; [复现脚本](reproduce.py) &nbsp;•&nbsp; [回测基线](baselines.json)*

</div>

GenZ-ICP 在退化场景里根据残差分布自适应地调整权重，与 KISS-ICP 共用同一套数据与指标，可以直接并排比较。

|  |  |
| :--- | :--- |
| 结果 | KITTI 00–10 平均相对平移误差 0.52 %（论文 0.51 %） |
| 对照 | 同一份数据上 KISS-ICP 为 0.53 %（01-02） |
| 数据 | 复用 01-02 已下载的官方 KITTI 00–10 |
| 复现 | `python3 reproductions/run_all.py --only 01-10` |

---

## 快速开始

| 依赖 | 版本 |
| :--- | :--- |
| Python | PyPI `genz-icp`，自带预调 `kitti.yaml` |
| 数据 | KITTI 00–10（软链接复用） |

```bash
python3 reproductions/run_all.py --only 01-10
```

## 结果

| 方法 | 同一份 KITTI 00–10，23,201 帧 | 论文 |
| :--- | ---: | ---: |
| GenZ-ICP | 0.52 % | 0.51 % |
| KISS-ICP | 0.53 % | 0.50 % |

两条方法同数据同指标并排，与论文表 III 的排法一致。

## 说明

- 两个坑记在 `work/run_genz.py` 的 docstring 里，都与配置读取有关。

## 文档

- 论文自报数字与出处：[`paper_baseline.md`](paper_baseline.md)
- 复现脚本与回测基线：[`reproduce.py`](reproduce.py) · [`baselines.json`](baselines.json)
- 本文件夹的脚本与实测记录：[`work/`](work/)
- 复现区索引：[`../README.md`](../README.md)
