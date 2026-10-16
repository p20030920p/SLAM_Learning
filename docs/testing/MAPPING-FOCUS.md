<a id="mapping-hypothesis-tests"></a>

## Hypothesis

<!-- SIMPLE_HYPOTHESES_V2 -->
<!-- OWN_HYPOTHESES_20261016 -->

| Question | Hypothesis and method | Controls | Metrics |
| --- | --- | --- | --- |
| H1 / Q1 | In 2D LiDAR mapping, structure observed in multiple earlier time bins corrects the current scan's position and heading; 0.5 s bins count returns within each 5 cm cell's 10 cm neighborhood and valid free rays crossing that cell; an occupied record is deleted only with at least three free-crossing bins and free evidence at least 1.5 times neighborhood hit support; the hypothesis is that this method removes more dynamic traces than wheel-pose accumulation while limiting static-reference coverage loss to one percentage point, and yields lower XY localization RMSE with independent B and identical AMCL on frozen maps. | M₀: wheel-pose accumulation / M₁: own alignment + cleaning | A: DA, SA; B: XY RMSE |
| H2 / Q2 | Wheel-odometry compensation for point timestamps reduces map and held-out localization error. | M₀: compensation off / M₁: on | A: map RMSE; B: XY RMSE |

Both interventions are implemented in this repository; AMCL is the common downstream localizer. Mirror identification still needs physical validation.

<a id="hypothesis-math"></a>

### Mathematical form

**Core: use temporal support for scan alignment and dynamic-trace cleaning to build a 2D map for subsequent localization.** H2 separately tests point-time compensation. Each equation group is explained below; **the three bold, boxed equations are the core algorithm equations**.

**Experiment convention.** A builds the maps; B is acquired independently. Within each experiment, $`M_0`$ is the baseline and $`M_1`$ the intervention. Build both from the same A, freeze them, then evaluate with identical B scans, odometry, AMCL parameters and initialization. Truth enters post-run evaluation only.

| Symbol | Meaning |
| --- | --- |
| $`T_k^o`$ / $`T_k`$ | Wheel-derived sensor pose / H1-corrected pose at frame $`k`$, both sensor-to-fixed-map transforms |
| $`c`$ / $`\mathbf x_c`$ | A 5 cm grid cell / its center |
| $`b`$ | A 0.5 s time bin; each evidence type contributes at most once per bin |
| $`\mathbf1[\cdot]`$ | Indicator: 1 if true, otherwise 0 |
| $`M`$ | A nonempty set of occupied-cell centers, distinguished from the full grid used by AMCL |

Coordinates are in metres; experiment tables convert distance errors to cm. Score point sets in the same frame before inflation; generate and inflate AMCL grids by the same rule across controls. An empty map is a mapping failure.

**1. Common evaluation equation: localization RMSE on frozen maps.**

```math
E_{{\rm loc},m}=\sqrt{\frac{1}{|\mathcal T|}\sum_{k\in\mathcal T}\|\hat{\mathbf p}_{m,k}-\mathbf p_k^*\|_2^2}.
```

$`\hat{\mathbf p}_{m,k}`$ is the estimated 2D robot position on $`M_m`$; $`\mathbf p_k^*`$ is position truth at the same time; $`m\in\{0,1\}`$. Square each position distance, average, then take the square root. Test localization improvement with $`E_{{\rm loc},1}<E_{{\rm loc},0}`$.

$`\mathcal T`$ contains only common times with valid outputs from both controls. Current scoring uses 10 Hz times after 5 s warmup and outputs no older than 0.15 s; an empty set is not scored. Across H1 trials, $`k`$ indexes both trial and time, pooling all common valid samples. Missing-output times are excluded, so this RMSE is not localization success rate. Complete navigation arrival outcomes were not measured.

**Evaluation scope.** Freeze the A maps and apply the same localizer to independent B to evaluate the effect of map changes on localization error. The current algorithm does not directly minimize AMCL error.

**H1: 2D scan-pose correction and temporal occupancy filtering.**

