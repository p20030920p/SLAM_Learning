<div align="center">

# SLAM_Learning

**一个用于 SLAM 实践的 ROS 2 Jazzy + Gazebo 场地 —— 一台全向小车、一个赛场，以及真正重要的三件事：建图、定位、规划。**

[![ROS 2](https://img.shields.io/badge/ROS%202-Jazzy-22314E?logo=ros&logoColor=white)](https://docs.ros.org/en/jazzy/)
[![Gazebo](https://img.shields.io/badge/Gazebo%20Sim-8-F58113?logo=gazebo&logoColor=white)](https://gazebosim.org/)
[![定位](https://img.shields.io/badge/%E5%AE%9A%E4%BD%8D-AMCL-blue)](#技术栈)
[![规划器](https://img.shields.io/badge/%E8%A7%84%E5%88%92%E5%99%A8-A*-brightgreen)](#规划器)
[![License](https://img.shields.io/badge/license-MIT-3DA639)](LICENSE)

[技术栈](#技术栈) &nbsp;•&nbsp; [快速开始](#快速开始) &nbsp;•&nbsp; [三条工作流](#三条工作流) &nbsp;•&nbsp; [规划器](#规划器)

*[English](README.md) &nbsp;|&nbsp; 中文*

</div>

<p align="center">
  <img src="docs/images/01_mapping.png" width="860" alt="slam_toolbox 在小车行进中构建赛场地图"/>
</p>

<p align="center">
  <em>建图：小车在 Gazebo 中行驶，slam_toolbox 用仿真激光雷达把地图一点点长出来。</em>
</p>

## 技术栈

本仓库是从 [Sim2Real-AlgoBench](https://github.com/p20030920p/Sim2Real-AlgoBench) 中抽出来的
建模、建图、定位与规划底座。基准里的算法仓库是刻意删掉的：留下来的，是一个可以从头读到尾的
规划器，以及 SLAM 练习真正需要的全部外围。

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

赛场为 14.7 × 14.7 m，栅格 5 cm（294 × 294），保存为
`src/race_navigation/maps/race_map.{pgm,yaml}`。小车出生点在 `(8.07, 7.53)`，朝向场地内部，
搭载 12 m 激光雷达与前置摄像头，AMCL 使用全向运动模型。

包名保留了上游的 `race_*` 前缀，这样可以和 Sim2Real-AlgoBench 一一对应；你实际打交道的是
launch 文件和配置。

<p align="center">
  <img src="docs/images/03_nav2_navigation.png" width="860" alt="AMCL 粒子云与 Nav2 代价地图，小车正在驶向目标点"/>
</p>

<p align="center">
  <em>定位与规划：AMCL 粒子云、全局代价地图，A* 正把小车带向 Nav2 目标点。</em>
</p>

## 快速开始

```bash
git clone https://github.com/p20030920p/SLAM_Learning.git
cd SLAM_Learning
source /opt/ros/jazzy/setup.bash
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
```

## 三条工作流

### 1. 建图

```bash
ros2 launch race_navigation mapping.launch.py
# 另开一个终端，用键盘遥控小车
ros2 launch race_navigation keyboard.launch.py
```

`slam_toolbox` 会边跑边发地图，觉得差不多了就保存：

```bash
ros2 run nav2_map_server map_saver_cli -f src/race_navigation/maps/my_map
```

会得到 `my_map.pgm` 和 `my_map.yaml`，下一条工作流用 `map:=...` 指过去即可。

### 2. 用保存的地图定位，用 A\* 规划

```bash
ros2 launch race_navigation localization_navigation.launch.py
# 或者换成自己建的地图：
ros2 launch race_navigation localization_navigation.launch.py map:=$PWD/src/race_navigation/maps/my_map.yaml
```

AMCL 从 `nav2_params.yaml` 里配置的位姿（也就是赛场出生点）起步，粒子云一开始就是收敛的。
`spawn_*` 这几个 launch 参数只移动 Gazebo 里的小车，**故意没有**和 AMCL 的 `initial_pose` 联动：
如果车出生在别处，要么改那段配置，要么在 RViz 里点 **2D Pose Estimate**，然后发 **Nav2 Goal**。
你拿到的路径就是 A\*。

### 3. 边建图边导航

```bash
ros2 launch race_navigation navigation_slam.launch.py
```

这条链路里 `map → odom` 由 `slam_toolbox` 独占，AMCL 是关掉的 —— 两个都开会让同一条 TF 边出现
两个发布者。想探索未知场地用它；地图存好之后再用第 2 条。

| 保存下来的地图 | TF 树 |
| :---: | :---: |
| ![保存的地图](docs/images/02_map_saved.png) | ![TF 树](docs/images/06_tf_tree.png) |

### 几点说明

* 两个仿真 launch 加 `stress:=true` 会加载障碍场地。它的两个障碍关节分别听
  `/dynamic_obstacle/cmd_pos` 和 `/dynamic_obstacle_2/cmd_pos`；本仓库已经没有节点往这两个话题发消息了，
  所以在你自己写发布者之前障碍是不动的 —— 在那之前它可以当一个静态障碍场地用。
* 第 3 条工作流里 `map → odom` 归 `slam_toolbox`，第 2 条里归 AMCL。两者不要同时开：
  同一条 TF 边上有两个发布者，地图就会抖。

## 规划器

`algo_core` 里的 A\* 用二叉堆、octile 启发式，并且实现了对角切角规则 —— 这样机器人足迹不会
从两个相接触的障碍之间"挤"过去。它只依赖 C++ 标准库，不依赖 ROS、不依赖代价地图类型，因此
不用仿真就能测：

```bash
# 不变量检查：能找到路径、端点连通、路径不落在致命栅格上、上报代价等于返回路径的代价、
# 8 邻接路径不比 4 邻接更长
./install/algo_core/lib/algo_core/algo_core_selftest

# 在真实赛场地图上离线跑同一次搜索
./install/algo_core/lib/algo_core/algo_plan_dump \
  src/race_navigation/maps/race_map.pgm /tmp/astar_dump.bin \
  8.0727 7.5312 -2.5 -5.5 -3.700 -6.342 0.050 0.196 0.65
```

在 Nav2 里，规划器配置在 `src/race_navigation/config/nav2_params.yaml`：

```yaml
planner_server:
  ros__parameters:
    planner_plugins: ["GridBased"]
    GridBased:
      plugin: "algo_nav2_plugins/GridPlanner"
      algorithm: "astar"        # 规划器注册时用的名字
      cost_scale: 1.0           # 0.0 = 只看致命/空闲，越大越躲开膨胀层
      snap_radius: 6.0          # 起终点落在膨胀栅格里时，向外找空闲栅格的半径（单位：栅格）
      allow_diagonal: true
      remove_collinear: true
      publish_expanded: true    # 在 GridBased/expanded 上发 MarkerArray，可以在 RViz 里看搜索过程
```

想把别的规划器加回来只有两步：继承 `algo_core::GridPlanner`，用
`ALGO_CORE_REGISTER(YourPlanner, "your_name")` 注册，把源文件加进
`src/algo_core/CMakeLists.txt`，再把上面的 `algorithm` 改成 `"your_name"`。Nav2 适配器不用动。

## 复现区 Reproductions

`reproductions/` 是按**两个研究方向**组织的论文复现区：**D1** 动态环境下的鲁棒定位与 SLAM、
**D2** 语义建图、视觉定位与导航。每篇论文一个带序号的文件夹，里面有复现方案（目标 / 数据 /
步骤 / 验收）与 `code/`、`data/`、`work/`、`results/` 四个子目录；上游代码与数据集留在本机，
不进 git。

| | 方向 | 复现对象 |
| :--- | :--- | :--- |
| **01** | 动态环境下的鲁棒定位与 SLAM | DynamicMap_Benchmark · KISS-ICP · ERASOR · Removert · DUFOMap · BeautyMap · DynoSAM · NGD-SLAM · LT-mapper |
| **02** | 语义建图、视觉定位与导航 | 3RScan · OASIS-Map · ConceptGraphs · DualMap · HOV-SG · Clio · AnyLoc · Revisit Anything |

索引、两个方向与任务书的对应关系、以及建议顺序见
[`reproductions/README.md`](reproductions/README.md)。

<!-- PROGRESS:START -->

## 复现进度 Reproduction progress

**进度** — 1/17 跑通 · 1 本次实际运行 · 1/17 已自动化 · 更新于 2026-10-05 00:24 CST

| # | 方向 | 复现对象 | 状态 | 本次运行 | 回测 | 关键指标 / 阻塞原因 / findings |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| 01-01 | D1 | DynamicMap_Benchmark | ⬜ planned | — | — | 待开始（缺 reproduce.py） |
| 01-02 | D1 | KISS-ICP | ⬜ planned | — | — | 待开始（缺 reproduce.py） |
| 01-03 | D1 | ERASOR | ⬜ planned | — | — | 待开始（缺 reproduce.py） |
| 01-04 | D1 | Removert | ⬜ planned | — | — | 待开始（缺 reproduce.py） |
| 01-05 | D1 | DUFOMap | ⬜ planned | — | — | 待开始（缺 reproduce.py） |
| 01-06 | D1 | BeautyMap | ⬜ planned | — | — | 待开始（缺 reproduce.py） |
| 01-07 | D1 | DynoSAM | ⬜ planned | — | — | 待开始（缺 reproduce.py） |
| 01-08 | D1 | NGD-SLAM | ⬜ planned | — | — | 待开始（缺 reproduce.py） |
| 01-09 | D1 | LT-mapper | ⬜ planned | — | — | 待开始（缺 reproduce.py） |
| 02-01 | D2 | 3RScan | 🟢 green | ✅ | ✅ 通过 | objects_total=32, unchanged=26, moved=5, absent_unlabelled=1 · 5 条 finding |
| 02-02 | D2 | OASIS-Map | ⬜ planned | — | — | 待开始（缺 reproduce.py） |
| 02-03 | D2 | ConceptGraphs | ⬜ planned | — | — | 待开始（缺 reproduce.py） |
| 02-04 | D2 | DualMap | ⬜ planned | — | — | 待开始（缺 reproduce.py） |
| 02-05 | D2 | HOV-SG | ⬜ planned | — | — | 待开始（缺 reproduce.py） |
| 02-06 | D2 | Clio | ⬜ planned | — | — | 待开始（缺 reproduce.py） |
| 02-07 | D2 | AnyLoc | ⬜ planned | — | — | 待开始（缺 reproduce.py） |
| 02-08 | D2 | Revisit Anything | ⬜ planned | — | — | 待开始（缺 reproduce.py） |

> 本表由 `python3 reproductions/run_all.py` 自动生成，块内内容请勿手改。
> 新增复现：建好文件夹与 `README.md`，再放一个实现 `require(ctx)` / `run(ctx)` 的 `reproduce.py`，重跑本命令即可。

<!-- PROGRESS:END -->

## 相比基准删掉了什么

Dijkstra、加权 A\*、GBFS、JPS、Theta\*、D\* Lite，用来在它们之间切换的 `algo_bringup` 注册表，
绿板视觉包 `race_vision`，比赛自主状态机，以及演示录制工具和媒体文件。其余部分没有改动：小车、
赛场、控制链路、建图与定位配置，都是基准原来的那一套。

## 验证情况

* `colcon build --symlink-install` —— 7 个包，无告警。
* `algo_core_selftest` —— 全部不变量通过；注册的规划器只有 `astar`。
* `algo_plan_dump` 跑 `race_map.pgm` —— 找到路径，扩展 24,563 个栅格，耗时约 0.1 s（随机器波动）。
* 用本仓库的 `nav2_params.yaml` 起 Nav2 `planner_server` —— 把 `GridBased` 加载为
  `algo_nav2_plugins/GridPlanner`，日志打印 `algorithm 'astar' ready`，
  在地图上发 `ComputePathToPose` 返回 `SUCCEEDED`，约 6 ms 得到合法路径。
* 用本仓库的 `nav2_params.yaml` 起 `localization_launch.py` —— `map_server` 与 `amcl` 都进入
  `active`，AMCL 正确应用了配置的初始位姿。
* 九个 launch 文件全部能正常构造 launch description。

<p align="center">
  <sub>Gazebo 需要可用的 GPU / 渲染环境。如果摄像头传感器无法初始化，Gazebo 会在传感器初始化阶段
  段错误退出；上游基准在同样的机器上表现一致。其余部分（建图、定位、规划）不依赖渲染也能跑通。</sub>
</p>

## 许可证

MIT，见 [LICENSE](LICENSE)。派生自 p20030920p 与 zfyyyyy 的
[Sim2Real-AlgoBench](https://github.com/p20030920p/Sim2Real-AlgoBench)。
