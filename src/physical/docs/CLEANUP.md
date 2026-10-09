# Branch organization

English | [中文](CLEANUP.zh-CN.md)

The branch consolidates daily entry points while preserving raw recordings, earlier failures and diagnostic tools.

## 1. Layout

| Location | Purpose |
| --- | --- |
| `scripts/` | Capture, ROS bridge, algorithms, exports and audits |
| `configs/rviz/` | Current camera raw/odom/map and LiDAR raw/odom views |
| `docs/` | Current guides |
| `docs/archive/` | Historical experiments and old procedures |
| `evidence/` | Lightweight numerical records |

`start_live.ps1` is the daily entry. Existing usage/walkthrough paths link to current guides and history. Diagnostic scripts remain available for raw SDK, geometry, IMU, timing, small-map and semantic-loader checks; they are not the first daily step.

## 2. Preserved boundaries

Raw data, environments and caches were not batch-deleted. Original errors were not reclassified as success. Loader checks do not run semantic models; host receipt matching is not calibration or fusion. This documentation edit changes no algorithm or environment and does not merge main. [Detailed script roles](CLEANUP.zh-CN.md).