Wheel odometry supplies the initial scan pose; structure observed in multiple earlier time bins corrects its position and heading to reduce misaligned accumulation of static structure; the map uses 5 cm cells and observations are grouped into 0.5 s bins, counting returns within each cell's 10 cm neighborhood and valid free rays crossing that cell, once per evidence type per bin; rays stop 15 cm before returns; an occupied record is deleted only with at least three free-crossing bins and free evidence at least 1.5 times neighborhood hit support, while sparse observations or subsequent occlusion alone are not motion criteria.

The hypothesis is that this method removes more dynamic traces than wheel-pose accumulation while limiting observed static-reference coverage loss to one percentage point; frozen maps are evaluated with independently acquired B and identical AMCL configuration to test whether the intervention yields lower XY position RMSE; A's DA/SA evaluate cleaning and retention, and B's localization RMSE evaluates the downstream effect separately.

Raw accumulates wheel-derived poses only. The current intervention includes both alignment and cleaning; alignment-only / filter-only ablations distinguish their contributions. The equations below explain each step.

**2. Predict the current pose using the wheel increment.**

```math
T_{k,0}=T_{k-1}(T_{k-1}^o)^{-1}T_k^o.
```

$`(T_{k-1}^o)^{-1}T_k^o`$ is the wheel-derived motion between frames. Compose it with the previously corrected pose $`T_{k-1}`$ to obtain the current initial estimate $`T_{k,0}`$. Initialize the first frame using the known start and wheel pose; the algorithm does not read pose truth.

**3. Downweight poorer correspondences.** At each iteration set $`\mathbf p=T_k\mathbf z`$, where $`\mathbf z`$ is a 2D scan point; $`\mathbf q`$ is its nearest point in the previous reference:

```math
w_{\mathbf p}=\min\!\left(1,\frac{0.05}{\max(\|\mathbf p-\mathbf q\|_2,10^{-9})}\right).
```

Distances up to 5 cm receive weight 1; larger distances receive progressively smaller weights. $`10^{-9}`$ prevents division by zero. The weight describes correspondence reliability, not a probability of motion, and does not identify every moving object.

**4. Core equation I: robust scan alignment.**

```math
\boxed{\boldsymbol{\Delta T=\arg\min_{U\in\mathrm{SE}(2)}\sum_{(\mathbf p,\mathbf q)\in\mathcal C_k}w_{\mathbf p}\|U\mathbf p-\mathbf q\|_2^2}}
```

```math
T_k\leftarrow\Delta T T_k.
```

$`U\in\mathrm{SE}(2)`$ permits only 2D rotation and translation; $`\mathcal C_k`$ is the current correspondence set. Minimize the sum of weighted squared transformed distances, update the pose by the rigid increment $`\Delta T`$, and recompute correspondences each iteration, up to 12 iterations.

The reference $`\mathcal R_{k-1}`$ contains only retained prior-map positions with neighborhood support from at least three time bins. Correspondences must be within 0.30 m; retain the closest 70% with at least 30 pairs. Fall back to wheel prediction with fewer than 80 reference points, fewer than 30 pairs, or a total correction exceeding 0.15 m / 0.05 rad relative to prediction. These are implementation parameters, not novelty claims.

This module performs local sequential pose correction without global pose-graph optimization.

**5. Direct-hit evidence and candidate map.** Accumulate under corrected poses:

```math
h(c)=\sum_b\mathbf1[\text{hit at }c\text{ in bin }b],\qquad\widetilde M=\{\mathbf x_c:h(c)>0\}.
```

$`h(c)`$ counts bins that directly hit cell $`c`$; repeated high-rate returns within a bin count once. $`\widetilde M`$ contains positions hit at least once. It uses corrected poses and differs from the wheel-pose baseline $`M_0`$.

**6. Neighborhood hit support.**

```math
s(c)=\sum_b\mathbf1[\exists c':\|\mathbf x_{c'}-\mathbf x_c\|_2\le0.10,\ \text{hit at }c'\text{ in bin }b].
```

