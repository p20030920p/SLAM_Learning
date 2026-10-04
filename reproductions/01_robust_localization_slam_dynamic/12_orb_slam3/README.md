# 01-12 · ORB-SLAM3（双目惯性 / VIO 半边）

| 项 Item | 内容 |
| :--- | :--- |
| 论文 | ORB-SLAM3: An Accurate Open-Source Library for Visual, Visual-Inertial and Multi-Map SLAM |
| Venue | **T-RO 2021**（arXiv:2007.11898） |
| 论文链接 | [arXiv:2007.11898](https://arxiv.org/abs/2007.11898) |
| 论文报告值 | EuRoC 双目惯性 ATE 表（待补录到 `paper_baseline.md`） |
| 代码 | [UZ-SLAMLab/ORB_SLAM3](https://github.com/UZ-SLAMLab/ORB_SLAM3) ✅ GPL-3.0，**自包含 CMake，不需要 ROS** |
| 数据 | EuRoC MAV（ETH ASL）：公开、免注册；**注意**：`robotics.ethz.ch` 这台镜像从本机连不上（curl 000），要从 ASL 页面上的其它镜像/链接取，复现时先把这条查清 |
| 为什么在这 | 任务书 §0.1 的实物是 **D435i（双目 IR + 深度 + BMI055 IMU）**，而本目录此前 17 个复现**没有一个吃这套配置**。ORB-SLAM3 仓库自带 **`Examples/Stereo-Inertial/stereo_inertial_realsense_D435i`** 例子和 `RealSense_D435i.yaml`，是最短的一条「对上实物相机半边」的路 |
| 方向 | D1 · 传感器半边（VIO）；同时补上 [`../../NOTES.md`](../../NOTES.md) 里点名的空白 |
| 任务书对应 | §0.1 传感器设定；§2 难点 3/7 的视觉惯性一半 |
| 复现状态 | ⬜ 未开始（已检查：仓库可达、无 ROS 依赖、数据公开但镜像需确认） |

| 复现顺序 | 11 |
| 能否复现 | 🟡 能，但要先解决 EuRoC 下载镜像：`./build.sh` 自包含编译（Pangolin/OpenCV/Eigen 需另装），跑 `euroc_examples.sh` 出轨迹，再按论文的 ATE 表对照；纯 CPU，慢但不需 GPU。 |
| 复现完成 | ☐ 待做 |

## 为什么它值得单独一条复现

三个理由，逐条对上现在这份仓库的缺口：

1. **实物对不上**：本仓库 17 个复现全是 3D 雷达或纯视觉，**没有一个用「相机 + IMU」**，
   而任务书 §0.1 的实物正是 D435i —— ORB-SLAM3 的 D435i 双目惯性例子是现成的接口。
2. **仿真侧缺口**：本仓库 Gazebo 的 `front_camera` 只有 RGB、**没有深度也没有 IMU**，
   所以「仿真验证 → 自采确认」这条链在相机这一半是断的；先在公开数据上把 VIO 半边跑通，
   才知道补仿真是为了验证什么。
3. **任务书 §2 难点 7（连续时间/运动畸变）与难点 3（退化定位）**都要用到视觉惯性，
   而这一块此前是空白。

## 复现计划 Steps

1. 装依赖（Pangolin、OpenCV、Eigen3、DBoW2/g2o 仓库自带），`./build.sh`；
2. 解决 EuRoC 下载（本机实测 `robotics.ethz.ch` 不可达，需换镜像——**这一步先查清再动手**）；
3. `./euroc_examples.sh`（全部序列 × 各传感器配置）或单跑 `stereo_inertial_euroc`；
4. 用仓库 `evaluation/` 里的真值变换 + 官方 ATE 口径对表；
5. 再看能不能用 `stereo_inertial_realsense_D435i` 接上实物（或仿真补齐后的数据）。
