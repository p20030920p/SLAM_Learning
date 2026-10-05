<div align="center">

# SLAM_Learning

**An idea-validation platform for SLAM — one omnidirectional robot, one arena, and the three pieces that matter: mapping, localization, planning. Drop a method in, drive the robot, and see whether the idea works.**

[![ROS 2](https://img.shields.io/badge/ROS%202-Jazzy-22314E?logo=ros&logoColor=white)](https://docs.ros.org/en/jazzy/)
[![Gazebo](https://img.shields.io/badge/Gazebo%20Sim-8-F58113?logo=gazebo&logoColor=white)](https://gazebosim.org/)
[![Localization](https://img.shields.io/badge/localization-AMCL-blue)](#the-platform)
[![Planner](https://img.shields.io/badge/planner-A*-brightgreen)](#the-platform)
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

## What this is — and what it is not

**This is a platform for validating ideas.** A self-contained ROS 2 Jazzy + Gazebo arena in which the
robot, the sensors, the map and the evaluation are already wired up: put a mapping, localization or
planning method in, drive the robot, and find out whether it actually works.

| What it is | What it is **not** |
| :--- | :--- |
| A testbed for **one method or idea at a time** | **Not a benchmark**: no leaderboard, no cross-paper metric, no fixed protocol. Reproducing *other people's* papers, against their own numbers, is what [`reproductions/`](reproductions/) is for |
| A **scene you control**: known geometry, known ground truth, repeatable runs | **Not an autonomy stack**: there is no perception → decision → safety chain here — only mapping, localization and planning |
| A **simulation of the robot you actually have** (2D lidar + camera) | **Not a real-robot system**: no hardware drivers, no calibration pipeline; and the camera is RGB-only — no depth, no IMU — so VIO/LIO fusion cannot be exercised here yet |
| A way to compare **two versions of your own method** under identical conditions | **Not a substitute for Sim2Real-AlgoBench**: this is the modelling / mapping / localization / planning base extracted from it, with the algorithm zoo removed on purpose |

<!-- PROGRESS:START -->

## 复现清单 Reproduction checklist

**按「越好复现 + 越能对上原库结果」排序** —— ☑ 10 · ◐ 2 · ☐ 1 · ⛔ 8（共 21） · 更新于 2026-10-06 01:23 CST

| # | ✓ | 复现库 | 对应论文 | 能不能复现（一句话） |
| :-- | :-- | :-- | :-- | :-- |
| 01-05 | ☑ | [KTH-RPL/dufomap](https://github.com/KTH-RPL/dufomap) | [doi:10.1109/LRA.2024.3387658](https://doi.org/10.1109/LRA.2024.3387658) | ✅ 能，而且最简单：`pip install dufomap` + KITTI 00 免注册数据，官方评测脚本直接出论文表 I。 |
| 01-06 | ☑ | [MKJia/BeautyMap](https://github.com/MKJia/BeautyMap) | [arXiv:2405.07283](https://arxiv.org/abs/2405.07283) | ✅ 能：官方仓库 `python main.py`，配同一套官方评测，命中论文表 I。 |
| 01-01 | ☑ | [KTH-RPL/DynamicMap_Benchmark](https://github.com/KTH-RPL/DynamicMap_Benchmark) | [arXiv:2307.07260](https://arxiv.org/abs/2307.07260) | ✅ 能：官方评测脚本 + Zenodo 免注册数据 `00.zip`，出论文里那张方法对比表。 |
| 01-03 | ☑ | [LimHyungTae/ERASOR](https://github.com/LimHyungTae/ERASOR) | [arXiv:2103.04316](https://arxiv.org/abs/2103.04316) | ✅ 能，但要 ROS 1（本机已用 micromamba 建好）：官方仓库跑通，对上论文表 II 的 PR/RR/F1。 |
| 01-04 | ☑ | [irapkaist/removert](https://github.com/irapkaist/removert) | [doi:10.1109/IROS45743.2020.9340856](https://doi.org/10.1109/IROS45743.2020.9340856) | ✅ 能，但要 ROS 1：官方仓库跑通；原论文没有数字表，对上的是官方仓库自己的输出。 |
| 01-08 | ☑ | [yuhaozhang7/NGD-SLAM](https://github.com/yuhaozhang7/NGD-SLAM) | [arXiv:2405.07392](https://arxiv.org/abs/2405.07392) | ✅ 能：官方代码明确「无 GPU」，TUM RGB-D 免注册直链，对上论文的 ATE / RPE 表。 |
| 01-02 | ☑ | [PRBonn/kiss-icp](https://github.com/PRBonn/kiss-icp) | [doi:10.1109/LRA.2023.3236571](https://doi.org/10.1109/LRA.2023.3236571) | ✅ 能：`pip install kiss-icp` + 官方 84.8 GB zip 里只取 00–10（43 GB，免注册），跑作者自己的 `eval/kitti.ipynb` 等价脚本即出论文表 II。 |
| 01-10 | ☑ | [cocel-postech/genz-icp](https://github.com/cocel-postech/genz-icp) | [arXiv:2411.06766](https://arxiv.org/abs/2411.06766) | ✅ 能：`pip install genz-icp pyyaml` + 已经在手的 KITTI 00–10，跑 `kitti.yaml` 预调参数即出论文表 III。 |
| 01-09 | ◐ | [gisbi-kim/lt-mapper](https://github.com/gisbi-kim/lt-mapper) | [arXiv:2107.07712](https://arxiv.org/abs/2107.07712) | 🟡 半能：要 ROS 1 + MulRan（需注册）+ 先有 SC-LIO-SAM 会话；仓库只有 ltremovert 半边，lt-map 无代码。 |
| 01-11 | ☑ | [dongjae0107/ELite](https://github.com/dongjae0107/ELite) | [arXiv:2502.13452](https://arxiv.org/abs/2502.13452) | 🟡 能：`python3.10 + open3d 0.18 + loguru`，跑官方 `run_elite.py`（两段 config：先建 01 的图，再把 02 对齐上去），再用官方定义算 AC/RMSE/CD 对表 I；纯 CPU（CUDA 只用于可选的加速匹配）。 |
| 01-12 | ☑ | [UZ-SLAMLab/ORB_SLAM3](https://github.com/UZ-SLAMLab/ORB_SLAM3) | [arXiv:2007.11898](https://arxiv.org/abs/2007.11898) | ✅ **能，而且完全不需要 GPU**：自编 Pangolin(v0.8) + ORB-SLAM3，跑 `stereo_inertial_euroc`，再用**仓库自带的** `evaluation/evaluate_ate_scale.py` 对表 II。 |
| 01-13 | ☐ | [MIT-SPARK/Khronos](https://github.com/MIT-SPARK/Khronos) | [arXiv:2402.13817](https://arxiv.org/abs/2402.13817) | ✅ **能，而且环境正好命中**：Ubuntu 24.04 + ROS 2 Jazzy 就是官方要求的组合，`colcon build` 已在本机跑通；数据（模拟 bag + GT）与评测套件都是官方直链。剩下的是跑一遍 + 用官方 `evaluate_pipeline.sh` 出表。 |
| 02-01 | ◐ | [WaldJohannaU/3RScan](https://github.com/WaldJohannaU/3RScan) | [arXiv:1908.06109](https://arxiv.org/abs/1908.06109) | 🟡 半能：仓库只有数据集 + 工具（数据要签协议），三个二进制可跑，没有方法代码。 |
| 02-06 | ⛔ | [MIT-SPARK/Clio](https://github.com/MIT-SPARK/Clio) | [arXiv:2404.13696](https://arxiv.org/abs/2404.13696) | ⛔ 按论文规模不现实：FastSAM + CLIP ViT-L 在 CPU 上每分钟只能处理少量帧，而论文是对整段 Replica 序列建图。**注意**：TensorRT 是可选的（README 明说不是必须），所以卡住的不是「有没有 GPU」这一句话，而是 CPU 的吞吐。 |
| 02-07 | ⛔ | [AnyLoc/AnyLoc](https://github.com/AnyLoc/AnyLoc) | [arXiv:2308.00688](https://arxiv.org/abs/2308.00688) | 🟡 **CPU 可以跑，只是慢**：论文的表格要 ViT-G/14 提特征（GPU 才现实），但官方 README 明确给了**小数据集 17places** 的快速入口，CPU 上做小规模检索是可行的 —— 复现目标是「同一套评测口径下的 Recall@1」，不是全量 12 个数据集。 |
| 02-08 | ⛔ | [AnyLoc/Revisit-Anything](https://github.com/AnyLoc/Revisit-Anything) | [arXiv:2409.18049](https://arxiv.org/abs/2409.18049) | 🟡 **CPU 可以跑，只是慢**：仓库自己建议先用 **17places**（约 340 张图）跑通；DINOv2 + SAM 在 CPU 上是分钟级/张，整套小数据集是小时级 —— 可行但要有耐心。 |
| 02-03 | ⛔ | [concept-graphs/concept-graphs](https://github.com/concept-graphs/concept-graphs) | [arXiv:2309.16650](https://arxiv.org/abs/2309.16650) | ⛔ 按论文规模不现实：CPU 上 PyTorch3D 与 SAM/CLIP/LLaVA 都能装能跑，但论文是对 Replica/ScanNet 整段序列建图，CPU 吞吐差两三个数量级；另外 LLaVA-7B 光权重就 ~14 GB（本机 15 GB 内存）。 |
| 02-04 | ⛔ | [Eku127/DualMap](https://github.com/Eku127/DualMap) | [arXiv:2506.01950](https://arxiv.org/abs/2506.01950) | ⛔ 按论文规模不现实：GroundingDINO + SAM 在 CPU 上能跑但每帧几十秒，论文的 Replica 序列是几千帧；本机内存 15 GB 也吃紧。 |
| 02-05 | ⛔ | [hovsg/HOV-SG](https://github.com/hovsg/HOV-SG) | [arXiv:2403.17846](https://arxiv.org/abs/2403.17846) | ⛔ 按论文规模不现实：habitat-sim 本身可以 headless 跑，CLIP/SAM 在 CPU 上也能推理，但 HM3DSem 是数千帧的大场景，CPU 上不现实。 |
| 01-07 | ⛔ | [ACFR-RPG/DynoSAM](https://github.com/ACFR-RPG/DynoSAM) | [arXiv:2501.11893](https://arxiv.org/abs/2501.11893) | 🟡 **原来的判读要改**：CUDA 不是死结 —— `nvcc` 可以**在没有 GPU 的机器上安装**（已实测：conda-forge `cuda-nvcc` 装上 CUDA 13.4 编译器），`-DDYNOSAM_NN_USE_TRT=OFF` 又能去掉 TensorRT，两者一起就把 configure 阶段的 CUDA 门去掉了。真正剩下的是**一整套 ROS 2 + GTSAM 工作区**（上游对着 ROS 2 Kilted 写，本机是 Jazzy）。 |
| 02-02 | ⛔ | — | [arXiv:2607.14899](https://arxiv.org/abs/2607.14899) | ⛔ 不能复现：代码未发布（项目页仍写 Code Soon），没有库可跑。 |

> ✓ 的含义：**☑ 已完成并对上原库/论文的结果 · ◐ 只做了一半 · ☐ 还没做 · ⛔ 本机做不了（无 GPU / 无代码）**。
> 每一行的三个字段写在对应文件夹的 `README.md` 里（`复现库` / `论文链接` / `能否复现` / `复现顺序` / `复现完成`），
> 本表由 `python3 reproductions/run_all.py` 从这些字段生成，**块内内容不要手改**；跑完一个就把那个文件夹的 `复现完成` 改成 ☑。

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

Three workflows ship with it — **build a map** (`mapping.launch.py`), **localize against a saved map
and plan with A\*** (`localization_navigation.launch.py`), and **map while navigating**
(`navigation_slam.launch.py`). All three, the planner configuration and the verification log are in
[`docs/platform.md`](docs/platform.md).

## The platform

This repository is the modelling, mapping, localization and planning base extracted from
[Sim2Real-AlgoBench](https://github.com/p20030920p/Sim2Real-AlgoBench). The benchmark's algorithm
zoo was removed on purpose: what is left is one planner you can read end to end, and everything
around it that a SLAM exercise needs.

| Layer | Package | What it holds |
| :--- | :--- | :--- |
| Modelling | `race_description` | The three-wheeled omni car: URDF, meshes, `ros2_control` joint definitions |
| Modelling | `race_gazebo` | The arena world, the competition map model, the dynamic-obstacle variant |
| Modelling | `race_bringup` | Simulation bring-up: Gazebo, controller spawners, sensor bridges, RViz layout |
| Modelling | `race_control` | One node: `Twist` → `TwistStamped`, so Nav2 and teleop can drive the wheels |
| Mapping | `race_navigation` | `slam_toolbox` configuration and the mapping launch |
| Localization | `race_navigation` | AMCL, tuned for the holonomic chassis, plus the saved arena map |
| Planning | `algo_core` | A\* over an 8-connected cost grid — ROS-free C++, unit-testable offline |
| Planning | `algo_nav2_plugins` | The Nav2 `GlobalPlanner` adapter that runs `algo_core` inside Nav2 |

The robot carries a **single-plane 360° 12 m 2D lidar** (`/scan`) and a **front RGB camera**
(640×480, 15 Hz — no depth, no IMU); AMCL uses an omnidirectional motion model. The arena, the
sensor rig, the sim-to-hardware gap and the removal list are detailed in
[`docs/platform.md`](docs/platform.md).

## Documentation

| Where | What |
| :--- | :--- |
| [`docs/platform.md`](docs/platform.md) | Workflows, planner configuration, arena and sensors, verification log |
| [`reproductions/`](reproductions/) | Paper-reproduction area: one folder per paper, plus the checklist above |
| [`docs/task-book/TASK_BOOK.md`](docs/task-book/TASK_BOOK.md) | The task book the two research directions come from |
| [`docs/task-book/PAPER_AUDIT.md`](docs/task-book/PAPER_AUDIT.md) | Whether each cited paper has runnable code at all |
| [`car.md`](car.md) | The eight difficulties, each with a falsifiable hypothesis |

## Licence

MIT, see [LICENSE](LICENSE). Derived from
[Sim2Real-AlgoBench](https://github.com/p20030920p/Sim2Real-AlgoBench) by p20030920p and zfyyyyy.
