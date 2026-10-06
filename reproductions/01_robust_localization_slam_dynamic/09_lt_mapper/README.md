<div align="center">

# 01-09 LT-mapper

**LT-mapper: A Modular Framework for LiDAR-based Lifelong Mapping**

多会话 LiDAR 长期建图框架，仓库只放了变化检测那一半。

[![venue](https://img.shields.io/badge/venue-ICRA%202022-22314E)](https://arxiv.org/abs/2107.07712)
![result](https://img.shields.io/badge/result-change--detection%20half%20only-bf8700)
[![code](https://img.shields.io/badge/code-gisbi--kim%2Flt--mapper-181717?logo=github&logoColor=white)](https://github.com/gisbi-kim/lt-mapper)
![compute](https://img.shields.io/badge/compute-ROS%201%20Noetic-6f42c1)

[快速开始](#快速开始) &nbsp;•&nbsp; [结果](#结果) &nbsp;•&nbsp; [说明](#说明)

*[索引](../README.md) &nbsp;•&nbsp; [论文报告值](paper_baseline.md) &nbsp;•&nbsp; [复现脚本](reproduce.py) &nbsp;•&nbsp; [回测基线](baselines.json)*

</div>

LT-mapper 的完整链条是多会话对齐、高低动态变化检测、正负变化管理。仓库只提供变化检测部分，这里把这一半跑通，并量化它的覆盖度代价。

|  |  |
| :--- | :--- |
| 结果 | 官方 ltremovert：SA/DA/AA = 69.14 / 74.51 / 71.78 |
| 输入 | KITTI 00 双会话切分，中心 004390–004470，查询 004451–004530 |
| 缺失 | LT-map 模块不在仓库里，论文的 85.7 MB / 9.8 s 无法复现 |
| 复现 | `bash work/run_ltremovert.sh` |

---

## 快速开始

| 依赖 | 版本 |
| :--- | :--- |
| ROS | ROS 1 Noetic（micromamba），只编 ltremovert，不链接 GTSAM |
| 输入 | KITTI 00 双会话切分，81 中心帧 + 29 查询帧 |

```bash
source reproductions/tools/ros1_env.sh
bash reproductions/01_robust_localization_slam_dynamic/09_lt_mapper/work/run_ltremovert.sh
python3 reproductions/run_all.py --only 01-09
```

## 结果

覆盖度匹配的真值下 SA/DA/AA = 69.14 / 74.51 / 71.78；未清理的对照是 99.44 / 1.65 / 5.5。

只有 71.6 % 的真值静态点被这两段会话观测到，所以这一行不能和兄弟条目直接比大小。

## 说明

- 「半个仓库」是这条复现最重要的结论：换任何环境都跑不出论文的建图数字。
- 覆盖度匹配是本条目的口径修正，否则 SA 会被未观测区域系统性抬高。

## 文档

- 论文自报数字与出处：[`paper_baseline.md`](paper_baseline.md)
- 复现脚本与回测基线：[`reproduce.py`](reproduce.py) · [`baselines.json`](baselines.json)
- 本文件夹的脚本与实测记录：[`work/`](work/)
- 复现区索引：[`../README.md`](../README.md)
