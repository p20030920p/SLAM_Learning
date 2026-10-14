# Native desktop simulation and scoring

2026-10-14: actual Windows Gazebo, RViz2 and Windows Terminal windows, recorded with Windows Graphics Capture. The Sim2Real omnidirectional chassis retains its native 2D sensor and gains the independent 3D profile. Worlds and controllers are disclosed local adaptations, not paper datasets. [中文细节](LIVE.zh-CN.md).

### Pure static

[Raw live RViz](../../results/reference/robot-live-static/executions/raw.mp4) · [DUFOMap live RViz](../../results/reference/robot-live-static/executions/dufomap.mp4) · [BeautyMap live RViz](../../results/reference/robot-live-static/executions/beautymap.mp4) · [record](../../results/reference/robot-live-static/record.json)

[Mapping A](../../results/reference/robot-static-mapping/execution.mp4)

### Moving obstacles

[Raw live RViz](../../results/reference/robot-live-dynamic/executions/raw.mp4) · [DUFOMap live RViz](../../results/reference/robot-live-dynamic/executions/dufomap.mp4) · [BeautyMap live RViz](../../results/reference/robot-live-dynamic/executions/beautymap.mp4) · [record](../../results/reference/robot-live-dynamic/record.json)

[Mapping A](../../results/reference/robot-dynamic-mapping/execution.mp4)

### Persistent change

[Raw live RViz](../../results/reference/robot-live-large-change/executions/raw.mp4) · [DUFOMap live RViz](../../results/reference/robot-live-large-change/executions/dufomap.mp4) · [BeautyMap live RViz](../../results/reference/robot-live-large-change/executions/beautymap.mp4) · [record](../../results/reference/robot-live-large-change/record.json)

[Mapping A](../../results/reference/robot-static-mapping/execution.mp4)

### Corridor degradation

[Raw live RViz](../../results/reference/robot-live-degradation/executions/degraded_raw.mp4) · [DUFOMap live RViz](../../results/reference/robot-live-degradation/executions/degraded_dufomap.mp4) · [BeautyMap live RViz](../../results/reference/robot-live-degradation/executions/degraded_beautymap.mp4) · [record](../../results/reference/robot-live-degradation/record.json)

[Mapping A](../../results/reference/robot-corridor-mapping/execution.mp4)

Execution combines synchronized captures of real application windows; unrelated desktop content is excluded. Gazebo's visible real-time factor reports actual simulation speed; 15fps capture is not algorithm throughput. GIFs sample the full MP4 interval at 5fps without acceleration. `timing.json` records duration/frame checks, and every MP4 is fully decoded.

Replays are labelled `MEASURED RESULT REPLAY`: saved AMCL updates and independent simulator truth, sampled at 8fps of simulation time using the latest saved update. No inference is performed during replay. Capture uses wall time, replay uses simulation time, so durations differ.

## Mapping and method scope

Native slam_toolbox builds a live 2D map. Mapping A records the independent 3D clouds at approximately one scan per simulation second, then selects up to 60 evenly spaced scans. Raw stacking, native DUFOMap and native BeautyMap receive identical provided sensor poses and scans. Their outputs use common observed free rays, a 0.12–1.20m height band, 0.05m cells and one-cell occupied dilation for AMCL maps; no world geometry fills unseen space.

DUFOMap: 0.1m / d_s=0.2 / d_p=1. BeautyMap: range=8m / XY=0.5m / Z=0.2m, disclosed Python-reader and small-map query-border compatibility patch. Working indices receive an empty integer border; original world points remain unchanged. Native logs, patch hashes and retained-point identity checks are saved. These are platform adaptations, not unmodified paper-protocol reproductions. Removed-point counts are not static/dynamic accuracy without validated point labels.

Held-out B starts a fresh simulation. Identical native Nav2 AMCL instances share live scan and wheel-odometry inputs, changing only the frozen maps; dynamic B includes static-A map controls. Corridor stress instances instead receive the disclosed derived scan. Truth goes only to evaluation/display, never AMCL or the odometry-controlled patrol. Settings include OmniMotionModel, 500–2000 particles, up to 60 beams and shared motion/observation parameters. All AMCL TF broadcasts are disabled to avoid interference. Three separate RViz processes display Raw, DUFOMap and BeautyMap with their own map, native pose/particles and isolated TF topics. The passive display relay changes no AMCL inputs. Each live video captures its own method window. Static-map dynamic controls and full-scan corridor controls also run and retain native scores.

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
| Pure static | 7.28 | 7.28 | 6.89 | 290 |
| Dynamic maps / moving obstacles | 7.41 | 7.35 | 7.14 | 288 |
| Static-map controls / same dynamic input | 7.08 | 7.08 | 6.78 | 288 |
| Old maps / persistent change | 6.84 | 6.84 | 6.39 | 290 |
| Full-scan controls | 53.46 | 53.46 | 53.46 | 476 |
| Limited → restored scans | 75.66 | 75.66 | 75.66 | 476 |

The homepage shows separate method GIFs; the [recording index](../../demo/recording-index.json) connects local video names to these rows.

## Corridor restoration

Matched 20 m parallel-wall corridor. Initial belief offset: X=1 m, Y=0.15 m, yaw=0.12 rad; other scenes use X=0.25 m. Full controls receive 720 beams / 360° / 12 m. Pressure cases receive 72 beams / 240° / 3.5 m from the same scan for 50 simulation seconds, then regain full observations. Independent 3D LiDAR stays full and does not feed AMCL.

This new run retains 476 native updates per case through t=103.3 s, with restoration at t=58.5 s. Pressure-group RMSE is 0.975 m before restoration, 0.441 m over the post-restoration transition, and 6.62 cm at the last update. Sustained convergence begins 31.3 s after restoration and is confirmed across 5 simulation seconds, >=8 native updates, position <0.1 m and absolute yaw <5°.

All three projected corridor maps are identical, so their outcomes are identical. The earlier 478-update / 11.3 s trial remains [archived](../../results/reference/robot-degradation/record.json); it is not paired with the new live clips. The new 31.3 s delay illustrates why one run does not establish recovery stability. Neither trial is physical kidnapping. The persistent-change route did not induce loss.

The [historical normal-coverage audit](../../results/reference/robot-degradation/geometry-audit.json) describes the earlier trial, not this new one. Its local Gram ratio is not a full SLAM Hessian or calibrated recovery probability.

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

## Live author-state display

Current author states are written atomically during execution and published to RViz; frame/serial order, state hashes and the computation interval are verified. WSL wall clocks showed sub-second corrections in the IR-MCL run, so frame order is authoritative with a 2 s wall-clock tolerance. Future captures also store monotonic clocks. Display thinning and observer overhead are disclosed; original inference and cleaning decisions are unchanged.

DUFOMap and BeautyMap final `cleaned.pcd` SHA256 values are byte-identical to the preceding native executions: [DUFOMap previous](../../results/reference/desktop-dufomap/native-run/record.json) / [current](../../results/reference/desktop-live-dufomap/native-run/record.json), [BeautyMap previous](../../results/reference/desktop-beautymap/native-run/record.json) / [current](../../results/reference/desktop-live-beautymap/native-run/record.json).
