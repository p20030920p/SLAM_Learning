<div align="center">

# SLAM_Learning

**一个用于验证想法的 SLAM 平台：一台全向小车、一个赛场，以及已经接好的三件事 —— 建图、定位、规划。把一个方法丢进来，把车开一圈，就知道这个想法行不行。**

[![ROS 2](https://img.shields.io/badge/ROS%202-Jazzy-22314E?logo=ros&logoColor=white)](https://docs.ros.org/en/jazzy/)
[![Gazebo](https://img.shields.io/badge/Gazebo%20Sim-8-F58113?logo=gazebo&logoColor=white)](https://gazebosim.org/)
[![License](https://img.shields.io/badge/license-MIT-3DA639)](LICENSE)

[复现清单](#复现清单-reproduction-checklist) &nbsp;•&nbsp; [快速开始](#快速开始) &nbsp;•&nbsp; [平台](#平台) &nbsp;•&nbsp; [详细文档](docs/platform.md)

*[English](README.md) &nbsp;|&nbsp; 中文*

</div>

<p align="center">
  <img src="docs/images/01_mapping.png" width="860" alt="slam_toolbox 在小车行进中构建赛场地图"/>
</p>

<p align="center">
  <em>建图：小车在 Gazebo 中行驶，slam_toolbox 用仿真激光雷达把地图一点点长出来。</em>
</p>

## 这是什么

一个一次验证一个想法的试验台。机器人、传感器、地图与评测都已经接好，
把一个建图、定位或规划方法丢进来就能开跑。

它不是基准，也不是自主系统：没有排行榜与固定协议，也没有感知到决策到安全那条链。
复现别人的论文并对齐他们自己的数字，是 [`reproductions/`](reproductions/) 的事。

|  |  |
| :--- | :--- |
| 机器人 | 三轮全向小车，单线 360 度 2D 雷达（`/scan`），前置 RGB 相机 |
| 技术栈 | ROS 2 Jazzy、Gazebo Sim 8、slam_toolbox、AMCL、Nav2 加 A* 全局规划器 |
| 范围 | 建图、定位、规划。没有硬件驱动，也没有标定流程 |
| 来源 | 从 [Sim2Real-AlgoBench](https://github.com/p20030920p/Sim2Real-AlgoBench) 抽出的建模、建图、定位与规划底座，算法库已删除 |

<!-- PROGRESS:START -->

## 复现清单 Reproduction checklist

**按「越好复现 + 越能对上原库结果」排序** —— 完成 12 · 半完成 2 · 阻塞 7（共 21） · 更新于 2026-10-06 16:22 CST

| # | 状态 | 复现库 | 论文 | 一句话 |
| :-- | :-- | :-- | :-- | :-- |
| 01-05 | 完成 | [KTH-RPL/dufomap](https://github.com/KTH-RPL/dufomap) | [doi:10.1109/LRA.2024.3387658](https://doi.org/10.1109/LRA.2024.3387658) | 能。与论文表 I 两位小数一致。 |
| 01-06 | 完成 | [MKJia/BeautyMap](https://github.com/MKJia/BeautyMap) | [arXiv:2405.07283](https://arxiv.org/abs/2405.07283) | 能。命中论文表 I。 |
| 01-01 | 完成 | [KTH-RPL/DynamicMap_Benchmark](https://github.com/KTH-RPL/DynamicMap_Benchmark) | [arXiv:2307.07260](https://arxiv.org/abs/2307.07260) | 能。官方评测器加 Zenodo 免注册数据，四个方法同表。 |
| 01-03 | 完成 | [LimHyungTae/ERASOR](https://github.com/LimHyungTae/ERASOR) | [arXiv:2103.04316](https://arxiv.org/abs/2103.04316) | 能，需 ROS 1。官方仓库对上论文表 II。 |
| 01-04 | 完成 | [irapkaist/removert](https://github.com/irapkaist/removert) | [doi:10.1109/IROS45743.2020.9340856](https://doi.org/10.1109/IROS45743.2020.9340856) | 能，需 ROS 1。官方实现 SA/DA/AA 99.62/89.25/94.29。 |
| 01-08 | 完成 | [yuhaozhang7/NGD-SLAM](https://github.com/yuhaozhang7/NGD-SLAM) | [arXiv:2405.07392](https://arxiv.org/abs/2405.07392) | 能。纯 CPU，ATE 0.0157 m。 |
| 01-02 | 完成 | [PRBonn/kiss-icp](https://github.com/PRBonn/kiss-icp) | [doi:10.1109/LRA.2023.3236571](https://doi.org/10.1109/LRA.2023.3236571) | 能。PyPI 包加官方 KITTI 00–10，均值 0.53 %。 |
| 01-10 | 完成 | [cocel-postech/genz-icp](https://github.com/cocel-postech/genz-icp) | [arXiv:2411.06766](https://arxiv.org/abs/2411.06766) | 能。均值 0.52 %，论文 0.51 %。 |
| 01-09 | 半完成 | [gisbi-kim/lt-mapper](https://github.com/gisbi-kim/lt-mapper) | [arXiv:2107.07712](https://arxiv.org/abs/2107.07712) | 半能。仓库只有变化检测半边。 |
| 01-11 | 完成 | [dongjae0107/ELite](https://github.com/dongjae0107/ELite) | [arXiv:2502.13452](https://arxiv.org/abs/2502.13452) | 能。AC 0.9708，论文 0.969，纯 CPU。 |
| 01-12 | 完成 | [UZ-SLAMLab/ORB_SLAM3](https://github.com/UZ-SLAMLab/ORB_SLAM3) | [arXiv:2007.11898](https://arxiv.org/abs/2007.11898) | 能。纯 CPU，RMSE ATE 0.035 至 0.045 m。 |
| 01-13 | 阻塞 | [MIT-SPARK/Khronos](https://github.com/MIT-SPARK/Khronos) | [arXiv:2402.13817](https://arxiv.org/abs/2402.13817) | 不能。实测需要 13.5 GB 以上内存。 |
| 02-01 | 半完成 | [WaldJohannaU/3RScan](https://github.com/WaldJohannaU/3RScan) | [arXiv:1908.06109](https://arxiv.org/abs/1908.06109) | 半能。只有数据集与工具，全量数据需申请。 |
| 02-06 | 阻塞 | [MIT-SPARK/Clio](https://github.com/MIT-SPARK/Clio) | [arXiv:2404.13696](https://arxiv.org/abs/2404.13696) | 不能。论文用 RTX 3090。 |
| 02-07 | 完成 | [AnyLoc/AnyLoc](https://github.com/AnyLoc/AnyLoc) | [arXiv:2308.00688](https://arxiv.org/abs/2308.00688) | 能。纯 CPU 约 3.3 h，R@1 65.0 与论文一致。 |
| 02-08 | 完成 | [AnyLoc/Revisit-Anything](https://github.com/AnyLoc/Revisit-Anything) | [arXiv:2409.18049](https://arxiv.org/abs/2409.18049) | 能。纯 CPU 约 25 min，R@1 95.32 与论文一致。 |
| 02-03 | 阻塞 | [concept-graphs/concept-graphs](https://github.com/concept-graphs/concept-graphs) | [arXiv:2309.16650](https://arxiv.org/abs/2309.16650) | 不能。需 16 至 24 GB 显存与 GPT-4 key。 |
| 02-04 | 阻塞 | [Eku127/DualMap](https://github.com/Eku127/DualMap) | [arXiv:2506.01950](https://arxiv.org/abs/2506.01950) | 不能。论文用 RTX 4090。 |
| 02-05 | 阻塞 | [hovsg/HOV-SG](https://github.com/hovsg/HOV-SG) | [arXiv:2403.17846](https://arxiv.org/abs/2403.17846) | 不能。四篇底座里算力最重，论文未写门槛。 |
| 01-07 | 阻塞 | [ACFR-RPG/DynoSAM](https://github.com/ACFR-RPG/DynoSAM) | [arXiv:2501.11893](https://arxiv.org/abs/2501.11893) | 不能。configure 阶段就要求 CUDA。 |
| 02-02 | 阻塞 | — | [arXiv:2607.14899](https://arxiv.org/abs/2607.14899) | 不能。代码未发布。 |

> 状态：完成 = 已对上原库数字 · 半完成 = 只做了仓库里有的那一半 · 阻塞 = 本机做不了（缺硬件或没有代码）。
> 每一行的字段写在对应文件夹的 `baselines.json` 里，本表由 `python3 reproductions/run_all.py` 生成，块内不要手改。
<!-- PROGRESS:END -->

## 快速开始

```bash
git clone https://github.com/p20030920p/SLAM_Learning.git
cd SLAM_Learning
source /opt/ros/jazzy/setup.bash
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
```

仓库带三个流程：

| Launch | 作用 |
| :--- | :--- |
| `mapping.launch.py` | 开动小车，用 slam_toolbox 建图 |
| `localization_navigation.launch.py` | 在已保存的地图上定位，并用 A* 规划 |
| `navigation_slam.launch.py` | 边导航边建图 |

规划器配置与验证记录见 [`docs/platform.md`](docs/platform.md)。

## 平台

| 层 | 包 | 里面是什么 |
| :--- | :--- | :--- |
| 建模 | `race_description` · `race_gazebo` · `race_bringup` | 全向小车 URDF 与网格、赛场世界、仿真启动 |
| 控制 | `race_control` | 一个节点：`Twist` 转 `TwistStamped`，让 Nav2 与遥控能驱动轮子 |
| 建图 | `race_navigation` | slam_toolbox 配置与建图 launch |
| 定位 | `race_navigation` | 为全向底盘调过的 AMCL，以及保存好的赛场地图 |
| 规划 | `algo_core` · `algo_nav2_plugins` | 八邻域代价栅格上的 A*，以及把它接进 Nav2 的适配器 |

相机的图像是 RGB，没有深度也没有 IMU，所以视觉惯性融合在这个仿真里还跑不了。
赛场、传感器配置与仿真到实机的差距写在 [`docs/platform.md`](docs/platform.md)。

## 文档

| 位置 | 内容 |
| :--- | :--- |
| [`docs/platform.md`](docs/platform.md) | 流程、规划器配置、赛场与传感器、验证记录 |
| [`reproductions/`](reproductions/) | 论文复现区：一篇论文一个文件夹，清单见上 |
| [`docs/task-book/TASK_BOOK.md`](docs/task-book/TASK_BOOK.md) | 两个研究方向所依据的任务书 |
| [`car.md`](car.md) | 八个难点，每个配一条可否证的假设 |

## 许可

MIT，见 [LICENSE](LICENSE)。派生自
[Sim2Real-AlgoBench](https://github.com/p20030920p/Sim2Real-AlgoBench)，作者 p20030920p 与 zfyyyyy。
