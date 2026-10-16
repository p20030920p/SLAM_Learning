<a id="mapping-hypothesis-tests"></a>

## 假设

<!-- SIMPLE_HYPOTHESES_V2 -->
<!-- OWN_HYPOTHESES_20261016 -->

| 问题 | 假设与具体做法 | 对照方法 | 指标 |
| --- | --- | --- | --- |
| H1 / Q1 | 在二维激光建图中，利用前序多个时间箱持续观测到的结构修正当前扫描的位置和朝向；以0.5秒为时间箱，对每个5 cm栅格分别统计其10 cm邻域获得回波命中、以及有效射线穿过该格的时间箱数；仅当空闲穿越至少达到3个时间箱，且次数不少于邻域命中支持的1.5倍时，删除该格的占据记录；假设该方法相对轮速直接累积能够删除更多动态残影，将静态参考位置覆盖率的损失控制在1个百分点以内，并在冻结地图后，使用独立采集B和相同AMCL获得更低的XY定位RMSE。 | M₀：轮速累积图 / M₁：自写对齐＋清理 | A：DA、SA；B：XY RMSE |
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

**评价范围。**冻结A地图后，使用同一定位器处理独立B，评估地图变化对定位误差的影响。当前算法没有直接最小化AMCL误差。

**H1：二维扫描位姿修正与跨时间占据过滤。**

轮速里程计提供当前扫描的初始位姿；前序多个时间段持续观测到的结构用于修正扫描的位置和朝向，减少同一静态结构在地图中的错位累积；地图采用5 cm栅格，观测按0.5秒划分时间箱，每个格子分别累计10 cm邻域获得回波命中、以及有效射线穿过该格的时间箱数，每类证据在同一箱内最多计一次；射线在回波前15 cm停止；仅当空闲穿越至少达到3个时间箱，且次数不少于邻域命中支持的1.5倍时，删除该格占据记录，观测稀疏或后续遮挡本身不作为动态判据。

假设该方法相比轮速直接累积图能够删除更多动态残影，同时将已观测静态参考位置覆盖率的损失控制在1个百分点以内；地图冻结后，使用另一轮独立采集的B和相同AMCL配置，检验干预图是否获得更低的XY位置RMSE；A的DA／SA评价清理与保留，B的定位RMSE评价后续定位，两者分别判断。

Raw只用轮速位姿累积；当前干预同时包含对齐与清理，两项贡献需用“只对齐／只清理”消融区分。下面的公式分别对应这些步骤。

**2．轮速增量预测当前位姿。**

```math
T_{k,0}=T_{k-1}(T_{k-1}^o)^{-1}T_k^o.
```

$`(T_{k-1}^o)^{-1}T_k^o`$为轮速给出的相邻帧运动；将它接在上一帧已修正位姿$`T_{k-1}`$上，得到当前初值$`T_{k,0}`$。初帧使用已知起点与轮速位姿，算法不读取位姿真值。

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

该模块执行局部逐帧位姿修正，当前未包含全局位姿图优化。

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

**删除原则：删除需要足够反证，观察次数少本身不足以删除。** 清理后的地图及其时序支持供下一帧对齐使用，形成逐帧反馈。

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

**验证协议。**旧B用于开发消融，最终新B采集前固定参数。地图清理与独立定位分别评价；联合方法的收益不能全部归因于动态删除。

**H2：统一点的采样参考时刻，再分别检验地图几何和定位。**

**12．核心公式三：运动畸变补偿。** $`\mathbf z_i=(x_i,y_i,1)^{\mathsf T}`$是在$`t_i`$采集的局部齐次点；$`\hat T(t)\in\mathrm{SE}(2)`$由轮速插值和传感器外参得到，从该时刻传感器系变换到固定地图系。$`t_e`$为扫描末时刻：

```math
\boxed{\boldsymbol{\bar{\mathbf z}_i=\hat T(t_e)^{-1}\hat T(t_i)\mathbf z_i}}
```

从右向左理解：先用$`\hat T(t_i)`$将点放入固定坐标系，再用$`\hat T(t_e)^{-1}`$转入扫描末时刻坐标系。$`M_0`$把混合时刻的点直接当作$`t_e`$采集；$`M_1`$先补偿。两图都用$`\hat T(t_e)`$融合，其他步骤相同；H2不额外开启H1过滤。

该变换将不同时刻采集的点统一到同一参考时刻，补偿机器人自身运动，不自动补偿物体自身运动；补偿质量依赖轮速估计。

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

[实现、实验与录像](../HOME.zh-CN.md#hypothesis-test-index)
