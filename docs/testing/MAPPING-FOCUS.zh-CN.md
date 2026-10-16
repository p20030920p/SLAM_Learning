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

**实验约定。** A用于建图，B为另一次独立采集。每项实验中，$`M_0`$是基线图，$`M_1`$是干预图；两图由同一份A生成，再冻结，用同一份B、相同AMCL参数与初始化配置评价定位。

$`M`$在下式中表示地图占据格中心组成的非空点集。点集评分在同一坐标系、膨胀前进行；AMCL使用各组对应的完整栅格图，生成与膨胀规则一致。坐标以米计，展示表将误差换算成cm。空图记为建图失败。

**定位是否改善。** $`\hat{\mathbf p}_{m,k}`$是在地图$`M_m`$中估计的机器人二维位置，$`\mathbf p_k^*`$是同一时刻的真值；$`m\in\{0,1\}`$。$`\mathcal T`$为两组都有有效输出的共同评分时间集合：

```math
E_{{\rm loc},m}=
\sqrt{\frac{1}{|\mathcal T|}\sum_{k\in\mathcal T}
\|\hat{\mathbf p}_{m,k}-\mathbf p_k^*\|_2^2}.
```
直接比较$`E_{{\rm loc},1}<E_{{\rm loc},0}`$，不再另设差值符号。当前使用预热5秒后的10 Hz时间点，输出滞后不超过0.15秒；不为空的共同时间集才评分。H1多轮时，$`k`$同时索引轮次与时刻，合并全部共同有效样本。真值只用于事后评分，B评的是定位，尚未测完整导航到达效果。

**H1：先定义“动态残影清理改善”，再检验规则。**

$`S`$是A中已观测静态参考位置组成的非空集合，$`D`$是A中后来被射线验证为空、且不与静态支持或当前障碍物重叠的历史动态位置集合。两组共用相同$`S,D`$；本轮按10 cm格去重，位姿真值与物体标签只用于构造评分参照，不输入清图算法。

$`d(\mathbf q,M)`$是参考位置到最近地图点的距离，匹配容差固定为$`r=0.15\,\mathrm m`$：

```math
d(\mathbf q,M)=\min_{\mathbf x\in M}\|\mathbf q-\mathbf x\|_2.
```

```math
\mathrm{SA}(M)=\frac{\sum_{\mathbf q\in S}\mathbf1[d(\mathbf q,M)\le r]}{|S|},
\qquad
\mathrm{DA}(M)=\frac{\sum_{\mathbf q\in D}\mathbf1[d(\mathbf q,M)>r]}{|D|}.
```
公式中的比例取0–1，表格换成百分数。$`D`$为空时不定义DA；静态对照只看SA。这是二维参考位置的覆盖／未覆盖比例，不是逐个原始点的保留追踪。

**本研究的相对定义：动态残影删除更多，且静态保留相对基线损失不超过1个百分点，才称“动态残影清理改善”。**

```math
\mathrm{DA}(M_1)>\mathrm{DA}(M_0)
\quad\land\quad
\mathrm{SA}(M_1)\ge\mathrm{SA}(M_0)-0.01.
```
该定义只针对已观测支持上的动态残影；不据此宣称整张地图完整、几何准确或镜面问题已解决。

**修订为联合建图方法。** Raw仍用轮速位姿直接累积。干预先用前序时序支持点修正逐帧对齐，再清理动态残影；这包含位姿修正与清理，不是只改变删除规则。两项贡献由“只清理／只对齐”消融区分。

$`T_k^o`$是第$`k`$帧的轮速传感器位姿，$`T_k`$是修正位姿；均从传感器系到固定地图系。$`\mathcal R_{k-1}`$来自前序保留地图中至少3个时间箱支持的点，算法不读取真值。轮速增量给出预测：

```math
T_{k,0}=T_{k-1}(T_{k-1}^o)^{-1}T_k^o.
```

$`\mathbf z`$为二维扫描点，$`T\mathbf z`$指旋转和平移后的二维坐标。每次迭代令$`\mathbf p=T_k\mathbf z`$，在$`\mathcal R_{k-1}`$找最近点$`\mathbf q`$；从距离小于0.30 m的对应中保留最接近的70%（至少30对），组成$`\mathcal C_k`$。按下式求二维刚体增量，最多12次：

```math
w_{\mathbf p}=\min\!\left(1,\frac{0.05}{\max(\|\mathbf p-\mathbf q\|_2,10^{-9})}\right),
```

