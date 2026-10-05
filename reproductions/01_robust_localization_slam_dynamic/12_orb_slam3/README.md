<div align="center">

# 01-12 · ORB-SLAM3（双目惯性 / VIO 半边）

**ORB-SLAM3: An Accurate Open-Source Library for Visual, Visual-Inertial and Multi-Map SLAM**

视觉 / 视觉惯性 / 多地图 SLAM 的经典实现。

[![venue](https://img.shields.io/badge/venue-T--RO%202021-22314E)](https://arxiv.org/abs/2007.11898)
![result](https://img.shields.io/badge/result-ATE%200.035--0.045%20m%20vs%200.036-2ea043)
[![code](https://img.shields.io/badge/code-UZ--SLAMLab%2FORB__SLAM3-181717?logo=github&logoColor=white)](https://github.com/UZ-SLAMLab/ORB_SLAM3)
![data](https://img.shields.io/badge/data-EuRoC%20MH__01%20%C2%B7%20HF%20mirror-1c7ed6)
![compute](https://img.shields.io/badge/compute-CPU%20only%20%C2%B7%20no%20ROS-6f42c1)

[Quick start](#quick-start) &nbsp;•&nbsp; [Results](#results) &nbsp;•&nbsp; [Notes](#notes)

*[← 复现区索引](../README.md) &nbsp;•&nbsp; [复现脚本](reproduce.py) &nbsp;•&nbsp; [回测基线](baselines.json)*

</div>

|  |  |
| :--- | :--- |
| **指标（EuRoC MH_01，双目惯性）** | 本文件夹（三次运行） · 论文 论文表 II |
| **RMSE ATE** | **0.0454 / 0.0351 / 0.0416 m** · 论文 0.036 m |
| **Platform** | CPU · 20 核 · Ubuntu 24.04 + ROS 2 Jazzy |
| **Reproduce** | [`reproduce.py`](reproduce.py) · [`baselines.json`](baselines.json) |

为什么它值得单独一条：任务书 §0.1 的实物是 **D435i（双目 IR + 深度 + IMU）**，
而此前 17 个复现**没有一个吃这套配置**；ORB-SLAM3 自带 `stereo_inertial_realsense_D435i`
例子与 `RealSense_D435i.yaml`，是「对上实物相机半边」最短的一条路。

---

## Quick start

| 依赖 | 版本 / 说明 |
| :--- | :--- |
| 构建 | 自编 Pangolin v0.8 + ORB-SLAM3，**不需要 ROS** |
| 数据 | EuRoC MH_01（ETH 源从本机连不上，改用 HuggingFace 镜像） |
| 为什么是它 | 任务书 §0.1 的实物是 D435i（双目 IR + 深度 + BMI055 IMU），仓库自带 `stereo_inertial_realsense_D435i` 例子 |
| 指标 | 仓库自带的 `evaluation/evaluate_ate_scale.py`，不自己发明口径 |

```bash
bash reproductions/01_robust_localization_slam_dynamic/12_orb_slam3/work/run_euroc.sh
python3 reproductions/run_all.py --only 01-12
```

1. 装依赖（Pangolin、OpenCV、Eigen3、DBoW2/g2o 仓库自带），`./build.sh`；
2. 解决 EuRoC 下载（本机实测 `robotics.ethz.ch` 不可达，需换镜像——**这一步先查清再动手**）；
3. `./euroc_examples.sh`（全部序列 × 各传感器配置）或单跑 `stereo_inertial_euroc`；
4. 用仓库 `evaluation/` 里的真值变换 + 官方 ATE 口径对表；
5. 再看能不能用 `stereo_inertial_realsense_D435i` 接上实物（或仿真补齐后的数据）。

## Results

```bash
cd results/run_mh01 && ../../code/ORB_SLAM3/Examples/Stereo-Inertial/stereo_inertial_euroc \
  ../../code/ORB_SLAM3/Vocabulary/ORBvoc.txt \
  ../../code/ORB_SLAM3/Examples/Stereo-Inertial/EuRoC.yaml \
  ../../data/raw ../../code/ORB_SLAM3/Examples/Stereo-Inertial/EuRoC_TimeStamps/MH01.txt dataset-MH01
```

三次同样的命令、同样的数据（ORB-SLAM3 是多线程的，结果本身就会抖）：

| 运行 | RMSE ATE（全轨迹） | 尺度校正后 | 匹配上的位姿对 |
| :-- | --: | --: | --: |
| run 1 | 0.0454 m | 0.0247 m | 3638 |
| **run 2** | **0.0351 m** | 0.0225 m | 3638 |
| run 3 | 0.0416 m | 0.0237 m | 3570 |
| **论文表 II（MH01，双目惯性）** | **0.036 m** | — | — |

**判读**：

1. **论文那个数复现出来了**：run 2 的 0.0351 m 与论文 0.036 m 只差 1 mm；
   三次的散布（0.035–0.045）把论文值夹在中间。**只报最好的一次是挑数据，只报最差的一次也是**，
   所以三次都列出来。
2. **两条曲线口径不同**：上游评测脚本同时给出「不做尺度校正」与「做尺度校正」两列
   （0.0454 vs 0.0247）。双目惯性里尺度是可观测的，选哪列会差一倍；
   论文表 II 的脚注写的是「all the frames in the trajectory, comparing with the processed GT」，
   所以这里以**不做尺度校正**的全轨迹为主列。
3. **整条链路没有 GPU、没有显示器、没有 ROS、没有 sudo**：Pangolin v0.8 用 conda 的 GLFW 自己编，
   ORB-SLAM3 自包含编译，例子本身就是 `bUseViewer=false`。
   代价只是**墙钟时间**（3682 帧双目约 4 分钟），不是硬件门槛。

### 一个上游的坑（值得记下来）

序列路径给错的时候（例如指到不存在的目录），程序**不会报错，而是卡死在 100% CPU 上空转**。
原因在 `Examples/Stereo-Inertial/stereo_inertial_euroc.cc` 的 `LoadIMU`：

```cpp
while(!fImu.eof()){
    string s; getline(fImu,s);
    if (s[0] == '#') continue;   // 文件打不开 -> getline 立刻失败 -> s 为空 -> s[0] 是 UB
    ...
}
```

文件打开失败时 `failbit` 置位而 `eofbit` 没有，`getline` 每次立即返回空串，循环不退出。
我们一开始就踩了这个：把序列目录写成 `data/raw/MH_01_easy`（实际解压出来是 `data/raw/mav0`），
于是白等了 60 分钟。**用 strace 看 `openat` 的返回值**才定位到
（`openat(.../mav0/imu0/data.csv) = -1 ENOENT`）。
教训：这种「不报错只空转」的失败模式，只能靠看系统调用或 IO 计数发现。

三个理由，逐条对上现在这份仓库的缺口：

1. **实物对不上**：本仓库 17 个复现全是 3D 雷达或纯视觉，**没有一个用「相机 + IMU」**，
   而任务书 §0.1 的实物正是 D435i —— ORB-SLAM3 的 D435i 双目惯性例子是现成的接口。
2. **仿真侧缺口**：本仓库 Gazebo 的 `front_camera` 只有 RGB、**没有深度也没有 IMU**，
   所以「仿真验证 → 自采确认」这条链在相机这一半是断的；先在公开数据上把 VIO 半边跑通，
   才知道补仿真是为了验证什么。
3. **任务书 §2 难点 7（连续时间/运动畸变）与难点 3（退化定位）**都要用到视觉惯性，
   而这一块此前是空白。

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

| # | 问题 | 处理 |
| :-- | :--- | :--- |
| 1 | 系统没有 Pangolin，且**无 sudo** | 用 micromamba 装 `glfw`，自己编 **Pangolin v0.8** 装到 `reproductions/.venvs/pangolin`（master 要 `libepoxy`，v0.8 只要 GLEW；ORB-SLAM3 本来就是对着 v0.6–0.8 写的） |
| 2 | GCC 13 不再隐式带 `<cstdint>` / `<type_traits>`，Pangolin v0.8 与 g2o 都会报一堆「`uint32_t`/`std::decay_t` 不存在」 | 编译期统一加 `-include cstdint -include type_traits`（一个开关解决一类错误，**不改上游源码**） |
| 3 | Pangolin v0.8 的 ffmpeg 驱动引用了 FFmpeg 7 已删除的 `AV_PIX_FMT_XVMC_*` | 编 Pangolin 时 `-DBUILD_PANGOLIN_FFMPEG=OFF`（ORB-SLAM3 只用它做显示，不用视频驱动） |
| 4 | ORB-SLAM3 自己的 `CMakeLists.txt` 写死 `-std=c++11`，而 Pangolin v0.8 的头文件要 C++14 | 本地补丁把它改成 `-std=c++14`，记在 [`work/local_patches.patch`](work/local_patches.patch)；**不涉及算法** |

`stereo_inertial_euroc.cc:132` 本来就是 `bUseViewer=false`，**所以运行时不需要显示器、不需要 Xvfb** ——
这一点让「无 GPU、无显示器的纯 CPU 跑 VIO」成立。

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

## Notes

## Documentation

- 论文自报数字与出处：[`paper_baseline.md`](paper_baseline.md)
- 复现脚本：[`reproduce.py`](reproduce.py) · 回测基线：[`baselines.json`](baselines.json)
- 本文件夹的脚本、协议与实测记录：[`work/`](work/)
- 复现区索引与约定：[`../README.md`](../README.md) · 状态账本：[`../../status.json`](../../status.json)

<!-- run_all.py 读下面这几行生成索引表，改动请保持同样的 | 键 | 值 | 形式 -->

| 元数据 | 内容 |
| :--- | :--- |
| 论文 | ORB-SLAM3: An Accurate Open-Source Library for Visual, Visual-Inertial and Multi-Map SLAM |
| 论文链接 | [arXiv:2007.11898](https://arxiv.org/abs/2007.11898) |
| 代码 | [UZ-SLAMLab/ORB_SLAM3](https://github.com/UZ-SLAMLab/ORB_SLAM3) ✅ GPL-3.0，**自包含 CMake，不需要 ROS** |
| 方向 | D1 · 传感器半边（VIO）；同时补上 [`../../NOTES.md`](../../NOTES.md) 里点名的空白 |
| 任务书对应 | §0.1 传感器设定；§2 难点 3/7 的视觉惯性一半 |
| 能否复现 | ✅ **能，而且完全不需要 GPU**：自编 Pangolin(v0.8) + ORB-SLAM3，跑 `stereo_inertial_euroc`，再用**仓库自带的** `evaluation/evaluate_ate_scale.py` 对表 II。 |
| 复现完成 | ☑ 2026-10-05 · MH_01 RMSE ATE 0.035–0.045 m（论文 0.036 m），用仓库自带的评测脚本 |
| 复现顺序 | 11 |
| 项 | 内容 |
| 本机怎么跑 | 纯 CPU · 自编 Pangolin v0.8 + ORB-SLAM3，**不需要 ROS**；EuRoC MH_01 三次运行 |
| 论文报告值 | 表 II, p.7（EuRoC，**双目惯性**，RMS ATE / m）：MH01 **0.036**、MH02 0.033、MH03 0.035、MH04 0.051、MH05 0.082、V101 0.038、V102 0.014、V103 0.024、V201 0.032、V202 0.014、V203 0.024，**平均 0.035** |
| 数据 | ✅ **EuRoC MH_01 已到手**（ASL 格式：3682 张双目图 + 36821 行 IMU + 真值）。⚠️ ETH 自己的 `robotics.ethz.ch` 从本机连不上（curl 000），改用 **HuggingFace 镜像** `GlowBond/EuRoC_MAV_Dataset`，见下 |
| 为什么在这 | 任务书 §0.1 的实物是 **D435i（双目 IR + 深度 + BMI055 IMU）**，而本目录此前 17 个复现**没有一个吃这套配置**。ORB-SLAM3 仓库自带 **`Examples/Stereo-Inertial/stereo_inertial_realsense_D435i`** 例子和 `RealSense_D435i.yaml`，是最短的一条「对上实物相机半边」的路 |
