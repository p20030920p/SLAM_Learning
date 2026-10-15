<a id="mapping-hypothesis-tests"></a>

## Hypothesis

<!-- SIMPLE_HYPOTHESES_V2 -->
<!-- OWN_HYPOTHESES_20261016 -->

| Question | Hypothesis | Controls | Metrics |
| --- | --- | --- | --- |
| H1 / Q1 | Temporal hit/free filtering removes more dynamic traces with at most one percentage point of static loss and improves held-out localization. | M₀: own accumulation / M₁: temporal filtering | A: DA, SA; B: XY RMSE |
| H2 / Q2 | Wheel-odometry compensation for point timestamps reduces map and held-out localization error. | M₀: compensation off / M₁: on | A: map RMSE; B: XY RMSE |

Both interventions are implemented in this repository; AMCL is the common downstream localizer. Mirror identification still needs physical validation.

<a id="hypothesis-math"></a>

### Mathematical form

**Experiment convention.** A builds the maps; B is acquired independently. In each experiment, $`M_0`$ is the baseline and $`M_1`$ the intervention. Build both from the same A, freeze them, and evaluate with the same B, AMCL parameters and initialization configuration.

$`M`$ denotes a nonempty point set of occupied-cell centers in the formulas below. Score pre-inflation points in the same frame; AMCL uses each arm's corresponding full grid, generated and inflated by the same rule. Coordinates are in metres; tables convert errors to cm. Empty maps are mapping failures.

**Localization improvement.** $`\hat{\mathbf p}_{m,k}`$ is the estimated 2D robot position on $`M_m`$, and $`\mathbf p_k^*`$ is truth at that time; $`m\in\{0,1\}`$. $`\mathcal T`$ contains common scoring times with valid outputs from both controls:

```math
E_{{\rm loc},m}=
\sqrt{\frac{1}{|\mathcal T|}\sum_{k\in\mathcal T}
\|\hat{\mathbf p}_{m,k}-\mathbf p_k^*\|_2^2}.
```
Compare $`E_{{\rm loc},1}<E_{{\rm loc},0}`$ directly, without another difference symbol. Current scoring uses 10 Hz times after 5 s warmup and outputs no older than 0.15 s; an empty common set is not scored. Truth is used only for post-run evaluation. B tests localization; complete navigation outcomes were not measured.

**H1: define improved dynamic-trace cleaning before testing the rule.**

$`S`$ is a nonempty set of observed static reference positions from A. $`D`$ contains historical dynamic positions later verified free by measured rays, excluding overlap with static support or current obstacles. Both controls share $`S,D`$; current scoring deduplicates in 10 cm cells. Pose truth and object labels construct evaluation references only and never enter the cleaner.

$`d(\mathbf q,M)`$ is the distance to the nearest map point, with fixed tolerance $`r=0.15\,\mathrm m`$:

```math
d(\mathbf q,M)=\min_{\mathbf x\in M}\|\mathbf q-\mathbf x\|_2.
```

```math
\mathrm{SA}(M)=\frac{\sum_{\mathbf q\in S}\mathbf1[d(\mathbf q,M)\le r]}{|S|},
\qquad
\mathrm{DA}(M)=\frac{\sum_{\mathbf q\in D}\mathbf1[d(\mathbf q,M)>r]}{|D|}.
```
Ratios in formulas are 0–1; tables display percentages. DA is undefined for empty $`D`$; static controls use SA only. These are coverage / noncoverage rates of 2D reference positions, not exact source-point retention.

**Operational relative definition: more dynamic traces are removed, with at most one percentage point of static-retention loss relative to the baseline.**

```math
\mathrm{DA}(M_1)>\mathrm{DA}(M_0)
\quad\land\quad
\mathrm{SA}(M_1)\ge\mathrm{SA}(M_0)-0.01.
```
This definition concerns dynamic traces on observed support; it does not establish global completeness, geometric accuracy or removal of mirror artifacts.

**Implementation rule.** $`c`$ is a cell, $`\mathbf x_c`$ its center, and $`b`$ a 0.5 s time bin. $`h(c)`$ counts bins with at least one endpoint hit; $`f(c)`$ counts bins with at least one truncated free ray through the cell. Count each once per bin; free rays stop 15 cm before a return:

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
Here $`M_0`$ is this experiment's Raw: 5 cm occupied cells accumulated using the known start and wheel-odometry poses, retaining cells hit at least once. Valid-range filtering, gridding and shared inflation still apply. $`M_1`$ adds only the temporal retention condition above.

**H1 to test:** the rule satisfies the cleaning criterion above and yields $`E_{{\rm loc},1}<E_{{\rm loc},0}`$. The values 3 and 1.5 are fixed heuristic parameters, not definitions of static structure or cleanliness; sparsely observed static cells may also be removed.

**H2: align point timestamps, then test geometry and localization separately.**

$`\mathbf z_i=(x_i,y_i,1)^{\mathsf T}`$ is a sensor-local homogeneous point acquired at $`t_i`$. Wheel odometry plus the sensor extrinsic provides $`\hat T(t)\in\mathrm{SE}(2)`$, mapping the instantaneous sensor frame to a fixed map frame. $`t_e`$ is the scan-end time:

```math
\bar{\mathbf z}_i=\hat T(t_e)^{-1}\hat T(t_i)\mathbf z_i.
```
Transform first to the fixed frame, then to the scan-end sensor frame. $`M_0`$ treats mixed-time points as acquired at $`t_e`$; $`M_1`$ applies the compensation above. Both are integrated using $`\hat T(t_e)`$ with all other steps fixed; H2 does not additionally enable H1 filtering.

Construct $`S`$ afresh from this experiment's A and use the same nearest-distance definition $`d`$. Current geometry scoring is:

```math
E_{\rm map}(M)=
\sqrt{\frac1{|M|}\sum_{\mathbf x\in M}d(\mathbf x,S)^2}.
```
This is a one-way map-to-observed-static-support distance RMSE; it does not alone measure completeness. An empty map is a mapping failure, not a geometric improvement.

**H2 to test:**

```math
E_{\rm map}(M_1)<E_{\rm map}(M_0)
\quad\land\quad
E_{{\rm loc},1}<E_{{\rm loc},0}.
```
If only the first inequality holds, only the geometry-score claim is supported. These are single exploratory trials; repeat trials are needed to establish consistent benefit.

<a id="hypothesis-pseudocode"></a>

### Pseudocode

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

[Implementation, experiments and recordings](../../README.md#hypothesis-test-index)
