<div align="center">

# 01-04 Removert

**Removert: Remove then Revert**

先从距离图像删可疑点，再用多分辨率图像把误删的静态点找回来。

[![venue](https://img.shields.io/badge/venue-IROS%202020-22314E)](https://doi.org/10.1109/IROS45743.2020.9340856)
![result](https://img.shields.io/badge/result-DA%2089.25%20vs%2041.53%20port-2ea043)
[![code](https://img.shields.io/badge/code-irapkaist%2Fremovert-181717?logo=github&logoColor=white)](https://github.com/irapkaist/removert)
![compute](https://img.shields.io/badge/compute-ROS%201%20Noetic-6f42c1)

[快速开始](#快速开始) &nbsp;•&nbsp; [结果](#结果) &nbsp;•&nbsp; [说明](#说明)

*[索引](../README.md) &nbsp;•&nbsp; [论文报告值](paper_baseline.md) &nbsp;•&nbsp; [复现脚本](reproduce.py) &nbsp;•&nbsp; [回测基线](baselines.json)*

</div>

Removert 先删除再回滚，是这批方法里最保守的一个。这里用作者自己的仓库复核它的实际行为，并与基准里的重实现对照。

|  |  |
| :--- | :--- |
| 结果 | 官方实现 SA/DA/AA = 99.62 / 89.25 / 94.29 |
| 对照 | 同一份数据、同一个点级评分下，基准重实现是 99.44 / 41.53 / 64.26 |
| 论文 | 原文没有编号表格，对标的是官方实现自己的输出 |
| 耗时 | 141 帧 76 s（CPU） |
| 复现 | `bash work/run_official.sh` |

---

## 快速开始

| 依赖 | 版本 |
| :--- | :--- |
| ROS | ROS 1 Noetic（micromamba） |
| 数据 | KITTI 00，141 帧，免注册 |

```bash
source reproductions/tools/ros1_env.sh
bash reproductions/01_robust_localization_slam_dynamic/04_removert/work/run_official.sh
python3 reproductions/run_all.py --only 01-04
```

## 结果

| 同一份数据、同一个评分器 | SA | DA | AA |
| :--- | ---: | ---: | ---: |
| 官方仓库 | 99.62 | 89.25 | 94.29 |
| 基准里的重实现 | 99.44 | 41.53 | 64.26 |

DA 差 47.7 个百分点。「Removert 最保守」是重实现的产物，不是方法本身的性质。

## 说明

- 论文原文没有编号结果表（PDF 全文检索 TABLE 命中 0 次），所以只能与官方实现自己的输出对齐。
- 这条对照说明：拿重实现当某个方法的代理，会系统性地改变它在排行榜上的位置。

## 文档

- 论文自报数字与出处：[`paper_baseline.md`](paper_baseline.md)
- 复现脚本与回测基线：[`reproduce.py`](reproduce.py) · [`baselines.json`](baselines.json)
- 本文件夹的脚本与实测记录：[`work/`](work/)
- 复现区索引：[`../README.md`](../README.md)
