<div align="center">

# SLAM_Learning

**A ROS 2 Jazzy and Gazebo arena for SLAM practice: one omnidirectional robot, and the three pieces that matter already wired up — mapping, localization, planning. Drop a method in, drive the robot, and see whether the idea works.**

[![ROS 2](https://img.shields.io/badge/ROS%202-Jazzy-22314E?logo=ros&logoColor=white)](https://docs.ros.org/en/jazzy/)
[![Gazebo](https://img.shields.io/badge/Gazebo%20Sim-8-F58113?logo=gazebo&logoColor=white)](https://gazebosim.org/)
[![License](https://img.shields.io/badge/license-MIT-3DA639)](LICENSE)

[Reproduction checklist](#复现清单-reproduction-checklist) &nbsp;•&nbsp; [Quick start](#quick-start) &nbsp;•&nbsp; [The platform](#the-platform) &nbsp;•&nbsp; [Details](docs/platform.md)

*English &nbsp;|&nbsp; [中文](README.zh-CN.md)*

</div>

<p align="center">
  <img src="docs/images/01_mapping.png" width="860" alt="slam_toolbox building the arena map while the robot drives through Gazebo"/>
</p>

<p align="center">
  <em>Mapping: slam_toolbox grows the map from the simulated lidar while the arena runs in Gazebo.</em>
</p>

## What this is

A testbed for validating one idea at a time. The robot, the sensors, the map and the evaluation are
already wired up, so a new mapping, localization or planning method can be dropped in and driven.

It is not a benchmark and not an autonomy stack. There is no leaderboard and no fixed protocol, and
there is no perception to decision to safety chain. Reproducing other people's papers against their
own numbers is what [`reproductions/`](reproductions/) is for.

|  |  |
| :--- | :--- |
| Robot | three-wheeled omni car, single-plane 360 degree 2D lidar on `/scan`, front RGB camera |
| Stack | ROS 2 Jazzy, Gazebo Sim 8, slam_toolbox, AMCL, Nav2 with an A* global planner |
| Scope | mapping, localization, planning. No hardware drivers, no calibration pipeline |
| Origin | the modelling, mapping, localization and planning base of [Sim2Real-AlgoBench](https://github.com/p20030920p/Sim2Real-AlgoBench), with its algorithm zoo removed |

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

## Quick start

```bash
git clone https://github.com/p20030920p/SLAM_Learning.git
cd SLAM_Learning
source /opt/ros/jazzy/setup.bash
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
```

Three workflows ship with it:

| Launch | What it does |
| :--- | :--- |
| `mapping.launch.py` | drive the robot and build a map with slam_toolbox |
| `localization_navigation.launch.py` | localize against a saved map and plan with A* |
| `navigation_slam.launch.py` | map while navigating |

Planner configuration and the verification log are in [`docs/platform.md`](docs/platform.md).

## The platform

| Layer | Package | What it holds |
| :--- | :--- | :--- |
| Modelling | `race_description` · `race_gazebo` · `race_bringup` | the omni car URDF and meshes, the arena world, simulation bring-up |
| Control | `race_control` | one node: `Twist` to `TwistStamped`, so Nav2 and teleop can drive the wheels |
| Mapping | `race_navigation` | slam_toolbox configuration and the mapping launch |
| Localization | `race_navigation` | AMCL tuned for the holonomic chassis, plus the saved arena map |
| Planning | `algo_core` · `algo_nav2_plugins` | A* over an 8-connected cost grid, and the Nav2 adapter that runs it |

The camera is RGB only, with no depth and no IMU, so visual-inertial fusion cannot be exercised in
this simulator yet. The arena, the sensor rig and the sim-to-hardware gap are in
[`docs/platform.md`](docs/platform.md).

## Documentation

| Where | What |
| :--- | :--- |
| [`docs/platform.md`](docs/platform.md) | workflows, planner configuration, arena and sensors, verification log |
| [`reproductions/`](reproductions/) | paper reproductions: one folder per paper, with the checklist above |
| [`docs/task-book/TASK_BOOK.md`](docs/task-book/TASK_BOOK.md) | the task book the two research directions come from |
| [`car.md`](car.md) | the eight difficulties, each with a falsifiable hypothesis |

## Licence

MIT, see [LICENSE](LICENSE). Derived from
[Sim2Real-AlgoBench](https://github.com/p20030920p/Sim2Real-AlgoBench) by p20030920p and zfyyyyy.
