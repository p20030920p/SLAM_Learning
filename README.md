<div align="center">

# SLAM Learning

**Localization self-recovery**

Robust localization and SLAM in dynamic environments · Localization self-recovery

[![CPU reproducibility](https://github.com/p20030920p/slam_learning_updated/actions/workflows/ci.yml/badge.svg)](https://github.com/p20030920p/slam_learning_updated/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.10-3776AB)](src/pyproject.toml)

English | [中文](docs/HOME.zh-CN.md)

[Open question](#open-question) · [Localization GIFs](#static-and-dynamic-localization-recordings) · [Direction](#direction-analysis) · [Related works](#related-works)

[Results](#reproduction-results) · [Evidence](#evidence) · [Hypothesis](#hypothesis) · [Branches](#branches)

</div>

## Open question

**What strategies enable a localization system to recover itself under degradation and substantial environmental change?** The first experiment focuses on 2D MCL recovery triggers, pose proposals and sustained confirmation. [Research design](docs/self-recovery/DESIGN.md) · [Chinese talk](docs/self-recovery/TALK.zh-CN.md) · [Handoff status](docs/self-recovery/STATUS.zh-CN.md) · [Working literature](docs/self-recovery/README.zh-CN.md).

## Live experiments and local demos

[**SLAM-Physical**](https://github.com/p20030920p/SLAM-Physical) contains native BeautyMap pose-revision C1/C2/C4 experiments, a first Gazebo object-departure scenario, measured results and live RViz demos of BeautyMap and DUFOMap. On the prepared local machine, double-click scripts in [demo/](demo/README.md); missing sibling code is cloned automatically. Each demo executes the native pipeline again. Small demo subsets do not replace the paper benchmarks below.

New [Windows / WSL2 AMCL guide](https://github.com/p20030920p/SLAM-Physical/blob/main/docs/WINDOWS_AMCL.zh-CN.md): keyboard driving, live truth/estimate errors, automatic ROS bag recording, native paper-map adapters and paired localization replay.

Local `demo/14_static_keyboard.cmd` opens a purely static scene; `demo/15_dynamic_keyboard.cmd` opens a scene with three moving obstacles and a raw/paper-map menu. Both record automatically. `demo/16_record_static_dynamic.cmd` acquires independent mapping/test drives and runs repeated AMCL comparisons.

## Static and dynamic localization recordings

**Earlier map-filtering comparison.** Recorded 2026-10-14 with independent mapping A and test B. This historical LiDAR subset contains six maps and 21 scored replays. Position RMSE below excludes the first 5 s (cm); recovery after failure has not been evaluated.

| Map | Static test | Dynamic test | Clean map + same dynamic test |
| --- | ---: | ---: | ---: |
| Raw | 5.59 | 6.29 | 4.86 |
| BeautyMap | 6.01 | 5.52 | 5.52 |
| DUFOMap | 6.21 | 5.06 | 4.75 |

![Dynamic LiDAR map and localization replay](results/localization/static-dynamic/dynamic-lidar.gif)

Recorded-data reconstruction with three moving boxes: green is truth, blue the estimate. Mapping uses supplied poses; test AMCL receives no truth. Three identical-input main replays check reproducibility; the clean-map control has one replay. [MP4](results/localization/static-dynamic/dynamic-lidar.mp4) · [Historical evidence](results/localization/static-dynamic/README.md).

**Recovery footage preparation.** S1 static, S2 dynamic, S3 persistent structural change and S4 degradation are being prepared. Split-screen footage has not passed visual acceptance. [Status](docs/self-recovery/STATUS.zh-CN.md).

## Direction analysis

**SLAM (Simultaneous Localization and Mapping)** estimates motion while building a map. The first experiment studies recovery against a prior map; full SLAM back ends are a later extension.

| Stage | Current role |
| --- | --- |
| Map preparation | DUFOMap/BeautyMap controls and static-structure preservation |
| Online localization | MCL estimates pose from scans, odometry and map; AMCL is not a factor-graph back end |
| Recovery supervision | Monitor anomalies, generate proposals within budget and confirm trust using later observations |

The semantic-mapping direction and earlier projection comparisons remain in the [original repository](https://github.com/p20030920p/SLAM_Learning).

## Related works

These are saved-result replays of recorded runs. GIFs preserve the companion MP4 timing; for the two mapping replays each selected map observation is held for eight frames at 12 fps. [DUFOMap timing](results/reference/dufomap/media/timing.json) · [BeautyMap timing](results/reference/beautymap/media/timing.json) · [IR-MCL timing](results/reference/ir-mcl/media/timing.json) · [AdaM-MCL timing](results/reference/adam-mcl/media/timing.json).

### [DUFOMap](docs/papers/dufomap.md)

![DUFOMap core replay](results/reference/dufomap/media/preview.gif)

**KITTI-00 outdoor scene, 141 LiDAR scans.** Observed empty space identifies dynamic points; pose margins protect static geometry. The GIF selects 21 scans to compare input, removed and retained points against the final map. [MP4](results/reference/dufomap/media/replay/replay.mp4).

### [BeautyMap](docs/papers/beautymap.md)

![BeautyMap core replay](results/reference/beautymap/media/preview.gif)

**KITTI-00 outdoor scene, 141 LiDAR scans.** Occupancy comparisons remove dynamic traces; restoration protects static geometry. The GIF selects 21 scans to compare input, removed and retained points against the final map. [MP4](results/reference/beautymap/media/replay/replay.mp4).

### [IR-MCL](docs/papers/ir-mcl.md)

![IR-MCL saved localization replay](results/reference/ir-mcl/media/preview.gif)

**Bonn IPBLab indoor lab, the released localization sequence, 1543 2D LiDAR scans.** A neural occupancy field renders a synthetic scan for every particle, and the rendered-versus-real range difference weights the particles. The GIF replays all 1543 saved frames at the upstream tool's 10 fps. [MP4](results/reference/ir-mcl/media/replay/replay.mp4).

### [AdaM-MCL](docs/papers/adam-mcl.md)

![AdaM-MCL recorded evaluation session](results/reference/adam-mcl/media/preview.gif)

**Authored 128-cell indoor plan, one held-out scene, 200 particles.** A CNN turns a map and a 2-D scan into a samplable pose distribution, so global-localization particles are drawn from the whole map instead of a uniform prior. Unlike the rows above this one is the recorded run in real time: the cloud contracts from its uniform start, then again after the teleport at update 63. [MP4](results/reference/adam-mcl/media/replay/replay.mp4).

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

**No numeric comparison is made.** The paper's 20 simulation maps are 43 m × 43 m with six evaluation sequences and released checkpoints, all of them external downloads; this run authors its own plans and trains for 2 432 optimizer steps against the authors' 2 880 000, so cells are not metres. Measured here, in cells: position RMSE 5.49 over 10 repeats, mean final error 6.78, 0.43 s per filter update, and 0 of 10 repeats holding the paper's convergence rule rescaled to this plan.

## Hypothesis

Temporal triggering and sustained recovery confirmation may reduce unnecessary resets and improve correctly available time within a fixed budget. Compare explicit AMCL recovery off/on, single-frame triggering and periodic resets first. [Candidate hypotheses and falsification](docs/self-recovery/DESIGN.md).

## Branches

| Branch | Role |
| --- | --- |
| main | Curated submission: dynamic-environment localization, scoped mapping/localization reproductions and a candidate recovery experiment. |
| [reproduce/author-originals](https://github.com/p20030920p/SLAM_Learning/tree/reproduce/author-originals) | Original pipelines, paper-table scoring and recordings. |
| [notes/personal-study-guide-20261008](https://github.com/p20030920p/SLAM_Learning/tree/notes/personal-study-guide-20261008) | Personal study notes and hardware trials under `src/physical/`, including operations and failures. |


[AI use](docs/guides/DISCLOSURE.md) · [Sources/licenses](docs/guides/ATTRIBUTION.md) · [Citation](docs/CITATION.cff) · [License](src/LICENSE)