```math
\Delta T=\arg\min_{U\in\mathrm{SE}(2)}\sum_{(\mathbf p,\mathbf q)\in\mathcal C_k}
w_{\mathbf p}\|U\mathbf p-\mathbf q\|_2^2,
\qquad T_k\leftarrow\Delta T T_k.
```
参照不足80点、对应不足30对或总修正超过0.15 m／0.05 rad时使用轮速预测。初帧使用已知起点与轮速位姿。然后在修正位姿下统计5 cm栅格：$`h(c)`$为该格命中时间箱数，$`s(c)`$为0.10 m近邻命中支持箱数，$`f(c)`$为空闲穿越箱数；每箱各最多一次。自由射线在回波前15 cm停止。

```math
h(c)=\sum_b\mathbf1[\text{hit at }c\text{ in bin }b],
\qquad \widetilde M=\{\mathbf x_c:h(c)>0\}.
```

```math
s(c)=\sum_b\mathbf1[\exists c':\|\mathbf x_{c'}-\mathbf x_c\|_2\le0.10,
\ \text{hit at }c'\text{ in bin }b].
```

```math
f(c)=\sum_b\mathbf1[\text{free ray through }c\text{ in bin }b].
```

```math
M_1=\{\mathbf x_c\in \widetilde M:f(c)<3\ \lor\ f(c)<1.5s(c)\}.
```
即：至少3个空闲时间箱，且空闲证据至少为近邻命中支持的1.5倍，才删除。同一箱可同时计入$`s,f`$，它们是证据计数，不是互斥概率。少见本身不等于动态；邻域支持允许同一墙面的回波落在相邻格中，不向未观测格补点。算法不使用语义标签或真值；两组距离筛选、栅格化、自由区与膨胀规则相同。

**要检验的H1：**联合方法相对轮速Raw满足清理改善条件，并降低另采B的定位误差。所有参数在最终新B采集前固定；旧B用于开发消融。旧逐格规则和只清理版本的负结果全部保留，不能将联合方法的收益全归因于动态去除。

**H2：统一采样时刻，再分别检验几何与定位。**

$`\mathbf z_i=(x_i,y_i,1)^{\mathsf T}`$是在$`t_i`$采集的传感器局部齐次点；$`\hat T(t)\in\mathrm{SE}(2)`$为轮式里程计加传感器外参得到的估计变换，从$`t`$时刻传感器坐标系变到固定地图坐标系。$`t_e`$为扫描末时刻：

```math
\bar{\mathbf z}_i=\hat T(t_e)^{-1}\hat T(t_i)\mathbf z_i.
```
先变到固定坐标系，再变回扫描末时刻坐标系。$`M_0`$不补偿，直接把混合时刻的点当作$`t_e`$采集；$`M_1`$先按上式补偿。两图融合时都用$`\hat T(t_e)`$，其他步骤相同；H2不额外开启H1过滤。

从本项A重新构造静态参照$`S`$，沿用最近距离$`d`$，当前几何评分明确定义为：

```math
E_{\rm map}(M)=
\sqrt{\frac1{|M|}\sum_{\mathbf x\in M}d(\mathbf x,S)^2}.
```
这是“地图到已观测静态支持”的单向距离RMSE，不能单独评价地图完整性；空图判为建图失败，不算几何改善。

**要检验的H2：**

```math
E_{\rm map}(M_1)<E_{\rm map}(M_0)
\quad\land\quad
E_{{\rm loc},1}<E_{{\rm loc},0}.
```
若只有前一项成立，只支持几何评分改善；不能推断定位改善。当前均为单轮探索，稳定收益仍需重复验证。

<a id="hypothesis-pseudocode"></a>

### 伪代码

```text
for test, scene in [(H1, static), (H1, dynamic), (H2, motion)]:
    A = acquire_scans_and_wheel_odometry(scene)
    if test == H1:
        M0 = integrate_A_with_wheel_poses(A)
        corrected_poses = align_scans_to_previous_supported_map(A)  # own implementation
        h, s, f = initialize_grid_evidence()
        for bin in A.project_with(corrected_poses).time_bins(seconds=0.5):
            add_hits_once_per_cell(h, bin)
            add_neighborhood_hit_support_once(s, bin, radius=0.10)
            add_truncated_free_ray_evidence_once(f, bin, stop_before_return=0.15)
        M1 = cell_centers_where((h > 0) & ((f < 3) | (f < 1.5 * s)))
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
