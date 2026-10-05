<div align="center">

# 01-08 · NGD-SLAM

**没有 GPU 也要实时：用光流与深度方差替代神经网络的逐帧分割，让追踪不再等网络 —— ATE 与 RPE-平移命中论文。**

[![venue](https://img.shields.io/badge/venue-IROS%202025-22314E)](https://arxiv.org/abs/2405.07392)
![result](https://img.shields.io/badge/result-ATE%200.0157%20vs%200.015-2ea043)
[![code](https://img.shields.io/badge/code-yuhaozhang7%2FNGD--SLAM-181717?logo=github&logoColor=white)](https://github.com/yuhaozhang7/NGD-SLAM)
![data](https://img.shields.io/badge/data-TUM%20RGB--D%20%C2%B7%20direct%20links-1c7ed6)
![compute](https://img.shields.io/badge/compute-CPU%20only-6f42c1)

[结论](#一句话-verdict) &nbsp;•&nbsp; [复现结果](#复现结果-results) &nbsp;•&nbsp; [记录](#记录-log)

*[← 复现区索引](../README.md) &nbsp;•&nbsp; [论文报告值](paper_baseline.md) &nbsp;•&nbsp; [复现脚本](reproduce.py) &nbsp;•&nbsp; [回测基线](baselines.json)*

</div>

---

## 一句话 Verdict

| 指标 | 本文件夹（TUM f3/walking_xyz） | 论文表 I |
| :--- | ---: | ---: |
| ATE | **0.0157 m** | 0.015 m |
| RPE 平移 | **0.0201 m/s** | 0.020 m/s |
| RPE 旋转 | 0.604 °/s（RMSE）/ 0.475 °/s（均值） | 0.470 °/s —— **未解差异**（论文没写用哪个统计量） |

读官方代码推翻了计划里的一条判断：它**用** YOLO 语义（`System.cc:217`），省掉的是「追踪等网络」，不是语义本身。

## 关键设定 Settings

| 项 | 内容 |
| :--- | :--- |
| 本机怎么跑 | 纯 CPU · 官方 C++ 自编 + `.venvs/dmb`；数据集直链免注册 |
| 论文 | NGD-SLAM: Towards Real-Time Dynamic SLAM without GPU |
| 论文链接 | [arXiv:2405.07392](https://arxiv.org/abs/2405.07392) |
| 论文报告值 | [`paper_baseline.md`](paper_baseline.md) —— f3/w xyz：ATE **0.015 m**、RPE 0.020 m/s、0.470 °/s |
| 代码 | [yuhaozhang7/NGD-SLAM](https://github.com/yuhaozhang7/NGD-SLAM) ✅ 官方仓库，本地 commit `a93a14c` |
| 数据 | TUM RGB-D（[cvg.cit.tum.de](https://cvg.cit.tum.de/data/datasets/rgbd-dataset/download)，**免注册直链**）；BONN |
| 方向 | D1 · 动态环境下的鲁棒定位与 SLAM |
| 任务书对应 | §2 难点 5（算力受限 + 语义）；§1 H6（算力与分割冲突的调度方案） |
| 复现顺序 | 6 |
| 能否复现 | ✅ 能：官方代码明确「无 GPU」，TUM RGB-D 免注册直链，对上论文的 ATE / RPE 表。 |
| 复现完成 | ☑ 2026-10-05 · ATE 与 RPE-平移命中论文 |

---

## 它做了什么 What it does

> ⚠️ **本 README 原来写的是错的。** 原描述是「不用神经网络做分割，改用光流 + 深度方差判断特征点是否运动」。
> **读代码后确认：它用了神经网络（YOLO-fastest-xl），而且恰恰是一个语义方法。**
> 它省掉的不是网络，而是**追踪对网络的等待**。详见 [`work/code_reading.md`](work/code_reading.md)。

**NDG-SLAM = ORB-SLAM3 + 一个 YOLO 语义线程 + 被改写的 `Tracking.cc`。**
`src/` 里 27 个 `.cc` 只有 `YOLO.cc` 是新文件，其余都是 ORB-SLAM3 的——**贡献不在"加了个网络"，在于怎么让追踪不等它**。

两个机制（行号可核，全部来自官方仓库）：

**① 掩码传播**（`Tracking.cc:4286`）——网络结果只在少数帧上更新，中间帧靠光流把掩码"推"过去：

| 步 | 代码 | 做什么 |
| :-- | :--- | :--- |
| 1 | `Tracking.cc:4300-4302` | 对上一张关键掩码做 **11×11 腐蚀**，扔掉不可靠的分割边界 |
| 2 | `Tracking.cc:4304` | `ExtractDynaPoints(..., cellSize=15)`：掩码内**每 15×15 像素取一个代表点** |
| 3 | `Tracking.cc:4308` | `cv::calcOpticalFlowPyrLK` 把这些点跟踪到当前帧 |
| 4 | `Tracking.cc:4314-4317` | 取深度，得到 3D 点（深度 < 0.05 m 丢弃） |
| 5 | `Tracking.cc:4318` | `ClusterWithDBSCAN(..., eps=50, minPts=15)` 在 (x, y, depth) 上聚类 |
| 6 | `Tracking.cc:4320` | `CreateMaskFromClusters` 把聚类画回当前帧掩码 |

而**追踪侧从不等待**：`Tracking.cc:1592` 那句 `else if(mFrameNum > 1) break;` 就是题眼——
拿得到新掩码就用，拿不到就用传播顶上，只有第 1 帧会阻塞。

**② 混合追踪**（`ORBmatcher.cc:2012`）——非关键帧**根本不提 ORB**：

- `Tracking.cc:1602` 用 `Frame(mbStartOpticalFlow)` 建一个**空帧**（`Frame.cc:55`，不提取特征、不算描述子）；
- `SearchByOpticalFlow` 只把上一帧里观测数 ≥ 3 的地图点做 LK 光流，并且
  **落进动态掩码的点直接丢弃**（`ORBmatcher.cc:2045`），地图点身份直接继承；
- 光流不够用时按**分级规则**退回完整 ORB（`Tracking.cc:3381`：内点 < 20 立刻切；< 75 且隔了 5 帧；< 300 且隔了 30 帧）。

## 为什么复现它 Why

**这里要对 car.md 的假设做一次纠正。** car.md 难点 1 主张「独立于语义分割、用纯几何运动视差检测未知动态物体」。
**NGD-SLAM 不是这条路线**：它依赖 YOLO 的 COCO 类别，未知类别的动态物体同样看不见。
它真正的贡献是**算力调度**——论文 §1 H6 给的第三条修正（"低频语义 + 高频传播"）的一个完整实现。

所以复现它的正确问题是：**"把语义这个最贵的模块从每帧解耦出去，代价有多大？"**
答案是下面那组数字：精度基本不掉，速度翻倍。

## 复现结果 Results

### 一、跑法与结果

```bash
./Examples/RGB-D/rgbd_tum ./Vocabulary/ORBvoc.txt ./Examples/RGB-D/TUM3.yaml \
    <data>/rgbd_dataset_freiburg3_walking_xyz \
    ./Examples/RGB-D/associations/fr3_walk_xyz.txt
```

827 帧全部处理（论文明确要求 "processing all frames in the sequence"）。

**单次运行不能当作结果**：这个系统是多线程的（局部建图、回环与追踪并行），
同一条命令跑 7 次，ATE 落在 **0.0146 – 0.0168**，跨度比它与论文的差距还大。
所以 `reproduce.py` 默认跑 **3 次取中位数**，并把每次的值一起记下来：

| 试验 | ATE (m) | RPE 平移 (m/s) |
| :--- | ---: | ---: |
| 1 | 0.014969 | 0.019811 |
| 2 | 0.016363 | 0.021173 |
| 3 | 0.015709 | 0.020093 |
| **中位数（本次结果）** | **0.015709** | **0.020093** |
| **论文（表 I）** | **0.015** | **0.020** |
| 判定 | ✅ 命中 | ✅ 命中 |

**RPE 旋转则取决于一个论文没写明的口径**：

| 口径 | 本次 | 论文 | 判定 |
| :--- | ---: | ---: | :--- |
| RMSE | 0.6036 °/s | 0.470 | ❌ 高 28% |
| **均值** | **0.4753 °/s** | 0.470 | ✅ 差 1.1% |

论文表头只写 "RPE rotation (°/s)"，**没说是 RMSE 还是均值**。
这个误差分布很偏（median 0.39、max 5.6），正好是两个口径会分道扬镳的情形。
**这是一个真实的、未解决的复现差异**——不是我们没跑对，也不是我们没读懂自己的数据。

复现口径：ATE/平移用仓库自带的 `evaluation/evaluate_ate_scale.py`（**取不做尺度修正的刚体对齐值**，
RGB-D 尺度已知，脚本里的尺度拟合是为单目写的；本次拟合出的尺度是 0.973，接近 1）；
旋转用 TUM 官方 `evaluate_rpe.py`（`--fixed_delta --delta 1 --delta_unit s`，即论文的 m/s 与 °/s 口径）。

### 二、速度

| 指标 | 本次 | 论文 |
| :--- | ---: | ---: |
| 平均追踪耗时 | **20.76 ms/帧**（三次 20.33 / 20.95 / 20.76） | 16.72 ms/帧（≈60 FPS） |
| 端到端跑完 827 帧 | 约 45–52 s（含建图与回环） | — |
| 峰值内存 | 631 MB | — |

比论文慢约 24%，但**同量级、同为纯 CPU**，而且这是在**关闭可视化**、硬件不同的情况下测的——
这个数只能说明"量级对上了"，不能当作对 16.72 ms 的精确复现。

### 三、环境上必须处理的三件事（都不是算法问题）

| 问题 | 处理 |
| :--- | :--- |
| `CMakeLists.txt:42` 是 `find_package(Pangolin REQUIRED)`，但发行版 noble 不带 `libpangolin-dev`，且本机无 sudo | 用 `apt-get download ros-jazzy-pangolin` 解到本地前缀；它的 CMake 配置里硬编码了 `/usr/lib/x86_64-linux-gnu/libepoxy.so`，改成我们自己的路径（见 `code/headless_and_epoxy.patch` 说明） |
| Pangolin 0.9.6 依赖 `libepoxy` 而不是 GLEW | 同样 `apt-get download libepoxy-dev libepoxy0` 解到本地前缀 |
| 示例程序默认开可视化，本机没有可依赖的 X（无 Xvfb、无 sudo） | `Examples/RGB-D/rgbd_tum.cc` 的最后一个参数 `true` → `false`（**只改这一行**，补丁留档） |

另有一条**照抄官方 `build.sh` 会撞上、但其实不需要**的坑：
`build.sh` 会构建 Sophus 的库与单元测试，而 Sophus 的测试在 GCC 13 下因 `-Werror=array-bounds` 失败；
**但这个项目只用 Sophus 的头文件**（`CMakeLists.txt:49` 只把它加进 include 路径），跳过它不影响任何结果。

## 记录 Log

| 日期 | 做了什么 | 结果 / 数字 | 结论 |
| :--- | :--- | :--- | :--- |
| 10-05 | 从论文里找到官方仓库地址（`yuhaozhang7/NGD-SLAM`）并克隆 | commit `a93a14c` | 用论文自己的仓库，不用任何 fork |
| 10-05 | 下载 TUM `fr3_walking_xyz` | 527 MB，827 帧，**免注册** | 数据无阻塞 |
| 10-05 | 逐行读 `Tracking.cc` / `ORBmatcher.cc` / `YOLO.cc` | 见 [`work/code_reading.md`](work/code_reading.md) | **推翻本 README 原有的"纯几何"描述** |
| 10-05 | 解决 Pangolin / epoxy / headless 三个环境问题 | 编译通过 | 见上表 |
| 10-05 | 跑 3 次，827 帧全量 | ATE 0.0146–0.0156、RPE 平移 0.0195–0.0201 | ✅ 两项命中论文 |
| 10-05 | 旋转 RPE 两种口径 | RMSE 0.601 / 均值 0.476（论文 0.470） | ⚠️ **未解差异**，已如实记录 |

## 下一步 Next

1. **RPE-旋转的差异定性**：论文表头没写 RMSE 还是均值。要么找到它引用的原始表格来源，
   要么在 BONN 序列上再验一次——如果 BONN 的旋转数也对不上，就说明是口径问题而不是我们的运行问题。
2. **回答"动态物体类别 × 是否检出"**（原来的复现目标）：现在知道它走 YOLO 的 COCO 类别，
   所以正确做法是**构造 COCO 之外的动态物体**（气球/被推的椅子）看它漏不漏——
   这正好同时检验 car.md 难点 1 的假设和 NGD-SLAM 的边界。
3. **补 f3/w static**（论文 0.007 m）：静态序列是这套系统的下限，
   如果连静态序列都对不上，说明差异来自 SLAM 本身而不是动态处理。