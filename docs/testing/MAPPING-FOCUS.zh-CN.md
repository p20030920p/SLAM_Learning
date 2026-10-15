<a id="mapping-hypothesis-tests"></a>

## 假设

<!-- SIMPLE_HYPOTHESES_V2 -->
<!-- OWN_HYPOTHESES_20261016 -->

| 问题 | 一句话假设 | 对照方法 | 指标 |
| --- | --- | --- | --- |
| H1 / Q1 | 跨时间命中与空闲证据过滤，在静态保留损失≤1个百分点时减少动态残影，并改善独立定位。 | M₀：自写累积图 / M₁：自写时序过滤 | A：DA、SA；B：XY RMSE |
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
直接比较$`E_{{\rm loc},1}<E_{{\rm loc},0}`$，不再另设差值符号。当前使用预热5秒后的10 Hz时间点，输出滞后不超过0.15秒；不为空的共同时间集才评分。真值只用于事后评分，B评的是定位，尚未测完整导航到达效果。

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

**实现规则。** $`c`$为栅格，$`\mathbf x_c`$为其中心，$`b`$为0.5秒时间箱。$`h(c)`$统计至少有一次回波命中的时间箱数，$`f(c)`$统计至少有一次截断自由射线穿过的时间箱数；每箱各最多计一次，自由射线在回波前15 cm停止：

```math
h(c)=\sum_b\mathbf1[\text{hit in bin }b\text{ at }c],
\qquad
f(c)=\sum_b\mathbf1[\text{free ray in bin }b\text{ through }c].
```

```math
M_0=\{\mathbf x_c:h(c)>0\},
\qquad
M_1=\{\mathbf x_c:h(c)\ge3\ \land\ h(c)\ge1.5f(c)\}.
```
这里$`M_0`$就是本项Raw：已知起点＋轮速里程计位姿累积的5 cm占据格，至少命中一次就保留；有效距离筛选、栅格化与公共膨胀仍然执行。$`M_1`$仅增加上述时序保留条件。

**要检验的H1：**该规则满足上述清理改善条件，并使$`E_{{\rm loc},1}<E_{{\rm loc},0}`$。3与1.5是本轮固定的启发式参数；规则本身不是“静态”或“干净”的定义，低命中的静态结构也可能被删。

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
        h, f = count_time_bins_with_hits_and_free_rays(A, bin_seconds=0.5)
        M0 = cell_centers_where(h > 0)
        M1 = cell_centers_where((h >= 3) & (h >= 1.5 * f))
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
