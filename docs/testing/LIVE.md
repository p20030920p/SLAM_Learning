# Native desktop simulation and scoring

2026-10-14: actual Windows Gazebo, RViz2 and Windows Terminal windows, recorded with Windows Graphics Capture. The Sim2Real omnidirectional chassis retains its native 2D sensor and gains the independent 3D profile. Worlds and controllers are disclosed local adaptations, not paper datasets. [中文细节](LIVE.zh-CN.md).

| Scene | Independent mapping A | Localization B | Measured B replay | Evidence |
| --- | --- | --- | --- | --- |
| Static | [MP4](../../results/reference/robot-static-mapping/execution.mp4) | [MP4](../../results/reference/robot-static/execution.mp4) | [MP4](../../results/reference/robot-static/result.mp4) | [Record](../../results/reference/robot-static/record.json) |
| Three moving obstacles | [MP4](../../results/reference/robot-dynamic-mapping/execution.mp4) | [MP4](../../results/reference/robot-dynamic/execution.mp4) | [MP4](../../results/reference/robot-dynamic/result.mp4) | [Record](../../results/reference/robot-dynamic/record.json) |
| Persistent change | Static A reused | [MP4](../../results/reference/robot-large-change/execution.mp4) | [MP4](../../results/reference/robot-large-change/result.mp4) | [Record](../../results/reference/robot-large-change/record.json) |
| Corridor degradation | [MP4](../../results/reference/robot-corridor-mapping/execution.mp4) | [MP4](../../results/reference/robot-degradation/execution.mp4) | [MP4](../../results/reference/robot-degradation/result.mp4) | [Record](../../results/reference/robot-degradation/record.json) |

Execution combines synchronized captures of real application windows; unrelated desktop content is excluded. Gazebo's visible real-time factor reports actual simulation speed; 15fps capture is not algorithm throughput. GIFs sample the full MP4 interval at 5fps without acceleration. `timing.json` records duration/frame checks, and every MP4 is fully decoded.

Replays are labelled `MEASURED RESULT REPLAY`: saved AMCL updates and independent simulator truth, sampled at 8fps of simulation time using the latest saved update. No inference is performed during replay. Capture uses wall time, replay uses simulation time, so durations differ.

## Mapping and method scope

Native slam_toolbox builds a live 2D map. Mapping A records the independent 3D clouds at approximately one scan per simulation second, then selects up to 60 evenly spaced scans. Raw stacking, native DUFOMap and native BeautyMap receive identical provided sensor poses and scans. Their outputs use common observed free rays, a 0.12–1.20m height band, 0.05m cells and one-cell occupied dilation for AMCL maps; no world geometry fills unseen space.

DUFOMap: 0.1m / d_s=0.2 / d_p=1. BeautyMap: range=8m / XY=0.5m / Z=0.2m, disclosed Python-reader and small-map query-border compatibility patch. Working indices receive an empty integer border; original world points remain unchanged. Native logs, patch hashes and retained-point identity checks are saved. These are platform adaptations, not unmodified paper-protocol reproductions. Removed-point counts are not static/dynamic accuracy without validated point labels.

Held-out B starts a fresh simulation. Identical native Nav2 AMCL instances share live scan and wheel-odometry inputs, changing only the frozen maps; dynamic B includes static-A map controls. Corridor stress instances instead receive the disclosed derived scan. Truth goes only to evaluation/display, never AMCL or the odometry-controlled patrol. Settings include OmniMotionModel, 500–2000 particles, up to 60 beams and shared motion/observation parameters. All AMCL TF broadcasts are disabled to avoid interference. RViz displays the Raw frame; terminal and replay show every instance.

Scope: native 2D SLAM/localization plus 3D mapping with provided poses. Full 3D SLAM, per-point motion-distortion scoring and physical-robot tests remain outside these results. See the [layered protocol](PROTOCOL.md).

## How errors are calculated

Every `<case>-samples.csv` retains native AMCL updates, estimates, associated simulator truth and timestamp deltas. Independent Gazebo `Pose_V` selects `omni_car` using its top-level simulation timestamp. Each update matches nearest truth within 0.05 simulation seconds, without SE(2) fitting.

\[
e_i=\sqrt{(\hat{x}_i-x_i)^2+(\hat{y}_i-y_i)^2},\qquad
\mathrm{RMSE}_{xy}=\sqrt{\frac1N\sum_i e_i^2}.
\]

