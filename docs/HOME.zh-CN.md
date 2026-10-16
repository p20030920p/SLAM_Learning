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
| **测试7 · `7.mp4`** | **测试6 · `6.mp4`** |
| <a href="media/physical-test/20261016-additional/7.gif"><img src="media/physical-test/20261016-additional/7.gif" width="420" loading="lazy" alt="实物测试7"></a> | <a href="media/physical-test/20261016-additional/6.gif"><img src="media/physical-test/20261016-additional/6.gif" width="420" loading="lazy" alt="实物测试6"></a> |

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
| H1 / Q1 | 自写静态支持对齐与时序清理，在静态保留损失≤1个百分点时减少残影，并改善独立定位。 | M₀：轮速累积图 / M₁：自写对齐＋清理 | A：DA、SA；B：XY RMSE |
| H2 / Q2 | 用轮式里程计补偿点的采样时间差，能降低地图和独立定位误差。 | M₀：补偿关 / M₁：补偿开 | A：地图RMSE；B：XY RMSE |

两项干预均由本库实现；AMCL只作为统一的下游评分定位器。镜面识别仍待实物验证。

<a id="hypothesis-math"></a>

### 数学表达

**核心：利用时序支持进行扫描对齐与动态残影清理，构建用于后续定位的二维地图。** H2单独检验点的采样时间补偿。下文逐组解释现有公式；**加粗并加框的三条是核心算法公式**。

**实验约定。** A用于建图，B为另一次独立采集。每项实验中，基线地图为$`M_0`$，干预地图为$`M_1`$；两图来自同一份A，建好后冻结，再用相同B扫描、里程计、AMCL参数和初始化评价定位。真值仅进入事后评分。

| 符号 | 含义 |
| --- | --- |
| $`T_k^o`$ / $`T_k`$ | 第$`k`$帧轮速传感器位姿／H1修正位姿，均从传感器系变换到固定地图系 |
| $`c`$ / $`\mathbf x_c`$ | 5 cm栅格／栅格中心坐标 |
| $`b`$ | 0.5秒时间箱；每类证据在同一箱内最多计一次 |
| $`\mathbf1[\cdot]`$ | 条件成立记1，否则记0 |
| $`M`$ | 地图占据格中心组成的非空点集；与AMCL使用的完整栅格图相区分 |

坐标以米计，实验表将距离误差换算为cm。点集评分在同一坐标系、膨胀前进行；各组AMCL栅格采用相同生成及膨胀规则。空图记为建图失败。

**1．共同评价公式：冻结地图后的定位RMSE。**

```math
E_{{\rm loc},m}=\sqrt{\frac{1}{|\mathcal T|}\sum_{k\in\mathcal T}\|\hat{\mathbf p}_{m,k}-\mathbf p_k^*\|_2^2}.
```

$`\hat{\mathbf p}_{m,k}`$是在$`M_m`$上估计的机器人二维位置，$`\mathbf p_k^*`$为同一时刻的位置真值，$`m\in\{0,1\}`$。先计算每个时刻的位置距离平方，再平均、开平方；用$`E_{{\rm loc},1}<E_{{\rm loc},0}`$检验定位改善。

$`\mathcal T`$只含两组都有有效输出的共同评分时刻。当前协议为预热5秒后10 Hz采样、输出滞后不超过0.15秒；集合为空不评分。H1多轮时，$`k`$同时索引轮次与时刻，合并全部共同有效样本。未输出时刻不计入本项RMSE，因此它不等于定位成功率；也没有评价完整导航任务的到达效果。

**口头表述：**先冻结A地图，再让同一定位器处理独立B，检查地图变化是否降低定位误差。这是评价要求，算法没有直接最小化AMCL误差。

**H1：前序时序支持辅助对齐，再用空闲反证清理残影。** Raw用轮速位姿直接累积；干预同时改变位姿对齐和残影清理，两项贡献需用“只对齐／只清理”消融区分。

**2．轮速增量预测当前位姿。**

```math
T_{k,0}=T_{k-1}(T_{k-1}^o)^{-1}T_k^o.
```

$`(T_{k-1}^o)^{-1}T_k^o`$为轮速给出的相邻帧运动；将它接在上一帧已修正位姿$`T_{k-1}`$上，得到当前初值$`T_{k,0}`$。初帧使用已知起点与轮速位姿，算法不读取位姿真值。

**口头表述：**轮速提供这一小步走了多少，我们从上一帧修正后的位置继续预测。

**3．对较差对应点降权。** 每次迭代令$`\mathbf p=T_k\mathbf z`$，其中$`\mathbf z`$是二维扫描点；$`\mathbf q`$为前序参照中的最近点：

```math
w_{\mathbf p}=\min\!\left(1,\frac{0.05}{\max(\|\mathbf p-\mathbf q\|_2,10^{-9})}\right).
```

距离不超过5 cm时权重为1，更大时逐渐减小；$`10^{-9}`$用于避免除零。权重反映配准对应的可靠程度，不是动态物体概率，也不保证识别出全部运动物体。

**4．核心公式一：鲁棒扫描对齐。**

```math
\boxed{\boldsymbol{\Delta T=\arg\min_{U\in\mathrm{SE}(2)}\sum_{(\mathbf p,\mathbf q)\in\mathcal C_k}w_{\mathbf p}\|U\mathbf p-\mathbf q\|_2^2}}
```

```math
T_k\leftarrow\Delta T T_k.
```

$`U\in\mathrm{SE}(2)`$只允许二维旋转和平移；$`\mathcal C_k`$为本轮对应点对；目标是最小化变换后的加权距离平方和。求得刚体增量$`\Delta T`$后更新位姿，每轮重新匹配，最多迭代12次。

参照$`\mathcal R_{k-1}`$只来自前序保留地图中至少获得3个时间箱邻域支持的位置。对应距离需小于0.30 m，再保留最接近的70%（至少30对）。参照不足80点、对应不足30对，或相对轮速预测的总修正超过0.15 m／0.05 rad时，退回轮速预测。这些是当前实现参数，不是创新性结论。

**口头表述：**利用前序反复获得观测支持的结构修正当前位姿，并用对应筛选和降权减少错误匹配的影响。当前是局部逐帧修正，没有全局位姿图优化。

**5．命中证据与候选地图。** 在修正位姿下累计：

```math
h(c)=\sum_b\mathbf1[\text{hit at }c\text{ in bin }b],\qquad\widetilde M=\{\mathbf x_c:h(c)>0\}.
```

$`h(c)`$统计有多少个时间箱直接命中栅格$`c`$；同箱高频重复回波只计一次。$`\widetilde M`$包含至少命中过一次的位置。它使用修正位姿，不同于轮速位姿累积的基线$`M_0`$。

**6．邻域命中支持。**

```math
s(c)=\sum_b\mathbf1[\exists c':\|\mathbf x_{c'}-\mathbf x_c\|_2\le0.10,\ \text{hit at }c'\text{ in bin }b].
```

$`s(c)`$统计有多少个时间箱在$`c`$附近10 cm内获得命中。这样，同一墙面的回波因轻微测量或位姿误差落在相邻格时，仍能贡献支持。邻域证据只影响判断，不向未观测位置补出占据点。

**口头表述：**判断附近结构是否持续被看到，允许回波在相邻格之间轻微变化。

**7．空闲穿越证据。**

```math
f(c)=\sum_b\mathbf1[\text{free ray through }c\text{ in bin }b].
```

