# Hypotheses from failure recordings, followed by small experiments

This preserves earlier **pose-level exploration with frozen maps**. The current [mapping question and M1/M4/M5](MAPPING-FOCUS.md) are separate; Depth trials change localization observations and do not validate the current contamination relationship or geometry-retention strategy.

Map cleaning did not consistently improve localization, and native 3D GICP also diverged or stopped publishing in the original corridor. This motivates testing when to trust matching, which observations are missing, and how to propose and confirm recovery. [Earlier evidence and diagnosis](MAP-2D-3D.md).

These are small custom prototypes, not reproductions of additional papers. The [frame-calibrated protocol and source hashes](../../results/analysis/hypotheses/calibrated-protocol.json) are frozen before the repeat. The [initial protocol](../../results/analysis/hypotheses/protocol.json) and all unsuccessful results remain available.

## Check the frame convention before judging the method

The initial prototype fixed z=0. Its static 3D XY error was about 0.14cm, while XYZ was 9.41cm, almost entirely a constant Z error. This was a prototype reference-height mistake; it does not show that 3D observations or the paper cleaners are ineffective. Native GICP in that trial was about 1.09cm and did not share the fixed-z assumption. [Initial static 3D evidence](../../results/reference/probe-3d-static/record.json).

The actual URDF places the 3D lidar 0.30m above the body frame. Reconstruct `T_world_body = T_world_lidar × inverse(T_body_lidar)` from supplied mapping-A poses and the actual extrinsic. The median body Z is approximately 0.09414m for every A dataset. Internal XYZ matching subtracts this reference from map coordinates; published world poses use the same A-derived height. B truth is never read by the estimators and no trajectory fitting is applied.

The main results below use the complete frame-corrected repeat. Each package retains the calibration matrices, URDF and emitted poses. The initial ten trials remain diagnostic evidence, rather than samples to combine into a ranking.

## H1: protect the estimate from unreliable matches

