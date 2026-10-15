<div align="center">

# SLAM Learning

**Robust localization and SLAM in dynamic environments**

Dynamic map cleaning · Static structure retention · Downstream localization

[![CPU reproducibility](https://github.com/p20030920p/SLAM_Learning/actions/workflows/ci.yml/badge.svg)](https://github.com/p20030920p/SLAM_Learning/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.10-3776AB)](src/pyproject.toml)

English | [中文](docs/HOME.zh-CN.md)

[Physical test problems](#problem-getting-from-physical-test) · [Direction](#direction-analysis) · [Open question](#open-question) · [Hypothesis](#hypothesis) · [Related works](#related-works) · [Metrics](#metrics)

[Practice](#practice) · [Branches](#branches)

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

| Question | Hypothesis | Controls | Metrics |
| --- | --- | --- | --- |
| H1 / Q1 | Dynamic cleaning removes traces while retaining static structure and reduces held-out localization error. | Raw / SRRG | DA, SA, Eₘ, XY RMSE |
| H2 / Q2 | FAST-LIO deskew reduces motion-induced map error and improves held-out localization accuracy. | Point compensation off / on | Eₘ, Cₘ, XYZ RMSE |
| H3 / Q3 | Adding LiDAR-visible asymmetric static references reduces along-corridor localization error. | Original / landmark corridor | Eₘ, SA, along RMSE |

Goal: first measure map improvement, then test whether the same localizer has lower error on independent B.

Mirror identification and physical reflections remain open within Q3; physical evidence stays at the top.

<a id="hypothesis-math"></a>

### Mathematical form

A builds the map; B is a separate acquisition. Freeze A's map and run the same localizer on B. $`j`$ indexes the control, $`Z`$ denotes scans, $`T`$ is the sensor pose and $`p^{\ast}`$ is true position:

```math
M_j = \mathcal{B}_j\bigl(Z^A,\hat{T}_j^A\bigr)
```

```math
\hat{T}_{j,t}^B = \mathcal{L}\bigl(Z_{\leq t}^B,M_j\bigr)
```

```math
E_L(j) = \sqrt{\frac{1}{N}\sum_t\left\lVert\hat{p}_{j,t}^B-p_t^{B,\ast}\right\rVert^2}
```

```math
\Delta E_L = E_L(\mathrm{baseline})-E_L(\mathrm{method})
```

$`\Delta E_L\gt 0`$ means improved localization; lower map error $`E_M`$ with $`\Delta E_L\leq 0`$ supports only map improvement. Test these predictions:

**H1**

```math
\mathrm{DA}_{\mathrm{SRRG}}\gt\mathrm{DA}_{\mathrm{Raw}},\qquad \mathrm{SA}_{\mathrm{SRRG}}\geq\mathrm{SA}_{\mathrm{Raw}}-\varepsilon
```

```math
E_M(\mathrm{SRRG})\lt E_M(\mathrm{Raw}),\qquad\Delta E_L\gt 0
```

**H2**

```math
p_i^{\mathrm{end}}=T(t_{\mathrm{end}})^{-1}T(t_i)p_i
```

```math
E_M(\mathrm{on})\lt E_M(\mathrm{off}),\qquad\Delta E_L\gt 0
```

**H3**

```math
E_{\parallel}=\sqrt{\frac{1}{N}\sum_t\left[u^{\mathsf{T}}\left(\hat{p}_t-p_t^{\ast}\right)\right]^2}
```

```math
E_{\parallel}(\mathrm{landmark})\lt E_{\parallel}(\mathrm{original})
```

$`\varepsilon=1`$ percentage point is the static-loss tolerance; $`u`$ is the corridor direction. This SRRG comparison includes pose optimization and maintenance; deletion alone at fixed poses remains untested. Truth is used only for scoring.

<a id="hypothesis-pseudocode"></a>

### Pseudocode

```text
for scene in [static, dynamic, motion, corridor, corridor_landmarks]:
    controls = methods_for(scene)
    A, maps = record_A_and_build_maps(scene, controls)
    map_metrics = score_and_freeze(maps)
    B = record_new_localization_session(scene)
    poses = same_localizer_for_all_maps(B, maps)
    report(map_metrics, score_on_common_times(poses, B.truth))
    save_native_recordings_and_input_hashes()
compare_corridor_variants_on_common_elapsed_times()
```

For H3, acquire A/B in each corridor variant with the same route, speed, initial offset and localization settings.

[Experiments and new recordings](#practice-index)

## Related works

<!-- HOME_RELATED_TABLE -->
Grouped by algorithm family. Click a GIF for the full video. The application-direction column is intentionally blank. Different data protocols prevent cross-row ranking.

| Method / algorithm family | Native GIF / original point-cloud figure | Measured metrics and scope | Application direction |
| --- | --- | --- | --- |
| <a id="related-fast_lio"></a>[FAST-LIO / FAST-LIO2](docs/papers/fast_lio.md) | <img src="docs/assets/related/20261016-pointcloud/fastlio2-fig12.png" width="280" alt="FAST-LIO2 original Fig. 12: point-cloud map"> | Original-paper experiments: **not reproduced**; original figure and method summary; custom-scene tests in Practice |  |
| <a id="related-srrg_mapper2d"></a>[SRRG / srrg_mapper2d](docs/papers/srrg_mapper2d.md) | <img src="docs/assets/related/20261016-pointcloud/srrg-fig7.png" width="280" alt="SRRG original Fig. 7: point-cloud map"> | Original-paper experiments: **not reproduced**; original figure and method summary; custom-scene tests in Practice |  |
| <a id="related-dufomap"></a>[DUFOMap](docs/papers/dufomap.md)<br>3D map cleaning | <a href="results/reference/desktop-live-dufomap/execution.mp4"><img src="docs/media/related-pointcloud/20261016/dufomap.gif" width="280" loading="lazy" alt="dufomap · Point-cloud capture excerpt"></a><br>[Point-cloud capture excerpt](results/reference/desktop-live-dufomap/execution.mp4) | SA 97.98% / DA 98.7%<br>KITTI-00 · 141 scans; cleaning demonstrated<br>[Record](results/reference/desktop-live-dufomap/record.json) |  |
| <a id="related-beautymap"></a>[BeautyMap](docs/papers/beautymap.md)<br>Offline 3D map cleaning | <a href="results/reference/desktop-live-beautymap/execution.mp4"><img src="docs/media/related-pointcloud/20261016/beautymap.gif" width="280" loading="lazy" alt="beautymap · Point-cloud capture excerpt"></a><br>[Point-cloud capture excerpt](results/reference/desktop-live-beautymap/execution.mp4) | SA 96.95% / DA 98.34%<br>KITTI-00 · 141 scans; cleaning demonstrated<br>[Record](results/reference/desktop-live-beautymap/record.json) |  |
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

**Original-paper experiments: not reproduced.** The original figure introduces the method. Custom Gazebo runs of the author code appear separately in [Practice](#experiment-h1); these do not reproduce the LCAS/MIT Stata long-term multi-session benchmark.

![SRRG · original point-cloud Fig. 7](docs/assets/related/20261016-pointcloud/srrg-fig7.png)

Source: Lázaro et al., *Efficient Long-term Mapping in Dynamic Environments*, IROS 2018, Fig. 7, page 6. [Paper](https://iris.uniroma1.it/handle/11573/1340118) · [Author code](https://gitlab.com/srrg-software/srrg_mapper2d). Registration, local maintenance and graph optimization connect H1 to geometric conditions in H3.
<!-- /SRRG_RELATED -->

<!-- FASTLIO_RELATED -->
### FAST-LIO / FAST-LIO2 · LiDAR–IMU estimation and point compensation

**Original-paper experiments: not reproduced.** This is the original FAST-LIO2 paper figure. Our custom-scene ablation uses the official ROS2 branch and FAST-LIO2 direct registration, distinct from reproducing the first FAST-LIO paper. [New hypothesis tests](#experiment-h2).

![FAST-LIO2 · original point-cloud Fig. 12](docs/assets/related/20261016-pointcloud/fastlio2-fig12.png)

Source: Xu et al., *FAST-LIO2: Fast Direct LiDAR-inertial Odometry*, Fig. 12, page 16. [FAST-LIO](https://arxiv.org/abs/2010.08196) · [FAST-LIO2](https://arxiv.org/abs/2107.06829) · [Official ROS2 code](https://github.com/hku-mars/FAST_LIO/tree/ROS2). IMU propagation and backward point compensation address H2. The incremental spatial index is not a dynamic-object removal or mirror detector.
<!-- /FASTLIO_RELATED -->
<!-- /HOME_RELATED_DETAILS -->

</details>

## Metrics

| Metric | Definition |
| --- | --- |
| DA ↑ / SA ↑ | Dynamic-trace removal / static retention; SRRG scores spatial-support coverage. |
| Eₘ ↓ | Map distance RMSE, cm; observed static support in 2D, reference surfaces in 3D. |
| Cₘ ↑ | Fraction of observed static reference covered by the map. |
| XY / XYZ / along RMSE ↓ | 2D / 3D / along-corridor position error, cm. |
| Angular RMSE ↓ | 2D yaw or 3D rotation error, degrees. |
| P95 ↓ / N / Update coverage ↑ | 95th-percentile position error / valid samples / grid fraction with fresh outputs. |
| N/A | Not applicable; DA is undefined without dynamics. |

### Evidence

| DUFOMap · KITTI-00 · Metric | Paper % | Reproduced % |
| --- | ---: | ---: |
| SA | 97.96 | 97.9635 |
| DA | 98.72 | 98.7196 |
| AA | 98.34 | 98.3408 |

| BeautyMap · KITTI-02 · Metric | Paper % | Reproduced % |
| --- | ---: | ---: |
| SA | 83.40 | 83.3978 |
| DA | 82.41 | 82.4092 |
| HA | 82.90 | 82.9006 |

| IR-MCL · Metric | Paper, Seq 1 | Reproduced |
| --- | ---: | ---: |
| Location RMSE (cm) | 5.13 | 5.32 |
| Yaw RMSE (deg) | 1.05 | 1.07 |
| Location < 5 cm (%) | 63.15 | 61.74 |
| Location < 10 cm (%) | 97.27 | 96.01 |
| Location < 20 cm (%) | 100.00 | 100.00 |
| Yaw < 0.5° (%) | 47.12 | 47.64 |
| Yaw < 1° (%) | 74.59 | 75.85 |
| Yaw < 2° (%) | 94.24 | 93.57 |

| AdaM-MCL · Metric | Paper Table II | This run |
| --- | ---: | ---: |
| Global localization $E_{pos}$ | 0.153 m | not compared |
| Kidnapping $E_{pos}$ | 0.128 m | not compared |

## Practice

<!-- HOME_EXPERIMENTS_V2 -->
<!-- SIMPLE_HYPOTHESES_V2 -->

<a id="practice-index"></a>

### Contents

| No. | Experiment | Subexperiments (direct links) |
| --- | --- | --- |
| 0 | [Setup](#practice-setup) | [URDF](#robot-urdf) · [Metrics](#practice-metrics) |
| 1 | [H1 · Dynamic cleaning](#experiment-h1) | [Static A](#h1-static-a) / [B](#h1-static-b) · [Dynamic A](#h1-dynamic-a) / [B](#h1-dynamic-b) |
| 2 | [H2 · FAST-LIO](#experiment-h2) | [A](#h2-a) · [Stationary](#h2-stationary) / [Slow turn](#h2-slow) / [Fast turn](#h2-fast) / [Translation](#h2-translation) · [B](#h2-b) |
| 3 | [H3 · Corridor references](#experiment-h3) | [Original A](#h3-original-a) / [B](#h3-original-b) · [Landmark A](#h3-landmark-a) / [B](#h3-landmark-b) · [Paired scores](#h3-scores) |
| 4 | [Existing 3D tests](#baseline-3d) | [Static](#scene-static-3d) · [Dynamic](#scene-dynamic-3d) · [Corridor](#scene-corridor-3d) · [Changed world](#scene-change-3d) |
| 5 | [Supplementary experiments](#practice-appendix) | [SRRG](#supp-srrg) · [Cloud replay](#map-review-3d) · [NDT/GICP](#supp-registrations) · [Acquisition](#supp-acquisition) · [Failed runs](#srrg-diagnostics) |


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

New localization scores use common 10 Hz times after 5 s warmup, with pose age ≤0.15 s; update coverage is not a tracking-loss rate. One run per arm.

<a id="experiment-h1"></a>

### H1 · Dynamic cleaning → held-out localization

| Scene | Change | Keep fixed |
| --- | --- | --- |
| Static control / moving obstacles | Raw / SRRG | Shared A scans, shared B scans, AMCL settings and initial offset |


<a id="h1-static-a"></a>

#### Static · A

| Method | DA | SA | Eₘ / cm |
| --- | --- | --- | --- |
| Raw | N/A | 100.00% | 3.79 |
| SRRG | N/A | 100.00% | 2.57 |


[Record](results/reference/direction-20261016-v2/2d-A-static/record.json)

| A · Raw / SRRG |
| --- |
| <a href="results/reference/direction-20261016-v2/2d-A-static/execution.mp4"><img src="results/reference/direction-20261016-v2/2d-A-static/execution.gif" width="340" loading="lazy" alt="A · Raw / SRRG"></a> |


**Analysis:**
<!-- PRACTICE_ANALYSIS:h1-static-a -->

<!-- /PRACTICE_ANALYSIS:h1-static-a -->

[↑ Contents](#practice-index)

<a id="h1-static-b"></a>

#### Static · B

| Map | XY RMSE / cm | yaw / ° | P95 / cm | Update coverage | N |
| --- | --- | --- | --- | --- | --- |
| Raw | 5.03 | 2.88 | 8.76 | 41.43% | 278 |
| SRRG | 5.84 | 2.91 | 9.58 | 41.43% | 278 |


[Scores](results/reference/direction-20261016-v2/2d-static/time-grid-score.json)

| Raw | SRRG |
| --- | --- |
| <a href="results/reference/direction-20261016-v2/2d-static/executions/raw.mp4"><img src="results/reference/direction-20261016-v2/2d-static/executions/raw.gif" width="340" loading="lazy" alt="Raw"></a> | <a href="results/reference/direction-20261016-v2/2d-static/executions/srrg.mp4"><img src="results/reference/direction-20261016-v2/2d-static/executions/srrg.gif" width="340" loading="lazy" alt="SRRG"></a> |


**Analysis:**
<!-- PRACTICE_ANALYSIS:h1-static-b -->

<!-- /PRACTICE_ANALYSIS:h1-static-b -->

[↑ Contents](#practice-index)

<a id="h1-dynamic-a"></a>

#### Dynamic · A

| Method | DA | SA | Eₘ / cm |
| --- | --- | --- | --- |
| Raw | 0.00% | 100.00% | 49.05 |
| SRRG | 36.94% | 99.84% | 15.45 |


[Record](results/reference/direction-20261016-v2/2d-A-dynamic/record.json)

| A · Raw / SRRG |
| --- |
| <a href="results/reference/direction-20261016-v2/2d-A-dynamic/execution.mp4"><img src="results/reference/direction-20261016-v2/2d-A-dynamic/execution.gif" width="340" loading="lazy" alt="A · Raw / SRRG"></a> |


**Analysis:**
<!-- PRACTICE_ANALYSIS:h1-dynamic-a -->

<!-- /PRACTICE_ANALYSIS:h1-dynamic-a -->

[↑ Contents](#practice-index)

<a id="h1-dynamic-b"></a>

#### Dynamic · B

| Map | XY RMSE / cm | yaw / ° | P95 / cm | Update coverage | N |
| --- | --- | --- | --- | --- | --- |
| Raw | 5.53 | 0.76 | 7.92 | 66.77% | 448 |
| SRRG | 5.13 | 0.70 | 7.32 | 66.77% | 448 |


[Scores](results/reference/direction-20261016-v2/2d-dynamic/time-grid-score.json)

| Raw | SRRG |
| --- | --- |
| <a href="results/reference/direction-20261016-v2/2d-dynamic/executions/raw.mp4"><img src="results/reference/direction-20261016-v2/2d-dynamic/executions/raw.gif" width="340" loading="lazy" alt="Raw"></a> | <a href="results/reference/direction-20261016-v2/2d-dynamic/executions/srrg.mp4"><img src="results/reference/direction-20261016-v2/2d-dynamic/executions/srrg.gif" width="340" loading="lazy" alt="SRRG"></a> |


**Analysis:**
<!-- PRACTICE_ANALYSIS:h1-dynamic-b -->

<!-- /PRACTICE_ANALYSIS:h1-dynamic-b -->

[↑ Contents](#practice-index)

<a id="experiment-h2"></a>

### H2 · FAST-LIO motion distortion

| Scene | Change | Keep fixed |
| --- | --- | --- |
| Existing static scene; stationary → slow/fast turns → translation | FAST-LIO point compensation off / on | Same scans, point timing, IMU and state prediction; identical GICP for B |


Three measured 120° sectors form a 0.2 s scan; this is controlled grouped sampling.

<a id="h2-a"></a>

#### A · Mapping and motion phases

| Point compensation | Eₘ / cm | Cₘ |
| --- | --- | --- |
| Off | 13.49 | 82.28% |
| On | 4.61 | 94.38% |


[Scores](results/reference/direction-20261016-v2/fastlio-maps/score.json)

| A · FAST-LIO on / off |
| --- |
| <a href="results/reference/direction-20261016-v2/fastlio-motion/execution.mp4"><img src="results/reference/direction-20261016-v2/fastlio-motion/execution.gif" width="340" loading="lazy" alt="A · FAST-LIO on / off"></a> |


<a id="h2-stationary"></a>

##### Stationary

| Point compensation | Phase time | A odometry XYZ RMSE / cm | Rotation / ° | N |
| --- | --- | --- | --- | --- |
| Off | 0–7 s | 0.12 | 0.02 | 7 |
| On | 0–7 s | 0.15 | 0.03 | 7 |


<a id="h2-slow"></a>

##### Slow turn

| Point compensation | Phase time | A odometry XYZ RMSE / cm | Rotation / ° | N |
| --- | --- | --- | --- | --- |
| Off | 7–15 s | 1.30 | 0.95 | 26 |
| On | 7–15 s | 0.42 | 0.14 | 26 |


<a id="h2-fast"></a>

##### Fast turn

| Point compensation | Phase time | A odometry XYZ RMSE / cm | Rotation / ° | N |
| --- | --- | --- | --- | --- |
| Off | 15–31 s | 3.18 | 4.35 | 54 |
| On | 15–31 s | 0.79 | 0.26 | 54 |


<a id="h2-translation"></a>

##### Translation

| Point compensation | Phase time | A odometry XYZ RMSE / cm | Rotation / ° | N |
| --- | --- | --- | --- | --- |
| Off | 31–39 s | 5.33 | 3.68 | 26 |
| On | 31–39 s | 1.45 | 0.25 | 26 |


**Analysis:**
<!-- PRACTICE_ANALYSIS:h2-a -->

<!-- /PRACTICE_ANALYSIS:h2-a -->

[↑ Contents](#practice-index)

<a id="h2-b"></a>

#### B · GICP on frozen maps

| A compensation | XYZ RMSE / cm | Rotation / ° | P95 / cm | N |
| --- | --- | --- | --- | --- |
| Off | 14.03 | 3.62 | 19.68 | 601 |
| On | 2.04 | 0.87 | 4.35 | 601 |


[Scores](results/reference/direction-20261016-v2/fastlio-B/score-3d.json)

| Off map | On map |
| --- | --- |
| <a href="results/reference/direction-20261016-v2/fastlio-B/executions/no_deskew.mp4"><img src="results/reference/direction-20261016-v2/fastlio-B/executions/no_deskew.gif" width="340" loading="lazy" alt="Off map"></a> | <a href="results/reference/direction-20261016-v2/fastlio-B/executions/deskew.mp4"><img src="results/reference/direction-20261016-v2/fastlio-B/executions/deskew.gif" width="340" loading="lazy" alt="On map"></a> |


**Analysis:**
<!-- PRACTICE_ANALYSIS:h2-b -->

<!-- /PRACTICE_ANALYSIS:h2-b -->

[↑ Contents](#practice-index)

<a id="experiment-h3"></a>

### H3 · Corridor static references

| Scene | Change | Keep fixed |
| --- | --- | --- |
| Original / landmark corridor | Two asymmetric physical side blocks, 0.24×0.24×0.9 m | SRRG, AMCL, route and initial offset; A/B use 72 beams, 240°, 3.5 m for 50 s, then restore full scans |


<a id="h3-original-a"></a>

#### Original corridor · A

| Method | DA | SA | Eₘ / cm |
| --- | --- | --- | --- |
| Raw | N/A | 82.63% | 16.67 |
| SRRG | N/A | 82.05% | 14.93 |


[Record](results/reference/direction-20261016-v2/2d-A-corridor/record.json)

| A · Raw / SRRG |
| --- |
| <a href="results/reference/direction-20261016-v2/2d-A-corridor/execution.mp4"><img src="results/reference/direction-20261016-v2/2d-A-corridor/execution.gif" width="340" loading="lazy" alt="A · Raw / SRRG"></a> |


**Analysis:**
<!-- PRACTICE_ANALYSIS:h3-original-a -->

<!-- /PRACTICE_ANALYSIS:h3-original-a -->

[↑ Contents](#practice-index)

<a id="h3-original-b"></a>

#### Original corridor · B

| Map | XY RMSE / cm | yaw / ° | P95 / cm | Update coverage | N |
| --- | --- | --- | --- | --- | --- |
| Raw | 113.30 | 1.38 | 128.91 | 88.08% | 591 |
| SRRG | 102.72 | 1.08 | 121.25 | 88.08% | 591 |


[Scores](results/reference/direction-20261016-v2/2d-corridor/time-grid-score.json)

| Raw | SRRG |
| --- | --- |
| <a href="results/reference/direction-20261016-v2/2d-corridor/executions/degraded_raw.mp4"><img src="results/reference/direction-20261016-v2/2d-corridor/executions/degraded_raw.gif" width="340" loading="lazy" alt="Raw"></a> | <a href="results/reference/direction-20261016-v2/2d-corridor/executions/degraded_srrg.mp4"><img src="results/reference/direction-20261016-v2/2d-corridor/executions/degraded_srrg.gif" width="340" loading="lazy" alt="SRRG"></a> |


**Analysis:**
<!-- PRACTICE_ANALYSIS:h3-original-b -->

<!-- /PRACTICE_ANALYSIS:h3-original-b -->

[↑ Contents](#practice-index)

<a id="h3-landmark-a"></a>

#### Landmark corridor · A

| Method | DA | SA | Eₘ / cm |
| --- | --- | --- | --- |
| Raw | N/A | 99.86% | 27.58 |
| SRRG | N/A | 99.01% | 21.06 |


[Record](results/reference/direction-20261016-v2/2d-A-landmark-corridor/record.json)

| A · Raw / SRRG |
| --- |
| <a href="results/reference/direction-20261016-v2/2d-A-landmark-corridor/execution.mp4"><img src="results/reference/direction-20261016-v2/2d-A-landmark-corridor/execution.gif" width="340" loading="lazy" alt="A · Raw / SRRG"></a> |


**Analysis:**
<!-- PRACTICE_ANALYSIS:h3-landmark-a -->

<!-- /PRACTICE_ANALYSIS:h3-landmark-a -->

[↑ Contents](#practice-index)

<a id="h3-landmark-b"></a>

#### Landmark corridor · B

| Map | XY RMSE / cm | yaw / ° | P95 / cm | Update coverage | N |
| --- | --- | --- | --- | --- | --- |
| Raw | 69.61 | 1.52 | 99.27 | 87.93% | 590 |
| SRRG | 54.03 | 1.08 | 94.32 | 87.93% | 590 |


[Scores](results/reference/direction-20261016-v2/2d-landmark-corridor/time-grid-score.json)

| Raw | SRRG |
| --- | --- |
| <a href="results/reference/direction-20261016-v2/2d-landmark-corridor/executions/degraded_raw.mp4"><img src="results/reference/direction-20261016-v2/2d-landmark-corridor/executions/degraded_raw.gif" width="340" loading="lazy" alt="Raw"></a> | <a href="results/reference/direction-20261016-v2/2d-landmark-corridor/executions/degraded_srrg.mp4"><img src="results/reference/direction-20261016-v2/2d-landmark-corridor/executions/degraded_srrg.gif" width="340" loading="lazy" alt="SRRG"></a> |


**Analysis:**
<!-- PRACTICE_ANALYSIS:h3-landmark-b -->

<!-- /PRACTICE_ANALYSIS:h3-landmark-b -->

[↑ Contents](#practice-index)

<a id="h3-scores"></a>

#### Paired scores in the first 50 s

| SRRG map | Along RMSE / cm | Across RMSE / cm | N |
| --- | --- | --- | --- |
| Original | 99.84 | 3.83 | 373 |
| Landmarks | 63.25 | 6.34 | 373 |


[Common-time scores](results/reference/direction-20261016-v2/corridor-comparison.json)

**Analysis:**
<!-- PRACTICE_ANALYSIS:h3-scores -->

<!-- /PRACTICE_ANALYSIS:h3-scores -->

[↑ Contents](#practice-index)

<a id="baseline-3d"></a>

### Existing 3D tests

Original Raw/DUFOMap/BeautyMap and GICP results are retained; see records for scoring windows.

<a id="scene-static-3d"></a>

#### Static · 3D

<!-- HOME_EXPERIMENT_TABLE -->
| Map | DA | SA | XYZ RMSE / cm | Rotation RMSE / ° | P95 / cm | N |
| --- | --- | --- | --- | --- | --- | --- |
| Raw | N/A | 100% | 0.95 | 0.15 | 1.47 | 845 |
| DUFOMap | N/A | 99.999% | 0.99 | 0.16 | 1.47 | 835 |
| BeautyMap | N/A | 83.33% | 1.07 | 0.17 | 1.44 | 917 |
<!-- /HOME_EXPERIMENT_TABLE -->

[Record](results/reference/robot-3d-static/record.json)

| Raw | DUFOMap | BeautyMap |
| --- | --- | --- |
| <a href="results/reference/robot-3d-static/executions/raw.mp4"><img src="results/reference/robot-3d-static/executions/raw.gif" width="340" loading="lazy" alt="Raw"></a> | <a href="results/reference/robot-3d-static/executions/dufomap.mp4"><img src="results/reference/robot-3d-static/executions/dufomap.gif" width="340" loading="lazy" alt="DUFOMap"></a> | <a href="results/reference/robot-3d-static/executions/beautymap.mp4"><img src="results/reference/robot-3d-static/executions/beautymap.gif" width="340" loading="lazy" alt="BeautyMap"></a> |


**Analysis:**
<!-- PRACTICE_ANALYSIS:scene-static-3d -->

<!-- /PRACTICE_ANALYSIS:scene-static-3d -->

[↑ Contents](#practice-index)

<a id="scene-dynamic-3d"></a>

#### Dynamic · 3D

<!-- HOME_EXPERIMENT_TABLE -->
| Map | DA | SA | XYZ RMSE / cm | Rotation RMSE / ° | P95 / cm | N |
| --- | --- | --- | --- | --- | --- | --- |
| Raw | 0% | 100% | 0.98 | 0.17 | 1.96 | 967 |
| DUFOMap | 46.59% | 99.998% | 0.98 | 0.18 | 2.00 | 963 |
| BeautyMap | 74.36% | 81.15% | 1.04 | 0.17 | 1.99 | 1022 |
<!-- /HOME_EXPERIMENT_TABLE -->

[Record](results/reference/robot-3d-dynamic/record.json)

| Raw | DUFOMap | BeautyMap |
| --- | --- | --- |
| <a href="results/reference/robot-3d-dynamic/executions/raw.mp4"><img src="results/reference/robot-3d-dynamic/executions/raw.gif" width="340" loading="lazy" alt="Raw"></a> | <a href="results/reference/robot-3d-dynamic/executions/dufomap.mp4"><img src="results/reference/robot-3d-dynamic/executions/dufomap.gif" width="340" loading="lazy" alt="DUFOMap"></a> | <a href="results/reference/robot-3d-dynamic/executions/beautymap.mp4"><img src="results/reference/robot-3d-dynamic/executions/beautymap.gif" width="340" loading="lazy" alt="BeautyMap"></a> |


**Analysis:**
<!-- PRACTICE_ANALYSIS:scene-dynamic-3d -->

<!-- /PRACTICE_ANALYSIS:scene-dynamic-3d -->

[↑ Contents](#practice-index)

<a id="scene-corridor-3d"></a>

#### Corridor · 3D

<!-- HOME_EXPERIMENT_TABLE -->
| Map | DA | SA | XYZ RMSE / cm | Rotation RMSE / ° | P95 / cm | N |
| --- | --- | --- | --- | --- | --- | --- |
| Raw | N/A | 100% | 474.38 | 0.53 | 828.94 | 530 |
| DUFOMap | N/A | 100% | 497.05 | 0.48 | 814.15 | 599 |
| BeautyMap | N/A | 99.9% | 592.00 | 49.16 | 917.05 | 655 |
<!-- /HOME_EXPERIMENT_TABLE -->

[Record](results/reference/robot-3d-corridor/record.json)

| Raw | DUFOMap | BeautyMap |
| --- | --- | --- |
| <a href="results/reference/robot-3d-corridor/executions/raw.mp4"><img src="results/reference/robot-3d-corridor/executions/raw.gif" width="340" loading="lazy" alt="Raw"></a> | <a href="results/reference/robot-3d-corridor/executions/dufomap.mp4"><img src="results/reference/robot-3d-corridor/executions/dufomap.gif" width="340" loading="lazy" alt="DUFOMap"></a> | <a href="results/reference/robot-3d-corridor/executions/beautymap.mp4"><img src="results/reference/robot-3d-corridor/executions/beautymap.gif" width="340" loading="lazy" alt="BeautyMap"></a> |


**Analysis:**
<!-- PRACTICE_ANALYSIS:scene-corridor-3d -->

<!-- /PRACTICE_ANALYSIS:scene-corridor-3d -->

[↑ Contents](#practice-index)

<a id="scene-change-3d"></a>

#### Changed world · 3D

<!-- HOME_EXPERIMENT_TABLE -->
| Map | DA | SA | XYZ RMSE / cm | Rotation RMSE / ° | P95 / cm | N |
| --- | --- | --- | --- | --- | --- | --- |
| Raw | N/A | 100% | 0.93 | 0.17 | 1.45 | 859 |
| DUFOMap | N/A | 99.999% | 1.01 | 0.19 | 1.45 | 860 |
| BeautyMap | N/A | 83.33% | 1.04 | 0.17 | 1.46 | 945 |
<!-- /HOME_EXPERIMENT_TABLE -->

[Record](results/reference/robot-3d-large-change/record.json)

| Raw | DUFOMap | BeautyMap |
| --- | --- | --- |
| <a href="results/reference/robot-3d-large-change/executions/raw.mp4"><img src="results/reference/robot-3d-large-change/executions/raw.gif" width="340" loading="lazy" alt="Raw"></a> | <a href="results/reference/robot-3d-large-change/executions/dufomap.mp4"><img src="results/reference/robot-3d-large-change/executions/dufomap.gif" width="340" loading="lazy" alt="DUFOMap"></a> | <a href="results/reference/robot-3d-large-change/executions/beautymap.mp4"><img src="results/reference/robot-3d-large-change/executions/beautymap.gif" width="340" loading="lazy" alt="BeautyMap"></a> |


**Analysis:**
<!-- PRACTICE_ANALYSIS:scene-change-3d -->

<!-- /PRACTICE_ANALYSIS:scene-change-3d -->

[↑ Contents](#practice-index)

<a id="practice-appendix"></a>

### Supplementary experiments

<a id="supp-srrg"></a>

#### SRRG · Persistent change

| Method | DA | SA | New structure coverage | Separate B |
| --- | --- | --- | --- | --- |
| Raw | N/A | 100.00% | 100.00% | Not tested |
| SRRG | N/A | 99.71% | 98.90% | Not tested |


[Record](results/reference/srrg-2d-large-change/record.json)

| SRRG changed-world A |
| --- |
| <a href="results/reference/srrg-2d-large-change/execution.mp4"><img src="results/reference/srrg-2d-large-change/execution.gif" width="340" loading="lazy" alt="SRRG changed-world A"></a> |


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
| NDT initial | 34.43 | 0.15 | [Record](results/reference/robot-ndt-static-initial/record.json) |
| NDT | 0.93 | 0.17 | [Record](results/reference/robot-ndt-static/record.json) |
| GICP | 1.09 | 0.16 | [Record](results/reference/robot-gicp-static/record.json) |


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

## Branches

| Branch | Role |
| --- | --- |
| main | Curated submission: dynamic-environment localization, scoped mapping/localization reproductions and a candidate recovery experiment. |
| [reproduce/author-originals](https://github.com/p20030920p/SLAM_Learning/tree/reproduce/author-originals) | Original pipelines, paper-table scoring and recordings. |
| [notes/personal-study-guide-20261008](https://github.com/p20030920p/SLAM_Learning/tree/notes/personal-study-guide-20261008) | Personal study notes and hardware trials under `src/physical/`, including operations and failures. |

[AI use](docs/guides/DISCLOSURE.md) · [Sources/licenses](docs/guides/ATTRIBUTION.md) · [Citation](docs/CITATION.cff) · [License](src/LICENSE)
