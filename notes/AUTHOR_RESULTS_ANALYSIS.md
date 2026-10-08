# New author-workflow evidence and its research limits

English · [中文](AUTHOR_RESULTS_ANALYSIS.zh-CN.md) · [Index](README.md)

Updated 2026-10-09. This addition concerns the independent [author-originals branch](https://github.com/p20030920p/SLAM_Learning/tree/reproduce/author-originals). Earlier tables in this study-guide branch remain historical subset and exploratory records. Do not concatenate the two experiments. Consult the [live scope](https://github.com/p20030920p/SLAM_Learning/blob/reproduce/author-originals/docs/STATUS.zh-CN.md) for completed versus queued stages.

Both original LiDAR entries and the author's PCL export/scoring finished all four public labeled releases: 1997 scans per method. These are single runs, percentages, without repeatability intervals.

| Release | DUFOMap SA / DA | BeautyMap SA / DA |
|---|---:|---:|
| 00, 141 scans | 97.9635 / 98.7196 | 96.9529 / 98.3382 |
| 05, 321 scans | 97.3035 / 96.7986 | 96.7933 / 98.2248 |
| AV2, 575 scans | 96.6651 / 88.8985 | 92.4013 / 85.1671 |
| Semi-indoor, 960 scans | 99.6373 / 83.0049 | 94.7785 / 90.4048 |

[Immutable scoring log](https://github.com/p20030920p/SLAM_Learning/blob/cf21494/evidence/runs/released-lidar-01/scores/run.log), [parameters and figure](https://github.com/p20030920p/SLAM_Learning/blob/cf21494/docs/STATUS.zh-CN.md). The paper tables use selected KITTI intervals rather than full sequences. BeautyMap AV2 transfers the outdoor example parameters as an additional experiment outside that paper's reported scenes.

The new [DUFOMap Table IV ablation](https://github.com/p20030920p/SLAM_Learning/blob/reproduce/author-originals/docs/DUFOMAP_TABLE4.zh-CN.md) matches all five SA/DA/AA rows at the paper's two-decimal precision. SA changes from 14.89% without the error margins to 97.96% with full settings. Error compensation is therefore an existing strong baseline, not a new contribution. This does not test H1: recovery of object correspondence and query coordinates after delayed correction still needs its own experiment.

Semi-indoor results expose a static-preservation/dynamic-removal tradeoff. Compare false deletion at matched change recall; a composite score conceals error types. Both methods consume supplied poses, so these runs establish no ATE/RPE or online localization gain. BeautyMap consumes prior XYZ geometry; the GT label channel is not used in cleaning decisions. DUFOMap's voxel-center output can lose nearest-neighbor matches at a tighter threshold, which must not be interpreted directly as static-point deletion.

ConceptGraphs' complete room0 frontend, original mapping and RGB reference fusion have now succeeded after the temporary-swap retry. The validated postprocessed map has 77 object records; this count is not instance accuracy. Original semantic evaluation failed because chamferdist lacked CUDA support; the unchanged dependency has been rebuilt, with real GPU KNN and evaluation queued after HOV-SG. No semantic score is claimed. HOV-SG previously finished 200/200 native-resolution feature extractions, then hit a confirmed cgroup OOM before final feature-map saving; its complete retry is running. These execution failures are not semantic-accuracy failures or evidence for H1. Replica semantic mapping does not establish HM3D hierarchy performance.

A [60-second original viewer recording](https://github.com/p20030920p/SLAM_Learning/blob/reproduce/author-originals/evidence/videos/conceptgraphs-room0-original-window.mp4) now shows the verified map with RGB/instance colors and orbit controls. Display color changes are not an accuracy comparison.

Keep resource issues separate. The pinned HOV-SG [merge function](https://github.com/hovsg/HOV-SG/blob/d6e65a53c8be6faec3f01f00d1644d967f89e605/hovsg/utils/graph_utils.py#L373) accepts `voxel_size` but appends points and runs DBSCAN without voxel downsampling inside that function. This suggests a factor to investigate using per-round point counts, RAM/swap peaks and stage time; it does not establish the sole OOM cause or support H1. SAM microbatching reduces GPU pressure without guaranteeing that CPU mask fusion fits.

New original KITTI inputs expose another protocol issue: all 141 scans reconstructed by the current author's 50m preprocessing differ in point count from the older 00 release, and the supplied poses differ too. [Download and protocol records](https://github.com/p20030920p/SLAM_Learning/blob/reproduce/author-originals/docs/DATA_ACCESS.zh-CN.md). Report new 01/02 runs separately; these differences alone establish neither algorithm degradation, a refutation of the paper, nor H1 effectiveness.

On the same new 02 input, DUFOMap SA/DA is 68.6114/89.2862%, versus default BeautyMap 83.4254/84.6594%. [Original scores and three cell sizes](https://github.com/p20030920p/SLAM_Learning/blob/reproduce/author-originals/docs/KITTI_SELECTED_RESULTS.zh-CN.md). This makes static preservation a useful target for paired interventions, keeping observations/evaluation fixed and varying poses, visibility or parameters separately. Cross-scene scores alone do not identify the cause.

A concise motivation is: original cleaning works, with scene-dependent tradeoffs; what remains untested is recovery of object correspondence and query coordinates after delayed pose correction. Test geometry correction, reassociation and bounded replay on identical observations, measuring change recall, query coverage, stale duration, latency and memory. Reject an additional reassociation mechanism if geometry-only correction matches full replay; reject apparent deletion gains obtained by retaining stale targets. These new baselines did not run H1 or prove a shared dominant failure mechanism.

Keep each semantic method's native GT support, ignored classes and interpolation protocol explicit; their native mIoU numbers do not support direct cross-method ranking. [Protocol comparison](https://github.com/p20030920p/SLAM_Learning/blob/reproduce/author-originals/docs/SCOPE.zh-CN.md), [existing analysis and rejection controls](LAB_ANALYSIS.md).
