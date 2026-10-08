# Home validation with D435i and Unitree L2

English | [中文](REAL_WORLD.zh-CN.md)

**No hardware data has been collected yet.** Use this Windows/WSL computer, D435i, L2, tripods, a chair, boxes, an occlusion board, tape measure and a phone to test map decisions and target validity. Test each fixed sensor separately before handheld revisits; no mobile robot is required.

## Three distinguishable questions

| Question | Intervention | Main criterion |
| --- | --- | --- |
| Is visibility mistaken for change? | Fixed sensor; static, occluded, removed and moved target | False static removal, visible-removal recall and stale-coordinate duration |
| Is pose correction sufficient? | Same observations/features; correct history with associations fixed or recomputed | Surface coverage, identity fragments, coordinate error and recovery time |
| Is bounded H1 worth its cost? | Independent-variance versus shared-pose protection at matched recall, coverage and delay | Risk frontier, memory, replay time and stale-result exposure |

Raw collection can begin immediately. The second and third questions still require hardware-data adapters and candidate modules; current Replica entry points cannot directly consume device recordings. A sensor image or RViz cloud proves acquisition/viewing, not H1.

## Room and independent reference

Include a wall, floor and another plane orientation. Full pose estimation needs independently measured multiple markers or sufficiently observable background; one plane does not constrain all degrees of freedom. Fix markers to the background, not moving targets.

Fix the sensor and initially place targets around 1.5–3 m away, subject to measured depth validity and L2 return density. Assign physical IDs to the chair and two similar boxes. Mark initial and 30 cm translated locations with tape and record measurement uncertainty. A separate fixed phone should see the objects, sensor and session label.

Algorithm-visible anchors are auxiliary inputs shared by applicable baselines. Evaluation-only markers must not leak into inputs. D435i IMU is not position GT. Use identity relative poses for the fixed sensor and record origin/axes per session.

## A Fixed-sensor events

Collect four event types separately for each sensor. Each session lasts 80 seconds: static baseline 0–20, event action 20–25, hold 25–60, restoration and static observation 60–80. Log actual times; moving transitions are separate from completed states.

| Event | Action | Required interpretation |
| --- | --- | --- |
| Static | Nothing moves | Observation noise should not delete or split targets |
| Occluded | Hide the stationary chair behind a board | Hidden/unknown is not absent; restore the same physical ID afterwards |
| Removed | Remove the chair while old space/background remains visible | Evaluate visible-removal recall only with rays/depth reaching the old space |
| Moved | Translate the chair 30 cm along tape | New coordinates become valid; old coordinates become stale |

Add out-of-view and failure controls with most similar boxes moving together while stable background is hidden. Unseen old space is not visible removal. Without anchors, coherent object motion and camera drift may be unidentifiable.

Start with one four-event demonstration per sensor: 5 min 20 s each, for pipeline checking only. For formal exploration, use three validation sessions per event, then freeze and collect five test sessions with a changed layout: 32 sessions or 42 min 40 s per sensor. This does not guarantee statistical power. Do not inspect test outcomes before freezing; statistical units are sessions, not pixels or random seeds.

## B Delayed corrections on identical observations

Extract 40 timestamped observations from a fixed-sensor recording. Hold RGB, depth, calibration, masks and per-mask features fixed. Identity poses are the reference. Observations 0–7 are exact; 8–15 receive a world-x bias ramping from 0 to 10 cm; the remainder are exact. This is a deterministic recovery stress test, not a deployment noise model. Report achieved RMS, extrema and ordering; do not claim sorting isolates correlation.

Deliver the same historical correction at observation 16, 24 or 36, restoring reference poses for 8–15. Fix event order: receive correction before processing the new observation, retaining the previous 16 processed observations. The respective caches are 0–15, 8–23 and 20–35: the first two retain the affected provenance; the last does not. Observation 24 is the boundary at which frame 8 is still retained; correcting after processing the new frame changes that condition. Record ordering and evictions. Fall back to full reconstruction or explicitly return unrecoverable. Cross event conditions with delay, debugging on static clips before freezing settings. Rotation and handheld estimated poses are later factors.

