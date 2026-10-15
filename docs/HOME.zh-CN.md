<div align="center">

# SLAM Learning

**动态环境中的鲁棒定位与 SLAM**

动态残影清理 · 静态结构保留 · 下游定位检验

[![CPU reproducibility](https://github.com/p20030920p/slam_learning_updated/actions/workflows/ci.yml/badge.svg)](https://github.com/p20030920p/slam_learning_updated/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.10-3776AB)](../src/pyproject.toml)

[English](../README.md) | 中文 | [**Minimal English · Practice**](MINIMAL.md) | [**极简中文 · 实践**](MINIMAL.zh-CN.md)

[开放问题](#开放问题) · [方向分析](#方向分析) · [相关工作](#相关工作) · [指标](#指标)

[实践](#实践) · [假设](#假设) · [假设检验实验](#假设检验实验) · [实机实验](#实机实验) · [分支](#分支)

</div>

## 开放问题

**大方向：变化环境中的可靠建图与定位。** 原来的“退化与大变动下定位自恢复”适合作为长期方向，但同时跨越建图、配准、重定位和多传感器融合，对当前论文与实验过于开放。

**本轮小问题：在给定多帧扫描和建图位姿的条件下，如何删除动态障碍物残影，同时保留静态结构；这种地图改善在什么污染和几何条件下，能够降低独立定位的误差？** 先验证地图，再检验定位；不把“地图更干净”直接写成“保证定位准确”。[问题边界与论文依据](testing/MAPPING-FOCUS.zh-CN.md) · [原自恢复背景](self-recovery/DESIGN.zh-CN.md)。

## 方向分析

**SLAM**同时估计运动和地图。本轮控制建图位姿与定位器，把干预放在地图层；动态清理、持久变化更新、走廊几何退化分开讨论。IRMCL／AdaM-MCL属于定位参照，不作为动态建图方法。

![SLAM 位姿与地图估计及恢复：实体底盘与传感器、Gazebo 扫描、给定位姿地图与走廊](assets/slam-recovery-flow.zh-CN.v2.png)

当前研究主线是**动态残影删除→静态约束保留→独立定位检验**。上图保留为此前定位自恢复方向的背景图，不代表本轮聚焦后的研究框架。[原可编辑图](assets/slam-recovery-flow.zh-CN.v2.pptx) · [图像来源](assets/direction/sources.json)。照片为已有器材，实体实验待测。

| 成果 | 内容 |
| --- | --- |
| 原库复现 | 作者代码、数据与协议，保留各论文自己的指标及实际复现范围 |
| 机器人测试 | Sim2Real-AlgoBench 三轮全向底盘；原生二维＋独立三维激光版本，逐级测试点云建图、定位与恢复 |
| 问题分析 | 区分约束不足与地图失配，通过失败与恢复对照收窄问题，方法保持开放 |

语义建图方向及早期投影比较保留在[原库](https://github.com/p20030920p/SLAM_Learning)。

## 相关工作

**作者原库现场执行：RViz＋终端。**显示器观察当前计算状态，仅在可视化时稀疏展示点／粒子；观察器开销不作论文运行时间对比。

最新原库运行；数据范围与失效分析见各论文条目。SA为静态点保留率，DA为动态点删除率。

| 方法 | 地图类型 | 指标效果 |
| --- | --- | --- |
| DUFOMap | 三维去动态点地图 | SA 97.98% / DA 98.70%；清理有效 |
| BeautyMap | 三维离线清理地图 | SA 96.95% / DA 98.34%；清理有效 |
| IR-MCL | 神经占据场 | RMSE 5.31 cm / 1.07°；Seq 1定位有效 |
| AdaM-MCL | 自建128格栅格图 | RMSE 32.23格；历史持续收敛0/10 |
| srrg_mapper2d | 原生二维点图（Gazebo） | 动态残影删除42.31% / 静态覆盖保留99.51% |

### DUFOMap — 在地图积分过程中去除动态点

**输入：**连续三维激光扫描与给定传感器位姿。**处理：**用扫描实际观测到的空闲空间判断过去的占据点是否为动态残留；八叉树累积证据，并为位姿不确定性留出裕量。**输出：**去除动态残留的点云地图。它本身不估计机器人位姿。[论文与复现范围](papers/dufomap.zh-CN.md)。

录像中灰色是保留点、红色是移除点、青色是当前扫描。重点看后续扫描如何改变旧点的保留决策。KITTI-00，141 帧；SA 97.98%／DA 98.70%。SA 是静态点保留率，DA 是动态点删除率，都不是定位误差。

**现场执行 · Live execution**

![DUFOMap author-code live execution](../results/reference/desktop-live-dufomap/execution.gif)

[Live MP4](../results/reference/desktop-live-dufomap/execution.mp4) · [record](../results/reference/desktop-live-dufomap/record.json)

### BeautyMap — 清理已有点云地图

**输入：**完整累积三维地图、扫描与给定位姿。**处理：**作者占据表示检测不一致结构，再通过静态结构恢复步骤减少误删。**输出：**清理后的参考地图。这是离线地图清理，录像展示它正在计算，开始时完整输入地图已经存在。[论文与复现范围](papers/beautymap.zh-CN.md)。

灰色／红色分别表示保留／移除。重点看累计移除决策，不把初始完整地图理解成在线 SLAM 的建图结果。KITTI-00，141 帧；SA 96.95%／DA 98.34%。更干净的地图是否改善定位，需要另做下游测试。

**现场执行 · Live execution**

![BeautyMap author-code live execution](../results/reference/desktop-live-beautymap/execution.gif)

[Live MP4](../results/reference/desktop-live-beautymap/execution.mp4) · [record](../results/reference/desktop-live-beautymap/record.json)

### IR-MCL — 用神经观测模型定位

**输入：**预训练神经占据场、真实二维扫描与运动输入。**处理：**每个粒子代表一个候选机器人位姿；神经场在该位姿渲染预测扫描，与真实扫描比较后更新权重，再重采样。**输出：**估计位姿与粒子分布。[论文、原库与评分协议](papers/ir-mcl.zh-CN.md)。

RViz 中地图提供环境参照，黄色粒子是候选位置，蓝色是显示估计，绿色是真值轨迹。重点看粒子是否集中，以及估计是否贴近参照。显示用加权粒子均值，评分用原生保存轨迹。Bonn IPBLab Seq 1：处理 1543／评分 1354 帧，本次 RMSE 5.31 cm／1.07°。这次作者数据运行与接入 Gazebo 是两项不同实验。

**现场执行 · Live execution**

![IR-MCL author-code live execution](../results/reference/desktop-live-ir-mcl/execution.gif)

[Live MP4](../results/reference/desktop-live-ir-mcl/execution.mp4) · [record](../results/reference/desktop-live-ir-mcl/record.json)

### AdaM-MCL — 学习式候选位置与粒子跟踪混合

**输入：**地图、激光观测、运动输入与训练好的候选位姿模型。**处理：**学习模型提出候选位置，自适应混合机制将其与常规粒子跟踪结合。**输出：**位姿分布，可包含绑架事件后的新位置假设。[论文与范围限制](papers/adam-mcl.zh-CN.md)。

当前使用自建 128 格地图、2432 步权重，123 次滤波更新，RMSE 32.23 格。未获取论文发布数据与权重，因此这是受限原库流程执行；没有复现论文的米制精度，也没有证明成功自恢复。[评分更正](../results/reference/adam-mcl/ERRATUM.md)。

**现场执行 · Live execution**

![AdaM-MCL author-code live execution](../results/reference/desktop-adam-mcl/execution.gif)

[Live MP4](../results/reference/desktop-adam-mcl/execution.mp4) · [record](../results/reference/desktop-adam-mcl/record.json)

**保存结果回放**

![AdaM-MCL saved result replay](../results/reference/desktop-adam-mcl/result.gif)

[Result MP4](../results/reference/desktop-adam-mcl/result.mp4)

<!-- SRRG_RELATED -->
### srrg_mapper2d · 原生二维动态残影维护

[IROS 2018 论文](https://iris.uniroma1.it/handle/11573/1340118) · [作者建图库](https://gitlab.com/srrg-software/srrg_mapper2d) · [ROS入口](https://gitlab.com/srrg-software/srrg_mapper2d_ros) · [merger2d.cpp](https://gitlab.com/srrg-software/srrg_scan_matcher/-/blob/master/src/merger2d.cpp)。

原文针对连续二维点云的长期动态环境建图，使用 LCAS–STRANDS 与 MIT Stata Center；动态处理嵌在多帧配准／合并和图维护中。已编译并完成本机同四场景录制。

[2D 实践：视频与指标](#srrg-2d) · [失败诊断](#srrg-diagnostics) · [原文适用条件](papers/srrg_mapper2d.zh-CN.md)

<!-- /SRRG_RELATED -->

## 指标

### 地图清理指标 · SA / DA / AA / HA

**共用指标。** DUFOMap 和 BeautyMap 的 SA、DA 定义相同。$S,D$ 为真值中的静态／动态点数；$S_k,D_r$ 为正确保留的静态点数／正确剔除的动态点数。AA（DUFOMap）为几何平均，HA（BeautyMap）为调和平均。[DUFOMap 定义](https://arxiv.org/html/2403.01449v1#S4.SS2) · [BeautyMap 定义](https://arxiv.org/html/2405.07283v1#S4)。

$$
\begin{aligned}
\mathrm{SA} &= 100\frac{S_k}{S}, &
\mathrm{DA} &= 100\frac{D_r}{D},\\
\mathrm{AA} &= \sqrt{\mathrm{SA}\,\mathrm{DA}}, &
\mathrm{HA} &= \frac{2\,\mathrm{SA}\,\mathrm{DA}}{\mathrm{SA}+\mathrm{DA}}.
\end{aligned}
$$

### 实测结果如何计算

每条原生定位输出按时间与独立 Gazebo 机器人真值关联，最近时间差必须 **≤0.05 个仿真秒**。二者使用相同地图／世界坐标，不做空间拟合；评分包含初始化阶段，并记录时间不匹配的丢弃数量。

$$e_i=\sqrt{(\hat x_i-x_i)^2+(\hat y_i-y_i)^2},\quad \mathrm{RMSE}_{xy}=\sqrt{\frac1N\sum_{i=1}^N e_i^2}.$$

三维GICP使用完整三维地图和点云，读取`*-poses3d.csv`的原生XYZ输出，按相同≤0.05s同步规则计算下式。缺失输出不补零；须同时检查有效数量、首末时间及共同覆盖。走廊三方法输出覆盖不同，不能直接用整段RMSE排名。地图动态删除／静态保留是另一组指标。

$$e_{i,xyz}=\sqrt{(\hat x_i-x_i)^2+(\hat y_i-y_i)^2+(\hat z_i-z_i)^2},\quad \mathrm{RMSE}_{xyz}=100\sqrt{\frac1N\sum_{i=1}^N e_{i,xyz}^2}\;\text{cm}.$$

偏航差先折回 $[-\pi,\pi]$，再求均方根并转换成度；米乘 100 得到厘米。**Live execution** 是按真实时间录制的现场计算；**Measured result replay** 按仿真时间绘制已保存估计与真值，不重新运行算法。曲线显示每时刻误差，RMSE 标注来自完整评分 CSV。[CSV、窗口与恢复判据](testing/LIVE.zh-CN.md) · [可执行评分代码](../src/scripts/presentation/observe_session.py)。

### 复现结果

| 工作 | 数据 | 结果 |
| --- | --- | --- |
| [DUFOMap](https://github.com/p20030920p/SLAM_Learning/blob/535a2780af7ca7eb3aa02f722e1340fe90bc2dcf/docs/DUFOMAP_TABLE4.zh-CN.md) | KITTI-00，141 扫描 | 表 IV 准确率匹配 |
| [BeautyMap](https://github.com/p20030920p/SLAM_Learning/blob/535a2780af7ca7eb3aa02f722e1340fe90bc2dcf/docs/KITTI_PAPER_PROTOCOL.zh-CN.md) | 历史 KITTI-02，91 扫描 | 表 III 准确率匹配 |
| [IR-MCL](papers/ir-mcl.zh-CN.md) | 波恩 IPBLab，公开定位序列，1543 扫描 | 位置 RMSE 5.32 cm，论文 5.13 cm |
| [AdaM-MCL](papers/adam-mcl.zh-CN.md) | 自建 128 格平面，一个留出场景，123 次更新 × 10 次重复 | 上游流程跑通；未与论文数值对照 |

### 实验证据

以下数值取自作者源库链接的论文及我们保存的作者代码运行结果。每张表仅对照同一种方法，不作跨方法排名。

#### DUFOMap

KITTI-00，141 扫描公开数据；完整设置：体素 0.1 m、d_s=0.2 m、d_p=1。[作者源库](https://github.com/KTH-RPL/dufomap/tree/9e239ddd5995136e14f5212f33382a6ebc59e518) · [论文表 IV](https://arxiv.org/html/2403.01449v1#S5.T4) · [我们的结果](https://github.com/p20030920p/SLAM_Learning/blob/535a2780af7ca7eb3aa02f722e1340fe90bc2dcf/docs/DUFOMAP_TABLE4.zh-CN.md)。

| 指标 | 论文 % | 复现 % |
| --- | ---: | ---: |
| SA | 97.96 | 97.9635 |
| DA | 98.72 | 98.7196 |
| AA | 98.34 | 98.3408 |

完整设置的三项数值保留两位小数后均与论文一致。表 IV 五组设置共 15 项准确率均匹配；本表不包含运行时间和在线实验。

#### BeautyMap

历史 KITTI-02，第 860–950 帧，共 91 扫描；XY=1 m、Z=0.5 m、范围 40 m。[作者源库](https://github.com/MKJia/BeautyMap/tree/98bce4a97db96ddd0d5342e31425c7679f58ba2e) · [论文表 III](https://arxiv.org/html/2405.07283v1#S4.T3) · [我们的结果](https://github.com/p20030920p/SLAM_Learning/blob/535a2780af7ca7eb3aa02f722e1340fe90bc2dcf/docs/KITTI_PAPER_PROTOCOL.zh-CN.md)。

| 指标 | 论文 % | 复现 % |
| --- | ---: | ---: |
| SA | 83.40 | 83.3978 |
| DA | 82.41 | 82.4092 |
| HA | 82.90 | 82.9006 |

三项数值保留两位小数后均一致。XY=0.5／1／2 m 的九项准确率全部匹配。使用历史预处理／GT 与作者 HA 评分器；论文当时的精确方法提交尚未确定。其他序列及运行时间不在本表范围内。

#### IR-MCL

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

#### AdaM-MCL

自建 128 格室内平面、一个留出场景、123 次滤波更新、200 个粒子、$T_{\mathrm{cut}}=0.6$——粒子数与信赖阈值取自论文的仿真设置。[作者源库](https://github.com/Runjian-Chen/AdaM_MCL/tree/e8aedd2bae03816aabd5300e5ca2fe181b39d830) · [论文表 II](https://arxiv.org/html/2009.00211v3) · [我们的运行](../results/reference/adam-mcl/runs/adam-mcl-wsl/record.json)。

| 指标 | 论文表 II | 本次复现 |
| --- | ---: | ---: |
| 全局定位 $E_{pos}$ | 0.153 m | 未做数值对照 |
| 绑架 $E_{pos}$ | 0.128 m | 未做数值对照 |

**未做数值对照。** 论文的 20 张仿真地图为 43 m × 43 m，另有 6 条评测序列与已发布权重，全部是外部下载；本次用自建平面，训练 **2432** 次优化步而作者默认 **2 880 000** 步，格不是米。本次实测（单位：格）：10 次重复的每次运行 RMSE 均值 34.82，末帧误差均值 47.71，每次更新 0.43 s，10 次重复中 0 次满足折算到本平面的论文收敛判据。 [指标勘误](../results/reference/adam-mcl/ERRATUM.md)。

## 实践

[极简实践：GIF预览与视频](MINIMAL.zh-CN.md)

[键盘演示](../demo/README.md) · [视频目录](../demo/gallery.html) · [代码 Notebook](../notebooks/presentation/SLAM_实验逐步展示.ipynb)。

### 实践目录

<a id="practice-index"></a>

| 场景 | 2D · AMCL | 3D · GICP |
| --- | --- | --- |
| 纯静态 | [SRRG建图](#srrg-static-2d) / [旧投影定位](#scene-static-2d) | [查看录像](#scene-static-3d) |
| 运动障碍物 | [SRRG建图](#srrg-dynamic-2d) / [旧投影定位](#scene-dynamic-2d) | [查看录像](#scene-dynamic-3d) |
| 持久结构变化 | [SRRG建图](#srrg-large-change-2d) / [旧投影定位](#scene-change-2d) | [查看录像](#scene-change-3d) |
| 走廊退化 | [SRRG建图](#srrg-corridor-2d) / [旧投影定位](#scene-corridor-2d) | [查看录像](#scene-corridor-3d) |

[三维地图清理结果](#map-review-3d) · [开放问题：假设与新实验](#hypothesis-experiments)

[仿真设置](#仿真设置--传感器与小车结构参数) · [原生二维建图 · SRRG](#srrg-2d) · [2D · AMCL](#2d--amcl) · [3D · GICP](#3d--gicp) · [二维定位录制](#二维定位录制) · [三维地图清理与定位录制](#三维地图清理与定位录制) · [此前Raw单地图三维静态试验](#此前raw单地图三维静态试验) · [补充场景实时录制](#补充场景实时录制)

**地图清理主指标：动态障碍物删除率、静态障碍物保留率，越高越好。** 旧二维投影按5cm唯一格评分；新SRRG按10cm观测支持、15cm覆盖容差评分；三维评分源点。口径不同不排名。静态／走廊无动态样本，删除率记N/A；持久变化旧图仅评分静态A，未测试B在线更新。定位RMSE另列，不能代替地图清理效果。原二维DUFOMap／BeautyMap投影保留为跨维参考；新增原生二维SRRG见下方。

<a id="仿真雷达与小车结构参数"></a>

### 仿真设置 · 传感器与小车结构参数

| 项目 | 实际设置 |
| --- | --- |
| 平台 | Sim2Real全向底盘；ROS 2 Jazzy＋Gazebo Harmonic；理想仿真传感器，实体测试待做 |
| 底盘结构 | 三个全向轮，间隔120°；轮半径0.06364 m；轮心到车体中心0.1934 m；碰撞圆柱半径0.20 m、高0.14 m |
| 质量／接触 | base_link为0.953513 kg，每轮0.20 kg；滚子以球形接触和方向摩擦近似，μ=0.02／2.0 |
| 二维雷达 | 通用gpu_lidar，720束、360°、10 Hz、0.08–12 m；相对base_link安装位置(0.06, 0, 0.16) m |
| 三维雷达 | 通用gpu_lidar，水平720×垂直16束、360°×30°（±15°）、10 Hz、0.08–12 m；安装位置(0, 0, 0.30) m |
| RGB相机 | 640×480、15 Hz、水平视场80°；安装位置(0.18, 0, 0.12) m |
| 深度假设组 | 实际渲染depth_camera：320×240、10 Hz、水平80°、0.25–4 m；未加实体噪声模型；原生二维／SRRG组移除三维雷达 |
| 地图表示 | 三维源点；旧二维投影为0.05 m格、世界Z=0.12–1.20 m、一格占据膨胀；SRRG使用独立的原生二维地图及覆盖容差 |

[实际机器人URDF](../config/robot_profiles/omni-3d-v1/omni_car_lidar3d.urdf) · [深度相机和传感器分组](../src/scripts/presentation/probe_sensors.py) · [地图投影](../src/scripts/presentation/build_maps.py)。安装位置相对base_link，不能当作离地高度；仿真16线雷达没有指定商用型号。

<!-- SRRG_PRACTICE -->
<a id="srrg-2d"></a>

### 原生二维建图 · srrg_mapper2d

[↑ 实践目录](#practice-index)

本组实际使用二维雷达和轮式里程计，无三维雷达、无真值配准。调用作者完整Mapper2D配准与位姿图；主组按作者默认关闭图合并，局部投影融合开启。图合并开启的数值失败单独保留。

指标：10cm唯一观测支持、15cm覆盖容差；只对后来实测射线确认为空的历史动态位置计算删除率，排除当前动态物体。原始图按各帧当时估计累计，SRRG还进行图优化，属于端到端维护对照。百分数不可与三维精确点保留率直接排名。

<a id="srrg-static-2d"></a>

#### 纯静态 · 2D

| 方法 | 地图类型 | 指标效果 |
| --- | --- | --- |
| Raw | 原生二维点图 | 动态残影删除 N/A；静态覆盖保留 100.00% |
| srrg_mapper2d | 原生二维点图 | 动态残影删除 N/A；静态覆盖保留 99.84% |

建图轨迹XY RMSE（非固定地图定位B）: 0.71 cm.

本轮未记录作者跟踪器重置或持续20cm定位预警；不能据此保证所有地图几何无误。

![SRRG Pure static actual native mapping](../results/reference/srrg-2d-static/execution.gif)

[MP4](../results/reference/srrg-2d-static/execution.mp4) · [record](../results/reference/srrg-2d-static/record.json)

<a id="srrg-dynamic-2d"></a>

#### 运动障碍物 · 2D

| 方法 | 地图类型 | 指标效果 |
| --- | --- | --- |
| Raw | 原生二维点图 | 动态残影删除 0.00%；静态覆盖保留 100.00% |
| srrg_mapper2d | 原生二维点图 | 动态残影删除 42.31%；静态覆盖保留 99.51% |

建图轨迹XY RMSE（非固定地图定位B）: 0.64 cm.

本轮未记录作者跟踪器重置或持续20cm定位预警；不能据此保证所有地图几何无误。

![SRRG Moving obstacles actual native mapping](../results/reference/srrg-2d-dynamic/execution.gif)

[MP4](../results/reference/srrg-2d-dynamic/execution.mp4) · [record](../results/reference/srrg-2d-dynamic/record.json)

<a id="srrg-large-change-2d"></a>

#### 持久结构变化 · 2D

| 方法 | 地图类型 | 指标效果 |
| --- | --- | --- |
| Raw | 原生二维点图 | 动态残影删除 N/A；静态覆盖保留 100.00% |
| srrg_mapper2d | 原生二维点图 | 动态残影删除 N/A；静态覆盖保留 99.71% |

建图轨迹XY RMSE（非固定地图定位B）: 0.46 cm.

实际加载静态A旧图，已知会话起点，调用作者多会话入口更新。该短路线不能覆盖论文的长期多会话结论。

当前可见新增结构覆盖保留 98.90%（91个观测格）；本场景只增加结构，没有旧结构被搬走，动态删除率为N/A。

本轮未记录作者跟踪器重置或持续20cm定位预警；不能据此保证所有地图几何无误。

![SRRG Persistent change actual native mapping](../results/reference/srrg-2d-large-change/execution.gif)

[MP4](../results/reference/srrg-2d-large-change/execution.mp4) · [record](../results/reference/srrg-2d-large-change/record.json)

<a id="srrg-corridor-2d"></a>

#### 走廊退化 · 2D

| 方法 | 地图类型 | 指标效果 |
| --- | --- | --- |
| Raw | 原生二维点图 | 动态残影删除 N/A；静态覆盖保留 83.43% |
| srrg_mapper2d | 原生二维点图 | 动态残影删除 N/A；静态覆盖保留 82.24% |

建图轨迹XY RMSE（非固定地图定位B）: 83.23 cm.

前50个录制仿真秒限制72束／3.5m；保留720角度格，其余无效，随后恢复。

| 事件 | 仿真秒 | 视频定位（约） |
| --- | --- | --- |
| 建图跟踪重置 | 11.1 | [4.6s](../results/reference/srrg-2d-corridor/execution.mp4#t=4.6) |
| 观测受限 | 7.5 | [2.7s](../results/reference/srrg-2d-corridor/execution.mp4#t=2.7) |
| 观测恢复 | 57.6 | [50.9s](../results/reference/srrg-2d-corridor/execution.mp4#t=50.9) |
| 定位偏差持续超过20cm | 11.5 | [5.0s](../results/reference/srrg-2d-corridor/execution.mp4#t=5.0) |

![SRRG Corridor degradation actual native mapping](../results/reference/srrg-2d-corridor/execution.gif)

[MP4](../results/reference/srrg-2d-corridor/execution.mp4) · [record](../results/reference/srrg-2d-corridor/record.json)

<a id="srrg-diagnostics"></a>

#### 保留的失败诊断

| 视频 | 结果 |
| --- | --- |
| [GIF](../results/reference/srrg-diagnostic-20261015-025711-mapping-srrg-static-dd423d/execution.gif) · [MP4](../results/reference/srrg-diagnostic-20261015-025711-mapping-srrg-static-dd423d/execution.mp4) · [record](../results/reference/srrg-diagnostic-20261015-025711-mapping-srrg-static-dd423d/record.json) | 联调失败：Eigen ABI不一致（首次运动） |
| [GIF](../results/reference/srrg-diagnostic-20261015-030327-mapping-srrg-static-a275d3/execution.gif) · [MP4](../results/reference/srrg-diagnostic-20261015-030327-mapping-srrg-static-a275d3/execution.mp4) · [record](../results/reference/srrg-diagnostic-20261015-030327-mapping-srrg-static-a275d3/record.json) | 联调失败：作者stdout诊断污染传输；已隔离 |
| [GIF](../results/reference/srrg-diagnostic-20261015-030729-mapping-srrg-dynamic-14123d/execution.gif) · [MP4](../results/reference/srrg-diagnostic-20261015-030729-mapping-srrg-dynamic-14123d/execution.mp4) · [record](../results/reference/srrg-diagnostic-20261015-030729-mapping-srrg-dynamic-14123d/record.json) | 图合并开启：最后成功输出仿真66.0s／录制55.4s，随后g2o数值分解失败并崩溃；不是动态清理率为零。 |

[原文数据与适用性](papers/srrg_mapper2d.zh-CN.md) · [指标与退化时间说明](testing/MAP-METRICS.zh-CN.md)
<!-- /SRRG_PRACTICE -->

### 2D · AMCL

**[纯静态](#scene-static-2d)** · [record](../results/reference/robot-live-static/record.json)

| 方法 | 地图类型 | 指标效果 |
| --- | --- | --- |
| Raw | 原始二维投影图 | 动态格删除 N/A；静态格保留 100.00% |
| DUFOMap | 去动态点二维投影图 | 动态格删除 N/A；静态格保留 100.00% |
| BeautyMap | 离线清理二维投影图 | 动态格删除 N/A；静态格保留 96.51% |

定位另列 (XY RMSE, cm): Raw 7.28 / DUFOMap 7.28 / BeautyMap 6.89.

Raw与DUFOMap投影相同；BeautyMap本次低0.39 cm，未测试恢复。

**[运动障碍物](#scene-dynamic-2d)** · [record](../results/reference/robot-2d-dynamic-matched/record.json)

| 方法 | 地图类型 | 指标效果 |
| --- | --- | --- |
| Raw | 原始二维投影图 | 动态格删除 0.00%；静态格保留 100.00% |
| DUFOMap | 去动态点二维投影图 | 动态格删除 8.33%；静态格保留 100.00% |
| BeautyMap | 离线清理二维投影图 | 动态格删除 33.33%；静态格保留 96.64% |

定位另列 (XY RMSE, cm): Raw 7.52 / DUFOMap 8.19 / BeautyMap 7.29.

新建图A配对结果：DUFOMap高0.67 cm，BeautyMap低0.23 cm；单次结果无稳定排名，旧一轮结果保留。

**[持久结构变化](#scene-change-2d)** · [record](../results/reference/robot-live-large-change/record.json)

| 方法 | 地图类型 | 指标效果 |
| --- | --- | --- |
| Raw | 原始二维投影图 | 动态格删除 N/A；静态格保留 100.00%（静态A旧图） |
| DUFOMap | 去动态点二维投影图 | 动态格删除 N/A；静态格保留 100.00%（静态A旧图） |
| BeautyMap | 离线清理二维投影图 | 动态格删除 N/A；静态格保留 96.51%（静态A旧图） |

定位另列 (XY RMSE, cm): Raw 6.84 / DUFOMap 6.84 / BeautyMap 6.39.

旧图定位；未调用在线地图更新，本路线未诱发失效。

**[走廊退化](#scene-corridor-2d)** · [record](../results/reference/robot-corridor-v2/record.json)

| 方法 | 地图类型 | 指标效果 |
| --- | --- | --- |
| Raw | 原始二维投影图 | 动态格删除 N/A；静态格保留 100.00% |
| DUFOMap | 去动态点二维投影图 | 动态格删除 N/A；静态格保留 100.00% |
| BeautyMap | 离线清理二维投影图 | 动态格删除 N/A；静态格保留 100.00% |

定位另列 (XY RMSE, cm): Raw 72.53 / DUFOMap 72.53 / BeautyMap 72.53.

三张投影图相同；13.3 s是初始信念偏移纠正，不能区分清理效果。

### 3D · GICP

**[纯静态](#scene-static-3d)** · [record](../results/reference/robot-3d-static/record.json)

| 方法 | 地图类型 | 指标效果 |
| --- | --- | --- |
| Raw | 原始三维点云图 | 动态点删除 N/A；静态点保留 100.00% |
| DUFOMap | 三维去动态点图 | 动态点删除 N/A；静态点保留 100.00% |
| BeautyMap | 三维离线清理图 | 动态点删除 N/A；静态点保留 83.33% |

定位另列 (XYZ RMSE, cm): Raw 0.95 / DUFOMap 0.99 / BeautyMap 1.07.

无动态污染需要清理，本次三维定位未见改善。

**[运动障碍物](#scene-dynamic-3d)** · [record](../results/reference/robot-3d-dynamic/record.json)

| 方法 | 地图类型 | 指标效果 |
| --- | --- | --- |
| Raw | 原始三维点云图 | 动态点删除 0.00%；静态点保留 100.00% |
| DUFOMap | 三维去动态点图 | 动态点删除 46.59%；静态点保留 100.00% |
| BeautyMap | 三维离线清理图 | 动态点删除 74.36%；静态点保留 81.15% |

定位另列 (XYZ RMSE, cm): Raw 0.98 / DUFOMap 0.98 / BeautyMap 1.04.

三维清理确实去除了动态点，但GICP定位仍未见明显收益。

**[持久结构变化](#scene-change-3d)** · [record](../results/reference/robot-3d-large-change/record.json)

| 方法 | 地图类型 | 指标效果 |
| --- | --- | --- |
| Raw | 原始三维点云图 | 动态点删除 N/A；静态点保留 100.00%（静态A旧图） |
| DUFOMap | 三维去动态点图 | 动态点删除 N/A；静态点保留 100.00%（静态A旧图） |
| BeautyMap | 三维离线清理图 | 动态点删除 N/A；静态点保留 83.33%（静态A旧图） |

定位另列 (XYZ RMSE, cm): Raw 0.93 / DUFOMap 1.01 / BeautyMap 1.04.

复用静态三维旧图；未执行变化检测或更新，未见定位改善。

**[走廊退化](#scene-corridor-3d)** · [record](../results/reference/robot-3d-corridor/record.json)

| 方法 | 地图类型 | 指标效果 |
| --- | --- | --- |
| Raw | 原始三维点云图 | 动态点删除 N/A；静态点保留 100.00% |
| DUFOMap | 三维去动态点图 | 动态点删除 N/A；静态点保留 100.00% |
| BeautyMap | 三维离线清理图 | 动态点删除 N/A；静态点保留 99.90% |

定位另列 (XYZ RMSE, cm): Raw 474.38 / DUFOMap 497.05 / BeautyMap 592.00.

Raw与DUFOMap三维图字节相同却得到不同结果；有效输出覆盖不同，不能据此排名。

[原因分析、点级地图质量与参数排查](testing/MAP-2D-3D.zh-CN.md) · [2D／3D独立视频目录](../demo/gallery.html)

### 二维定位录制

**2026-10-14 本机重新实测。**每种方法都有自己的真实 RViz 窗口、地图主题、原生 AMCL 位姿／粒子和独立显示 TF；每段 GIF 录制 Gazebo＋该方法 RViz＋终端，使用同一次场景的实时输入。

**Raw／DUFOMap／BeautyMap 表示地图处理方式，实时定位器统一为 AMCL。**建图使用给定位姿并作共用二维投影，属于三维地图到二维定位的平台适配。下面的数值来自本次新运行，含初始化；每条件一次。

[计算口径与控制组](testing/LIVE.zh-CN.md) · [录像名称对照](../demo/recording-index.json) · [逐方法一键演示](../demo/README.md#逐方法独立-rviz-现场对照)

<a id="scene-static-2d"></a>

#### 纯静态

<!-- MAP_QUALITY_VIDEO_TABLE -->
| 方法 | 地图类型 | 指标效果 |
| --- | --- | --- |
| Raw | 2D | 动态格删除 N/A；静态格保留 100.00% |
| DUFOMap | 2D | 动态格删除 N/A；静态格保留 100.00% |
| BeautyMap | 2D | 动态格删除 N/A；静态格保留 96.51% |
<!-- /MAP_QUALITY_VIDEO_TABLE -->

[↑ 返回目录](#practice-index)

定位器：AMCL；每组290次更新，位置RMSE含初始化。

本路线未诱发定位失效，恢复能力未验证。

##### Raw map + AMCL

**现场执行 · Live execution — Raw RViz**

![Pure static: actual Raw RViz live execution](../results/reference/robot-live-static/executions/raw.gif)

[Live MP4](../results/reference/robot-live-static/executions/raw.mp4) · [RViz config](../results/reference/robot-live-static/view-raw.rviz) · [record](../results/reference/robot-live-static/record.json)

**结果回放 · Measured result replay — Raw**

![Pure static: Raw measured replay from this new run](../results/reference/robot-live-static/methods/raw/result.gif)

[Result MP4](../results/reference/robot-live-static/methods/raw/result.mp4) · [case record](../results/reference/robot-live-static/methods/raw/record.json) · RMSE **7.28 cm** · 290 次原生更新。

##### DUFOMap map + AMCL

**现场执行 · Live execution — DUFOMap RViz**

![Pure static: actual DUFOMap RViz live execution](../results/reference/robot-live-static/executions/dufomap.gif)

[Live MP4](../results/reference/robot-live-static/executions/dufomap.mp4) · [RViz config](../results/reference/robot-live-static/view-dufomap.rviz) · [record](../results/reference/robot-live-static/record.json)

**结果回放 · Measured result replay — DUFOMap**

![Pure static: DUFOMap measured replay from this new run](../results/reference/robot-live-static/methods/dufomap/result.gif)

[Result MP4](../results/reference/robot-live-static/methods/dufomap/result.mp4) · [case record](../results/reference/robot-live-static/methods/dufomap/record.json) · RMSE **7.28 cm** · 290 次原生更新。

##### BeautyMap map + AMCL

**现场执行 · Live execution — BeautyMap RViz**

![Pure static: actual BeautyMap RViz live execution](../results/reference/robot-live-static/executions/beautymap.gif)

[Live MP4](../results/reference/robot-live-static/executions/beautymap.mp4) · [RViz config](../results/reference/robot-live-static/view-beautymap.rviz) · [record](../results/reference/robot-live-static/record.json)

**结果回放 · Measured result replay — BeautyMap**

![Pure static: BeautyMap measured replay from this new run](../results/reference/robot-live-static/methods/beautymap/result.gif)

[Result MP4](../results/reference/robot-live-static/methods/beautymap/result.mp4) · [case record](../results/reference/robot-live-static/methods/beautymap/record.json) · RMSE **6.89 cm** · 290 次原生更新。

<a id="scene-dynamic-2d"></a>

#### 运动障碍物

<!-- MAP_QUALITY_VIDEO_TABLE -->
| 方法 | 地图类型 | 指标效果 |
| --- | --- | --- |
| Raw | 2D | 动态格删除 0.00%；静态格保留 100.00% |
| DUFOMap | 2D | 动态格删除 8.33%；静态格保留 100.00% |
| BeautyMap | 2D | 动态格删除 33.33%；静态格保留 96.64% |
<!-- /MAP_QUALITY_VIDEO_TABLE -->

[↑ 返回目录](#practice-index)

定位器：AMCL；每组291次更新，位置RMSE含初始化。

##### Raw map + AMCL

**现场执行 · Live execution — Raw RViz**

![Moving obstacles: actual Raw RViz live execution](../results/reference/robot-2d-dynamic-matched/executions/raw.gif)

[Live MP4](../results/reference/robot-2d-dynamic-matched/executions/raw.mp4) · [RViz config](../results/reference/robot-2d-dynamic-matched/view-raw.rviz) · [record](../results/reference/robot-2d-dynamic-matched/record.json)

**结果回放 · Measured result replay — Raw**

![Moving obstacles: Raw measured replay from this new run](../results/reference/robot-2d-dynamic-matched/methods/raw/result.gif)

[Result MP4](../results/reference/robot-2d-dynamic-matched/methods/raw/result.mp4) · [case record](../results/reference/robot-2d-dynamic-matched/methods/raw/record.json) · RMSE **7.52 cm** · 291 次原生更新。

##### DUFOMap map + AMCL

**现场执行 · Live execution — DUFOMap RViz**

![Moving obstacles: actual DUFOMap RViz live execution](../results/reference/robot-2d-dynamic-matched/executions/dufomap.gif)

[Live MP4](../results/reference/robot-2d-dynamic-matched/executions/dufomap.mp4) · [RViz config](../results/reference/robot-2d-dynamic-matched/view-dufomap.rviz) · [record](../results/reference/robot-2d-dynamic-matched/record.json)

**结果回放 · Measured result replay — DUFOMap**

![Moving obstacles: DUFOMap measured replay from this new run](../results/reference/robot-2d-dynamic-matched/methods/dufomap/result.gif)

[Result MP4](../results/reference/robot-2d-dynamic-matched/methods/dufomap/result.mp4) · [case record](../results/reference/robot-2d-dynamic-matched/methods/dufomap/record.json) · RMSE **8.19 cm** · 291 次原生更新。

##### BeautyMap map + AMCL

**现场执行 · Live execution — BeautyMap RViz**

![Moving obstacles: actual BeautyMap RViz live execution](../results/reference/robot-2d-dynamic-matched/executions/beautymap.gif)

[Live MP4](../results/reference/robot-2d-dynamic-matched/executions/beautymap.mp4) · [RViz config](../results/reference/robot-2d-dynamic-matched/view-beautymap.rviz) · [record](../results/reference/robot-2d-dynamic-matched/record.json)

**结果回放 · Measured result replay — BeautyMap**

![Moving obstacles: BeautyMap measured replay from this new run](../results/reference/robot-2d-dynamic-matched/methods/beautymap/result.gif)

[Result MP4](../results/reference/robot-2d-dynamic-matched/methods/beautymap/result.mp4) · [case record](../results/reference/robot-2d-dynamic-matched/methods/beautymap/record.json) · RMSE **7.29 cm** · 291 次原生更新。

<a id="scene-change-2d"></a>

#### 持久结构变化

<!-- MAP_QUALITY_VIDEO_TABLE -->
| 方法 | 地图类型 | 指标效果 |
| --- | --- | --- |
| Raw | 2D | 动态格删除 N/A；静态格保留 100.00%（静态A旧图） |
| DUFOMap | 2D | 动态格删除 N/A；静态格保留 100.00%（静态A旧图） |
| BeautyMap | 2D | 动态格删除 N/A；静态格保留 96.51%（静态A旧图） |
<!-- /MAP_QUALITY_VIDEO_TABLE -->

[↑ 返回目录](#practice-index)

定位器：AMCL；每组290次更新，位置RMSE含初始化。

本路线未诱发定位失效，恢复能力未验证。

##### Raw map + AMCL

**现场执行 · Live execution — Raw RViz**

![Persistent change: actual Raw RViz live execution](../results/reference/robot-live-large-change/executions/raw.gif)

[Live MP4](../results/reference/robot-live-large-change/executions/raw.mp4) · [RViz config](../results/reference/robot-live-large-change/view-raw.rviz) · [record](../results/reference/robot-live-large-change/record.json)

**结果回放 · Measured result replay — Raw**

![Persistent change: Raw measured replay from this new run](../results/reference/robot-live-large-change/methods/raw/result.gif)

[Result MP4](../results/reference/robot-live-large-change/methods/raw/result.mp4) · [case record](../results/reference/robot-live-large-change/methods/raw/record.json) · RMSE **6.84 cm** · 290 次原生更新。

##### DUFOMap map + AMCL

**现场执行 · Live execution — DUFOMap RViz**

![Persistent change: actual DUFOMap RViz live execution](../results/reference/robot-live-large-change/executions/dufomap.gif)

[Live MP4](../results/reference/robot-live-large-change/executions/dufomap.mp4) · [RViz config](../results/reference/robot-live-large-change/view-dufomap.rviz) · [record](../results/reference/robot-live-large-change/record.json)

**结果回放 · Measured result replay — DUFOMap**

![Persistent change: DUFOMap measured replay from this new run](../results/reference/robot-live-large-change/methods/dufomap/result.gif)

[Result MP4](../results/reference/robot-live-large-change/methods/dufomap/result.mp4) · [case record](../results/reference/robot-live-large-change/methods/dufomap/record.json) · RMSE **6.84 cm** · 290 次原生更新。

##### BeautyMap map + AMCL

**现场执行 · Live execution — BeautyMap RViz**

![Persistent change: actual BeautyMap RViz live execution](../results/reference/robot-live-large-change/executions/beautymap.gif)

[Live MP4](../results/reference/robot-live-large-change/executions/beautymap.mp4) · [RViz config](../results/reference/robot-live-large-change/view-beautymap.rviz) · [record](../results/reference/robot-live-large-change/record.json)

**结果回放 · Measured result replay — BeautyMap**

![Persistent change: BeautyMap measured replay from this new run](../results/reference/robot-live-large-change/methods/beautymap/result.gif)

[Result MP4](../results/reference/robot-live-large-change/methods/beautymap/result.mp4) · [case record](../results/reference/robot-live-large-change/methods/beautymap/record.json) · RMSE **6.39 cm** · 290 次原生更新。

<a id="scene-corridor-2d"></a>

#### 走廊退化

<!-- MAP_QUALITY_VIDEO_TABLE -->
| 方法 | 地图类型 | 指标效果 |
| --- | --- | --- |
| Raw | 2D | 动态格删除 N/A；静态格保留 100.00% |
| DUFOMap | 2D | 动态格删除 N/A；静态格保留 100.00% |
| BeautyMap | 2D | 动态格删除 N/A；静态格保留 100.00% |
<!-- /MAP_QUALITY_VIDEO_TABLE -->

[↑ 返回目录](#practice-index)

AMCL，508次更新；RMSE含1 m初值偏移。三张投影地图相同。

完整扫描对照：71.60 cm，同一参考事件后6.6 s持续收敛。本次为初值偏移纠正。[恢复判据与记录](../results/reference/robot-corridor-v2/record.json)。

##### Raw map + AMCL

**现场执行 · Live execution — Raw RViz**

![Corridor degradation: actual Raw RViz live execution](../results/reference/robot-corridor-v2/executions/degraded_raw.gif)

[Live MP4](../results/reference/robot-corridor-v2/executions/degraded_raw.mp4) · [RViz config](../results/reference/robot-corridor-v2/view-degraded_raw.rviz) · [record](../results/reference/robot-corridor-v2/record.json)

**结果回放 · Measured result replay — Raw**

![Corridor degradation: Raw measured replay from this new run](../results/reference/robot-corridor-v2/methods/degraded_raw/result.gif)

[Result MP4](../results/reference/robot-corridor-v2/methods/degraded_raw/result.mp4) · [case record](../results/reference/robot-corridor-v2/methods/degraded_raw/record.json) · RMSE **72.53 cm** · 508 次原生更新。

##### DUFOMap map + AMCL

**现场执行 · Live execution — DUFOMap RViz**

![Corridor degradation: actual DUFOMap RViz live execution](../results/reference/robot-corridor-v2/executions/degraded_dufomap.gif)

[Live MP4](../results/reference/robot-corridor-v2/executions/degraded_dufomap.mp4) · [RViz config](../results/reference/robot-corridor-v2/view-degraded_dufomap.rviz) · [record](../results/reference/robot-corridor-v2/record.json)

**结果回放 · Measured result replay — DUFOMap**

![Corridor degradation: DUFOMap measured replay from this new run](../results/reference/robot-corridor-v2/methods/degraded_dufomap/result.gif)

[Result MP4](../results/reference/robot-corridor-v2/methods/degraded_dufomap/result.mp4) · [case record](../results/reference/robot-corridor-v2/methods/degraded_dufomap/record.json) · RMSE **72.53 cm** · 508 次原生更新。

##### BeautyMap map + AMCL

**现场执行 · Live execution — BeautyMap RViz**

![Corridor degradation: actual BeautyMap RViz live execution](../results/reference/robot-corridor-v2/executions/degraded_beautymap.gif)

[Live MP4](../results/reference/robot-corridor-v2/executions/degraded_beautymap.mp4) · [RViz config](../results/reference/robot-corridor-v2/view-degraded_beautymap.rviz) · [record](../results/reference/robot-corridor-v2/record.json)

**结果回放 · Measured result replay — BeautyMap**

![Corridor degradation: BeautyMap measured replay from this new run](../results/reference/robot-corridor-v2/methods/degraded_beautymap/result.gif)

[Result MP4](../results/reference/robot-corridor-v2/methods/degraded_beautymap/result.mp4) · [case record](../results/reference/robot-corridor-v2/methods/degraded_beautymap/record.json) · RMSE **72.53 cm** · 508 次原生更新。

**实体机器人待测。**本机键盘演示在 `F:\be2演讲\实机脚本` 的 `20–23`；`24` 自动录制四类场景。此前现场及结果回放保留归档，与上面这轮录像区分。

### 三维地图清理与定位录制

新仿真B中的原库GICP真实窗口录制；保留完整XYZ／旋转评分及输出缺失情况。建图A是给定位姿的三维点云融合、清理，不等同于完整三维SLAM。

<a id="map-review-3d"></a>

#### 三维建图清理结果展示

[↑ 返回目录](#practice-index)

| 方法 | 地图类型 | 指标效果 |
| --- | --- | --- |
| Raw | 三维点云图 | 静态保留 100%；动态去除 0% |
| DUFOMap | 三维点云图 | 静态保留 99.998%；动态去除 46.59% |
| BeautyMap | 三维点云图 | 静态保留 81.15%；动态去除 74.36% |

真实RViz结果展示，使用已经计算好的原生输出，不进行新推理。灰色为静态及未评分背景点，红色为可信标注的残留运动箱体点。

![3D map cleaning result review](../results/reference/robot-3d-map-review-v2/execution.gif)

[MP4](../results/reference/robot-3d-map-review-v2/execution.mp4) · [point audit](../results/reference/robot-3d-map-audit/record.json)

<a id="scene-static-3d"></a>

#### 纯静态 · 3D

<!-- MAP_QUALITY_VIDEO_TABLE -->
| 方法 | 地图类型 | 指标效果 |
| --- | --- | --- |
| Raw | 3D | 动态点删除 N/A；静态点保留 100.00% |
| DUFOMap | 3D | 动态点删除 N/A；静态点保留 100.00% |
| BeautyMap | 3D | 动态点删除 N/A；静态点保留 83.33% |
<!-- /MAP_QUALITY_VIDEO_TABLE -->

[↑ 返回目录](#practice-index)

无动态污染需要清理，本次三维定位未见改善。

##### Raw 3D map + GICP

![Raw native 3D localization](../results/reference/robot-3d-static/executions/raw.gif)

[Live MP4](../results/reference/robot-3d-static/executions/raw.mp4) · [record](../results/reference/robot-3d-static/record.json)

##### DUFOMap 3D map + GICP

![DUFOMap native 3D localization](../results/reference/robot-3d-static/executions/dufomap.gif)

[Live MP4](../results/reference/robot-3d-static/executions/dufomap.mp4) · [record](../results/reference/robot-3d-static/record.json)

##### BeautyMap 3D map + GICP

![BeautyMap native 3D localization](../results/reference/robot-3d-static/executions/beautymap.gif)

[Live MP4](../results/reference/robot-3d-static/executions/beautymap.mp4) · [record](../results/reference/robot-3d-static/record.json)

<a id="scene-dynamic-3d"></a>

#### 运动障碍物 · 3D

<!-- MAP_QUALITY_VIDEO_TABLE -->
| 方法 | 地图类型 | 指标效果 |
| --- | --- | --- |
| Raw | 3D | 动态点删除 0.00%；静态点保留 100.00% |
| DUFOMap | 3D | 动态点删除 46.59%；静态点保留 100.00% |
| BeautyMap | 3D | 动态点删除 74.36%；静态点保留 81.15% |
<!-- /MAP_QUALITY_VIDEO_TABLE -->

[↑ 返回目录](#practice-index)

三维清理确实去除了动态点，但GICP定位仍未见明显收益。

##### Raw 3D map + GICP

![Raw native 3D localization](../results/reference/robot-3d-dynamic/executions/raw.gif)

[Live MP4](../results/reference/robot-3d-dynamic/executions/raw.mp4) · [record](../results/reference/robot-3d-dynamic/record.json)

##### DUFOMap 3D map + GICP

![DUFOMap native 3D localization](../results/reference/robot-3d-dynamic/executions/dufomap.gif)

[Live MP4](../results/reference/robot-3d-dynamic/executions/dufomap.mp4) · [record](../results/reference/robot-3d-dynamic/record.json)

##### BeautyMap 3D map + GICP

![BeautyMap native 3D localization](../results/reference/robot-3d-dynamic/executions/beautymap.gif)

[Live MP4](../results/reference/robot-3d-dynamic/executions/beautymap.mp4) · [record](../results/reference/robot-3d-dynamic/record.json)

<a id="scene-change-3d"></a>

#### 持久结构变化 · 3D

<!-- MAP_QUALITY_VIDEO_TABLE -->
| 方法 | 地图类型 | 指标效果 |
| --- | --- | --- |
| Raw | 3D | 动态点删除 N/A；静态点保留 100.00%（静态A旧图） |
| DUFOMap | 3D | 动态点删除 N/A；静态点保留 100.00%（静态A旧图） |
| BeautyMap | 3D | 动态点删除 N/A；静态点保留 83.33%（静态A旧图） |
<!-- /MAP_QUALITY_VIDEO_TABLE -->

[↑ 返回目录](#practice-index)

复用静态三维旧图；未执行变化检测或更新，未见定位改善。

##### Raw 3D map + GICP

![Raw native 3D localization](../results/reference/robot-3d-large-change/executions/raw.gif)

[Live MP4](../results/reference/robot-3d-large-change/executions/raw.mp4) · [record](../results/reference/robot-3d-large-change/record.json)

##### DUFOMap 3D map + GICP

![DUFOMap native 3D localization](../results/reference/robot-3d-large-change/executions/dufomap.gif)

[Live MP4](../results/reference/robot-3d-large-change/executions/dufomap.mp4) · [record](../results/reference/robot-3d-large-change/record.json)

##### BeautyMap 3D map + GICP

![BeautyMap native 3D localization](../results/reference/robot-3d-large-change/executions/beautymap.gif)

[Live MP4](../results/reference/robot-3d-large-change/executions/beautymap.mp4) · [record](../results/reference/robot-3d-large-change/record.json)

<a id="scene-corridor-3d"></a>

#### 走廊退化 · 3D

<!-- MAP_QUALITY_VIDEO_TABLE -->
| 方法 | 地图类型 | 指标效果 |
| --- | --- | --- |
| Raw | 3D | 动态点删除 N/A；静态点保留 100.00% |
| DUFOMap | 3D | 动态点删除 N/A；静态点保留 100.00% |
| BeautyMap | 3D | 动态点删除 N/A；静态点保留 99.90% |
<!-- /MAP_QUALITY_VIDEO_TABLE -->

[↑ 返回目录](#practice-index)

Raw与DUFOMap三维图字节相同却得到不同结果；有效输出覆盖不同，不能据此排名。

##### Raw 3D map + GICP

![Raw native 3D localization](../results/reference/robot-3d-corridor/executions/raw.gif)

[Live MP4](../results/reference/robot-3d-corridor/executions/raw.mp4) · [record](../results/reference/robot-3d-corridor/record.json)

##### DUFOMap 3D map + GICP

![DUFOMap native 3D localization](../results/reference/robot-3d-corridor/executions/dufomap.gif)

[Live MP4](../results/reference/robot-3d-corridor/executions/dufomap.mp4) · [record](../results/reference/robot-3d-corridor/record.json)

##### BeautyMap 3D map + GICP

![BeautyMap native 3D localization](../results/reference/robot-3d-corridor/executions/beautymap.gif)

[Live MP4](../results/reference/robot-3d-corridor/executions/beautymap.mp4) · [record](../results/reference/robot-3d-corridor/record.json)

### 此前Raw单地图三维静态试验

以下短静态试验使用实时三维点云和固定 Raw 三维地图；不使用 IMU／去畸变。评分为 XY／yaw 并包含初始化，传感器与时长不同，不能与二维 AMCL 直接排名。[Libraries and scope](testing/LOCALIZERS.zh-CN.md).

| 方法 | 地图类型 | 指标效果 |
| --- | --- | --- |
| NDT_OMP | Raw三维先验图 | XY RMSE 0.93 cm；首轮34.43 cm |
| GICP | Raw三维先验图 | XY RMSE 1.09 cm；仅静态验证 |

#### Pure static — NDT_OMP

**Live execution**

![NDT_OMP native 3D localization](../results/reference/robot-ndt-static/execution.gif)

[Live MP4](../results/reference/robot-ndt-static/execution.mp4) · [record](../results/reference/robot-ndt-static/record.json)

**Measured result replay**

![NDT_OMP saved pose result](../results/reference/robot-ndt-static/result.gif)

[Result MP4](../results/reference/robot-ndt-static/result.mp4) · XY RMSE **0.93 cm** · yaw **0.17°** · 402 updates.

#### Pure static — GICP

**Live execution**

![GICP native 3D localization](../results/reference/robot-gicp-static/execution.gif)

[Live MP4](../results/reference/robot-gicp-static/execution.mp4) · [record](../results/reference/robot-gicp-static/record.json)

**Measured result replay**

![GICP saved pose result](../results/reference/robot-gicp-static/result.gif)

[Result MP4](../results/reference/robot-gicp-static/result.mp4) · XY RMSE **1.09 cm** · yaw **0.16°** · 397 updates.

相同估计器参数的首次 NDT 试验为 34.43 cm，记录也保留。差异原因尚未定位，不能只用最新分数宣称鲁棒性。[Initial trial](../results/reference/robot-ndt-static-initial/record.json).

### 补充场景实时录制

真实 Gazebo＋RViz＋终端；RViz 使用完整视口，并按地图坐标居中。旧自建看图程序录像保留归档。

#### S1 static · slam_toolbox mapping

![S1 static · slam_toolbox mapping](../results/reference/robot-supp-static/execution.gif)

[MP4](../results/reference/robot-supp-static/execution.mp4) · [record](../results/reference/robot-supp-static/record.json)

#### S2 dynamic · slam_toolbox mapping

![S2 dynamic · slam_toolbox mapping](../results/reference/robot-supp-dynamic/execution.gif)

[MP4](../results/reference/robot-supp-dynamic/execution.mp4) · [record](../results/reference/robot-supp-dynamic/record.json)

#### S3 persistent change · Raw map + AMCL

![S3 persistent change · Raw map + AMCL](../results/reference/robot-supp-large-change/execution.gif)

[MP4](../results/reference/robot-supp-large-change/execution.mp4) · [record](../results/reference/robot-supp-large-change/record.json)

#### S4 new corridor · limited → restored AMCL

![S4 new corridor · limited → restored AMCL](../results/reference/robot-corridor-v2/executions/degraded_raw.gif)

[MP4](../results/reference/robot-corridor-v2/executions/degraded_raw.mp4) · [record](../results/reference/robot-corridor-v2/record.json)

<a id="mapping-hypothesis-tests"></a>

## 假设

本轮问题聚焦**地图清理**。假设由易到难逐项检验；前提不成立，就不能继续推出定位收益。已有Guard／Depth／Search仅作为标明范围的定位探索附录保留。

| 假设：由易到难 | 已有简单实验／结果 |
| --- | --- |
| M1：多帧可见性能够删除动态残影 | 动态场景：DUFOMap删除46.59%、BeautyMap删除74.36%的三维动态点；原生二维SRRG删除42.31%的已验证动态残影格。分母不同，不跨方法排名。 |
| M2：删动态时能保留静态约束 | 同场景：三维静态保留DUFOMap为99.998%、BeautyMap为81.15%；SRRG二维静态覆盖为99.51%。BeautyMap本次删得更多，也损失更多静态支持。 |
| M3：三维清理收益能保留到二维投影 | 同图重新评分：投影动态格删除仅8.33%／33.33%，只部分支持；原生二维SRRG是另一种表示和对照。 |
| M4：残影污染有效约束时，地图更干净才能降低独立定位B误差 | 动态GICP的Raw／DUFO／Beauty XYZ RMSE为0.98／0.98／1.04 cm，尚无收益证据。固定定位器、逐级增加污染并重复的实验待做；SRRG独立定位B也待测。 |
| M5：二维雷达＋深度相机能够区分遮挡与静态结构 | 已有Depth实验只检验定位，未见普遍稳定收益。将时序深度可见性用于地图更新门控，并对照二维SRRG和三维参照，仍是未验证的建图假设。 |

[建图问题、论文依据与后续单因素实验](testing/MAPPING-FOCUS.zh-CN.md) · [地图指标与故障时间点](testing/MAP-METRICS.zh-CN.md)。静态和走廊是边界对照：删除点不能凭空增加缺失几何；持久变化需另测地图更新。

<a id="hypothesis-experiments"></a>

## 假设检验实验

此附录保留此前的定位层探索；地图冻结，不能据此声称验证了动态建图。

根据此前录像，先提出三个方向，再做对应实验：

- **H1 · 退化保护：**抑制不一致匹配，弱约束方向减少激光修正，保留轮式里程计预测。
- **H2 · 深度补充：**用二维雷达＋深度相机补充可见的高度结构，并用三维雷达做对应对照。
- **H3 · 搜索与确认：**搜索多个附近位置，只有候选足够独特、连续两次与里程计运动一致时才接受。

这是自写的地面机器人小原型。二维组没有三维雷达；三维组使用XYZ观测、约束x/y/yaw运动。建图A给定位姿，地图冻结，定位B不读取真值。保留四个原场景，另将增加两块高处几何的场景单独标为派生对照。理想仿真单轮结果不构成稳定排名。

[固定假设、对照与结果解释](testing/HYPOTHESES.zh-CN.md) · [实验视频目录](../demo/hypotheses.html) · [一键脚本](../demo/README.md#开放问题假设与简单实验)

<!-- PROBE_APPENDIX_RESULTS -->

<a id="hypothesis-experiment-index"></a>

| 场景 | 2D＋深度 | 3D＋深度 |
| --- | --- | --- |
| 纯静态 | [查看实验](#probe-calibrated-2d-static) | [查看实验](#probe-calibrated-3d-static) |
| 运动障碍物 | [查看实验](#probe-calibrated-2d-dynamic) | [查看实验](#probe-calibrated-3d-dynamic) |
| 持久结构变化 | [查看实验](#probe-calibrated-2d-large-change) | [查看实验](#probe-calibrated-3d-large-change) |
| 原走廊退化 | [查看实验](#probe-calibrated-2d-corridor) | [查看实验](#probe-calibrated-3d-corridor) |
| 高处标志 · 派生对照 | [查看实验](#probe-calibrated-2d-height-corridor) | [查看实验](#probe-calibrated-3d-height-corridor) |

[粗到细补充实验](#probe-refinement-index)

[结果解释与后续方向](#hypothesis-findings)

本轮固定同源Raw图，五个原型严格共享已配对输入。红Plain、黄Guard、橙Depth、紫雷达搜索、绿深度＋搜索、蓝原生AMCL／GICP。二维报XY，三维报XYZ；单轮结果不构成稳定排名。

### 2D · 真实窗口实验

<a id="probe-calibrated-2d-static"></a>

#### 纯静态 · 2D

[↑ 返回目录](#hypothesis-experiment-index)

| 方法 | 地图／观测 | 指标效果 |
| --- | --- | --- |
| Raw + AMCL | 同源二维栅格投影图 | XY RMSE 6.82 cm |
| Plain ICP | 二维雷达点图 | XY RMSE 0.15 cm |
| H1 · Guard | 二维雷达点图 | XY RMSE 0.15 cm；接近Plain |
| H2 · Guard＋Depth | 二维雷达点图＋深度点图 | XY RMSE 0.21 cm；较Guard高0.06 cm |
| H3 · 雷达搜索 | 二维雷达点图 | XY RMSE 0.15 cm；接近Guard |
| H3 · 深度＋搜索 | 二维雷达点图＋深度点图 | XY RMSE 0.21 cm；接近Depth |

五原型各264帧；有效深度219/264帧；原生参照287次输出。车体高度由建图A标定。

原生参照最后一次有效输出在仿真73.2s，原型记录至99.4s；无输出时段未填补，其RMSE只覆盖已有输出。

![纯静态 · 2D · 真实窗口](../results/reference/probe-calibrated-2d-static/execution.gif)

[MP4](../results/reference/probe-calibrated-2d-static/execution.mp4) · [record](../results/reference/probe-calibrated-2d-static/record.json) · [CSV](../results/reference/probe-calibrated-2d-static/recover-samples.csv)

<a id="probe-calibrated-2d-dynamic"></a>

#### 运动障碍物 · 2D

[↑ 返回目录](#hypothesis-experiment-index)

| 方法 | 地图／观测 | 指标效果 |
| --- | --- | --- |
| Raw + AMCL | 同源二维栅格投影图 | XY RMSE 7.08 cm |
| Plain ICP | 二维雷达点图 | XY RMSE 0.37 cm |
| H1 · Guard | 二维雷达点图 | XY RMSE 0.19 cm；较Plain低0.18 cm |
| H2 · Guard＋Depth | 二维雷达点图＋深度点图 | XY RMSE 0.18 cm；接近Guard |
| H3 · 雷达搜索 | 二维雷达点图 | XY RMSE 0.19 cm；接近Guard |
| H3 · 深度＋搜索 | 二维雷达点图＋深度点图 | XY RMSE 0.18 cm；接近Depth |

五原型各265帧；有效深度181/265帧；原生参照292次输出。车体高度由建图A标定。

原生参照最后一次有效输出在仿真72.3s，原型记录至99.7s；无输出时段未填补，其RMSE只覆盖已有输出。

![运动障碍物 · 2D · 真实窗口](../results/reference/probe-calibrated-2d-dynamic/execution.gif)

[MP4](../results/reference/probe-calibrated-2d-dynamic/execution.mp4) · [record](../results/reference/probe-calibrated-2d-dynamic/record.json) · [CSV](../results/reference/probe-calibrated-2d-dynamic/recover-samples.csv)

<a id="probe-calibrated-2d-large-change"></a>

#### 持久结构变化 · 2D

[↑ 返回目录](#hypothesis-experiment-index)

| 方法 | 地图／观测 | 指标效果 |
| --- | --- | --- |
| Raw + AMCL | 同源二维栅格投影图 | XY RMSE 6.28 cm |
| Plain ICP | 二维雷达点图 | XY RMSE 7.98 cm |
| H1 · Guard | 二维雷达点图 | XY RMSE 0.49 cm；较Plain低7.49 cm |
| H2 · Guard＋Depth | 二维雷达点图＋深度点图 | XY RMSE 0.49 cm；接近Guard |
| H3 · 雷达搜索 | 二维雷达点图 | XY RMSE 0.49 cm；接近Guard |
| H3 · 深度＋搜索 | 二维雷达点图＋深度点图 | XY RMSE 0.49 cm；接近Depth |

五原型各263帧；有效深度187/263帧；原生参照288次输出。车体高度由建图A标定。

原生参照最后一次有效输出在仿真71.3s，原型记录至99.3s；无输出时段未填补，其RMSE只覆盖已有输出。

旧图保持冻结；此处检验不一致观测的处理，没有执行地图更新。

![持久结构变化 · 2D · 真实窗口](../results/reference/probe-calibrated-2d-large-change/execution.gif)

[MP4](../results/reference/probe-calibrated-2d-large-change/execution.mp4) · [record](../results/reference/probe-calibrated-2d-large-change/record.json) · [CSV](../results/reference/probe-calibrated-2d-large-change/recover-samples.csv)

<a id="probe-calibrated-2d-corridor"></a>

#### 原走廊退化 · 2D

[↑ 返回目录](#hypothesis-experiment-index)

| 方法 | 地图／观测 | 指标效果 |
| --- | --- | --- |
| Raw + AMCL | 同源二维栅格投影图 | XY RMSE 100.61 cm；恢复后45.7 s持续收敛 |
| Plain ICP | 二维雷达点图 | XY RMSE 1037.69 cm；未持续收敛 |
| H1 · Guard | 二维雷达点图 | XY RMSE 100.48 cm；较Plain低937.21 cm；未持续收敛 |
| H2 · Guard＋Depth | 二维雷达点图＋深度点图 | XY RMSE 100.54 cm；较Guard高0.06 cm；未持续收敛 |
| H3 · 雷达搜索 | 二维雷达点图 | XY RMSE 70.40 cm；较Guard低30.08 cm；恢复后5.8 s持续收敛 |
| H3 · 深度＋搜索 | 二维雷达点图＋深度点图 | XY RMSE 70.44 cm；较Depth低30.11 cm；恢复后5.8 s持续收敛 |

五原型各338帧；有效深度195/338帧；原生参照600次输出。车体高度由建图A标定。

![原走廊退化 · 2D · 真实窗口](../results/reference/probe-calibrated-2d-corridor/execution.gif)

[MP4](../results/reference/probe-calibrated-2d-corridor/execution.mp4) · [record](../results/reference/probe-calibrated-2d-corridor/record.json) · [CSV](../results/reference/probe-calibrated-2d-corridor/recover-samples.csv)

<a id="probe-calibrated-2d-height-corridor"></a>

#### 高处标志 · 派生对照 · 2D

[↑ 返回目录](#hypothesis-experiment-index)

| 方法 | 地图／观测 | 指标效果 |
| --- | --- | --- |
| Raw + AMCL | 同源二维栅格投影图 | XY RMSE 67.00 cm；恢复后11.7 s持续收敛 |
| Plain ICP | 二维雷达点图 | XY RMSE 285.54 cm；未持续收敛 |
| H1 · Guard | 二维雷达点图 | XY RMSE 101.15 cm；较Plain低184.39 cm；未持续收敛 |
| H2 · Guard＋Depth | 二维雷达点图＋深度点图 | XY RMSE 100.77 cm；较Guard低0.38 cm；未持续收敛 |
| H3 · 雷达搜索 | 二维雷达点图 | XY RMSE 70.93 cm；较Guard低30.22 cm；恢复后5.0 s持续收敛 |
| H3 · 深度＋搜索 | 二维雷达点图＋深度点图 | XY RMSE 21.15 cm；较Depth低79.61 cm；恢复后0.2 s持续收敛 |

五原型各345帧；有效深度239/345帧；原生参照620次输出。车体高度由建图A标定。

此场景额外加入两块高处几何，作为结构互补的可行性对照；与原走廊分别报告。

![高处标志 · 派生对照 · 2D · 真实窗口](../results/reference/probe-calibrated-2d-height-corridor/execution.gif)

[MP4](../results/reference/probe-calibrated-2d-height-corridor/execution.mp4) · [record](../results/reference/probe-calibrated-2d-height-corridor/record.json) · [CSV](../results/reference/probe-calibrated-2d-height-corridor/recover-samples.csv)

### 3D · 真实窗口实验

<a id="probe-calibrated-3d-static"></a>

#### 纯静态 · 3D

[↑ 返回目录](#hypothesis-experiment-index)

| 方法 | 地图／观测 | 指标效果 |
| --- | --- | --- |
| Raw + GICP | 三维雷达点图 | XYZ RMSE 1.08 cm |
| Plain ICP | 三维雷达点图 | XYZ RMSE 0.12 cm |
| H1 · Guard | 三维雷达点图 | XYZ RMSE 0.12 cm；接近Plain |
| H2 · Guard＋Depth | 三维雷达点图＋深度点图 | XYZ RMSE 0.21 cm；较Guard高0.09 cm |
| H3 · 雷达搜索 | 三维雷达点图 | XYZ RMSE 0.12 cm；接近Guard |
| H3 · 深度＋搜索 | 三维雷达点图＋深度点图 | XYZ RMSE 0.21 cm；接近Depth |

五原型各266帧；有效深度184/266帧；原生参照994次输出。车体高度由建图A标定。

![纯静态 · 3D · 真实窗口](../results/reference/probe-calibrated-3d-static/execution.gif)

[MP4](../results/reference/probe-calibrated-3d-static/execution.mp4) · [record](../results/reference/probe-calibrated-3d-static/record.json) · [CSV](../results/reference/probe-calibrated-3d-static/recover-samples.csv)

<a id="probe-calibrated-3d-dynamic"></a>

#### 运动障碍物 · 3D

[↑ 返回目录](#hypothesis-experiment-index)

| 方法 | 地图／观测 | 指标效果 |
| --- | --- | --- |
| Raw + GICP | 三维雷达点图 | XYZ RMSE 1.39 cm |
| Plain ICP | 三维雷达点图 | XYZ RMSE 0.17 cm |
| H1 · Guard | 三维雷达点图 | XYZ RMSE 0.13 cm；较Plain低0.04 cm |
| H2 · Guard＋Depth | 三维雷达点图＋深度点图 | XYZ RMSE 0.13 cm；接近Guard |
| H3 · 雷达搜索 | 三维雷达点图 | XYZ RMSE 0.13 cm；接近Guard |
| H3 · 深度＋搜索 | 三维雷达点图＋深度点图 | XYZ RMSE 0.13 cm；接近Depth |

五原型各258帧；有效深度154/258帧；原生参照951次输出。车体高度由建图A标定。

![运动障碍物 · 3D · 真实窗口](../results/reference/probe-calibrated-3d-dynamic/execution.gif)

[MP4](../results/reference/probe-calibrated-3d-dynamic/execution.mp4) · [record](../results/reference/probe-calibrated-3d-dynamic/record.json) · [CSV](../results/reference/probe-calibrated-3d-dynamic/recover-samples.csv)

<a id="probe-calibrated-3d-large-change"></a>

#### 持久结构变化 · 3D

[↑ 返回目录](#hypothesis-experiment-index)

| 方法 | 地图／观测 | 指标效果 |
| --- | --- | --- |
| Raw + GICP | 三维雷达点图 | XYZ RMSE 1.25 cm |
| Plain ICP | 三维雷达点图 | XYZ RMSE 3.69 cm |
| H1 · Guard | 三维雷达点图 | XYZ RMSE 0.24 cm；较Plain低3.45 cm |
| H2 · Guard＋Depth | 三维雷达点图＋深度点图 | XYZ RMSE 0.35 cm；较Guard高0.11 cm |
| H3 · 雷达搜索 | 三维雷达点图 | XYZ RMSE 0.24 cm；接近Guard |
| H3 · 深度＋搜索 | 三维雷达点图＋深度点图 | XYZ RMSE 0.35 cm；接近Depth |

五原型各264帧；有效深度163/264帧；原生参照950次输出。车体高度由建图A标定。

旧图保持冻结；此处检验不一致观测的处理，没有执行地图更新。

![持久结构变化 · 3D · 真实窗口](../results/reference/probe-calibrated-3d-large-change/execution.gif)

[MP4](../results/reference/probe-calibrated-3d-large-change/execution.mp4) · [record](../results/reference/probe-calibrated-3d-large-change/record.json) · [CSV](../results/reference/probe-calibrated-3d-large-change/recover-samples.csv)

<a id="probe-calibrated-3d-corridor"></a>

#### 原走廊退化 · 3D

[↑ 返回目录](#hypothesis-experiment-index)

| 方法 | 地图／观测 | 指标效果 |
| --- | --- | --- |
| Raw + GICP | 三维雷达点图 | XYZ RMSE 397.82 cm；未持续收敛 |
| Plain ICP | 三维雷达点图 | XYZ RMSE 733.38 cm；未持续收敛 |
| H1 · Guard | 三维雷达点图 | XYZ RMSE 100.49 cm；较Plain低632.88 cm；未持续收敛 |
| H2 · Guard＋Depth | 三维雷达点图＋深度点图 | XYZ RMSE 100.62 cm；较Guard高0.12 cm；未持续收敛 |
| H3 · 雷达搜索 | 三维雷达点图 | XYZ RMSE 56.77 cm；较Guard低43.72 cm；恢复后6.2 s持续收敛 |
| H3 · 深度＋搜索 | 三维雷达点图＋深度点图 | XYZ RMSE 57.56 cm；较Depth低43.06 cm；恢复后6.6 s持续收敛 |

五原型各247帧；有效深度122/247帧；原生参照712次输出。车体高度由建图A标定。

原生参照最后一次有效输出在仿真75.6s，原型记录至132.8s；无输出时段未填补，其RMSE只覆盖已有输出。

![原走廊退化 · 3D · 真实窗口](../results/reference/probe-calibrated-3d-corridor/execution.gif)

[MP4](../results/reference/probe-calibrated-3d-corridor/execution.mp4) · [record](../results/reference/probe-calibrated-3d-corridor/record.json) · [CSV](../results/reference/probe-calibrated-3d-corridor/recover-samples.csv)

<a id="probe-calibrated-3d-height-corridor"></a>

#### 高处标志 · 派生对照 · 3D

[↑ 返回目录](#hypothesis-experiment-index)

| 方法 | 地图／观测 | 指标效果 |
| --- | --- | --- |
| Raw + GICP | 三维雷达点图 | XYZ RMSE 512.79 cm；未持续收敛 |
| Plain ICP | 三维雷达点图 | XYZ RMSE 46.60 cm；恢复后8.7 s持续收敛 |
| H1 · Guard | 三维雷达点图 | XYZ RMSE 100.36 cm；较Plain高53.76 cm；未持续收敛 |
| H2 · Guard＋Depth | 三维雷达点图＋深度点图 | XYZ RMSE 100.38 cm；较Guard高0.02 cm；未持续收敛 |
| H3 · 雷达搜索 | 三维雷达点图 | XYZ RMSE 47.70 cm；较Guard低52.66 cm；恢复后8.7 s持续收敛 |
| H3 · 深度＋搜索 | 三维雷达点图＋深度点图 | XYZ RMSE 50.79 cm；较Depth低49.59 cm；恢复后12.8 s持续收敛 |

五原型各203帧；有效深度124/203帧；原生参照716次输出。车体高度由建图A标定。

原生参照最后一次有效输出在仿真75.1s，原型记录至132.5s；无输出时段未填补，其RMSE只覆盖已有输出。

此场景额外加入两块高处几何，作为结构互补的可行性对照；与原走廊分别报告。

![高处标志 · 派生对照 · 3D · 真实窗口](../results/reference/probe-calibrated-3d-height-corridor/execution.gif)

[MP4](../results/reference/probe-calibrated-3d-height-corridor/execution.mp4) · [record](../results/reference/probe-calibrated-3d-height-corridor/record.json) · [CSV](../results/reference/probe-calibrated-3d-height-corridor/recover-samples.csv)

<a id="probe-refinement-index"></a>

### 补充假设：粗到细搜索与恢复确认

首轮高处对照出现约20cm平台误差。补充试验将候选平移网格从0.4m细化到0.1m，并把更多已检查位置纳入分数差检验；H1／H2、分数门槛和连续确认规则保持一致。使用上方同一B包的雷达、深度、里程计数组重新推理，下面的视频是保存输出的结果回放。

| 场景 | 2D重算 | 3D重算 |
| --- | --- | --- |
| 原走廊退化 | [2D](#probe-calibrated-refinement-2d-corridor) | [3D](#probe-calibrated-refinement-3d-corridor) |
| 高处标志 · 派生对照 | [2D](#probe-calibrated-refinement-2d-height-corridor) | [3D](#probe-calibrated-refinement-3d-height-corridor) |

<a id="probe-calibrated-refinement-2d-corridor"></a>

#### 2D · 原走廊退化 · 同输入细化

[↑ 返回目录](#hypothesis-experiment-index)

| 方法 | 地图／观测 | 指标效果 |
| --- | --- | --- |
| 粗搜索·雷达 | 雷达点图 | XY RMSE 70.40 cm；首次输出后61.1s持续收敛 |
| 粗搜索·深度＋雷达 | 雷达点图＋深度点图 | XY RMSE 70.44 cm；首次输出后61.1s持续收敛 |
| 细化·雷达 | 雷达点图 | XY RMSE 70.40 cm；首次输出后61.1s持续收敛 |
| 细化·深度＋雷达 | 雷达点图＋深度点图 | XY RMSE 70.44 cm；首次输出后61.1s持续收敛 |

![原走廊退化 · 2D · 离线重算结果回放](../results/reference/probe-calibrated-refinement-2d-corridor/result.gif)

[结果回放MP4](../results/reference/probe-calibrated-refinement-2d-corridor/result.mp4) · [record](../results/reference/probe-calibrated-refinement-2d-corridor/record.json)

<a id="probe-calibrated-refinement-2d-height-corridor"></a>

#### 2D · 高处标志 · 派生对照 · 同输入细化

[↑ 返回目录](#hypothesis-experiment-index)

| 方法 | 地图／观测 | 指标效果 |
| --- | --- | --- |
| 粗搜索·雷达 | 雷达点图 | XY RMSE 70.93 cm；首次输出后60.7s持续收敛 |
| 粗搜索·深度＋雷达 | 雷达点图＋深度点图 | XY RMSE 21.15 cm；首次输出后55.9s持续收敛 |
| 细化·雷达 | 雷达点图 | XY RMSE 70.93 cm；首次输出后60.7s持续收敛 |
| 细化·深度＋雷达 | 雷达点图＋深度点图 | XY RMSE 16.20 cm；首次输出后3.3s持续收敛 |

![高处标志 · 派生对照 · 2D · 离线重算结果回放](../results/reference/probe-calibrated-refinement-2d-height-corridor/result.gif)

[结果回放MP4](../results/reference/probe-calibrated-refinement-2d-height-corridor/result.mp4) · [record](../results/reference/probe-calibrated-refinement-2d-height-corridor/record.json)

<a id="probe-calibrated-refinement-3d-corridor"></a>

#### 3D · 原走廊退化 · 同输入细化

[↑ 返回目录](#hypothesis-experiment-index)

| 方法 | 地图／观测 | 指标效果 |
| --- | --- | --- |
| 粗搜索·雷达 | 雷达点图 | XYZ RMSE 56.77 cm；首次输出后63.7s持续收敛 |
| 粗搜索·深度＋雷达 | 雷达点图＋深度点图 | XYZ RMSE 57.56 cm；首次输出后64.1s持续收敛 |
| 细化·雷达 | 雷达点图 | XYZ RMSE 56.77 cm；首次输出后63.7s持续收敛 |
| 细化·深度＋雷达 | 雷达点图＋深度点图 | XYZ RMSE 56.84 cm；首次输出后63.7s持续收敛 |

![原走廊退化 · 3D · 离线重算结果回放](../results/reference/probe-calibrated-refinement-3d-corridor/result.gif)

[结果回放MP4](../results/reference/probe-calibrated-refinement-3d-corridor/result.mp4) · [record](../results/reference/probe-calibrated-refinement-3d-corridor/record.json)

<a id="probe-calibrated-refinement-3d-height-corridor"></a>

#### 3D · 高处标志 · 派生对照 · 同输入细化

[↑ 返回目录](#hypothesis-experiment-index)

| 方法 | 地图／观测 | 指标效果 |
| --- | --- | --- |
| 粗搜索·雷达 | 雷达点图 | XYZ RMSE 47.70 cm；首次输出后66.1s持续收敛 |
| 粗搜索·深度＋雷达 | 雷达点图＋深度点图 | XYZ RMSE 50.79 cm；首次输出后70.2s持续收敛 |
| 细化·雷达 | 雷达点图 | XYZ RMSE 47.70 cm；首次输出后66.1s持续收敛 |
| 细化·深度＋雷达 | 雷达点图＋深度点图 | XYZ RMSE 47.71 cm；首次输出后66.1s持续收敛 |

![高处标志 · 派生对照 · 3D · 离线重算结果回放](../results/reference/probe-calibrated-refinement-3d-height-corridor/result.gif)

[结果回放MP4](../results/reference/probe-calibrated-refinement-3d-height-corridor/result.mp4) · [record](../results/reference/probe-calibrated-refinement-3d-height-corridor/record.json)

<!-- PROBE_APPENDIX_RESULTS_END -->

<a id="hypothesis-findings"></a>

### 本轮实验支持的方向

- **稳健匹配＋里程计保底**：持久变化中，二维RMSE由Plain的7.98降到Guard的0.49cm，三维由3.69降到0.24cm。但三维高处走廊中Guard保留约1m偏差，反而差于恢复后自行收敛的Plain；保护跟踪不能替代重定位。
- **二维雷达＋深度＋候选细化**：在额外高度几何对照中，同输入细化将持续收敛从首次输出后55.9s提前到3.3s，完整XY RMSE由21.15降到16.20cm。原走廊没有同样收益；三维高处组也未提前恢复，负结果均列在上方。
- **有界搜索＋恢复确认**：原走廊完整观测恢复后，雷达搜索在二维／三维分别用5.8／6.2s持续收敛。几何分数高、连续两次一致仍不保证正确：二维粗深度搜索曾确认约20cm偏差，细化实验才纠正它。

[详细原因与后续方向](testing/HYPOTHESES.zh-CN.md#hypothesis-findings) · [逐帧汇总](../results/analysis/hypotheses/calibrated-summary.json) · [首轮与无效细化录像](../demo/hypotheses-diagnostics.html)。本轮是给定位姿建图A、冻结图定位B的理想仿真，尚未验证仅廉价传感器的自主建图、实际绑架恢复或实体效果。

## 实机实验

<!-- 待补：实机实验内容。 -->

## 分支

| 分支 | 用途 |
| --- | --- |
| main | 提交展示：动态环境鲁棒定位主线、按范围记录的建图／定位复现，以及候选自恢复实验。 |
| [reproduce/author-originals](https://github.com/p20030920p/SLAM_Learning/tree/reproduce/author-originals) | 作者原流程、论文表格评分与录制。 |
| [notes/personal-study-guide-20261008](https://github.com/p20030920p/SLAM_Learning/tree/notes/personal-study-guide-20261008) | 个人学习笔记与 `src/physical/` 实物实验，保留操作说明和失败记录。 |

[AI 使用](guides/DISCLOSURE.zh-CN.md) · [来源／许可](guides/ATTRIBUTION.zh-CN.md) · [引用](CITATION.cff) · [许可](../src/LICENSE)