$`s(c)`$ counts bins with a hit within 10 cm of $`c`$. Returns from the same wall can still contribute support when small measurement or pose errors place them in adjacent cells. Neighborhood evidence changes decisions; it does not invent occupied points at unobserved positions.

**7. Free-crossing evidence.**

```math
f(c)=\sum_b\mathbf1[\text{free ray through }c\text{ in bin }b].
```

$`f(c)`$ counts bins with a valid measurement ray crossing $`c`$. Rays stop 15 cm before the return to allow endpoint uncertainty. Unobserved or occluded positions cannot simply be marked free. A bin can contribute to both $`s,f`$: these are evidence counts, not mutually exclusive probabilities. Different bins are not necessarily statistically independent either.

**8. Core equation II: trace-cleaning rule.**

```math
\boxed{\boldsymbol{M_1=\{\mathbf x_c\in\widetilde M:f(c)<3\ \lor\ f(c)<1.5s(c)\}}}
```

Equivalently, delete only when $`f(c)\ge3`$ and $`f(c)\ge1.5s(c)`$: at least three distinct bins supply free-space counterevidence, reaching 1.5 times the neighborhood hit support. A corner seen only once and never revisited is not deleted merely for being rare. The rule does not guarantee removal of every moving object.

**Deletion principle: deletion requires sufficient counterevidence; rare observations alone do not justify deletion.** The retained map and temporal support then inform the next alignment step, forming sequential feedback.

**9. Nearest distance used for scoring.**

```math
d(\mathbf q,M)=\min_{\mathbf x\in M}\|\mathbf q-\mathbf x\|_2.
```

Find the map point nearest reference position $`\mathbf q`$. A smaller distance means the reference position is closer to the map. This definition serves evaluation, not the algorithm's motion decision.

**10. Static coverage SA and trace removal DA.** $`S`$ is a nonempty set of observed static reference positions from A. $`D`$ contains historical dynamic positions later verified free by rays, excluding overlap with static support or current obstacles. Both controls share $`S,D`$, deduplicated in 10 cm cells, with matching tolerance $`r=0.15\,\mathrm m`$:

```math
\mathrm{SA}(M)=\frac{\sum_{\mathbf q\in S}\mathbf1[d(\mathbf q,M)\le r]}{|S|},\qquad\mathrm{DA}(M)=\frac{\sum_{\mathbf q\in D}\mathbf1[d(\mathbf q,M)>r]}{|D|}.
```

SA is the fraction of static reference positions still covered by the map; DA is the fraction of historical trace positions no longer covered. Formulas use 0–1; tables show percentages. DA is undefined for empty $`D`$. These are 2D position-coverage scores, not exact source-point retention or geometric accuracy. Truth and object labels construct evaluation references only and do not enter the algorithm.

**11. Cleaning-improvement condition and H1 prediction.**

```math
\mathrm{DA}(M_1)>\mathrm{DA}(M_0)\quad\land\quad\mathrm{SA}(M_1)\ge\mathrm{SA}(M_0)-0.01.
```

The study defines improved cleaning as removing more traces while losing at most one percentage point of static coverage relative to baseline. This concerns observed support; it establishes neither global completeness, geometric accuracy nor a solution to mirror artifacts.

H1 also requires independent-B localization improvement. The full prediction can be written together:

```math
\mathrm{DA}(M_1)>\mathrm{DA}(M_0),\qquad\mathrm{SA}(M_1)\ge\mathrm{SA}(M_0)-0.01,\qquad E_{{\rm loc},1}<E_{{\rm loc},0}.
```

**Validation protocol.** Old B is used for development ablation; parameters are fixed before final fresh B acquisition. Evaluate map cleaning and independent localization separately. The joint gain cannot be attributed entirely to dynamic removal.

**H2: bring point samples to a common reference time, then test map geometry and localization separately.**

**12. Core equation III: motion-distortion compensation.** $`\mathbf z_i=(x_i,y_i,1)^{\mathsf T}`$ is a local homogeneous point acquired at $`t_i`$. Wheel-odometry interpolation plus sensor extrinsics provides $`\hat T(t)\in\mathrm{SE}(2)`$ from that sensor frame to the fixed map frame. $`t_e`$ is scan end:

