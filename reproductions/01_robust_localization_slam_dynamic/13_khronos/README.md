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
| 复现状态 | ⬜ 未开始（已检查：仓库/数据可达，依赖明确；**作者自述 ROS 2 版仍在开发、不稳定**） |

| 复现顺序 | 12 |
| 能否复现 | 🟡 能，但是本清单里最重的一个：`vcs import` 拉一个 ROS 2 工作区（Hydra/spark_dsg 等一系列依赖）+ `colcon build`，再跑 GDrive 上的 bag；换来的是**官方评测脚本直接产出论文那张表**。 |
| 复现完成 | ☐ 待做 |

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
