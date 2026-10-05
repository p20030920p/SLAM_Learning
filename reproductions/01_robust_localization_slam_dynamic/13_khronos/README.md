<div align="center">

# 01-13 · Khronos

**Khronos: A Unified Approach for Spatio-Temporal Metric-Semantic SLAM**

4D 时空度量语义地图：物体、动态与变化都进场景图。

[![venue](https://img.shields.io/badge/venue-RSS%202024-0b7285)](https://arxiv.org/abs/2402.13817)
![blocked](https://img.shields.io/badge/blocked-needs%20more%20than%2013.5%20GB%20RAM-cf222e)
[![code](https://img.shields.io/badge/code-MIT--SPARK%2FKhronos-181717?logo=github&logoColor=white)](https://github.com/MIT-SPARK/Khronos)
![data](https://img.shields.io/badge/data-tesse__cd%20bag%20%2B%20GT%20%C2%B7%20downloaded-1c7ed6)
![needs](https://img.shields.io/badge/needs-a%20machine%20with%2020%20GB%2B%20free%20RAM-6f42c1)

[Requirements](#requirements) &nbsp;•&nbsp; [Why not reproduced](#why-not-reproduced) &nbsp;•&nbsp; [Notes](#notes)

*[← 复现区索引](../README.md) &nbsp;•&nbsp; [论文报告值](paper_baseline.md)*

</div>

|  |  |
| :--- | :--- |
| **Status** | ⛔ 本机不可复现 —— 需要 >13.5 GB 内存，五次上限尝试全部 OOM-killed（换机器即可跑） |

---

## Requirements

| 需要什么 | 说明 |
| :--- | :--- |
| 内存 | 可用内存 **≥ 20 GB** 的机器（`require()` 按 `/proc/meminfo` 的 `MemAvailable` 判定） |
| 系统 | Ubuntu 24.04 + ROS 2 Jazzy —— **本机正好命中**，29 个包已编译通过 |
| 数据 | 作者 GDrive 的模拟 bag（10.3 GB）+ 四份 GT：均已下载并核对尺寸 |
| 已就绪 | 无头启动补丁、评测配置、运行驱动全部写好，换机器即可直接跑 |

## Why not reproduced

| | |
| :--- | :--- |
| **阻塞点** | 29 个包已编译、10.3 GB bag 已解压、四份 GT 已下齐、无头启动与评测配置都已就绪；一跑起来 `khronos_node` 就以约 **250 MB/s** 涨内存，**五次尝试（`systemd` 上限 5 / 8 / 11 / 12 / 13.5 GB）全部 OOM-killed** |
| **实测证据** | RSS 逐 5 秒采样：1.34 → 2.64 → 4.04 → 4.82 → 6.02 GB（20 秒内），**没有收敛迹象**；同一时段 bag 播放器始终不在前列 —— 是节点本身，不是 10.3 GB 的 bag |
| **要什么才能跑** | 可用内存 ≥ 20 GB 的机器：`require()` 现在按 `/proc/meminfo` 的 `MemAvailable` 判定，**换机器即可直接跑完整流程**。要在这台机器上跑，只能降分辨率或截断 bag（会改实验口径，未擅自采用） |
| **记录** | [README 的内存一节](README.md) —— 五次尝试与采样表 |

## Notes

| 项 | 状态 |
| :--- | :--- |
| ROS 2 工作区 | `code/` 下 29 个包装成（`install/` 里含 `khronos`、`khronos_ros`、`khronos_eval`、`hydra`、`kimera_pgmo`、`spark_dsg`…）|
| 系统依赖 | GTSAM 4.2 装在 `reproductions/.venvs/gtsam42`（conda-forge，无 sudo），构建时用 `-Dgtsam_DIR=...`；另加了 `-include cstdint -include type_traits`（新 GCC 下上游缺头）与 `-ltbb` |
| 数据 | `data/datasets/tesse_cd_apartment/`（10.3 GB bag，话题与 launch 里的 `/tesse/*` 逐条对上，含 GT 语义 `/tesse/seg_cam/converted/image_raw`）；`data/raw/gt_apartment/` 四份 GT（尺寸与 Drive 声明一致） |
| GDrive 下载 | 两个数据文件夹都用 [`../../tools/gdrive_range_fetch.py`](../../tools/gdrive_range_fetch.py) 分块拉（普通下载会被 Drive 的按文件配额挡住） |
| 无头启动补丁 | [`work/local_patches.patch`](work/local_patches.patch)：上游把可视化和 rviz 都挂在 `start_visualizer` 上，**但没从 `uhumans2_khronos.launch.yaml` 透传**，导致命令行关不掉 —— 补一个 arg 转发，算法零改动 |
| 评测配置 | [`work/eval_apartment.yaml`](work/eval_apartment.yaml)：上游把 GT 路径写死在 `/data/datasets/...`（容器布局），本机无 `/data` 也无 root，只改这三条路径，其余阈值/检测器/评测项全部保留上游值 |
| 运行驱动 | [`work/run_khronos.sh`](work/run_khronos.sh)：无头 `ros2 launch` → 等 bag 播完 → 调 `/khronos_node/experiment/finish_mapping_and_save` → 等 `final.4dmap` |

不是因为它不对口 —— 恰恰相反，它是**任务书 §2 难点 4 里唯一一个「本机操作系统 + ROS 发行版完全命中」**
的官方实现（Ubuntu 24.04 + ROS 2 Jazzy）。它排后面只因为**安装面最大**：
`vcs import` 会拉进一整套 MIT-SPARK 的依赖树，编译时间和磁盘都不小，
而且作者在 README 里明说 ROS 2 版 *"in active development and is unstable"*。
按「越好复现的先做」，它应该在前四个之后动手，但**动手前先把工作区建起来看能不能编译过**，
编译不过就立刻记 ⛔ 而不是耗在里面。

官方评测套件 `khronos_eval` 会直接打出论文同格式的表（README 里给的示例行就是 tesse_cd 两个场景）：

| Data | Accuracy@0.2 | Completeness@0.2 | F1@0.2 | ObjectF1 | DynamicF1 | ChangeF1 |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| apartment（论文/上游 README 示例） | 99.9 | 91.9 | 95.5 | 53.1 | 49.5 | 47.8 |
| office（同上） | 99.3 | 77.0 | 84.1 | 54.8 | 41.4 | 51.7 |

复现目标是 **apartment 这一行**：跑官方 pipeline → `khronos_eval` 出表 → 对上这六个数。

工作区、数据、补丁、评测配置**全部就绪**，卡住的是内存。这一条是量出来的，不是猜的：

| 尝试 | 内存上限 | 结果 |
| :--- | ---: | :--- |
| 1 | 5 GB | 36 s 后 OOM-killed |
| 2 | 8 GB | 45 s 后 OOM-killed |
| 3 | 11 GB | 71 s 后 OOM-killed |
| 4 | 12 GB | 约 90 s 后 OOM-killed |
| 5 | 13.5 GB | 约 90 s 后 OOM-killed |

systemd 每次都记 `A process of this unit has been killed by the OOM killer` / `Failed with result 'oom-kill'`。

**是谁在涨**（RSS 逐 5 秒采样，第 4 次尝试）：

| 时刻 | `khronos_node` RSS | 机器可用内存 |
| :--- | ---: | ---: |
| 01:00:58 | 1.34 GB | 10.5 GB |
| 01:01:03 | 2.64 GB | 9.2 GB |
| 01:01:08 | 4.04 GB | 7.7 GB |
| 01:01:13 | 4.82 GB | 6.9 GB |
| 01:01:18 | 6.02 GB | 5.7 GB |

**约 250 MB/s，且没有收敛迹象**；同一时段 bag 播放器（`play_rosbag`）始终不在前几名 ——
所以吃内存的是 `khronos_node` 本身，不是 10.3 GB 的 bag 文件。本机总内存 15 GB（另有浏览器约 0.7–1 GB），
按这条曲线跑到 1745 帧结束需要的内存远超本机上限。

> 上游 README 自己写着：*"The ROS2 version of Khronos is in active development and is unstable
> and may not fully be feature-complete."* 这个无界增长与这句话是一致的；**在复现记录里它是"本机内存不够"，
> 不是"方法不行"**。

### 想在这台机器上跑通的话，三条路（都需要改实验口径，故未擅自采用）

1. **降内存换规模**：`khronos_ros/config/mapper/uHumans2.yaml` 里有 `voxel_size: 0.1`、
   `max_buffer_size: 300`、`object_reconstruction_resolution: -0.02` 等旋钮 —— 调粗分辨率能显著降内存，
   但**这就不是论文那组配置了**，出来的表不能当表 I 用（应作为"降配变体"单独报）。
2. **截断 bag**：只播前 30 s（`--playback-duration`），得到部分场景的重建 —— 同样不是论文那张表。
3. **换机器**：≥32 GB 内存的机器上，本文件夹的 `reproduce.py` 会直接通过 `require()`（它用
   `MemAvailable` 判定，阈值 20 GB）并跑完整流程。

1. 建 ROS 2 工作区，`git clone` + `vcs import . < khronos/install/https.rosinstall`；
2. 系统依赖 `ros-$ROS_DISTRO-gtsam libgoogle-glog-dev nlohmann-json3-dev`（本机无 sudo 时走 micromamba/conda-forge，与 ROS 1 那套做法一致）；
3. `colcon build --symlink-build -DCMAKE_BUILD_TYPE=Release`；
4. 下 `tesse_cd_office`（变化与动态物体最多的那条）→ 按 README 改 bag 路径 → 跑 launch；
5. 用 `khronos_eval` 的 `scripts/evaluate_pipeline.sh` + `plotting/tables.py` 出表，与论文对照。

> ⚠️ 语义推理（`semantic_inference`）是**可选**的：模拟数据集默认用真值语义标签，
> 真实数据集用预录的分割话题 —— 也就是说**没有 GPU / 没有 TensorRT 也能跑通主线**，
> 只是不能用在线开放集分割。这一点复现时要写清楚。

## Documentation

- 论文自报数字与阻塞分析：[`paper_baseline.md`](paper_baseline.md)
- `reproduce.py`：`require()` 给出上面这条阻塞的**可判定**版本（满足即通过）
- 本文件夹的实测记录：[`work/`](work/)
- 复现区索引与约定：[`../README.md`](../README.md)

<!-- run_all.py 读下面这几行生成索引表，改动请保持同样的 | 键 | 值 | 形式 -->

| 元数据 | 内容 |
| :--- | :--- |
| 项 | 内容 |
| 怎么才能跑 | 可用内存 ≥ 20 GB 的机器（`require()` 按 `MemAvailable` 判定）；本机 15 GB 总内存，实测 >13.5 GB 仍不够 |
| 论文 | Khronos: A Unified Approach for Spatio-Temporal Metric-Semantic SLAM in Dynamic Environments |
| 论文链接 | [arXiv:2402.13817](https://arxiv.org/abs/2402.13817) |
| 论文报告值 | 官方评测套件会直接打出论文那张表：Accuracy / Completeness / F1@0.2、Object F1、Dynamic F1、Change F1（见 `khronos_eval` 的 `plotting/tables.py`） |
| 代码 | [MIT-SPARK/Khronos](https://github.com/MIT-SPARK/Khronos) ✅ BSD-3，**ROS 2 版** |
| 数据 | 论文数据集在 Google Drive（免注册）：模拟 `tesse_cd` + 真实 `khronos_real`（mezzanine rosbag）；实测文件夹可达 |
| 为什么在这 | **官方要求 Ubuntu 24.04 + ROS 2 Jazzy —— 正是本机**（`lsb_release`：Ubuntu 24.04.4，`/opt/ros/jazzy`），而且仓库**自带评测套件**，能出与论文同格式的表；任务书 §2 难点 4 的核心参考 |
| 方向 | D1 · 动态环境下的鲁棒定位与 SLAM（4D 时空地图 + 变化检测） |
| 任务书对应 | §2 难点 4 高变动场景的地图维护；§4.1 地图更新策略（「删什么、什么时候删」） |
| 复现顺序 | 12 |
| 能否复现 | ✅ **能，而且环境正好命中**：Ubuntu 24.04 + ROS 2 Jazzy 就是官方要求的组合，`colcon build` 已在本机跑通；数据（模拟 bag + GT）与评测套件都是官方直链。剩下的是跑一遍 + 用官方 `evaluate_pipeline.sh` 出表。 |
| 复现完成 | ☐ 待做（工作区/数据/驱动 ✅，未跑） |
