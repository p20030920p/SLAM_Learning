<div align="center">

# 01-01 DynamicMap_Benchmark

**A Dynamic Points Removal Benchmark in Point Cloud Maps**

把动态点删除放到同一把尺子上：一份点级真值、一套评测规则、四个方法同台。

[![venue](https://img.shields.io/badge/venue-ITSC%202023-22314E)](https://arxiv.org/abs/2307.07260)
![result](https://img.shields.io/badge/result-4%2F4%20methods%20scored-2ea043)
[![code](https://img.shields.io/badge/code-KTH--RPL%2FDynamicMap__Benchmark-181717?logo=github&logoColor=white)](https://github.com/KTH-RPL/DynamicMap_Benchmark)
![compute](https://img.shields.io/badge/compute-CPU-6f42c1)

[快速开始](#快速开始) &nbsp;•&nbsp; [结果](#结果) &nbsp;•&nbsp; [说明](#说明)

*[索引](../README.md) &nbsp;•&nbsp; [论文报告值](paper_baseline.md) &nbsp;•&nbsp; [复现脚本](reproduce.py) &nbsp;•&nbsp; [回测基线](baselines.json)*

</div>

这是本复现区的地基：一份 141 帧的点级真值、一套统一的评测规则，四个清理方法在同一口径下排名，再用下游定位效果检验这些排名是否可信。

|  |  |
| :--- | :--- |
| 数据 | 141 帧 · 17,362,230 个真值点 · 动态点占 0.55 % |
| 评测器 | 官方 C++ 与独立 scipy 重写，在 300 万点上 0 处分歧 |
| 四个方法 | SA 排名 Removert > DUFOMap > BeautyMap > ERASOR |
| 下游检验 | ρ(归一化 AA, 定位效用) = 0.78，ρ(提交口径 AA) = 0.38，ρ(SA) = 0.23 |
| 复现 | `python3 reproductions/run_all.py --only 01-01` |

---

## 快速开始

| 依赖 | 版本 |
| :--- | :--- |
| Python | python3 + `.venvs/dmb` |
| 数据 | Zenodo 包 00.zip（385 MB，免注册） |

```bash
python3 reproductions/run_all.py --only 01-01
```

## 结果

四个方法的指标与论文表 I 的对照见 [`results/`](results/)。下游配准实验用 6 张清理后的地图 × 141 帧 × 4 档初值误差。

误删分层（[`results/observability_strata.png`](results/observability_strata.png)）：Removert 官方在「从没被看到」的点上误删率是「每帧都看得到」的 51 倍，而体素化到 0.2 m 的地图这条曲线反过来，说明那些「误删」其实是分辨率而不是误分类。

## 说明

- 动态点只占 0.55 %，所以 SA 高不代表方法好，DA/AA 才是区分度所在。
- 指标排名与定位可用性排名不一致，这是本方向 H1′ 假设的直接证据。
- 四个方法的数字都在同一份真值与同一套评分代码下产生。

## 文档

- 论文自报数字与出处：[`paper_baseline.md`](paper_baseline.md)
- 复现脚本与回测基线：[`reproduce.py`](reproduce.py) · [`baselines.json`](baselines.json)
- 本文件夹的脚本与实测记录：[`work/`](work/)
- 复现区索引：[`../README.md`](../README.md)