| Comparison | Intervention |
| --- | --- |
| B0 Native core | Preserve original association/fusion and historical decisions |
| B1 Simple protection | Select thresholds/visibility on validation; retain ConceptGraphs threshold 1.0 as a competitor |
| B2 Correct geometry, freeze association | Reproject the same cached observations with corrected poses but retain previous object membership, isolating geometry correction from reassociation |
| B3 Independent variance | Same provenance cache, budget and commit policy; independent uncertainty controls tentative/committed updates |
| B4 Candidate shared pose | Add shared-pose handling and affected-association replay without stronger front ends or additional labels |
| B5 Oracle full replay | Rebuild all history under corrected poses; report actual time and memory |

Run B0/B1/B2/B5 plus B4-R, changing association replay alone with the same protection rule, to test its value beyond geometry correction. In a second stage, B3 and B4-U use identical replay and differ only in independent/joint uncertainty models. Implement and calibrate the estimator before comparison; known injected covariance is a separate oracle. B5 is a same-core corrected-input reference and still requires independent ground truth evaluation. See the [completed research draft](../notes/OPEN_QUESTION_AND_HYPOTHESIS.zh-CN.md). Provenance and pose versions alone are not demonstrated novelty.

## C Handheld and dual-sensor extensions

After fixed-sensor validation, separately walk a slow 1–2 minute revisit loop with each sensor, starting and ending stationary. Keep estimated odometry separate from independent background/marker reference and report reprojection, depth and reference errors. Preserve L2 point time/ring for deskewing; scanning distortion is not automatically scene motion.

Combine devices only after rigid mounting, extrinsic calibration, timestamp-offset/drift measurement and other-device on/off interference controls. USB/network timestamps and two IMUs do not automatically provide a shared clock or fusion system.

## Metrics and rejection rules

| Metric | Definition |
| --- | --- |
| False static removal / real-removal recall | Lost independently annotated visible static support / detected visible-removal events; point and event denominators remain separate |
| Coverage and identity | Annotated visible-surface coverage within 10 cm; recovery requires at least 20% coverage and 50% visible projection precision; count segments per physical ID |
| Target coordinate error | Distance to an independently measured designated surface anchor, with reference uncertainty; not full-object center or navigation error |
| Staleness and delay | Completed event to old-coordinate invalidation; delivered correction to updated query; log valid, tentative, stale and unrecoverable states |
| Resources | Serial runs on this computer; 16 observations / 512 MiB is a proposed provenance-cache budget only. Measure process RSS, GPU peak and replay time separately |

Select operating points on validation, then report test risk–coverage–delay curves with matched change recall. Reject the corresponding H1 benefit if simple protection reaches the same frontier, B2 explains all recovery, uncertainty is uncalibrated, or fewer deletions merely retain stale targets longer. Abstention reduces coverage; retain out-of-window failures.

## Acquisition and video evidence

Use official RealSense Viewer to record raw RGB/depth/IMU, calibration, depth scale, SDK/firmware versions and hashes. Current documentation uses `.db3`; legacy versions use `.bag`. Choose the installed SDK's format and inspect playback; the extension does not establish IMU completeness. [Official record/playback](https://github.com/realsenseai/librealsense/blob/master/doc/record-and-playback.md).

For L2 pin SDK2/ROS2 and retain all PointCloud2 fields, IMU, point time/ring, actual topics and TF. Official defaults are `unilidar/cloud`, `unilidar/imu` and lidar frame `unilidar_lidar`. The published ROS2 validation environment is Foxy; this host's Humble hardware connection remains unverified. [Official SDK2](https://github.com/unitreerobotics/unilidar_sdk2).

Each session retains raw files, `capture.json`, calibration, `events.csv`, object/visibility labels, reference measurements, logs, screen capture and phone event video. RGB-D/3D clouds and map/target outputs occupy the main screen area; terminal text establishes commands and exit status. Label inference and offline inspection separately. Publish verified lightweight evidence and short clips on main; keep large files local.
