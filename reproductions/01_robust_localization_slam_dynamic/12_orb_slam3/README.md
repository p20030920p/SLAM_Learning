# 01-12 · ORB-SLAM3（双目惯性 / VIO 半边）

| 项 Item | 内容 |
| :--- | :--- |
| 论文 | ORB-SLAM3: An Accurate Open-Source Library for Visual, Visual-Inertial and Multi-Map SLAM |
| Venue | **T-RO 2021**（arXiv:2007.11898） |
| 论文链接 | [arXiv:2007.11898](https://arxiv.org/abs/2007.11898) |
| 论文报告值 | 表 II, p.7（EuRoC，**双目惯性**，RMS ATE / m）：MH01 **0.036**、MH02 0.033、MH03 0.035、MH04 0.051、MH05 0.082、V101 0.038、V102 0.014、V103 0.024、V201 0.032、V202 0.014、V203 0.024，**平均 0.035** |
| 代码 | [UZ-SLAMLab/ORB_SLAM3](https://github.com/UZ-SLAMLab/ORB_SLAM3) ✅ GPL-3.0，**自包含 CMake，不需要 ROS** |
| 数据 | ✅ **EuRoC MH_01 已到手**（ASL 格式：3682 张双目图 + 36821 行 IMU + 真值）。⚠️ ETH 自己的 `robotics.ethz.ch` 从本机连不上（curl 000），改用 **HuggingFace 镜像** `GlowBond/EuRoC_MAV_Dataset`，见下 |
| 为什么在这 | 任务书 §0.1 的实物是 **D435i（双目 IR + 深度 + BMI055 IMU）**，而本目录此前 17 个复现**没有一个吃这套配置**。ORB-SLAM3 仓库自带 **`Examples/Stereo-Inertial/stereo_inertial_realsense_D435i`** 例子和 `RealSense_D435i.yaml`，是最短的一条「对上实物相机半边」的路 |
| 方向 | D1 · 传感器半边（VIO）；同时补上 [`../../NOTES.md`](../../NOTES.md) 里点名的空白 |
| 任务书对应 | §0.1 传感器设定；§2 难点 3/7 的视觉惯性一半 |
| 复现状态 | 🟡 **编译完成、正在跑**：Pangolin + ORB-SLAM3 已在本机编好（无需 sudo），EuRoC MH_01 双目惯性正在跑（纯 CPU） |

| 复现顺序 | 11 |
| 能否复现 | ✅ **能，而且完全不需要 GPU**：自编 Pangolin(v0.8) + ORB-SLAM3，跑 `stereo_inertial_euroc`，再用**仓库自带的** `evaluation/evaluate_ate_scale.py` 对表 II。 |
| 复现完成 | ☐ MH_01 正在跑（并发的 3 个进程已收成 1 个），跑完填 ATE |

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

## 数据：ETH 镜像连不上，走 HuggingFace 镜像（实测）

ETH 官方的下载链接指向 `robotics.ethz.ch`，而**本机连不上这台主机**（curl 返回 000，
连 DNS/连接都建立不了；`projects.asl.ethz.ch` 的说明页倒是可达 206）。

替代路径（本仓库在用）：

```
HF: GlowBond/EuRoC_MAV_Dataset/machine_hall.zip   (12.68 GB，内含每条序列的 .bag 与 ASL 格式 .zip)
    └── machine_hall/MH_01_easy/MH_01_easy.zip    (1.57 GB，deflate 压缩)
```

外层 zip 是「按字节区间可取」的（和 KITTI 那份一样），所以用 `remotezip` **只取 MH_01 这一个成员**、
不用下 12.68 GB。解开后就是 ORB-SLAM3 要的 ASL 目录：
`mav0/{cam0,cam1}/data/*.png`（3682 张）+ `mav0/imu0/data.csv`（36821 行）+ 真值。

## 编译：三条必须显式说的（都不是算法改动）

| # | 问题 | 处理 |
| :-- | :--- | :--- |
| 1 | 系统没有 Pangolin，且**无 sudo** | 用 micromamba 装 `glfw`，自己编 **Pangolin v0.8** 装到 `reproductions/.venvs/pangolin`（master 要 `libepoxy`，v0.8 只要 GLEW；ORB-SLAM3 本来就是对着 v0.6–0.8 写的） |
| 2 | GCC 13 不再隐式带 `<cstdint>` / `<type_traits>`，Pangolin v0.8 与 g2o 都会报一堆「`uint32_t`/`std::decay_t` 不存在」 | 编译期统一加 `-include cstdint -include type_traits`（一个开关解决一类错误，**不改上游源码**） |
| 3 | Pangolin v0.8 的 ffmpeg 驱动引用了 FFmpeg 7 已删除的 `AV_PIX_FMT_XVMC_*` | 编 Pangolin 时 `-DBUILD_PANGOLIN_FFMPEG=OFF`（ORB-SLAM3 只用它做显示，不用视频驱动） |
| 4 | ORB-SLAM3 自己的 `CMakeLists.txt` 写死 `-std=c++11`，而 Pangolin v0.8 的头文件要 C++14 | 本地补丁把它改成 `-std=c++14`，记在 [`work/local_patches.patch`](work/local_patches.patch)；**不涉及算法** |

`stereo_inertial_euroc.cc:132` 本来就是 `bUseViewer=false`，**所以运行时不需要显示器、不需要 Xvfb** ——
这一点让「无 GPU、无显示器的纯 CPU 跑 VIO」成立。

## 评测：用仓库自己的工具，不自己发明指标

```bash
# 跑（cwd 无所谓，输出落在当前目录）
./Examples/Stereo-Inertial/stereo_inertial_euroc ./Vocabulary/ORBvoc.txt \
    ./Examples/Stereo-Inertial/EuRoC.yaml <MH_01_easy 目录> \
    ./Examples/Stereo-Inertial/EuRoC_TimeStamps/MH01.txt dataset-MH01

# 评测：把 f_dataset-MH01.txt 与 evaluation/Ground_truth/EuRoC_imu/MH_GT.txt 对齐后，
# 调用上游自带的 evaluation/evaluate_ate_scale.py
python3 work/evaluate_ate.py --run-dir results/run_mh01 --gt-seq MH01 \
    --out results/orbslam3_mh01_ate.json
```

论文表 II 的脚注写明是「与 **processed GT** 比较」，`evaluation/Ground_truth/EuRoC_imu/MH_GT.txt`
就是那份 GT —— 所以评测口径直接沿用作者的工具与真值，坐标/单位/对齐方式都不需要我们猜。
