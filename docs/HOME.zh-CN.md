<div align="center">

# SLAM Learning

**动态环境中的鲁棒定位与 SLAM**

动态残影清理 · 静态结构保留 · 下游定位检验

[![CPU reproducibility](https://github.com/p20030920p/SLAM_Learning/actions/workflows/ci.yml/badge.svg)](https://github.com/p20030920p/SLAM_Learning/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.10-3776AB)](../src/pyproject.toml)

[English](../README.md) | 中文

[实物测试问题](#problem-getting-from-physical-test) · [方向分析](#方向分析) · [开放问题](#开放问题) · [假设](#假设) · [相关工作](#相关工作) · [指标](#指标)

[实践](#实践) · [分支](#分支)

</div>

## Problem getting from Physical test

<a id="physical-test-mirror"></a>

### 镜面与建图不全

| 图1：镜面 | 图2：镜面导致的建图不全 |
| --- | --- |
| <a id="physical-test-mirror-photo"></a><a href="media/physical-test/20261015-mirror/mirror-surface.jpg"><img src="media/physical-test/20261015-mirror/mirror-surface.jpg" width="420" alt="图1：镜面"></a> | <a id="physical-test-mirror-map"></a><a href="media/physical-test/20261015-mirror/mirror-incomplete-map.png"><img src="media/physical-test/20261015-mirror/mirror-incomplete-map.png" width="420" alt="图2：镜面导致的建图不全"></a> |

从图2中可以看出，当出现镜面的情况下，建图会难以继续，这是建图中的一个问题之一，在定位时候也是如此，没法扫描出边界

**分析：**
<!-- PHYSICAL_TEST_ANALYSIS:mirror -->

<!-- /PHYSICAL_TEST_ANALYSIS:mirror -->

<a id="physical-test-real"></a>

### 实物现场

<a href="media/physical-test/20261015/real.gif"><img src="media/physical-test/20261015/real.gif" width="360" loading="lazy" alt="实物现场"></a>



<!-- PHYSICAL_TEST_ANALYSIS:real -->

<!-- /PHYSICAL_TEST_ANALYSIS:real -->

<a id="physical-test-rviz-static"></a>

### RViz 静态视频

<a href="media/physical-test/20261015/rviz_Static.gif"><img src="media/physical-test/20261015/rviz_Static.gif" width="960" loading="lazy" alt="RViz 静态视频"></a>
<!-- PHYSICAL_TEST_ANALYSIS:rviz-static -->

<!-- /PHYSICAL_TEST_ANALYSIS:rviz-static -->

<a id="physical-test-rviz-dynamic"></a>

### 3. RViz 动态视频

<a href="media/physical-test/20261015/rviz_dyn.gif"><img src="media/physical-test/20261015/rviz_dyn.gif" width="960" loading="lazy" alt="RViz 动态视频"></a>



**分析：**从视频中，其一，可以看出，由于运动速度过快，导致建图过程中建图的畸变；其次，从动态视频中可以看出，由于动态人的出现，导致建图中间出现了污染点。
<!-- PHYSICAL_TEST_ANALYSIS:rviz-dynamic -->

<!-- /PHYSICAL_TEST_ANALYSIS:rviz-dynamic -->

## 方向分析

### 1. 题目究竟在研究什么？

**方向：动态环境中的鲁棒定位与 SLAM。**

建图-定位，他们不是单一的，而是相辅相成的，

测试方式：使用不同的建图，再跑统一的定位方法，看看误差是否会减小


以下是我对定位的理解

* 在我看来定位的本质：是在运动先验的条件下，根据当前观测，进行地图一致性评分，推断机器人位姿和可信度
  * 以AMCL和GICP为例，AMCL维护粒子位姿分布，通过观测一致性更新权重并重采样；GICP用几何一致性优化位姿
  * 地图决定了定位能够使用哪些参照，能够将输入的传感器数据通过地图比对来进行定位

因此，我们的目标是：优化建图，以优化定位

* 运动的物体会形成残影，污染建图，影响静态建图保留--**我们主要做这个**

  * 运动检测与剔除--剔除动态物体的情况下，尽可能保留静态结构

    * 2D Lidar-SRRG √

    * 3D Lidar-DUFOMap, Beauty Map √

      ![image-20261015222612651](media/direction/20261016-user/image-20261015222612651.png)

    * Depth/RGB Camera- DynaSLAM![image-20261015222431746](media/direction/20261016-user/image-20261015222431746.png)

* 传感器本身的运动会导致运动畸变，进而引起定位漂移和地图错位

  * 速度过快/转弯时，导致里程计漂移
    * ![image-20261015230734740](media/direction/20261016-user/image-20261015230734740.png)
    * 解决方案：Fast-LIO：融合LiDAR与IMU，估计扫描期间的传感器运动并进行点补偿，再进行配准；在快速运动下是否稳定，需要实验验证![image-20261015231926970](media/direction/20261016-user/image-20261015231926970.png)
    * 个人的小理解：多传感器融合本身也是解决这个问题的好方法，因为可以通过视觉，雷达，里程计等多方面比对；这样即使传感器本身较差也能做的比较好；但是本身多传感器融合就很难

* 特殊的障碍物/退化的环境，会导致定位失准和建图失效

  * 镜面
    * ![image-20261015230454037](media/direction/20261016-user/image-20261015230454037.png)
  * 长廊
    * ![image-20261015234829998](media/direction/20261016-user/image-20261015234829998.png)
    * 由于特征相同的位置太多，所以无法判断实际位置，很容易出现定位系统失效的问题
    * 一些简单的提案：在长廊中间放入二维码等容易辨认的，并在地图上标注他的位置，作为一个标志，

* 在地图建好后，要进行维护和优化，这样才能长久地对定位友好

  * 家具移动位置的时候，更新地图的--Khronos
    * 为什么要更新地图：能够根据这个变动的速度，判断，这个地图是长期静止，偶尔搬动-在建图中标记为静态结构；快速变动-动态结构![image-20261016000012003](media/direction/20261016-user/image-20261016000012003.png)
    * 这里也可以回答我在课堂上没有说的内容，分割和识别在本方向中，可以辅助判断哪些结构适合保留；语义类别本身不能判断物体当前是否在运动，在定位的时候是否使用作为参考；对于导航来说，可以在地图中标记出新的位置，有利于导航和抓取

根据如上，我提出核心问题：

**在动态环境下，怎样建立几何可信、保留有效静态约束的地图，并检验它能否让定位更准确、更连续？**

## 开放问题

**大方向：使用什么样的策略，能够实现变化环境中的可靠建图，进而实现可靠定位。**

**小问题1：在给定多帧扫描和建图位姿的条件下，如何删除动态障碍物残影，同时保留静态结构；这种地图改善在什么污染和几何条件下，能够降低独立定位的误差？**

**小问题2：如何在其他条件不变的情况下，减少机器人／传感器快速运动或旋转时产生的运动畸变** 。

**小问题3：如何识别特殊障碍物/应对退化场景如长廊，尽可能避免他对建图部分的影响，进而减少定位误差** 。

<a id="mapping-hypothesis-tests"></a>

## 假设

<!-- SIMPLE_HYPOTHESES_V2 -->

| 问题 | 一句话假设 | 对照方法 | 指标 |
| --- | --- | --- | --- |
| H1 / Q1 | 动态清图在保留静态结构的同时减少残影，并降低独立定位误差。 | Raw / SRRG | DA、SA、Eₘ、XY RMSE |
| H2 / Q2 | FAST-LIO去畸变能降低运动造成的地图误差，并提高独立定位精度。 | 点补偿关 / 开 | Eₘ、Cₘ、XYZ RMSE |
| H3 / Q3 | 长廊中增加雷达可见的非对称静态参照，能降低沿廊定位误差。 | 原长廊 / 加参照长廊 | Eₘ、SA、沿廊 RMSE |

目标：先检查地图是否改善，再检验同一定位器在独立B中的误差是否下降。

镜面识别与真实反射仍是Q3中待验证的部分，实物证据保留在首页开头。

<a id="hypothesis-math"></a>

### 数学表达

A用于建图，B是另一次采集；冻结A的地图后，用相同定位器处理B。$`j`$是对照方法，$`Z`$是扫描，$`T`$是传感器位姿，$`p^{\ast}`$是位置真值：

```math
M_j = \mathcal{B}_j\bigl(Z^A,\hat{T}_j^A\bigr)
```

```math
\hat{T}_{j,t}^B = \mathcal{L}\bigl(Z_{\leq t}^B,M_j\bigr)
```

```math
E_L(j) = \sqrt{\frac{1}{N}\sum_t\left\lVert\hat{p}_{j,t}^B-p_t^{B,\ast}\right\rVert^2}
```

```math
\Delta E_L = E_L(\mathrm{baseline})-E_L(\mathrm{method})
```

$`\Delta E_L\gt 0`$表示定位改善；地图误差$`E_M`$下降但$`\Delta E_L\leq 0`$时，只支持建图改善。下式是要检验的预测：

**H1**

```math
\mathrm{DA}_{\mathrm{SRRG}}\gt\mathrm{DA}_{\mathrm{Raw}},\qquad \mathrm{SA}_{\mathrm{SRRG}}\geq\mathrm{SA}_{\mathrm{Raw}}-\varepsilon
```

```math
E_M(\mathrm{SRRG})\lt E_M(\mathrm{Raw}),\qquad\Delta E_L\gt 0
```

**H2**

```math
p_i^{\mathrm{end}}=T(t_{\mathrm{end}})^{-1}T(t_i)p_i
```

```math
E_M(\mathrm{on})\lt E_M(\mathrm{off}),\qquad\Delta E_L\gt 0
```

**H3**

```math
E_{\parallel}=\sqrt{\frac{1}{N}\sum_t\left[u^{\mathsf{T}}\left(\hat{p}_t-p_t^{\ast}\right)\right]^2}
```

```math
E_{\parallel}(\mathrm{landmark})\lt E_{\parallel}(\mathrm{original})
```

$`\varepsilon=1`$个百分点为本轮静态损失容差；$`u`$为走廊方向。SRRG本轮是端到端对照，包含位姿优化与地图维护；给定相同位姿的纯删除消融仍待做。真值仅用于评分。

<a id="hypothesis-pseudocode"></a>

### 伪代码

```text
for scene in [static, dynamic, motion, corridor, corridor_landmarks]:
    controls = methods_for(scene)
    A, maps = record_A_and_build_maps(scene, controls)
    map_metrics = score_and_freeze(maps)
    B = record_new_localization_session(scene)
    poses = same_localizer_for_all_maps(B, maps)
    report(map_metrics, score_on_common_times(poses, B.truth))
    save_native_recordings_and_input_hashes()
compare_corridor_variants_on_common_elapsed_times()
```

H3分别采集原长廊与加参照场景的A/B，保持路线、速度、初始偏移和定位参数相同。

[实验与新录像](#practice-index)

## 相关工作

<!-- HOME_RELATED_TABLE -->
按算法类型排列；GIF可直接查看，点击可播放完整视频。适用方向列保留空白，供后续填写。各行数据协议不同，不跨数据集排名。

| 方法／算法类型 | 原库复现GIF／原文点云图 | 评价指标与本次范围 | 适用方向 |
| --- | --- | --- | --- |
| <a id="related-fast_lio"></a>[FAST-LIO / FAST-LIO2](papers/fast_lio.zh-CN.md) | <img src="assets/related/20261016-pointcloud/fastlio2-fig12.png" width="280" alt="FAST-LIO2 original Fig. 12: point-cloud map"> | 原文实验：**不复现**；原图与方法介绍，自有场景测试见Practice |  |
| <a id="related-srrg_mapper2d"></a>[SRRG / srrg_mapper2d](papers/srrg_mapper2d.zh-CN.md) | <img src="assets/related/20261016-pointcloud/srrg-fig7.png" width="280" alt="SRRG original Fig. 7: point-cloud map"> | 原文实验：**不复现**；原图与方法介绍，自有场景测试见Practice |  |
| <a id="related-dufomap"></a>[DUFOMap](papers/dufomap.md)<br>三维地图清理 | <a href="../results/reference/desktop-live-dufomap/execution.mp4"><img src="media/related-pointcloud/20261016/dufomap.gif" width="280" loading="lazy" alt="dufomap · 点云实录节选"></a><br>[点云实录节选](../results/reference/desktop-live-dufomap/execution.mp4) | SA 97.98% / DA 98.7%<br>KITTI-00 · 141 帧；清理有效<br>[记录](../results/reference/desktop-live-dufomap/record.json) |  |
| <a id="related-beautymap"></a>[BeautyMap](papers/beautymap.md)<br>三维离线地图清理 | <a href="../results/reference/desktop-live-beautymap/execution.mp4"><img src="media/related-pointcloud/20261016/beautymap.gif" width="280" loading="lazy" alt="beautymap · 点云实录节选"></a><br>[点云实录节选](../results/reference/desktop-live-beautymap/execution.mp4) | SA 96.95% / DA 98.34%<br>KITTI-00 · 141 帧；清理有效<br>[记录](../results/reference/desktop-live-beautymap/record.json) |  |
| <a id="related-ir-mcl"></a>[IR-MCL](papers/ir-mcl.md)<br>二维神经场定位 | <a href="../results/reference/desktop-live-ir-mcl/execution.mp4"><img src="media/related-pointcloud/20261016/ir-mcl.gif" width="280" loading="lazy" alt="ir-mcl · 点云实录节选"></a><br>[点云实录节选](../results/reference/desktop-live-ir-mcl/execution.mp4) | RMSE 5.31 cm / 1.07°<br>Bonn IPBLab Seq 1<br>[记录](../results/reference/desktop-live-ir-mcl/record.json) |  |
| <a id="related-adam-mcl"></a>[AdaM-MCL](papers/adam-mcl.md)<br>学习提议＋粒子定位 | <a href="../results/reference/desktop-adam-mcl/result.mp4"><img src="../results/reference/desktop-adam-mcl/result.gif" width="280" loading="lazy" alt="AdaM-MCL · 二维粒子结果回放"></a><br>二维粒子结果回放 | RMSE 32.23 格；自建128格地图、2432步训练；历史10轮持续收敛0/10，不能比较论文米制精度<br>[记录](../results/reference/desktop-adam-mcl/record.json) |  |
<!-- /HOME_RELATED_TABLE -->

SA／DA与定位RMSE的定义见[指标](#指标)。SRRG按二维观测支持评分，DUFOMap／BeautyMap按三维点评分；IR-MCL／AdaM-MCL不清理地图。

<details>
<summary>各论文的输入、处理流程与复现边界</summary>

<!-- HOME_RELATED_DETAILS -->
### DUFOMap — 在地图积分过程中去除动态点

**输入：**连续三维激光扫描与给定传感器位姿。**处理：**用扫描实际观测到的空闲空间判断过去的占据点是否为动态残留；八叉树累积证据，并为位姿不确定性留出裕量。**输出：**去除动态残留的点云地图。它本身不估计机器人位姿。[论文与复现范围](papers/dufomap.zh-CN.md)。

录像中灰色是保留点、红色是移除点、青色是当前扫描。重点看后续扫描如何改变旧点的保留决策。KITTI-00，141 帧；SA 97.98%／DA 98.70%。SA 是静态点保留率，DA 是动态点删除率，都不是定位误差。

[Live MP4](../results/reference/desktop-live-dufomap/execution.mp4) · [record](../results/reference/desktop-live-dufomap/record.json)

### BeautyMap — 清理已有点云地图

**输入：**完整累积三维地图、扫描与给定位姿。**处理：**作者占据表示检测不一致结构，再通过静态结构恢复步骤减少误删。**输出：**清理后的参考地图。这是离线地图清理，录像展示它正在计算，开始时完整输入地图已经存在。[论文与复现范围](papers/beautymap.zh-CN.md)。

灰色／红色分别表示保留／移除。重点看累计移除决策，不把初始完整地图理解成在线 SLAM 的建图结果。KITTI-00，141 帧；SA 96.95%／DA 98.34%。更干净的地图是否改善定位，需要另做下游测试。

[Live MP4](../results/reference/desktop-live-beautymap/execution.mp4) · [record](../results/reference/desktop-live-beautymap/record.json)

### IR-MCL — 用神经观测模型定位

**输入：**预训练神经占据场、真实二维扫描与运动输入。**处理：**每个粒子代表一个候选机器人位姿；神经场在该位姿渲染预测扫描，与真实扫描比较后更新权重，再重采样。**输出：**估计位姿与粒子分布。[论文、原库与评分协议](papers/ir-mcl.zh-CN.md)。

RViz 中地图提供环境参照，黄色粒子是候选位置，蓝色是显示估计，绿色是真值轨迹。重点看粒子是否集中，以及估计是否贴近参照。显示用加权粒子均值，评分用原生保存轨迹。Bonn IPBLab Seq 1：处理 1543／评分 1354 帧，本次 RMSE 5.31 cm／1.07°。这次作者数据运行与接入 Gazebo 是两项不同实验。

[Live MP4](../results/reference/desktop-live-ir-mcl/execution.mp4) · [record](../results/reference/desktop-live-ir-mcl/record.json)

### AdaM-MCL — 学习式候选位置与粒子跟踪混合

**输入：**地图、激光观测、运动输入与训练好的候选位姿模型。**处理：**学习模型提出候选位置，自适应混合机制将其与常规粒子跟踪结合。**输出：**位姿分布，可包含绑架事件后的新位置假设。[论文与范围限制](papers/adam-mcl.zh-CN.md)。

当前使用自建 128 格地图、2432 步权重，123 次滤波更新，RMSE 32.23 格。未获取论文发布数据与权重，因此这是受限原库流程执行；没有复现论文的米制精度，也没有证明成功自恢复。[评分更正](../results/reference/adam-mcl/ERRATUM.md)。

[Live MP4](../results/reference/desktop-adam-mcl/execution.mp4) · [record](../results/reference/desktop-adam-mcl/record.json)

**保存结果回放**

[Result MP4](../results/reference/desktop-adam-mcl/result.mp4)

<!-- SRRG_RELATED -->
### SRRG · 原生二维动态环境建图

**原文实验：不复现。** 使用论文原图介绍方法；自有Gazebo场景中的作者代码测试独立列在[Practice](#experiment-h1)，不等于复现LCAS／MIT Stata长期多会话实验。

![SRRG · original point-cloud Fig. 7](assets/related/20261016-pointcloud/srrg-fig7.png)

来源：Lázaro等，*Efficient Long-term Mapping in Dynamic Environments*，IROS 2018，图7，第6页。[原文](https://iris.uniroma1.it/handle/11573/1340118) · [作者代码](https://gitlab.com/srrg-software/srrg_mapper2d)。二维点云和里程计经过配准、局部图维护与位姿图优化；对应H1的动态地图维护，也需要检查H3中的几何约束。
<!-- /SRRG_RELATED -->

<!-- FASTLIO_RELATED -->
### FAST-LIO / FAST-LIO2 · LiDAR–IMU运动估计与点补偿

**原文实验：不复现。** 下面是FAST-LIO2论文的原图。本文的FAST-LIO实现测试使用官方ROS2分支、FAST-LIO2直接配准路径；同名软件包与初版论文需要区分。自有场景消融见[新假设实验](#experiment-h2)。

![FAST-LIO2 · original point-cloud Fig. 12](assets/related/20261016-pointcloud/fastlio2-fig12.png)

来源：Xu等，*FAST-LIO2: Fast Direct LiDAR-inertial Odometry*，图12，第16页。[FAST-LIO论文](https://arxiv.org/abs/2010.08196) · [FAST-LIO2论文](https://arxiv.org/abs/2107.06829) · [官方ROS2代码](https://github.com/hku-mars/FAST_LIO/tree/ROS2)。IMU传播与逐点反向补偿对应H2；ikd-Tree维护的是增量空间数据结构，不能直接当成动态物体去除或镜面检测器。
<!-- /FASTLIO_RELATED -->
<!-- /HOME_RELATED_DETAILS -->

</details>

## 指标

| 指标 | 一句话说明 |
| --- | --- |
| DA ↑ / SA ↑ | 动态残影删除比例 / 静态保留比例；SRRG按空间支持覆盖计。 |
| Eₘ ↓ | 地图点到参考几何的距离RMSE，cm；2D用已观测静态支持，3D用真实表面。 |
| Cₘ ↑ | 被地图覆盖的已观测静态参照比例。 |
| XY / XYZ / 沿廊 RMSE ↓ | 二维 / 三维 / 沿走廊方向的位置误差，cm。 |
| 角度RMSE ↓ | 二维偏航或三维旋转误差，度。 |
| P95 ↓ / N / 更新覆盖 ↑ | 位置误差95分位 / 有效样本数 / 评分网格上新鲜输出比例。 |
| N/A | 不适用；没有动态物体时不计算DA。 |

### 实验证据

| DUFOMap · KITTI-00 · 指标 | 论文 % | 复现 % |
| --- | ---: | ---: |
| SA | 97.96 | 97.9635 |
| DA | 98.72 | 98.7196 |
| AA | 98.34 | 98.3408 |

| BeautyMap · KITTI-02 · 指标 | 论文 % | 复现 % |
| --- | ---: | ---: |
| SA | 83.40 | 83.3978 |
| DA | 82.41 | 82.4092 |
| HA | 82.90 | 82.9006 |

| IR-MCL · 指标 | 论文 Seq 1 | 复现 |
| --- | ---: | ---: |
| 位置 RMSE（cm） | 5.13 | 5.32 |
| 偏航 RMSE（度） | 1.05 | 1.07 |
| 位置 < 5 cm（%） | 63.15 | 61.74 |
| 位置 < 10 cm（%） | 97.27 | 96.01 |
| 位置 < 20 cm（%） | 100.00 | 100.00 |
| 偏航 < 0.5°（%） | 47.12 | 47.64 |
| 偏航 < 1°（%） | 74.59 | 75.85 |
| 偏航 < 2°（%） | 94.24 | 93.57 |

| AdaM-MCL · 指标 | 论文表 II | 本次复现 |
| --- | ---: | ---: |
| 全局定位 $E_{pos}$ | 0.153 m | 未做数值对照 |
| 绑架 $E_{pos}$ | 0.128 m | 未做数值对照 |

## 实践

<!-- HOME_EXPERIMENTS_V2 -->
<!-- SIMPLE_HYPOTHESES_V2 -->

<a id="practice-index"></a>

### 目录

| 序号 | 实验 | 下属实验（直接点击） |
| --- | --- | --- |
| 0 | [实验设置](#practice-setup) | [URDF](#robot-urdf) · [指标](#practice-metrics) |
| 1 | [H1 · 动态清图](#experiment-h1) | [静态A](#h1-static-a) / [B](#h1-static-b) · [动态A](#h1-dynamic-a) / [B](#h1-dynamic-b) |
| 2 | [H2 · FAST-LIO](#experiment-h2) | [A](#h2-a) · [静止](#h2-stationary) / [慢转](#h2-slow) / [快转](#h2-fast) / [平移](#h2-translation) · [B](#h2-b) |
| 3 | [H3 · 长廊参照](#experiment-h3) | [原场景A](#h3-original-a) / [B](#h3-original-b) · [加参照A](#h3-landmark-a) / [B](#h3-landmark-b) · [配对指标](#h3-scores) |
| 4 | [三维原测试](#baseline-3d) | [静态](#scene-static-3d) · [动态](#scene-dynamic-3d) · [长廊](#scene-corridor-3d) · [结构变化](#scene-change-3d) |
| 5 | [补充实验](#practice-appendix) | [SRRG](#supp-srrg) · [点云回放](#map-review-3d) · [NDT/GICP](#supp-registrations) · [采集](#supp-acquisition) · [失败记录](#srrg-diagnostics) |


<a id="practice-setup"></a>

### 实验设置

| 项目 | 设置 |
| --- | --- |
| 平台 | Windows / WSL2 · ROS 2 Jazzy · Gazebo Harmonic · RViz2 |
| 机器人 | Sim2Real全向轮底盘；URDF截图见下。 |
| 二维设备 | 720束二维激光雷达＋轮式里程计。 |
| 三维设备 | 16×720三维激光雷达；FAST-LIO组另加200 Hz IMU。 |


<a id="robot-urdf"></a>

<img src="media/robot/20261016/urdf.png" width="560" alt="Actual robot URDF rendered in RViz">

<a id="practice-metrics"></a>

### 指标说明

[简短定义见指标表](#指标)

本轮定位按共同10 Hz时间点评分，预热5秒，最新输出最多滞后0.15秒；更新覆盖不是失锁率。每组1轮。

<a id="experiment-h1"></a>

### H1 · 动态清图 → 独立定位

| 场景 | 只改变 | 固定 |
| --- | --- | --- |
| 静态对照 / 运动障碍物 | Raw / SRRG | 同次A扫描、同一B扫描、AMCL参数与初始偏移 |


<a id="h1-static-a"></a>

#### 静态 · A

| 方法 | DA | SA | Eₘ / cm |
| --- | --- | --- | --- |
| Raw | N/A | 100.00% | 3.79 |
| SRRG | N/A | 100.00% | 2.57 |


[记录](../results/reference/direction-20261016-v2/2d-A-static/record.json)

| A · Raw / SRRG |
| --- |
| <a href="../results/reference/direction-20261016-v2/2d-A-static/execution.mp4"><img src="../results/reference/direction-20261016-v2/2d-A-static/execution.gif" width="340" loading="lazy" alt="A · Raw / SRRG"></a> |


**分析：**
<!-- PRACTICE_ANALYSIS:h1-static-a -->

<!-- /PRACTICE_ANALYSIS:h1-static-a -->

[↑ 目录](#practice-index)

<a id="h1-static-b"></a>

#### 静态 · B

| 地图 | XY RMSE / cm | yaw / ° | P95 / cm | 更新覆盖 | N |
| --- | --- | --- | --- | --- | --- |
| Raw | 5.03 | 2.88 | 8.76 | 41.43% | 278 |
| SRRG | 5.84 | 2.91 | 9.58 | 41.43% | 278 |


[评分](../results/reference/direction-20261016-v2/2d-static/time-grid-score.json)

| Raw | SRRG |
| --- | --- |
| <a href="../results/reference/direction-20261016-v2/2d-static/executions/raw.mp4"><img src="../results/reference/direction-20261016-v2/2d-static/executions/raw.gif" width="340" loading="lazy" alt="Raw"></a> | <a href="../results/reference/direction-20261016-v2/2d-static/executions/srrg.mp4"><img src="../results/reference/direction-20261016-v2/2d-static/executions/srrg.gif" width="340" loading="lazy" alt="SRRG"></a> |


**分析：**
<!-- PRACTICE_ANALYSIS:h1-static-b -->

<!-- /PRACTICE_ANALYSIS:h1-static-b -->

[↑ 目录](#practice-index)

<a id="h1-dynamic-a"></a>

#### 动态 · A

| 方法 | DA | SA | Eₘ / cm |
| --- | --- | --- | --- |
| Raw | 0.00% | 100.00% | 49.05 |
| SRRG | 36.94% | 99.84% | 15.45 |


[记录](../results/reference/direction-20261016-v2/2d-A-dynamic/record.json)

| A · Raw / SRRG |
| --- |
| <a href="../results/reference/direction-20261016-v2/2d-A-dynamic/execution.mp4"><img src="../results/reference/direction-20261016-v2/2d-A-dynamic/execution.gif" width="340" loading="lazy" alt="A · Raw / SRRG"></a> |


**分析：**
<!-- PRACTICE_ANALYSIS:h1-dynamic-a -->

<!-- /PRACTICE_ANALYSIS:h1-dynamic-a -->

[↑ 目录](#practice-index)

<a id="h1-dynamic-b"></a>

#### 动态 · B

| 地图 | XY RMSE / cm | yaw / ° | P95 / cm | 更新覆盖 | N |
| --- | --- | --- | --- | --- | --- |
| Raw | 5.53 | 0.76 | 7.92 | 66.77% | 448 |
| SRRG | 5.13 | 0.70 | 7.32 | 66.77% | 448 |


[评分](../results/reference/direction-20261016-v2/2d-dynamic/time-grid-score.json)

| Raw | SRRG |
| --- | --- |
| <a href="../results/reference/direction-20261016-v2/2d-dynamic/executions/raw.mp4"><img src="../results/reference/direction-20261016-v2/2d-dynamic/executions/raw.gif" width="340" loading="lazy" alt="Raw"></a> | <a href="../results/reference/direction-20261016-v2/2d-dynamic/executions/srrg.mp4"><img src="../results/reference/direction-20261016-v2/2d-dynamic/executions/srrg.gif" width="340" loading="lazy" alt="SRRG"></a> |


**分析：**
<!-- PRACTICE_ANALYSIS:h1-dynamic-b -->

<!-- /PRACTICE_ANALYSIS:h1-dynamic-b -->

[↑ 目录](#practice-index)

<a id="experiment-h2"></a>

### H2 · FAST-LIO 运动畸变

| 场景 | 只改变 | 固定 |
| --- | --- | --- |
| 现有静态场景；静止→慢转→快转→平移 | FAST-LIO点补偿关 / 开 | 相同扫描、逐点时间、IMU、状态预测；B使用相同GICP |


三帧真实扫描各取120°扇区组成0.2秒扫描；这是受控分组采样，不是商用雷达扫描模式。

<a id="h2-a"></a>

#### A · 建图与运动阶段

| 点补偿 | Eₘ / cm | Cₘ |
| --- | --- | --- |
| 关 | 13.49 | 82.28% |
| 开 | 4.61 | 94.38% |


[评分](../results/reference/direction-20261016-v2/fastlio-maps/score.json)

| A · FAST-LIO on / off |
| --- |
| <a href="../results/reference/direction-20261016-v2/fastlio-motion/execution.mp4"><img src="../results/reference/direction-20261016-v2/fastlio-motion/execution.gif" width="340" loading="lazy" alt="A · FAST-LIO on / off"></a> |


<a id="h2-stationary"></a>

##### 静止

| 点补偿 | 阶段时间 | A里程计XYZ RMSE / cm | 旋转 / ° | N |
| --- | --- | --- | --- | --- |
| 关 | 0–7 s | 0.12 | 0.02 | 7 |
| 开 | 0–7 s | 0.15 | 0.03 | 7 |


<a id="h2-slow"></a>

##### 慢转

| 点补偿 | 阶段时间 | A里程计XYZ RMSE / cm | 旋转 / ° | N |
| --- | --- | --- | --- | --- |
| 关 | 7–15 s | 1.30 | 0.95 | 26 |
| 开 | 7–15 s | 0.42 | 0.14 | 26 |


<a id="h2-fast"></a>

##### 快转

| 点补偿 | 阶段时间 | A里程计XYZ RMSE / cm | 旋转 / ° | N |
| --- | --- | --- | --- | --- |
| 关 | 15–31 s | 3.18 | 4.35 | 54 |
| 开 | 15–31 s | 0.79 | 0.26 | 54 |


<a id="h2-translation"></a>

##### 平移

| 点补偿 | 阶段时间 | A里程计XYZ RMSE / cm | 旋转 / ° | N |
| --- | --- | --- | --- | --- |
| 关 | 31–39 s | 5.33 | 3.68 | 26 |
| 开 | 31–39 s | 1.45 | 0.25 | 26 |


**分析：**
<!-- PRACTICE_ANALYSIS:h2-a -->

<!-- /PRACTICE_ANALYSIS:h2-a -->

[↑ 目录](#practice-index)

<a id="h2-b"></a>

#### B · 冻结地图后GICP定位

| A点补偿 | XYZ RMSE / cm | 旋转 / ° | P95 / cm | N |
| --- | --- | --- | --- | --- |
| 关 | 14.03 | 3.62 | 19.68 | 601 |
| 开 | 2.04 | 0.87 | 4.35 | 601 |


[评分](../results/reference/direction-20261016-v2/fastlio-B/score-3d.json)

| Off map | On map |
| --- | --- |
| <a href="../results/reference/direction-20261016-v2/fastlio-B/executions/no_deskew.mp4"><img src="../results/reference/direction-20261016-v2/fastlio-B/executions/no_deskew.gif" width="340" loading="lazy" alt="Off map"></a> | <a href="../results/reference/direction-20261016-v2/fastlio-B/executions/deskew.mp4"><img src="../results/reference/direction-20261016-v2/fastlio-B/executions/deskew.gif" width="340" loading="lazy" alt="On map"></a> |


**分析：**
<!-- PRACTICE_ANALYSIS:h2-b -->

<!-- /PRACTICE_ANALYSIS:h2-b -->

[↑ 目录](#practice-index)

<a id="experiment-h3"></a>

### H3 · 长廊静态参照

| 场景 | 只改变 | 固定 |
| --- | --- | --- |
| 原长廊 / 加参照长廊 | 侧壁两处非对称0.24×0.24×0.9 m实体 | SRRG、AMCL、路线、初始偏移；A/B前50秒为72束、240°、3.5 m，随后恢复 |


<a id="h3-original-a"></a>

#### 原长廊 · A

| 方法 | DA | SA | Eₘ / cm |
| --- | --- | --- | --- |
| Raw | N/A | 82.63% | 16.67 |
| SRRG | N/A | 82.05% | 14.93 |


[记录](../results/reference/direction-20261016-v2/2d-A-corridor/record.json)

| A · Raw / SRRG |
| --- |
| <a href="../results/reference/direction-20261016-v2/2d-A-corridor/execution.mp4"><img src="../results/reference/direction-20261016-v2/2d-A-corridor/execution.gif" width="340" loading="lazy" alt="A · Raw / SRRG"></a> |


**分析：**
<!-- PRACTICE_ANALYSIS:h3-original-a -->

<!-- /PRACTICE_ANALYSIS:h3-original-a -->

[↑ 目录](#practice-index)

<a id="h3-original-b"></a>

#### 原长廊 · B

| 地图 | XY RMSE / cm | yaw / ° | P95 / cm | 更新覆盖 | N |
| --- | --- | --- | --- | --- | --- |
| Raw | 113.30 | 1.38 | 128.91 | 88.08% | 591 |
| SRRG | 102.72 | 1.08 | 121.25 | 88.08% | 591 |


[评分](../results/reference/direction-20261016-v2/2d-corridor/time-grid-score.json)

| Raw | SRRG |
| --- | --- |
| <a href="../results/reference/direction-20261016-v2/2d-corridor/executions/degraded_raw.mp4"><img src="../results/reference/direction-20261016-v2/2d-corridor/executions/degraded_raw.gif" width="340" loading="lazy" alt="Raw"></a> | <a href="../results/reference/direction-20261016-v2/2d-corridor/executions/degraded_srrg.mp4"><img src="../results/reference/direction-20261016-v2/2d-corridor/executions/degraded_srrg.gif" width="340" loading="lazy" alt="SRRG"></a> |


**分析：**
<!-- PRACTICE_ANALYSIS:h3-original-b -->

<!-- /PRACTICE_ANALYSIS:h3-original-b -->

[↑ 目录](#practice-index)

<a id="h3-landmark-a"></a>

#### 加参照长廊 · A

| 方法 | DA | SA | Eₘ / cm |
| --- | --- | --- | --- |
| Raw | N/A | 99.86% | 27.58 |
| SRRG | N/A | 99.01% | 21.06 |


[记录](../results/reference/direction-20261016-v2/2d-A-landmark-corridor/record.json)

| A · Raw / SRRG |
| --- |
| <a href="../results/reference/direction-20261016-v2/2d-A-landmark-corridor/execution.mp4"><img src="../results/reference/direction-20261016-v2/2d-A-landmark-corridor/execution.gif" width="340" loading="lazy" alt="A · Raw / SRRG"></a> |


**分析：**
<!-- PRACTICE_ANALYSIS:h3-landmark-a -->

<!-- /PRACTICE_ANALYSIS:h3-landmark-a -->

[↑ 目录](#practice-index)

<a id="h3-landmark-b"></a>

#### 加参照长廊 · B

| 地图 | XY RMSE / cm | yaw / ° | P95 / cm | 更新覆盖 | N |
| --- | --- | --- | --- | --- | --- |
| Raw | 69.61 | 1.52 | 99.27 | 87.93% | 590 |
| SRRG | 54.03 | 1.08 | 94.32 | 87.93% | 590 |


[评分](../results/reference/direction-20261016-v2/2d-landmark-corridor/time-grid-score.json)

| Raw | SRRG |
| --- | --- |
| <a href="../results/reference/direction-20261016-v2/2d-landmark-corridor/executions/degraded_raw.mp4"><img src="../results/reference/direction-20261016-v2/2d-landmark-corridor/executions/degraded_raw.gif" width="340" loading="lazy" alt="Raw"></a> | <a href="../results/reference/direction-20261016-v2/2d-landmark-corridor/executions/degraded_srrg.mp4"><img src="../results/reference/direction-20261016-v2/2d-landmark-corridor/executions/degraded_srrg.gif" width="340" loading="lazy" alt="SRRG"></a> |


**分析：**
<!-- PRACTICE_ANALYSIS:h3-landmark-b -->

<!-- /PRACTICE_ANALYSIS:h3-landmark-b -->

[↑ 目录](#practice-index)

<a id="h3-scores"></a>

#### 前50秒配对指标

| SRRG地图 | 沿廊RMSE / cm | 横向RMSE / cm | N |
| --- | --- | --- | --- |
| 原长廊 | 99.84 | 3.83 | 373 |
| 加参照 | 63.25 | 6.34 | 373 |


[共同时间评分](../results/reference/direction-20261016-v2/corridor-comparison.json)

**分析：**
<!-- PRACTICE_ANALYSIS:h3-scores -->

<!-- /PRACTICE_ANALYSIS:h3-scores -->

[↑ 目录](#practice-index)

<a id="baseline-3d"></a>

### 三维原测试

保留原Raw／DUFOMap／BeautyMap及GICP结果；各表的评分窗口见记录。

<a id="scene-static-3d"></a>

#### 静态 · 3D

<!-- HOME_EXPERIMENT_TABLE -->
| Map | DA | SA | XYZ RMSE / cm | 旋转 RMSE / ° | P95 / cm | N |
| --- | --- | --- | --- | --- | --- | --- |
| Raw | N/A | 100% | 0.95 | 0.15 | 1.47 | 845 |
| DUFOMap | N/A | 99.999% | 0.99 | 0.16 | 1.47 | 835 |
| BeautyMap | N/A | 83.33% | 1.07 | 0.17 | 1.44 | 917 |
<!-- /HOME_EXPERIMENT_TABLE -->

[记录](../results/reference/robot-3d-static/record.json)

| Raw | DUFOMap | BeautyMap |
| --- | --- | --- |
| <a href="../results/reference/robot-3d-static/executions/raw.mp4"><img src="../results/reference/robot-3d-static/executions/raw.gif" width="340" loading="lazy" alt="Raw"></a> | <a href="../results/reference/robot-3d-static/executions/dufomap.mp4"><img src="../results/reference/robot-3d-static/executions/dufomap.gif" width="340" loading="lazy" alt="DUFOMap"></a> | <a href="../results/reference/robot-3d-static/executions/beautymap.mp4"><img src="../results/reference/robot-3d-static/executions/beautymap.gif" width="340" loading="lazy" alt="BeautyMap"></a> |


**分析：**
<!-- PRACTICE_ANALYSIS:scene-static-3d -->

<!-- /PRACTICE_ANALYSIS:scene-static-3d -->

[↑ 目录](#practice-index)

<a id="scene-dynamic-3d"></a>

#### 动态 · 3D

<!-- HOME_EXPERIMENT_TABLE -->
| Map | DA | SA | XYZ RMSE / cm | 旋转 RMSE / ° | P95 / cm | N |
| --- | --- | --- | --- | --- | --- | --- |
| Raw | 0% | 100% | 0.98 | 0.17 | 1.96 | 967 |
| DUFOMap | 46.59% | 99.998% | 0.98 | 0.18 | 2.00 | 963 |
| BeautyMap | 74.36% | 81.15% | 1.04 | 0.17 | 1.99 | 1022 |
<!-- /HOME_EXPERIMENT_TABLE -->

[记录](../results/reference/robot-3d-dynamic/record.json)

| Raw | DUFOMap | BeautyMap |
| --- | --- | --- |
| <a href="../results/reference/robot-3d-dynamic/executions/raw.mp4"><img src="../results/reference/robot-3d-dynamic/executions/raw.gif" width="340" loading="lazy" alt="Raw"></a> | <a href="../results/reference/robot-3d-dynamic/executions/dufomap.mp4"><img src="../results/reference/robot-3d-dynamic/executions/dufomap.gif" width="340" loading="lazy" alt="DUFOMap"></a> | <a href="../results/reference/robot-3d-dynamic/executions/beautymap.mp4"><img src="../results/reference/robot-3d-dynamic/executions/beautymap.gif" width="340" loading="lazy" alt="BeautyMap"></a> |


**分析：**
<!-- PRACTICE_ANALYSIS:scene-dynamic-3d -->

<!-- /PRACTICE_ANALYSIS:scene-dynamic-3d -->

[↑ 目录](#practice-index)

<a id="scene-corridor-3d"></a>

#### 长廊 · 3D

<!-- HOME_EXPERIMENT_TABLE -->
| Map | DA | SA | XYZ RMSE / cm | 旋转 RMSE / ° | P95 / cm | N |
| --- | --- | --- | --- | --- | --- | --- |
| Raw | N/A | 100% | 474.38 | 0.53 | 828.94 | 530 |
| DUFOMap | N/A | 100% | 497.05 | 0.48 | 814.15 | 599 |
| BeautyMap | N/A | 99.9% | 592.00 | 49.16 | 917.05 | 655 |
<!-- /HOME_EXPERIMENT_TABLE -->

[记录](../results/reference/robot-3d-corridor/record.json)

| Raw | DUFOMap | BeautyMap |
| --- | --- | --- |
| <a href="../results/reference/robot-3d-corridor/executions/raw.mp4"><img src="../results/reference/robot-3d-corridor/executions/raw.gif" width="340" loading="lazy" alt="Raw"></a> | <a href="../results/reference/robot-3d-corridor/executions/dufomap.mp4"><img src="../results/reference/robot-3d-corridor/executions/dufomap.gif" width="340" loading="lazy" alt="DUFOMap"></a> | <a href="../results/reference/robot-3d-corridor/executions/beautymap.mp4"><img src="../results/reference/robot-3d-corridor/executions/beautymap.gif" width="340" loading="lazy" alt="BeautyMap"></a> |


**分析：**
<!-- PRACTICE_ANALYSIS:scene-corridor-3d -->

<!-- /PRACTICE_ANALYSIS:scene-corridor-3d -->

[↑ 目录](#practice-index)

<a id="scene-change-3d"></a>

#### 结构变化 · 3D

<!-- HOME_EXPERIMENT_TABLE -->
| Map | DA | SA | XYZ RMSE / cm | 旋转 RMSE / ° | P95 / cm | N |
| --- | --- | --- | --- | --- | --- | --- |
| Raw | N/A | 100% | 0.93 | 0.17 | 1.45 | 859 |
| DUFOMap | N/A | 99.999% | 1.01 | 0.19 | 1.45 | 860 |
| BeautyMap | N/A | 83.33% | 1.04 | 0.17 | 1.46 | 945 |
<!-- /HOME_EXPERIMENT_TABLE -->

[记录](../results/reference/robot-3d-large-change/record.json)

| Raw | DUFOMap | BeautyMap |
| --- | --- | --- |
| <a href="../results/reference/robot-3d-large-change/executions/raw.mp4"><img src="../results/reference/robot-3d-large-change/executions/raw.gif" width="340" loading="lazy" alt="Raw"></a> | <a href="../results/reference/robot-3d-large-change/executions/dufomap.mp4"><img src="../results/reference/robot-3d-large-change/executions/dufomap.gif" width="340" loading="lazy" alt="DUFOMap"></a> | <a href="../results/reference/robot-3d-large-change/executions/beautymap.mp4"><img src="../results/reference/robot-3d-large-change/executions/beautymap.gif" width="340" loading="lazy" alt="BeautyMap"></a> |


**分析：**
<!-- PRACTICE_ANALYSIS:scene-change-3d -->

<!-- /PRACTICE_ANALYSIS:scene-change-3d -->

[↑ 目录](#practice-index)

<a id="practice-appendix"></a>

### 补充实验

<a id="supp-srrg"></a>

#### SRRG · 持久结构变化

| 方法 | DA | SA | 新增结构覆盖 | 独立B |
| --- | --- | --- | --- | --- |
| Raw | N/A | 100.00% | 100.00% | 未测 |
| SRRG | N/A | 99.71% | 98.90% | 未测 |


[记录](../results/reference/srrg-2d-large-change/record.json)

| SRRG changed-world A |
| --- |
| <a href="../results/reference/srrg-2d-large-change/execution.mp4"><img src="../results/reference/srrg-2d-large-change/execution.gif" width="340" loading="lazy" alt="SRRG changed-world A"></a> |


**分析：**
<!-- PRACTICE_ANALYSIS:srrg-large-change-2d -->

<!-- /PRACTICE_ANALYSIS:srrg-large-change-2d -->

[↑ 目录](#practice-index)

<a id="map-review-3d"></a>

#### 保存点云回放

| 已保存结果，无新推理 |
| --- |
| <a href="../results/reference/robot-3d-map-review-v2/execution.mp4"><img src="../results/reference/robot-3d-map-review-v2/execution.gif" width="340" loading="lazy" alt="已保存结果，无新推理"></a> |


<a id="supp-registrations"></a>

#### Raw · NDT / GICP

| 方法 | XY RMSE / cm | yaw / ° | 证据 |
| --- | --- | --- | --- |
| NDT initial | 34.43 | 0.15 | [记录](../results/reference/robot-ndt-static-initial/record.json) |
| NDT | 0.93 | 0.17 | [记录](../results/reference/robot-ndt-static/record.json) |
| GICP | 1.09 | 0.16 | [记录](../results/reference/robot-gicp-static/record.json) |


<a id="supp-acquisition"></a>

#### 补充采集与定位

| 场景 | 方法 | 扫描帧数 | 记录 | 录制 |
| --- | --- | --- | --- | --- |
| 静态 | slam_toolbox | 54 | [记录](../results/reference/robot-supp-static/record.json) | [MP4](../results/reference/robot-supp-static/execution.mp4) |
| 动态 | slam_toolbox | 55 | [记录](../results/reference/robot-supp-dynamic/record.json) | [MP4](../results/reference/robot-supp-dynamic/execution.mp4) |
| 结构变化 | AMCL | — | [记录](../results/reference/robot-supp-large-change/record.json) | [MP4](../results/reference/robot-supp-large-change/execution.mp4) |


<a id="srrg-diagnostics"></a>

#### SRRG失败记录

| 环节 | 状态 | 记录 | 录制 |
| --- | --- | --- | --- |
| Eigen ABI | diagnostic_failed | [记录](../results/reference/srrg-diagnostic-20261015-025711-mapping-srrg-static-dd423d/record.json) | [MP4](../results/reference/srrg-diagnostic-20261015-025711-mapping-srrg-static-dd423d/execution.mp4) |
| stdout | diagnostic_failed | [记录](../results/reference/srrg-diagnostic-20261015-030327-mapping-srrg-static-a275d3/record.json) | [MP4](../results/reference/srrg-diagnostic-20261015-030327-mapping-srrg-static-a275d3/execution.mp4) |
| g2o | diagnostic_failed | [记录](../results/reference/srrg-diagnostic-20261015-030729-mapping-srrg-dynamic-14123d/record.json) | [MP4](../results/reference/srrg-diagnostic-20261015-030729-mapping-srrg-dynamic-14123d/execution.mp4) |


[↑ 目录](#practice-index)

## 分支

| 分支 | 用途 |
| --- | --- |
| main | 提交展示：动态环境鲁棒定位主线、按范围记录的建图／定位复现，以及候选自恢复实验。 |
| [reproduce/author-originals](https://github.com/p20030920p/SLAM_Learning/tree/reproduce/author-originals) | 作者原流程、论文表格评分与录制。 |
| [notes/personal-study-guide-20261008](https://github.com/p20030920p/SLAM_Learning/tree/notes/personal-study-guide-20261008) | 个人学习笔记与 `src/physical/` 实物实验，保留操作说明和失败记录。 |

[AI 使用](guides/DISCLOSURE.zh-CN.md) · [来源／许可](guides/ATTRIBUTION.zh-CN.md) · [引用](CITATION.cff) · [许可](../src/LICENSE)
