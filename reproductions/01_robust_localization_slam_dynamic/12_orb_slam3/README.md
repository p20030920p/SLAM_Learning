<div align="center">

# 01-12 ORB-SLAM3

**ORB-SLAM3: Visual, Visual-Inertial and Multi-Map SLAM**

视觉、视觉惯性与多地图 SLAM 的经典实现。

[![venue](https://img.shields.io/badge/venue-T--RO%202021-22314E)](https://arxiv.org/abs/2007.11898)
![result](https://img.shields.io/badge/result-ATE%200.035%E2%80%930.045%20m%20vs%200.036-2ea043)
[![code](https://img.shields.io/badge/code-UZ--SLAMLab%2FORB__SLAM3-181717?logo=github&logoColor=white)](https://github.com/UZ-SLAMLab/ORB_SLAM3)
![compute](https://img.shields.io/badge/compute-CPU%20%C2%B7%20%E4%B8%8D%E7%94%A8%20ROS-6f42c1)

[快速开始](#快速开始) &nbsp;•&nbsp; [结果](#结果) &nbsp;•&nbsp; [说明](#说明)

*[索引](../README.md) &nbsp;•&nbsp; [论文报告值](paper_baseline.md) &nbsp;•&nbsp; [复现脚本](reproduce.py) &nbsp;•&nbsp; [回测基线](baselines.json)*

</div>

这条复现对应任务书里的相机半边：实物是 D435i，仓库自带 stereo-inertial 例子与 RealSense D435i 配置文件，是最短的一条对上实物配置的路径。

|  |  |
| :--- | :--- |
| 结果 | EuRoC MH_01 双目惯性 RMSE ATE 0.0454 / 0.0351 / 0.0416 m（论文 0.036 m） |
| 数据 | EuRoC MH_01，ETH 源连不上，改用 HuggingFace 镜像 |
| 评测 | 仓库自带的 evaluate_ate_scale.py |
| 复现 | `bash work/run_euroc.sh` |

---

## 快速开始

| 依赖 | 版本 |
| :--- | :--- |
| 构建 | 自编 Pangolin v0.8 与 ORB-SLAM3，不需要 ROS |
| 数据 | EuRoC MH_01（ASL 格式） |

```bash
bash reproductions/01_robust_localization_slam_dynamic/12_orb_slam3/work/run_euroc.sh
python3 reproductions/run_all.py --only 01-12
```

## 结果

三次运行的 RMSE ATE 为 0.0454 / 0.0351 / 0.0416 m，论文表 II 是 0.036 m。最好的一次几乎命中，三次散布把论文值夹在中间。

## 说明

- 编译有三处必须显式说明的改动（不是算法改动），记在 README 的旧版本与 `work/` 里。
- 这条是 D1 里唯一吃 D435i 那套传感器配置的复现。

## 文档

- 论文自报数字与出处：[`paper_baseline.md`](paper_baseline.md)
- 复现脚本与回测基线：[`reproduce.py`](reproduce.py) · [`baselines.json`](baselines.json)
- 本文件夹的脚本与实测记录：[`work/`](work/)
- 复现区索引：[`../README.md`](../README.md)
