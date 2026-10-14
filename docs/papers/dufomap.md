# DUFOMap

English | [中文](dufomap.zh-CN.md)

**KITTI-00, 141 LiDAR scans.** Observed free space identifies dynamic points; pose margins protect static geometry.

## Original paper datasets and scenes

| Evaluation | Data / scene |
| --- | --- |
| Quantitative 3D map cleaning | KITTI 00 (town) / 01 (highway), 64-channel LiDAR; Argoverse 2 urban traffic, two 32-channel sensors; semi-indoor moving people, 16-channel LiDAR. |
| Qualitative transfer | MCD VIRAL survey scans from separated Leica RTC360 stations; DOALS crowded train station, 128-channel LiDAR; two-floor building, Livox Mid-360. |
| Evaluated task | Scan classification using supplied poses. The paper distinguishes post-processing with all scans from online DUFOMap⋆ using only accumulated observations. |

[Paper §IV-A / §V](https://arxiv.org/html/2403.01449v1#S4). Its §V-E identifies sparse sampling as a limitation; §V-C shows pose errors affect classification. Our KITTI-00 run does not reproduce all of these datasets or the online benchmark.

## Observed effects before watching

| Effective | Failure / limit |
| --- | --- |
| Latest native KITTI-00, 141 scans: SA 97.98%, DA 98.70%; most dynamic traces removed and static points retained. [Live record](../../results/reference/desktop-live-dufomap/record.json) | Residual dynamic points and static-point loss remain. This is map cleaning, not pose recovery. Dynamic Gazebo AMCL with its projected map improves RMSE by only 0.06 cm against Raw in one run. [Robot record](../../results/reference/robot-live-dynamic/record.json) |

**Failure hypothesis to check:** sparse rays, occlusion or insufficient revisits may leave too little observed free space; pose errors can corrupt that evidence. Check visibility and point-retention decisions before attributing localization failure to the cleaner. This is a diagnostic inference, not an established cause in our runs.

The video below is the retained historical result replay; the [latest actual execution](../../results/reference/desktop-live-dufomap/execution.mp4) observes a fresh native run.

![DUFOMap](../../results/reference/dufomap/media/preview.gif)

[MP4](../../results/reference/dufomap/media/replay/replay.mp4) · [Run](../../results/reference/dufomap/runs/dufomap-wsl/record.json) · [Timing](../../results/reference/dufomap/media/timing.json)

## Results

The retained wrapper run gives SA / DA / AA = 97.9798 / 98.7029 / 98.3407%. The separate original C++ Table IV experiment matches all 15 paper accuracy values at two decimals.

[Original-code paper protocol](https://github.com/p20030920p/SLAM_Learning/blob/535a2780af7ca7eb3aa02f722e1340fe90bc2dcf/docs/DUFOMAP_TABLE4.md)

## Usage

[Setup and commands](../guides/REPRODUCE.md) · [Sources](../guides/ATTRIBUTION.md)

## Scope

Supplied poses isolate the declared mapping stages. Videos replay saved outputs; complete SLAM, navigation and hardware accuracy remain unverified.
