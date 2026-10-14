# Sim2Real robot mapping and localization test protocol

English | [中文](PROTOCOL.zh-CN.md)

Use the robot model from [Sim2Real-AlgoBench](https://github.com/p20030920p/Sim2Real-AlgoBench). Progressively characterize point-cloud mapping, localization and recovery failures. This is a test design, not a claim that every level has run.

## Robot and sensors

The local upstream revision inspected is `53324d40def0dd753b4a99021b8fe596955a1ecd`. The three-wheel omnidirectional URDF and four STL assets match that revision. [Inspection record](robot-model.json) retains hashes, joints and sensor configuration; it does not establish runtime success.

Preserve body geometry, mass/inertia, wheel joints, collisions and drive interfaces. The native navigation configuration uses `nav2_amcl::OmniMotionModel` and `/omni_drive_controller/odom`; lateral motion must be represented.

| Profile | Cloud source | Scope | State |
| --- | --- | --- | --- |
| Native 2D | Calibrated projection of `/scan` into planar points | 2D mapping/localization; configured 720 beams, 360 degrees, 10 Hz, 0.08–12 m | Source inspected; runtime acceptance remains separate |
| Same-chassis 3D extension | An explicitly mounted 3D LiDAR publishing `PointCloud2` | 3D mapping and method adaptation | V1 static and stationary source checks pass; motion/mapping/localization pending |

The original camera is RGB, not depth. XYZ storage of planar scans does not provide 3D geometry. Version any added sensor, extrinsics, URDF and bridge independently. Native-paper reproduction continues using author data.

V1 uses 720×16 beams, 30-degree vertical FOV, 10 Hz and 0.08–12 m range, mounted 0.30 m above `base_link`. It adds a 0.05 kg sensor assembly; native chassis/sensor elements are preserved, while total assembly mass increases. [URDF](../../config/robot_profiles/omni-3d-v1/omni_car_lidar3d.urdf) · [Bridge](../../config/robot_profiles/omni-3d-v1/bridge_sensors.yaml) · [Profile/checks](../../config/robot_profiles/omni-3d-v1/profile.json). `/points` bridges `/lidar_3d/points`; do not assume point timestamps or an original IMU.

```bash
python3 src/scripts/testing/create_robot_profile.py \
  --upstream-root /root/projects/Sim2Real-AlgoBench
gz sdf -p config/robot_profiles/omni-3d-v1/omni_car_lidar3d.urdf
```

Use the upstream installed description/control packages. These generate/parse the profile rather than completing runtime testing or recording.

Stationary source check (ROS Jazzy, Gazebo Harmonic, `ros_gz_bridge`, Xvfb and the built upstream workspace):

```bash
bash src/scripts/testing/verify_3d_source.sh
```

[Measured record](t0-3d-source.json): 15 frames, each with 720×16 finite points and `x/y/z/intensity/ring` fields; the final Z span is about 1.88 m and the simulation-time rate about 10.01 Hz. This validates the stationary 3D source, while wall-time rate, motion distortion, mapping and localization remain untested. Model, harness and world hashes bind the record. Retain failed attempts caused by [mesh resource resolution](t0-3d-source-attempt1.json) and [controller initialization order](t0-3d-source-attempt2.json).

## Runtime acceptance

Measure actual rates, valid point counts, range/FOV, transforms, timestamps, wheel/lateral motion, collisions and stopping. Save running-node parameters and simulation/wall-time ratio. Treat rendering failures separately from topic-rate health.

Algorithms use sensor observations. Gazebo truth evaluates results and annotates faults; world geometry must not fill unobserved map regions or supply localization answers.

## Three test chains

| Chain | Controlled input | Question |
| --- | --- | --- |
| A Supplied-pose cloud mapping | Same raw points/poses, raw versus paper map processing | Dynamic traces removed versus valid static structure lost |
| B Fixed-map localization | Independent mapping A and test B; replay common B across maps/localizers | Effects of map quality, observation model and environmental change |
| C Estimated-pose mapping and SLAM | Algorithm estimates motion while building the map | Interaction of registration, pose drift and map corruption |

A is controlled mapping, B localization, C their coupled estimation. Separate 2D/3D and native/adapted configurations. Disclose geometric projections and information loss when a 3D map supplies 2D localization.

## Progressive test order

| Stage | Intervention | Mapping observation | Localization observation |
| --- | --- | --- | --- |
| T0 Interfaces/calibration | Stationary, forward, rotation, lateral motion | Frames, motion distortion, synchronization | Pose/odometry agreement; engineering faults first |
| T1 Rich static geometry | Short then complete routes; independent mapping/test | Preservation, completeness, alignment | Normal accuracy and availability |
| T2 Moving objects | Increase object count on a fixed route | Traces and static deletions | Outliers, drift, failure incidence |
| T3 Temporary occlusion | Fixed count, longer occlusion, then removal | Loss of usable structure | Failure during occlusion and recovery after removal |
| T4 Geometric degradation | Longer/repetitive corridors, fixed sensor; then rich structure | Weak-direction map distortion | Directional drift and recovery after constraints return |
| T5 Persistent change | Alter furniture/partitions after freezing the map | Old/new structure conflict | Failure and recovery against the stale map |
| T6 Combined stress | Combine factors after individual characterization | Compounded errors | Strategy boundaries and incorrect recovery |

This is a progression of tests, not a presumed cross-category difficulty ranking. Increase one factor per family and measure actual difficulty. Beam count, range, FOV and noise are separate sensor factors.

## Change and fault events

Change the test world after mapping. Log moved/added/removed structures and the changes actually visible from the robot; global map-change percentage does not replace scan-visible change. Map-file editing is a separate error control.

Cross each environment with no injection, initial-belief offsets and physical kidnapping. Check whether odometry reveals physical relocation. Log occlusion removal or return to informative geometry. Report both fault-to-recovery time and information-return-to-recovery time. Persistent changes need a specified remaining stable region and deadline instead.

## Evaluation and controls

| Object | Metrics |
| --- | --- |
| Cloud/map | Static preservation, dynamic traces, observed-region geometric error/completeness; original paper scores separately |
| Localization | Full-time position/orientation error, directional drift and failure incidence, including initialization/recovery |
| Recovery | Sustained successes/all failed episodes, unrecovered episodes, latency, incorrect recovery, recurrence, human interventions |
| Normal-operation cost | Unnecessary resets, unavailable time and nominal accuracy |
| Resources | Actual latency, CPU/GPU, memory, particles/points; training, mapping and online localization separately |

Validate source-point labels and reference geometry. Score completeness over observed regions and retain the unprocessed baseline. Share data/routes/seeds/fault timing for passive comparisons. Freeze thresholds on validation data, retain every trial and deadline-censored failure, and disclose alignment/scoring coordinates.

Active motion changes observations and requires separate closed-loop comparisons. Check native protocol, training budget and adapter correctness before interpreting poor transferred performance.

## Deliverables

Native reproduction evidence belongs in `results/reference/<method>/`. Raw robot recordings remain in ignored `results/runs/robot-tests/`; accepted lightweight reports/maps/media belong in `results/robot-tests/reference/`.

Log upstream revisions, robot/sensor hashes, factors, routes, fault/information-return times, input hashes, algorithm/training settings, seeds, exit status and outputs. Label live recordings versus data replays and preserve negative results.

The first deliverable is **author-code reproduction + staged mapping/localization tests + evidence-based analysis of failure and recovery**. Choose a recovery strategy from that evidence.