$`f(c)`$统计有效测量射线穿过$`c`$的时间箱数。射线在回波前15 cm停止，为端点误差留出裕量；未观测或被遮挡的位置不能直接记为空闲。$`s,f`$可在同箱同时增加，它们是证据计数，不是互斥概率；不同时间箱也不保证统计独立。

**8．核心公式二：残影清理规则。**

```math
\boxed{\boldsymbol{M_1=\{\mathbf x_c\in\widetilde M:f(c)<3\ \lor\ f(c)<1.5s(c)\}}}
```

等价地，只有$`f(c)\ge3`$且$`f(c)\ge1.5s(c)`$时才删除：至少3个不同时间箱提供空闲反证，并且空闲证据达到邻域命中支持的1.5倍。一个仅看见一次、之后没有再观测到的角落，不会仅因命中少被删除。当前规则不能保证去除全部动态物体。

**口头表述：删除需要足够反证，观察次数少本身不足以删除。** 清理后的地图及其时序支持供下一帧对齐使用，形成逐帧反馈。

**9．评分使用的最近距离。**

```math
d(\mathbf q,M)=\min_{\mathbf x\in M}\|\mathbf q-\mathbf x\|_2.
```

在地图中找到离参考位置$`\mathbf q`$最近的点，距离越小表示该参考位置越接近地图。此处用于评分，不参与算法的动态判断。

**10．静态覆盖SA与残影清除DA。** $`S`$为A中已观测静态参考位置的非空集合；$`D`$为后来被射线验证为空、且不与静态支持或当前障碍物重叠的历史动态位置。两组共用$`S,D`$，按10 cm格去重，统一匹配容差$`r=0.15\,\mathrm m`$：

```math
\mathrm{SA}(M)=\frac{\sum_{\mathbf q\in S}\mathbf1[d(\mathbf q,M)\le r]}{|S|},\qquad\mathrm{DA}(M)=\frac{\sum_{\mathbf q\in D}\mathbf1[d(\mathbf q,M)>r]}{|D|}.
```

SA是静态参考位置仍被地图覆盖的比例；DA是历史残影参考位置已不再被覆盖的比例。公式取0–1，实验表换成百分数；$`D`$为空时不定义DA。这里是二维位置覆盖评分，不是逐个原始点的保留追踪，也不等于几何精度。真值及物体标签只用于构造评分参照，不输入算法。

**11．清理改善条件与H1预测。**

```math
\mathrm{DA}(M_1)>\mathrm{DA}(M_0)\quad\land\quad\mathrm{SA}(M_1)\ge\mathrm{SA}(M_0)-0.01.
```

动态残影删除更多，且静态覆盖相对基线最多损失1个百分点，才满足本文的“清理改善”定义。这只针对已观测支持，不代表整张地图完整、几何准确或镜面问题已解决。

H1还要求独立B定位改善，可将完整预测合写为：

```math
\mathrm{DA}(M_1)>\mathrm{DA}(M_0),\qquad\mathrm{SA}(M_1)\ge\mathrm{SA}(M_0)-0.01,\qquad E_{{\rm loc},1}<E_{{\rm loc},0}.
```

**口头表述：**先检查残影减少和静态支持保留，再检查冻结地图后的独立定位是否改善。旧B用于开发消融，最终新B采集前固定参数；联合方法收益不能全归因于动态删除。

**H2：统一点的采样参考时刻，再分别检验地图几何和定位。**

**12．核心公式三：运动畸变补偿。** $`\mathbf z_i=(x_i,y_i,1)^{\mathsf T}`$是在$`t_i`$采集的局部齐次点；$`\hat T(t)\in\mathrm{SE}(2)`$由轮速插值和传感器外参得到，从该时刻传感器系变换到固定地图系。$`t_e`$为扫描末时刻：

```math
\boxed{\boldsymbol{\bar{\mathbf z}_i=\hat T(t_e)^{-1}\hat T(t_i)\mathbf z_i}}
```

从右向左理解：先用$`\hat T(t_i)`$将点放入固定坐标系，再用$`\hat T(t_e)^{-1}`$转入扫描末时刻坐标系。$`M_0`$把混合时刻的点直接当作$`t_e`$采集；$`M_1`$先补偿。两图都用$`\hat T(t_e)`$融合，其他步骤相同；H2不额外开启H1过滤。

**口头表述：**利用机器人运动估计，把不同时刻测到的点统一到同一参考时刻。它补偿机器人自身运动，不会自动补偿物体自身运动；也依赖轮速估计质量。

**13．地图几何误差。** 从本项A重新构造静态参照$`S`$，沿用最近距离$`d`$：

```math
E_{\rm map}(M)=\sqrt{\frac1{|M|}\sum_{\mathbf x\in M}d(\mathbf x,S)^2}.
```

逐个计算地图点到静态参照的最近距离，再平方、平均和开平方。这是“地图到已观测静态支持”的单向距离，不能单独评价完整性；空图判为建图失败。

**14．H2的联合检验条件。**

```math
E_{\rm map}(M_1)<E_{\rm map}(M_0)\quad\land\quad E_{{\rm loc},1}<E_{{\rm loc},0}.
```

几何评分下降后，还要验证独立定位误差下降；若只有前一项成立，只支持几何评分改善。H2当前是单轮探索，稳定收益仍需重复验证。

<a id="hypothesis-srrg-comparison"></a>

### 创新点与SRRG思路对比

