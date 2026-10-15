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

| Method | Map type | Metric / effect |
| --- | --- | --- |
| DUFOMap | 3D dynamic-point-cleaned map | SA 97.98% / DA 98.70%; cleaning works |

**Failure hypothesis to check:** sparse rays, occlusion or insufficient revisits may leave too little observed free space; pose errors can corrupt that evidence. Check visibility and point-retention decisions before attributing localization failure to the cleaner. This is a diagnostic inference, not an established cause in our runs.

The video below is the retained historical result replay; the [latest actual execution](../../results/reference/desktop-live-dufomap/execution.mp4) observes a fresh native run.

![DUFOMap](../../results/reference/dufomap/media/preview.gif)

[MP4](../../results/reference/dufomap/media/replay/replay.mp4) · [Run](../../results/reference/dufomap/runs/dufomap-wsl/record.json) · [Timing](../../results/reference/dufomap/media/timing.json)

## Results

The retained wrapper run gives SA / DA = 97.9798 / 98.7029%. Only static retention and dynamic removal are displayed here; complete paper scores remain in the source records. This cleaning experiment does not measure downstream localization or navigation.

[Original-code paper protocol](https://github.com/p20030920p/SLAM_Learning/blob/535a2780af7ca7eb3aa02f722e1340fe90bc2dcf/docs/DUFOMAP_TABLE4.md)

## Usage

[Setup and commands](../guides/REPRODUCE.md) · [Sources](../guides/ATTRIBUTION.md)

## Scope

Supplied poses isolate the declared mapping stages. Videos replay saved outputs; complete SLAM, navigation and hardware accuracy remain unverified.
