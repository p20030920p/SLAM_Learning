# Optional physical validation

English | [中文](REAL_WORLD.zh-CN.md)

Hardware is a follow-up to the room2 decision, not evidence confirming H1. Current acquisition, failed trials and operating instructions live on the [hardware branch](https://github.com/p20030920p/SLAM_Learning/tree/notes/personal-study-guide-20261008/src/physical). The connected depth device was identified as D435 without IMU; L2 is tested separately. No mobile robot is required.

## One fixed-sensor session

Use a stable background, a chair, two similar boxes, an occlusion board and a fixed phone showing the event timeline. Assign physical IDs and measured positions before running algorithms. Keep annotation-only markers out of algorithm inputs.

| Event | Controlled change | Evaluate |
| --- | --- | --- |
| Static | Repeat the same view | False removal and baseline identity/query errors |
| Occluded | Hide one unchanged object | Wrong deletion and unsupported stale answers |
| Removed | Remove an object, observe its former space | Removal recall and stale-coordinate duration |
| Moved | Move one marked object | Old/new target coordinates, duplicates and mixed IDs |

Record raw observations, calibration, depth scale, timestamps, SDK versions and event timing. Sensor images and point clouds establish acquisition, not semantic quality. The [branch recording guide](https://github.com/p20030920p/SLAM_Learning/blob/30ccf1b4299e1d301740423661abaa91bb047573/docs/SIMPLE_RECORDING.md) covers full execution and same-recording replay.

## Test the same correction question

After the baseline works, reuse identical observations/features and compare exact geometry correction with fixed versus recomputed associations, including threshold and visibility controls. An injected correction tests controlled sensitivity; actual odometry-error claims require an independent reference. Do not equate the two.

Score physical-instance recovery and category queries separately, along with identity errors, actual candidates/points, correction latency and peak memory. Unlabelled candidates are unknown. Fixed sensors need no IMU; handheld and cross-device fusion require separate pose/calibration validation.

Only design bounded replay if the [room2 decision gate](../research/PLAN.md) supports it. Independent labels and real change events are still needed for confirmation. Preserve full collection/execution videos; label saved-map viewing as replay. [Main recording scope](RECORDING.md).

The [earlier detailed protocol](https://github.com/p20030920p/SLAM_Learning/blob/dfd4a05f02352d32b4f0a2bf522e189708c9e2b2/docs/REAL_WORLD.md) remains in Git history; current device operations are maintained on the hardware branch.
