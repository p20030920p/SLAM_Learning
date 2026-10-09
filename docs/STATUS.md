# Execution status

English | [中文](STATUS.zh-CN.md)

Snapshot: 9 October 2026, Moscow. Runtime: `/home/qzl/projects/SLAM_Author_Originals`. Completed runs and queued work are separate.

## 1. Completed results

| Method | Scope | Result |
| --- | --- | --- |
| DUFOMap / BeautyMap | Four labelled releases, 1,997 scans each | Original entries and author evaluation completed |
| DUFOMap Table IV | Five settings | All 15 SA/DA/AA entries match paper rounding |
| BeautyMap Table III | Historical KITTI-02, three grid sizes | All nine SA/DA/HA entries match paper rounding |
| ConceptGraphs SAM-only | room0 / office0 / office1 | mIoU 21.3460 / 20.4157 / 14.9755% |
| ConceptGraphs Detect | room0 / office0 | mIoU 25.5987 / 17.5151% |
| HOV-SG home variant | room0, 20 frames | mIoU 34.7500%, F-mIoU 62.8725% |

The labelled releases contain 141 / 321 / 575 / 960 scans. They are released intervals, not complete KITTI sequences. BeautyMap on AV2 is an additional transfer experiment.

| Release | DUFOMap SA / DA % | BeautyMap SA / DA % |
| --- | ---: | ---: |
| 00 | 97.9635 / 98.7196 | 96.9529 / 98.3382 |
| 05 | 97.3035 / 96.7986 | 96.7933 / 98.2248 |
| AV2 | 96.6651 / 88.8985 | 92.4013 / 85.1671 |
| Semi-indoor | 99.6373 / 83.0049 | 94.7785 / 90.4048 |

![Author LiDAR scores](../evidence/figures/lidar-scores.png)

[Scoring log](../evidence/runs/released-lidar-01/scores/run.log) · [Figure provenance](../evidence/figures/lidar-scores.json). AA is geometric and HA harmonic. The author PCL exporter uses 0.05 m. BeautyMap consumes prior XYZ geometry, not GT labels for cleaning.

## 2. What changes the interpretation

Representation and scoring thresholds strongly change DUFOMap Python scores. [Output audit](DUFOMAP_OUTPUT_AUDIT.md). Current and historical KITTI preprocessing also differ; keep their results separate. [Input audit](DATA_ACCESS.md) · [Selected intervals](KITTI_SELECTED_RESULTS.md) · [Historical protocol](KITTI_PAPER_PROTOCOL.md).

Unlabelled twofloor and campus runs processed 3,305 and 18 scans. Their finite outputs and hashes establish execution, not cleaning accuracy.

## 3. Failures and pending work

Preserve the g++-10 failure, interrupted SAM runs, confirmed cgroup OOMs and timeout records. A partial frontend or map is not a completed evaluation. [Environment](ENVIRONMENT.md) · [GPU recovery](CG_GPU_RECOVERY.md).

Queue 09 uses a disclosed sequential-residency Detect variant; HOV default 06 and follower 08 wait. The three-frame compatibility check adds no semantic score. HOV's completed 20-frame variant does not complete its default 200-frame run.

LLaVA base weights, original GPT-4 stages, full semantic benchmarks and robot navigation remain incomplete. These supplied-pose runs measure no ATE/RPE or H1 benefit. The [Chinese record](STATUS.zh-CN.md) retains the detailed chronological diagnostics.
