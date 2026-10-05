<div align="center">

# SLAM_Learning

**一个用于验证想法的 SLAM 平台 —— 一台全向小车、一个赛场，以及真正重要的三件事：建图、定位、规划。把一个方法丢进来，把车开一圈，就知道这个想法行不行。**

[![ROS 2](https://img.shields.io/badge/ROS%202-Jazzy-22314E?logo=ros&logoColor=white)](https://docs.ros.org/en/jazzy/)
[![Gazebo](https://img.shields.io/badge/Gazebo%20Sim-8-F58113?logo=gazebo&logoColor=white)](https://gazebosim.org/)
[![定位](https://img.shields.io/badge/%E5%AE%9A%E4%BD%8D-AMCL-blue)](#平台)
[![规划器](https://img.shields.io/badge/%E8%A7%84%E5%88%92%E5%99%A8-A*-brightgreen)](#平台)
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

## 这是什么 —— 以及不是什么

**这是一个用于验证想法的平台。** 一个自包含的 ROS 2 Jazzy + Gazebo 赛场，
机器人、传感器、地图与评测都已经接好：把一个建图 / 定位 / 规划方法丢进来，把车开一圈，
就能看出这个方法到底行不行。

| 它是什么 | 它**不是**什么 |
| :--- | :--- |
| **一次验证一个方法 / 想法**的试验台 | **不是基准（benchmark）**：没有排行榜、没有跨论文指标、没有固定协议。复现**别人的论文**并对齐他们自己的数字，是 [`reproductions/`](reproductions/) 的事 |
| **你能控制的场景**：几何已知、真值已知、可重复 | **不是自主系统**：这里没有感知 → 决策 → 安全那条链，只有建图、定位、规划 |
| 对**你实际那台车**的仿真（2D 雷达 + 相机） | **不是真机系统**：没有硬件驱动、没有标定流程；而且相机只是 RGB——没有深度、没有 IMU，所以 VIO/LIO 融合在这里还跑不了 |
| 在**完全相同的条件**下比较你自己方法的两个版本 | **不替代 Sim2Real-AlgoBench**：本仓库是从它抽出来的建模 / 建图 / 定位 / 规划底座，算法库是刻意删掉的 |

<!-- PROGRESS:START -->

## 复现清单 Reproduction checklist

**按「越好复现 + 越能对上原库结果」排序** —— ☑ 10 · ◐ 2 · ☐ 1 · ⛔ 8（共 21） · 更新于 2026-10-06 01:09 CST

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

## 快速开始

```bash
git clone https://github.com/p20030920p/SLAM_Learning.git
cd SLAM_Learning
source /opt/ros/jazzy/setup.bash
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
```

平台自带三条工作流：**建图**（`mapping.launch.py`）、**用保存的地图定位 + A\* 规划**
（`localization_navigation.launch.py`）、**边建图边导航**（`navigation_slam.launch.py`）。
三条工作流、规划器配置与验证记录都在 [`docs/platform.md`](docs/platform.md)。

## 平台

本仓库是从 [Sim2Real-AlgoBench](https://github.com/p20030920p/Sim2Real-AlgoBench) 中抽出来的
建模、建图、定位与规划底座。基准里的算法仓库是刻意删掉的：留下来的，是一个可以从头读到尾的
规划器，以及搭载这套方法真正需要的全部外围。

| 层 | 包 | 内容 |
| :--- | :--- | :--- |
| 建模 | `race_description` | 三轮全向小车：URDF、网格模型、`ros2_control` 关节定义 |
| 建模 | `race_gazebo` | 赛场世界文件、比赛地图模型、动态障碍变体世界 |
| 建模 | `race_bringup` | 仿真启动：Gazebo、控制器 spawner、传感器桥、RViz 配置 |
| 建模 | `race_control` | 只有一个节点：`Twist` → `TwistStamped`，让 Nav2 和遥控都能驱动轮子 |
| 建图 | `race_navigation` | `slam_toolbox` 配置与建图 launch |
| 定位 | `race_navigation` | 针对全向底盘调好的 AMCL，以及保存好的赛场地图 |
| 规划 | `algo_core` | 8 邻接代价栅格上的 A\* —— 不依赖 ROS 的 C++，可脱离仿真做单元测试 |
| 规划 | `algo_nav2_plugins` | 让 `algo_core` 在 Nav2 里跑起来的 `GlobalPlanner` 适配器 |

小车搭载**单线 360°、12 m 的 2D 激光雷达**（话题 `/scan`）与**前置 RGB 摄像头**
（640×480、15 Hz，没有深度、也没有 IMU），AMCL 使用全向运动模型。赛场、传感器、
仿真与实物的差距、以及删掉了什么，都在 [`docs/platform.md`](docs/platform.md)。

## 文档

| 位置 | 内容 |
| :--- | :--- |
| [`docs/platform.md`](docs/platform.md) | 三条工作流、规划器配置、赛场与传感器、验证记录 |
| [`reproductions/`](reproductions/) | 论文复现区：一篇论文一个文件夹，加上上面那张清单 |
| [`docs/task-book/TASK_BOOK.md`](docs/task-book/TASK_BOOK.md) | 两个研究方向来源的那份任务书 |
| [`docs/task-book/PAPER_AUDIT.md`](docs/task-book/PAPER_AUDIT.md) | 任务书引用的论文到底有没有能跑的代码 |
| [`car.md`](car.md) | 八个难点，每个都带一条可否证的假设 |

## 许可证

MIT，见 [LICENSE](LICENSE)。派生自 p20030920p 与 zfyyyyy 的
[Sim2Real-AlgoBench](https://github.com/p20030920p/Sim2Real-AlgoBench)。