The hypothesis is that robust residuals suppress moving/new obstacles, while weak-direction updates should defer to wheel odometry. [RELEAD](https://arxiv.org/abs/2402.18934) motivates observability-aware multisensor constraints; this prototype does not implement its ESIKF or graph optimizer. Plain and Guard share the lidar map, scans and wheel prediction. Guard adds a Huber loss, a tighter correspondence gate, weak-eigenvalue projection and odometry regularization. This bundled comparison cannot identify the contribution of each component. Odometry preserves, rather than resolves, a 1m initial bias along an entirely unobservable corridor.

## H2: supplement a 2D lidar with a depth camera

The hypothesis is that height-dependent edges or suspended structures can add constraints missing from a planar scan. More points on the same parallel walls cannot supply a missing direction. Guard versus Depth isolates an additional depth residual group and its independently observed map A. Each modality is normalized separately. Depth is paired within 0.12s and motion-compensated to the lidar timestamp using wheel odometry; stale/empty observations are skipped and their usage is reported.

A genuine Gazebo `depth_camera`, following the [official example](https://github.com/gazebosim/gz-sim/blob/gz-sim8/examples/worlds/depth_camera_sensor.sdf), renders 320×240 depth over an 80° horizontal FOV and 0.25–4m range, requesting 10Hz. The 2D B robot physically has no 3D lidar. No depth is fabricated by cropping a lidar cloud. Hardware noise, reflective/transparent surfaces and calibration errors are not modelled.

The unchanged corridor remains a test. A separately labelled feasibility control adds two high geometric blocks to that corridor, present in both A and B, keeping its ground route, initial bias and lidar degradation. Success there would support the conditional value of visible height structure, not improve the original corridor result or prove general indoor applicability.

## H3: search several candidates and confirm recovery

The hypothesis is that a bounded candidate search can escape a bad local basin. A candidate must fit well, beat a spatially distinct alternative and remain consistent with the next search under wheel odometry. [Cartographer's official algorithm description](https://google-cartographer-ros.readthedocs.io/en/latest/algo_walkthrough.html) explains combining candidate search and local refinement; this prototype uses a simple grid, not its branch-and-bound or full backend.

Compare Guard with LiDAR Search and Depth with Depth + Search. The search spans ±2m and ±30° around the current belief, at least 3s apart. Acceptance requires score≥0.65, a distinct-candidate margin≥0.025 and two consecutive map/odom alignments within 0.25m and 8°. Search runs during unconfirmed startup, rank loss, large residuals or insufficient correspondences. Algorithm acceptance and truth-verified sustained recovery are separate measurements.

## Controls and scope

- Retain static, moving-obstacle, persistent-change and original corridor scenes; separately label the derived height control. Record 90 simulation seconds for the first three and 120 for either corridor. Lidar is restricted during preparation and for 50 simulation seconds after recording starts, then restored; depth remains limited to 4m.
- Run both 2D lidar + depth and 16-channel 3D lidar + depth. All five prototypes consume identical frame IDs, point arrays and wheel odometry. Native AMCL/GICP anchors consume the same source independently, so their differences cannot isolate a sensor or algorithm component.
- Every prototype estimates ground-robot x/y/yaw, fixing z to the A-derived reference and roll/pitch to zero. The 3D arm uses XYZ plane residuals but is not full SE(3) SLAM. Native GICP retains its complete pose. This flat-ground motion prior is itself a difference from native GICP.
- Native 2D AMCL uses a 5cm grid projection with one-cell inflation, while prototypes match the lidar point map directly. Representation and observation models therefore also differ; paired prototype ablations are the relevant H1–H3 comparisons.
- All estimators only publish poses. The same wheel-odometry patrol drives the robot; localization outputs do not close the navigation loop.
- Mapping A uses supplied poses. Localization B never reads truth. Persistent-change B reuses static A; all maps remain frozen. H1 rejects inconsistent observations without confirming new walls or updating maps.
- Mapping A also retains 3D lidar as a reference and uses its supplied poses and extrinsics to audit body height. The 2D prototypes match the independent 2D lidar and depth maps. This tests localization from inexpensive sensors; autonomous mapping and height estimation using only those sensors remain untested.
- Report XY RMSE for 2D and XYZ RMSE for 3D, without spatial fitting. Pair published outputs to independent truth within 0.05s. First scores are computed estimates; unpublished initial beliefs and missing outputs are not inserted as zero error. Report output coverage separately.
- Prototype messages omitted at observer startup/shutdown can be paired from their actual emitted-pose log; original observer CSVs and an explicit repair record are retained. Estimator output gaps are never filled. Native AMCL's retained initial pose is received with its actual Transient Local QoS, with duplicate messages removed.
- Recovery means XY<0.1m and |yaw|<5° continuously for 5s with at least 8 updates after observation restoration. This corrects an offset belief; no physical kidnapping or arbitrary global recovery is tested.
- One exploratory ideal-simulation trial per condition cannot establish a ranking or promise hardware precision.
- Estimators run during capture preparation. If confirmation precedes recording, the video shows subsequent tracking; CSVs, error curves and candidate logs retain the complete startup error and acceptance timing.

## Small experiment results

The complete formal batch is shown separately for 2D and 3D, with a compact table before each genuine Gazebo + RViz + Terminal recording. [Video directory](../../demo/hypotheses.html).

<!-- PROBE_RESULTS -->

<a id="hypothesis-experiment-index"></a>

| Scene | 2D + depth | 3D + depth |
| --- | --- | --- |
| Pure static | [View experiment](#probe-calibrated-2d-static) | [View experiment](#probe-calibrated-3d-static) |
| Moving obstacles | [View experiment](#probe-calibrated-2d-dynamic) | [View experiment](#probe-calibrated-3d-dynamic) |
| Persistent change | [View experiment](#probe-calibrated-2d-large-change) | [View experiment](#probe-calibrated-3d-large-change) |
| Original corridor degradation | [View experiment](#probe-calibrated-2d-corridor) | [View experiment](#probe-calibrated-3d-corridor) |
| Height landmarks · derived control | [View experiment](#probe-calibrated-2d-height-corridor) | [View experiment](#probe-calibrated-3d-height-corridor) |

[Coarse-to-fine follow-up](#probe-refinement-index)

[Interpretation and next directions](#hypothesis-findings)

This matrix fixes the raw source maps and shares identical paired inputs across five prototypes. Red: Plain; yellow: Guard; orange: Depth; purple: lidar search; green: depth + search; blue: native AMCL/GICP. Report XY for 2D and XYZ for 3D; these single trials do not establish a ranking.

### 2D · native-window experiments

<a id="probe-calibrated-2d-static"></a>

#### Pure static · 2D

[↑ Back to index](#hypothesis-experiment-index)

| Method | Map / observations | Metric / effect |
| --- | --- | --- |
| Raw + AMCL | Same-source 2D grid projection | XY RMSE 6.82 cm |
| Plain ICP | 2D lidar point map | XY RMSE 0.15 cm |
| H1 · Guard | 2D lidar point map | XY RMSE 0.15 cm; close to plain |
| H2 · Guard + Depth | 2D lidar point map + depth map | XY RMSE 0.21 cm; 0.06 cm above guard |
| H3 · LiDAR Search | 2D lidar point map | XY RMSE 0.15 cm; close to guard |
| H3 · Depth + Search | 2D lidar point map + depth map | XY RMSE 0.21 cm; close to depth |

Each prototype: 264 frames; usable depth: 219/264; native anchor: 287 outputs. Body height is calibrated from mapping A.

The native anchor last published at simulation 73.2s; prototypes extend to 99.4s. Missing outputs are not filled; native RMSE covers its available outputs only.

![Pure static · 2D · native windows](../../results/reference/probe-calibrated-2d-static/execution.gif)

[MP4](../../results/reference/probe-calibrated-2d-static/execution.mp4) · [record](../../results/reference/probe-calibrated-2d-static/record.json) · [CSV](../../results/reference/probe-calibrated-2d-static/recover-samples.csv)

<a id="probe-calibrated-2d-dynamic"></a>

#### Moving obstacles · 2D

[↑ Back to index](#hypothesis-experiment-index)

| Method | Map / observations | Metric / effect |
| --- | --- | --- |
| Raw + AMCL | Same-source 2D grid projection | XY RMSE 7.08 cm |
| Plain ICP | 2D lidar point map | XY RMSE 0.37 cm |
| H1 · Guard | 2D lidar point map | XY RMSE 0.19 cm; 0.18 cm below plain |
| H2 · Guard + Depth | 2D lidar point map + depth map | XY RMSE 0.18 cm; close to guard |
| H3 · LiDAR Search | 2D lidar point map | XY RMSE 0.19 cm; close to guard |
| H3 · Depth + Search | 2D lidar point map + depth map | XY RMSE 0.18 cm; close to depth |

Each prototype: 265 frames; usable depth: 181/265; native anchor: 292 outputs. Body height is calibrated from mapping A.

The native anchor last published at simulation 72.3s; prototypes extend to 99.7s. Missing outputs are not filled; native RMSE covers its available outputs only.

![Moving obstacles · 2D · native windows](../../results/reference/probe-calibrated-2d-dynamic/execution.gif)

[MP4](../../results/reference/probe-calibrated-2d-dynamic/execution.mp4) · [record](../../results/reference/probe-calibrated-2d-dynamic/record.json) · [CSV](../../results/reference/probe-calibrated-2d-dynamic/recover-samples.csv)

<a id="probe-calibrated-2d-large-change"></a>

#### Persistent change · 2D

[↑ Back to index](#hypothesis-experiment-index)

| Method | Map / observations | Metric / effect |
| --- | --- | --- |
| Raw + AMCL | Same-source 2D grid projection | XY RMSE 6.28 cm |
| Plain ICP | 2D lidar point map | XY RMSE 7.98 cm |
| H1 · Guard | 2D lidar point map | XY RMSE 0.49 cm; 7.49 cm below plain |
| H2 · Guard + Depth | 2D lidar point map + depth map | XY RMSE 0.49 cm; close to guard |
| H3 · LiDAR Search | 2D lidar point map | XY RMSE 0.49 cm; close to guard |
| H3 · Depth + Search | 2D lidar point map + depth map | XY RMSE 0.49 cm; close to depth |

Each prototype: 263 frames; usable depth: 187/263; native anchor: 288 outputs. Body height is calibrated from mapping A.

The native anchor last published at simulation 71.3s; prototypes extend to 99.3s. Missing outputs are not filled; native RMSE covers its available outputs only.

The old map remains frozen; this tests inconsistent-observation handling without map updates.

![Persistent change · 2D · native windows](../../results/reference/probe-calibrated-2d-large-change/execution.gif)

[MP4](../../results/reference/probe-calibrated-2d-large-change/execution.mp4) · [record](../../results/reference/probe-calibrated-2d-large-change/record.json) · [CSV](../../results/reference/probe-calibrated-2d-large-change/recover-samples.csv)

<a id="probe-calibrated-2d-corridor"></a>

#### Original corridor degradation · 2D

[↑ Back to index](#hypothesis-experiment-index)

| Method | Map / observations | Metric / effect |
| --- | --- | --- |
| Raw + AMCL | Same-source 2D grid projection | XY RMSE 100.61 cm; sustained recovery 45.7s after restoration |
| Plain ICP | 2D lidar point map | XY RMSE 1037.69 cm; no sustained recovery |
| H1 · Guard | 2D lidar point map | XY RMSE 100.48 cm; 937.21 cm below plain; no sustained recovery |
| H2 · Guard + Depth | 2D lidar point map + depth map | XY RMSE 100.54 cm; 0.06 cm above guard; no sustained recovery |
| H3 · LiDAR Search | 2D lidar point map | XY RMSE 70.40 cm; 30.08 cm below guard; sustained recovery 5.8s after restoration |
| H3 · Depth + Search | 2D lidar point map + depth map | XY RMSE 70.44 cm; 30.11 cm below depth; sustained recovery 5.8s after restoration |

Each prototype: 338 frames; usable depth: 195/338; native anchor: 600 outputs. Body height is calibrated from mapping A.

![Original corridor degradation · 2D · native windows](../../results/reference/probe-calibrated-2d-corridor/execution.gif)

[MP4](../../results/reference/probe-calibrated-2d-corridor/execution.mp4) · [record](../../results/reference/probe-calibrated-2d-corridor/record.json) · [CSV](../../results/reference/probe-calibrated-2d-corridor/recover-samples.csv)

<a id="probe-calibrated-2d-height-corridor"></a>

#### Height landmarks · derived control · 2D

[↑ Back to index](#hypothesis-experiment-index)

| Method | Map / observations | Metric / effect |
| --- | --- | --- |
| Raw + AMCL | Same-source 2D grid projection | XY RMSE 67.00 cm; sustained recovery 11.7s after restoration |
| Plain ICP | 2D lidar point map | XY RMSE 285.54 cm; no sustained recovery |
| H1 · Guard | 2D lidar point map | XY RMSE 101.15 cm; 184.39 cm below plain; no sustained recovery |
| H2 · Guard + Depth | 2D lidar point map + depth map | XY RMSE 100.77 cm; 0.38 cm below guard; no sustained recovery |
| H3 · LiDAR Search | 2D lidar point map | XY RMSE 70.93 cm; 30.22 cm below guard; sustained recovery 5.0s after restoration |
| H3 · Depth + Search | 2D lidar point map + depth map | XY RMSE 21.15 cm; 79.61 cm below depth; sustained recovery 0.2s after restoration |

Each prototype: 345 frames; usable depth: 239/345; native anchor: 620 outputs. Body height is calibrated from mapping A.

Two high blocks are added in this feasibility control; report it separately from the original corridor.

![Height landmarks · derived control · 2D · native windows](../../results/reference/probe-calibrated-2d-height-corridor/execution.gif)

[MP4](../../results/reference/probe-calibrated-2d-height-corridor/execution.mp4) · [record](../../results/reference/probe-calibrated-2d-height-corridor/record.json) · [CSV](../../results/reference/probe-calibrated-2d-height-corridor/recover-samples.csv)

### 3D · native-window experiments

<a id="probe-calibrated-3d-static"></a>

#### Pure static · 3D

[↑ Back to index](#hypothesis-experiment-index)

| Method | Map / observations | Metric / effect |
| --- | --- | --- |
| Raw + GICP | 3D lidar point map | XYZ RMSE 1.08 cm |
| Plain ICP | 3D lidar point map | XYZ RMSE 0.12 cm |
| H1 · Guard | 3D lidar point map | XYZ RMSE 0.12 cm; close to plain |
| H2 · Guard + Depth | 3D lidar point map + depth map | XYZ RMSE 0.21 cm; 0.09 cm above guard |
| H3 · LiDAR Search | 3D lidar point map | XYZ RMSE 0.12 cm; close to guard |
| H3 · Depth + Search | 3D lidar point map + depth map | XYZ RMSE 0.21 cm; close to depth |

Each prototype: 266 frames; usable depth: 184/266; native anchor: 994 outputs. Body height is calibrated from mapping A.

![Pure static · 3D · native windows](../../results/reference/probe-calibrated-3d-static/execution.gif)

[MP4](../../results/reference/probe-calibrated-3d-static/execution.mp4) · [record](../../results/reference/probe-calibrated-3d-static/record.json) · [CSV](../../results/reference/probe-calibrated-3d-static/recover-samples.csv)

<a id="probe-calibrated-3d-dynamic"></a>

#### Moving obstacles · 3D

[↑ Back to index](#hypothesis-experiment-index)

| Method | Map / observations | Metric / effect |
| --- | --- | --- |
| Raw + GICP | 3D lidar point map | XYZ RMSE 1.39 cm |
| Plain ICP | 3D lidar point map | XYZ RMSE 0.17 cm |
| H1 · Guard | 3D lidar point map | XYZ RMSE 0.13 cm; 0.04 cm below plain |
| H2 · Guard + Depth | 3D lidar point map + depth map | XYZ RMSE 0.13 cm; close to guard |
| H3 · LiDAR Search | 3D lidar point map | XYZ RMSE 0.13 cm; close to guard |
| H3 · Depth + Search | 3D lidar point map + depth map | XYZ RMSE 0.13 cm; close to depth |

Each prototype: 258 frames; usable depth: 154/258; native anchor: 951 outputs. Body height is calibrated from mapping A.

![Moving obstacles · 3D · native windows](../../results/reference/probe-calibrated-3d-dynamic/execution.gif)

[MP4](../../results/reference/probe-calibrated-3d-dynamic/execution.mp4) · [record](../../results/reference/probe-calibrated-3d-dynamic/record.json) · [CSV](../../results/reference/probe-calibrated-3d-dynamic/recover-samples.csv)

<a id="probe-calibrated-3d-large-change"></a>

#### Persistent change · 3D

[↑ Back to index](#hypothesis-experiment-index)

| Method | Map / observations | Metric / effect |
| --- | --- | --- |
| Raw + GICP | 3D lidar point map | XYZ RMSE 1.25 cm |
| Plain ICP | 3D lidar point map | XYZ RMSE 3.69 cm |
| H1 · Guard | 3D lidar point map | XYZ RMSE 0.24 cm; 3.45 cm below plain |
| H2 · Guard + Depth | 3D lidar point map + depth map | XYZ RMSE 0.35 cm; 0.11 cm above guard |
| H3 · LiDAR Search | 3D lidar point map | XYZ RMSE 0.24 cm; close to guard |
| H3 · Depth + Search | 3D lidar point map + depth map | XYZ RMSE 0.35 cm; close to depth |

Each prototype: 264 frames; usable depth: 163/264; native anchor: 950 outputs. Body height is calibrated from mapping A.

The old map remains frozen; this tests inconsistent-observation handling without map updates.

![Persistent change · 3D · native windows](../../results/reference/probe-calibrated-3d-large-change/execution.gif)

[MP4](../../results/reference/probe-calibrated-3d-large-change/execution.mp4) · [record](../../results/reference/probe-calibrated-3d-large-change/record.json) · [CSV](../../results/reference/probe-calibrated-3d-large-change/recover-samples.csv)

<a id="probe-calibrated-3d-corridor"></a>

#### Original corridor degradation · 3D

[↑ Back to index](#hypothesis-experiment-index)

| Method | Map / observations | Metric / effect |
| --- | --- | --- |
| Raw + GICP | 3D lidar point map | XYZ RMSE 397.82 cm; no sustained recovery |
| Plain ICP | 3D lidar point map | XYZ RMSE 733.38 cm; no sustained recovery |
| H1 · Guard | 3D lidar point map | XYZ RMSE 100.49 cm; 632.88 cm below plain; no sustained recovery |
| H2 · Guard + Depth | 3D lidar point map + depth map | XYZ RMSE 100.62 cm; 0.12 cm above guard; no sustained recovery |
| H3 · LiDAR Search | 3D lidar point map | XYZ RMSE 56.77 cm; 43.72 cm below guard; sustained recovery 6.2s after restoration |
| H3 · Depth + Search | 3D lidar point map + depth map | XYZ RMSE 57.56 cm; 43.06 cm below depth; sustained recovery 6.6s after restoration |

Each prototype: 247 frames; usable depth: 122/247; native anchor: 712 outputs. Body height is calibrated from mapping A.

The native anchor last published at simulation 75.6s; prototypes extend to 132.8s. Missing outputs are not filled; native RMSE covers its available outputs only.

![Original corridor degradation · 3D · native windows](../../results/reference/probe-calibrated-3d-corridor/execution.gif)

[MP4](../../results/reference/probe-calibrated-3d-corridor/execution.mp4) · [record](../../results/reference/probe-calibrated-3d-corridor/record.json) · [CSV](../../results/reference/probe-calibrated-3d-corridor/recover-samples.csv)

<a id="probe-calibrated-3d-height-corridor"></a>

#### Height landmarks · derived control · 3D

[↑ Back to index](#hypothesis-experiment-index)

| Method | Map / observations | Metric / effect |
| --- | --- | --- |
| Raw + GICP | 3D lidar point map | XYZ RMSE 512.79 cm; no sustained recovery |
| Plain ICP | 3D lidar point map | XYZ RMSE 46.60 cm; sustained recovery 8.7s after restoration |
| H1 · Guard | 3D lidar point map | XYZ RMSE 100.36 cm; 53.76 cm above plain; no sustained recovery |
| H2 · Guard + Depth | 3D lidar point map + depth map | XYZ RMSE 100.38 cm; 0.02 cm above guard; no sustained recovery |
| H3 · LiDAR Search | 3D lidar point map | XYZ RMSE 47.70 cm; 52.66 cm below guard; sustained recovery 8.7s after restoration |
| H3 · Depth + Search | 3D lidar point map + depth map | XYZ RMSE 50.79 cm; 49.59 cm below depth; sustained recovery 12.8s after restoration |

Each prototype: 203 frames; usable depth: 124/203; native anchor: 716 outputs. Body height is calibrated from mapping A.

The native anchor last published at simulation 75.1s; prototypes extend to 132.5s. Missing outputs are not filled; native RMSE covers its available outputs only.

Two high blocks are added in this feasibility control; report it separately from the original corridor.

![Height landmarks · derived control · 3D · native windows](../../results/reference/probe-calibrated-3d-height-corridor/execution.gif)

[MP4](../../results/reference/probe-calibrated-3d-height-corridor/execution.mp4) · [record](../../results/reference/probe-calibrated-3d-height-corridor/record.json) · [CSV](../../results/reference/probe-calibrated-3d-height-corridor/recover-samples.csv)

<a id="probe-refinement-index"></a>

### Follow-up hypothesis: coarse-to-fine search and recovery confirmation

An approximately 20cm plateau in the initial height control motivated a 0.1m refinement of the 0.4m candidate grid and checks against more evaluated alternatives. H1/H2, score thresholds and consecutive confirmation stay fixed. New inference uses exactly the retained B arrays above; these videos replay its saved results.

| Scene | 2D inference | 3D inference |
| --- | --- | --- |
| Original corridor degradation | [2D](#probe-calibrated-refinement-2d-corridor) | [3D](#probe-calibrated-refinement-3d-corridor) |
| Height landmarks · derived control | [2D](#probe-calibrated-refinement-2d-height-corridor) | [3D](#probe-calibrated-refinement-3d-height-corridor) |

<a id="probe-calibrated-refinement-2d-corridor"></a>

#### 2D · Original corridor degradation · same-input refinement

[↑ Back to index](#hypothesis-experiment-index)

| Method | Map / observations | Metric / effect |
| --- | --- | --- |
| Coarse · lidar | Lidar point map | XY RMSE 70.40 cm；sustained convergence 61.1s from first output |
| Coarse · depth + lidar | Lidar + depth point maps | XY RMSE 70.44 cm；sustained convergence 61.1s from first output |
| Fine · lidar | Lidar point map | XY RMSE 70.40 cm；sustained convergence 61.1s from first output |
| Fine · depth + lidar | Lidar + depth point maps | XY RMSE 70.44 cm；sustained convergence 61.1s from first output |

![Original corridor degradation · 2D · offline-inference result replay](../../results/reference/probe-calibrated-refinement-2d-corridor/result.gif)

[Result replay MP4](../../results/reference/probe-calibrated-refinement-2d-corridor/result.mp4) · [record](../../results/reference/probe-calibrated-refinement-2d-corridor/record.json)

<a id="probe-calibrated-refinement-2d-height-corridor"></a>

#### 2D · Height landmarks · derived control · same-input refinement

[↑ Back to index](#hypothesis-experiment-index)

| Method | Map / observations | Metric / effect |
| --- | --- | --- |
| Coarse · lidar | Lidar point map | XY RMSE 70.93 cm；sustained convergence 60.7s from first output |
| Coarse · depth + lidar | Lidar + depth point maps | XY RMSE 21.15 cm；sustained convergence 55.9s from first output |
| Fine · lidar | Lidar point map | XY RMSE 70.93 cm；sustained convergence 60.7s from first output |
| Fine · depth + lidar | Lidar + depth point maps | XY RMSE 16.20 cm；sustained convergence 3.3s from first output |

![Height landmarks · derived control · 2D · offline-inference result replay](../../results/reference/probe-calibrated-refinement-2d-height-corridor/result.gif)

[Result replay MP4](../../results/reference/probe-calibrated-refinement-2d-height-corridor/result.mp4) · [record](../../results/reference/probe-calibrated-refinement-2d-height-corridor/record.json)

<a id="probe-calibrated-refinement-3d-corridor"></a>

#### 3D · Original corridor degradation · same-input refinement

[↑ Back to index](#hypothesis-experiment-index)

| Method | Map / observations | Metric / effect |
| --- | --- | --- |
| Coarse · lidar | Lidar point map | XYZ RMSE 56.77 cm；sustained convergence 63.7s from first output |
| Coarse · depth + lidar | Lidar + depth point maps | XYZ RMSE 57.56 cm；sustained convergence 64.1s from first output |
| Fine · lidar | Lidar point map | XYZ RMSE 56.77 cm；sustained convergence 63.7s from first output |
| Fine · depth + lidar | Lidar + depth point maps | XYZ RMSE 56.84 cm；sustained convergence 63.7s from first output |

![Original corridor degradation · 3D · offline-inference result replay](../../results/reference/probe-calibrated-refinement-3d-corridor/result.gif)

[Result replay MP4](../../results/reference/probe-calibrated-refinement-3d-corridor/result.mp4) · [record](../../results/reference/probe-calibrated-refinement-3d-corridor/record.json)

<a id="probe-calibrated-refinement-3d-height-corridor"></a>

#### 3D · Height landmarks · derived control · same-input refinement

[↑ Back to index](#hypothesis-experiment-index)

| Method | Map / observations | Metric / effect |
| --- | --- | --- |
| Coarse · lidar | Lidar point map | XYZ RMSE 47.70 cm；sustained convergence 66.1s from first output |
| Coarse · depth + lidar | Lidar + depth point maps | XYZ RMSE 50.79 cm；sustained convergence 70.2s from first output |
| Fine · lidar | Lidar point map | XYZ RMSE 47.70 cm；sustained convergence 66.1s from first output |
| Fine · depth + lidar | Lidar + depth point maps | XYZ RMSE 47.71 cm；sustained convergence 66.1s from first output |

![Height landmarks · derived control · 3D · offline-inference result replay](../../results/reference/probe-calibrated-refinement-3d-height-corridor/result.gif)

[Result replay MP4](../../results/reference/probe-calibrated-refinement-3d-height-corridor/result.mp4) · [record](../../results/reference/probe-calibrated-refinement-3d-height-corridor/record.json)

<!-- PROBE_RESULTS_END -->

<a id="hypothesis-findings"></a>

## What improved, what failed, and what remains open

**H1 handles inconsistent observations but can overprotect the estimate.** Persistent-change Plain→Guard RMSE is 7.98→0.49cm in 2D and 3.69→0.24cm in 3D. Static trials do not benefit; moving-obstacle differences are small. In the 3D height corridor, Guard is worse: 100.36cm versus Plain's 46.60cm. Plain recovers 8.7s after restoration, while Guard does not. At the wrong pose, Guard/Depth keep rank=2 although Plain reaches rank=3. The tighter correspondence gate and weak-direction suppression can retain the initial bias. The bundled experiment does not isolate individual components.

**H2 requires geometry that distinguishes position.** At independent evaluation truth in the limited original corridor, neither lidar nor lidar+depth reaches the configured full-rank threshold in 151 2D frames or 76 3D frames. Parallel walls remain ambiguous. In the 2D height control, depth observes 2159 high-fixture points while lidar observes zero; only 4/157 frames reach joint full rank. Depth alone still keeps the 1m bias. Weak distinguishing information can support candidate comparison even when the local update suppresses that direction. [Original-corridor audit](../../results/analysis/hypotheses/calibrated-2d-corridor-observability.json), [height audit](../../results/analysis/hypotheses/calibrated-2d-height-corridor-observability.json). Local full rank does not prove global uniqueness.

**H3 helps after information returns, but its gate can accept biased positions.** Lidar search recovers in 5.8s/6.2s after restoration in the original 2D/3D corridor; adding depth gives 5.8s/6.6s. In the 2D height control at simulation 8.5s, coarse depth search has score 0.969, margin 0.041 and two confirmations, yet retains a 20.2cm error. The 0.4m grid and weak-direction projection can leave a half-cell bias. On exactly the same B arrays and confirmation thresholds, 0.1m refinement plus checks against more alternatives finds a candidate with 0.43cm error. Sustained convergence advances to 3.3s from first output. Full RMSE is 16.20cm, including the initial approximately 1m offset; after the first 5s it is 0.60cm. This is conditional evidence from the added-height control.

**The 3D height control does not recover early.** Same-input depth refinement changes XYZ RMSE from 50.79 to 47.71cm and post-restore delay from 12.8 to 8.7s, but does not converge before restoration. Only 2/19 limited-phase proposals pass the geometry gate, at 11.8s and 57.5s. Each is followed by a search without usable depth, resetting confirmation. Visibility, discrimination and temporal confirmation all matter. The 0.025 margin was not relaxed to obtain a favorable result. [3D height audit](../../results/analysis/hypotheses/calibrated-3d-height-corridor-observability.json).

**Engineering effects are separate from paper applicability.** The initial approximately 9.4cm XYZ offset was a prototype frame error; after correction static 3D Plain is approximately 0.12cm. This says nothing about the earlier paper cleaners. Processing cadence also differs: the limited 3D height trial retains 45 inputs versus 157 in 2D; logged 3D search updates take 3.0–4.5s. Five prototypes share exact frames within a trial, but cross-dimension RMSE cannot isolate sensor geometry. RMSE weights available outputs equally rather than integrating over time. Native GICP stops effective publication at 75.6s/75.1s in the two 3D corridors while prototypes continue. Its RMSE covers its available outputs only; a frozen last pose is not continued localization.

**The next method should combine the supported parts.** Use Guard for tracking, distinguishable lidar/depth geometry for bounded candidate refinement, and assess sustained recovery separately from candidate acceptance. Untested follow-ups include weighting sensors by information in weak directions, accumulating evidence across frames, separating slow search from tracking, and actively observing end walls or corners. Confirming persistent changes in separate old/new map layers is also unimplemented. Frozen-map localization gains do not demonstrate online map updating. Inexpensive-sensor autonomous mapping, physical kidnapping, realistic noise/calibration errors and independent repeated trials remain separate tests.

[Calibrated summary](../../results/analysis/hypotheses/calibrated-summary.json) · [2D height error curve](../../results/analysis/hypotheses/calibrated-2d-height-corridor-errors.png) · [3D height error curve](../../results/analysis/hypotheses/calibrated-3d-height-corridor-errors.png) · [Initial frame-error trials and unsuccessful refinements](../../demo/hypotheses-diagnostics.html) · [Development, capture and readiness failures](../../results/analysis/hypotheses/diagnostics.json). Earlier uncalibrated refinement worsened the 2D height RMSE from 21.21 to 70.76cm; the corresponding 3D diagnostics are retained too. They are not pooled with the corrected repeat.
