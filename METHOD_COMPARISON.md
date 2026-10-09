# Common scene experiments across method repositories

English | [中文](METHOD_COMPARISON.zh-CN.md)

Use a fixed room, controlled events and frozen recordings to compare map cleaning and semantic targets in separate task groups. Then test how historical pose corrections affect map decisions. The four mapping cores consume supplied poses; trajectory accuracy follows the separate [hardware test plan](docs/TEST_PLAN.md).

This is an experiment design. Existing streaming, odometry videos and loader checks are not quality results for this protocol.

## 1. Background and objectives

A box can be occluded, removed or moved. A localization backend can also revise historical sensor poses. Both changes affect spatial correspondence, stable geometry and the validity of queried target coordinates.

The common chain is **posed observations → spatial correspondence → map decisions → usable targets**. DUFOMap and BeautyMap clean geometry; ConceptGraphs and HOV-SG build semantic representations. Comparison has three levels:

| Level | Objective | Supported conclusion |
| --- | --- | --- |
| Input checks | Match units, calibration, poses and accepted observations | Whether comparison can begin |
| Same-task comparison | Compare LiDAR cleaning separately from RGB-D target quality | Quality and cost for this scene and budget |
| Mechanism test | Deliver identical historical corrections; compare simple protection, geometry correction and reassociation | Whether reassociation addresses a remaining recovery gap |

Candidate hypothesis: reassociation recovers more valid targets at the same candidate budget when pose correction changes correspondence. Simple thresholds, geometry correction or later observations catching up weakens this claim. A physical recording might not induce enough association errors; report that outcome too.

The main homepage now introduces the background and H1. Its comparison GIFs, execution counts and scores from different datasets remain reproduction evidence, not a four-method leaderboard.

## 2. Lessons from Aligning Physics

