<div align="center">

# SLAM Learning

**动态环境中的鲁棒定位与 SLAM**

动态残影清理 · 静态结构保留 · 下游定位检验

[![CPU reproducibility](https://github.com/p20030920p/SLAM_Learning/actions/workflows/ci.yml/badge.svg)](https://github.com/p20030920p/SLAM_Learning/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.10-3776AB)](../src/pyproject.toml)

[English](../README.md) | 中文

[实物测试问题](#problem-getting-from-physical-test) · [方向分析](#方向分析) · [开放问题](#开放问题) · [假设](#假设) · [相关工作](#相关工作) · [指标](#指标)

[实践](#practice-index) · [Hypothesis test](#hypothesis-test-index)

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

<a id="physical-test-additional"></a>

### 新增实物测试

| 测试4 · `4.mp4` | 测试5 · `5.mp4` |
| --- | --- |
| <a href="media/physical-test/20261016-additional/4.gif"><img src="media/physical-test/20261016-additional/4.gif" width="420" loading="lazy" alt="实物测试4"></a> | <a href="media/physical-test/20261016-additional/5.gif"><img src="media/physical-test/20261016-additional/5.gif" width="420" loading="lazy" alt="实物测试5"></a> |
| **测试6 · `6.mp4`** | **测试7 · `7.mp4`** |
| <a href="media/physical-test/20261016-additional/6.gif"><img src="media/physical-test/20261016-additional/6.gif" width="420" loading="lazy" alt="实物测试6"></a> | <a href="media/physical-test/20261016-additional/7.gif"><img src="media/physical-test/20261016-additional/7.gif" width="420" loading="lazy" alt="实物测试7"></a> |

**分析：**
<!-- PHYSICAL_TEST_ANALYSIS:additional-four -->

<!-- /PHYSICAL_TEST_ANALYSIS:additional-four -->

<a id="physical-test-annotated-maps"></a>

### 建图结果标注图

<a href="media/physical-test/20261016-additional/annotated-maps.png"><img src="media/physical-test/20261016-additional/annotated-maps.png" width="653" alt="用户标注的四组实物测试建图结果"></a>

**分析：**
<!-- PHYSICAL_TEST_ANALYSIS:annotated-maps -->

<!-- /PHYSICAL_TEST_ANALYSIS:annotated-maps -->

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
<!-- OWN_HYPOTHESES_20261016 -->

| 问题 | 一句话假设 | 对照方法 | 指标 |
| --- | --- | --- | --- |
| H1 / Q1 | 重复命中＋自由射线确认能减少动态残影，并改善独立定位。 | 自写累积图 / 自写时序清图 | A：DA、SA；B：XY RMSE |
| H2 / Q2 | 用轮式里程计补偿点的采样时间差，能降低地图和独立定位误差。 | 自写补偿关 / 开 | A：Eₘ；B：XY RMSE |
| H3 / Q3 | 检测几何退化并按弱方向的约束贡献保留可靠静态结构，能减少沿廊定位误差。 | 自写统一阈值 / 自写退化感知清图 | A：额外保留格数；B：沿廊 RMSE |

三项干预均由本库实现；AMCL只作为统一的下游评分定位器。镜面识别仍待实物验证。

<a id="hypothesis-math"></a>

### 数学表达

A建图、B独立采集；冻结地图后，各对照使用相同B扫描、里程计和AMCL参数。

DA/SA只衡量清图的删除与保留比例，不代表几何精度或定位精度。B评估在既有地图中运动时的定位误差；本轮未测完整导航任务的到达效果。

```math
M_j=\mathcal{B}_j(Z^A,\hat T_{\rm odom}^A),\qquad \hat T_{j,t}^B=\mathcal{L}_{\rm AMCL}(Z_{\leq t}^B,M_j)
```

```math
E_L(j)=\sqrt{\frac{1}{N}\sum_t\lVert\hat p_{j,t}^B-p_t^{B,\ast}\rVert^2},\qquad \Delta E_L=E_L(\mathrm{baseline})-E_L(\mathrm{method})
```

**H1**

```math
H_c=\sum_b\mathbf{1}[\text{hit in time bin }b],\quad F_c=\sum_b\mathbf{1}[\text{free ray through }c],\quad K_c=\mathbf{1}[H_c\geq3\ \land\ H_c\geq1.5F_c]
```

```math
\mathrm{DA}_{\rm temporal}\gt\mathrm{DA}_{\rm raw},\quad\mathrm{SA}_{\rm temporal}\geq\mathrm{SA}_{\rm raw}-\varepsilon,\quad\Delta E_L\gt0
```

**H2**

```math
\tilde p_i=\hat T_{\rm odom}(t_e)^{-1}\hat T_{\rm odom}(t_i)p_i,\qquad E_M(\mathrm{on})\lt E_M(\mathrm{off}),\quad\Delta E_L\gt0
```

**H3**

解决方案：从已观测结构的局部法线估计约束较弱的方向；对该方向有约束贡献、至少两次命中且没有自由射线反证的结构，降低删除阈值。下面n为局部法线，G为平移约束的近似矩阵，v为最弱方向。


```math
G=\sum_{c\in C}n_cn_c^{\mathsf T},\quad v_{\min}=\mathrm{eigvec}_{\min}(G),\quad R_c=\mathbf{1}[H_c\geq2,\ F_c=0,\ |n_c^{\mathsf T}v_{\min}|\gt0.7]
```

```math
D=\mathbf{1}[\lambda_{\min}(G)\lt0.25\lambda_{\max}(G)],\qquad K_c^{\rm protected}=\mathbf{1}[(H_c\geq5\land H_c\geq1.5F_c)\lor(D=1\land R_c=1)]
```

```math
E_{\parallel}=\sqrt{\frac1N\sum_t[u^{\mathsf T}(\hat p_t-p_t^\ast)]^2},\qquad E_{\parallel}(\mathrm{protected})\lt E_{\parallel}(\mathrm{strict})
```

时间箱0.5秒；自由射线在回波前15 cm停止；静态损失容差ε＝1个百分点。H3保持走廊、路线、传感器和定位器相同，仅切换清图规则。它保护已有观测提供的约束；完全缺少沿廊信息时仍需额外观测，不能凭空恢复位置。真值仅用于评分。

<a id="hypothesis-pseudocode"></a>

### 伪代码

```text
for scene in [static, dynamic, motion, corridor]:
    A = acquire_scans_and_wheel_odometry(scene)
    for control in controls_for(scene):
        if H2: compensate_sector_points_by_interpolated_odometry()
        update_hit_and_free_evidence_in_distinct_time_bins()
        if H1: retain_temporally_supported_cells()
        if H3: protect_supported_normals_along_the_weak_direction()
        freeze_map(control)
    B = acquire_a_separate_session(scene)
    run_the_same_AMCL_on_all_frozen_maps(B)
    score_map_and_localization_on_common_times_using_truth_only_here()
```

[实现、实验与录像](#hypothesis-test-index)

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

**原文实验：不复现。** 使用论文原图介绍方法；自有Gazebo场景中的作者代码测试独立列在[Practice](#practice-srrg)，不等于复现LCAS／MIT Stata长期多会话实验。

![SRRG · original point-cloud Fig. 7](assets/related/20261016-pointcloud/srrg-fig7.png)

来源：Lázaro等，*Efficient Long-term Mapping in Dynamic Environments*，IROS 2018，图7，第6页。[原文](https://iris.uniroma1.it/handle/11573/1340118) · [作者代码](https://gitlab.com/srrg-software/srrg_mapper2d)。二维点云和里程计经过配准、局部图维护与位姿图优化；对应H1的动态地图维护，也需要检查H3中的几何约束。
<!-- /SRRG_RELATED -->

<!-- FASTLIO_RELATED -->
### FAST-LIO / FAST-LIO2 · LiDAR–IMU运动估计与点补偿

**原文实验：不复现。** 下面是FAST-LIO2论文的原图。本文的FAST-LIO实现测试使用官方ROS2分支、FAST-LIO2直接配准路径；同名软件包与初版论文需要区分。自有场景消融见[FAST-LIO Practice](#practice-fastlio)。

![FAST-LIO2 · original point-cloud Fig. 12](assets/related/20261016-pointcloud/fastlio2-fig12.png)

来源：Xu等，*FAST-LIO2: Fast Direct LiDAR-inertial Odometry*，图12，第16页。[FAST-LIO论文](https://arxiv.org/abs/2010.08196) · [FAST-LIO2论文](https://arxiv.org/abs/2107.06829) · [官方ROS2代码](https://github.com/hku-mars/FAST_LIO/tree/ROS2)。IMU传播与逐点反向补偿对应H2；ikd-Tree维护的是增量空间数据结构，不能直接当成动态物体去除或镜面检测器。
<!-- /FASTLIO_RELATED -->
<!-- /HOME_RELATED_DETAILS -->

</details>

## 指标

| 指标 | 一句话说明 |
| --- | --- |
| DA ↑ / SA ↑ | 仅评清图A：动态删除比例／静态保留比例；无动态时只列SA。二维按观测支持、三维按点评分。 |
| Eₘ ↓ | 去畸变A：地图点到静态参考几何的距离RMSE，cm。 |
| XY / XYZ RMSE ↓ | 冻结地图后的定位B：二维／三维位置误差，cm。 |
| 沿廊 RMSE ↓ | H3受限观测阶段：沿走廊方向的位置误差，cm。 |
| 角度RMSE ↓ | 仅在评价姿态时报告偏航或三维旋转误差，度；A里程计误差单独标注。 |

### 实验证据

| DUFOMap · KITTI-00 · 指标 | 论文 % | 复现 % |
| --- | ---: | ---: |
| SA | 97.96 | 97.9635 |
| DA | 98.72 | 98.7196 |

| BeautyMap · KITTI-02 · 指标 | 论文 % | 复现 % |
| --- | ---: | ---: |
| SA | 83.40 | 83.3978 |
| DA | 82.41 | 82.4092 |

| IR-MCL · 指标 | 论文 Seq 1 | 复现 |
| --- | ---: | ---: |
| 位置 RMSE（cm） | 5.13 | 5.32 |
| 偏航 RMSE（度） | 1.05 | 1.07 |

## 实践

这里实践Related works中的方法。A＝建图，B＝冻结地图后的另一次定位；点击目录中的A/B直接进入对应录像与指标。

<a id="practice-index"></a>

### 实验目录

| 编号 | 方法／下属实验 | 直达 |
| --- | --- | --- |
| P0 | 实验设置与设备 | [进入实验](#practice-setup) |
| P1.1 | SRRG · 静态 | [A](#h1-static-a) / [B](#h1-static-b) |
| P1.2 | SRRG · 动态 | [A](#h1-dynamic-a) / [B](#h1-dynamic-b) |
| P1.3 | SRRG · 原长廊 | [A](#h3-original-a) / [B](#h3-original-b) |
| P1.4 | SRRG · 结构变化 | [A](#supp-srrg) |
| P2.1 | FAST-LIO · 建图与运动阶段 | [A](#h2-a) / [静止](#h2-stationary) / [慢转](#h2-slow) / [快转](#h2-fast) / [平移](#h2-translation) |
| P2.2 | FAST-LIO · 冻结地图定位 | [B](#h2-b) |
| P3.0 | DUFOMap / BeautyMap · KITTI-00 | [清图实践](#practice-kitti) |
| P3.1 | DUFOMap / BeautyMap · 3D · 静态 | [A/B](#scene-static-3d) |
| P3.2 | DUFOMap / BeautyMap · 3D · 动态 | [A/B](#scene-dynamic-3d) |
| P3.3 | DUFOMap / BeautyMap · 3D · 长廊 | [A/B](#scene-corridor-3d) |
| P3.4 | DUFOMap / BeautyMap · 3D · 结构变化 | [A/B](#scene-change-3d) |
| P4 | IR-MCL · Bonn | [进入实验](#practice-irmcl) |
| P5 | AdaM-MCL | [进入实验](#practice-adam) |
| P6.1 | NDT / GICP | [进入实验](#supp-registrations) |
| P6.2 | slam_toolbox / AMCL | [进入实验](#supp-acquisition) |
| P6.3 | 保存点云回放 | [进入实验](#map-review-3d) |
| P6.4 | 失败诊断 | [进入实验](#srrg-diagnostics) |

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

A按任务评价清图或几何；B评价冻结地图后的定位。B使用共同10 Hz时间点，预热5秒，输出滞后≤0.15秒；样本数与缺失情况见记录。每组1轮，未测完整导航到达效果。

<a id="practice-srrg"></a>

### P1 · SRRG · 静态与动态

| 场景 | 只改变 | 固定 |
| --- | --- | --- |
| 静态对照 / 运动障碍物 | Raw / SRRG | 同次A扫描、同一B扫描、AMCL参数与初始偏移 |


<a id="h1-static-a"></a>

#### 静态 · A

| 方法 | SA ↑ |
| --- | --- |
| Raw | 100.00% |
| SRRG | 100.00% |


[记录](../results/reference/direction-20261016-v2/2d-A-static/record.json)

| A · Raw / SRRG |
| --- |
| <a href="../results/reference/direction-20261016-v2/2d-A-static/execution.mp4"><img src="../results/reference/direction-20261016-v2/2d-A-static/execution.gif" width="840" loading="lazy" alt="A · Raw / SRRG"></a> |


**分析：**
<!-- PRACTICE_ANALYSIS:h1-static-a -->

<!-- /PRACTICE_ANALYSIS:h1-static-a -->

[↑ 目录](#practice-index)

<a id="h1-static-b"></a>

#### 静态 · B

| 地图 | XY RMSE / cm | yaw / ° |
| --- | --- | --- |
| Raw | 5.03 | 2.88 |
| SRRG | 5.84 | 2.91 |


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

| 方法 | DA ↑ | SA ↑ |
| --- | --- | --- |
| Raw | 0.00% | 100.00% |
| SRRG | 36.94% | 99.84% |


[记录](../results/reference/direction-20261016-v2/2d-A-dynamic/record.json)

| A · Raw / SRRG |
| --- |
| <a href="../results/reference/direction-20261016-v2/2d-A-dynamic/execution.mp4"><img src="../results/reference/direction-20261016-v2/2d-A-dynamic/execution.gif" width="840" loading="lazy" alt="A · Raw / SRRG"></a> |


**分析：**
<!-- PRACTICE_ANALYSIS:h1-dynamic-a -->

<!-- /PRACTICE_ANALYSIS:h1-dynamic-a -->

[↑ 目录](#practice-index)

<a id="h1-dynamic-b"></a>

#### 动态 · B

| 地图 | XY RMSE / cm | yaw / ° |
| --- | --- | --- |
| Raw | 5.53 | 0.76 |
| SRRG | 5.13 | 0.70 |


[评分](../results/reference/direction-20261016-v2/2d-dynamic/time-grid-score.json)

| Raw | SRRG |
| --- | --- |
| <a href="../results/reference/direction-20261016-v2/2d-dynamic/executions/raw.mp4"><img src="../results/reference/direction-20261016-v2/2d-dynamic/executions/raw.gif" width="340" loading="lazy" alt="Raw"></a> | <a href="../results/reference/direction-20261016-v2/2d-dynamic/executions/srrg.mp4"><img src="../results/reference/direction-20261016-v2/2d-dynamic/executions/srrg.gif" width="340" loading="lazy" alt="SRRG"></a> |


**分析：**
<!-- PRACTICE_ANALYSIS:h1-dynamic-b -->

<!-- /PRACTICE_ANALYSIS:h1-dynamic-b -->

[↑ 目录](#practice-index)

<a id="practice-srrg-corridor"></a>

### P1.3 · SRRG · 长廊

<a id="h3-original-a"></a>

#### 原长廊 · A

| 方法 | SA ↑ |
| --- | --- |
| Raw | 82.63% |
| SRRG | 82.05% |


[记录](../results/reference/direction-20261016-v2/2d-A-corridor/record.json)

| A · Raw / SRRG |
| --- |
| <a href="../results/reference/direction-20261016-v2/2d-A-corridor/execution.mp4"><img src="../results/reference/direction-20261016-v2/2d-A-corridor/execution.gif" width="840" loading="lazy" alt="A · Raw / SRRG"></a> |


**分析：**
<!-- PRACTICE_ANALYSIS:h3-original-a -->

<!-- /PRACTICE_ANALYSIS:h3-original-a -->

[↑ 目录](#practice-index)

<a id="h3-original-b"></a>

#### 原长廊 · B

| 地图 | XY RMSE / cm | yaw / ° |
| --- | --- | --- |
| Raw | 113.30 | 1.38 |
| SRRG | 102.72 | 1.08 |


[评分](../results/reference/direction-20261016-v2/2d-corridor/time-grid-score.json)

| Raw | SRRG |
| --- | --- |
| <a href="../results/reference/direction-20261016-v2/2d-corridor/executions/degraded_raw.mp4"><img src="../results/reference/direction-20261016-v2/2d-corridor/executions/degraded_raw.gif" width="340" loading="lazy" alt="Raw"></a> | <a href="../results/reference/direction-20261016-v2/2d-corridor/executions/degraded_srrg.mp4"><img src="../results/reference/direction-20261016-v2/2d-corridor/executions/degraded_srrg.gif" width="340" loading="lazy" alt="SRRG"></a> |


**分析：**
<!-- PRACTICE_ANALYSIS:h3-original-b -->

<!-- /PRACTICE_ANALYSIS:h3-original-b -->

[↑ 目录](#practice-index)

<a id="practice-fastlio"></a>

### P2 · FAST-LIO · 运动畸变

| 场景 | 只改变 | 固定 |
| --- | --- | --- |
| 现有静态场景；静止→慢转→快转→平移 | FAST-LIO点补偿关 / 开 | 相同扫描、逐点时间、IMU、状态预测；B使用相同GICP |


三帧真实扫描各取120°扇区组成0.2秒扫描；这是受控分组采样，不是商用雷达扫描模式。

<a id="h2-a"></a>

#### A · 建图与运动阶段

| 点补偿 | Eₘ / cm ↓ |
| --- | --- |
| 关 | 13.49 |
| 开 | 4.61 |


[评分](../results/reference/direction-20261016-v2/fastlio-maps/score.json)

| A · FAST-LIO on / off |
| --- |
| <a href="../results/reference/direction-20261016-v2/fastlio-motion/execution.mp4"><img src="../results/reference/direction-20261016-v2/fastlio-motion/execution.gif" width="840" loading="lazy" alt="A · FAST-LIO on / off"></a> |


<a id="h2-stationary"></a>

##### 静止

| 点补偿 | 阶段时间 | A里程计XYZ RMSE / cm | 旋转 / ° |
| --- | --- | --- | --- |
| 关 | 0–7 s | 0.12 | 0.02 |
| 开 | 0–7 s | 0.15 | 0.03 |


<a id="h2-slow"></a>

##### 慢转

| 点补偿 | 阶段时间 | A里程计XYZ RMSE / cm | 旋转 / ° |
| --- | --- | --- | --- |
| 关 | 7–15 s | 1.30 | 0.95 |
| 开 | 7–15 s | 0.42 | 0.14 |


<a id="h2-fast"></a>

##### 快转

| 点补偿 | 阶段时间 | A里程计XYZ RMSE / cm | 旋转 / ° |
| --- | --- | --- | --- |
| 关 | 15–31 s | 3.18 | 4.35 |
| 开 | 15–31 s | 0.79 | 0.26 |


<a id="h2-translation"></a>

##### 平移

| 点补偿 | 阶段时间 | A里程计XYZ RMSE / cm | 旋转 / ° |
| --- | --- | --- | --- |
| 关 | 31–39 s | 5.33 | 3.68 |
| 开 | 31–39 s | 1.45 | 0.25 |


**分析：**
<!-- PRACTICE_ANALYSIS:h2-a -->

<!-- /PRACTICE_ANALYSIS:h2-a -->

[↑ 目录](#practice-index)

<a id="h2-b"></a>

#### B · 冻结地图后GICP定位

| A点补偿 | XYZ RMSE / cm | 旋转 / ° |
| --- | --- | --- |
| 关 | 14.03 | 3.62 |
| 开 | 2.04 | 0.87 |


[评分](../results/reference/direction-20261016-v2/fastlio-B/score-3d.json)

| Off map | On map |
| --- | --- |
| <a href="../results/reference/direction-20261016-v2/fastlio-B/executions/no_deskew.mp4"><img src="../results/reference/direction-20261016-v2/fastlio-B/executions/no_deskew.gif" width="340" loading="lazy" alt="Off map"></a> | <a href="../results/reference/direction-20261016-v2/fastlio-B/executions/deskew.mp4"><img src="../results/reference/direction-20261016-v2/fastlio-B/executions/deskew.gif" width="340" loading="lazy" alt="On map"></a> |


**分析：**
<!-- PRACTICE_ANALYSIS:h2-b -->

<!-- /PRACTICE_ANALYSIS:h2-b -->

[↑ 目录](#practice-index)

<a id="practice-kitti"></a>

### P3.0 · DUFOMap / BeautyMap · KITTI-00

KITTI-00，141帧；本项只评价地图清理。

| 方法 | DA ↑ | SA ↑ | 点云实录节选（点击看完整录像） | 记录 |
| --- | --- | --- | --- | --- |
| DUFOMap | 98.70% | 97.98% | <a href="../results/reference/desktop-live-dufomap/execution.mp4"><img src="media/related-pointcloud/20261016/dufomap.gif" width="340" alt="DUFOMap"></a> | [记录](../results/reference/desktop-live-dufomap/record.json) |
| BeautyMap | 98.34% | 96.95% | <a href="../results/reference/desktop-live-beautymap/execution.mp4"><img src="media/related-pointcloud/20261016/beautymap.gif" width="340" alt="BeautyMap"></a> | [记录](../results/reference/desktop-live-beautymap/record.json) |

<a id="baseline-3d"></a>

### 三维原测试

保留原Raw／DUFOMap／BeautyMap及GICP结果；各表的评分窗口见记录。

<a id="scene-static-3d"></a>

#### 静态 · 3D

**A · 地图清理**

| 地图 | SA ↑ |
| --- | --- |
| Raw | 100% |
| DUFOMap | 99.999% |
| BeautyMap | 83.33% |


**B · 冻结地图后定位**

<!-- HOME_EXPERIMENT_TABLE -->
| 地图 | XYZ RMSE / cm | 旋转 RMSE / ° |
| --- | --- | --- |
| Raw | 0.95 | 0.15 |
| DUFOMap | 0.99 | 0.16 |
| BeautyMap | 1.07 | 0.17 |
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

**A · 地图清理**

| 地图 | DA ↑ | SA ↑ |
| --- | --- | --- |
| Raw | 0% | 100% |
| DUFOMap | 46.59% | 99.998% |
| BeautyMap | 74.36% | 81.15% |


**B · 冻结地图后定位**

<!-- HOME_EXPERIMENT_TABLE -->
| 地图 | XYZ RMSE / cm | 旋转 RMSE / ° |
| --- | --- | --- |
| Raw | 0.98 | 0.17 |
| DUFOMap | 0.98 | 0.18 |
| BeautyMap | 1.04 | 0.17 |
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

**A · 地图清理**

| 地图 | SA ↑ |
| --- | --- |
| Raw | 100% |
| DUFOMap | 100% |
| BeautyMap | 99.9% |


**B · 冻结地图后定位**

<!-- HOME_EXPERIMENT_TABLE -->
| 地图 | XYZ RMSE / cm | 旋转 RMSE / ° |
| --- | --- | --- |
| Raw | 474.38 | 0.53 |
| DUFOMap | 497.05 | 0.48 |
| BeautyMap | 592.00 | 49.16 |
<!-- /HOME_EXPERIMENT_TABLE -->

[记录](../results/reference/robot-3d-corridor/record.json)

本组有效定位输出区间不同；RMSE只覆盖有输出的时段，不能据此排名稳定性。缺失输出详情见记录。

| Raw | DUFOMap | BeautyMap |
| --- | --- | --- |
| <a href="../results/reference/robot-3d-corridor/executions/raw.mp4"><img src="../results/reference/robot-3d-corridor/executions/raw.gif" width="340" loading="lazy" alt="Raw"></a> | <a href="../results/reference/robot-3d-corridor/executions/dufomap.mp4"><img src="../results/reference/robot-3d-corridor/executions/dufomap.gif" width="340" loading="lazy" alt="DUFOMap"></a> | <a href="../results/reference/robot-3d-corridor/executions/beautymap.mp4"><img src="../results/reference/robot-3d-corridor/executions/beautymap.gif" width="340" loading="lazy" alt="BeautyMap"></a> |


**分析：**
<!-- PRACTICE_ANALYSIS:scene-corridor-3d -->

<!-- /PRACTICE_ANALYSIS:scene-corridor-3d -->

[↑ 目录](#practice-index)

<a id="scene-change-3d"></a>

#### 结构变化 · 3D

**A · 地图清理**

| 地图 | SA ↑ |
| --- | --- |
| Raw | 100% |
| DUFOMap | 99.999% |
| BeautyMap | 83.33% |


**B · 冻结地图后定位**

<!-- HOME_EXPERIMENT_TABLE -->
| 地图 | XYZ RMSE / cm | 旋转 RMSE / ° |
| --- | --- | --- |
| Raw | 0.93 | 0.17 |
| DUFOMap | 1.01 | 0.19 |
| BeautyMap | 1.04 | 0.17 |
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

| 方法 | SA | 新增结构覆盖 | 独立B |
| --- | --- | --- | --- |
| Raw | 100.00% | 100.00% | 未测 |
| SRRG | 99.71% | 98.90% | 未测 |


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
| NDT initial | 34.43 | 0.15 | [记录](../results/reference/robot-ndt-static-initial/record.json) · [MP4](../results/reference/robot-ndt-static-initial/execution.mp4) |
| NDT | 0.93 | 0.17 | [记录](../results/reference/robot-ndt-static/record.json) · [MP4](../results/reference/robot-ndt-static/execution.mp4) |
| GICP | 1.09 | 0.16 | [记录](../results/reference/robot-gicp-static/record.json) · [MP4](../results/reference/robot-gicp-static/execution.mp4) |


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

<a id="practice-irmcl"></a>

### IR-MCL

| 录像 | 指标 | 记录 |
| --- | --- | --- |
| <a href="../results/reference/desktop-live-ir-mcl/execution.mp4"><img src="media/related-pointcloud/20261016/ir-mcl.gif" width="340" alt="IR-MCL"></a> | XY RMSE 5.31 cm / yaw 1.07° | [记录](../results/reference/desktop-live-ir-mcl/record.json) |

**分析：**

[↑ 目录](#practice-index)

<a id="practice-adam"></a>

### AdaM-MCL

| 录像 | 指标 | 记录 |
| --- | --- | --- |
| <a href="../results/reference/desktop-adam-mcl/result.mp4"><img src="../results/reference/desktop-adam-mcl/result.gif" width="340" alt="AdaM-MCL"></a> | RMSE 32.23格；持续收敛0/10；保存结果回放 | [记录](../results/reference/desktop-adam-mcl/record.json) |

**分析：**

[↑ 目录](#practice-index)

<a id="hypothesis-test"></a>

## Hypothesis test

<a id="hypothesis-test-index"></a>

自写方法的实验。每个场景重新采集A/B；同一场景各对照共享输入。每组1轮，固定参数，不根据真值调参。

| 实验 | 建图与指标 | 独立定位与指标 |
| --- | --- | --- |
| H1 静态保留 | [A](#own-static-a) | [B](#own-static-b) |
| H1 动态清理 | [A](#own-dynamic-a) | [B](#own-dynamic-b) |
| H2 里程计去畸变 | [A](#own-motion-a) | [B](#own-motion-b) |
| H3 退化约束保护 | [A](#own-corridor-a) | [B](#own-corridor-b) |

设备同Practice的全向轮机器人；算法仅使用二维雷达和轮式里程计。H2将三个真实时刻的扇区组合为滚动扫描，保留各点原采样时刻；未使用FAST-LIO。H3保持同一走廊，只切换地图保留规则。

[自写算法](../src/slam_learning/runtime/own_mapping.py) · [一键录制](../demo/record-own-hypotheses.ps1)

H2录像阶段：静止0–7秒、慢转7–15秒、快转15–31秒、平移31–39秒。

<a id="own-static-a"></a>

### H1 · 静态保留 · A

| 对照 | SA ↑ |
| --- | --- |
| raw | 99.55% |
| temporal | 95.62% |

| 建图录像：灰色为基线，蓝色为自写干预 |
| --- |
| <a href="../results/reference/own-hypotheses-20261016/static-A/execution.mp4"><img src="../results/reference/own-hypotheses-20261016/static-A/execution.gif" width="840" loading="lazy" alt="H1 · 静态保留 A"></a> |

[记录](../results/reference/own-hypotheses-20261016/static-A/record.json)

**分析：**
<!-- OWN_ANALYSIS:static-a -->

<!-- /OWN_ANALYSIS:static-a -->

<a id="own-static-b"></a>

### H1 · 静态保留 · B

| 地图／AMCL | XY RMSE / cm ↓ |
| --- | --- |
| raw | 4.74 |
| temporal | 5.68 |

| raw | temporal |
| --- | --- |
| <a href="../results/reference/own-hypotheses-20261016/static-B/executions/raw.mp4"><img src="../results/reference/own-hypotheses-20261016/static-B/executions/raw.gif" width="420" loading="lazy" alt="raw B"></a> | <a href="../results/reference/own-hypotheses-20261016/static-B/executions/temporal.mp4"><img src="../results/reference/own-hypotheses-20261016/static-B/executions/temporal.gif" width="420" loading="lazy" alt="temporal B"></a> |

[共同时间点评分](../results/reference/own-hypotheses-20261016/static-B/time-grid-score.json) · [记录](../results/reference/own-hypotheses-20261016/static-B/record.json)

**分析：**
<!-- OWN_ANALYSIS:static-b -->

<!-- /OWN_ANALYSIS:static-b -->

[↑ 目录](#hypothesis-test-index)

<a id="own-dynamic-a"></a>

### H1 · 动态清理 · A

| 对照 | DA ↑ | SA ↑ |
| --- | --- | --- |
| raw | 5.13% | 99.50% |
| temporal | 94.87% | 92.55% |

| 建图录像：灰色为基线，蓝色为自写干预 |
| --- |
| <a href="../results/reference/own-hypotheses-20261016/dynamic-A/execution.mp4"><img src="../results/reference/own-hypotheses-20261016/dynamic-A/execution.gif" width="840" loading="lazy" alt="H1 · 动态清理 A"></a> |

[记录](../results/reference/own-hypotheses-20261016/dynamic-A/record.json)

**分析：**
<!-- OWN_ANALYSIS:dynamic-a -->

<!-- /OWN_ANALYSIS:dynamic-a -->

<a id="own-dynamic-b"></a>

### H1 · 动态清理 · B

| 地图／AMCL | XY RMSE / cm ↓ |
| --- | --- |
| raw | 5.72 |
| temporal | 6.11 |

| raw | temporal |
| --- | --- |
| <a href="../results/reference/own-hypotheses-20261016/dynamic-B/executions/raw.mp4"><img src="../results/reference/own-hypotheses-20261016/dynamic-B/executions/raw.gif" width="420" loading="lazy" alt="raw B"></a> | <a href="../results/reference/own-hypotheses-20261016/dynamic-B/executions/temporal.mp4"><img src="../results/reference/own-hypotheses-20261016/dynamic-B/executions/temporal.gif" width="420" loading="lazy" alt="temporal B"></a> |

[共同时间点评分](../results/reference/own-hypotheses-20261016/dynamic-B/time-grid-score.json) · [记录](../results/reference/own-hypotheses-20261016/dynamic-B/record.json)

**分析：**
<!-- OWN_ANALYSIS:dynamic-b -->

<!-- /OWN_ANALYSIS:dynamic-b -->

[↑ 目录](#hypothesis-test-index)

<a id="own-motion-a"></a>

### H2 · 里程计去畸变 · A

| 对照 | Eₘ / cm ↓ |
| --- | --- |
| off | 34.10 |
| deskew | 4.57 |

| 建图录像：灰色为基线，蓝色为自写干预 |
| --- |
| <a href="../results/reference/own-hypotheses-20261016/motion-A/execution.mp4"><img src="../results/reference/own-hypotheses-20261016/motion-A/execution.gif" width="840" loading="lazy" alt="H2 · 里程计去畸变 A"></a> |

[记录](../results/reference/own-hypotheses-20261016/motion-A/record.json)

**分析：**
<!-- OWN_ANALYSIS:motion-a -->

<!-- /OWN_ANALYSIS:motion-a -->

<a id="own-motion-b"></a>

### H2 · 里程计去畸变 · B

| 地图／AMCL | XY RMSE / cm ↓ |
| --- | --- |
| off | 4.70 |
| deskew | 4.71 |

| off | deskew |
| --- | --- |
| <a href="../results/reference/own-hypotheses-20261016/motion-B/executions/off.mp4"><img src="../results/reference/own-hypotheses-20261016/motion-B/executions/off.gif" width="420" loading="lazy" alt="off B"></a> | <a href="../results/reference/own-hypotheses-20261016/motion-B/executions/deskew.mp4"><img src="../results/reference/own-hypotheses-20261016/motion-B/executions/deskew.gif" width="420" loading="lazy" alt="deskew B"></a> |

[共同时间点评分](../results/reference/own-hypotheses-20261016/motion-B/time-grid-score.json) · [记录](../results/reference/own-hypotheses-20261016/motion-B/record.json)

**分析：**
<!-- OWN_ANALYSIS:motion-b -->

<!-- /OWN_ANALYSIS:motion-b -->

[↑ 目录](#hypothesis-test-index)

<a id="own-corridor-a"></a>

### H3 · 退化约束保护 · A

| 保护规则额外保留的栅格数 | 冻结地图字节相同 |
| --- | --- |
| 0 | 是 |

本轮保护规则未改变最终地图；B中的随机误差差别不能视为地图干预带来的改善。

| 建图录像：灰色为基线，蓝色为自写干预 |
| --- |
| <a href="../results/reference/own-hypotheses-20261016/corridor-A/execution.mp4"><img src="../results/reference/own-hypotheses-20261016/corridor-A/execution.gif" width="840" loading="lazy" alt="H3 · 退化约束保护 A"></a> |

[记录](../results/reference/own-hypotheses-20261016/corridor-A/record.json)

**分析：**
<!-- OWN_ANALYSIS:corridor-a -->

<!-- /OWN_ANALYSIS:corridor-a -->

<a id="own-corridor-b"></a>

### H3 · 退化约束保护 · B

仅用前50秒受限扫描阶段的沿廊RMSE检验弱方向定位。

| 地图／AMCL | 沿廊 RMSE / cm ↓ |
| --- | --- |
| degraded_strict | 80.56 |
| degraded_protected | 80.56 |

| degraded_strict | degraded_protected |
| --- | --- |
| <a href="../results/reference/own-hypotheses-20261016/corridor-B/executions/degraded_strict.mp4"><img src="../results/reference/own-hypotheses-20261016/corridor-B/executions/degraded_strict.gif" width="420" loading="lazy" alt="degraded_strict B"></a> | <a href="../results/reference/own-hypotheses-20261016/corridor-B/executions/degraded_protected.mp4"><img src="../results/reference/own-hypotheses-20261016/corridor-B/executions/degraded_protected.gif" width="420" loading="lazy" alt="degraded_protected B"></a> |

[共同时间点评分](../results/reference/own-hypotheses-20261016/corridor-B/time-grid-score.json) · [记录](../results/reference/own-hypotheses-20261016/corridor-B/record.json)

**分析：**
<!-- OWN_ANALYSIS:corridor-b -->

<!-- /OWN_ANALYSIS:corridor-b -->

[↑ 目录](#hypothesis-test-index)

H1用DA/SA评清图，静态对照只看SA；H2用Eₘ评地图几何；H3检查保护规则是否增加保留格数，再看B沿廊误差。定位预热5秒后使用共同10 Hz时间点，最新输出最多滞后0.15秒；样本数与输出缺失情况见原始评分记录。建图指标改善但B误差不降时，只支持建图结论。
