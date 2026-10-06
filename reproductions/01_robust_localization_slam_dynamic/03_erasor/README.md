<div align="center">

# 01-03 ERASOR

**Egocentric Ratio of Pseudo Occupancy-Based Dynamic Object Removal**

极坐标伪占据体素加高度比阈值，删除地图里的动态点。

[![venue](https://img.shields.io/badge/venue-RA--L%202021-22314E)](https://arxiv.org/abs/2103.04316)
![result](https://img.shields.io/badge/result-F1%200.950%20vs%200.955-2ea043)
[![code](https://img.shields.io/badge/code-LimHyungTae%2FERASOR-181717?logo=github&logoColor=white)](https://github.com/LimHyungTae/ERASOR)
![compute](https://img.shields.io/badge/compute-ROS%201%20Noetic-6f42c1)

[快速开始](#快速开始) &nbsp;•&nbsp; [结果](#结果) &nbsp;•&nbsp; [说明](#说明)

*[索引](../README.md) &nbsp;•&nbsp; [论文报告值](paper_baseline.md) &nbsp;•&nbsp; [复现脚本](reproduce.py) &nbsp;•&nbsp; [回测基线](baselines.json)*

</div>

ERASOR 把地图切成极坐标的伪占据体素，用每个体素在单次扫描中的高度比判断动静态。它是阈值敏感方法的代表，也是「删除决策没有被标定」这句话最直接的物证。

|  |  |
| :--- | :--- |
| 结果 | PR/RR/F1 = 95.62 / 94.41 / 0.950（论文表 II 93.980 / 97.081 / 0.955） |
| 自检 | 把作者自己发布的输出重打分得 93.979 / 97.081 / 0.9550，评测链一致 |
| 数据 | 官方 seq-00 rosbag 与全部 PCD/GT，作者服务器直链 |
| 耗时 | 全流程 47 s（CPU） |
| 复现 | `bash work/run_official.sh` |

---

## 快速开始

| 依赖 | 版本 |
| :--- | :--- |
| ROS | ROS 1 Noetic，用 micromamba 装，不需要 root |
| 构建 | `reproductions/tools/build_ros1_catkin.sh` |
| 数据 | 官方 seq-00 rosbag 与 PCD/GT |

```bash
source reproductions/tools/ros1_env.sh
bash reproductions/01_robust_localization_slam_dynamic/03_erasor/work/run_official.sh
python3 reproductions/run_all.py --only 01-03
```

## 结果

| 指标 | 官方仓库与数据 | 论文表 II |
| :--- | ---: | ---: |
| PR / RR / F1 | 95.62 / 94.41 / 0.950 | 93.980 / 97.081 / 0.955 |

同一份数据换成基准的点级口径，同一个方法的 SA 掉到 66.71。差的是指标，不是方法。

## 说明

- ROS 1 环境用 micromamba 建在 `reproductions/.venvs/ros1noetic`，脚本会剥掉 ROS 2 的库避免符号冲突。
- 上游有两个真 bug：`setFilterLimitsNegative` 改成 `setNegative`，`load_pcd` 的 `boost::shared_ptr` 改成 `std::shared_ptr`，补丁在 `work/local_patches.patch`。
- 阈值本身没有标定，换数据集就要重调，这一点在 01-01 的量表里体现为 SA/DA 的取舍。

## 文档

- 论文自报数字与出处：[`paper_baseline.md`](paper_baseline.md)
- 复现脚本与回测基线：[`reproduce.py`](reproduce.py) · [`baselines.json`](baselines.json)
- 本文件夹的脚本与实测记录：[`work/`](work/)
- 复现区索引：[`../README.md`](../README.md)
