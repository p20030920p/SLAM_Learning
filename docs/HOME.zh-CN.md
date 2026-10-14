<div align="center">

# SLAM Learning

**动态环境中的鲁棒定位与 SLAM**

动态环境中的鲁棒定位与 SLAM · 定位系统自恢复

[![CPU reproducibility](https://github.com/p20030920p/slam_learning_updated/actions/workflows/ci.yml/badge.svg)](https://github.com/p20030920p/slam_learning_updated/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.10-3776AB)](../src/pyproject.toml)

[English](../README.md) | 中文

[开放问题](#开放问题) · [定位实测 GIF](#静态与动态定位录制) · [方向分析](#方向分析) · [相关工作](#相关工作)

[复现结果](#复现结果) · [实验证据](#实验证据) · [假设](#假设) · [分支](#分支)

</div>

## 开放问题

**在退化与大变动环境中，什么样的策略能够有效地让定位系统自恢复？** 先分析失效原因、恢复目标和适用边界，再选择策略。成果包括作者原库复现，以及使用 Sim2Real-AlgoBench 机器人逐步加难的点云建图与定位测试。[问题分析与收窄](self-recovery/DESIGN.zh-CN.md) · [机器人测试协议](testing/PROTOCOL.zh-CN.md) · [汇报稿](self-recovery/TALK.zh-CN.md) · [接续状态](self-recovery/STATUS.zh-CN.md)。

## 仿真实验与本机演示入口

当前真实 Gazebo／RViz／终端流程：[一键说明](../demo/README.md)、[成对视频页](../demo/gallery.html)、[评分协议](testing/LIVE.zh-CN.md)。已准备的 Windows 脚本在 `F:\be2演讲\实机脚本`，分别提供静态、运动障碍物、持久变化及走廊观测恢复的键盘入口和自动录制入口。

[逐步演示 Notebook](../notebooks/presentation/SLAM_实验逐步展示.ipynb) 串起四种作者原库执行及四类机器人场景，保存视频、地图、独立误差复算和结论边界。本机 Notebook 与离线 HTML 在 `F:\be2演讲\展示`；[打开说明](../notebooks/presentation/README.md)。

[SLAM-Physical](https://github.com/p20030920p/SLAM-Physical) 保留此前 C1/C2/C4、物体离场与地图适配实验。其旧 `demo/14–16` 流程及历史回放分数与下面的本机现场录屏分开。

## 静态与动态定位录制

**2026-10-14 本机现场录制。**真实 Gazebo＋RViz＋终端执行，随后分别展示各方法的保存数据回放。Sim2Real 三轮全向底盘，原生二维激光＋独立三维版本。

**方法名表示地图处理，机器人定位器统一为 AMCL。**Raw 使用未清理地图；DUFOMap、BeautyMap 清理同一给定位姿三维建图输入，再作共用二维投影。各方法下面的现场 GIF 来自**同一次场景并行执行**：RViz 显示 Raw，终端报告所有组；结果 GIF 则分别展示该组数据，回放不执行新推理。

平面位置 RMSE 包含初始化，按全部保留的原生更新计算；每种条件当前一次运行。[计算公式与数值对照表](testing/LIVE.zh-CN.md#误差如何测算) · [录像名称／模块／算法对照](../demo/recording-index.json)。

### 纯静态

小初值偏移，本路线未失效。

#### Raw + AMCL

**现场执行 · Live execution**

![Pure static — Raw: shared native execution](../results/reference/robot-static/execution.gif)

[MP4 · 170202-5abed0](../results/reference/robot-static/execution.mp4)

**结果回放 · Measured result replay**

![Pure static — Raw: raw measured replay](../results/reference/robot-static/methods/raw/result.gif)

[MP4](../results/reference/robot-static/methods/raw/result.mp4) · [record](../results/reference/robot-static/methods/raw/record.json) · RMSE **7.08 cm** · 290 次原生更新。

#### DUFOMap + AMCL

**现场执行 · Live execution**

![Pure static — DUFOMap: shared native execution](../results/reference/robot-static/execution.gif)

[MP4 · 170202-5abed0](../results/reference/robot-static/execution.mp4)

**结果回放 · Measured result replay**

![Pure static — DUFOMap: dufomap measured replay](../results/reference/robot-static/methods/dufomap/result.gif)

[MP4](../results/reference/robot-static/methods/dufomap/result.mp4) · [record](../results/reference/robot-static/methods/dufomap/record.json) · RMSE **7.08 cm** · 290 次原生更新。

#### BeautyMap + AMCL

**现场执行 · Live execution**

![Pure static — BeautyMap: shared native execution](../results/reference/robot-static/execution.gif)

[MP4 · 170202-5abed0](../results/reference/robot-static/execution.mp4)

**结果回放 · Measured result replay**

![Pure static — BeautyMap: beautymap measured replay](../results/reference/robot-static/methods/beautymap/result.gif)

[MP4](../results/reference/robot-static/methods/beautymap/result.mp4) · [record](../results/reference/robot-static/methods/beautymap/record.json) · RMSE **6.55 cm** · 290 次原生更新。

### 运动障碍物

三个运动箱体。动态 A 地图与静态 A 控制组接收同一动态 B 输入。

#### Raw + AMCL

**现场执行 · Live execution**

![Moving obstacles — Raw: shared native execution](../results/reference/robot-dynamic/execution.gif)

[MP4 · 170718-20a6e0](../results/reference/robot-dynamic/execution.mp4)

**结果回放 · Measured result replay — 动态 A 地图**

![Moving obstacles — Raw: raw measured replay](../results/reference/robot-dynamic/methods/raw/result.gif)

[MP4](../results/reference/robot-dynamic/methods/raw/result.mp4) · [record](../results/reference/robot-dynamic/methods/raw/record.json) · RMSE **7.31 cm** · 291 次原生更新。

**结果回放 · Measured result replay — 静态 A 地图控制组**

![Moving obstacles — Raw: clean_raw measured replay](../results/reference/robot-dynamic/methods/clean_raw/result.gif)

[MP4](../results/reference/robot-dynamic/methods/clean_raw/result.mp4) · [record](../results/reference/robot-dynamic/methods/clean_raw/record.json) · RMSE **6.30 cm** · 291 次原生更新。

#### DUFOMap + AMCL

**现场执行 · Live execution**

![Moving obstacles — DUFOMap: shared native execution](../results/reference/robot-dynamic/execution.gif)

[MP4 · 170718-20a6e0](../results/reference/robot-dynamic/execution.mp4)

**结果回放 · Measured result replay — 动态 A 地图**

![Moving obstacles — DUFOMap: dufomap measured replay](../results/reference/robot-dynamic/methods/dufomap/result.gif)

[MP4](../results/reference/robot-dynamic/methods/dufomap/result.mp4) · [record](../results/reference/robot-dynamic/methods/dufomap/record.json) · RMSE **7.10 cm** · 291 次原生更新。

**结果回放 · Measured result replay — 静态 A 地图控制组**

![Moving obstacles — DUFOMap: clean_dufomap measured replay](../results/reference/robot-dynamic/methods/clean_dufomap/result.gif)

[MP4](../results/reference/robot-dynamic/methods/clean_dufomap/result.mp4) · [record](../results/reference/robot-dynamic/methods/clean_dufomap/record.json) · RMSE **6.30 cm** · 291 次原生更新。

#### BeautyMap + AMCL

**现场执行 · Live execution**

![Moving obstacles — BeautyMap: shared native execution](../results/reference/robot-dynamic/execution.gif)

[MP4 · 170718-20a6e0](../results/reference/robot-dynamic/execution.mp4)

**结果回放 · Measured result replay — 动态 A 地图**

![Moving obstacles — BeautyMap: beautymap measured replay](../results/reference/robot-dynamic/methods/beautymap/result.gif)

[MP4](../results/reference/robot-dynamic/methods/beautymap/result.mp4) · [record](../results/reference/robot-dynamic/methods/beautymap/record.json) · RMSE **7.28 cm** · 291 次原生更新。

**结果回放 · Measured result replay — 静态 A 地图控制组**

![Moving obstacles — BeautyMap: clean_beautymap measured replay](../results/reference/robot-dynamic/methods/clean_beautymap/result.gif)

[MP4](../results/reference/robot-dynamic/methods/clean_beautymap/result.mp4) · [record](../results/reference/robot-dynamic/methods/clean_beautymap/record.json) · RMSE **6.89 cm** · 291 次原生更新。

### 持久结构变化

变化后的世界使用旧静态 A 地图；本路线未诱发失效，不能作为恢复成功证据。

#### Raw + AMCL

**现场执行 · Live execution**

![Persistent change — Raw: shared native execution](../results/reference/robot-large-change/execution.gif)

[MP4 · 172452-ca9681](../results/reference/robot-large-change/execution.mp4)

**结果回放 · Measured result replay**

![Persistent change — Raw: raw measured replay](../results/reference/robot-large-change/methods/raw/result.gif)

[MP4](../results/reference/robot-large-change/methods/raw/result.mp4) · [record](../results/reference/robot-large-change/methods/raw/record.json) · RMSE **6.25 cm** · 290 次原生更新。

#### DUFOMap + AMCL

**现场执行 · Live execution**

![Persistent change — DUFOMap: shared native execution](../results/reference/robot-large-change/execution.gif)

[MP4 · 172452-ca9681](../results/reference/robot-large-change/execution.mp4)

**结果回放 · Measured result replay**

![Persistent change — DUFOMap: dufomap measured replay](../results/reference/robot-large-change/methods/dufomap/result.gif)

[MP4](../results/reference/robot-large-change/methods/dufomap/result.mp4) · [record](../results/reference/robot-large-change/methods/dufomap/record.json) · RMSE **6.25 cm** · 290 次原生更新。

#### BeautyMap + AMCL

**现场执行 · Live execution**

![Persistent change — BeautyMap: shared native execution](../results/reference/robot-large-change/execution.gif)

[MP4 · 172452-ca9681](../results/reference/robot-large-change/execution.mp4)

**结果回放 · Measured result replay**

![Persistent change — BeautyMap: beautymap measured replay](../results/reference/robot-large-change/methods/beautymap/result.gif)

[MP4](../results/reference/robot-large-change/methods/beautymap/result.mp4) · [record](../results/reference/robot-large-change/methods/beautymap/record.json) · RMSE **6.16 cm** · 290 次原生更新。

### 走廊退化

X 初值偏移 1 m。完整扫描为 720 束／360°／12 m；受限扫描为 72 束／240°／3.5 m，持续 50 个仿真秒后恢复。恢复后约 11.3 s 开始持续收敛，随后覆盖 5 s 确认。本走廊三种占据地图相同。

#### Raw + AMCL

**现场执行 · Live execution**

![Corridor degradation — Raw: shared native execution](../results/reference/robot-degradation/execution.gif)

[MP4 · 173508-e41e34](../results/reference/robot-degradation/execution.mp4)

**结果回放 · Measured result replay — 完整扫描控制组**

![Corridor degradation — Raw: raw measured replay](../results/reference/robot-degradation/methods/raw/result.gif)

[MP4](../results/reference/robot-degradation/methods/raw/result.mp4) · [record](../results/reference/robot-degradation/methods/raw/record.json) · RMSE **62.64 cm** · 478 次原生更新。

**结果回放 · Measured result replay — 受限→恢复扫描**

![Corridor degradation — Raw: degraded_raw measured replay](../results/reference/robot-degradation/methods/degraded_raw/result.gif)

[MP4](../results/reference/robot-degradation/methods/degraded_raw/result.mp4) · [record](../results/reference/robot-degradation/methods/degraded_raw/record.json) · RMSE **73.63 cm** · 478 次原生更新。

#### DUFOMap + AMCL

**现场执行 · Live execution**

![Corridor degradation — DUFOMap: shared native execution](../results/reference/robot-degradation/execution.gif)

[MP4 · 173508-e41e34](../results/reference/robot-degradation/execution.mp4)

**结果回放 · Measured result replay — 完整扫描控制组**

![Corridor degradation — DUFOMap: dufomap measured replay](../results/reference/robot-degradation/methods/dufomap/result.gif)

[MP4](../results/reference/robot-degradation/methods/dufomap/result.mp4) · [record](../results/reference/robot-degradation/methods/dufomap/record.json) · RMSE **62.64 cm** · 478 次原生更新。

**结果回放 · Measured result replay — 受限→恢复扫描**

![Corridor degradation — DUFOMap: degraded_dufomap measured replay](../results/reference/robot-degradation/methods/degraded_dufomap/result.gif)

[MP4](../results/reference/robot-degradation/methods/degraded_dufomap/result.mp4) · [record](../results/reference/robot-degradation/methods/degraded_dufomap/record.json) · RMSE **73.63 cm** · 478 次原生更新。

#### BeautyMap + AMCL

**现场执行 · Live execution**

![Corridor degradation — BeautyMap: shared native execution](../results/reference/robot-degradation/execution.gif)

[MP4 · 173508-e41e34](../results/reference/robot-degradation/execution.mp4)

**结果回放 · Measured result replay — 完整扫描控制组**

![Corridor degradation — BeautyMap: beautymap measured replay](../results/reference/robot-degradation/methods/beautymap/result.gif)

[MP4](../results/reference/robot-degradation/methods/beautymap/result.mp4) · [record](../results/reference/robot-degradation/methods/beautymap/record.json) · RMSE **62.64 cm** · 478 次原生更新。

**结果回放 · Measured result replay — 受限→恢复扫描**

![Corridor degradation — BeautyMap: degraded_beautymap measured replay](../results/reference/robot-degradation/methods/degraded_beautymap/result.gif)

[MP4](../results/reference/robot-degradation/methods/degraded_beautymap/result.mp4) · [record](../results/reference/robot-degradation/methods/degraded_beautymap/record.json) · RMSE **73.63 cm** · 478 次原生更新。

**实体机器人测试：**静态、动态、退化与持久变化均标明待测，二维／三维层配置见[测试协议](testing/LIVE.zh-CN.md#一键演示与实体测试)。

本机键盘演示与录制脚本：`F:\be2演讲\实机脚本`；[使用说明](../demo/README.md)。

## 方向分析

**SLAM（Simultaneous Localization and Mapping）**在构建地图的同时估计自身运动。大方向包含动态环境下的建图、定位和 SLAM，自恢复是其中的开放问题。

| 成果 | 内容 |
| --- | --- |
| 原库复现 | 作者代码、数据与协议，保留各论文自己的指标及实际复现范围 |
| 机器人测试 | Sim2Real-AlgoBench 三轮全向底盘；原生二维＋独立三维激光版本，逐级测试点云建图、定位与恢复 |
| 问题分析 | 区分约束不足与地图失配，通过失败与恢复对照收窄问题，方法保持开放 |

语义建图方向及早期投影比较保留在[原库](https://github.com/p20030920p/SLAM_Learning)。

## 相关工作

本机作者原库执行及各自结果回放；原始数据与 Gazebo 平台测试分开。下文保留历史论文表证据，本次 LiDAR 分数来自独立评分器，未重新作 PCL 交叉核验。

### DUFOMap — 作者原库复现

KITTI-00，141 帧；最终地图环视，不是在线增长。 [Paper card](papers/dufomap.zh-CN.md) · [record](../results/reference/desktop-dufomap/record.json)

**现场执行 · Live execution**

![DUFOMap native execution](../results/reference/desktop-dufomap/execution.gif)

[MP4](../results/reference/desktop-dufomap/execution.mp4)

**结果回放 · Measured result replay**

![DUFOMap measured result replay](../results/reference/desktop-dufomap/result.gif)

[MP4](../results/reference/desktop-dufomap/result.mp4)

### BeautyMap — 作者原库复现

KITTI-00，141 帧；与历史 KITTI-02 论文表复现不是同一范围。 [Paper card](papers/beautymap.zh-CN.md) · [record](../results/reference/desktop-beautymap/record.json)

**现场执行 · Live execution**

![BeautyMap native execution](../results/reference/desktop-beautymap/execution.gif)

[MP4](../results/reference/desktop-beautymap/execution.mp4)

**结果回放 · Measured result replay**

![BeautyMap measured result replay](../results/reference/desktop-beautymap/result.gif)

[MP4](../results/reference/desktop-beautymap/result.mp4)

### IR-MCL — 作者原库复现

Bonn IPBLab：处理 1543、评分 1354 帧；本轮 5.36 cm／1.06°。 [Paper card](papers/ir-mcl.zh-CN.md) · [record](../results/reference/desktop-ir-mcl/record.json)

**现场执行 · Live execution**

![IR-MCL native execution](../results/reference/desktop-ir-mcl/execution.gif)

[MP4](../results/reference/desktop-ir-mcl/execution.mp4)

**结果回放 · Measured result replay**

![IR-MCL measured result replay](../results/reference/desktop-ir-mcl/result.gif)

[MP4](../results/reference/desktop-ir-mcl/result.mp4)

### AdaM-MCL — 作者原库复现

自建 128 格地图、已有 2432 步权重；本轮 123 次更新×1 试验，RMSE 32.23 格；不与论文值数值对照。 [Paper card](papers/adam-mcl.zh-CN.md) · [record](../results/reference/desktop-adam-mcl/record.json)

**现场执行 · Live execution**

![AdaM-MCL native execution](../results/reference/desktop-adam-mcl/execution.gif)

[MP4](../results/reference/desktop-adam-mcl/execution.mp4)

**结果回放 · Measured result replay**

![AdaM-MCL measured result replay](../results/reference/desktop-adam-mcl/result.gif)

[MP4](../results/reference/desktop-adam-mcl/result.mp4)

AdaM-MCL 终端看板末尾含旧统计公式错误；当前指标从作者保存的距离日志重算，后续演示包装器的末尾公式已修正。[指标勘误](../results/reference/adam-mcl/ERRATUM.md)。

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

**未做数值对照。** 论文的 20 张仿真地图为 43 m × 43 m，另有 6 条评测序列与已发布权重，全部是外部下载；本次用自建平面，训练 **2432** 次优化步而作者默认 **2 880 000** 步，格不是米。本次实测（单位：格）：10 次重复的每次运行 RMSE 均值 34.82，末帧误差均值 47.71，每次更新 0.43 s，10 次重复中 0 次满足折算到本平面的论文收敛判据。 [指标勘误](../results/reference/adam-mcl/ERRATUM.md)。

## 假设

待检验：地图更干净是否也更容易恢复，更好的正常观测模型是否扩大恢复范围，剩余稳定结构怎样限制地图过期后的恢复。先完成原库复现与逐级测试，再根据可重复失败选择恢复策略。[分析与反例](self-recovery/DESIGN.zh-CN.md)。

## 分支

| 分支 | 用途 |
| --- | --- |
| main | 提交展示：动态环境鲁棒定位主线、按范围记录的建图／定位复现，以及候选自恢复实验。 |
| [reproduce/author-originals](https://github.com/p20030920p/SLAM_Learning/tree/reproduce/author-originals) | 作者原流程、论文表格评分与录制。 |
| [notes/personal-study-guide-20261008](https://github.com/p20030920p/SLAM_Learning/tree/notes/personal-study-guide-20261008) | 个人学习笔记与 `src/physical/` 实物实验，保留操作说明和失败记录。 |


[AI 使用](guides/DISCLOSURE.zh-CN.md) · [来源／许可](guides/ATTRIBUTION.zh-CN.md) · [引用](CITATION.cff) · [许可](../src/LICENSE)
