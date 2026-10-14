<div align="center">

# SLAM Learning

**地图修复？**

动态环境中的鲁棒定位与 SLAM · 定位系统自恢复

[![CPU reproducibility](https://github.com/p20030920p/slam_learning_updated/actions/workflows/ci.yml/badge.svg)](https://github.com/p20030920p/slam_learning_updated/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.10-3776AB)](../src/pyproject.toml)

[English](../README.md) | 中文

[开放问题](#开放问题) · [定位实测 GIF](#静态与动态定位录制) · [方向分析](#方向分析) · [相关工作](#相关工作)

[复现结果](#复现结果) · [实验证据](#实验证据) · [假设](#假设) · [分支](#分支)

</div>

## 开放问题

**在退化与大变动环境中，什么样的策略能够有效地让定位系统自恢复？** 工作文档：[主线与缺口](self-recovery/README.zh-CN.md) · [论文地图](self-recovery/SURVEY.zh-CN.md) · [可行性评估](self-recovery/FEASIBILITY.zh-CN.md) · [按策略族的假设集](self-recovery/HYPOTHESES-BY-PAPER.zh-CN.md) · [逐篇假设](self-recovery/PAPER-TO-HYPOTHESIS.zh-CN.md)。此前放在本仓库的语义建图与视觉定位方向已归档到旧库 [SLAM_Learning](https://github.com/p20030920p/SLAM_Learning)。

## 仿真实验与本机演示入口

[**SLAM-Physical 公开实验仓库**](https://github.com/p20030920p/SLAM-Physical)：BeautyMap 静态位姿修正与 C1/C2/C4 对照、首个物体离场场景、实测报告，以及 BeautyMap / DUFOMap 的实时 RViz 演示。本机双击 [demo 文件夹](../demo/README.md) 中的脚本，缺少同级实验仓库时会自动克隆。演示重新执行原生流程；小样本演示不替代下文的论文正式复现。

新增 [Windows / WSL2 键盘 AMCL 操作指南](https://github.com/p20030920p/SLAM-Physical/blob/main/docs/WINDOWS_AMCL.zh-CN.md)：实时真值/估计偏移、自动录制、论文地图适配与同一输入回放对照。

本机 `demo/14_static_keyboard.cmd` 打开纯静态场景，`demo/15_dynamic_keyboard.cmd` 打开含三个运动障碍物的场景并选择原始/论文地图；两个入口均自动录制。`demo/16_record_static_dynamic.cmd` 执行独立建图/测试录制及重复 AMCL 对比。

## 静态与动态定位录制

**录制条件。**Gazebo，2026-10-14：建图 A 与独立测试 B，静态与动态（三个运动箱体）两种场景，十二张传感器地图、42 次有效 AMCL 回放。绿色为真值，蓝色为定位估计，橙色为运动箱体。

**平面位置 RMSE，排除最初 5 秒，单位 cm，越小越好。**按传感器家族分别比较。

| 地图类别 | 建图方法 | 纯静态 | 动态 | 动态 RMSE 降幅 | 干净地图＋动态测试 |
| --- | --- | ---: | ---: | ---: | ---: |
| LiDAR | 原始，不使用论文算法 | 5.59 | 6.29 | 基线 | 4.86 |
| LiDAR | BeautyMap | 6.01 | 5.52 | 12.3% | 5.52 |
| LiDAR | DUFOMap | 6.21 | 5.06 | 19.5% | 4.75 |
| RGB-D 几何 | 原始，不使用论文算法 | 5.97 | 6.45 | 基线 | 6.48 |

另有两个已归档方向的 RGB-D 几何地图族（ConceptGraphs、HOV-SG），位置 RMSE 分别为 5.48／6.02／6.36 cm 与 6.35／6.28／5.71 cm；第 3 类是其 GIF。

每组条件下三次相同输入的 AMCL 回放给出相同的位置估计。单一受控场景。[CSV](../results/localization/static-dynamic/summary.csv) · [协议与地图](https://github.com/p20030920p/SLAM-Physical/blob/main/docs/results/static-dynamic/README.md)。

### 1. 纯静态场景

![纯静态：六种地图、轨迹与实时误差](../results/localization/static-dynamic/static.gif)

静态建图 A 与独立静态测试 B，无运动箱体。干净场景中过滤不带来定位收益。[MP4](../results/localization/static-dynamic/static.mp4)。

### 2. 动态场景——LiDAR 地图过滤

![动态 LiDAR：原始、BeautyMap 与 DUFOMap 对照](../results/localization/static-dynamic/dynamic-lidar.gif)

建图与测试期间均有三个运动箱体。同一测试 B 上，相比未过滤的 LiDAR 地图，BeautyMap 的 RMSE 降低 **0.78 cm**，DUFOMap 降低 **1.23 cm**。[MP4](../results/localization/static-dynamic/dynamic-lidar.mp4)。

### 3. 动态场景——RGB-D 几何地图

![动态 RGB-D 几何：原始基线与两个已归档方法对照](../results/localization/static-dynamic/dynamic-rgbd.gif)

以 RGB-D 原始地图为基线，上表所述两个已归档的 RGB-D 几何方法分别使 RMSE 降低 **0.43 cm** 与 **0.18 cm**。[MP4](../results/localization/static-dynamic/dynamic-rgbd.mp4)。

### 4. 控制组——干净地图＋相同动态测试

![静态干净地图＋完全相同的动态测试：六种方法](../results/localization/static-dynamic/clean-map-dynamic-test.gif)

与第 2、3 类同一份动态测试 B，只把建图 A 换成静态录制：原始 LiDAR 的 RMSE **4.86 cm**，动态建图结果为 **6.29 cm**。[MP4](../results/localization/static-dynamic/clean-map-dynamic-test.mp4)。

建图使用仿真提供的传感器位姿；测试 B 的 AMCL 仅接收扫描、轮速里程计与待测地图，真值只用于评分。[时序与轨迹](../results/localization/static-dynamic/README.md) · [动态对照 MP4](https://github.com/p20030920p/SLAM-Physical/blob/main/docs/results/static-dynamic/dynamic-localization-replay.mp4)。

## 方向分析

**SLAM — Simultaneous Localization and Mapping，同步定位与建图：**利用传感器观测，同时估计自身运动并构建地图。

- **动态环境中的鲁棒定位与 SLAM：**物体运动时仍能可靠估计自身运动并维护稳定地图；当地图与现状不再一致时，保持位姿估计可信。

本仓库只保留这一个方向。用五个要素理解这个过程，当前主线在其外围加上检测与恢复：

```text
传感器数据 → 前端 → 后端（优化） → 地图构建与位姿输出
              ↓        ↑                    ↓
          回环检测 ────┘            失效检测 → 恢复
```

| 要素 | 收益 | 本仓库的做法 |
| --- | --- | --- |
| 传感器数据 | 干净输入 | 已录制的 Gazebo 激光与 RGB-D 采集 |
| 前端 | 稳定匹配 | 定位前先做静态结构过滤（DUFOMap、BeautyMap） |
| 后端 | 一致位姿 | 由扫描与轮速里程计驱动的 AMCL 位姿更新；异常约束处理不在这些实验内 |
| 回环检测 | 减少漂移 | 不在这些实验内：本平台是 AMCL，没有因子图后端 |
| 地图构建 | 稳定地图 | 给定位姿的建图 A 生成各地图；同一测试 B 上为六个地图族打分 |
| 失效检测与恢复 | 位姿可信 | 当前开放主线：检测 → 归因 → 恢复 → 确认，工作文档见上 |

已完成的建图实验使用给定位姿，单独检查地图构建；完整 SLAM、导航与因子图后端不在这些实验范围内。

## 相关工作

以下回放录制运行的保存结果。GIF 保留对应 MP4 的播放时序；两个建图回放中每个选定地图观测在 12 fps 下保持八帧。[DUFOMap 时序](../results/reference/dufomap/media/timing.json) · [BeautyMap 时序](../results/reference/beautymap/media/timing.json) · [IR-MCL 时序](../results/reference/ir-mcl/media/timing.json) · [AdaM-MCL 时序](../results/reference/adam-mcl/media/timing.json)。

### [DUFOMap](papers/dufomap.zh-CN.md)

![DUFOMap 核心回放](../results/reference/dufomap/media/preview.gif)

**KITTI-00 户外场景，141 帧激光雷达扫描。**用已观测的空区域识别动态点，位姿容差保护静态几何。GIF 节选 21 帧，对比原始、剔除与保留点，背景为最终地图。[MP4](../results/reference/dufomap/media/replay/replay.mp4)。

### [BeautyMap](papers/beautymap.zh-CN.md)

![BeautyMap 核心回放](../results/reference/beautymap/media/preview.gif)

**KITTI-00 户外场景，141 帧激光雷达扫描。**通过占据比较清理动态残影，用恢复机制保护静态几何。GIF 节选 21 帧，对比原始、剔除与保留点，背景为最终地图。[MP4](../results/reference/beautymap/media/replay/replay.mp4)。

### [IR-MCL](papers/ir-mcl.zh-CN.md)

![IR-MCL 已保存定位回放](../results/reference/ir-mcl/media/preview.gif)

**波恩 IPBLab 室内实验室，官方公开的定位序列，1543 帧二维激光扫描。**神经占据场为每个粒子渲染一条合成扫描，渲染距离与真实距离之差用于加权粒子。GIF 以作者工具自带的 10 fps 回放全部 1543 帧。[MP4](../results/reference/ir-mcl/media/replay/replay.mp4)。

### [AdaM-MCL](papers/adam-mcl.zh-CN.md)

![AdaM-MCL 评测会话录制](../results/reference/adam-mcl/media/preview.gif)

**自建 128 格室内平面、一个留出场景、200 个粒子。**卷积网络把地图与二维扫描变成可采样的位姿分布，全局定位的粒子直接从整张地图上抽取，而不是从均匀先验。与上面几条不同，这条 GIF 就是按真实时间录下来的运行本身：粒子云从均匀铺开逐步收紧，第 63 次更新发生瞬移后再次收紧。[MP4](../results/reference/adam-mcl/media/replay/replay.mp4)。

## 复现结果

| 工作 | 数据 | 结果 |
| --- | --- | --- |
| [DUFOMap](https://github.com/p20030920p/SLAM_Learning/blob/535a2780af7ca7eb3aa02f722e1340fe90bc2dcf/docs/DUFOMAP_TABLE4.zh-CN.md) | KITTI-00，141 扫描 | 表 IV 准确率匹配 |
| [BeautyMap](https://github.com/p20030920p/SLAM_Learning/blob/535a2780af7ca7eb3aa02f722e1340fe90bc2dcf/docs/KITTI_PAPER_PROTOCOL.zh-CN.md) | 历史 KITTI-02，91 扫描 | 表 III 准确率匹配 |
| [IR-MCL](papers/ir-mcl.zh-CN.md) | 波恩 IPBLab，公开定位序列，1543 扫描 | 位置 RMSE 5.32 cm，论文 5.13 cm |
| [AdaM-MCL](papers/adam-mcl.zh-CN.md) | 自建 128 格平面，一个留出场景，123 次更新 × 10 次重复 | 上游流程跑通；未与论文数值对照 |

## 实验证据

以下数值取自作者源库链接的论文及我们保存的作者代码运行结果。每张表仅对照同一种方法，不作跨方法排名。

**共用指标。** DUFOMap 和 BeautyMap 的 SA、DA 定义相同。$S,D$ 为真值中的静态／动态点数；$S_k,D_r$ 为正确保留的静态点数／正确剔除的动态点数。AA（DUFOMap）为几何平均，HA（BeautyMap）为调和平均。[DUFOMap 定义](https://arxiv.org/html/2403.01449v1#S4.SS2) · [BeautyMap 定义](https://arxiv.org/html/2405.07283v1#S4)。

$$
\begin{aligned}
\mathrm{SA} &= 100\frac{S_k}{S}, &
\mathrm{DA} &= 100\frac{D_r}{D},\\
\mathrm{AA} &= \sqrt{\mathrm{SA}\,\mathrm{DA}}, &
\mathrm{HA} &= \frac{2\,\mathrm{SA}\,\mathrm{DA}}{\mathrm{SA}+\mathrm{DA}}.
\end{aligned}
$$

### DUFOMap

KITTI-00，141 扫描公开数据；完整设置：体素 0.1 m、d_s=0.2 m、d_p=1。[作者源库](https://github.com/KTH-RPL/dufomap/tree/9e239ddd5995136e14f5212f33382a6ebc59e518) · [论文表 IV](https://arxiv.org/html/2403.01449v1#S5.T4) · [我们的结果](https://github.com/p20030920p/SLAM_Learning/blob/535a2780af7ca7eb3aa02f722e1340fe90bc2dcf/docs/DUFOMAP_TABLE4.zh-CN.md)。

| 指标 | 论文 % | 复现 % |
| --- | ---: | ---: |
| SA | 97.96 | 97.9635 |
| DA | 98.72 | 98.7196 |
| AA | 98.34 | 98.3408 |

完整设置的三项数值保留两位小数后均与论文一致。表 IV 五组设置共 15 项准确率均匹配；本表不包含运行时间和在线实验。

### BeautyMap

历史 KITTI-02，第 860–950 帧，共 91 扫描；XY=1 m、Z=0.5 m、范围 40 m。[作者源库](https://github.com/MKJia/BeautyMap/tree/98bce4a97db96ddd0d5342e31425c7679f58ba2e) · [论文表 III](https://arxiv.org/html/2405.07283v1#S4.T3) · [我们的结果](https://github.com/p20030920p/SLAM_Learning/blob/535a2780af7ca7eb3aa02f722e1340fe90bc2dcf/docs/KITTI_PAPER_PROTOCOL.zh-CN.md)。

| 指标 | 论文 % | 复现 % |
| --- | ---: | ---: |
| SA | 83.40 | 83.3978 |
| DA | 82.41 | 82.4092 |
| HA | 82.90 | 82.9006 |

三项数值保留两位小数后均一致。XY=0.5／1／2 m 的九项准确率全部匹配。使用历史预处理／GT 与作者 HA 评分器；论文当时的精确方法提交尚未确定。其他序列及运行时间不在本表范围内。

### IR-MCL

波恩 IPBLab，官方公开的唯一一个定位序列；评分窗口为 1543 帧中的 1354 帧，因为仓库自带的评估会剔除最初 20 秒。[作者源库](https://github.com/PRBonn/ir-mcl/tree/aab8c91b37e59f94442d8eddfa2f920ab1ecc4c5) · [论文 IV-B 定位结果表](https://arxiv.org/html/2210.03113v2#S4.SS2) · [我们的运行](../results/reference/ir-mcl/runs/ir-mcl-wsl/record.json)。

| 指标 | 论文 Seq 1 | 复现 |
| --- | ---: | ---: |
| 位置 RMSE（cm） | 5.13 | 5.32 |
| 偏航 RMSE（度） | 1.05 | 1.07 |
| 位置 < 5 cm（%） | 63.15 | 61.74 |
| 位置 < 10 cm（%） | 97.27 | 96.01 |
| 位置 < 20 cm（%） | 100.00 | 100.00 |
| 偏航 < 0.5°（%） | 47.12 | 47.64 |
| 偏航 < 1°（%） | 74.59 | 75.85 |
| 偏航 < 2°（%） | 94.24 | 93.57 |

论文 Seq 1 的百分比恰好是 1354 个样本上的整数计数，与本仓库评估产生的窗口一致，因此两行可直接对照。C++ 运动模型的随机数发生器由 `std::random_device` 播种，重复运行会略有差异；第二次完整运行给出 5.28 cm。上游 README 补遗表中的 6.62 cm／1.11° 是整个自录数据集的汇总而非 Seq 1，本表不使用它。

### AdaM-MCL

自建 128 格室内平面、一个留出场景、123 次滤波更新、200 个粒子、$T_{\mathrm{cut}}=0.6$——粒子数与信赖阈值取自论文的仿真设置。[作者源库](https://github.com/Runjian-Chen/AdaM_MCL/tree/e8aedd2bae03816aabd5300e5ca2fe181b39d830) · [论文表 II](https://arxiv.org/html/2009.00211v3) · [我们的运行](../results/reference/adam-mcl/runs/adam-mcl-wsl/record.json)。

| 指标 | 论文表 II | 本次复现 |
| --- | ---: | ---: |
| 全局定位 $E_{pos}$ | 0.153 m | 未做数值对照 |
| 绑架 $E_{pos}$ | 0.128 m | 未做数值对照 |

**未做数值对照。** 论文的 20 张仿真地图为 43 m × 43 m，另有 6 条评测序列与已发布权重，全部是外部下载；本次用自建平面，训练 **2432** 次优化步而作者默认 **2 880 000** 步，格不是米。本次实测（单位：格）：10 次重复的位置 RMSE 5.49，末帧误差均值 6.78，每次更新 0.43 s，10 次重复中 0 次满足折算到本平面的论文收敛判据。

## 假设

我们假设，保留地图更新背后的观测证据，并随着位姿估计的改善重新审视这些更新，能够减少持续性建图错误，保持几何地图更加一致。当前自恢复主线的候选假设列在[开放问题](#开放问题)一节。

## 分支

| 分支 | 用途 |
| --- | --- |
| main | 提交展示：单一方向（动态环境中的鲁棒定位与 SLAM）、两项方法复现、开放问题与假设。 |
| [reproduce/author-originals](https://github.com/p20030920p/SLAM_Learning/tree/reproduce/author-originals) | 作者原流程、论文表格评分与录制。 |
| [notes/personal-study-guide-20261008](https://github.com/p20030920p/SLAM_Learning/tree/notes/personal-study-guide-20261008) | 个人学习笔记与 `src/physical/` 实物实验，保留操作说明和失败记录。 |


[AI 使用](guides/DISCLOSURE.zh-CN.md) · [来源／许可](guides/ATTRIBUTION.zh-CN.md) · [引用](CITATION.cff) · [许可](../src/LICENSE)