```math
\boxed{\boldsymbol{\bar{\mathbf z}_i=\hat T(t_e)^{-1}\hat T(t_i)\mathbf z_i}}
```

Read right to left: $`\hat T(t_i)`$ moves the point to the fixed frame, then $`\hat T(t_e)^{-1}`$ moves it into the scan-end sensor frame. $`M_0`$ treats mixed-time points as acquired at $`t_e`$; $`M_1`$ compensates first. Integrate both with $`\hat T(t_e)`$ and hold all other steps fixed. H2 does not additionally enable H1 filtering.

The transform expresses points acquired at different times in one reference frame. It compensates robot motion, not object motion; compensation quality depends on odometry accuracy.

**13. Map geometry error.** Construct static references $`S`$ afresh from this experiment's A and reuse nearest distance $`d`$:

```math
E_{\rm map}(M)=\sqrt{\frac1{|M|}\sum_{\mathbf x\in M}d(\mathbf x,S)^2}.
```

Find each map point's nearest static reference, square the distance, average and take the square root. This is a one-way map-to-observed-static-support distance and does not alone measure completeness. An empty map is a mapping failure.

**14. Joint H2 test condition.**

```math
E_{\rm map}(M_1)<E_{\rm map}(M_0)\quad\land\quad E_{{\rm loc},1}<E_{{\rm loc},0}.
```

After a lower geometry score, independently test for lower localization error. If only the first inequality holds, only geometry-score improvement is supported. H2 remains a single exploratory trial; consistent benefit requires repeat validation.

<a id="hypothesis-srrg-comparison"></a>

### Innovation and conceptual comparison with SRRG

**Innovation and conceptual comparison with SRRG.** Here SRRG refers to Lázaro et al., *Efficient Long-term Mapping in Dynamic Environments* (IROS 2018), and its 2D mapping code. It already includes point/normal registration, free-space fusion, a pose graph and long-term multi-session map maintenance. Alignment plus cleaning, or using free space to remove dynamics, is therefore not itself a first-of-its-kind contribution over SRRG. [Paper, Section III](https://iris.uniroma1.it/handle/11573/1340118).

| Aspect | Main idea in the SRRG paper | Current approach |
| --- | --- | --- |
| Map representation | 2D local point clouds with normals and a pose graph | Grid counts of hits, neighborhood support and free crossings |
| Registration | Point/normal correspondences with odometry initialization / prior | Robust point-to-point alignment to previously supported positions |
| Dynamic handling | Project to a common viewpoint, compare ranges, then merge, add or replace points | Accumulate free-space counterevidence across time bins; delete only when conditions hold |
| Small misalignments | Geometric correspondence and point-cloud merging | Neighborhood hits allow returns to fall into adjacent cells |
| System scope | Full SLAM, global graph optimization and long-term maintenance | Current local sequential intervention without global pose-graph or long-term multi-session mechanisms |
| Evaluation focus here | Practice the authors' map-maintenance pipeline | Relate cleaning / retention to independent localization on frozen maps |

**Candidate contribution: explicit neighborhood temporal evidence jointly selects registration references and decides trace deletion, with independent localization testing the map's downstream value.** The concrete difference is the organization of time bins, neighborhood support and deletion counterevidence. Parameter choices, local implementation and standard robust registration do not establish novelty. Independent B is an evaluation design; the algorithm does not directly optimize AMCL error. H2 uses standard relative-pose compensation and is not claimed as a separate first-of-its-kind contribution over SRRG.

Conservative evidence could reduce deletion caused by isolated anomalous observations while delaying adaptation to real changes; both need testing. The open research claim is whether this evidence design better balances static-support retention and trace removal under pose perturbations, sparse observations and dynamic occlusion. **These are implemented design differences, not established literature novelty. Metric effectiveness is not compared with SRRG here, and no performance superiority is claimed.**

<a id="hypothesis-pseudocode"></a>

### Pseudocode

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

[Implementation, experiments and recordings](../../README.md#hypothesis-test-index)
