<div align="center">

# 01-06 BeautyMap

**BeautyMap: Binary-Encoded Adaptable Ground Matrix**

用二值编码的地面矩阵取代阈值，免调参的动态点删除。

[![venue](https://img.shields.io/badge/venue-RA--L%202024-22314E)](https://arxiv.org/abs/2405.07283)
![result](https://img.shields.io/badge/result-hit%20Table%20I-2ea043)
[![code](https://img.shields.io/badge/code-MKJia%2FBeautyMap-181717?logo=github&logoColor=white)](https://github.com/MKJia/BeautyMap)
![compute](https://img.shields.io/badge/compute-CPU-6f42c1)

[快速开始](#快速开始) &nbsp;•&nbsp; [结果](#结果) &nbsp;•&nbsp; [说明](#说明)

*[索引](../README.md) &nbsp;•&nbsp; [论文报告值](paper_baseline.md) &nbsp;•&nbsp; [复现脚本](reproduce.py) &nbsp;•&nbsp; [回测基线](baselines.json)*

</div>

BeautyMap 不设删除阈值，用二值编码的地面矩阵表达地面与障碍，路线是免调参。

|  |  |
| :--- | :--- |
| 结果 | SA/DA/HA = 96.95 / 98.34 / 97.64（论文 96.76 / 98.38 / 97.56） |
| 数据 | KITTI 00 |
| 特点 | 没有需要标定的删除阈值 |
| 复现 | `python3 reproductions/run_all.py --only 01-06` |

---

## 快速开始

| 依赖 | 版本 |
| :--- | :--- |
| Python | 官方仓库脚本 + `.venvs/dmb` |
| 数据 | KITTI 00 |

```bash
python3 reproductions/run_all.py --only 01-06
```

## 结果

| 指标 | 本文件夹 | 论文表 I |
| :--- | ---: | ---: |
| SA / DA / HA | 96.95 / 98.34 / 97.64 | 96.76 / 98.38 / 97.56 |

四个清理方法里唯一 SA 与 DA 都过 96 的一个。

## 说明

- 免调参是它相对 01-03 的主要区别，代价是场景先验依赖地面矩阵的表达能力。

## 文档

- 论文自报数字与出处：[`paper_baseline.md`](paper_baseline.md)
- 复现脚本与回测基线：[`reproduce.py`](reproduce.py) · [`baselines.json`](baselines.json)
- 本文件夹的脚本与实测记录：[`work/`](work/)
- 复现区索引：[`../README.md`](../README.md)
