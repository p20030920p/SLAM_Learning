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

[实现、实验与录像](../HOME.zh-CN.md#hypothesis-test-index)
