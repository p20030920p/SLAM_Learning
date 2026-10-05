# 01-13 · Khronos

| 项 Item | 内容 |
| :--- | :--- |
| 论文 | Khronos: A Unified Approach for Spatio-Temporal Metric-Semantic SLAM in Dynamic Environments |
| Venue | **RSS 2024**（arXiv:2402.13817） |
| 论文链接 | [arXiv:2402.13817](https://arxiv.org/abs/2402.13817) |
| 论文报告值 | 官方评测套件会直接打出论文那张表：Accuracy / Completeness / F1@0.2、Object F1、Dynamic F1、Change F1（见 `khronos_eval` 的 `plotting/tables.py`） |
| 代码 | [MIT-SPARK/Khronos](https://github.com/MIT-SPARK/Khronos) ✅ BSD-3，**ROS 2 版** |
| 数据 | 论文数据集在 Google Drive（免注册）：模拟 `tesse_cd` + 真实 `khronos_real`（mezzanine rosbag）；实测文件夹可达 |
| 为什么在这 | **官方要求 Ubuntu 24.04 + ROS 2 Jazzy —— 正是本机**（`lsb_release`：Ubuntu 24.04.4，`/opt/ros/jazzy`），而且仓库**自带评测套件**，能出与论文同格式的表；任务书 §2 难点 4 的核心参考 |
| 方向 | D1 · 动态环境下的鲁棒定位与 SLAM（4D 时空地图 + 变化检测） |
| 任务书对应 | §2 难点 4 高变动场景的地图维护；§4.1 地图更新策略（「删什么、什么时候删」） |
| 复现状态 | 🟡 **工作区已编译、数据已下载、无头驱动已就绪，待跑**：29 个包全部 `colcon build` 通过（含 `khronos`/`khronos_ros`/`khronos_eval`）；`tesse_cd_apartment` bag（10.3 GB）与四份 GT 已下齐；本机无显示器，加了一个把 `start_visualizer` 透传到内层 launch 的补丁 |

| 复现顺序 | 12 |
| 能否复现 | ✅ **能，而且环境正好命中**：Ubuntu 24.04 + ROS 2 Jazzy 就是官方要求的组合，`colcon build` 已在本机跑通；数据（模拟 bag + GT）与评测套件都是官方直链。剩下的是跑一遍 + 用官方 `evaluate_pipeline.sh` 出表。 |
| 复现完成 | ☐ 待做（工作区/数据/驱动 ✅，未跑） |

## 已经落地的东西（2026-10-05）

| 项 | 状态 |
| :--- | :--- |
| ROS 2 工作区 | `code/` 下 29 个包装成（`install/` 里含 `khronos`、`khronos_ros`、`khronos_eval`、`hydra`、`kimera_pgmo`、`spark_dsg`…）|
| 系统依赖 | GTSAM 4.2 装在 `reproductions/.venvs/gtsam42`（conda-forge，无 sudo），构建时用 `-Dgtsam_DIR=...`；另加了 `-include cstdint -include type_traits`（新 GCC 下上游缺头）与 `-ltbb` |
| 数据 | `data/datasets/tesse_cd_apartment/`（10.3 GB bag，话题与 launch 里的 `/tesse/*` 逐条对上，含 GT 语义 `/tesse/seg_cam/converted/image_raw`）；`data/raw/gt_apartment/` 四份 GT（尺寸与 Drive 声明一致） |
| GDrive 下载 | 两个数据文件夹都用 [`../../tools/gdrive_range_fetch.py`](../../tools/gdrive_range_fetch.py) 分块拉（普通下载会被 Drive 的按文件配额挡住） |
| 无头启动补丁 | [`work/local_patches.patch`](work/local_patches.patch)：上游把可视化和 rviz 都挂在 `start_visualizer` 上，**但没从 `uhumans2_khronos.launch.yaml` 透传**，导致命令行关不掉 —— 补一个 arg 转发，算法零改动 |
| 评测配置 | [`work/eval_apartment.yaml`](work/eval_apartment.yaml)：上游把 GT 路径写死在 `/data/datasets/...`（容器布局），本机无 `/data` 也无 root，只改这三条路径，其余阈值/检测器/评测项全部保留上游值 |
| 运行驱动 | [`work/run_khronos.sh`](work/run_khronos.sh)：无头 `ros2 launch` → 等 bag 播完 → 调 `/khronos_node/experiment/finish_mapping_and_save` → 等 `final.4dmap` |

## 为什么它排在 ELite / ORB-SLAM3 之后

不是因为它不对口 —— 恰恰相反，它是**任务书 §2 难点 4 里唯一一个「本机操作系统 + ROS 发行版完全命中」**
的官方实现（Ubuntu 24.04 + ROS 2 Jazzy）。它排后面只因为**安装面最大**：
`vcs import` 会拉进一整套 MIT-SPARK 的依赖树，编译时间和磁盘都不小，
而且作者在 README 里明说 ROS 2 版 *"in active development and is unstable"*。
按「越好复现的先做」，它应该在前四个之后动手，但**动手前先把工作区建起来看能不能编译过**，
编译不过就立刻记 ⛔ 而不是耗在里面。

## 复现计划 Steps

1. 建 ROS 2 工作区，`git clone` + `vcs import . < khronos/install/https.rosinstall`；
2. 系统依赖 `ros-$ROS_DISTRO-gtsam libgoogle-glog-dev nlohmann-json3-dev`（本机无 sudo 时走 micromamba/conda-forge，与 ROS 1 那套做法一致）；
3. `colcon build --symlink-build -DCMAKE_BUILD_TYPE=Release`；
4. 下 `tesse_cd_office`（变化与动态物体最多的那条）→ 按 README 改 bag 路径 → 跑 launch；
5. 用 `khronos_eval` 的 `scripts/evaluate_pipeline.sh` + `plotting/tables.py` 出表，与论文对照。

> ⚠️ 语义推理（`semantic_inference`）是**可选**的：模拟数据集默认用真值语义标签，
> 真实数据集用预录的分割话题 —— 也就是说**没有 GPU / 没有 TensorRT 也能跑通主线**，
> 只是不能用在线开放集分割。这一点复现时要写清楚。

## 与论文表格的对照目标

官方评测套件 `khronos_eval` 会直接打出论文同格式的表（README 里给的示例行就是 tesse_cd 两个场景）：

| Data | Accuracy@0.2 | Completeness@0.2 | F1@0.2 | ObjectF1 | DynamicF1 | ChangeF1 |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| apartment（论文/上游 README 示例） | 99.9 | 91.9 | 95.5 | 53.1 | 49.5 | 47.8 |
| office（同上） | 99.3 | 77.0 | 84.1 | 54.8 | 41.4 | 51.7 |

复现目标是 **apartment 这一行**：跑官方 pipeline → `khronos_eval` 出表 → 对上这六个数。
