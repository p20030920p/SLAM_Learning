# New author-workflow evidence and its research limits

English · [中文](AUTHOR_RESULTS_ANALYSIS.zh-CN.md) · [Index](README.md)

This 2026-10-08 addition concerns the independent [author-originals branch](https://github.com/p20030920p/SLAM_Learning/tree/reproduce/author-originals). Earlier tables in this study-guide branch remain historical subset and exploratory records. Do not concatenate the two experiments. Consult the [live scope](https://github.com/p20030920p/SLAM_Learning/blob/reproduce/author-originals/docs/STATUS.zh-CN.md) for completed versus queued stages.

Both original LiDAR entries and the author's PCL export/scoring finished all four public labeled releases: 1997 scans per method. These are single runs, percentages, without repeatability intervals.

| Release | DUFOMap SA / DA | BeautyMap SA / DA |
|---|---:|---:|
| 00, 141 scans | 97.9635 / 98.7196 | 96.9529 / 98.3382 |
| 05, 321 scans | 97.3035 / 96.7986 | 96.7933 / 98.2248 |
| AV2, 575 scans | 96.6651 / 88.8985 | 92.4013 / 85.1671 |
| Semi-indoor, 960 scans | 99.6373 / 83.0049 | 94.7785 / 90.4048 |

[Immutable scoring log](https://github.com/p20030920p/SLAM_Learning/blob/cf21494/evidence/runs/released-lidar-01/scores/run.log), [parameters and figure](https://github.com/p20030920p/SLAM_Learning/blob/cf21494/docs/STATUS.zh-CN.md). Public releases are not complete KITTI sequences. BeautyMap AV2 transfers the outdoor example parameters, not a verified paper-specific configuration.

Semi-indoor results expose a static-preservation/dynamic-removal tradeoff. Compare false deletion at matched change recall; a composite score conceals error types. Both methods consume supplied poses, so these runs establish no ATE/RPE or online localization gain. BeautyMap consumes prior XYZ geometry; the GT label channel is not used in cleaning decisions. DUFOMap's voxel-center output can lose nearest-neighbor matches at a tighter threshold, which must not be interpreted directly as static-point deletion.

ConceptGraphs' complete 400-sample room0 frontend is validated. Disabling optional animation snapshots allowed all 400 associations to finish, but final serialization still hit a confirmed memory-cgroup OOM. A retry now has additional temporary swap. HOV-SG finished 200/200 native-resolution feature extractions, then hit a confirmed cgroup OOM during hierarchical mask merging before final feature-map saving. These resource failures are not semantic-accuracy failures or evidence for H1. No final map or semantic score is claimed yet. Replica semantic mapping does not establish HM3D hierarchy performance.

A concise motivation is: original cleaning works, with scene-dependent tradeoffs; what remains untested is recovery of object correspondence and query coordinates after delayed pose correction. Test geometry correction, reassociation and bounded replay on identical observations, measuring change recall, query coverage, stale duration, latency and memory. Reject an additional reassociation mechanism if geometry-only correction matches full replay; reject apparent deletion gains obtained by retaining stale targets. These new baselines did not run H1 or prove a shared dominant failure mechanism.

Keep each semantic method's native GT support, ignored classes and interpolation protocol explicit; their native mIoU numbers do not support direct cross-method ranking. [Protocol comparison](https://github.com/p20030920p/SLAM_Learning/blob/reproduce/author-originals/docs/SCOPE.zh-CN.md), [existing analysis and rejection controls](LAB_ANALYSIS.md).
