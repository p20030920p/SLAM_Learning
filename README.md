<div align="center">

# SLAM Learning

**Map repair?**

Robust localization and SLAM in dynamic environments · Localization self-recovery

[![CPU reproducibility](https://github.com/p20030920p/slam_learning_updated/actions/workflows/ci.yml/badge.svg)](https://github.com/p20030920p/slam_learning_updated/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.10-3776AB)](src/pyproject.toml)

English | [中文](docs/HOME.zh-CN.md)

[Research thread](#research-thread-localization-self-recovery-under-degradation-and-large-scene-change) · [Localization GIFs](#static-and-dynamic-localization-recordings) · [Direction](#direction-analysis) · [Open question](#open-questions) · [Related works](#related-works)

[Results](#reproduction-results) · [Evidence](#evidence) · [Hardware tests](#hardware-tests) · [Hypothesis](#hypothesis) · [Branches](#branches)

</div>

## Research thread: localization self-recovery under degradation and large scene change

The current thread of this repository is the **self-recovery of a localization system**: under geometric/perceptual **degradation** and under **large scene change** (the prior map no longer matches the world), how does the system detect that its own pose is no longer trustworthy, attribute the cause, recover without human intervention, and verify that the recovery actually succeeded?

Working documents (Chinese; English counterparts follow once the paper set is frozen):

- [Thread definition, evidence gaps and platform inventory](docs/self-recovery/README.zh-CN.md)
- [Paper map: degradation detection, relocalization, map maintenance, robust back-ends, evaluation](docs/self-recovery/SURVEY.zh-CN.md)
- [Feasibility with the existing static/dynamic AMCL recordings](docs/self-recovery/FEASIBILITY.zh-CN.md)
- [Candidate hypotheses H1–H6 with falsification conditions](docs/self-recovery/HYPOTHESES.zh-CN.md)
- [Hypotheses grouped by strategy family, each bound to one simulation cell](docs/self-recovery/HYPOTHESES-BY-PAPER.zh-CN.md)
- [Per-paper hypotheses: which paper suggests which claim, and which simulation cell tests it](docs/self-recovery/PAPER-TO-HYPOTHESIS.zh-CN.md)

The semantic-mapping and visual-localization direction previously hosted here has moved to the archived repository [SLAM_Learning](https://github.com/p20030920p/SLAM_Learning).

## Live experiments and local demos

[**SLAM-Physical**](https://github.com/p20030920p/SLAM-Physical) contains native BeautyMap pose-revision C1/C2/C4 experiments, a first Gazebo object-departure scenario, measured results and live RViz demos of BeautyMap and DUFOMap. On the prepared local machine, double-click scripts in [demo/](demo/README.md); missing sibling code is cloned automatically. Each demo executes the native pipeline again. Small demo subsets do not replace the paper benchmarks below.

New [Windows / WSL2 AMCL guide](https://github.com/p20030920p/SLAM-Physical/blob/main/docs/WINDOWS_AMCL.zh-CN.md): keyboard driving, live truth/estimate errors, automatic ROS bag recording, native paper-map adapters and paired localization replay.

Local `demo/14_static_keyboard.cmd` opens a purely static scene; `demo/15_dynamic_keyboard.cmd` opens a scene with three moving obstacles and a raw/paper-map menu. Both record automatically. `demo/16_record_static_dynamic.cmd` acquires independent mapping/test drives and runs repeated AMCL comparisons.

## Static and dynamic localization recordings

**Recorded on 2026-10-14:** four Gazebo mapping/test drives, 12 sensor-built maps and 42 scored AMCL replays. The four GIFs below replay recorded trajectories, maps and measured obstacle positions, with live error curves. Green is ground truth, blue is the localization estimate, and orange marks moving boxes. Each GIF preserves its companion MP4's complete playback duration; these are recorded-data reconstructions.

**Measured effect — position RMSE in cm, after the first 5 s; lower is better.** Compare methods within each sensor family. The dynamic improvement uses that family's raw map on the same dynamic test B.

| Map family | Map method | Pure static | Dynamic | Dynamic RMSE reduction | Clean map + dynamic test |
| --- | --- | ---: | ---: | ---: | ---: |
| LiDAR | Raw, no paper algorithm | 5.59 | 6.29 | Baseline | 4.86 |
| LiDAR | BeautyMap | 6.01 | 5.52 | 12.3% | 5.52 |
| LiDAR | DUFOMap | 6.21 | 5.06 | 19.5% | 4.75 |
| RGB-D geometry | Raw, no paper algorithm | 5.97 | 6.45 | Baseline | 6.48 |

Two further RGB-D geometry families were recorded with the same protocol by methods of the direction now archived in the old repository — ConceptGraphs and HOV-SG, with position RMSE 5.48 / 6.02 / 6.36 cm and 6.35 / 6.28 / 5.71 cm for the static / dynamic / clean-map conditions — and are shown in category 3 below.

Static and dynamic results each use three fresh AMCL replays of identical input; their position estimates were identical, so these check reproducibility. The clean-map control uses one replay per method. This is one controlled scene. [Full precision CSV](results/localization/static-dynamic/summary.csv) · [Protocol, maps and reports](https://github.com/p20030920p/SLAM-Physical/blob/main/docs/results/static-dynamic/README.md).

### 1. Pure static scene

![Pure static scene: six map methods, trajectories and live errors](results/localization/static-dynamic/static.gif)

Static mapping A and an independently recorded static test B contain no moving boxes. BeautyMap and DUFOMap slightly increase localization RMSE here; filtering does not automatically improve a clean scene. [MP4](results/localization/static-dynamic/static.mp4).

### 2. Dynamic scene — LiDAR map filtering

![Dynamic LiDAR comparison: raw, BeautyMap and DUFOMap](results/localization/static-dynamic/dynamic-lidar.gif)

Three boxes move during both mapping and testing. On the same test B, BeautyMap reduces RMSE by **0.78 cm**, and DUFOMap by **1.23 cm**, relative to the unfiltered LiDAR map. [MP4](results/localization/static-dynamic/dynamic-lidar.mp4).

### 3. Dynamic scene — RGB-D geometry maps

![Dynamic RGB-D geometry comparison: raw baseline and the two archived methods](results/localization/static-dynamic/dynamic-rgbd.gif)

With RGB-D raw as the baseline, the two archived RGB-D geometry methods listed above reduce RMSE by **0.43 cm** and **0.18 cm**. [MP4](results/localization/static-dynamic/dynamic-rgbd.mp4).

### 4. Control — clean maps with the same dynamic test

![Clean static maps with the identical dynamic test: six methods](results/localization/static-dynamic/clean-map-dynamic-test.gif)

This reuses **exactly the dynamic test B from categories 2–3**, changing mapping A to the static recording. Raw LiDAR RMSE is **4.86 cm** on the clean map versus **6.29 cm** on the dynamically built map. It helps separate map contamination from obstacles encountered during localization. [MP4](results/localization/static-dynamic/clean-map-dynamic-test.mp4).

Mapping A uses simulator-provided sensor poses to isolate map construction. Test B gives AMCL only scans, wheel odometry and the selected map; truth is used for scoring and display. The clips show repeat 1, with live AMCL + odometry prediction errors; the table scores AMCL pose updates. Map generation runs offline. [GIF timing, source hashes and recorded traces](results/localization/static-dynamic/README.md) · [Original six-method dynamic MP4](https://github.com/p20030920p/SLAM-Physical/blob/main/docs/results/static-dynamic/dynamic-localization-replay.mp4).

**Try it locally:** on the prepared Windows / WSL2 machine, double-click [14: static keyboard](demo/14_static_keyboard.cmd), [15: dynamic keyboard + map menu](demo/15_dynamic_keyboard.cmd), or [16: record and compare](demo/16_record_static_dynamic.cmd). Keyboard: `i` forward, `,` backward, `j` / `l` turn, `k` stop; `Ctrl+C` ends and saves the recording. [Setup and controls](demo/README.md).

## Direction analysis

**SLAM — Simultaneous Localization and Mapping:** estimate sensor motion while building a map from its observations.

- **Robust localization and SLAM in dynamic environments:** estimate motion and maintain a stable map despite moving objects, and keep the pose estimate trustworthy once the map no longer matches the world.

This repository keeps that single direction. Five elements organize the process, and the current thread adds detection and recovery around it:

```text
Sensor data → Front end → Back end (optimize) → Map build and pose output
                  ↓              ↑                        ↓
             Loop detection ─────┘          Failure detection → Recovery
```

| Element | Benefit | In this repository |
| --- | --- | --- |
| Sensor data | Cleaner input | Recorded Gazebo LiDAR and RGB-D drives; desktop hardware capture checks |
| Front end | Stable matches | Static-structure filtering (DUFOMap, BeautyMap) applied before localization |
| Back end | Consistent poses | AMCL pose updates from scans and wheel odometry; outlier handling is outside these experiments |
| Loop detection | Less drift | Not part of these experiments: the platform is AMCL, not a factor-graph back end |
| Map build | Stable maps | Supplied-pose mapping A builds each map; six map families are scored on the same test B |
| Failure detection and recovery | Trustworthy pose | The open thread: detection → attribution → recovery → confirmation, with the working documents linked above |

The direction kept here emphasizes reliable motion and geometry. The completed mapping experiments use supplied poses to isolate **map construction**; complete SLAM, navigation and a factor-graph back end remain outside these experiments. Pose errors can still corrupt static-structure filtering, which is where the open question below comes from.

## Open questions

**In degradation and large-change environments, what strategy effectively lets a localization system recover itself?**

Two working documents state the candidate claims and the measurements that would falsify them:

- [Hypotheses grouped by strategy family, each bound to one simulation cell](docs/self-recovery/HYPOTHESES-BY-PAPER.zh-CN.md) (Chinese)
- [Metric definitions, experiment matrix and falsification conditions](docs/self-recovery/HYPOTHESES.zh-CN.md) (Chinese)

## Related works

These are saved-result replays from supplied-pose mapping runs. GIFs preserve the companion MP4 timing; each selected map observation is held for eight frames at 12 fps. [DUFOMap timing](results/reference/dufomap/media/timing.json) · [BeautyMap timing](results/reference/beautymap/media/timing.json).

### [DUFOMap](docs/papers/dufomap.md)

![DUFOMap core replay](results/reference/dufomap/media/preview.gif)

**KITTI-00 outdoor scene, 141 LiDAR scans.** Observed empty space identifies dynamic points; pose margins protect static geometry. The GIF selects 21 scans to compare input, removed and retained points against the final map. [MP4](results/reference/dufomap/media/replay/replay.mp4).

### [BeautyMap](docs/papers/beautymap.md)

![BeautyMap core replay](results/reference/beautymap/media/preview.gif)

**KITTI-00 outdoor scene, 141 LiDAR scans.** Occupancy comparisons remove dynamic traces; restoration protects static geometry. The GIF selects 21 scans to compare input, removed and retained points against the final map. [MP4](results/reference/beautymap/media/replay/replay.mp4).

## Reproduction results

| Work | Data | Result |
| --- | --- | --- |
| [DUFOMap](https://github.com/p20030920p/SLAM_Learning/blob/535a2780af7ca7eb3aa02f722e1340fe90bc2dcf/docs/DUFOMAP_TABLE4.md) | KITTI-00, 141 scans | Table IV accuracy matched |
| [BeautyMap](https://github.com/p20030920p/SLAM_Learning/blob/535a2780af7ca7eb3aa02f722e1340fe90bc2dcf/docs/KITTI_PAPER_PROTOCOL.md) | Historical KITTI-02, 91 scans | Table III accuracy matched |

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

## Hardware tests

![D435 / Unitree L2](docs/media/hardware/devices.jpg)

Desktop setup: RealSense D435 depth camera (without IMU) and Unitree L2 LiDAR.

| Device | Basic test | Full video |
| --- | --- | --- |
| D435 | RGB / depth / stereo IR capture | [24.6 s](docs/media/hardware/d435-input.mp4) |
| L2 | Point cloud / ICP display | [42.2 s](docs/media/hardware/l2.mp4) |

![D435 input](docs/media/hardware/d435-input.gif)

![L2 display](docs/media/hardware/l2.gif)

Supplement: [D435 RGB-D odometry, 44.9 s](docs/media/hardware/d435.mp4). These are recorded acquisition and display checks; hardware accuracy, full SLAM and cross-sensor fusion remain unverified. [Timing and sources](docs/media/hardware/record.json).

## Hypothesis

We hypothesize that retaining the observation evidence behind map updates and revisiting these updates as pose estimates improve will reduce persistent mapping errors and keep geometric maps more consistent. Candidate hypotheses for the current self-recovery thread are stated under [Open questions](#open-questions).

## Branches

| Branch | Role |
| --- | --- |
| main | Curated submission: one direction (robust localization and SLAM in dynamic environments), two mapping reproductions, open question and hypothesis. |
| [reproduce/author-originals](https://github.com/p20030920p/SLAM_Learning/tree/reproduce/author-originals) | Original pipelines, paper-table scoring and recordings. |
| [notes/personal-study-guide-20261008](https://github.com/p20030920p/SLAM_Learning/tree/notes/personal-study-guide-20261008) | Personal study notes and hardware trials under `src/physical/`, including operations and failures. |


[AI use](docs/guides/DISCLOSURE.md) · [Sources/licenses](docs/guides/ATTRIBUTION.md) · [Citation](docs/CITATION.cff) · [License](src/LICENSE)
