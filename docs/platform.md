# 平台细节 Platform details

> **归档说明（2026-10）**：本页描述的 ROS 2 平台（`race_*` / `algo_*` 六个包）已从本仓库移除，
> 仓库现在只保留复现区与文档。下面的 launch 命令与包路径在本仓库内**已不可执行**，
> 保留本页是为了留住赛场几何、传感器配置与仿真到实机差距这几节的判断。
> 要重新跑起来，回到上游 [Sim2Real-AlgoBench](https://github.com/p20030920p/Sim2Real-AlgoBench)
> 取 `src/`，或从本仓库的 git 历史里恢复（`git checkout <commit> -- src`）。

[`README.md`](../README.md) 主页只留「这是什么 / 复现清单 / 目录结构」。
三条工作流、规划器配置、验证记录、传感器差距这些**用起来才需要**的内容放在这里。


---

## 三条工作流 Workflows

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
| ![保存的地图](images/02_map_saved.png) | ![TF 树](images/06_tf_tree.png) |

### 几点说明

* 两个仿真 launch 加 `stress:=true` 会加载障碍场地。它的两个障碍关节分别听
  `/dynamic_obstacle/cmd_pos` 和 `/dynamic_obstacle_2/cmd_pos`；本仓库已经没有节点往这两个话题发消息了，
  所以在你自己写发布者之前障碍是不动的 —— 在那之前它可以当一个静态障碍场地用。
* 第 3 条工作流里 `map → odom` 归 `slam_toolbox`，第 2 条里归 AMCL。两者不要同时开：
  同一条 TF 边上有两个发布者，地图就会抖。

<p align="center">
  <img src="images/03_nav2_navigation.png" width="860" alt="AMCL 粒子云与 Nav2 代价地图，小车正在驶向目标点"/>
</p>

<p align="center">
  <em>定位与规划：AMCL 粒子云、全局代价地图，A* 正把小车带向 Nav2 目标点。</em>
</p>

---

## 规划器 The planner

`algo_core` 里的 A\* 用二叉堆、octile 启发式，并且实现了对角切角规则 —— 这样机器人足迹不会
从两个相接触的障碍之间“挤”过去。它只依赖 C++ 标准库，不依赖 ROS、不依赖代价地图类型，因此
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

---

## 赛场与传感器 Arena and sensors

赛场为 14.7 × 14.7 m，栅格 5 cm（294 × 294），保存为
`src/race_navigation/maps/race_map.{pgm,yaml}`。小车出生点在 `(8.07, 7.53)`，朝向场地内部，
搭载**单线 360°、12 m 的 2D 激光雷达**（`gpu_lidar` 只配了水平 `<scan>`、没有 `<vertical>`，
话题 `/scan` —— 正好对上目标硬件的那台雷达）与**前置 RGB 摄像头**（640×480、15 Hz，
**没有深度、也没有 IMU**），AMCL 使用全向运动模型。

> **仿真与实物的差距，直说**：目标平台是 Intel RealSense **D435i**（双目 IR + 深度 + Bosch BMI055 IMU）
> 加一台 2D 雷达。**雷达这一半已经对上，相机这一半没有** —— 本仿真既无深度也无 IMU，
> 所以在这里还跑不了 VIO/LIO 融合。逐条复现的传感器契合度与两个半边各自可用的公开数据，
> 见 [`reproductions/NOTES.md`](../reproductions/NOTES.md)。

包名保留了上游的 `race_*` 前缀，这样可以和 Sim2Real-AlgoBench 一一对应；你实际打交道的是
launch 文件和配置。

---

## 相比基准删掉了什么 What was removed

Dijkstra、加权 A\*、GBFS、JPS、Theta\*、D\* Lite，用来在它们之间切换的 `algo_bringup` 注册表，
绿板视觉包 `race_vision`，比赛自主状态机，以及演示录制工具和媒体文件。其余部分没有改动：小车、
赛场、控制链路、建图与定位配置，都是基准原来的那一套。

---

## 验证情况 Verified

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
