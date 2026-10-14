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

[Raw live RViz](../../results/reference/robot-corridor-v2/executions/degraded_raw.mp4) · [DUFOMap live RViz](../../results/reference/robot-corridor-v2/executions/degraded_dufomap.mp4) · [BeautyMap live RViz](../../results/reference/robot-corridor-v2/executions/degraded_beautymap.mp4) · [record](../../results/reference/robot-corridor-v2/record.json)

[Mapping A](../../results/reference/robot-corridor-mapping/execution.mp4)

Execution combines synchronized captures of real application windows; unrelated desktop content is excluded. Gazebo's visible real-time factor reports actual simulation speed; 12/15fps capture is not algorithm throughput. GIFs sample the full MP4 interval at 5fps without acceleration. `timing.json` records duration/frame checks, and every MP4 is fully decoded.

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
| New corridor full-scan controls | 71.60 | 71.60 | 71.60 | 508 |
| New corridor limited → restored scans | 72.53 | 72.53 | 72.53 | 508 |

The homepage shows separate method GIFs; the [recording index](../../demo/recording-index.json) connects local video names to these rows.

## Corridor restoration

The rebuilt model has a 14 m plain parallel-wall centre and wider end rooms with asymmetric columns/blocks, total length about 24 m. The central 3.5 m scan cannot see the end landmarks at the starting pose; full 12 m scans regain distant constraints as the robot drives. Both mapping A and held-out B use the same saved world hash. Changing geometry forces a fresh A and map processing; old maps cannot silently enter this test.

Initial belief offset: X=1 m, Y=0.15 m, yaw=0.12 rad. Full controls receive 720 beams / 360° / 12 m; pressure cases receive 72 beams / 240° / 3.5 m for 50 simulation seconds, then full observations. The 3D sensor remains full and does not feed AMCL.

This run retains 508 updates per case. Restoration occurs at t=66.2 s. Pressure cases have full-window XY RMSE 72.53 cm; full controls 71.60 cm, both including initialization. Pressure convergence begins 13.3 s after restoration; confirmation requires position <0.1 m and |yaw|<5° across 5 simulation seconds and at least 8 native updates. The full controls first satisfy the same sustained rule 6.6 s after that reference time, despite never being scan-limited.

All three projected maps are identical. The full-control ambiguity means this run does not isolate scan limitation as the sole failure cause, and does not rank map cleaners. The 11.3 s and 31.3 s results refer to earlier corridor models/runs, retained as history. No physical kidnapping is performed.

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

## Separate 2D / 3D comparison, 2026-10-14–15

The homepage/video gallery now separates 2D AMCL from 3D GICP. A fresh dynamic mapping A supplies both the new 2D dynamic run and 3D dynamic run. The original table above is historical; its dynamic maps came from an earlier A. All other worlds/routes remain the existing four scenarios.

The 3D branch uses full native cleaned point maps, retained XYZ/quaternion outputs and private SE(3) display TF. It also applies the corridor limitation to 3D clouds, keeping full-cloud controls. Missing native outputs after restoration are reported as insufficient evidence rather than successful recovery. GICP's first published pose has already undergone registration. Shared source streams do not guarantee identical consumed histories; byte-identical corridor maps with divergent tracking expose this limitation.

[New scores, common-point map-quality audit, all parameter checks and paper applicability](MAP-2D-3D.md) · [2D recordings](../../demo/gallery.html#2d) · [3D recordings](../../demo/gallery.html#3d) · [new mapping-A input capture](../../results/reference/robot-3d-dynamic-mapping/record.json).

Mapping remains point-cloud fusion/cleaning with supplied poses, not a full 3D SLAM claim. True live inference recordings and the explicitly labelled saved-map result review are separate. The recorder keeps the genuine status terminal repainting during encoder shutdown, allowing WGC/FFmpeg to finalize every MP4 before native windows close.
