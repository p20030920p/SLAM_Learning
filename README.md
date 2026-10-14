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

[SLAM-Physical](https://github.com/p20030920p/SLAM-Physical) retains the earlier C1/C2/C4, object-departure and map-adapter experiments. Its legacy `demo/14–16` workflows and historical replay scores are distinct from the native desktop recordings below.

## Static and dynamic localization recordings

**Recorded on this Windows computer, 2026-10-14.** Actual Gazebo + RViz + Terminal windows; fresh measured-data replays shown separately. Sim2Real omnidirectional chassis, native 2D LiDAR + independent 3D profile. [Protocol / 计算口径](docs/testing/LIVE.md)

| Gazebo scene | Live execution | Measured result replay | Observed outcome |
| --- | --- | --- | --- |
| Pure static | ![live](results/reference/robot-static/execution.gif) [MP4](results/reference/robot-static/execution.mp4) | ![result](results/reference/robot-static/result.gif) [MP4](results/reference/robot-static/result.mp4) | Small offset; no loss |
| Moving obstacles | ![live](results/reference/robot-dynamic/execution.gif) [MP4](results/reference/robot-dynamic/execution.mp4) | ![result](results/reference/robot-dynamic/result.gif) [MP4](results/reference/robot-dynamic/result.mp4) | Three moving boxes; six simultaneous localizers |
| Persistent change | ![live](results/reference/robot-large-change/execution.gif) [MP4](results/reference/robot-large-change/execution.mp4) | ![result](results/reference/robot-large-change/result.gif) [MP4](results/reference/robot-large-change/result.mp4) | Old map; this route did not induce loss |
| Corridor degradation | ![live](results/reference/robot-degradation/execution.gif) [MP4](results/reference/robot-degradation/execution.mp4) | ![result](results/reference/robot-degradation/result.gif) [MP4](results/reference/robot-degradation/result.mp4) | Limited scans restored; convergence after 11.3s |

**Gazebo position RMSE (cm), all retained native AMCL updates including initialization.** DUFOMap/BeautyMap provide offline 3D-derived maps to the same 2D AMCL; these are platform adaptations. Mapping A receives provided poses; held-out B receives scans and wheel odometry, with independent simulator truth for scoring only. One run per condition.

| Condition | Raw | DUFOMap | BeautyMap | Updates per method |
| --- | ---: | ---: | ---: | ---: |
| Pure static | 7.08 | 7.08 | 6.55 | 290 |
| Moving obstacles | 7.31 | 7.10 | 7.28 | 291 |
| Static map + same dynamic input | 6.30 | 6.30 | 6.89 | 291 |
| Persistent change | 6.25 | 6.25 | 6.16 | 290 |
| Corridor degradation | 62.64 | 62.64 | 62.64 | 478 |
| Limited → restored corridor scans | 73.63 | 73.63 | 73.63 | 478 |

Corridor rows use a disclosed 1 m initial X offset; other rows use 0.25 m. The corridor restores 720-beam / 360° / 12 m observations after 50 simulation seconds of 72-beam / 240° / 3.5 m input. Continued motion allows AMCL updates; sustained convergence is checked for 5 seconds. This is an initial-belief recovery test, not physical kidnapping.

**Physical robot tests**

| Scene | Robot / sensors | Status |
| --- | --- | --- |
| Static / dynamic / degradation / persistent change | Same chassis; 2D and 3D layers | Pending measurement |

Local one-click keyboard/recording scripts: `F:\be2演讲\实机脚本`; [instructions](demo/README.md) · [historical error audit](results/localization/static-dynamic/scored/audit.json).

## Direction analysis

**SLAM (Simultaneous Localization and Mapping)** estimates motion while building a map. The direction includes dynamic-environment mapping, localization and SLAM; self-recovery is an open question within it.

| Deliverable | Content |
| --- | --- |
| Native reproduction | Author source/data/protocol, each paper's metrics and actual reproduced scope |
| Robot tests | Sim2Real-AlgoBench omnidirectional chassis, native 2D and independent 3D LiDAR profiles, progressively harder mapping/localization/recovery |
| Question analysis | Separate weak constraints from map mismatch; narrow using reproducible failures, keeping methods open |

Semantic mapping and earlier projections remain in the [original repository](https://github.com/p20030920p/SLAM_Learning).

## Related works

Fresh native executions on this Windows computer, paired with their own measured result replays. Original author datasets are distinct from the Gazebo platform tests above. Older paper-table evidence remains archived below; fresh LiDAR scores use the independent scorer, without a new PCL cross-check.

| Method | Native execution | Fresh result replay | Scope |
| --- | --- | --- | --- |
| [dufomap](docs/papers/dufomap.md) | ![execution](results/reference/desktop-dufomap/execution.gif) [MP4](results/reference/desktop-dufomap/execution.mp4) | ![result](results/reference/desktop-dufomap/result.gif) [MP4](results/reference/desktop-dufomap/result.mp4) | KITTI-00, 141 scans; final-map orbit, no online-growth claim · [record](results/reference/desktop-dufomap/record.json) |
| [beautymap](docs/papers/beautymap.md) | ![execution](results/reference/desktop-beautymap/execution.gif) [MP4](results/reference/desktop-beautymap/execution.mp4) | ![result](results/reference/desktop-beautymap/result.gif) [MP4](results/reference/desktop-beautymap/result.mp4) | KITTI-00, 141 scans; this differs from historical KITTI-02 paper match · [record](results/reference/desktop-beautymap/record.json) |
| [ir-mcl](docs/papers/ir-mcl.md) | ![execution](results/reference/desktop-ir-mcl/execution.gif) [MP4](results/reference/desktop-ir-mcl/execution.mp4) | ![result](results/reference/desktop-ir-mcl/result.gif) [MP4](results/reference/desktop-ir-mcl/result.mp4) | Bonn IPBLab: 1543 processed, 1354 scored; fresh 5.36 cm / 1.06° · [record](results/reference/desktop-ir-mcl/record.json) |
| [adam-mcl](docs/papers/adam-mcl.md) | ![execution](results/reference/desktop-adam-mcl/execution.gif) [MP4](results/reference/desktop-adam-mcl/execution.mp4) | ![result](results/reference/desktop-adam-mcl/result.gif) [MP4](results/reference/desktop-adam-mcl/result.mp4) | Authored 128-cell plan, existing 2432-step checkpoint, one fresh 123-update trial; 32.23-cell RMSE; no paper comparison · [record](results/reference/desktop-adam-mcl/record.json) |

AdaM-MCL's terminal dashboard had a legacy footer error; corrected scores are recomputed from native saved distance logs. The author filter is unchanged; the wrapper footer is corrected for subsequent demonstrations. [erratum](results/reference/adam-mcl/ERRATUM.md).

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