[Aligning_Physics](https://github.com/Turf1Ctkk/Aligning_Physics/blob/220e1a8997d16d819797de3badd8e59c96cb0be3/docs/experimental_protocol.md) controls a G1/IsaacGym dynamics difference, splits data by parent rollout and separates replay from deployment evaluation. Borrow shared conditions, parent-recording splits, explicit budgets and failure retention; substitute scene events or pose perturbations for the dynamics mismatch.

It studies humanoid calibration and control, so it is not a D435/L2 SLAM baseline. Its [method documentation](https://github.com/Turf1Ctkk/Aligning_Physics/blob/220e1a8997d16d819797de3badd8e59c96cb0be3/docs/methods.md) discloses adaptation, data and rate differences. A common background still requires an audit of comparison conditions.

## 3. Physical setting and shared input

Start with fixed sensors, a wall corner, table and stable background. Current objects are a box, cup and paper notebook; follow the [walkthrough](docs/TABLETOP_WALKTHROUGH.md). Add two similar boxes with independent physical IDs for identity confusion. Start around 1–2 m, subject to valid depth, LiDAR returns and object resolution. Record reflective/transparent cups, illumination and exposure. Exclude the notebook from static support while it serves as the occluder.

Require a genuine fixed-sensor declaration, layout photos, object positions and actual event times. Formal geometry evaluation needs independently measured anchors and measurement uncertainty. An independent phone recording can document the sensor and events. Algorithm estimates are not ground truth; unreferenced ranges are readings only.

| Group | Must match | Differences to disclose |
| --- | --- | --- |
| DUFOMap / BeautyMap | L2 raw file, official decoding, 50-line groups, observation IDs, origins, poses and evaluation labels | Native algorithms, parameters, grids and implementation; room adaptations reported separately |
| ConceptGraphs / HOV-SG | D435 RGB-D, SDK alignment, metric depth, color intrinsics, observation IDs, poses, targets and queries | Native frontends, fusion and representations; shared-feature variants reported separately |
| Within-method controls | Observations, cached masks/features, perturbations, correction contents and delivery order | Predeclared protection, association or replay strategy |

The sensors share a scene but differ in field of view and visible support. Report modalities separately. The actual camera is **D435 without IMU**. L2 device-time scaling near 2 remains unresolved; shared timing and extrinsics are not validated. Start with independently confirmed fixed recordings and identity relative poses. Single-view conclusions concern visible surfaces only.

Tune only on validation sessions. Preserve BeautyMap's original small-map boundary failure and report padding separately. Its native 1 m grid may not resolve a 30 cm event: check observability, then freeze room parameters. Matching a numeric threshold across different algorithms is not a fairness requirement.

Keep independent repository environments and pinned commits. Adapters consume the same session manifest and feed a common evaluator. Run serially on the same computer, recording CPU threads, GPU, software and models; separate initialization from steady-state time. Disclose adapter and algorithm changes separately rather than hiding failures in modified author caches.

## 4. Events and feasible scale

Record each event separately for 80 seconds: baseline 0–20 s, action 20–25 s, hold 25–60 s, restore 60–80 s. Annotate actual transitions. The static control stays unchanged. Replay one raw recording for all methods within its modality.

| Event | Action | Main observation |
| --- | --- | --- |
| Static | Sensor and objects remain fixed | Background deletion and target fragmentation |
| Occlusion | Hide a stationary box behind a board | Confusing hidden with removed; recovery after uncovering |
| Removal | Remove the box while exposing its former space and background | Map update and stale query location |
| Movement | Move a box along an independently measured 30 cm mark | New location, stale location and identity |

Out-of-view former space and a blocked stable background are failure controls, excluded from visible-removal denominators. Hold illumination fixed first; normal/low light and projector settings become separate paired factors.

Pilot: one session per event, four sessions and 5 min 20 s per modality. Formal exploration: three validation and five test sessions per event, 32 sessions and 42 min 40 s per modality, excluding pilots. This size does not guarantee statistical power. Change test layouts and split whole acquisitions; adjacent frames from one recording cannot straddle validation and test.

First run both semantic cores on the same eight frames and inspect actual outputs and memory. Then attempt 40 observations per event at `t=0,2,…,78 s`. Select the nearest valid frame/complete LiDAR group and retain actual timestamps and offsets. If either method cannot process 40, freeze a common feasible subset and disclose the reduction. Report larger native runs separately. Never silently remove difficult observations or treat eight loaded frames as a quality result.

For current L2 selection, use explicitly labeled host-receipt elapsed time and retain original device timestamps and QPC provenance. This supports fixed-sensor replay selection, not exposure/firing synchronization. Do not use it for moving-scan deskew or fusion before resolving device timing.

## 5. Metrics and expected video

Show raw input, method output, independent event/labels and a metric timeline. Match viewpoint, point size, colors, frame IDs and query text. Identify GT coloring and distinguish execution, prefix reruns and saved-output playback.

| Method | Desired effect | Limits and failures |
| --- | --- | --- |
| D435 preview | Recognizable RGB, approximately consistent depth edges and stereo disparity | Invalid depth and reflective holes can occur; record blur, saturation and large invalid regions |
| L2 preview | Walls, floor and objects refresh across scan groups | Changing scan coverage is normal; motion without deskew can smear geometry |
| DUFOMap / BeautyMap | Reduced moving support with stable walls retained | Deleted points are not automatically correct; batch cleaning does not imply immediate removal detection |
| ConceptGraphs | Masks, object clouds and query candidates; consistent physical identities where supported | Misses, duplicates and mixed objects are possible; highlights do not prove query success |
| HOV-SG core | Segments, feature map and shared text queries | Current core is not full hierarchical navigation; segment indices are not temporal object identities |
| Pose correction | Geometry, object membership and query validity update together | Aligned walls can coexist with mixed objects; unavailable identity interfaces are not applicable |

| Metric | Definition |
| --- | --- |
| SA / DA | Retained stable-background support / removed independently labeled moving support. Freeze labeling before runs; separate transitions from static intervals. Use identical 5 cm map-neighbor scoring for both LiDAR methods, reporting ambiguity and label coverage. Report direct membership separately when traceable point IDs exist |
| Static deletion / visible-removal recall | Deleted visible static support / eligible support; correctly detected eligible removal events / eligible removal events. Event recall requires an implemented decision interface |
| Surface recovery | Coverage of independently labeled visible surfaces within 10 cm. Recovery requires coverage ≥20% and projection precision ≥50%; retain continuous scores |
| Query quality | Frozen texts and targets; top-1 hits / all queries, answer coverage, errors and abstention. Compare common surface targets, not object counts against segment counts |
| Identity / coordinates | Fragments per physical ID, mixed physical IDs, designated surface-anchor error and reference uncertainty. Compare identity only where compatible interfaces exist |
| Freshness / cost | Event completion to stale-coordinate expiry; correction delivery to output update; candidates, peak RSS/GPU memory, runtime, processed coverage, exit status and failures |

Initial engineering goals from the [integration guide](docs/MAIN_INTEGRATION.md) are static deletion <5%, visible-removal recall >80% and designated anchor error <10 cm. They remain unverified. Unsupported event capabilities are not passes. Report coverage, recall and staleness together: abstention or permanent retention can improve a single score misleadingly.

Batch methods may be rerun at fixed prefixes `0–20/0–30/0–60/0–80 s`. This diagnoses state changes; data-time differences are not online latency. Online response requires a real incremental decision interface. Historical moving-point cleaning and current object-removal detection are distinct tasks.

## 6. Historical correction controls

Use a separate **40-observation, 1 Hz** sequence from a confirmed fixed recording. Debug static identities first, then cross event conditions. Observations 0–7 have zero bias; 8–15 receive a world-x bias increasing from 0 to 10 cm; remaining observations have zero bias. Deliver identical historical corrections after processing observation index 16, 24 or 36. Preserve the zero-bias reference and actual perturbation RMS.

This is a controlled software stress test, not measured localization noise or a real loop closure. A 16-observation source cache then retains indices 1–16, 9–24 or 21–36: required sources are respectively all retained, partly evicted or all evicted. Flag insufficient budgets explicitly; do not silently access full history.

| Control | Behavior | Physical implementation status |
| --- | --- | --- |
| B0 | Keep perturbed historical decisions; ignore correction | Adapter pending |
| B1 | Frozen validation-selected thresholds/visibility protection | Concrete rules must be implemented and disclosed |
| B2 | Correct historical geometry, freeze membership/fusion associations | Requires original observation provenance; moving the whole map is insufficient |
| B5 | Rebuild full corrected history and reassociate | Separate unconstrained reference, with measured cost; neither physical truth nor a guaranteed performance bound |
| B3 / B4 | Independent variance / shared-pose handling and bounded reassociation | Uncertainty calibration and prototypes pending |

Hold the frontend fixed within each semantic method. A shared SAM/CLIP frontend is a controlled variant with disclosed adapters. Historical corrections and temporal identities require explicit support; static mapping does not imply these capabilities.

Compare candidate caps 25/50/100 and an uncapped reference. Match surface coverage, change recall and target validity at each operating point; measure memory and replay cost. Equal candidate caps do not imply equal memory. First determine whether B2 and B5 retain a recovery gap. All arms receive identical later observations.

Only a persistent B5 advantage over all simple controls at finite candidate caps, without extra duplicate/mixed targets, motivates a bounded prototype. B5 still accesses full source history and cannot establish bounded-cache effectiveness. Independent sessions are still needed; multiple seeds of one recording cannot establish H1. This proposal does not replace the research branch's frozen room2 decision rule or its analysis.

## 7. Readiness and execution order

| Stage | Existing evidence | Next step |
| --- | --- | --- |
| Reception | Four D435 streams and L2 point/IMU data; concurrent low-light videos | Recheck camera startup/depth and explain L2 timing; concurrent streams are not fusion |
| Author input | DUFOMap fixed input ran; BeautyMap original boundary failure with a padded diagnostic; semantic loaders passed 8/8 | Run both actual semantic cores on the same eight frames; resolve or isolate the boundary issue |
| Fair quality comparison | Existing media lacks the complete event/independent-label protocol | Four pilots, then freeze inputs, parameters and evaluation |
| Mechanism | Synthetic-data research exists; physical adapters pending | B0/B1/B2/B5 first; B3/B4 only after a remaining gap |

The older 60 s camera recording contains background motion and is exploratory. New post-fall previews lack a confirmed fixed declaration. Projector on/off/on checks contain neither four controlled events nor a separate L2-off control; they cannot populate the formal comparison table.

Reuse the [camera](docs/CAMERA_GUIDE.md), [LiDAR](docs/LIDAR_GUIDE.md), [recording](docs/SIMPLE_RECORDING.md) and [RGB-D input](docs/RGBD_MAIN_INPUT.md) guides. Replay and adapter work precede new physical event collection. This protocol has not started another capture or heavy experiment.

Each run manifest records parent recording/hash, split, events/actual times, selected IDs/times, calibration and pose provenance, repository commits, native/adapted mode, configuration/model hashes, seeds, budgets, command, exit code, outputs and failure reason. GT remains evaluation-only; frontend predictions are not independent labels.

Report paired session differences and all failures. Points, frames and seeds from one recording are not independent acquisitions. Freeze inputs and parameters before inspecting test outcomes. Raw recordings, indoor video and weights stay in ignored `data/` and `.cache/`; commit only the protocol, adapters and lightweight evidence. Main remains unchanged; follow existing [integration gates](docs/MAIN_INTEGRATION.md) without merging this branch.

## 8. Design provenance

Main was inspected at `dfd4a05f02352d32b4f0a2bf522e189708c9e2b2`. Its [study](https://github.com/p20030920p/SLAM_Learning/blob/dfd4a05f02352d32b4f0a2bf522e189708c9e2b2/docs/STUDY.md), [paired protocol](https://github.com/p20030920p/SLAM_Learning/blob/dfd4a05f02352d32b4f0a2bf522e189708c9e2b2/docs/PAIRED_PROTOCOL.md) and [physical design](https://github.com/p20030920p/SLAM_Learning/blob/dfd4a05f02352d32b4f0a2bf522e189708c9e2b2/docs/REAL_WORLD.md) supply the mechanism and events. The latter is a historical plan; actual device identity and completed hardware work follow this branch's [latest checks](docs/POSTFALL_LOWLIGHT.md). The physical sampling budget and execution stages above are proposed, not measured results.
