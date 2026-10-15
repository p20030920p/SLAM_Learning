# Why does map cleaning not clearly reduce localization error here?

These trials do not establish that switching to 3D makes the cleaners effective for localization. DUFOMap and BeautyMap already processed 3D clouds; the earlier pipeline projected their outputs for AMCL. Direct use of their 3D maps by the same upstream GICP still produced no clear cleaning benefit in the first three conditions, while corridor tracking diverged or lost valid outputs. Map classification and downstream pose accuracy are different measurements. [中文分析](MAP-2D-3D.zh-CN.md).

## Controlled scope

The same four Gazebo worlds, robot, patrol routes and initial offsets were used: 90 simulation seconds for static, moving obstacles and persistent change; 120 seconds for corridor. Mapping A still fuses and cleans scans using supplied sensor poses; this is not a new full 3D SLAM pipeline. Fresh localization B receives no truth. AMCL uses 2D maps/scans; upstream GICP uses complete frozen 3D maps, live 720×16 clouds, ±15° vertical field, 12m range and wheel odometry. GICP's global TF broadcasts are disabled; each RViz has a private display TF.

The 3D corridor also limits input to 240°, 72 horizontal directions and 3.5m for 50 seconds, then restores full clouds; three full-cloud controls are retained. XY scores are reported for 2D, XYZ plus full quaternion-angle errors for 3D. Every published native update matches independent truth within 0.05 simulation seconds, without fitting. GICP's first output has already undergone registration; unpublished initial beliefs or missing outputs are not assigned zero error. Different localizers, sensors, rates and output availability prevent a causal comparison of absolute 2D versus 3D RMSE. Parallel instances share a source stream, but startup and consumed scan histories may differ. One trial per condition is not a ranking.

## Localization results

Centimetres; each cell orders Raw / DUFOMap / BeautyMap.

| Scene | 2D AMCL XY RMSE | 3D GICP XYZ RMSE |
| --- | --- | --- |
| Static | 7.28 / 7.28 / 6.89 | 0.95 / 0.99 / 1.07 |
| Moving obstacles, same new mapping A | 7.52 / 8.19 / 7.29 | 0.98 / 0.98 / 1.04 |
| Persistent change, frozen old maps | 6.84 / 6.84 / 6.39 | 0.93 / 1.01 / 1.04 |
| Corridor limited → restored | 72.53 / 72.53 / 72.53 | 474.38 / 497.05 / 592.00; unequal output coverage |

[3D static](../../results/reference/robot-3d-static/record.json) · [3D dynamic](../../results/reference/robot-3d-dynamic/record.json) · [3D change](../../results/reference/robot-3d-large-change/record.json) · [3D corridor](../../results/reference/robot-3d-corridor/record.json) · [paired 2D dynamic](../../results/reference/robot-2d-dynamic-matched/record.json). The previous dynamic 7.41 / 7.35 / 7.14cm run used another mapping A and remains [historical evidence](../../results/reference/robot-live-dynamic/record.json). DUFOMap's direction of change reverses between those runs.

Static-map controls in the same dynamic B yield 7.70 / 7.93cm despite identical Raw/DUFOMap 2D pixels, exposing pipeline variation too. The recovery rule remains the planar patrol criterion: XY<0.1m and |yaw|<5° for five seconds with at least eight updates. XYZ/full-rotation errors are retained separately; full six-degree-of-freedom recovery is not claimed.

Corridor Raw and DUFOMap 3D maps are byte-identical, yet tracking differs: the ordering cannot be attributed to cleaning. Restoration occurs at t=62.1s; last native pressure-case outputs are 63.5 / 76.4 / 119.3s, with 530 / 599 / 655 samples. Raw has insufficient updates for sustained recovery assessment; the other two fail the five-second convergence rule. Full-cloud controls stop valid output around 23s too. Published-update RMSE must not conceal output loss or serve as a ranking.

## Measured map cleaning

New dynamic mapping A records actual moving-box model/link poses and parentage. At each scan timestamp, points are transformed into box coordinates: 2cm surface tolerance, an unscored 2–5cm boundary shell, and near self-return exclusion. Of 685047 points, 677851 are static, 7076 dynamic and 120 ambiguous; dynamics occupy only about 1.03%. Positive surface-distance P95 is 0.74cm. These are simulator geometric labels, not paper benchmark annotations.

