<div align="center">

# 01-05 DUFOMap

**DUFOMap: Efficient Dynamic Awareness Mapping**

用光线投射显式建模遮挡，区分「这次被挡住了」和「真的动了」。

[![venue](https://img.shields.io/badge/venue-RA--L%202024-22314E)](https://doi.org/10.1109/LRA.2024.3387658)
![result](https://img.shields.io/badge/result-exact%20match-2ea043)
[![code](https://img.shields.io/badge/code-KTH--RPL%2Fdufomap-181717?logo=github&logoColor=white)](https://github.com/KTH-RPL/dufomap)
![compute](https://img.shields.io/badge/compute-CPU%20%C2%B7%20PyPI-6f42c1)

[快速开始](#快速开始) &nbsp;•&nbsp; [结果](#结果) &nbsp;•&nbsp; [说明](#说明)

*[索引](../README.md) &nbsp;•&nbsp; [论文报告值](paper_baseline.md) &nbsp;•&nbsp; [复现脚本](reproduce.py) &nbsp;•&nbsp; [回测基线](baselines.json)*

</div>

DUFOMap 用光线投射判断一个点是被遮挡还是真的移动了，属于「可观测性」这条线最直接的方法实现。

|  |  |
| :--- | :--- |
| 结果 | SA/DA/AA = 97.96 / 98.72 / 98.34（论文表 I 同值） |
| 数据 | KITTI 00，经基准打包，免注册 |
| 参数 | 论文默认 `d_p = 1` |
| 复现 | `python3 reproductions/run_all.py --only 01-05` |

---

## 快速开始

| 依赖 | 版本 |
| :--- | :--- |
| Python | PyPI `dufomap==1.1.1` + `.venvs/dmb` |
| 数据 | KITTI 00 |

```bash
python3 reproductions/run_all.py --only 01-05
```

## 结果

与论文表 I 两位小数完全一致。

需要注意参数：上游示例脚本传 `d_p = 2` 并注释 same with paper，但论文的默认值是 `d_p = 1`。只有 1 命中论文，2 的 AA 差 0.09。

## 说明

- 文档里的默认值与示例脚本不一致是这类复现最常见的坑，本条目把它记在明面上。
- SA 与 DA 都过 97，是四个清理方法里最均衡的一个。

## 文档

- 论文自报数字与出处：[`paper_baseline.md`](paper_baseline.md)
- 复现脚本与回测基线：[`reproduce.py`](reproduce.py) · [`baselines.json`](baselines.json)
- 本文件夹的脚本与实测记录：[`work/`](work/)
- 复现区索引：[`../README.md`](../README.md)