Yaw errors wrap with `atan2(sin(delta), cos(delta))` before RMS and degree conversion. Homepage values use every retained update including initialization; `metrics.json` also reports a window beginning five simulation seconds after the first scored update, sample counts and position P95. Capture starts after live readiness, while scores include initial updates preceding capture. Verification recomputes errors/metrics from poses and checks them against `truth.jsonl`; merely rehashing changed values cannot bypass validation.

One run per condition. Within a condition, all instances receive the same inputs; across conditions, routes, initial beliefs and maps differ, so these are not general algorithm rankings. Earlier homepage values came from another configuration and replay protocol; all 21 actual scored CSVs and recomputation are retained in the [historical audit](../../results/localization/static-dynamic/scored/audit.json), separately from these recordings.

**Position RMSE (cm), all retained native updates including initialization; one run per condition.**

| Condition | Raw + AMCL | DUFOMap + AMCL | BeautyMap + AMCL | Updates per case |
| --- | ---: | ---: | ---: | ---: |
| Pure static | 7.08 | 7.08 | 6.55 | 290 |
| Moving obstacles / dynamic-A maps | 7.31 | 7.10 | 7.28 | 291 |
| Moving obstacles / static-A controls | 6.30 | 6.30 | 6.89 | 291 |
| Persistent change / old static-A maps | 6.25 | 6.25 | 6.16 | 290 |
| Corridor / full-scan controls | 62.64 | 62.64 | 62.64 | 478 |
| Corridor / limited → restored | 73.63 | 73.63 | 73.63 | 478 |

The homepage shows separate method GIFs; the [recording index](../../demo/recording-index.json) connects local video names to these rows.

## Corridor restoration

Two 20m parallel walls and end walls; A/B geometry matches. Initial estimate offset: X=1m, Y=0.15m, yaw=0.12rad. Other scenes use X=0.25m. Full instances retain 720 beams / 360° / 12m. Stress instances derive 72 beams / 240° / 3.5m from that same sensor, restoring the original observations after 50 simulation seconds. No artificial measurement noise; the 3D profile stays full. This combines geometry and beam/FOV/range pressure, with individual attribution still pending.

Continued motion supplies 478 native updates per instance through t=103.5s. Restoration occurs at t=58.6s. Stress-group position RMSE: 1.002m before restoration, 0.278m over the entire post-restoration transition, final error approximately 5.94cm. Sustained convergence requires position <0.1m and yaw <5° across five simulation seconds with at least eight updates; the stress group meets this after 11.3s, while the full group had already converged.

All three occupancy maps are identical here, explaining identical localization outcomes. [Measured normal coverage](../../results/reference/robot-degradation/geometry-audit.json): median normal-Gram eigenvalue ratio 0.1042 full, 0.00024 limited, 0.1048 restored. This local scan diagnostic is neither a full SLAM Hessian nor calibrated recovery probability.

An earlier corridor patrol finished before restoration, so AMCL's motion thresholds stopped new pose updates; that local diagnostic is not used to judge recovery failure. Current checks reject insufficient post-restoration coverage. The persistent-change route did not induce loss and is not claimed as successful recovery. These are offset-initial-belief tests, not physical kidnapping.

## One-click demonstrations and physical tests

Local scripts: `F:\be2演讲\实机脚本`; [instructions](../../demo/README.md). In the dedicated terminal: i/k forward/back, j/l turn, u/o lateral, space stop, q finish. Automatic recording scripts save MP4, bag, truth and score logs; complete media are mirrored under `F:\be2演讲\屏幕实录\20261014-native-ui`.

| Physical scene | Sensor layer | Metrics/media | Status |
| --- | --- | --- | --- |
| Static | 2D / independent 3D | — | Pending |
| Dynamic occlusion | 2D / independent 3D | — | Pending |
| Geometric degradation | 2D / independent 3D | — | Pending |
| Persistent change | 2D / independent 3D | — | Pending |

## Rendering and truth fixes

Explicit `GALLIUM_DRIVER=d3d12` selects the local RTX4070SUPER instead of llvmpipe; saved renderer logs confirm NVIDIA acceleration and native Gazebo GUI rendering. [Upstream issue](https://github.com/gazebosim/gz-sim/issues/2670). A private ament resource overlay assigns distinct sampler bindings for the RViz map shader; system installation remains intact. Actual captures overturn the earlier claim that this computer could not render the GUI.

Native Gazebo transport avoids model-name/top-level timestamp losses in this ROS-Gazebo TF conversion. Validation checks model identity, timestamp monotonicity, synchronization, scored-update coverage and sustained convergence, so healthy-looking displays cannot substitute for valid measurements.
