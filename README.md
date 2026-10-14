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

[Step-by-step teaching Notebook](notebooks/presentation/SLAM_实验逐步展示.ipynb) covers four author-code executions and all four robot conditions, with saved videos, maps, independently recomputed scores and explicit limits. The prepared local Notebook and offline HTML are in `F:\be2演讲\展示`; [opening instructions](notebooks/presentation/README.md).

[SLAM-Physical](https://github.com/p20030920p/SLAM-Physical) retains the earlier C1/C2/C4, object-departure and map-adapter experiments. Its legacy `demo/14–16` workflows and historical replay scores are distinct from the native desktop recordings below.

## Static and dynamic localization recordings

**Recorded on this Windows computer, 2026-10-14.** Gazebo + RViz + Terminal live execution, followed by each method’s own saved-data replay. Sim2Real omnidirectional chassis, native 2D LiDAR + independent 3D profile.

**Method labels refer to map processing; every robot localizer is AMCL.** Raw uses the unfiltered map; DUFOMap and BeautyMap clean the same provided-pose 3D mapping input before common 2D projection. The live GIF under each method is the **same parallel scene execution**: RViz displays Raw, while the terminal reports all instances. Each result GIF isolates that case; replay performs no new inference.

All-position RMSE includes initialization and uses retained native updates. One run per condition. [Scoring formula and numeric comparison](docs/testing/LIVE.md#how-errors-are-calculated) · [Recording names / modules / algorithms](demo/recording-index.json).

### Pure static

Small initial offset; no loss on this route.

#### Raw + AMCL

**Live execution**

![Pure static — Raw: shared native execution](results/reference/robot-static/execution.gif)

[MP4 · 170202-5abed0](results/reference/robot-static/execution.mp4)

**Measured result replay**

![Pure static — Raw: raw measured replay](results/reference/robot-static/methods/raw/result.gif)

[MP4](results/reference/robot-static/methods/raw/result.mp4) · [record](results/reference/robot-static/methods/raw/record.json) · RMSE **7.08 cm** · 290 native updates.

#### DUFOMap + AMCL

**Live execution**

![Pure static — DUFOMap: shared native execution](results/reference/robot-static/execution.gif)

[MP4 · 170202-5abed0](results/reference/robot-static/execution.mp4)

**Measured result replay**

![Pure static — DUFOMap: dufomap measured replay](results/reference/robot-static/methods/dufomap/result.gif)

[MP4](results/reference/robot-static/methods/dufomap/result.mp4) · [record](results/reference/robot-static/methods/dufomap/record.json) · RMSE **7.08 cm** · 290 native updates.

#### BeautyMap + AMCL

**Live execution**

![Pure static — BeautyMap: shared native execution](results/reference/robot-static/execution.gif)

[MP4 · 170202-5abed0](results/reference/robot-static/execution.mp4)

**Measured result replay**

![Pure static — BeautyMap: beautymap measured replay](results/reference/robot-static/methods/beautymap/result.gif)

[MP4](results/reference/robot-static/methods/beautymap/result.mp4) · [record](results/reference/robot-static/methods/beautymap/record.json) · RMSE **6.55 cm** · 290 native updates.

### Moving obstacles

Three moving boxes. Dynamic-A maps and static-A controls receive the same dynamic B input.

#### Raw + AMCL

**Live execution**

![Moving obstacles — Raw: shared native execution](results/reference/robot-dynamic/execution.gif)

[MP4 · 170718-20a6e0](results/reference/robot-dynamic/execution.mp4)

**Measured result replay — dynamic-A map**

![Moving obstacles — Raw: raw measured replay](results/reference/robot-dynamic/methods/raw/result.gif)

[MP4](results/reference/robot-dynamic/methods/raw/result.mp4) · [record](results/reference/robot-dynamic/methods/raw/record.json) · RMSE **7.31 cm** · 291 native updates.

**Measured result replay — static-A map control**

![Moving obstacles — Raw: clean_raw measured replay](results/reference/robot-dynamic/methods/clean_raw/result.gif)

[MP4](results/reference/robot-dynamic/methods/clean_raw/result.mp4) · [record](results/reference/robot-dynamic/methods/clean_raw/record.json) · RMSE **6.30 cm** · 291 native updates.

#### DUFOMap + AMCL

**Live execution**

![Moving obstacles — DUFOMap: shared native execution](results/reference/robot-dynamic/execution.gif)

[MP4 · 170718-20a6e0](results/reference/robot-dynamic/execution.mp4)

**Measured result replay — dynamic-A map**

![Moving obstacles — DUFOMap: dufomap measured replay](results/reference/robot-dynamic/methods/dufomap/result.gif)

[MP4](results/reference/robot-dynamic/methods/dufomap/result.mp4) · [record](results/reference/robot-dynamic/methods/dufomap/record.json) · RMSE **7.10 cm** · 291 native updates.

**Measured result replay — static-A map control**

![Moving obstacles — DUFOMap: clean_dufomap measured replay](results/reference/robot-dynamic/methods/clean_dufomap/result.gif)

[MP4](results/reference/robot-dynamic/methods/clean_dufomap/result.mp4) · [record](results/reference/robot-dynamic/methods/clean_dufomap/record.json) · RMSE **6.30 cm** · 291 native updates.

#### BeautyMap + AMCL

**Live execution**

![Moving obstacles — BeautyMap: shared native execution](results/reference/robot-dynamic/execution.gif)

[MP4 · 170718-20a6e0](results/reference/robot-dynamic/execution.mp4)

**Measured result replay — dynamic-A map**

![Moving obstacles — BeautyMap: beautymap measured replay](results/reference/robot-dynamic/methods/beautymap/result.gif)

[MP4](results/reference/robot-dynamic/methods/beautymap/result.mp4) · [record](results/reference/robot-dynamic/methods/beautymap/record.json) · RMSE **7.28 cm** · 291 native updates.

**Measured result replay — static-A map control**

![Moving obstacles — BeautyMap: clean_beautymap measured replay](results/reference/robot-dynamic/methods/clean_beautymap/result.gif)

[MP4](results/reference/robot-dynamic/methods/clean_beautymap/result.mp4) · [record](results/reference/robot-dynamic/methods/clean_beautymap/record.json) · RMSE **6.89 cm** · 291 native updates.

### Persistent change

Old static-A maps in a changed world. This route did not induce loss, so it is not recovery-success evidence.

#### Raw + AMCL

**Live execution**

![Persistent change — Raw: shared native execution](results/reference/robot-large-change/execution.gif)

[MP4 · 172452-ca9681](results/reference/robot-large-change/execution.mp4)

**Measured result replay**

![Persistent change — Raw: raw measured replay](results/reference/robot-large-change/methods/raw/result.gif)

[MP4](results/reference/robot-large-change/methods/raw/result.mp4) · [record](results/reference/robot-large-change/methods/raw/record.json) · RMSE **6.25 cm** · 290 native updates.

#### DUFOMap + AMCL

**Live execution**

![Persistent change — DUFOMap: shared native execution](results/reference/robot-large-change/execution.gif)

[MP4 · 172452-ca9681](results/reference/robot-large-change/execution.mp4)

**Measured result replay**

![Persistent change — DUFOMap: dufomap measured replay](results/reference/robot-large-change/methods/dufomap/result.gif)

[MP4](results/reference/robot-large-change/methods/dufomap/result.mp4) · [record](results/reference/robot-large-change/methods/dufomap/record.json) · RMSE **6.25 cm** · 290 native updates.

#### BeautyMap + AMCL

**Live execution**

![Persistent change — BeautyMap: shared native execution](results/reference/robot-large-change/execution.gif)

[MP4 · 172452-ca9681](results/reference/robot-large-change/execution.mp4)

**Measured result replay**

![Persistent change — BeautyMap: beautymap measured replay](results/reference/robot-large-change/methods/beautymap/result.gif)

[MP4](results/reference/robot-large-change/methods/beautymap/result.mp4) · [record](results/reference/robot-large-change/methods/beautymap/record.json) · RMSE **6.16 cm** · 290 native updates.

### Corridor degradation

1 m initial X offset. Full scans: 720 beams / 360° / 12 m; limited scans: 72 beams / 240° / 3.5 m, restored after 50 simulation seconds. Sustained convergence starts 11.3 s after restoration and is confirmed over 5 s. All three occupancy maps are identical here.

#### Raw + AMCL

**Live execution**

![Corridor degradation — Raw: shared native execution](results/reference/robot-degradation/execution.gif)

[MP4 · 173508-e41e34](results/reference/robot-degradation/execution.mp4)

**Measured result replay — full-scan control**

![Corridor degradation — Raw: raw measured replay](results/reference/robot-degradation/methods/raw/result.gif)

[MP4](results/reference/robot-degradation/methods/raw/result.mp4) · [record](results/reference/robot-degradation/methods/raw/record.json) · RMSE **62.64 cm** · 478 native updates.

**Measured result replay — limited → restored scans**

![Corridor degradation — Raw: degraded_raw measured replay](results/reference/robot-degradation/methods/degraded_raw/result.gif)

[MP4](results/reference/robot-degradation/methods/degraded_raw/result.mp4) · [record](results/reference/robot-degradation/methods/degraded_raw/record.json) · RMSE **73.63 cm** · 478 native updates.

#### DUFOMap + AMCL

**Live execution**

![Corridor degradation — DUFOMap: shared native execution](results/reference/robot-degradation/execution.gif)

[MP4 · 173508-e41e34](results/reference/robot-degradation/execution.mp4)

**Measured result replay — full-scan control**

![Corridor degradation — DUFOMap: dufomap measured replay](results/reference/robot-degradation/methods/dufomap/result.gif)

[MP4](results/reference/robot-degradation/methods/dufomap/result.mp4) · [record](results/reference/robot-degradation/methods/dufomap/record.json) · RMSE **62.64 cm** · 478 native updates.

**Measured result replay — limited → restored scans**

![Corridor degradation — DUFOMap: degraded_dufomap measured replay](results/reference/robot-degradation/methods/degraded_dufomap/result.gif)

[MP4](results/reference/robot-degradation/methods/degraded_dufomap/result.mp4) · [record](results/reference/robot-degradation/methods/degraded_dufomap/record.json) · RMSE **73.63 cm** · 478 native updates.

#### BeautyMap + AMCL

**Live execution**

![Corridor degradation — BeautyMap: shared native execution](results/reference/robot-degradation/execution.gif)

[MP4 · 173508-e41e34](results/reference/robot-degradation/execution.mp4)

**Measured result replay — full-scan control**

![Corridor degradation — BeautyMap: beautymap measured replay](results/reference/robot-degradation/methods/beautymap/result.gif)

[MP4](results/reference/robot-degradation/methods/beautymap/result.mp4) · [record](results/reference/robot-degradation/methods/beautymap/record.json) · RMSE **62.64 cm** · 478 native updates.

**Measured result replay — limited → restored scans**

![Corridor degradation — BeautyMap: degraded_beautymap measured replay](results/reference/robot-degradation/methods/degraded_beautymap/result.gif)

[MP4](results/reference/robot-degradation/methods/degraded_beautymap/result.mp4) · [record](results/reference/robot-degradation/methods/degraded_beautymap/record.json) · RMSE **73.63 cm** · 478 native updates.

**Physical robot tests:** static, dynamic, degradation and persistent change remain pending; 2D/3D sensor layers are listed in the [protocol](docs/testing/LIVE.md#one-click-demonstrations-and-physical-tests).

Local keyboard and recording scripts: `F:\be2演讲\实机脚本`; [instructions](demo/README.md).

## Direction analysis

**SLAM (Simultaneous Localization and Mapping)** estimates motion while building a map. The direction includes dynamic-environment mapping, localization and SLAM; self-recovery is an open question within it.

| Deliverable | Content |
| --- | --- |
| Native reproduction | Author source/data/protocol, each paper's metrics and actual reproduced scope |
| Robot tests | Sim2Real-AlgoBench omnidirectional chassis, native 2D and independent 3D LiDAR profiles, progressively harder mapping/localization/recovery |
| Question analysis | Separate weak constraints from map mismatch; narrow using reproducible failures, keeping methods open |

Semantic mapping and earlier projections remain in the [original repository](https://github.com/p20030920p/SLAM_Learning).

## Related works

Fresh native author-code executions and their own result replays. Original datasets are separate from the Gazebo platform tests. Historical paper-table evidence remains below; fresh LiDAR scores use the independent scorer without a new PCL cross-check.

### DUFOMap — author-code reproduction

KITTI-00, 141 scans; final-map orbit, not online map growth. [Paper card](docs/papers/dufomap.md) · [record](results/reference/desktop-dufomap/record.json)

**Live execution**

![DUFOMap native execution](results/reference/desktop-dufomap/execution.gif)

[MP4](results/reference/desktop-dufomap/execution.mp4)

**Measured result replay**

![DUFOMap measured result replay](results/reference/desktop-dufomap/result.gif)

[MP4](results/reference/desktop-dufomap/result.mp4)

### BeautyMap — author-code reproduction

KITTI-00, 141 scans; distinct from the historical KITTI-02 paper-table reproduction. [Paper card](docs/papers/beautymap.md) · [record](results/reference/desktop-beautymap/record.json)

**Live execution**

![BeautyMap native execution](results/reference/desktop-beautymap/execution.gif)

[MP4](results/reference/desktop-beautymap/execution.mp4)

**Measured result replay**

![BeautyMap measured result replay](results/reference/desktop-beautymap/result.gif)

[MP4](results/reference/desktop-beautymap/result.mp4)

### IR-MCL — author-code reproduction

Bonn IPBLab: 1543 processed, 1354 scored; fresh 5.36 cm / 1.06°. [Paper card](docs/papers/ir-mcl.md) · [record](results/reference/desktop-ir-mcl/record.json)

**Live execution**

![IR-MCL native execution](results/reference/desktop-ir-mcl/execution.gif)

[MP4](results/reference/desktop-ir-mcl/execution.mp4)

**Measured result replay**

![IR-MCL measured result replay](results/reference/desktop-ir-mcl/result.gif)

[MP4](results/reference/desktop-ir-mcl/result.mp4)

### AdaM-MCL — author-code reproduction

Authored 128-cell plan, existing 2432-step checkpoint; one fresh 123-update trial, 32.23-cell RMSE; no numeric paper comparison. [Paper card](docs/papers/adam-mcl.md) · [record](results/reference/desktop-adam-mcl/record.json)

**Live execution**

![AdaM-MCL native execution](results/reference/desktop-adam-mcl/execution.gif)

[MP4](results/reference/desktop-adam-mcl/execution.mp4)

**Measured result replay**

![AdaM-MCL measured result replay](results/reference/desktop-adam-mcl/result.gif)

[MP4](results/reference/desktop-adam-mcl/result.mp4)

AdaM-MCL’s terminal dashboard had a legacy footer error; current scores are recomputed from native saved distance logs. The author filter is unchanged; the wrapper footer is corrected for subsequent demonstrations. [Erratum](results/reference/adam-mcl/ERRATUM.md).

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
