<div align="center">

# SLAM Learning

**Robust localization and SLAM in dynamic environments**

Robust localization and SLAM in dynamic environments · Localization self-recovery

[![CPU reproducibility](https://github.com/p20030920p/slam_learning_updated/actions/workflows/ci.yml/badge.svg)](https://github.com/p20030920p/slam_learning_updated/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.10-3776AB)](src/pyproject.toml)

English | [中文](docs/HOME.zh-CN.md)

[Open question](#open-question) · [Direction](#direction-analysis) · [Related works](#related-works) · [Hypothesis](#hypothesis)

[Results](#reproduction-results) · [Evidence](#evidence) · [Hypothesis](#hypothesis) · [Branches](#branches)

</div>

## Open question

**What strategies enable localization self-recovery under degradation and substantial environmental change?** Analyze failure mechanisms, recovery targets and boundaries before choosing a strategy. Deliver author-code reproductions and progressively harder point-cloud mapping/localization tests on the Sim2Real-AlgoBench robot. [Question analysis](docs/self-recovery/DESIGN.md) · [Robot test protocol](docs/testing/PROTOCOL.md) · [Chinese talk](docs/self-recovery/TALK.zh-CN.md) · [Status](docs/self-recovery/STATUS.zh-CN.md).

## Direction analysis

**SLAM (Simultaneous Localization and Mapping)** estimates motion while building a map. The direction includes dynamic-environment mapping, localization and SLAM; self-recovery is an open question within it.

![SLAM pose-map estimation and recovery: physical chassis and sensors, Gazebo scans, provided-pose map and corridor](docs/assets/slam-recovery-flow.en.v2.png)

The open question concerns recovery of pose estimation after failure, influenced by observation quality and map validity. A narrower candidate is: **after geometric observations become informative again, how can fixed-map localization avoid false convergence and confirm recovery?** [Editable English diagram](docs/assets/slam-recovery-flow.en.v2.pptx) · [Image sources](docs/assets/direction/sources.json). Hardware photographs document the existing chassis/sensors; physical tests remain pending.

| Deliverable | Content |
| --- | --- |
| Native reproduction | Author source/data/protocol, each paper's metrics and actual reproduced scope |
| Robot tests | Sim2Real-AlgoBench omnidirectional chassis, native 2D and independent 3D LiDAR profiles, progressively harder mapping/localization/recovery |
| Question analysis | Separate weak constraints from map mismatch; narrow using reproducible failures, keeping methods open |

Semantic mapping and earlier projections remain in the [original repository](https://github.com/p20030920p/SLAM_Learning).

## Related works

**Author-code live execution with RViz + Terminal.** The display observes current computation; points/particles are thinned only for visualization. Observer overhead is excluded from paper runtime comparisons.

**Paper scenarios and observed effects — read before the videos.** Paper datasets describe the evaluated scope, rather than a guarantee for every dynamic environment. The scores here belong to the latest author-code live runs; historical paper-table reproductions are listed separately below. SA/DA assess map-point classification; pose RMSE assesses localization.

| Method | Original paper datasets and task | Effective observation in our experiment | Failure, missing benefit or untested scope |
| --- | --- | --- | --- |
| DUFOMap | KITTI 00/01 (town/highway), Argoverse 2 (city), semi-indoor moving people; qualitative survey/train-station/two-floor scenes. 3D dynamic-point removal with supplied poses. [Paper §IV–V](https://arxiv.org/html/2403.01449v1#S4) | KITTI-00, 141 scans: SA 97.98%, DA 98.70%; dynamic traces are removed while most static geometry remains. [Live record](results/reference/desktop-live-dufomap/record.json) | Neither classification score reaches 100%. Pose estimation and recovery are outside this method; a clean map alone does not demonstrate better localization. |
| BeautyMap | KITTI 00/01/05; KITTI 02 cell-size study; semi-indoor data. Offline cleaning of an existing 3D map with supplied poses. [Paper §IV](https://arxiv.org/html/2405.07283v1#S4) | Latest KITTI-00, 141 scans: SA 96.95%, DA 98.34%; dynamic traces are removed. Historical KITTI-02, 91 scans, separately matches nine Table III accuracy entries. [Live record](results/reference/desktop-live-beautymap/record.json) | Static-point loss and dynamic remnants remain. Static-structure restoration is not robot-pose recovery. This is not an online SLAM or long-term recovery test. |
| IR-MCL | Bonn IPBLab offices/corridors/kitchen: five global-localization sequences. Freiburg 079, Intel Lab and MIT CSAIL test scan rendering, not global localization. [Paper §IV](https://ar5iv.labs.arxiv.org/html/2210.03113#S4) | Released IPBLab Seq 1: 1543 processed / 1354 scored poses, RMSE 5.31 cm / 1.07°, close to the paper's Seq-1 5.13 cm / 1.05°. [Live record](results/reference/desktop-live-ir-mcl/record.json) | The other four localization sequences are not reproduced. Severe observation loss, obsolete maps and kidnapping recovery are untested here; Gazebo deployment is not completed. |
| AdaM-MCL | 20 synthetic 43×43 m maps (18 training, two testing), UPO Alcazar and Bicocca indoor data; unknown obstacles, removed structure, global localization and kidnapping. [Paper §V](https://arxiv.org/html/2009.00211#S5) | The original data-generation/training/filtering workflow executes on an authored 128-cell plan and a 2432-step checkpoint. Latest run: 123 updates, RMSE 32.23 cells. [Live record](results/reference/desktop-adam-mcl/record.json) | Recovery is not demonstrated. Historical ten repeats: mean per-trial RMSE 34.82 cells; sustained convergence 0/10 in both global and kidnapping phases. Paper data/weights are unavailable; these are not metre-scale paper results. [Corrected evidence](results/reference/adam-mcl/ERRATUM.md) |

Each paper card below lists the original datasets, experimental assumptions and failure hypotheses. Hypotheses are distinguished from causes demonstrated in our runs.

### DUFOMap — dynamic-point removal during map integration

**Input:** successive 3D LiDAR scans and provided sensor poses. **Process:** observed free space supplies evidence that earlier occupied points are transient; an octree accumulates this evidence with margins for pose uncertainty. **Output:** a map with dynamic remnants removed. It does not estimate the robot pose. [Paper and reproduced scope](docs/papers/dufomap.md).

In the live video, gray points are retained, red points are removed, and cyan points are the current scan. Watch how decisions change as later scans supply evidence. KITTI-00, 141 scans; SA 97.98% / DA 98.70%. SA measures retained static points and DA measures removed dynamic points; neither is localization error.

**Live execution**

![DUFOMap author-code live execution](results/reference/desktop-live-dufomap/execution.gif)

[Live MP4](results/reference/desktop-live-dufomap/execution.mp4) · [record](results/reference/desktop-live-dufomap/record.json)

### BeautyMap — clean an existing point-cloud map

**Input:** the full accumulated 3D map, scans and provided poses. **Process:** the native occupancy representation detects inconsistent occupied structure, followed by the authors' static-structure recovery stage. **Output:** a cleaned reference map. This offline map cleaner is shown while it computes; the input map already exists at the start. [Paper and reproduced scope](docs/papers/beautymap.md).

Gray/red show retained/removed points. Watch the cumulative removal decisions, rather than interpreting the complete initial map as online SLAM. KITTI-00, 141 scans; SA 96.95% / DA 98.34%. Cleaner maps may help downstream localization, but that requires a separate test.

**Live execution**

![BeautyMap author-code live execution](results/reference/desktop-live-beautymap/execution.gif)

[Live MP4](results/reference/desktop-live-beautymap/execution.mp4) · [record](results/reference/desktop-live-beautymap/record.json)

### IR-MCL — localize with a neural observation model

**Input:** a pretrained neural occupancy field, measured 2D scans and motion input. **Process:** each particle represents a possible robot pose; the field renders a predicted scan at that pose, scan agreement changes particle weights, and resampling concentrates the belief. **Output:** an estimated pose and particle distribution. [Paper, original code and protocol](docs/papers/ir-mcl.md).

In RViz, the map supplies context, yellow particles show pose hypotheses, blue is the displayed estimate and green is the reference trajectory. Watch particle concentration and agreement with the reference. The displayed weighted particle mean is an observer; scoring uses the native saved estimate. Bonn IPBLab Seq 1: 1543 processed / 1354 scored poses, fresh RMSE 5.31 cm / 1.07°. This author-data run is separate from deployment into Gazebo.

**Live execution**

![IR-MCL author-code live execution](results/reference/desktop-live-ir-mcl/execution.gif)

[Live MP4](results/reference/desktop-live-ir-mcl/execution.mp4) · [record](results/reference/desktop-live-ir-mcl/record.json)

### AdaM-MCL — combine learned proposals and particle tracking

**Input:** a map, laser observation, motion input and trained proposal model. **Process:** the learned model proposes candidate poses; the adaptive mixture combines proposals with conventional particle tracking. **Output:** pose belief, including hypotheses after a kidnapping event. [Paper and limits](docs/papers/adam-mcl.md).

Our run uses an authored 128-cell map and a 2432-step checkpoint: 123 filter updates, RMSE 32.23 cells. The released paper dataset/checkpoint was unavailable. This verifies a limited original-code workflow; it neither reproduces the paper's metre-scale scores nor demonstrates successful recovery. [Score correction](results/reference/adam-mcl/ERRATUM.md).

**Live execution**

![AdaM-MCL author-code live execution](results/reference/desktop-adam-mcl/execution.gif)

[Live MP4](results/reference/desktop-adam-mcl/execution.mp4) · [record](results/reference/desktop-adam-mcl/record.json)

**Measured result replay**

![AdaM-MCL saved result replay](results/reference/desktop-adam-mcl/result.gif)

[Result MP4](results/reference/desktop-adam-mcl/result.mp4)

## Hypothesis

Test whether cleaner maps also improve recovery, better nominal observation models expand recovery range, and remaining stable structure limits recovery against obsolete maps. Complete native reproduction and progressive tests before choosing an intervention. [Analysis and counterexamples](docs/self-recovery/DESIGN.md).

## Reproduction results

| Work | Data | Result |
| --- | --- | --- |
| [DUFOMap](https://github.com/p20030920p/SLAM_Learning/blob/535a2780af7ca7eb3aa02f722e1340fe90bc2dcf/docs/DUFOMAP_TABLE4.md) | KITTI-00, 141 scans | Table IV accuracy matched |
| [BeautyMap](https://github.com/p20030920p/SLAM_Learning/blob/535a2780af7ca7eb3aa02f722e1340fe90bc2dcf/docs/KITTI_PAPER_PROTOCOL.md) | Historical KITTI-02, 91 scans | Table III accuracy matched |
| [IR-MCL](docs/papers/ir-mcl.md) | Bonn IPBLab, released localization sequence, 1543 scans | Location RMSE 5.32 cm against the paper's 5.13 cm |
| [AdaM-MCL](docs/papers/adam-mcl.md) | Authored 128-cell plan, one held-out scene, 123 updates × 10 repeats | Released pipeline executed; no paper value compared |

## Evidence

Values below come from the papers linked by the original repositories and our recorded author-code runs. Each table concerns one method; no cross-method ranking is implied.

**Shared metrics.** DUFOMap and BeautyMap use the same SA/DA definitions. $S,D$ count ground-truth static/dynamic points; $S_k,D_r$ count correctly kept static and removed dynamic points. AA (DUFOMap) is the geometric mean; HA (BeautyMap) is the harmonic mean. [DUFOMap definition](https://arxiv.org/html/2403.01449v1#S4.SS2) · [BeautyMap definition](https://arxiv.org/html/2405.07283v1#S4).

$$
\begin{aligned}
\mathrm{SA} &= 100\frac{S_k}{S}, &
\mathrm{DA} &= 100\frac{D_r}{D},\\
\mathrm{AA} &= \sqrt{\mathrm{SA}\,\mathrm{DA}}, &
\mathrm{HA} &= \frac{2\,\mathrm{SA}\,\mathrm{DA}}{\mathrm{SA}+\mathrm{DA}}.
\end{aligned}
$$

### DUFOMap

KITTI-00, 141 released scans; full setting: voxel 0.1 m, d_s=0.2 m, d_p=1. [Original repository](https://github.com/KTH-RPL/dufomap/tree/9e239ddd5995136e14f5212f33382a6ebc59e518) · [Paper Table IV](https://arxiv.org/html/2403.01449v1#S5.T4) · [Our results](https://github.com/p20030920p/SLAM_Learning/blob/535a2780af7ca7eb3aa02f722e1340fe90bc2dcf/docs/DUFOMAP_TABLE4.md).

| Metric | Paper % | Reproduced % |
| --- | ---: | ---: |
| SA | 97.96 | 97.9635 |
| DA | 98.72 | 98.7196 |
| AA | 98.34 | 98.3408 |

All three full-setting values match the paper at two decimals. Across all five Table IV settings, all 15 accuracy entries match; runtime and online experiments are outside this comparison.

### BeautyMap

Historical KITTI-02, frames 860–950, 91 scans; XY=1 m, Z=0.5 m, range=40 m. [Original repository](https://github.com/MKJia/BeautyMap/tree/98bce4a97db96ddd0d5342e31425c7679f58ba2e) · [Paper Table III](https://arxiv.org/html/2405.07283v1#S4.T3) · [Our results](https://github.com/p20030920p/SLAM_Learning/blob/535a2780af7ca7eb3aa02f722e1340fe90bc2dcf/docs/KITTI_PAPER_PROTOCOL.md).

| Metric | Paper % | Reproduced % |
| --- | ---: | ---: |
| SA | 83.40 | 83.3978 |
| DA | 82.41 | 82.4092 |
| HA | 82.90 | 82.9006 |

All three values match at two decimals. All nine accuracy entries across XY=0.5/1/2 m match. This uses historical preprocessing/GT and the author's HA scorer; the exact paper method commit remains unidentified. Other sequences and runtime are outside this comparison.

### IR-MCL

Bonn IPBLab, the single released localization sequence; scored window 1354 of 1543 scans, because the repository's own evaluation drops the first 20 s. [Original repository](https://github.com/PRBonn/ir-mcl/tree/aab8c91b37e59f94442d8eddfa2f920ab1ecc4c5) · [Paper IV-B localization table](https://arxiv.org/html/2210.03113v2#S4.SS2) · [Our run](results/reference/ir-mcl/runs/ir-mcl-wsl/record.json).

| Metric | Paper, Seq 1 | Reproduced |
| --- | ---: | ---: |
| Location RMSE (cm) | 5.13 | 5.32 |
| Yaw RMSE (deg) | 1.05 | 1.07 |
| Location < 5 cm (%) | 63.15 | 61.74 |
| Location < 10 cm (%) | 97.27 | 96.01 |
| Location < 20 cm (%) | 100.00 | 100.00 |
| Yaw < 0.5° (%) | 47.12 | 47.64 |
| Yaw < 1° (%) | 74.59 | 75.85 |
| Yaw < 2° (%) | 94.24 | 93.57 |

The paper's Seq-1 percentages are exact integer counts over 1354 samples, the same window this repository's evaluation produces, so the rows are directly comparable. The C++ motion model seeds its generator from `std::random_device`, so repeated runs differ slightly; a second full run gave 5.28 cm. The upstream README's supplementary 6.62 cm / 1.11° aggregates the whole self-recorded dataset, not Seq 1, and is not used here.

### AdaM-MCL

Authored 128-cell indoor plan, one held-out scene, 123 filter updates, 200 particles and $T_{\mathrm{cut}}=0.6$ — the particle number and trust threshold of the paper's synthetic setting. [Original repository](https://github.com/Runjian-Chen/AdaM_MCL/tree/e8aedd2bae03816aabd5300e5ca2fe181b39d830) · [Paper Table II](https://arxiv.org/html/2009.00211v3) · [Our run](results/reference/adam-mcl/runs/adam-mcl-wsl/record.json).

| Metric | Paper Table II | This run |
| --- | ---: | ---: |
| Global localization $E_{pos}$ | 0.153 m | not compared |
| Kidnapping $E_{pos}$ | 0.128 m | not compared |

**No numeric comparison is made.** The paper's 20 simulation maps are 43 m × 43 m with six evaluation sequences and released checkpoints, all of them external downloads; this run authors its own plans and trains for 2 432 optimizer steps against the authors' 2 880 000, so cells are not metres. Measured here, in cells: mean per-trial position RMSE 34.82 over 10 repeats, mean final error 47.71, 0.43 s per filter update, and 0 of 10 repeats holding the paper's convergence rule rescaled to this plan. [Score correction](results/reference/adam-mcl/ERRATUM.md).

## Branches

| Branch | Role |
| --- | --- |
| main | Curated submission: dynamic-environment localization, scoped mapping/localization reproductions and a candidate recovery experiment. |
| [reproduce/author-originals](https://github.com/p20030920p/SLAM_Learning/tree/reproduce/author-originals) | Original pipelines, paper-table scoring and recordings. |
| [notes/personal-study-guide-20261008](https://github.com/p20030920p/SLAM_Learning/tree/notes/personal-study-guide-20261008) | Personal study notes and hardware trials under `src/physical/`, including operations and failures. |


[AI use](docs/guides/DISCLOSURE.md) · [Sources/licenses](docs/guides/ATTRIBUTION.md) · [Citation](docs/CITATION.cff) · [License](src/LICENSE)
## Practice

[Keyboard demos](demo/README.md) · [Video gallery](demo/gallery.html) · [Code Notebook](notebooks/presentation/SLAM_实验逐步展示.ipynb).

**Observed robot-test effects — read before the videos.** These are Gazebo experiments. Raw / DUFOMap / BeautyMap are three map choices with the same AMCL localizer. The rows below summarize the latest displayed runs, including initialization; each condition has one trial unless noted. Small numerical differences do not establish a method ranking.

| Scene / method | Effective observation | Failure, missing benefit or untested scope | Evidence |
| --- | --- | --- | --- |
| Static · three maps + AMCL | Localization tracks this route; XY RMSE Raw / DUFOMap / BeautyMap = 7.28 / 7.28 / 6.89 cm, 290 updates each. | DUFOMap shows no improvement over Raw in this run; the small BeautyMap difference is not confirmed across repeats. No loss was induced, so recovery was not tested. | [record](results/reference/robot-live-static/record.json) |
| Three moving boxes · three maps + AMCL | Localization continues with moving obstacles; XY RMSE = 7.41 / 7.35 / 7.14 cm, 288 updates each. | The observed reductions against Raw are only 0.06 / 0.27 cm for DUFOMap / BeautyMap. One run does not establish a consistent cleaning benefit or recovery improvement. | [record](results/reference/robot-live-dynamic/record.json) |
| Persistent change · old maps + AMCL | Localization remains usable on this route; XY RMSE = 6.84 / 6.84 / 6.39 cm, 290 updates each. | This route did not induce loss. It cannot demonstrate recovery from major map mismatch, and DUFOMap has no observed RMSE benefit over Raw here. | [record](results/reference/robot-live-large-change/record.json) |
| Corridor · limited then restored scans + AMCL | After full scans return at simulation time 66.2 s, the limited-scan group starts sustained convergence after 13.3 s, confirmed over 5 s with ≥8 updates, position <0.1 m and yaw <5°. The full-scan control starts it 6.6 s after the same reference event. | Full-run XY RMSE remains 72.53 cm (limited) / 71.60 cm (full), 508 updates each, including the 1 m initial offset. All three projected maps are identical; cleaning methods cannot be distinguished. This starts from an offset belief rather than loss during otherwise successful tracking. | [record](results/reference/robot-corridor-v2/record.json) |
| Static · native NDT_OMP | Latest short 3D fixed-map run: XY RMSE 0.927 cm / yaw 0.171°, 402 updates. | The first trial gave 34.43 cm over 399 updates with the same estimator parameters; the cause is unresolved. Dynamic, degradation and recovery trials remain pending. | [latest](results/reference/robot-ndt-static/record.json) · [first trial](results/reference/robot-ndt-static-initial/record.json) |
| Static · native GICP | Short 3D fixed-map run: XY RMSE 1.091 cm / yaw 0.160°, 397 updates. | Only approximately 35 simulation seconds of static deployment; dynamics, degradation and recovery remain untested. Its 3D input differs from AMCL's 2D input, so their scores do not establish a ranking. | [record](results/reference/robot-gicp-static/record.json) |
| Supplementary mapping scenes | Native slam_toolbox generates a 2D map; the independent 3D branch collects scans and maps them with provided sensor poses. | The 3D branch does not estimate its own pose and is not complete 3D SLAM. Physical-robot accuracy and recovery remain pending. | [static mapping](results/reference/robot-supp-static/record.json) · [corridor mapping](results/reference/robot-corridor-v2-mapping/record.json) |

## Measured result calculation

Each saved native pose update is paired with independent Gazebo robot truth within **0.05 simulation seconds**. Both use the same map/world frame; no spatial fitting is applied. The scored files include initialization and retain rejected timestamp counts.

$$e_i=\sqrt{(\hat x_i-x_i)^2+(\hat y_i-y_i)^2},\quad \mathrm{RMSE}_{xy}=\sqrt{\frac1N\sum_{i=1}^N e_i^2}.$$

Yaw differences are wrapped to $[-\pi,\pi]$ before RMS and converted to degrees. Metres × 100 gives centimetres. **Live execution** records real computation in wall time; **Measured result replay** draws saved estimates and truth in simulation time, with no new inference. The replay curve is instantaneous error, while its RMSE label uses the full scored CSV. [CSV, window rules and recovery criterion](docs/testing/LIVE.md#how-errors-are-calculated) · [Executable score code](src/scripts/presentation/observe_session.py).

## Native 3D localization trials

The following short static trials use live 3D points and a fixed Raw 3D map. No IMU or deskew. Scores cover XY/yaw and initialization; sensor input and duration differ from the AMCL trials. [Libraries and scope](docs/testing/LOCALIZERS.md).

### Pure static — NDT_OMP

**Live execution**

![NDT_OMP native 3D localization](results/reference/robot-ndt-static/execution.gif)

[Live MP4](results/reference/robot-ndt-static/execution.mp4) · [record](results/reference/robot-ndt-static/record.json)

**Measured result replay**

![NDT_OMP saved pose result](results/reference/robot-ndt-static/result.gif)

[Result MP4](results/reference/robot-ndt-static/result.mp4) · XY RMSE **0.93 cm** · yaw **0.17°** · 402 updates.

### Pure static — GICP

**Live execution**

![GICP native 3D localization](results/reference/robot-gicp-static/execution.gif)

[Live MP4](results/reference/robot-gicp-static/execution.mp4) · [record](results/reference/robot-gicp-static/record.json)

**Measured result replay**

![GICP saved pose result](results/reference/robot-gicp-static/result.gif)

[Result MP4](results/reference/robot-gicp-static/result.mp4) · XY RMSE **1.09 cm** · yaw **0.16°** · 397 updates.

NDT also produced 34.43 cm in its first trial with the same estimator parameters; that run is retained. The cause of the variation is not yet established, so the latest score is not a robustness claim. [Initial trial](results/reference/robot-ndt-static-initial/record.json).

## Static and dynamic localization recordings

**Fresh live tests on this Windows computer, 2026-10-14.** Each method has its own actual RViz window, map topic, native AMCL pose/particles and isolated display TF. Each GIF records Gazebo + that method’s RViz + Terminal, during the same live scene input.

**Raw / DUFOMap / BeautyMap are map-processing choices; the live localizer is AMCL.** Mapping uses provided poses and common 2D projection; this is a scoped 3D-map-to-2D-localization adaptation. Results below come from these new runs, including initialization; one trial per condition.

[Scoring and controls](docs/testing/LIVE.md) · [Other localization libraries and deployment](docs/testing/LOCALIZERS.md) · [Recording names](demo/recording-index.json) · [One-click method demos](demo/README.md#逐方法独立-rviz-现场对照)

### Pure static

Small initial offset; no loss on this route.

#### Raw map + AMCL

**Live execution — Raw RViz**

![Pure static: actual Raw RViz live execution](results/reference/robot-live-static/executions/raw.gif)

[Live MP4](results/reference/robot-live-static/executions/raw.mp4) · [RViz config](results/reference/robot-live-static/view-raw.rviz) · [record](results/reference/robot-live-static/record.json)

**Measured result replay — Raw**

![Pure static: Raw measured replay from this new run](results/reference/robot-live-static/methods/raw/result.gif)

[Result MP4](results/reference/robot-live-static/methods/raw/result.mp4) · [case record](results/reference/robot-live-static/methods/raw/record.json) · RMSE **7.28 cm** · 290 native updates.

#### DUFOMap map + AMCL

**Live execution — DUFOMap RViz**

![Pure static: actual DUFOMap RViz live execution](results/reference/robot-live-static/executions/dufomap.gif)

[Live MP4](results/reference/robot-live-static/executions/dufomap.mp4) · [RViz config](results/reference/robot-live-static/view-dufomap.rviz) · [record](results/reference/robot-live-static/record.json)

**Measured result replay — DUFOMap**

![Pure static: DUFOMap measured replay from this new run](results/reference/robot-live-static/methods/dufomap/result.gif)

[Result MP4](results/reference/robot-live-static/methods/dufomap/result.mp4) · [case record](results/reference/robot-live-static/methods/dufomap/record.json) · RMSE **7.28 cm** · 290 native updates.

#### BeautyMap map + AMCL

**Live execution — BeautyMap RViz**

![Pure static: actual BeautyMap RViz live execution](results/reference/robot-live-static/executions/beautymap.gif)

[Live MP4](results/reference/robot-live-static/executions/beautymap.mp4) · [RViz config](results/reference/robot-live-static/view-beautymap.rviz) · [record](results/reference/robot-live-static/record.json)

**Measured result replay — BeautyMap**

![Pure static: BeautyMap measured replay from this new run](results/reference/robot-live-static/methods/beautymap/result.gif)

[Result MP4](results/reference/robot-live-static/methods/beautymap/result.mp4) · [case record](results/reference/robot-live-static/methods/beautymap/record.json) · RMSE **6.89 cm** · 290 native updates.

### Moving obstacles

Three moving boxes. Three dynamic-map localizers are shown live; three static-map controls run on the same input and are listed in the scoring protocol.

#### Raw map + AMCL

**Live execution — Raw RViz**

![Moving obstacles: actual Raw RViz live execution](results/reference/robot-live-dynamic/executions/raw.gif)

[Live MP4](results/reference/robot-live-dynamic/executions/raw.mp4) · [RViz config](results/reference/robot-live-dynamic/view-raw.rviz) · [record](results/reference/robot-live-dynamic/record.json)

**Measured result replay — Raw**

![Moving obstacles: Raw measured replay from this new run](results/reference/robot-live-dynamic/methods/raw/result.gif)

[Result MP4](results/reference/robot-live-dynamic/methods/raw/result.mp4) · [case record](results/reference/robot-live-dynamic/methods/raw/record.json) · RMSE **7.41 cm** · 288 native updates.

#### DUFOMap map + AMCL

**Live execution — DUFOMap RViz**

![Moving obstacles: actual DUFOMap RViz live execution](results/reference/robot-live-dynamic/executions/dufomap.gif)

[Live MP4](results/reference/robot-live-dynamic/executions/dufomap.mp4) · [RViz config](results/reference/robot-live-dynamic/view-dufomap.rviz) · [record](results/reference/robot-live-dynamic/record.json)

**Measured result replay — DUFOMap**

![Moving obstacles: DUFOMap measured replay from this new run](results/reference/robot-live-dynamic/methods/dufomap/result.gif)

[Result MP4](results/reference/robot-live-dynamic/methods/dufomap/result.mp4) · [case record](results/reference/robot-live-dynamic/methods/dufomap/record.json) · RMSE **7.35 cm** · 288 native updates.

#### BeautyMap map + AMCL

**Live execution — BeautyMap RViz**

![Moving obstacles: actual BeautyMap RViz live execution](results/reference/robot-live-dynamic/executions/beautymap.gif)

[Live MP4](results/reference/robot-live-dynamic/executions/beautymap.mp4) · [RViz config](results/reference/robot-live-dynamic/view-beautymap.rviz) · [record](results/reference/robot-live-dynamic/record.json)

**Measured result replay — BeautyMap**

![Moving obstacles: BeautyMap measured replay from this new run](results/reference/robot-live-dynamic/methods/beautymap/result.gif)

[Result MP4](results/reference/robot-live-dynamic/methods/beautymap/result.mp4) · [case record](results/reference/robot-live-dynamic/methods/beautymap/record.json) · RMSE **7.14 cm** · 288 native updates.

### Persistent change

Old static maps in a changed world; this route still did not induce loss.

#### Raw map + AMCL

**Live execution — Raw RViz**

![Persistent change: actual Raw RViz live execution](results/reference/robot-live-large-change/executions/raw.gif)

[Live MP4](results/reference/robot-live-large-change/executions/raw.mp4) · [RViz config](results/reference/robot-live-large-change/view-raw.rviz) · [record](results/reference/robot-live-large-change/record.json)

**Measured result replay — Raw**

![Persistent change: Raw measured replay from this new run](results/reference/robot-live-large-change/methods/raw/result.gif)

[Result MP4](results/reference/robot-live-large-change/methods/raw/result.mp4) · [case record](results/reference/robot-live-large-change/methods/raw/record.json) · RMSE **6.84 cm** · 290 native updates.

#### DUFOMap map + AMCL

**Live execution — DUFOMap RViz**

![Persistent change: actual DUFOMap RViz live execution](results/reference/robot-live-large-change/executions/dufomap.gif)

[Live MP4](results/reference/robot-live-large-change/executions/dufomap.mp4) · [RViz config](results/reference/robot-live-large-change/view-dufomap.rviz) · [record](results/reference/robot-live-large-change/record.json)

**Measured result replay — DUFOMap**

![Persistent change: DUFOMap measured replay from this new run](results/reference/robot-live-large-change/methods/dufomap/result.gif)

[Result MP4](results/reference/robot-live-large-change/methods/dufomap/result.mp4) · [case record](results/reference/robot-live-large-change/methods/dufomap/record.json) · RMSE **6.84 cm** · 290 native updates.

#### BeautyMap map + AMCL

**Live execution — BeautyMap RViz**

![Persistent change: actual BeautyMap RViz live execution](results/reference/robot-live-large-change/executions/beautymap.gif)

[Live MP4](results/reference/robot-live-large-change/executions/beautymap.mp4) · [RViz config](results/reference/robot-live-large-change/view-beautymap.rviz) · [record](results/reference/robot-live-large-change/record.json)

**Measured result replay — BeautyMap**

![Persistent change: BeautyMap measured replay from this new run](results/reference/robot-live-large-change/methods/beautymap/result.gif)

[Result MP4](results/reference/robot-live-large-change/methods/beautymap/result.mp4) · [case record](results/reference/robot-live-large-change/methods/beautymap/record.json) · RMSE **6.39 cm** · 290 native updates.

### Corridor degradation

1 m initial X offset; 72 beams / 240° / 3.5 m for 50 simulation seconds, then full scans. This trial starts sustained convergence 13.3 s after restoration, verified over 5 s. All three corridor occupancy maps are identical.

#### Raw map + AMCL

**Live execution — Raw RViz**

![Corridor degradation: actual Raw RViz live execution](results/reference/robot-corridor-v2/executions/degraded_raw.gif)

[Live MP4](results/reference/robot-corridor-v2/executions/degraded_raw.mp4) · [RViz config](results/reference/robot-corridor-v2/view-degraded_raw.rviz) · [record](results/reference/robot-corridor-v2/record.json)

**Measured result replay — Raw**

![Corridor degradation: Raw measured replay from this new run](results/reference/robot-corridor-v2/methods/degraded_raw/result.gif)

[Result MP4](results/reference/robot-corridor-v2/methods/degraded_raw/result.mp4) · [case record](results/reference/robot-corridor-v2/methods/degraded_raw/record.json) · RMSE **72.53 cm** · 508 native updates.

#### DUFOMap map + AMCL

**Live execution — DUFOMap RViz**

![Corridor degradation: actual DUFOMap RViz live execution](results/reference/robot-corridor-v2/executions/degraded_dufomap.gif)

[Live MP4](results/reference/robot-corridor-v2/executions/degraded_dufomap.mp4) · [RViz config](results/reference/robot-corridor-v2/view-degraded_dufomap.rviz) · [record](results/reference/robot-corridor-v2/record.json)

**Measured result replay — DUFOMap**

![Corridor degradation: DUFOMap measured replay from this new run](results/reference/robot-corridor-v2/methods/degraded_dufomap/result.gif)

[Result MP4](results/reference/robot-corridor-v2/methods/degraded_dufomap/result.mp4) · [case record](results/reference/robot-corridor-v2/methods/degraded_dufomap/record.json) · RMSE **72.53 cm** · 508 native updates.

#### BeautyMap map + AMCL

**Live execution — BeautyMap RViz**

![Corridor degradation: actual BeautyMap RViz live execution](results/reference/robot-corridor-v2/executions/degraded_beautymap.gif)

[Live MP4](results/reference/robot-corridor-v2/executions/degraded_beautymap.mp4) · [RViz config](results/reference/robot-corridor-v2/view-degraded_beautymap.rviz) · [record](results/reference/robot-corridor-v2/record.json)

**Measured result replay — BeautyMap**

![Corridor degradation: BeautyMap measured replay from this new run](results/reference/robot-corridor-v2/methods/degraded_beautymap/result.gif)

[Result MP4](results/reference/robot-corridor-v2/methods/degraded_beautymap/result.mp4) · [case record](results/reference/robot-corridor-v2/methods/degraded_beautymap/record.json) · RMSE **72.53 cm** · 508 native updates.

**Physical robot tests remain pending.** Keyboard demos: `F:\be2演讲\实机脚本\20–23`; `24` automatically records all four scenes. Historical executions/replays remain in the repository, separately from the videos above.

## Supplementary live scene recordings

Actual native Gazebo + RViz + Terminal. The RViz viewport fills its window and is centred for the map; the earlier custom-viewer clips remain archived.

### S1 static · slam_toolbox mapping

![S1 static · slam_toolbox mapping](results/reference/robot-supp-static/execution.gif)

[MP4](results/reference/robot-supp-static/execution.mp4) · [record](results/reference/robot-supp-static/record.json)

### S2 dynamic · slam_toolbox mapping

![S2 dynamic · slam_toolbox mapping](results/reference/robot-supp-dynamic/execution.gif)

[MP4](results/reference/robot-supp-dynamic/execution.mp4) · [record](results/reference/robot-supp-dynamic/record.json)

### S3 persistent change · Raw map + AMCL

![S3 persistent change · Raw map + AMCL](results/reference/robot-supp-large-change/execution.gif)

[MP4](results/reference/robot-supp-large-change/execution.mp4) · [record](results/reference/robot-supp-large-change/record.json)

### S4 new corridor · limited → restored AMCL

![S4 new corridor · limited → restored AMCL](results/reference/robot-corridor-v2/executions/degraded_raw.gif)

[MP4](results/reference/robot-corridor-v2/executions/degraded_raw.mp4) · [record](results/reference/robot-corridor-v2/record.json)