**创新点与SRRG思路对比。** 此处SRRG指Lázaro等的 *Efficient Long-term Mapping in Dynamic Environments*（IROS 2018）及对应二维建图库。它已经包含点及法向配准、自由空间融合、位姿图和长期多会话地图维护；“对齐＋清理”或“利用自由空间去动态”本身不能作为相对SRRG的首创新点。[原文，第III节](https://iris.uniroma1.it/handle/11573/1340118)。

| 比较角度 | SRRG论文的主要思路 | 当前方案的思路 |
| --- | --- | --- |
| 地图表示 | 带法向的二维局部点云及位姿图 | 栅格中的命中、邻域支持和空闲计数 |
| 配准依据 | 点与法向对应，结合里程计初值／先验 | 对前序时序支持位置做鲁棒点对点配准 |
| 动态处理 | 投影到共同视角，比较距离，融合、增加或替换点 | 跨时间箱累计空闲反证，满足条件才删除 |
| 轻微错位的处理 | 几何对应与点云融合 | 邻域命中允许回波落入相邻栅格 |
| 系统范围 | 完整SLAM、全局图优化及长期地图维护 | 当前局部逐帧干预，无全局位姿图及长期多会话机制 |
| 本项目的验证关注 | 实践作者地图维护流程 | 关联清理／保留与冻结地图后的独立定位 |

**创新候选：构造显式的邻域时序证据，让它同时参与配准参照筛选和动态残影删除，并用独立定位实验检验地图维护的价值。** 具体差异是时间箱、邻域支持与删除反证的组织方式；参数数值、自写实现及标准鲁棒配准本身不构成首创证明。独立B是验证设计，当前没有直接优化AMCL误差。H2采用标准相对位姿补偿，不列为相对SRRG的独立首创新点。

这套保守规则可能减少单次异常观测导致的误删，也可能延迟适应真实变化，均需验证。尚需证明：在位姿扰动、稀疏观测和动态遮挡下，该证据设计能否更好地平衡静态支持保留与残影清除。**目前是已实现的设计差异，尚未证明文献首创；与SRRG的指标效果暂不比较，也不声称性能更优。**

**汇报表述：**我们关注动态建图对后续定位的影响。与SRRG的投影融合及完整图维护思路相比，我们显式累计跨时间的邻域支持与空闲证据：先用持续获得支持的结构辅助配准，再以足够空闲反证清理历史残影。当前验证重点是这套证据设计能否保留定位所需结构，与SRRG的性能优劣尚未建立。

<a id="hypothesis-pseudocode"></a>

### 伪代码

```text
for test, scene in [(H1, static), (H1, dynamic), (H2, motion)]:
    A = acquire_scans_and_wheel_odometry(scene)
    if test == H1:
        M0 = integrate_A_with_wheel_poses(A)
        h, s, f = initialize_grid_evidence()
        M1 = empty_map()
        previous_wheel, previous_corrected = None, None
        for scan in A.in_time_order():
            wheel = sensor_pose_from_wheel_odometry(scan)
            predicted = wheel if previous_wheel is None else previous_corrected @ inverse(previous_wheel) @ wheel
            reference = previous_retained_cells_with_support(M1, s, min_bins=3)
            corrected = own_robust_SE2_alignment_or_wheel_fallback(scan, predicted, reference)
            points = transform_scan(scan, corrected)
            bin = floor(scan.time / 0.5)
            add_hits_once_per_cell_and_bin(h, points, bin)
            add_neighborhood_support_once_per_bin(s, points, bin, radius=0.10)
            add_free_crossings_once_per_bin(f, points, corrected, bin, stop_before_return=0.15)
            M1 = cell_centers_where((h > 0) & ((f < 3) | (f < 1.5 * s)))
            previous_wheel, previous_corrected = wheel, corrected
    else:
        M0 = integrate_A(A, point_compensation=False)
        M1 = integrate_A(A, point_compensation=True)  # no H1 filtering
    freeze(M0, M1)
    B = acquire_independent_scans_and_wheel_odometry(scene)
    positions = {}
    for m, map in [(0, M0), (1, M1)]:
        positions[m] = same_AMCL(B.scans, B.odometry, grid_of(map), same_initial_config)
    # Truth enters only here; references are shared across controls
    S, D = scoring_references_from_A_truth(A)
    if test == H1:
        score_SA(M0, M1, S)
        if scene == dynamic: score_DA(M0, M1, D)
    if test == H2: score_map_RMSE(M0, M1, S)
    score_position_RMSE(positions, B_truth, common_valid_times)
```

[实现、实验与录像](#hypothesis-test-index)

## 相关工作

<!-- HOME_RELATED_TABLE -->
按算法类型排列；GIF可直接查看，点击可播放完整视频。适用方向列保留空白，供后续填写。各行数据协议不同，不跨数据集排名。

| 方法／算法类型 | 原库实录GIF／原始图示 | 评价指标与本次范围 | 适用方向 |
| --- | --- | --- | --- |
| <a id="related-fast_lio"></a>[FAST-LIO / FAST-LIO2](papers/fast_lio.zh-CN.md) | <img src="assets/related/20261016-pointcloud/fastlio2-fig12.png" width="280" alt="FAST-LIO2 original Fig. 12: point-cloud map"> | 原文实验：**不复现**；原图与方法介绍，自有场景测试见Practice |  |
| <a id="related-srrg_mapper2d"></a>[SRRG / srrg_mapper2d](papers/srrg_mapper2d.zh-CN.md) | <img src="assets/related/20261016-pointcloud/srrg-fig7.png" width="280" alt="SRRG original Fig. 7: point-cloud map"> | 原文实验：**不复现**；原图与方法介绍，自有场景测试见Practice |  |
| <a id="related-dufomap"></a>[DUFOMap](papers/dufomap.md)<br>三维地图清理 | <a href="../results/reference/desktop-live-dufomap/execution.mp4"><img src="media/related-pointcloud/20261016/dufomap.gif" width="280" loading="lazy" alt="dufomap · 点云实录节选"></a><br>[点云实录节选](../results/reference/desktop-live-dufomap/execution.mp4) | SA 97.98% / DA 98.7%<br>KITTI-00 · 141 帧；清理有效<br>[记录](../results/reference/desktop-live-dufomap/record.json) |  |
| <a id="related-beautymap"></a>[BeautyMap](papers/beautymap.md)<br>三维离线地图清理 | <a href="../results/reference/desktop-live-beautymap/execution.mp4"><img src="media/related-pointcloud/20261016/beautymap.gif" width="280" loading="lazy" alt="beautymap · 点云实录节选"></a><br>[点云实录节选](../results/reference/desktop-live-beautymap/execution.mp4) | SA 96.95% / DA 98.34%<br>KITTI-00 · 141 帧；清理有效<br>[记录](../results/reference/desktop-live-beautymap/record.json) |  |
| <a id="related-amcl"></a>[AMCL / Nav2](https://github.com/ros-navigation/navigation2/tree/main/nav2_amcl)<br>二维粒子定位 | <a href="https://github.com/ros-navigation/docs.nav2.org/blob/8f6571b599d6b1e899f11ac58c5c1982d3b0a8b5/docs/getting_started/quickstart/assets/rviz/navstack_ready.png"><img src="assets/related/20261016-localizers/amcl-nav2-original.png" width="280" loading="lazy" alt="AMCL: original Nav2 repository localization screenshot"></a><br>Nav2官方文档库原图 | 二维冻结地图定位器；看XY／偏航RMSE。原库图示，非本项目实录；[方法说明](#related-amcl-details) |  |
| <a id="related-gicp"></a>[GICP](https://github.com/avsegal/gicp)<br>三维几何配准 | <a href="https://www.robots.ox.ac.uk/~avsegal/generalized_icp.html"><img src="assets/related/20261016-localizers/gicp-author-original.jpg" width="280" loading="lazy" alt="GICP: original point-cloud illustration from the algorithm author"></a><br>GICP作者主页原图 | 三维冻结地图定位器；看XYZ／旋转RMSE。原作者图示，非本项目实录；[方法说明](#related-gicp-details) |  |
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

来源：Lázaro等，*Efficient Long-term Mapping in Dynamic Environments*，IROS 2018，图7，第6页。[原文](https://iris.uniroma1.it/handle/11573/1340118) · [作者代码](https://gitlab.com/srrg-software/srrg_mapper2d)。二维点云和里程计经过配准、局部图维护与位姿图优化；对应H1的动态地图维护，也需要检查Q3中的几何约束。
<!-- /SRRG_RELATED -->

<!-- FASTLIO_RELATED -->
### FAST-LIO / FAST-LIO2 · LiDAR–IMU运动估计与点补偿

**原文实验：不复现。** 下面是FAST-LIO2论文的原图。本文的FAST-LIO实现测试使用官方ROS2分支、FAST-LIO2直接配准路径；同名软件包与初版论文需要区分。自有场景消融见[FAST-LIO Practice](#practice-fastlio)。

![FAST-LIO2 · original point-cloud Fig. 12](assets/related/20261016-pointcloud/fastlio2-fig12.png)

来源：Xu等，*FAST-LIO2: Fast Direct LiDAR-inertial Odometry*，图12，第16页。[FAST-LIO论文](https://arxiv.org/abs/2010.08196) · [FAST-LIO2论文](https://arxiv.org/abs/2107.06829) · [官方ROS2代码](https://github.com/hku-mars/FAST_LIO/tree/ROS2)。IMU传播与逐点反向补偿对应H2；ikd-Tree维护的是增量空间数据结构，不能直接当成动态物体去除或镜面检测器。
<!-- /FASTLIO_RELATED -->
<!-- LOCALIZERS_RELATED -->
<a id="related-amcl-details"></a>

### AMCL · 在已建好的二维地图中定位

**输入 → 处理 → 输出：**固定二维占据栅格地图、激光扫描与里程计 → 粒子运动预测、扫描与地图匹配加权、重采样及自适应粒子数量 → 平面位置、偏航与位姿不确定性。AMCL负责定位，不构建或清理地图。

<img src="assets/related/20261016-localizers/amcl-nav2-original.png" width="680" alt="Nav2官方文档库原图：地图中的机器人与AMCL粒子分布">

**图源：**[Nav2官方文档库原图](https://github.com/ros-navigation/docs.nav2.org/blob/8f6571b599d6b1e899f11ac58c5c1982d3b0a8b5/docs/getting_started/quickstart/assets/rviz/navstack_ready.png)，展示机器人、粒子分布及导航栈图层；非本项目录制。[AMCL官方代码](https://github.com/ros-navigation/navigation2/tree/main/nav2_amcl)。

**与本文的关系：**二维Practice及自写H1／H2均使用AMCL，在冻结A地图后处理独立B；对照共用扫描、里程计、参数及初始化，评价XY定位误差，按需要报告偏航误差。地图残影或静态约束损失会改变扫描匹配权重；DA／SA不用于评价AMCL。自有场景测试见[Practice](#practice-index)与[Hypothesis test](#hypothesis-test-index)，不复现原文基准实验。

<a id="related-gicp-details"></a>

### GICP · 将三维扫描配准到固定点云地图

**输入 → 处理 → 输出：**固定三维点云地图、当前扫描与初始位姿预测 → 建立对应，利用两侧局部表面协方差加权残差，迭代求解刚体变换 → 三维位置与姿态。原始GICP是配准算法；接入定位系统后用于扫描到地图定位，本身不执行动态清理。

<img src="assets/related/20261016-localizers/gicp-author-original.jpg" width="400" alt="GICP作者主页原始点云示意图">

**图源：**[GICP作者主页原图](https://www.robots.ox.ac.uk/~avsegal/generalized_icp.html)；作者参考库未提供图片，采用作者主页点云图，非本项目实录。[原始参考代码](https://github.com/avsegal/gicp) · [PCL实现说明](https://pointclouds.org/documentation/classpcl_1_1_generalized_iterative_closest_point.html) · [本文使用的ROS2定位框架](https://github.com/rsasaki0109/lidar_localization_ros2)。

**与本文的关系：**三维Practice将Raw／DUFOMap／BeautyMap的A地图冻结，用相同GICP配置处理新B点云与轮速里程计，评价XYZ及三维旋转RMSE。地图清理由前述方法完成，GICP只检验下游定位。局部配准依赖初值和几何约束；长廊中角度误差小也可能伴随纵向米级漂移。自有场景测试见[三维Practice](#scene-static-3d)；当前安装版ROS2/PCL实现不等同于作者参考库复现，也不复现原文基准实验。
<!-- /LOCALIZERS_RELATED -->

<!-- /HOME_RELATED_DETAILS -->

</details>

## 指标

| 指标 | 一句话说明 |
| --- | --- |
| DA ↑ / SA ↑ | 仅评清图A：动态删除比例／静态保留比例；无动态时只列SA。二维按观测支持、三维按点评分。 |
| 地图 RMSE ↓ | 去畸变A：地图点到静态参考几何的距离RMSE，cm。 |
| XY / XYZ RMSE ↓ | 冻结地图后的定位B：二维／三维位置误差，cm。 |
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
| P0.1 | Raw基线定义与区别 | [进入实验](#raw-baseline-definitions) |
| P1.1 | SRRG · 静态 | [A](#h1-static-a) / [B](#h1-static-b) |
| P1.2 | SRRG · 动态 | [A](#h1-dynamic-a) / [B](#h1-dynamic-b) |
| P1.3 | SRRG · 原长廊 | [A](#h3-original-a) / [B](#h3-original-b) |
| P1.4 | SRRG · 结构变化 | [A](#supp-srrg) / [B](#supp-srrg-b) |
| P2.1 | FAST-LIO · 建图与运动阶段 | [A](#h2-a) / [静止](#h2-stationary) / [慢转](#h2-slow) / [快转](#h2-fast) / [平移](#h2-translation) |
| P2.2 | FAST-LIO · 冻结地图定位 | [B](#h2-b) |
| P3.0 | DUFOMap / BeautyMap · KITTI-00 | [清图实践](#practice-kitti) |
| P3.1 | DUFOMap / BeautyMap · 3D · 静态 | [A](#scene-static-3d) / [B](#scene-static-3d-b) |
| P3.2 | DUFOMap / BeautyMap · 3D · 动态 | [A](#scene-dynamic-3d) / [B](#scene-dynamic-3d-b) |
| P3.3 | DUFOMap / BeautyMap · 3D · 长廊 | [A](#scene-corridor-3d) / [B](#scene-corridor-3d-b) |
| P3.4 | DUFOMap / BeautyMap · 3D · 结构变化 | [A](#scene-change-3d) / [B](#scene-change-3d-b) |
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

A按任务评价清图或几何；B评价冻结地图后的定位，均预热5秒。P3三维按三组共同扫描时间戳评分；其他组沿用共同10 Hz时间点、输出滞后≤0.15秒。样本与缺失情况见记录。每组1轮，未测完整导航到达效果。

<a id="raw-baseline-definitions"></a>

### Raw基线定义

**Raw的含义。** Raw是本库对“未做地图动态清理的累积基线”的标签，不是一个独立SLAM或定位算法，也不表示完全未经预处理的数据。

| 使用位置 | Raw如何生成 | 后续定位 |
| --- | --- | --- |
| 自写H1 | 用已知起点、轮速里程计和传感器外参，把有效二维回波变到同一坐标系；5 cm栅格至少命中一次就保留，只累计、不回撤，不用H1时序过滤。 | 冻结后用AMCL |
| Practice：SRRG二维对照 | 用SRRG每帧当时估计的传感器位姿直接累计回波；历史累计点不按最终图优化结果重新投影。SRRG输出另含地图维护与图优化。 | 冻结后用AMCL |
| Practice：Raw／DUFOMap／BeautyMap三维对照 | 用受控建图A提供的传感器位姿变换并拼接三维扫描，不调用DUFOMap或BeautyMap清理。该A使用提供的仿真位姿。 | 冻结后用GICP；B不输入真值 |

因此，不同实验的Raw不是同一张图，位姿来源也不相同；只能在各自匹配的对照内比较。SRRG这一组是包含位姿优化与地图维护的端到端对照，不是只改变删除规则的消融。当前H1干预还包含自写位姿对齐，Raw不含该对齐；仅清理／仅对齐消融区分两者贡献。H2基线另称Off，只关闭逐点运动补偿；FAST-LIO实践的Off仍保留LiDAR–IMU估计。


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

| 地图 | XY RMSE / cm | yaw / ° | 定位B实录（点击看MP4） |
| --- | --- | --- | --- |
| Raw | 5.03 | 2.88 | <a href="../results/reference/direction-20261016-v2/2d-static/executions/raw.mp4"><img src="../results/reference/direction-20261016-v2/2d-static/executions/raw.gif" width="320" loading="lazy" alt="Raw · localization B"></a> |
| SRRG | 5.84 | 2.91 | <a href="../results/reference/direction-20261016-v2/2d-static/executions/srrg.mp4"><img src="../results/reference/direction-20261016-v2/2d-static/executions/srrg.gif" width="320" loading="lazy" alt="SRRG · localization B"></a> |


[评分](../results/reference/direction-20261016-v2/2d-static/time-grid-score.json)

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

| 地图 | XY RMSE / cm | yaw / ° | 定位B实录（点击看MP4） |
| --- | --- | --- | --- |
| Raw | 5.53 | 0.76 | <a href="../results/reference/direction-20261016-v2/2d-dynamic/executions/raw.mp4"><img src="../results/reference/direction-20261016-v2/2d-dynamic/executions/raw.gif" width="320" loading="lazy" alt="Raw · localization B"></a> |
| SRRG | 5.13 | 0.70 | <a href="../results/reference/direction-20261016-v2/2d-dynamic/executions/srrg.mp4"><img src="../results/reference/direction-20261016-v2/2d-dynamic/executions/srrg.gif" width="320" loading="lazy" alt="SRRG · localization B"></a> |


[评分](../results/reference/direction-20261016-v2/2d-dynamic/time-grid-score.json)

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

| 地图 | XY RMSE / cm | yaw / ° | 定位B实录（点击看MP4） |
| --- | --- | --- | --- |
| Raw | 113.30 | 1.38 | <a href="../results/reference/direction-20261016-v2/2d-corridor/executions/degraded_raw.mp4"><img src="../results/reference/direction-20261016-v2/2d-corridor/executions/degraded_raw.gif" width="320" loading="lazy" alt="Raw · localization B"></a> |
| SRRG | 102.72 | 1.08 | <a href="../results/reference/direction-20261016-v2/2d-corridor/executions/degraded_srrg.mp4"><img src="../results/reference/direction-20261016-v2/2d-corridor/executions/degraded_srrg.gif" width="320" loading="lazy" alt="SRRG · localization B"></a> |


[评分](../results/reference/direction-20261016-v2/2d-corridor/time-grid-score.json)

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

| 点补偿 | 地图 RMSE / cm ↓ |
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

| A点补偿 | XYZ RMSE / cm | 旋转 / ° | 定位B实录（点击看MP4） |
| --- | --- | --- | --- |
| 关 | 14.03 | 3.62 | <a href="../results/reference/direction-20261016-v2/fastlio-B/executions/no_deskew.mp4"><img src="../results/reference/direction-20261016-v2/fastlio-B/executions/no_deskew.gif" width="320" loading="lazy" alt="关 map · localization B"></a> |
| 开 | 2.04 | 0.87 | <a href="../results/reference/direction-20261016-v2/fastlio-B/executions/deskew.mp4"><img src="../results/reference/direction-20261016-v2/fastlio-B/executions/deskew.gif" width="320" loading="lazy" alt="开 map · localization B"></a> |


[评分](../results/reference/direction-20261016-v2/fastlio-B/score-3d.json)

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

### 三维地图与独立定位

本轮重新采集三维A，执行Raw／DUFOMap／BeautyMap清图，再冻结地图、另采B；三组共享B点云和固定GICP参数。A/B均为Gazebo＋RViz实时录屏；B不更新地图。

A显示16线XYZ实时点云及墙体高度，采用斜视角；清图仍用给定仿真位姿拼接，以隔离清图影响，本项未验证完整三维SLAM。B：灰色＝冻结地图，绿色＝当前扫描，粉色＝估计位姿，青色＝估计轨迹；B不输入真值。

这是受控仿真：三维雷达未配置噪声模型，B使用轮式里程计与固定起点偏差（0.25 m、0.15 m、0.12 rad）；未测全局重定位或完整导航。冻结只停止更新，清图是否改善定位需看B误差。

本轮XYZ/旋转RMSE按三组共同的扫描时间戳计算，真值插值到同一时刻；旧表的10 Hz最新位姿评分混入了输出滞后，不能与本轮直接比较。
[维度、地图与评分核查](../results/reference/practice-3d-visible-20261016/audit.json) · [历史记录](../results/reference/practice-frozen-20261016)

<a id="scene-static-3d"></a>

#### 静态 · 3D

**A · 地图清理**

| 地图 | SA ↑ |
| --- | --- |
| Raw | 100.00% |
| DUFOMap | 99.99% |
| BeautyMap | 87.71% |


| A · 三维实时采集 | A · 清图结果回放（Raw / DUFOMap / BeautyMap） |
| --- | --- |
| <a href="../results/reference/practice-3d-visible-20261016/static-A/execution.mp4"><img src="../results/reference/practice-3d-visible-20261016/static-A/execution.gif" width="420" loading="lazy" alt="live 3D mapping A acquisition"></a> | <a href="../results/reference/practice-3d-visible-20261016/static-A/cleaning-review/result.mp4"><img src="../results/reference/practice-3d-visible-20261016/static-A/cleaning-review/result.gif" width="420" loading="lazy" alt="saved map cleaning results"></a> |


右侧展示已保存的清图结果，不是新推理；点击GIF可看完整MP4。

[A采集记录](../results/reference/practice-3d-visible-20261016/static-A/record.json) · [清图展示记录](../results/reference/practice-3d-visible-20261016/static-A/cleaning-review/record.json)

[建图A处理记录](../results/reference/practice-3d-visible-20261016/static-A/maps/record.json)

<a id="scene-static-3d-b"></a>

**B · 冻结地图后定位**

<!-- HOME_EXPERIMENT_TABLE -->
| 冻结地图 | XYZ RMSE / cm ↓ | 旋转 RMSE / ° | 定位B实录（点击看MP4） | 证据 |
| --- | --- | --- | --- | --- |
| Raw | 0.92 | 0.16 | <a href="../results/reference/practice-3d-visible-20261016/static-B/executions/raw.mp4"><img src="../results/reference/practice-3d-visible-20261016/static-B/executions/raw.gif" width="480" loading="lazy" alt="Raw · localization B"></a> | [记录](../results/reference/practice-3d-visible-20261016/static-B/record.json) |
| DUFOMap | 0.98 | 0.18 | <a href="../results/reference/practice-3d-visible-20261016/static-B/executions/dufomap.mp4"><img src="../results/reference/practice-3d-visible-20261016/static-B/executions/dufomap.gif" width="480" loading="lazy" alt="DUFOMap · localization B"></a> | [记录](../results/reference/practice-3d-visible-20261016/static-B/record.json) |
| BeautyMap | 1.14 | 0.21 | <a href="../results/reference/practice-3d-visible-20261016/static-B/executions/beautymap.mp4"><img src="../results/reference/practice-3d-visible-20261016/static-B/executions/beautymap.gif" width="480" loading="lazy" alt="BeautyMap · localization B"></a> | [记录](../results/reference/practice-3d-visible-20261016/static-B/record.json) |
<!-- /HOME_EXPERIMENT_TABLE -->

[共同扫描时刻评分](../results/reference/practice-3d-visible-20261016/static-B/score.json) · 共同有效扫描：458/600

有效扫描输出比例：Raw 87.83%, DUFOMap 86.83%, BeautyMap 97.33%；仅表示有输出，不是定位成功率，RMSE只覆盖共同有效扫描。

DUFOMap仅删除39/684477个点，15 cm占据格与Raw一致；静态组没有动态污染，预期定位变化很小。

**分析：**
<!-- PRACTICE_ANALYSIS:scene-static-3d -->

<!-- /PRACTICE_ANALYSIS:scene-static-3d -->

[↑ 目录](#practice-index)

<a id="scene-dynamic-3d"></a>

#### 动态 · 3D

**A · 地图清理**

| 地图 | DA ↑ | SA ↑ |
| --- | --- | --- |
| Raw | 0.00% | 100.00% |
| DUFOMap | 52.20% | 99.99% |
| BeautyMap | 71.81% | 87.33% |


| A · 三维实时采集 | A · 清图结果回放（Raw / DUFOMap / BeautyMap） |
| --- | --- |
| <a href="../results/reference/practice-3d-visible-20261016/dynamic-A/execution.mp4"><img src="../results/reference/practice-3d-visible-20261016/dynamic-A/execution.gif" width="420" loading="lazy" alt="live 3D mapping A acquisition"></a> | <a href="../results/reference/practice-3d-visible-20261016/dynamic-A/cleaning-review/result.mp4"><img src="../results/reference/practice-3d-visible-20261016/dynamic-A/cleaning-review/result.gif" width="420" loading="lazy" alt="saved map cleaning results"></a> |


右侧展示已保存的清图结果，不是新推理；点击GIF可看完整MP4。

[A采集记录](../results/reference/practice-3d-visible-20261016/dynamic-A/record.json) · [清图展示记录](../results/reference/practice-3d-visible-20261016/dynamic-A/cleaning-review/record.json)

[建图A处理记录](../results/reference/practice-3d-visible-20261016/dynamic-A/maps/record.json)

<a id="scene-dynamic-3d-b"></a>

**B · 冻结地图后定位**

<!-- HOME_EXPERIMENT_TABLE -->
| 冻结地图 | XYZ RMSE / cm ↓ | 旋转 RMSE / ° | 定位B实录（点击看MP4） | 证据 |
| --- | --- | --- | --- | --- |
| Raw | 1.18 | 0.22 | <a href="../results/reference/practice-3d-visible-20261016/dynamic-B/executions/raw.mp4"><img src="../results/reference/practice-3d-visible-20261016/dynamic-B/executions/raw.gif" width="480" loading="lazy" alt="Raw · localization B"></a> | [记录](../results/reference/practice-3d-visible-20261016/dynamic-B/record.json) |
| DUFOMap | 1.00 | 0.17 | <a href="../results/reference/practice-3d-visible-20261016/dynamic-B/executions/dufomap.mp4"><img src="../results/reference/practice-3d-visible-20261016/dynamic-B/executions/dufomap.gif" width="480" loading="lazy" alt="DUFOMap · localization B"></a> | [记录](../results/reference/practice-3d-visible-20261016/dynamic-B/record.json) |
| BeautyMap | 1.39 | 0.25 | <a href="../results/reference/practice-3d-visible-20261016/dynamic-B/executions/beautymap.mp4"><img src="../results/reference/practice-3d-visible-20261016/dynamic-B/executions/beautymap.gif" width="480" loading="lazy" alt="BeautyMap · localization B"></a> | [记录](../results/reference/practice-3d-visible-20261016/dynamic-B/record.json) |
<!-- /HOME_EXPERIMENT_TABLE -->

[共同扫描时刻评分](../results/reference/practice-3d-visible-20261016/dynamic-B/score.json) · 共同有效扫描：554/600

有效扫描输出比例：Raw 96.50%, DUFOMap 95.17%, BeautyMap 99.67%；仅表示有输出，不是定位成功率，RMSE只覆盖共同有效扫描。

DA/SA描述动态删除与静态保留；删掉残影不保证GICP约束增强。误差未降低时，只支持清图结果。

**分析：**
<!-- PRACTICE_ANALYSIS:scene-dynamic-3d -->

<!-- /PRACTICE_ANALYSIS:scene-dynamic-3d -->

[↑ 目录](#practice-index)

<a id="scene-corridor-3d"></a>

#### 长廊 · 3D

**A · 地图清理**

| 地图 | SA ↑ |
| --- | --- |
| Raw | 100.00% |
| DUFOMap | 100.00% |
| BeautyMap | 99.84% |


| A · 三维实时采集 | A · 清图结果回放（Raw / DUFOMap / BeautyMap） |
| --- | --- |
| <a href="../results/reference/practice-3d-visible-20261016/corridor-A/execution.mp4"><img src="../results/reference/practice-3d-visible-20261016/corridor-A/execution.gif" width="420" loading="lazy" alt="live 3D mapping A acquisition"></a> | <a href="../results/reference/practice-3d-visible-20261016/corridor-A/cleaning-review/result.mp4"><img src="../results/reference/practice-3d-visible-20261016/corridor-A/cleaning-review/result.gif" width="420" loading="lazy" alt="saved map cleaning results"></a> |


右侧展示已保存的清图结果，不是新推理；点击GIF可看完整MP4。

[A采集记录](../results/reference/practice-3d-visible-20261016/corridor-A/record.json) · [清图展示记录](../results/reference/practice-3d-visible-20261016/corridor-A/cleaning-review/record.json)

[建图A处理记录](../results/reference/practice-3d-visible-20261016/corridor-A/maps/record.json)

<a id="scene-corridor-3d-b"></a>

**B · 冻结地图后定位**

<!-- HOME_EXPERIMENT_TABLE -->
| 冻结地图 | XYZ RMSE / cm ↓ | 旋转 RMSE / ° | 定位B实录（点击看MP4） | 证据 |
| --- | --- | --- | --- | --- |
| Raw | 756.40 | 5.65 | <a href="../results/reference/practice-3d-visible-20261016/corridor-B/executions/raw.mp4"><img src="../results/reference/practice-3d-visible-20261016/corridor-B/executions/raw.gif" width="480" loading="lazy" alt="Raw · localization B"></a> | [记录](../results/reference/practice-3d-visible-20261016/corridor-B/record.json) |
| DUFOMap | 449.10 | 0.49 | <a href="../results/reference/practice-3d-visible-20261016/corridor-B/executions/dufomap.mp4"><img src="../results/reference/practice-3d-visible-20261016/corridor-B/executions/dufomap.gif" width="480" loading="lazy" alt="DUFOMap · localization B"></a> | [记录](../results/reference/practice-3d-visible-20261016/corridor-B/record.json) |
| BeautyMap | 482.16 | 0.43 | <a href="../results/reference/practice-3d-visible-20261016/corridor-B/executions/beautymap.mp4"><img src="../results/reference/practice-3d-visible-20261016/corridor-B/executions/beautymap.gif" width="480" loading="lazy" alt="BeautyMap · localization B"></a> | [记录](../results/reference/practice-3d-visible-20261016/corridor-B/record.json) |
<!-- /HOME_EXPERIMENT_TABLE -->

[共同扫描时刻评分](../results/reference/practice-3d-visible-20261016/corridor-B/score.json) · 共同有效扫描：381/599

前50秒限制观测，随后恢复完整扫描；本轮三组均出现米级漂移。Raw与DUFOMap冻结地图逐字节相同；独立进程的扫描处理历史可能不同，单次定位差异不能解释为清图收益。

有效扫描输出比例：Raw 74.29%, DUFOMap 69.95%, BeautyMap 94.49%；仅表示有输出，不是定位成功率，RMSE只覆盖共同有效扫描。

**分析：**
<!-- PRACTICE_ANALYSIS:scene-corridor-3d -->

<!-- /PRACTICE_ANALYSIS:scene-corridor-3d -->

[↑ 目录](#practice-index)

<a id="scene-change-3d"></a>

#### 结构变化 · 3D

本组冻结静态A地图，在结构变化场景重新采集B；A表沿用这三张静态地图的清理评分。

**A · 地图清理**

| 地图 | SA ↑ |
| --- | --- |
| Raw | 100.00% |
| DUFOMap | 99.99% |
| BeautyMap | 87.71% |


| A · 三维实时采集 | A · 清图结果回放（Raw / DUFOMap / BeautyMap） |
| --- | --- |
| <a href="../results/reference/practice-3d-visible-20261016/static-A/execution.mp4"><img src="../results/reference/practice-3d-visible-20261016/static-A/execution.gif" width="420" loading="lazy" alt="live 3D mapping A acquisition"></a> | <a href="../results/reference/practice-3d-visible-20261016/static-A/cleaning-review/result.mp4"><img src="../results/reference/practice-3d-visible-20261016/static-A/cleaning-review/result.gif" width="420" loading="lazy" alt="saved map cleaning results"></a> |


右侧展示已保存的清图结果，不是新推理；点击GIF可看完整MP4。

[A采集记录](../results/reference/practice-3d-visible-20261016/static-A/record.json) · [清图展示记录](../results/reference/practice-3d-visible-20261016/static-A/cleaning-review/record.json)

[建图A处理记录](../results/reference/practice-3d-visible-20261016/static-A/maps/record.json)

<a id="scene-change-3d-b"></a>

**B · 冻结地图后定位**

<!-- HOME_EXPERIMENT_TABLE -->
| 冻结地图 | XYZ RMSE / cm ↓ | 旋转 RMSE / ° | 定位B实录（点击看MP4） | 证据 |
| --- | --- | --- | --- | --- |
| Raw | 1.06 | 0.23 | <a href="../results/reference/practice-3d-visible-20261016/change-B/executions/raw.mp4"><img src="../results/reference/practice-3d-visible-20261016/change-B/executions/raw.gif" width="480" loading="lazy" alt="Raw · localization B"></a> | [记录](../results/reference/practice-3d-visible-20261016/change-B/record.json) |
| DUFOMap | 1.08 | 0.24 | <a href="../results/reference/practice-3d-visible-20261016/change-B/executions/dufomap.mp4"><img src="../results/reference/practice-3d-visible-20261016/change-B/executions/dufomap.gif" width="480" loading="lazy" alt="DUFOMap · localization B"></a> | [记录](../results/reference/practice-3d-visible-20261016/change-B/record.json) |
| BeautyMap | 1.24 | 0.27 | <a href="../results/reference/practice-3d-visible-20261016/change-B/executions/beautymap.mp4"><img src="../results/reference/practice-3d-visible-20261016/change-B/executions/beautymap.gif" width="480" loading="lazy" alt="BeautyMap · localization B"></a> | [记录](../results/reference/practice-3d-visible-20261016/change-B/record.json) |
<!-- /HOME_EXPERIMENT_TABLE -->

[共同扫描时刻评分](../results/reference/practice-3d-visible-20261016/change-B/score.json) · 共同有效扫描：486/599

有效扫描输出比例：Raw 91.32%, DUFOMap 90.32%, BeautyMap 97.33%；仅表示有输出，不是定位成功率，RMSE只覆盖共同有效扫描。

**分析：**
<!-- PRACTICE_ANALYSIS:scene-change-3d -->

<!-- /PRACTICE_ANALYSIS:scene-change-3d -->

[↑ 目录](#practice-index)

<a id="practice-appendix"></a>

### 补充实验

<a id="supp-srrg"></a>

#### SRRG · 持久结构变化

| 方法 | SA | 新增结构覆盖 |
| --- | --- | --- |
| Raw | 100.00% | 100.00% |
| SRRG | 99.71% | 98.90% |


[记录](../results/reference/srrg-2d-large-change/record.json)

| SRRG changed-world A |
| --- |
| <a href="../results/reference/srrg-2d-large-change/execution.mp4"><img src="../results/reference/srrg-2d-large-change/execution.gif" width="340" loading="lazy" alt="SRRG changed-world A"></a> |


<a id="supp-srrg-b"></a>

**B · 冻结地图后定位**

冻结持久变化建图A的两张地图；在相同变化场景重新采集B，用相同AMCL定位。

| 冻结地图 | XY RMSE / cm ↓ | yaw RMSE / ° | 定位B实录（点击看MP4） | 证据 |
| --- | --- | --- | --- | --- |
| Raw | 5.40 | 2.86 | <a href="../results/reference/practice-frozen-20261016/srrg-change/executions/raw.mp4"><img src="../results/reference/practice-frozen-20261016/srrg-change/executions/raw.gif" width="320" loading="lazy" alt="Raw · localization B"></a> | [记录](../results/reference/practice-frozen-20261016/srrg-change/record.json) |
| SRRG | 4.36 | 2.65 | <a href="../results/reference/practice-frozen-20261016/srrg-change/executions/srrg.mp4"><img src="../results/reference/practice-frozen-20261016/srrg-change/executions/srrg.gif" width="320" loading="lazy" alt="SRRG · localization B"></a> | [记录](../results/reference/practice-frozen-20261016/srrg-change/record.json) |


[共同时间点评分](../results/reference/practice-frozen-20261016/srrg-change/score.json) · 共同有效样本：273/601

AMCL按运动阈值触发发布；上述样本数只计输出滞后≤0.15秒的共同时间点，不代表定位成功率。

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

自写方法实验。H1重用同一原始A重算地图，旧B用于开发消融；固定规则后，另采静态B一次、动态B三次。H2保留原单轮A/B。每轮对照共享扫描、里程计、AMCL参数与初始化。

| 实验 | 建图与指标 | 独立定位与指标 |
| --- | --- | --- |
| H1 旧B开发消融 | — | [↗](#h1-revision-ablation) |
| H1 静态保留 | [A](#own-static-a) | [B](#own-static-b) |
| H1 动态清理 | [A](#own-dynamic-a) | [B](#own-dynamic-b) |
| H2 里程计去畸变 | [A](#own-motion-a) | [B](#own-motion-b) |

设备同Practice的全向轮机器人；算法仅使用二维雷达和轮式里程计。H2将三个真实时刻的扇区组合为滚动扫描，保留各点原采样时刻；未使用FAST-LIO。

[自写清理](../src/slam_learning/runtime/own_mapping.py) · [自写对齐](../src/slam_learning/runtime/own_refinement.py) · [H1验证录制](../demo/record-h1-revision.ps1) · [采集前固定设置](../results/reference/h1-refined-20261016/confirmation-protocol.json)

H2录像阶段：静止0–7秒、慢转7–15秒、快转15–31秒、平移31–39秒。

<a id="h1-revision-ablation"></a>

### H1 · 旧B开发消融

旧规则SA损失6.95个百分点；A轮速位姿RMSE还有7.74 cm。只清理无法修正地图位姿偏差，因此最终加入自写鲁棒二维对齐。下表重跑相同旧B，只用于开发消融，不混入最终新B评分。

| 方法 | DA ↑ | SA ↑ | XY RMSE / cm ↓ |
| --- | --- | --- | --- |
| Raw | 5.13% | 99.50% | 5.72 |
| 旧逐格过滤 | 94.87% | 92.55% | 6.11 |
| 后续空闲确认（中间版） | 29.49% | 99.50% | 5.81 |
| 近邻时序：只清理 | 79.49% | 99.17% | 5.66 |
| 只做自写对齐 | 0.00% | 100.00% | 4.86 |
| 自写对齐＋清理（最终） | 58.97% | 99.67% | 4.41 |

[原生AMCL重跑记录](../results/reference/h1-refined-20261016/dynamic-replay/trial-1/record.json) · [原始负结果保留](../results/reference/own-hypotheses-20261016/dynamic-B/record.json)

只清理版本另采三次B：Raw 6.02 cm、只清理6.06 cm，仍未改善；该批次完整保留。下方主实验使用最终联合方法重新采集的B。 [只清理验证记录](../results/reference/h1-supported-20261016/confirmation-score.json)

<a id="own-static-a"></a>

### H1 · 静态保留 · A

| 对照 | SA ↑ |
| --- | --- |
| M₀ · Raw：轮速位姿累积 | 99.55% |
| M₁ · Align+Temporal：自写对齐＋清理 | 100.00% |

| 原始A采集实录（旧算法画面） | 同一A重放清图：灰Raw，蓝新版 |
| --- | --- |
| <a href="../results/reference/own-hypotheses-20261016/static-A/execution.mp4"><img src="../results/reference/own-hypotheses-20261016/static-A/execution.gif" width="420" loading="lazy" alt="H1 · 静态保留 original A"></a> | <a href="../results/reference/h1-refined-20261016/static-A/execution.mp4"><img src="../results/reference/h1-refined-20261016/static-A/execution.gif" width="420" loading="lazy" alt="H1 · 静态保留 revised A input replay"></a> |

[记录](../results/reference/h1-refined-20261016/static-A/record.json)

**分析：**
<!-- OWN_ANALYSIS:static-a -->

<!-- /OWN_ANALYSIS:static-a -->

<a id="own-static-b"></a>

### H1 · 静态保留 · B

另采B，冻结地图后使用相同AMCL。 本项为一次静态对照。

| 地图／AMCL | XY RMSE / cm ↓ | 定位实录（点击MP4） |
| --- | --- | --- |
| M₀ · Raw：轮速位姿累积 | 5.44 | <a href="../results/reference/h1-refined-20261016/static-B/executions/raw.mp4"><img src="../results/reference/h1-refined-20261016/static-B/executions/raw.gif" width="420" loading="lazy" alt="raw fresh B"></a> |
| M₁ · Align+Temporal：自写对齐＋清理 | 4.64 | <a href="../results/reference/h1-refined-20261016/static-B/executions/temporal.mp4"><img src="../results/reference/h1-refined-20261016/static-B/executions/temporal.gif" width="420" loading="lazy" alt="temporal fresh B"></a> |

[共同时间点评分](../results/reference/h1-refined-20261016/static-B/time-grid-score.json) · [记录](../results/reference/h1-refined-20261016/static-B/record.json)

**分析：**
<!-- OWN_ANALYSIS:static-b -->

<!-- /OWN_ANALYSIS:static-b -->

[↑ 目录](#hypothesis-test-index)

<a id="own-dynamic-a"></a>

### H1 · 动态清理 · A

| 对照 | DA ↑ | SA ↑ |
| --- | --- | --- |
| M₀ · Raw：轮速位姿累积 | 5.13% | 99.50% |
| M₁ · Align+Temporal：自写对齐＋清理 | 58.97% | 99.67% |

| 原始A采集实录（旧算法画面） | 同一A重放清图：灰Raw，蓝新版 |
| --- | --- |
| <a href="../results/reference/own-hypotheses-20261016/dynamic-A/execution.mp4"><img src="../results/reference/own-hypotheses-20261016/dynamic-A/execution.gif" width="420" loading="lazy" alt="H1 · 动态清理 original A"></a> | <a href="../results/reference/h1-refined-20261016/dynamic-A/execution.mp4"><img src="../results/reference/h1-refined-20261016/dynamic-A/execution.gif" width="420" loading="lazy" alt="H1 · 动态清理 revised A input replay"></a> |

[记录](../results/reference/h1-refined-20261016/dynamic-A/record.json)

**分析：**
<!-- OWN_ANALYSIS:dynamic-a -->

<!-- /OWN_ANALYSIS:dynamic-a -->

<a id="own-dynamic-b"></a>

### H1 · 动态清理 · B

另采B，冻结地图后使用相同AMCL。 下表为三次B的共同时间样本合并RMSE；GIF固定展示第1轮。

| 地图／AMCL | XY RMSE / cm ↓ | 定位实录（点击MP4） |
| --- | --- | --- |
| M₀ · Raw：轮速位姿累积 | 5.82 | <a href="../results/reference/h1-refined-20261016/dynamic-B/executions/raw.mp4"><img src="../results/reference/h1-refined-20261016/dynamic-B/executions/raw.gif" width="420" loading="lazy" alt="raw fresh B"></a> |
| M₁ · Align+Temporal：自写对齐＋清理 | 4.65 | <a href="../results/reference/h1-refined-20261016/dynamic-B/executions/temporal.mp4"><img src="../results/reference/h1-refined-20261016/dynamic-B/executions/temporal.gif" width="420" loading="lazy" alt="temporal fresh B"></a> |

| 轮次 | Raw / cm | Temporal / cm | 完整录像 |
| --- | --- | --- | --- |
| 1 | 4.95 | 4.75 | [Raw MP4](../results/reference/h1-refined-20261016/dynamic-B/executions/raw.mp4) · [Temporal MP4](../results/reference/h1-refined-20261016/dynamic-B/executions/temporal.mp4) |
| 2 | 5.55 | 4.56 | [Raw MP4](../results/reference/h1-refined-20261016/dynamic-B2/executions/raw.mp4) · [Temporal MP4](../results/reference/h1-refined-20261016/dynamic-B2/executions/temporal.mp4) |
| 3 | 6.52 | 4.69 | [Raw MP4](../results/reference/h1-refined-20261016/dynamic-B3/executions/raw.mp4) · [Temporal MP4](../results/reference/h1-refined-20261016/dynamic-B3/executions/temporal.mp4) |

[共同时间点评分](../results/reference/h1-refined-20261016/confirmation-score.json) · [记录](../results/reference/h1-refined-20261016/dynamic-B/record.json)

**分析：**
<!-- OWN_ANALYSIS:dynamic-b -->

<!-- /OWN_ANALYSIS:dynamic-b -->

[↑ 目录](#hypothesis-test-index)

<a id="own-motion-a"></a>

### H2 · 里程计去畸变 · A

| 对照 | 地图 RMSE / cm ↓ |
| --- | --- |
| M₀ · Off：不补偿 | 34.10 |
| M₁ · On：运动补偿 | 4.57 |

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
| M₀ · Off：不补偿 | 4.70 |
| M₁ · On：运动补偿 | 4.71 |

| M₀ · Off：不补偿 | M₁ · On：运动补偿 |
| --- | --- |
| <a href="../results/reference/own-hypotheses-20261016/motion-B/executions/off.mp4"><img src="../results/reference/own-hypotheses-20261016/motion-B/executions/off.gif" width="420" loading="lazy" alt="off B"></a> | <a href="../results/reference/own-hypotheses-20261016/motion-B/executions/deskew.mp4"><img src="../results/reference/own-hypotheses-20261016/motion-B/executions/deskew.gif" width="420" loading="lazy" alt="deskew B"></a> |

[共同时间点评分](../results/reference/own-hypotheses-20261016/motion-B/time-grid-score.json) · [记录](../results/reference/own-hypotheses-20261016/motion-B/record.json)

**分析：**
<!-- OWN_ANALYSIS:motion-b -->

<!-- /OWN_ANALYSIS:motion-b -->

[↑ 目录](#hypothesis-test-index)

H1用DA/SA评清图，静态对照只看SA；H2用地图到静态支持的单向RMSE评分。定位预热5秒后使用共同10 Hz时间点，最新输出最多滞后0.15秒；样本数与输出缺失情况见原始评分记录。建图指标改善但B误差不降时，只支持建图结论。
