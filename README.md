<div align="center">

# SLAM Learning

**Robust localization and SLAM in dynamic environments**

Dynamic map cleaning · Static structure retention · Downstream localization

[![CPU reproducibility](https://github.com/p20030920p/SLAM_Learning/actions/workflows/ci.yml/badge.svg)](https://github.com/p20030920p/SLAM_Learning/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.10-3776AB)](src/pyproject.toml)

English | [中文](docs/HOME.zh-CN.md)

[Physical test problems](#problem-getting-from-physical-test) · [Direction](#direction-analysis) · [Open question](#open-question) · [Hypothesis](#hypothesis) · [Related works](#related-works) · [Metrics](#metrics)

[Practice](#practice-index) · [Hypothesis test](#hypothesis-test-index)

</div>

## Problem getting from Physical test

<a id="physical-test-mirror"></a>

### Mirror and incomplete mapping

| Figure 1: mirror | Figure 2: incomplete mapping associated with the mirror |
| --- | --- |
| <a id="physical-test-mirror-photo"></a><a href="docs/media/physical-test/20261015-mirror/mirror-surface.jpg"><img src="docs/media/physical-test/20261015-mirror/mirror-surface.jpg" width="420" alt="Figure 1: mirror"></a> | <a id="physical-test-mirror-map"></a><a href="docs/media/physical-test/20261015-mirror/mirror-incomplete-map.png"><img src="docs/media/physical-test/20261015-mirror/mirror-incomplete-map.png" width="420" alt="Figure 2: incomplete mapping associated with the mirror"></a> |

Observation from Figure 2: the mirror region lacks a usable mapped boundary, which also removes a reference for localization.

**Analysis:**
<!-- PHYSICAL_TEST_ANALYSIS:mirror -->

<!-- /PHYSICAL_TEST_ANALYSIS:mirror -->

<a id="physical-test-real"></a>

### Physical scene

<a href="docs/media/physical-test/20261015/real.gif"><img src="docs/media/physical-test/20261015/real.gif" width="360" loading="lazy" alt="Physical scene"></a>



<!-- PHYSICAL_TEST_ANALYSIS:real -->

<!-- /PHYSICAL_TEST_ANALYSIS:real -->

<a id="physical-test-rviz-static"></a>

### RViz static video

<a href="docs/media/physical-test/20261015/rviz_Static.gif"><img src="docs/media/physical-test/20261015/rviz_Static.gif" width="960" loading="lazy" alt="RViz static video"></a>
<!-- PHYSICAL_TEST_ANALYSIS:rviz-static -->

<!-- /PHYSICAL_TEST_ANALYSIS:rviz-static -->

<a id="physical-test-rviz-dynamic"></a>

### 3. RViz dynamic video

<a href="docs/media/physical-test/20261015/rviz_dyn.gif"><img src="docs/media/physical-test/20261015/rviz_dyn.gif" width="960" loading="lazy" alt="RViz dynamic video"></a>



**Analysis:** The video suggests distortion during fast motion, and the moving person leaves unwanted points in the map. These are the author's observations motivating separate controlled tests.
<!-- PHYSICAL_TEST_ANALYSIS:rviz-dynamic -->

<!-- /PHYSICAL_TEST_ANALYSIS:rviz-dynamic -->

<a id="physical-test-additional"></a>

### Additional physical tests

| Test 4 · `4.mp4` | Test 5 · `5.mp4` |
| --- | --- |
| <a href="docs/media/physical-test/20261016-additional/4.gif"><img src="docs/media/physical-test/20261016-additional/4.gif" width="420" loading="lazy" alt="Physical test 4"></a> | <a href="docs/media/physical-test/20261016-additional/5.gif"><img src="docs/media/physical-test/20261016-additional/5.gif" width="420" loading="lazy" alt="Physical test 5"></a> |
| **Test 7 · `7.mp4`** | **Test 6 · `6.mp4`** |
| <a href="docs/media/physical-test/20261016-additional/7.gif"><img src="docs/media/physical-test/20261016-additional/7.gif" width="420" loading="lazy" alt="Physical test 7"></a> | <a href="docs/media/physical-test/20261016-additional/6.gif"><img src="docs/media/physical-test/20261016-additional/6.gif" width="420" loading="lazy" alt="Physical test 6"></a> |

**Analysis:**
<!-- PHYSICAL_TEST_ANALYSIS:additional-four -->

<!-- /PHYSICAL_TEST_ANALYSIS:additional-four -->

<a id="physical-test-annotated-maps"></a>

### Annotated map comparison

<a href="docs/media/physical-test/20261016-additional/annotated-maps.png"><img src="docs/media/physical-test/20261016-additional/annotated-maps.png" width="653" alt="User-annotated comparison of four physical-test maps"></a>

**Analysis:**
<!-- PHYSICAL_TEST_ANALYSIS:annotated-maps -->

<!-- /PHYSICAL_TEST_ANALYSIS:annotated-maps -->

## Direction analysis

### 1. What does the research title ask?

**Direction: robust localization and SLAM in dynamic environments.**

Mapping and localization support each other. Our evaluation changes the map, then uses the same localization method to test whether error decreases.

My understanding of localization:

- Given a motion prior, use current observations to score consistency with the map and infer pose and confidence.
- AMCL represents possible poses with particles and weights them using an observation model; GICP estimates pose through geometric consistency.
- The map supplies the references against which sensor observations can be matched.

Our goal is therefore **to improve mapping and test the resulting improvement in localization**.

- **Moving objects leave traces that contaminate the map. This is our main focus.** Detect and remove motion while preserving static structures.
  - 2D LiDAR: SRRG.
  - 3D LiDAR: DUFOMap and BeautyMap.

    ![DUFOMap detection and cleaning example](docs/media/direction/20261016-user/image-20261015222612651.png)

  - Depth/RGB camera: DynaSLAM.

    ![DynaSLAM example](docs/media/direction/20261016-user/image-20261015222431746.png)

- **Sensor motion within a scan causes motion distortion**, which can affect registration, trajectory drift and map alignment. High speed or rotation makes timing errors more visible; drift can also have other causes.

  ![Motion-distortion example](docs/media/direction/20261016-user/image-20261015230734740.png)

  FAST-LIO estimates motion using LiDAR and IMU and compensates points before registration. This is a candidate for fast-motion tests, rather than a guarantee against all failures. [Official implementation](https://github.com/hku-mars/FAST_LIO/tree/ROS2).

  ![FAST-LIO example supplied with the Chinese analysis](docs/media/direction/20261016-user/image-20261015231926970.png)

  My interpretation: combining vision, LiDAR and odometry can provide complementary evidence, but synchronization, calibration and fusion themselves need validation.

- **Special materials and geometrically weak environments can damage mapping and localization.**
  - Mirrors:

    ![Mirror-related map issue](docs/media/direction/20261016-user/image-20261015230454037.png)

  - Corridors:

    ![Corridor example](docs/media/direction/20261016-user/image-20261015234829998.png)

    Repeated or parallel structures can leave the along-corridor position weakly constrained. A possible intervention is an identifiable landmark, such as a mapped visual marker. A QR marker requires a camera and detector; a LiDAR-only test must use visible geometry.

- **Maps need maintenance after construction** to remain useful for localization. Relocated furniture motivates updates, for example Khronos.

  ![Persistent-change example](docs/media/direction/20261016-user/image-20261016000012003.png)

  Temporal evidence helps distinguish persistent structures, occasional relocation and rapid motion. Recognition and segmentation can support these decisions and object-level navigation or manipulation; a semantic class alone does not establish whether something is moving now.

The core question is:

**In a dynamic environment, how can we build a geometrically trustworthy map that retains useful static constraints, and test whether it improves localization accuracy and continuity?**

## Open question

**Broad direction: which strategies enable reliable mapping in changing environments, and thereby reliable localization?**

**Question 1:** Given multiple scans and mapping poses, how can dynamic traces be removed while preserving static structures, and under which contamination and geometric conditions does this improve independent localization?

**Question 2:** With other conditions controlled, how can motion distortion caused by fast translation or rotation of the sensor be reduced?

**Question 3:** How can special obstacles be identified and weak environments such as corridors handled, limiting their effect on mapping and subsequent localization?

<a id="mapping-hypothesis-tests"></a>

## Hypothesis

<!-- SIMPLE_HYPOTHESES_V2 -->
<!-- OWN_HYPOTHESES_20261016 -->

| Question | Hypothesis | Controls | Metrics |
| --- | --- | --- | --- |
| H1 / Q1 | Own supported alignment and temporal cleaning remove traces with at most one percentage point of static loss and improve held-out localization. | M₀: wheel-pose accumulation / M₁: own alignment + cleaning | A: DA, SA; B: XY RMSE |
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

**Spoken explanation:** freeze the A maps, apply the same localizer to independent B, and check whether the map change reduces pose error. This is an evaluation requirement; the algorithm does not directly minimize AMCL error.

**H1: align using previous temporal support, then remove traces using free-space counterevidence.** Raw accumulates wheel-derived poses. The intervention changes both alignment and cleaning; alignment-only / filter-only ablations distinguish their contributions.

**2. Predict the current pose using the wheel increment.**

```math
T_{k,0}=T_{k-1}(T_{k-1}^o)^{-1}T_k^o.
```

$`(T_{k-1}^o)^{-1}T_k^o`$ is the wheel-derived motion between frames. Compose it with the previously corrected pose $`T_{k-1}`$ to obtain the current initial estimate $`T_{k,0}`$. Initialize the first frame using the known start and wheel pose; the algorithm does not read pose truth.

**Spoken explanation:** wheel odometry supplies the short motion increment, and prediction continues from the previous corrected pose.

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

**Spoken explanation:** use repeatedly supported prior structure to correct the current pose, while correspondence selection and weighting reduce unreliable matches. This is local sequential correction, without global pose-graph optimization.

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

**Spoken explanation:** check whether nearby structure continues to be observed while allowing small shifts between neighboring cells.

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

**Spoken explanation: deletion requires sufficient counterevidence; rare observations alone do not justify deletion.** The retained map and temporal support then inform the next alignment step, forming sequential feedback.

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

**Spoken explanation:** first check trace removal and static support, then check independent localization on the frozen maps. Old B is used for development ablation; parameters are fixed before final fresh B. The joint gain cannot be attributed entirely to dynamic removal.

**H2: bring point samples to a common reference time, then test map geometry and localization separately.**

**12. Core equation III: motion-distortion compensation.** $`\mathbf z_i=(x_i,y_i,1)^{\mathsf T}`$ is a local homogeneous point acquired at $`t_i`$. Wheel-odometry interpolation plus sensor extrinsics provides $`\hat T(t)\in\mathrm{SE}(2)`$ from that sensor frame to the fixed map frame. $`t_e`$ is scan end:

```math
\boxed{\boldsymbol{\bar{\mathbf z}_i=\hat T(t_e)^{-1}\hat T(t_i)\mathbf z_i}}
```

Read right to left: $`\hat T(t_i)`$ moves the point to the fixed frame, then $`\hat T(t_e)^{-1}`$ moves it into the scan-end sensor frame. $`M_0`$ treats mixed-time points as acquired at $`t_e`$; $`M_1`$ compensates first. Integrate both with $`\hat T(t_e)`$ and hold all other steps fixed. H2 does not additionally enable H1 filtering.

**Spoken explanation:** use estimated robot motion to express points measured at different times in one reference frame. This compensates robot motion, not object motion, and depends on odometry quality.

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

**Presentation wording:** we study how dynamic mapping affects later localization. Compared with SRRG's projective fusion and complete graph maintenance, we explicitly accumulate neighborhood support and free-space evidence across time: repeatedly supported structure assists alignment, and sufficient free-space counterevidence removes historical traces. Current validation asks whether this evidence design preserves useful localization structure; comparative performance against SRRG has not been established.

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

[Implementation, experiments and recordings](#hypothesis-test-index)

## Related works

<!-- HOME_RELATED_TABLE -->
Grouped by algorithm family. Click a GIF for the full video. The application-direction column is intentionally blank. Different data protocols prevent cross-row ranking.

| Method / algorithm family | Native GIF / original-source illustration | Measured metrics and scope | Application direction |
| --- | --- | --- | --- |
| <a id="related-fast_lio"></a>[FAST-LIO / FAST-LIO2](docs/papers/fast_lio.md) | <img src="docs/assets/related/20261016-pointcloud/fastlio2-fig12.png" width="280" alt="FAST-LIO2 original Fig. 12: point-cloud map"> | Original-paper experiments: **not reproduced**; original figure and method summary; custom-scene tests in Practice |  |
| <a id="related-srrg_mapper2d"></a>[SRRG / srrg_mapper2d](docs/papers/srrg_mapper2d.md) | <img src="docs/assets/related/20261016-pointcloud/srrg-fig7.png" width="280" alt="SRRG original Fig. 7: point-cloud map"> | Original-paper experiments: **not reproduced**; original figure and method summary; custom-scene tests in Practice |  |
| <a id="related-dufomap"></a>[DUFOMap](docs/papers/dufomap.md)<br>3D map cleaning | <a href="results/reference/desktop-live-dufomap/execution.mp4"><img src="docs/media/related-pointcloud/20261016/dufomap.gif" width="280" loading="lazy" alt="dufomap · Point-cloud capture excerpt"></a><br>[Point-cloud capture excerpt](results/reference/desktop-live-dufomap/execution.mp4) | SA 97.98% / DA 98.7%<br>KITTI-00 · 141 scans; cleaning demonstrated<br>[Record](results/reference/desktop-live-dufomap/record.json) |  |
| <a id="related-beautymap"></a>[BeautyMap](docs/papers/beautymap.md)<br>Offline 3D map cleaning | <a href="results/reference/desktop-live-beautymap/execution.mp4"><img src="docs/media/related-pointcloud/20261016/beautymap.gif" width="280" loading="lazy" alt="beautymap · Point-cloud capture excerpt"></a><br>[Point-cloud capture excerpt](results/reference/desktop-live-beautymap/execution.mp4) | SA 96.95% / DA 98.34%<br>KITTI-00 · 141 scans; cleaning demonstrated<br>[Record](results/reference/desktop-live-beautymap/record.json) |  |
| <a id="related-amcl"></a>[AMCL / Nav2](https://github.com/ros-navigation/navigation2/tree/main/nav2_amcl)<br>2D particle localization | <a href="https://github.com/ros-navigation/docs.nav2.org/blob/8f6571b599d6b1e899f11ac58c5c1982d3b0a8b5/docs/getting_started/quickstart/assets/rviz/navstack_ready.png"><img src="docs/assets/related/20261016-localizers/amcl-nav2-original.png" width="280" loading="lazy" alt="AMCL: original Nav2 repository localization screenshot"></a><br>Original Nav2 documentation-repository image | Common 2D frozen-map localizer; XY / yaw RMSE. Source illustration, not our recording; [method](#related-amcl-details) |  |
| <a id="related-gicp"></a>[GICP](https://github.com/avsegal/gicp)<br>3D geometric registration | <a href="https://www.robots.ox.ac.uk/~avsegal/generalized_icp.html"><img src="docs/assets/related/20261016-localizers/gicp-author-original.jpg" width="280" loading="lazy" alt="GICP: original point-cloud illustration from the algorithm author"></a><br>Original GICP author-page image | Common 3D frozen-map localizer; XYZ / rotation RMSE. Author illustration, not our recording; [method](#related-gicp-details) |  |
| <a id="related-ir-mcl"></a>[IR-MCL](docs/papers/ir-mcl.md)<br>2D neural-field localization | <a href="results/reference/desktop-live-ir-mcl/execution.mp4"><img src="docs/media/related-pointcloud/20261016/ir-mcl.gif" width="280" loading="lazy" alt="ir-mcl · Point-cloud capture excerpt"></a><br>[Point-cloud capture excerpt](results/reference/desktop-live-ir-mcl/execution.mp4) | RMSE 5.31 cm / 1.07°<br>Bonn IPBLab Seq 1<br>[Record](results/reference/desktop-live-ir-mcl/record.json) |  |
| <a id="related-adam-mcl"></a>[AdaM-MCL](docs/papers/adam-mcl.md)<br>Learned proposals + particle localization | <a href="results/reference/desktop-adam-mcl/result.mp4"><img src="results/reference/desktop-adam-mcl/result.gif" width="280" loading="lazy" alt="AdaM-MCL · 2D particle-result replay"></a><br>2D particle-result replay | RMSE 32.23 cells; authored 128-cell map, 2432 training steps; historical sustained convergence 0/10, no comparison to paper metre-scale accuracy<br>[Record](results/reference/desktop-adam-mcl/record.json) |  |
<!-- /HOME_RELATED_TABLE -->

See [Metrics](#metrics) for SA/DA and pose-RMSE definitions. SRRG scores 2D observed support; DUFOMap/BeautyMap score 3D points. IR-MCL/AdaM-MCL do not clean maps.

<details>
<summary>Inputs, processing and reproduction boundaries</summary>

<!-- HOME_RELATED_DETAILS -->
### DUFOMap — dynamic-point removal during map integration

**Input:** successive 3D LiDAR scans and provided sensor poses. **Process:** observed free space supplies evidence that earlier occupied points are transient; an octree accumulates this evidence with margins for pose uncertainty. **Output:** a map with dynamic remnants removed. It does not estimate the robot pose. [Paper and reproduced scope](docs/papers/dufomap.md).

In the live video, gray points are retained, red points are removed, and cyan points are the current scan. Watch how decisions change as later scans supply evidence. KITTI-00, 141 scans; SA 97.98% / DA 98.70%. SA measures retained static points and DA measures removed dynamic points; neither is localization error.

[Live MP4](results/reference/desktop-live-dufomap/execution.mp4) · [record](results/reference/desktop-live-dufomap/record.json)

### BeautyMap — clean an existing point-cloud map

**Input:** the full accumulated 3D map, scans and provided poses. **Process:** the native occupancy representation detects inconsistent occupied structure, followed by the authors' static-structure recovery stage. **Output:** a cleaned reference map. This offline map cleaner is shown while it computes; the input map already exists at the start. [Paper and reproduced scope](docs/papers/beautymap.md).

Gray/red show retained/removed points. Watch the cumulative removal decisions, rather than interpreting the complete initial map as online SLAM. KITTI-00, 141 scans; SA 96.95% / DA 98.34%. Cleaner maps may help downstream localization, but that requires a separate test.

[Live MP4](results/reference/desktop-live-beautymap/execution.mp4) · [record](results/reference/desktop-live-beautymap/record.json)

### IR-MCL — localize with a neural observation model

**Input:** a pretrained neural occupancy field, measured 2D scans and motion input. **Process:** each particle represents a possible robot pose; the field renders a predicted scan at that pose, scan agreement changes particle weights, and resampling concentrates the belief. **Output:** an estimated pose and particle distribution. [Paper, original code and protocol](docs/papers/ir-mcl.md).

In RViz, the map supplies context, yellow particles show pose hypotheses, blue is the displayed estimate and green is the reference trajectory. Watch particle concentration and agreement with the reference. The displayed weighted particle mean is an observer; scoring uses the native saved estimate. Bonn IPBLab Seq 1: 1543 processed / 1354 scored poses, fresh RMSE 5.31 cm / 1.07°. This author-data run is separate from deployment into Gazebo.

[Live MP4](results/reference/desktop-live-ir-mcl/execution.mp4) · [record](results/reference/desktop-live-ir-mcl/record.json)

### AdaM-MCL — combine learned proposals and particle tracking

**Input:** a map, laser observation, motion input and trained proposal model. **Process:** the learned model proposes candidate poses; the adaptive mixture combines proposals with conventional particle tracking. **Output:** pose belief, including hypotheses after a kidnapping event. [Paper and limits](docs/papers/adam-mcl.md).

Our run uses an authored 128-cell map and a 2432-step checkpoint: 123 filter updates, RMSE 32.23 cells. The released paper dataset/checkpoint was unavailable. This verifies a limited original-code workflow; it neither reproduces the paper's metre-scale scores nor demonstrates successful recovery. [Score correction](results/reference/adam-mcl/ERRATUM.md).

[Live MP4](results/reference/desktop-adam-mcl/execution.mp4) · [record](results/reference/desktop-adam-mcl/record.json)

[Result MP4](results/reference/desktop-adam-mcl/result.mp4)

<!-- SRRG_RELATED -->
### SRRG · Native 2D dynamic-environment mapping

**Original-paper experiments: not reproduced.** The original figure introduces the method. Custom Gazebo runs of the author code appear separately in [Practice](#practice-srrg); these do not reproduce the LCAS/MIT Stata long-term multi-session benchmark.

![SRRG · original point-cloud Fig. 7](docs/assets/related/20261016-pointcloud/srrg-fig7.png)

Source: Lázaro et al., *Efficient Long-term Mapping in Dynamic Environments*, IROS 2018, Fig. 7, page 6. [Paper](https://iris.uniroma1.it/handle/11573/1340118) · [Author code](https://gitlab.com/srrg-software/srrg_mapper2d). Registration, local maintenance and graph optimization connect H1 to geometric conditions in Q3.
<!-- /SRRG_RELATED -->

<!-- FASTLIO_RELATED -->
### FAST-LIO / FAST-LIO2 · LiDAR–IMU estimation and point compensation

**Original-paper experiments: not reproduced.** This is the original FAST-LIO2 paper figure. Our custom-scene ablation uses the official ROS2 branch and FAST-LIO2 direct registration, distinct from reproducing the first FAST-LIO paper. [FAST-LIO Practice](#practice-fastlio).

![FAST-LIO2 · original point-cloud Fig. 12](docs/assets/related/20261016-pointcloud/fastlio2-fig12.png)

Source: Xu et al., *FAST-LIO2: Fast Direct LiDAR-inertial Odometry*, Fig. 12, page 16. [FAST-LIO](https://arxiv.org/abs/2010.08196) · [FAST-LIO2](https://arxiv.org/abs/2107.06829) · [Official ROS2 code](https://github.com/hku-mars/FAST_LIO/tree/ROS2). IMU propagation and backward point compensation address H2. The incremental spatial index is not a dynamic-object removal or mirror detector.
<!-- /FASTLIO_RELATED -->
<!-- LOCALIZERS_RELATED -->
<a id="related-amcl-details"></a>

### AMCL · Localization in a prebuilt 2D map

**Input → process → output:** a fixed occupancy grid, laser scans and odometry → particle motion prediction, scan-to-map weighting, resampling and adaptive particle counts → planar position, yaw and pose uncertainty. AMCL localizes; it does not build or clean the map.

<img src="docs/assets/related/20261016-localizers/amcl-nav2-original.png" width="680" alt="Original Nav2 repository screenshot: robot and AMCL particles in the map">

**Image source:** [original Nav2 documentation-repository image](https://github.com/ros-navigation/docs.nav2.org/blob/8f6571b599d6b1e899f11ac58c5c1982d3b0a8b5/docs/getting_started/quickstart/assets/rviz/navstack_ready.png), showing the robot, particle distribution and navigation-stack layers; not our recording. [Official AMCL code](https://github.com/ros-navigation/navigation2/tree/main/nav2_amcl).

**Role here:** 2D Practice and our H1/H2 use AMCL on frozen A maps with independently acquired B. Paired controls share scans, odometry, parameters and initialization; evaluate XY localization RMSE and yaw when relevant. Map remnants and lost static constraints affect observation weights. DA/SA do not evaluate AMCL. Custom-scene tests are in [Practice](#practice-index) and [Hypothesis test](#hypothesis-test-index); original-paper benchmarks are not reproduced.

<a id="related-gicp-details"></a>

### GICP · Register a 3D scan to a fixed point-cloud map

**Input → process → output:** a fixed 3D point-cloud map, a current scan and an initial pose prediction → establish correspondences, weight residuals using local surface covariances on both sides, and iteratively solve a rigid transform → 3D position and orientation. GICP is originally a registration algorithm; a localization system uses it for scan-to-map matching. It does not remove dynamic objects itself.

<img src="docs/assets/related/20261016-localizers/gicp-author-original.jpg" width="400" alt="Original point-cloud illustration from the GICP author page">

**Image source:** [original GICP author-page image](https://www.robots.ox.ac.uk/~avsegal/generalized_icp.html). The author's reference repository contains no image; this uses the author's own point-cloud illustration, not our recording. [Reference code](https://github.com/avsegal/gicp) · [PCL implementation](https://pointclouds.org/documentation/classpcl_1_1_generalized_iterative_closest_point.html) · [ROS2 localization framework used here](https://github.com/rsasaki0109/lidar_localization_ros2).

**Role here:** 3D Practice freezes Raw/DUFOMap/BeautyMap A maps and applies the same GICP configuration to fresh B clouds and wheel odometry, evaluating XYZ and full-rotation RMSE. The preceding methods clean the maps; GICP evaluates downstream localization. Local registration depends on initialization and geometric constraints; small angular errors can coexist with metre-scale longitudinal drift in corridors. See [3D Practice](#scene-static-3d). Our installed ROS2/PCL implementation is distinct from the author's reference code; original-paper benchmarks are not reproduced.
<!-- /LOCALIZERS_RELATED -->

<!-- /HOME_RELATED_DETAILS -->

</details>

## Metrics

| Metric | Definition |
| --- | --- |
| DA ↑ / SA ↑ | Cleaning A only: dynamic removal / static retention; omit DA without dynamics. Units are observed support in 2D and points in 3D. |
| Map RMSE ↓ | Deskew A: map-point distance RMSE to static reference geometry, cm. |
| XY / XYZ RMSE ↓ | Localization B on frozen maps: 2D / 3D position error, cm. |
| Angular RMSE ↓ | Yaw or 3D rotation error when pose orientation is evaluated, degrees; A odometry is labelled separately. |

### Evidence

| DUFOMap · KITTI-00 · Metric | Paper % | Reproduced % |
| --- | ---: | ---: |
| SA | 97.96 | 97.9635 |
| DA | 98.72 | 98.7196 |

| BeautyMap · KITTI-02 · Metric | Paper % | Reproduced % |
| --- | ---: | ---: |
| SA | 83.40 | 83.3978 |
| DA | 82.41 | 82.4092 |

| IR-MCL · Metric | Paper, Seq 1 | Reproduced |
| --- | ---: | ---: |
| Location RMSE (cm) | 5.13 | 5.32 |
| Yaw RMSE (deg) | 1.05 | 1.07 |

## Practice

This section practices methods in Related works. A = mapping; B = a separate localization session on frozen maps. Click A/B in the contents to reach its recordings and metrics.

<a id="practice-index"></a>

### Experiment contents

| No. | Method / subexperiment | Go directly |
| --- | --- | --- |
| P0 | Setup and devices | [Open experiment](#practice-setup) |
| P0.1 | Raw baseline definitions | [Open experiment](#raw-baseline-definitions) |
| P1.1 | SRRG · Static | [A](#h1-static-a) / [B](#h1-static-b) |
| P1.2 | SRRG · Dynamic | [A](#h1-dynamic-a) / [B](#h1-dynamic-b) |
| P1.3 | SRRG · Original corridor | [A](#h3-original-a) / [B](#h3-original-b) |
| P1.4 | SRRG · Persistent change | [A](#supp-srrg) / [B](#supp-srrg-b) |
| P2.1 | FAST-LIO · Mapping and motion phases | [A](#h2-a) / [Stationary](#h2-stationary) / [Slow turn](#h2-slow) / [Fast turn](#h2-fast) / [Translation](#h2-translation) |
| P2.2 | FAST-LIO · Frozen-map localization | [B](#h2-b) |
| P3.0 | DUFOMap / BeautyMap · KITTI-00 | [Map-cleaning practice](#practice-kitti) |
| P3.1 | DUFOMap / BeautyMap · 3D · Static | [A](#scene-static-3d) / [B](#scene-static-3d-b) |
| P3.2 | DUFOMap / BeautyMap · 3D · Dynamic | [A](#scene-dynamic-3d) / [B](#scene-dynamic-3d-b) |
| P3.3 | DUFOMap / BeautyMap · 3D · Corridor | [A](#scene-corridor-3d) / [B](#scene-corridor-3d-b) |
| P3.4 | DUFOMap / BeautyMap · 3D · Changed world | [A](#scene-change-3d) / [B](#scene-change-3d-b) |
| P4 | IR-MCL · Bonn | [Open experiment](#practice-irmcl) |
| P5 | AdaM-MCL | [Open experiment](#practice-adam) |
| P6.1 | NDT / GICP | [Open experiment](#supp-registrations) |
| P6.2 | slam_toolbox / AMCL | [Open experiment](#supp-acquisition) |
| P6.3 | Saved-cloud replay | [Open experiment](#map-review-3d) |
| P6.4 | Failure diagnostics | [Open experiment](#srrg-diagnostics) |

<a id="practice-setup"></a>

### Setup

| Item | Setting |
| --- | --- |
| Platform | Windows / WSL2 · ROS 2 Jazzy · Gazebo Harmonic · RViz2 |
| Robot | Sim2Real omni chassis; rendered URDF below. |
| 2D devices | 720-beam 2D LiDAR + wheel odometry. |
| 3D devices | 16×720 3D LiDAR; FAST-LIO arm adds a 200 Hz IMU. |


<a id="robot-urdf"></a>

<img src="docs/media/robot/20261016/urdf.png" width="560" alt="Actual robot URDF rendered in RViz">

<a id="practice-metrics"></a>

### Metric definitions

[Short definitions in Metrics](#metrics)

A measures cleaning or geometry; B measures localization after 5 s warmup. P3 3D uses scan timestamps common to all three outputs; other groups retain common 10 Hz times with pose age ≤0.15 s. Counts and missing outputs remain in records. One trial per arm; complete navigation outcomes were not measured.

<a id="raw-baseline-definitions"></a>

### Raw baseline definitions

**Meaning of Raw.** Raw labels this repository's accumulated baseline without dynamic-map cleaning. It is not a standalone SLAM/localization algorithm or completely unprocessed sensor data.

| Context | How Raw is built | Downstream localization |
| --- | --- | --- |
| Own H1 | Transform valid 2D returns using the known start, wheel odometry and sensor extrinsic; retain each 5 cm cell hit at least once, without retracting earlier occupied cells or applying H1 temporal filtering. | Frozen-map AMCL |
| Practice: SRRG 2D comparison | Accumulate returns using SRRG's online sensor-pose estimate at each frame; do not reproject accumulated historical points with the final optimized graph. SRRG output additionally includes map maintenance and graph optimization. | Frozen-map AMCL |
| Practice: Raw / DUFOMap / BeautyMap 3D comparison | Transform and concatenate 3D scans using provided sensor poses from controlled mapping A, without DUFOMap/BeautyMap cleaning. A uses supplied simulation poses. | Frozen-map GICP; no truth input in B |

These Raw maps and pose sources differ between experiments; compare within the matched experiment. The SRRG comparison includes pose optimization and map maintenance, not just a deletion-rule ablation. Current H1 also adds own pose alignment, which Raw does not use; filter-only / alignment-only ablations distinguish their contributions. H2 calls its baseline Off: only point-time compensation is disabled. FAST-LIO Practice Off still retains LiDAR–IMU estimation.


<a id="practice-srrg"></a>

### P1 · SRRG · Static and dynamic

| Scene | Change | Keep fixed |
| --- | --- | --- |
| Static control / moving obstacles | Raw / SRRG | Shared A scans, shared B scans, AMCL settings and initial offset |


<a id="h1-static-a"></a>

#### Static · A

| Method | SA ↑ |
| --- | --- |
| Raw | 100.00% |
| SRRG | 100.00% |


[Record](results/reference/direction-20261016-v2/2d-A-static/record.json)

| A · Raw / SRRG |
| --- |
| <a href="results/reference/direction-20261016-v2/2d-A-static/execution.mp4"><img src="results/reference/direction-20261016-v2/2d-A-static/execution.gif" width="840" loading="lazy" alt="A · Raw / SRRG"></a> |


**Analysis:**
<!-- PRACTICE_ANALYSIS:h1-static-a -->

<!-- /PRACTICE_ANALYSIS:h1-static-a -->

[↑ Contents](#practice-index)

<a id="h1-static-b"></a>

#### Static · B

| Map | XY RMSE / cm | yaw / ° | Localization B (click for MP4) |
| --- | --- | --- | --- |
| Raw | 5.03 | 2.88 | <a href="results/reference/direction-20261016-v2/2d-static/executions/raw.mp4"><img src="results/reference/direction-20261016-v2/2d-static/executions/raw.gif" width="320" loading="lazy" alt="Raw · localization B"></a> |
| SRRG | 5.84 | 2.91 | <a href="results/reference/direction-20261016-v2/2d-static/executions/srrg.mp4"><img src="results/reference/direction-20261016-v2/2d-static/executions/srrg.gif" width="320" loading="lazy" alt="SRRG · localization B"></a> |


[Scores](results/reference/direction-20261016-v2/2d-static/time-grid-score.json)

**Analysis:**
<!-- PRACTICE_ANALYSIS:h1-static-b -->

<!-- /PRACTICE_ANALYSIS:h1-static-b -->

[↑ Contents](#practice-index)

<a id="h1-dynamic-a"></a>

#### Dynamic · A

| Method | DA ↑ | SA ↑ |
| --- | --- | --- |
| Raw | 0.00% | 100.00% |
| SRRG | 36.94% | 99.84% |


[Record](results/reference/direction-20261016-v2/2d-A-dynamic/record.json)

| A · Raw / SRRG |
| --- |
| <a href="results/reference/direction-20261016-v2/2d-A-dynamic/execution.mp4"><img src="results/reference/direction-20261016-v2/2d-A-dynamic/execution.gif" width="840" loading="lazy" alt="A · Raw / SRRG"></a> |


**Analysis:**
<!-- PRACTICE_ANALYSIS:h1-dynamic-a -->

<!-- /PRACTICE_ANALYSIS:h1-dynamic-a -->

[↑ Contents](#practice-index)

<a id="h1-dynamic-b"></a>

#### Dynamic · B

| Map | XY RMSE / cm | yaw / ° | Localization B (click for MP4) |
| --- | --- | --- | --- |
| Raw | 5.53 | 0.76 | <a href="results/reference/direction-20261016-v2/2d-dynamic/executions/raw.mp4"><img src="results/reference/direction-20261016-v2/2d-dynamic/executions/raw.gif" width="320" loading="lazy" alt="Raw · localization B"></a> |
| SRRG | 5.13 | 0.70 | <a href="results/reference/direction-20261016-v2/2d-dynamic/executions/srrg.mp4"><img src="results/reference/direction-20261016-v2/2d-dynamic/executions/srrg.gif" width="320" loading="lazy" alt="SRRG · localization B"></a> |


[Scores](results/reference/direction-20261016-v2/2d-dynamic/time-grid-score.json)

**Analysis:**
<!-- PRACTICE_ANALYSIS:h1-dynamic-b -->

<!-- /PRACTICE_ANALYSIS:h1-dynamic-b -->

[↑ Contents](#practice-index)

<a id="practice-srrg-corridor"></a>

### P1.3 · SRRG · Corridor

<a id="h3-original-a"></a>

#### Original corridor · A

| Method | SA ↑ |
| --- | --- |
| Raw | 82.63% |
| SRRG | 82.05% |


[Record](results/reference/direction-20261016-v2/2d-A-corridor/record.json)

| A · Raw / SRRG |
| --- |
| <a href="results/reference/direction-20261016-v2/2d-A-corridor/execution.mp4"><img src="results/reference/direction-20261016-v2/2d-A-corridor/execution.gif" width="840" loading="lazy" alt="A · Raw / SRRG"></a> |


**Analysis:**
<!-- PRACTICE_ANALYSIS:h3-original-a -->

<!-- /PRACTICE_ANALYSIS:h3-original-a -->

[↑ Contents](#practice-index)

<a id="h3-original-b"></a>

#### Original corridor · B

| Map | XY RMSE / cm | yaw / ° | Localization B (click for MP4) |
| --- | --- | --- | --- |
| Raw | 113.30 | 1.38 | <a href="results/reference/direction-20261016-v2/2d-corridor/executions/degraded_raw.mp4"><img src="results/reference/direction-20261016-v2/2d-corridor/executions/degraded_raw.gif" width="320" loading="lazy" alt="Raw · localization B"></a> |
| SRRG | 102.72 | 1.08 | <a href="results/reference/direction-20261016-v2/2d-corridor/executions/degraded_srrg.mp4"><img src="results/reference/direction-20261016-v2/2d-corridor/executions/degraded_srrg.gif" width="320" loading="lazy" alt="SRRG · localization B"></a> |


[Scores](results/reference/direction-20261016-v2/2d-corridor/time-grid-score.json)

**Analysis:**
<!-- PRACTICE_ANALYSIS:h3-original-b -->

<!-- /PRACTICE_ANALYSIS:h3-original-b -->

[↑ Contents](#practice-index)

<a id="practice-fastlio"></a>

### P2 · FAST-LIO · Motion distortion

| Scene | Change | Keep fixed |
| --- | --- | --- |
| Existing static scene; stationary → slow/fast turns → translation | FAST-LIO point compensation off / on | Same scans, point timing, IMU and state prediction; identical GICP for B |


Three measured 120° sectors form a 0.2 s scan; this is controlled grouped sampling.

<a id="h2-a"></a>

#### A · Mapping and motion phases

| Point compensation | Map RMSE / cm ↓ |
| --- | --- |
| Off | 13.49 |
| On | 4.61 |


[Scores](results/reference/direction-20261016-v2/fastlio-maps/score.json)

| A · FAST-LIO on / off |
| --- |
| <a href="results/reference/direction-20261016-v2/fastlio-motion/execution.mp4"><img src="results/reference/direction-20261016-v2/fastlio-motion/execution.gif" width="840" loading="lazy" alt="A · FAST-LIO on / off"></a> |


<a id="h2-stationary"></a>

##### Stationary

| Point compensation | Phase time | A odometry XYZ RMSE / cm | Rotation / ° |
| --- | --- | --- | --- |
| Off | 0–7 s | 0.12 | 0.02 |
| On | 0–7 s | 0.15 | 0.03 |


<a id="h2-slow"></a>

##### Slow turn

| Point compensation | Phase time | A odometry XYZ RMSE / cm | Rotation / ° |
| --- | --- | --- | --- |
| Off | 7–15 s | 1.30 | 0.95 |
| On | 7–15 s | 0.42 | 0.14 |


<a id="h2-fast"></a>

##### Fast turn

| Point compensation | Phase time | A odometry XYZ RMSE / cm | Rotation / ° |
| --- | --- | --- | --- |
| Off | 15–31 s | 3.18 | 4.35 |
| On | 15–31 s | 0.79 | 0.26 |


<a id="h2-translation"></a>

##### Translation

| Point compensation | Phase time | A odometry XYZ RMSE / cm | Rotation / ° |
| --- | --- | --- | --- |
| Off | 31–39 s | 5.33 | 3.68 |
| On | 31–39 s | 1.45 | 0.25 |


**Analysis:**
<!-- PRACTICE_ANALYSIS:h2-a -->

<!-- /PRACTICE_ANALYSIS:h2-a -->

[↑ Contents](#practice-index)

<a id="h2-b"></a>

#### B · GICP on frozen maps

| A compensation | XYZ RMSE / cm | Rotation / ° | Localization B (click for MP4) |
| --- | --- | --- | --- |
| Off | 14.03 | 3.62 | <a href="results/reference/direction-20261016-v2/fastlio-B/executions/no_deskew.mp4"><img src="results/reference/direction-20261016-v2/fastlio-B/executions/no_deskew.gif" width="320" loading="lazy" alt="Off map · localization B"></a> |
| On | 2.04 | 0.87 | <a href="results/reference/direction-20261016-v2/fastlio-B/executions/deskew.mp4"><img src="results/reference/direction-20261016-v2/fastlio-B/executions/deskew.gif" width="320" loading="lazy" alt="On map · localization B"></a> |


[Scores](results/reference/direction-20261016-v2/fastlio-B/score-3d.json)

**Analysis:**
<!-- PRACTICE_ANALYSIS:h2-b -->

<!-- /PRACTICE_ANALYSIS:h2-b -->

[↑ Contents](#practice-index)

<a id="practice-kitti"></a>

### P3.0 · DUFOMap / BeautyMap · KITTI-00

KITTI-00, 141 scans; this experiment evaluates map cleaning only.

| Method | DA ↑ | SA ↑ | Point-cloud excerpt (click for full recording) | Record |
| --- | --- | --- | --- | --- |
| DUFOMap | 98.70% | 97.98% | <a href="results/reference/desktop-live-dufomap/execution.mp4"><img src="docs/media/related-pointcloud/20261016/dufomap.gif" width="340" alt="DUFOMap"></a> | [Record](results/reference/desktop-live-dufomap/record.json) |
| BeautyMap | 98.34% | 96.95% | <a href="results/reference/desktop-live-beautymap/execution.mp4"><img src="docs/media/related-pointcloud/20261016/beautymap.gif" width="340" alt="BeautyMap"></a> | [Record](results/reference/desktop-live-beautymap/record.json) |

<a id="baseline-3d"></a>

### 3D maps and held-out localization

Reacquire 3D A, run Raw/DUFOMap/BeautyMap, freeze the maps, then acquire separate B. All three localizers share B clouds and fixed GICP parameters. A/B videos capture live Gazebo + RViz windows; B does not update maps.

A shows live 16-channel XYZ clouds and wall height in an oblique view. A uses supplied simulation poses to isolate cleaning, rather than evaluate full 3D SLAM. B: grey = frozen map, green = current scan, pink = estimated pose, cyan = estimated path. B receives no truth input.

This controlled simulation has no configured 3D LiDAR noise model. B uses wheel odometry and fixed initial offsets (0.25 m, 0.15 m, 0.12 rad); global relocalization and complete navigation are not tested. Freezing stops updates; localization benefit from cleaning requires lower B error.

XYZ/rotation RMSE now uses common scan timestamps, with truth interpolated to the same instant. The previous 10 Hz latest-pose score mixed in output age and is not directly comparable.
[Dimension, map and scoring audit](results/reference/practice-3d-visible-20261016/audit.json) · [Historical records](results/reference/practice-frozen-20261016)

<a id="scene-static-3d"></a>

#### Static · 3D

**A · Map cleaning**

| Map | SA ↑ |
| --- | --- |
| Raw | 100.00% |
| DUFOMap | 99.99% |
| BeautyMap | 87.71% |


| A · Live 3D acquisition | A · Saved cleaning results (Raw / DUFOMap / BeautyMap) |
| --- | --- |
| <a href="results/reference/practice-3d-visible-20261016/static-A/execution.mp4"><img src="results/reference/practice-3d-visible-20261016/static-A/execution.gif" width="420" loading="lazy" alt="live 3D mapping A acquisition"></a> | <a href="results/reference/practice-3d-visible-20261016/static-A/cleaning-review/result.mp4"><img src="results/reference/practice-3d-visible-20261016/static-A/cleaning-review/result.gif" width="420" loading="lazy" alt="saved map cleaning results"></a> |


The right panel reviews saved cleaning outputs without new inference; click a GIF for the full MP4.

[A acquisition record](results/reference/practice-3d-visible-20261016/static-A/record.json) · [Cleaning review record](results/reference/practice-3d-visible-20261016/static-A/cleaning-review/record.json)

[Mapping A processing record](results/reference/practice-3d-visible-20261016/static-A/maps/record.json)

<a id="scene-static-3d-b"></a>

**B · Localization on frozen maps**

<!-- HOME_EXPERIMENT_TABLE -->
| Frozen map | XYZ RMSE / cm ↓ | Rotation RMSE / ° | Localization B (click for MP4) | Evidence |
| --- | --- | --- | --- | --- |
| Raw | 0.92 | 0.16 | <a href="results/reference/practice-3d-visible-20261016/static-B/executions/raw.mp4"><img src="results/reference/practice-3d-visible-20261016/static-B/executions/raw.gif" width="480" loading="lazy" alt="Raw · localization B"></a> | [Record](results/reference/practice-3d-visible-20261016/static-B/record.json) |
| DUFOMap | 0.98 | 0.18 | <a href="results/reference/practice-3d-visible-20261016/static-B/executions/dufomap.mp4"><img src="results/reference/practice-3d-visible-20261016/static-B/executions/dufomap.gif" width="480" loading="lazy" alt="DUFOMap · localization B"></a> | [Record](results/reference/practice-3d-visible-20261016/static-B/record.json) |
| BeautyMap | 1.14 | 0.21 | <a href="results/reference/practice-3d-visible-20261016/static-B/executions/beautymap.mp4"><img src="results/reference/practice-3d-visible-20261016/static-B/executions/beautymap.gif" width="480" loading="lazy" alt="BeautyMap · localization B"></a> | [Record](results/reference/practice-3d-visible-20261016/static-B/record.json) |
<!-- /HOME_EXPERIMENT_TABLE -->

[Common-scan-time scores](results/reference/practice-3d-visible-20261016/static-B/score.json) · Common valid scans: 458/600

Valid scan-output fraction: Raw 87.83%, DUFOMap 86.83%, BeautyMap 97.33%; output availability is not localization success; RMSE covers common valid scans only.

DUFOMap removes only 39/684477 points, with identical occupied 15 cm cells to Raw. There is no dynamic pollution in this static case, so little pose change is expected.

**Analysis:**
<!-- PRACTICE_ANALYSIS:scene-static-3d -->

<!-- /PRACTICE_ANALYSIS:scene-static-3d -->

[↑ Contents](#practice-index)

<a id="scene-dynamic-3d"></a>

#### Dynamic · 3D

**A · Map cleaning**

| Map | DA ↑ | SA ↑ |
| --- | --- | --- |
| Raw | 0.00% | 100.00% |
| DUFOMap | 52.20% | 99.99% |
| BeautyMap | 71.81% | 87.33% |


| A · Live 3D acquisition | A · Saved cleaning results (Raw / DUFOMap / BeautyMap) |
| --- | --- |
| <a href="results/reference/practice-3d-visible-20261016/dynamic-A/execution.mp4"><img src="results/reference/practice-3d-visible-20261016/dynamic-A/execution.gif" width="420" loading="lazy" alt="live 3D mapping A acquisition"></a> | <a href="results/reference/practice-3d-visible-20261016/dynamic-A/cleaning-review/result.mp4"><img src="results/reference/practice-3d-visible-20261016/dynamic-A/cleaning-review/result.gif" width="420" loading="lazy" alt="saved map cleaning results"></a> |


The right panel reviews saved cleaning outputs without new inference; click a GIF for the full MP4.

[A acquisition record](results/reference/practice-3d-visible-20261016/dynamic-A/record.json) · [Cleaning review record](results/reference/practice-3d-visible-20261016/dynamic-A/cleaning-review/record.json)

[Mapping A processing record](results/reference/practice-3d-visible-20261016/dynamic-A/maps/record.json)

<a id="scene-dynamic-3d-b"></a>

**B · Localization on frozen maps**

<!-- HOME_EXPERIMENT_TABLE -->
| Frozen map | XYZ RMSE / cm ↓ | Rotation RMSE / ° | Localization B (click for MP4) | Evidence |
| --- | --- | --- | --- | --- |
| Raw | 1.18 | 0.22 | <a href="results/reference/practice-3d-visible-20261016/dynamic-B/executions/raw.mp4"><img src="results/reference/practice-3d-visible-20261016/dynamic-B/executions/raw.gif" width="480" loading="lazy" alt="Raw · localization B"></a> | [Record](results/reference/practice-3d-visible-20261016/dynamic-B/record.json) |
| DUFOMap | 1.00 | 0.17 | <a href="results/reference/practice-3d-visible-20261016/dynamic-B/executions/dufomap.mp4"><img src="results/reference/practice-3d-visible-20261016/dynamic-B/executions/dufomap.gif" width="480" loading="lazy" alt="DUFOMap · localization B"></a> | [Record](results/reference/practice-3d-visible-20261016/dynamic-B/record.json) |
| BeautyMap | 1.39 | 0.25 | <a href="results/reference/practice-3d-visible-20261016/dynamic-B/executions/beautymap.mp4"><img src="results/reference/practice-3d-visible-20261016/dynamic-B/executions/beautymap.gif" width="480" loading="lazy" alt="BeautyMap · localization B"></a> | [Record](results/reference/practice-3d-visible-20261016/dynamic-B/record.json) |
<!-- /HOME_EXPERIMENT_TABLE -->

[Common-scan-time scores](results/reference/practice-3d-visible-20261016/dynamic-B/score.json) · Common valid scans: 554/600

Valid scan-output fraction: Raw 96.50%, DUFOMap 95.17%, BeautyMap 99.67%; output availability is not localization success; RMSE covers common valid scans only.

DA/SA describe dynamic removal and static retention; removing traces does not guarantee stronger GICP constraints. Without lower B error, the result supports cleaning only.

**Analysis:**
<!-- PRACTICE_ANALYSIS:scene-dynamic-3d -->

<!-- /PRACTICE_ANALYSIS:scene-dynamic-3d -->

[↑ Contents](#practice-index)

<a id="scene-corridor-3d"></a>

#### Corridor · 3D

**A · Map cleaning**

| Map | SA ↑ |
| --- | --- |
| Raw | 100.00% |
| DUFOMap | 100.00% |
| BeautyMap | 99.84% |


| A · Live 3D acquisition | A · Saved cleaning results (Raw / DUFOMap / BeautyMap) |
| --- | --- |
| <a href="results/reference/practice-3d-visible-20261016/corridor-A/execution.mp4"><img src="results/reference/practice-3d-visible-20261016/corridor-A/execution.gif" width="420" loading="lazy" alt="live 3D mapping A acquisition"></a> | <a href="results/reference/practice-3d-visible-20261016/corridor-A/cleaning-review/result.mp4"><img src="results/reference/practice-3d-visible-20261016/corridor-A/cleaning-review/result.gif" width="420" loading="lazy" alt="saved map cleaning results"></a> |


The right panel reviews saved cleaning outputs without new inference; click a GIF for the full MP4.

[A acquisition record](results/reference/practice-3d-visible-20261016/corridor-A/record.json) · [Cleaning review record](results/reference/practice-3d-visible-20261016/corridor-A/cleaning-review/record.json)

[Mapping A processing record](results/reference/practice-3d-visible-20261016/corridor-A/maps/record.json)

<a id="scene-corridor-3d-b"></a>

**B · Localization on frozen maps**

<!-- HOME_EXPERIMENT_TABLE -->
| Frozen map | XYZ RMSE / cm ↓ | Rotation RMSE / ° | Localization B (click for MP4) | Evidence |
| --- | --- | --- | --- | --- |
| Raw | 756.40 | 5.65 | <a href="results/reference/practice-3d-visible-20261016/corridor-B/executions/raw.mp4"><img src="results/reference/practice-3d-visible-20261016/corridor-B/executions/raw.gif" width="480" loading="lazy" alt="Raw · localization B"></a> | [Record](results/reference/practice-3d-visible-20261016/corridor-B/record.json) |
| DUFOMap | 449.10 | 0.49 | <a href="results/reference/practice-3d-visible-20261016/corridor-B/executions/dufomap.mp4"><img src="results/reference/practice-3d-visible-20261016/corridor-B/executions/dufomap.gif" width="480" loading="lazy" alt="DUFOMap · localization B"></a> | [Record](results/reference/practice-3d-visible-20261016/corridor-B/record.json) |
| BeautyMap | 482.16 | 0.43 | <a href="results/reference/practice-3d-visible-20261016/corridor-B/executions/beautymap.mp4"><img src="results/reference/practice-3d-visible-20261016/corridor-B/executions/beautymap.gif" width="480" loading="lazy" alt="BeautyMap · localization B"></a> | [Record](results/reference/practice-3d-visible-20261016/corridor-B/record.json) |
<!-- /HOME_EXPERIMENT_TABLE -->

[Common-scan-time scores](results/reference/practice-3d-visible-20261016/corridor-B/score.json) · Common valid scans: 381/599

Observations are restricted for 50 s, then restored; all three cases drift by metres in this trial. Raw and DUFOMap frozen maps are byte-identical; separate processes can have different scan histories, so a single-run pose difference cannot be attributed to cleaning.

Valid scan-output fraction: Raw 74.29%, DUFOMap 69.95%, BeautyMap 94.49%; output availability is not localization success; RMSE covers common valid scans only.

**Analysis:**
<!-- PRACTICE_ANALYSIS:scene-corridor-3d -->

<!-- /PRACTICE_ANALYSIS:scene-corridor-3d -->

[↑ Contents](#practice-index)

<a id="scene-change-3d"></a>

#### Changed world · 3D

This group freezes static-A maps and acquires B in the changed world; the A table retains cleaning scores for those static maps.

**A · Map cleaning**

| Map | SA ↑ |
| --- | --- |
| Raw | 100.00% |
| DUFOMap | 99.99% |
| BeautyMap | 87.71% |


| A · Live 3D acquisition | A · Saved cleaning results (Raw / DUFOMap / BeautyMap) |
| --- | --- |
| <a href="results/reference/practice-3d-visible-20261016/static-A/execution.mp4"><img src="results/reference/practice-3d-visible-20261016/static-A/execution.gif" width="420" loading="lazy" alt="live 3D mapping A acquisition"></a> | <a href="results/reference/practice-3d-visible-20261016/static-A/cleaning-review/result.mp4"><img src="results/reference/practice-3d-visible-20261016/static-A/cleaning-review/result.gif" width="420" loading="lazy" alt="saved map cleaning results"></a> |


The right panel reviews saved cleaning outputs without new inference; click a GIF for the full MP4.

[A acquisition record](results/reference/practice-3d-visible-20261016/static-A/record.json) · [Cleaning review record](results/reference/practice-3d-visible-20261016/static-A/cleaning-review/record.json)

[Mapping A processing record](results/reference/practice-3d-visible-20261016/static-A/maps/record.json)

<a id="scene-change-3d-b"></a>

**B · Localization on frozen maps**

<!-- HOME_EXPERIMENT_TABLE -->
| Frozen map | XYZ RMSE / cm ↓ | Rotation RMSE / ° | Localization B (click for MP4) | Evidence |
| --- | --- | --- | --- | --- |
| Raw | 1.06 | 0.23 | <a href="results/reference/practice-3d-visible-20261016/change-B/executions/raw.mp4"><img src="results/reference/practice-3d-visible-20261016/change-B/executions/raw.gif" width="480" loading="lazy" alt="Raw · localization B"></a> | [Record](results/reference/practice-3d-visible-20261016/change-B/record.json) |
| DUFOMap | 1.08 | 0.24 | <a href="results/reference/practice-3d-visible-20261016/change-B/executions/dufomap.mp4"><img src="results/reference/practice-3d-visible-20261016/change-B/executions/dufomap.gif" width="480" loading="lazy" alt="DUFOMap · localization B"></a> | [Record](results/reference/practice-3d-visible-20261016/change-B/record.json) |
| BeautyMap | 1.24 | 0.27 | <a href="results/reference/practice-3d-visible-20261016/change-B/executions/beautymap.mp4"><img src="results/reference/practice-3d-visible-20261016/change-B/executions/beautymap.gif" width="480" loading="lazy" alt="BeautyMap · localization B"></a> | [Record](results/reference/practice-3d-visible-20261016/change-B/record.json) |
<!-- /HOME_EXPERIMENT_TABLE -->

[Common-scan-time scores](results/reference/practice-3d-visible-20261016/change-B/score.json) · Common valid scans: 486/599

Valid scan-output fraction: Raw 91.32%, DUFOMap 90.32%, BeautyMap 97.33%; output availability is not localization success; RMSE covers common valid scans only.

**Analysis:**
<!-- PRACTICE_ANALYSIS:scene-change-3d -->

<!-- /PRACTICE_ANALYSIS:scene-change-3d -->

[↑ Contents](#practice-index)

<a id="practice-appendix"></a>

### Supplementary experiments

<a id="supp-srrg"></a>

#### SRRG · Persistent change

| Method | SA | New structure coverage |
| --- | --- | --- |
| Raw | 100.00% | 100.00% |
| SRRG | 99.71% | 98.90% |


[Record](results/reference/srrg-2d-large-change/record.json)

| SRRG changed-world A |
| --- |
| <a href="results/reference/srrg-2d-large-change/execution.mp4"><img src="results/reference/srrg-2d-large-change/execution.gif" width="340" loading="lazy" alt="SRRG changed-world A"></a> |


<a id="supp-srrg-b"></a>

**B · Localization on frozen maps**

Freeze both maps from persistent-change mapping A; acquire fresh B in the changed world and localize with identical AMCL settings.

| Frozen map | XY RMSE / cm ↓ | yaw RMSE / ° | Localization B (click for MP4) | Evidence |
| --- | --- | --- | --- | --- |
| Raw | 5.40 | 2.86 | <a href="results/reference/practice-frozen-20261016/srrg-change/executions/raw.mp4"><img src="results/reference/practice-frozen-20261016/srrg-change/executions/raw.gif" width="320" loading="lazy" alt="Raw · localization B"></a> | [Record](results/reference/practice-frozen-20261016/srrg-change/record.json) |
| SRRG | 4.36 | 2.65 | <a href="results/reference/practice-frozen-20261016/srrg-change/executions/srrg.mp4"><img src="results/reference/practice-frozen-20261016/srrg-change/executions/srrg.gif" width="320" loading="lazy" alt="SRRG · localization B"></a> | [Record](results/reference/practice-frozen-20261016/srrg-change/record.json) |


[Common-time scores](results/reference/practice-frozen-20261016/srrg-change/score.json) · Common valid samples: 273/601

AMCL publishes after motion thresholds are met; the count includes only common times with pose age ≤0.15 s and is not a localization success rate.

**Analysis:**
<!-- PRACTICE_ANALYSIS:srrg-large-change-2d -->

<!-- /PRACTICE_ANALYSIS:srrg-large-change-2d -->

[↑ Contents](#practice-index)

<a id="map-review-3d"></a>

#### Saved point-cloud replay

| Saved results; no new inference |
| --- |
| <a href="results/reference/robot-3d-map-review-v2/execution.mp4"><img src="results/reference/robot-3d-map-review-v2/execution.gif" width="340" loading="lazy" alt="Saved results; no new inference"></a> |


<a id="supp-registrations"></a>

#### Raw · NDT / GICP

| Method | XY RMSE / cm | yaw / ° | Evidence |
| --- | --- | --- | --- |
| NDT initial | 34.43 | 0.15 | [Record](results/reference/robot-ndt-static-initial/record.json) · [MP4](results/reference/robot-ndt-static-initial/execution.mp4) |
| NDT | 0.93 | 0.17 | [Record](results/reference/robot-ndt-static/record.json) · [MP4](results/reference/robot-ndt-static/execution.mp4) |
| GICP | 1.09 | 0.16 | [Record](results/reference/robot-gicp-static/record.json) · [MP4](results/reference/robot-gicp-static/execution.mp4) |


<a id="supp-acquisition"></a>

#### Additional acquisition and localization

| Scene | Method | Scan frames | Record | Recording |
| --- | --- | --- | --- | --- |
| Static | slam_toolbox | 54 | [Record](results/reference/robot-supp-static/record.json) | [MP4](results/reference/robot-supp-static/execution.mp4) |
| Dynamic | slam_toolbox | 55 | [Record](results/reference/robot-supp-dynamic/record.json) | [MP4](results/reference/robot-supp-dynamic/execution.mp4) |
| Changed world | AMCL | — | [Record](results/reference/robot-supp-large-change/record.json) | [MP4](results/reference/robot-supp-large-change/execution.mp4) |


<a id="srrg-diagnostics"></a>

#### SRRG failed runs

| Stage | Status | Record | Recording |
| --- | --- | --- | --- |
| Eigen ABI | diagnostic_failed | [Record](results/reference/srrg-diagnostic-20261015-025711-mapping-srrg-static-dd423d/record.json) | [MP4](results/reference/srrg-diagnostic-20261015-025711-mapping-srrg-static-dd423d/execution.mp4) |
| stdout | diagnostic_failed | [Record](results/reference/srrg-diagnostic-20261015-030327-mapping-srrg-static-a275d3/record.json) | [MP4](results/reference/srrg-diagnostic-20261015-030327-mapping-srrg-static-a275d3/execution.mp4) |
| g2o | diagnostic_failed | [Record](results/reference/srrg-diagnostic-20261015-030729-mapping-srrg-dynamic-14123d/record.json) | [MP4](results/reference/srrg-diagnostic-20261015-030729-mapping-srrg-dynamic-14123d/execution.mp4) |


[↑ Contents](#practice-index)

<a id="practice-irmcl"></a>

### IR-MCL

| Recording | Metrics | Record |
| --- | --- | --- |
| <a href="results/reference/desktop-live-ir-mcl/execution.mp4"><img src="docs/media/related-pointcloud/20261016/ir-mcl.gif" width="340" alt="IR-MCL"></a> | XY RMSE 5.31 cm / yaw 1.07° | [Record](results/reference/desktop-live-ir-mcl/record.json) |

**Analysis:**

[↑ Contents](#practice-index)

<a id="practice-adam"></a>

### AdaM-MCL

| Recording | Metrics | Record |
| --- | --- | --- |
| <a href="results/reference/desktop-adam-mcl/result.mp4"><img src="results/reference/desktop-adam-mcl/result.gif" width="340" alt="AdaM-MCL"></a> | RMSE 32.23 cells; sustained convergence 0/10; saved-result replay | [Record](results/reference/desktop-adam-mcl/record.json) |

**Analysis:**

[↑ Contents](#practice-index)

<a id="hypothesis-test"></a>

## Hypothesis test

<a id="hypothesis-test-index"></a>

Experiments for project-written methods. H1 rebuilds maps from the same original A and uses old B for development ablation. After fixing the rule, acquire one fresh static B and three fresh dynamic B sessions. H2 retains its original single A/B trial. Each paired trial shares scans, odometry, AMCL parameters and initialization.

| Experiment | Mapping and scores | Held-out localization and scores |
| --- | --- | --- |
| H1 old-B development ablation | — | [↗](#h1-revision-ablation) |
| H1 Static retention | [A](#own-static-a) | [B](#own-static-b) |
| H1 Dynamic cleaning | [A](#own-dynamic-a) | [B](#own-dynamic-b) |
| H2 Odometry deskew | [A](#own-motion-a) | [B](#own-motion-b) |

Use the same omni robot as Practice; algorithms use only 2D LiDAR and wheel odometry. H2 combines sectors from three actual scan times, preserving each point timestamp, without FAST-LIO.

[Own cleaner](src/slam_learning/runtime/own_mapping.py) · [Own alignment](src/slam_learning/runtime/own_refinement.py) · [Record H1 confirmation](demo/record-h1-revision.ps1) · [Settings fixed before acquisition](results/reference/h1-refined-20261016/confirmation-protocol.json)

H2 recording phases: stationary 0–7 s, slow turn 7–15 s, fast turns 15–31 s, translation 31–39 s.

<a id="h1-revision-ablation"></a>

### H1 · Old-B development ablation

The old rule loses 6.95 percentage points of SA, while A wheel-pose RMSE is 7.74 cm. Cleaning cannot correct mapping-pose error, so the final method adds own robust 2D alignment. This table reruns the same old B for development ablation and is excluded from final fresh-B scores.

| Method | DA ↑ | SA ↑ | XY RMSE / cm ↓ |
| --- | --- | --- | --- |
| Raw | 5.13% | 99.50% | 5.72 |
| Old per-cell filtering | 94.87% | 92.55% | 6.11 |
| Later-free confirmation (pilot) | 29.49% | 99.50% | 5.81 |
| Neighborhood temporal: filter only | 79.49% | 99.17% | 5.66 |
| Own alignment only | 0.00% | 100.00% | 4.86 |
| Own alignment + cleaning (final) | 58.97% | 99.67% | 4.41 |

[Native AMCL rerun record](results/reference/h1-refined-20261016/dynamic-replay/trial-1/record.json) · [Original negative result](results/reference/own-hypotheses-20261016/dynamic-B/record.json)

Three fresh B sessions for filter-only yielded Raw 6.02 cm and filter-only 6.06 cm, without improvement; that full batch is retained. The main experiment below uses another fresh B batch for the final joint method. [Filter-only confirmation](results/reference/h1-supported-20261016/confirmation-score.json)

<a id="own-static-a"></a>

### H1 · Static retention · A

| Control | SA ↑ |
| --- | --- |
| M₀ · Raw: wheel-pose accumulation | 99.55% |
| M₁ · Align+Temporal: own alignment + cleaning | 100.00% |

| Original A acquisition (old algorithm view) | Same A reprocessed: grey Raw, blue revised |
| --- | --- |
| <a href="results/reference/own-hypotheses-20261016/static-A/execution.mp4"><img src="results/reference/own-hypotheses-20261016/static-A/execution.gif" width="420" loading="lazy" alt="H1 · Static retention original A"></a> | <a href="results/reference/h1-refined-20261016/static-A/execution.mp4"><img src="results/reference/h1-refined-20261016/static-A/execution.gif" width="420" loading="lazy" alt="H1 · Static retention revised A input replay"></a> |

[Record](results/reference/h1-refined-20261016/static-A/record.json)

**Analysis:**
<!-- OWN_ANALYSIS:static-a -->

<!-- /OWN_ANALYSIS:static-a -->

<a id="own-static-b"></a>

### H1 · Static retention · B

Acquire fresh B and use the same AMCL on frozen maps. One static control session.

| Map / AMCL | XY RMSE / cm ↓ | Localization recording (click MP4) |
| --- | --- | --- |
| M₀ · Raw: wheel-pose accumulation | 5.44 | <a href="results/reference/h1-refined-20261016/static-B/executions/raw.mp4"><img src="results/reference/h1-refined-20261016/static-B/executions/raw.gif" width="420" loading="lazy" alt="raw fresh B"></a> |
| M₁ · Align+Temporal: own alignment + cleaning | 4.64 | <a href="results/reference/h1-refined-20261016/static-B/executions/temporal.mp4"><img src="results/reference/h1-refined-20261016/static-B/executions/temporal.gif" width="420" loading="lazy" alt="temporal fresh B"></a> |

[Common-time scores](results/reference/h1-refined-20261016/static-B/time-grid-score.json) · [Record](results/reference/h1-refined-20261016/static-B/record.json)

**Analysis:**
<!-- OWN_ANALYSIS:static-b -->

<!-- /OWN_ANALYSIS:static-b -->

[↑ Contents](#hypothesis-test-index)

<a id="own-dynamic-a"></a>

### H1 · Dynamic cleaning · A

| Control | DA ↑ | SA ↑ |
| --- | --- | --- |
| M₀ · Raw: wheel-pose accumulation | 5.13% | 99.50% |
| M₁ · Align+Temporal: own alignment + cleaning | 58.97% | 99.67% |

| Original A acquisition (old algorithm view) | Same A reprocessed: grey Raw, blue revised |
| --- | --- |
| <a href="results/reference/own-hypotheses-20261016/dynamic-A/execution.mp4"><img src="results/reference/own-hypotheses-20261016/dynamic-A/execution.gif" width="420" loading="lazy" alt="H1 · Dynamic cleaning original A"></a> | <a href="results/reference/h1-refined-20261016/dynamic-A/execution.mp4"><img src="results/reference/h1-refined-20261016/dynamic-A/execution.gif" width="420" loading="lazy" alt="H1 · Dynamic cleaning revised A input replay"></a> |

[Record](results/reference/h1-refined-20261016/dynamic-A/record.json)

**Analysis:**
<!-- OWN_ANALYSIS:dynamic-a -->

<!-- /OWN_ANALYSIS:dynamic-a -->

<a id="own-dynamic-b"></a>

### H1 · Dynamic cleaning · B

Acquire fresh B and use the same AMCL on frozen maps. The table pools common-time samples from all three B sessions; GIFs always show trial 1.

| Map / AMCL | XY RMSE / cm ↓ | Localization recording (click MP4) |
| --- | --- | --- |
| M₀ · Raw: wheel-pose accumulation | 5.82 | <a href="results/reference/h1-refined-20261016/dynamic-B/executions/raw.mp4"><img src="results/reference/h1-refined-20261016/dynamic-B/executions/raw.gif" width="420" loading="lazy" alt="raw fresh B"></a> |
| M₁ · Align+Temporal: own alignment + cleaning | 4.65 | <a href="results/reference/h1-refined-20261016/dynamic-B/executions/temporal.mp4"><img src="results/reference/h1-refined-20261016/dynamic-B/executions/temporal.gif" width="420" loading="lazy" alt="temporal fresh B"></a> |

| Trial | Raw / cm | Temporal / cm | Full recordings |
| --- | --- | --- | --- |
| 1 | 4.95 | 4.75 | [Raw MP4](results/reference/h1-refined-20261016/dynamic-B/executions/raw.mp4) · [Temporal MP4](results/reference/h1-refined-20261016/dynamic-B/executions/temporal.mp4) |
| 2 | 5.55 | 4.56 | [Raw MP4](results/reference/h1-refined-20261016/dynamic-B2/executions/raw.mp4) · [Temporal MP4](results/reference/h1-refined-20261016/dynamic-B2/executions/temporal.mp4) |
| 3 | 6.52 | 4.69 | [Raw MP4](results/reference/h1-refined-20261016/dynamic-B3/executions/raw.mp4) · [Temporal MP4](results/reference/h1-refined-20261016/dynamic-B3/executions/temporal.mp4) |

[Common-time scores](results/reference/h1-refined-20261016/confirmation-score.json) · [Record](results/reference/h1-refined-20261016/dynamic-B/record.json)

**Analysis:**
<!-- OWN_ANALYSIS:dynamic-b -->

<!-- /OWN_ANALYSIS:dynamic-b -->

[↑ Contents](#hypothesis-test-index)

<a id="own-motion-a"></a>

### H2 · Odometry deskew · A

| Control | Map RMSE / cm ↓ |
| --- | --- |
| M₀ · Off: uncompensated | 34.10 |
| M₁ · On: motion compensated | 4.57 |

| Mapping: grey baseline, blue own intervention |
| --- |
| <a href="results/reference/own-hypotheses-20261016/motion-A/execution.mp4"><img src="results/reference/own-hypotheses-20261016/motion-A/execution.gif" width="840" loading="lazy" alt="H2 · Odometry deskew A"></a> |

[Record](results/reference/own-hypotheses-20261016/motion-A/record.json)

**Analysis:**
<!-- OWN_ANALYSIS:motion-a -->

<!-- /OWN_ANALYSIS:motion-a -->

<a id="own-motion-b"></a>

### H2 · Odometry deskew · B

| Map / AMCL | XY RMSE / cm ↓ |
| --- | --- |
| M₀ · Off: uncompensated | 4.70 |
| M₁ · On: motion compensated | 4.71 |

| M₀ · Off: uncompensated | M₁ · On: motion compensated |
| --- | --- |
| <a href="results/reference/own-hypotheses-20261016/motion-B/executions/off.mp4"><img src="results/reference/own-hypotheses-20261016/motion-B/executions/off.gif" width="420" loading="lazy" alt="off B"></a> | <a href="results/reference/own-hypotheses-20261016/motion-B/executions/deskew.mp4"><img src="results/reference/own-hypotheses-20261016/motion-B/executions/deskew.gif" width="420" loading="lazy" alt="deskew B"></a> |

[Common-time scores](results/reference/own-hypotheses-20261016/motion-B/time-grid-score.json) · [Record](results/reference/own-hypotheses-20261016/motion-B/record.json)

**Analysis:**
<!-- OWN_ANALYSIS:motion-b -->

<!-- /OWN_ANALYSIS:motion-b -->

[↑ Contents](#hypothesis-test-index)

H1 uses DA/SA for cleaning and only SA in its static control; H2 uses one-way map-to-static-support RMSE. Localization uses common 10 Hz times after 5 s warmup, with output age at most 0.15 s; sample counts and missing outputs remain in the score records. Better mapping scores without lower B error support only the mapping claim.
