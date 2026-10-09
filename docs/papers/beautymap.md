# BeautyMap

English | [中文](beautymap.zh-CN.md)

**KITTI-00, 141 LiDAR scans.** Occupancy comparisons remove dynamic traces; restoration protects static geometry.

![BeautyMap](../../results/reference/beautymap/media/preview.gif)

[MP4](../../results/reference/beautymap/media/replay/replay.mp4) · [Run](../../results/reference/beautymap/runs/beautymap-wsl/record.json) · [Timing](../../results/reference/beautymap/media/timing.json)

## Results

The retained wrapper run gives SA / DA / HA = 96.9529 / 98.3382 / 97.6407%. The separate historical KITTI-02 Table III experiment matches all nine paper accuracy values at two decimals.

[Original-code paper protocol](https://github.com/p20030920p/SLAM_Learning/blob/535a2780af7ca7eb3aa02f722e1340fe90bc2dcf/docs/KITTI_PAPER_PROTOCOL.md)

## Usage

[Setup and commands](../guides/REPRODUCE.md) · [Sources](../guides/ATTRIBUTION.md)

## Scope

Supplied poses isolate the declared mapping stages. Videos replay saved outputs; complete SLAM, navigation and hardware accuracy remain unverified.
