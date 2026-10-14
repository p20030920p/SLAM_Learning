<div align="center">

# SLAM Learning

**Robust localization and SLAM in dynamic environments**

Robust localization and SLAM in dynamic environments · Localization self-recovery

[![CPU reproducibility](https://github.com/p20030920p/slam_learning_updated/actions/workflows/ci.yml/badge.svg)](https://github.com/p20030920p/slam_learning_updated/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.10-3776AB)](src/pyproject.toml)

English | [中文](docs/HOME.zh-CN.md)

[Open question](#open-question) · [Localization GIFs](#static-and-dynamic-localization-recordings) · [Direction](#direction-analysis) · [Related works](#related-works)

[Results](#reproduction-results) · [Evidence](#evidence) · [Hypothesis](#hypothesis) · [Branches](#branches)

</div>

## Open question

**What strategies enable localization self-recovery under degradation and substantial environmental change?** Analyze failure mechanisms, recovery targets and boundaries before choosing a strategy. Deliver author-code reproductions and progressively harder point-cloud mapping/localization tests on the Sim2Real-AlgoBench robot. [Question analysis](docs/self-recovery/DESIGN.md) · [Robot test protocol](docs/testing/PROTOCOL.md) · [Chinese talk](docs/self-recovery/TALK.zh-CN.md) · [Status](docs/self-recovery/STATUS.zh-CN.md).

## Live experiments and local demos

Current native Gazebo/RViz/Terminal workflow: [one-click instructions](demo/README.md), [paired local video gallery](demo/gallery.html), [scoring protocol](docs/testing/LIVE.md). Prepared Windows scripts are in `F:\be2演讲\实机脚本`; separate keyboard and automatic recording entries cover static, moving-obstacle, persistent-change and corridor-restoration tests.

[Earlier executed teaching Notebook](notebooks/presentation/SLAM_实验逐步展示.ipynb) covers four author-code executions and all four robot conditions, with saved videos, maps, independently recomputed scores and explicit limits. The prepared local Notebook and offline HTML are in `F:\be2演讲\展示`; [opening instructions](notebooks/presentation/README.md).

[SLAM-Physical](https://github.com/p20030920p/SLAM-Physical) retains the earlier C1/C2/C4, object-departure and map-adapter experiments. Its legacy `demo/14–16` workflows and historical replay scores are distinct from the native desktop recordings below.

## Static and dynamic localization recordings

**Fresh live tests on this Windows computer, 2026-10-14.** Each method has its own actual RViz window, map topic, native AMCL pose/particles and isolated display TF. Each GIF records Gazebo + that method’s RViz + Terminal, during the same live scene input.

**Raw / DUFOMap / BeautyMap are map-processing choices; the live localizer is AMCL.** Mapping uses provided poses and common 2D projection; this is a scoped 3D-map-to-2D-localization adaptation. Results below come from these new runs, including initialization; one trial per condition.

[Scoring and controls](docs/testing/LIVE.md) · [Recording names](demo/recording-index.json) · [One-click method demos](demo/README.md#逐方法独立-rviz-现场对照)

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

1 m initial X offset; 72 beams / 240° / 3.5 m for 50 simulation seconds, then full scans. This trial starts sustained convergence 31.3 s after restoration, verified over 5 s. All three corridor occupancy maps are identical.

#### Raw map + AMCL

**Live execution — Raw RViz**

![Corridor degradation: actual Raw RViz live execution](results/reference/robot-live-degradation/executions/degraded_raw.gif)

[Live MP4](results/reference/robot-live-degradation/executions/degraded_raw.mp4) · [RViz config](results/reference/robot-live-degradation/view-degraded_raw.rviz) · [record](results/reference/robot-live-degradation/record.json)

**Measured result replay — Raw**

![Corridor degradation: Raw measured replay from this new run](results/reference/robot-live-degradation/methods/degraded_raw/result.gif)

[Result MP4](results/reference/robot-live-degradation/methods/degraded_raw/result.mp4) · [case record](results/reference/robot-live-degradation/methods/degraded_raw/record.json) · RMSE **75.66 cm** · 476 native updates.

#### DUFOMap map + AMCL

**Live execution — DUFOMap RViz**

![Corridor degradation: actual DUFOMap RViz live execution](results/reference/robot-live-degradation/executions/degraded_dufomap.gif)

[Live MP4](results/reference/robot-live-degradation/executions/degraded_dufomap.mp4) · [RViz config](results/reference/robot-live-degradation/view-degraded_dufomap.rviz) · [record](results/reference/robot-live-degradation/record.json)

**Measured result replay — DUFOMap**

![Corridor degradation: DUFOMap measured replay from this new run](results/reference/robot-live-degradation/methods/degraded_dufomap/result.gif)

[Result MP4](results/reference/robot-live-degradation/methods/degraded_dufomap/result.mp4) · [case record](results/reference/robot-live-degradation/methods/degraded_dufomap/record.json) · RMSE **75.66 cm** · 476 native updates.

#### BeautyMap map + AMCL

**Live execution — BeautyMap RViz**

![Corridor degradation: actual BeautyMap RViz live execution](results/reference/robot-live-degradation/executions/degraded_beautymap.gif)

[Live MP4](results/reference/robot-live-degradation/executions/degraded_beautymap.mp4) · [RViz config](results/reference/robot-live-degradation/view-degraded_beautymap.rviz) · [record](results/reference/robot-live-degradation/record.json)

**Measured result replay — BeautyMap**

![Corridor degradation: BeautyMap measured replay from this new run](results/reference/robot-live-degradation/methods/degraded_beautymap/result.gif)

[Result MP4](results/reference/robot-live-degradation/methods/degraded_beautymap/result.mp4) · [case record](results/reference/robot-live-degradation/methods/degraded_beautymap/record.json) · RMSE **75.66 cm** · 476 native updates.

**Physical robot tests remain pending.** Keyboard demos: `F:\be2演讲\实机脚本\20–23`; `24` automatically records all four scenes. Historical executions/replays remain in the repository, separately from the videos above.

## Supplementary live scene recordings

A separate offscreen camera + topic-viewer pipeline; the native Gazebo/RViz/Terminal captures and method scores are above.

Left is the simulator's own overview render; right is the map being built online. Both halves come from a single 1920x1080 capture, so they are the same instant. Every take is judged from the encoded file by five gates: the left renders, the right draws, the map grows (or, for a localisation level, correctly does **not** grow), the robot actually moved, and the display stayed alive. The right half is a purpose-built viewer for the same topics, not the RViz window, because RViz's map shader fails to link under llvmpipe. [Conditions, pipeline and limitations](results/localization/self-recovery/README.md).

### S1 static

![S1 static: live split screen](results/localization/self-recovery/S1_static.gif)

[MP4](results/localization/self-recovery/S1_static.mp4) · [check](results/localization/self-recovery/S1_static_check.json) · 170 s · map grew 216x143 to 293x143 cells (4.65 m to 14.65 m wide) · robot trail +265 px.

### S2 dynamic

![S2 dynamic: live split screen](results/localization/self-recovery/S2_dynamic.gif)

[MP4](results/localization/self-recovery/S2_dynamic.mp4) · [check](results/localization/self-recovery/S2_dynamic_check.json) · 80 s · three moving obstacles in frame; the right half changed 6.5 percent between samples.

### S3 large change

![S3 large change: live split screen](results/localization/self-recovery/S3_large_change.gif)

[MP4](results/localization/self-recovery/S3_large_change.mp4) · [check](results/localization/self-recovery/S3_large_change_check.json) · 70 s · the level is handed a saved map and must not grow it; robot trail +578 px. What failed here first was the criterion, not the localisation: `map -> base_footprint` moves and `amcl_pose` tracks it.

### S4 degradation

![S4 degradation: live split screen](results/localization/self-recovery/S4_degradation.gif)

[MP4](results/localization/self-recovery/S4_degradation.mp4) · [check](results/localization/self-recovery/S4_degradation_check.json) · 70 s · 72-beam, 120-degree, 3.5 m lidar in a straight corridor; robot trail +229 px. The map does not grow, which is the point of the level, and the check records that rather than leaning on a weak branch.

## Direction analysis

**SLAM (Simultaneous Localization and Mapping)** estimates motion while building a map. The direction includes dynamic-environment mapping, localization and SLAM; self-recovery is an open question within it.

| Deliverable | Content |
| --- | --- |
| Native reproduction | Author source/data/protocol, each paper's metrics and actual reproduced scope |
| Robot tests | Sim2Real-AlgoBench omnidirectional chassis, native 2D and independent 3D LiDAR profiles, progressively harder mapping/localization/recovery |
| Question analysis | Separate weak constraints from map mismatch; narrow using reproducible failures, keeping methods open |

Semantic mapping and earlier projections remain in the [original repository](https://github.com/p20030920p/SLAM_Learning).

## Related works

**Live author-code execution with RViz + Terminal.** These three new recordings show current native computation; they do not load a previously computed final map or trajectory as execution. Display-only observers thin points/particles and add overhead; no paper runtime comparison is made. Source data are the released author datasets.

### DUFOMap

**Live execution**

![DUFOMap: fresh native calculation and actual RViz](results/reference/desktop-live-dufomap/execution.gif)

[Live MP4](results/reference/desktop-live-dufomap/execution.mp4) · [record](results/reference/desktop-live-dufomap/record.json) · [paper](docs/papers/dufomap.md)

KITTI-00, 141 scans. The current octree is queried during integration, followed by final propagation; gray = retained, red = removed, cyan = current scan. SA 97.98% / DA 98.70%.

### BeautyMap

**Live execution**

![BeautyMap: fresh native calculation and actual RViz](results/reference/desktop-live-beautymap/execution.gif)

[Live MP4](results/reference/desktop-live-beautymap/execution.mp4) · [record](results/reference/desktop-live-beautymap/record.json) · [paper](docs/papers/beautymap.md)

KITTI-00, 141 scans. Offline map cleaning shown while it computes: the full input map is available at the start and cumulative native removal decisions update during scan processing. SA 96.95% / DA 98.34%.

### IR-MCL

**Live execution**

![IR-MCL: fresh native calculation and actual RViz](results/reference/desktop-live-ir-mcl/execution.gif)

[Live MP4](results/reference/desktop-live-ir-mcl/execution.mp4) · [record](results/reference/desktop-live-ir-mcl/record.json) · [paper](docs/papers/ir-mcl.md)

Bonn IPBLab, 1543 processed / 1354 scored poses. Current native particles, displayed estimate and reference update during inference. Fresh RMSE 5.31 cm / 1.07°.

### AdaM-MCL

Previous native terminal execution and labelled saved-output replay, retained unchanged. Authored 128-cell plan / 2432-step checkpoint; one 123-update trial, 32.23-cell RMSE; no paper numeric comparison.

**Live execution (terminal)**

![AdaM-MCL native terminal execution](results/reference/desktop-adam-mcl/execution.gif)

[MP4](results/reference/desktop-adam-mcl/execution.mp4)

**Measured result replay**

![AdaM-MCL saved result replay](results/reference/desktop-adam-mcl/result.gif)

[MP4](results/reference/desktop-adam-mcl/result.mp4) · [Score erratum](results/reference/adam-mcl/ERRATUM.md)

Historical paper-table evidence remains below; fresh LiDAR values use the independent scorer without a new PCL cross-check.

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

## Hypothesis

Test whether cleaner maps also improve recovery, better nominal observation models expand recovery range, and remaining stable structure limits recovery against obsolete maps. Complete native reproduction and progressive tests before choosing an intervention. [Analysis and counterexamples](docs/self-recovery/DESIGN.md).

## Branches

| Branch | Role |
| --- | --- |
| main | Curated submission: dynamic-environment localization, scoped mapping/localization reproductions and a candidate recovery experiment. |
| [reproduce/author-originals](https://github.com/p20030920p/SLAM_Learning/tree/reproduce/author-originals) | Original pipelines, paper-table scoring and recordings. |
| [notes/personal-study-guide-20261008](https://github.com/p20030920p/SLAM_Learning/tree/notes/personal-study-guide-20261008) | Personal study notes and hardware trials under `src/physical/`, including operations and failures. |


[AI use](docs/guides/DISCLOSURE.md) · [Sources/licenses](docs/guides/ATTRIBUTION.md) · [Citation](docs/CITATION.cff) · [License](src/LICENSE)
