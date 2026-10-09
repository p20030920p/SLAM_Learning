# DUFOMap

English | [中文](dufomap.zh-CN.md)

**KITTI-00, 141 LiDAR scans.** Observed free space identifies dynamic points; pose margins protect static geometry.

![DUFOMap](../../results/reference/dufomap/media/preview.gif)

[MP4](../../results/reference/dufomap/media/replay/replay.mp4) · [Run](../../results/reference/dufomap/runs/dufomap-wsl/record.json) · [Timing](../../results/reference/dufomap/media/timing.json)

## Results

The retained wrapper run gives SA / DA / AA = 97.9798 / 98.7029 / 98.3407%. The separate original C++ Table IV experiment matches all 15 paper accuracy values at two decimals.

[Original-code paper protocol](https://github.com/p20030920p/SLAM_Learning/blob/535a2780af7ca7eb3aa02f722e1340fe90bc2dcf/docs/DUFOMAP_TABLE4.md)

## Usage

[Setup and commands](../guides/REPRODUCE.md) · [Sources](../guides/ATTRIBUTION.md)

## Scope

Supplied poses isolate the declared mapping stages. Videos replay saved outputs; complete SLAM, navigation and hardware accuracy remain unverified.