[Genuine new mapping-A sensor recording](../../results/reference/robot-3d-dynamic-mapping/execution.mp4) retains the 2D slam_toolbox display and independent 3D scans; native 3D cleaning runs offline afterwards.

| Method | Static retained | Dynamic removed |
| --- | --- | --- |
| Raw | 100% | 0% |
| DUFOMap | 99.998% | 46.59% |
| BeautyMap | 81.15% | 74.36% |

DUFOMap demonstrably removes moving-box returns while preserving static geometry. BeautyMap removes more dynamics but also 127758 static points; almost none of those removed static points are below z=0.12m, so this is not simply ground removal. [Recomputable labels, retention masks, hashes and configurations](../../results/reference/robot-3d-map-audit/record.json) · [real RViz 3D result review](../../results/reference/robot-3d-map-review-v2/execution.mp4). Grey denotes static or unscored boundary points, red confidently labelled residual moving-box points. Display stride is six; scores use every confidently labelled input point. The review displays saved native results and performs no new inference.

## Single-factor checks

Every setting is retained and queried on exactly the same baseline 60-scan points, including the map constructed with all 128 scans.

| Method / only changed setting | Static retained | Dynamic removed |
| --- | --- | --- |
| DUFOMap baseline, 0.1m voxel | 99.998% | 46.59% |
| DUFOMap all 128 scans | 99.998% | 51.34% |
| DUFOMap 0.2m voxel | 99.998% | 50.92% |
| BeautyMap baseline, 8m query / 0.2m height cell | 81.15% | 74.36% |
| BeautyMap 12m query | 76.89% | 77.67% |
| BeautyMap all 128 scans | 80.84% | 73.84% |
| BeautyMap upstream-default 0.5m height cell | 89.87% | 42.93% |

More temporal observations and larger voxels modestly improve DUFOMap removal. A larger BeautyMap query sacrifices more static points; coarser height cells trade removal for preservation. These ablation maps were not retested in localization, so they establish no pose-error improvement.

## Scene interpretation and paper applicability

Static scenes have no moving contamination to remove: Raw/DUFOMap projections are identical and differ by only one 0.1m 3D voxel. In moving scenes, low contamination and BeautyMap's static losses constrain possible benefit. Abundant static walls and GICP's matching may already suppress the influence of dynamic points, but separating these effects requires identical consumed scan histories and repeated trials. Persistent-change B reuses frozen static-A maps without calling either cleaner again; this does not test online map updating. Corridor geometry lacks distinctive longitudinal constraints, and the observed localizer instability is separate from dynamic removal.

Projection does erase some information: the new dynamic DUFOMap removes 161 occupied 0.1m voxels but changes only 50 2D pixels; corridor BeautyMap removes 68 voxels but changes zero 2D pixels. A remaining point keeps an XY cell occupied, and one-cell dilation can conceal small gaps. Direct 3D localization still shows no clear gain, so projection alone is insufficient.

[DUFOMap §III / §V-E](https://arxiv.org/html/2403.01449v1#S5.SS5) requires observing a region fully empty at least once and identifies sparse sampling as a limitation. It also evaluates 16-channel semi-indoor data: indoor operation or 16 channels alone do not establish inapplicability. Our partial removal and limited density/voxel improvements are consistent with conservative void classification, without proving a sole cause.

[BeautyMap §IV / §V](https://arxiv.org/html/2405.07283v1#S4) evaluates static preservation and dynamic removal on KITTI and 16-channel semi-indoor data; long-term change detection/map updating is future work. The present small scene, low sensor, query/height settings and disclosed boundary adaptation remain deployment conditions. The supported conclusion is static loss and no demonstrated localization improvement in this configuration, rather than a refutation of the paper.

3D preserves height, occlusion and empty-space evidence; it cannot create absent corridor constraints or update a frozen old map by itself. IR-MCL and AdaM-MCL are 2D localization methods whose original models cannot simply consume 3D clouds. This experiment tests the downstream value of DUFOMap/BeautyMap maps for GICP.

[Capture failures, native truth-copy recovery and incomplete shutdown-tail handling](../../results/analysis/map-2d-3d/diagnostics.json) retain diagnostic scores and source hashes. Published trials were selected for complete recording, not lower pose errors; original sessions remain local.
