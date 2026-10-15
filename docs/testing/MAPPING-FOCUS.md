<a id="mapping-hypothesis-tests"></a>

## Hypothesis

<!-- SIMPLE_HYPOTHESES_V2 -->
<!-- OWN_HYPOTHESES_20261016 -->

| Question | Hypothesis | Controls | Metrics |
| --- | --- | --- | --- |
| H1 / Q1 | Repeated hits plus free-ray confirmation reduce dynamic traces and improve held-out localization. | Own accumulation / own temporal cleaning | A: DA, SA; B: XY RMSE |
| H2 / Q2 | Wheel-odometry compensation for point timestamps reduces map and held-out localization error. | Own compensation off / on | A: Eₘ; B: XY RMSE |
| H3 / Q3 | Detecting geometric degeneracy and retaining reliable static structures that constrain the weak direction reduces along-corridor error. | Own uniform threshold / own degeneracy-aware cleaning | A: additional retained cells; B: along RMSE |

All three interventions are implemented in this repository; AMCL is the common downstream localizer. Mirror identification still needs physical validation.

<a id="hypothesis-math"></a>

### Mathematical form

A builds the maps; B is a separate acquisition. Freeze the maps and share B scans, odometry and AMCL settings across controls.

DA/SA measure removal and retention, not geometric or localization accuracy. B evaluates localization while moving through an existing map; complete navigation-task outcomes were not measured.

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

Proposed solution: estimate the weak direction from observed local surface normals, then lower the deletion threshold for structures that constrain that direction, have repeated hits and have no contradicting free rays. Here n is a local normal, G approximates translational constraints and v is the weakest direction.


```math
G=\sum_{c\in C}n_cn_c^{\mathsf T},\quad v_{\min}=\mathrm{eigvec}_{\min}(G),\quad R_c=\mathbf{1}[H_c\geq2,\ F_c=0,\ |n_c^{\mathsf T}v_{\min}|\gt0.7]
```

```math
D=\mathbf{1}[\lambda_{\min}(G)\lt0.25\lambda_{\max}(G)],\qquad K_c^{\rm protected}=\mathbf{1}[(H_c\geq5\land H_c\geq1.5F_c)\lor(D=1\land R_c=1)]
```

```math
E_{\parallel}=\sqrt{\frac1N\sum_t[u^{\mathsf T}(\hat p_t-p_t^\ast)]^2},\qquad E_{\parallel}(\mathrm{protected})\lt E_{\parallel}(\mathrm{strict})
```

Time bins: 0.5 s; free rays stop 15 cm before each return; static-loss tolerance ε = 1 percentage point. H3 keeps the corridor, route, sensors and localizer fixed and changes only the cleaning rule. It protects observed constraints; a corridor with no along-axis information still needs additional observations. Truth is used only for scoring.

<a id="hypothesis-pseudocode"></a>

### Pseudocode

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

[Implementation, experiments and recordings](../../README.md#hypothesis-test-index)
