# Narrowing the question to dynamic mapping

[中文](MAPPING-FOCUS.zh-CN.md) · [Main article](../../README.md#hypothesis) · [Map metrics and timestamps](MAP-METRICS.zh-CN.md)

Reliable mapping and localization in changing environments is a useful broad direction. Recovery under degradation and large change combines missing constraints, obsolete maps, false matches and relocalization. A cleaner and one RMSE cannot answer all of these. The current intervention is at the map layer, controlling mapping poses and the downstream localizer.

**Focused question: given multi-frame scans and mapping poses, how can dynamic traces be removed while retaining static structure, and when does this map improvement reduce held-out localization error?** Cleaner maps are an intermediate outcome, not a sufficient condition for accurate pose. Supplied-pose mapping isolates cleaning; it does not validate an autonomous SLAM pipeline.

| Paper-visible problem | Testable subproblem | Scope boundary |
| --- | --- | --- |
| [DUFOMap](https://arxiv.org/html/2403.01449v1): 3D visibility/void evidence | Does repeated visibility support removal without static loss? | Mapping poses are inputs; it does not recover missing geometry or estimate the trajectory. |
| [BeautyMap](https://arxiv.org/html/2405.07283v1): clean an existing global 3D map and restore static points | Removal/retention trade-off under small indoor settings | Offline cleaning, not online SLAM or a recovery algorithm. |
| [SRRG, IROS 2018](https://iris.uniroma1.it/handle/11573/1340118): 2D registration, merging and long-term maintenance | Can native 2D remove ghosts, and does tracking remain healthy? | Short known-start sessions here; not a full long-term multi-session reproduction. |
| IR-MCL / AdaM-MCL | Observation models and pose proposals on a known map | Localization references, not map cleaners. |

DUFOMap evaluates KITTI, Argoverse 2 and semi-indoor 3D scans; BeautyMap evaluates KITTI and semi-indoor maps; SRRG includes LCAS–STRANDS and MIT Stata multi-session settings. Our short-range, small indoor, sparse 16-line simulator differs from those protocols. Lower transfer scores alone do not establish paper inapplicability. [Input/dataset audit](MAP-2D-3D.md) · [SRRG scope](../papers/srrg_mapper2d.zh-CN.md).

## Sequential hypotheses and simple tests

| Order | Hypothesis / controlled test | Existing evidence / status |
| --- | --- | --- |
| M1 | Repeated visibility can remove ghosts; compare identical Raw/cleaner inputs | 3D DUFO/Beauty remove 46.59%/74.36% of dynamic points; native 2D SRRG removes 42.31% of verified ghost cells. Removal exists; denominators differ. |
| M2 | Static constraints can survive cleaning; score retention alongside removal | 3D DUFO/Beauty retain 99.998%/81.15% of static points; SRRG 2D coverage is 99.51%. Beauty loses substantial static support here. Coverage is not complete geometric accuracy. |
| M3 | Representation changes preserve the benefit; re-score the same projected maps | DUFO/Beauty remove only 8.33%/33.33% of dynamic 2D cells. Partially supported; point/cell denominators cannot be interchanged. |
| M4 | Cleaning improves B only when ghosts corrupt informative constraints | About 1% of Raw points are dynamic; GICP=0.98/0.98/1.04cm. No established gain. Next: freeze the localizer, vary contamination/occlusion, require a preset static-retention floor and repeat on common time windows. This dose-response test is pending. |
| M5 | Temporal depth visibility can preserve occluded static structure with cheap sensors | Proposed mapping intervention: native 2D SRRG + depth visibility gate; delete only after repeated free-space evidence, retain unknown under occlusion, confirm new structure across frames. Compare 2D-only, 2D+depth and 3D reference on removal/retention before held-out B. Untested. |

M5 requires calibrated extrinsics, synchronized inputs and explicit handling of depth FOV/missing values. Not seeing a surface is insufficient deletion evidence. Begin with one fixed temporal gate before adding confidence or semantics. Native SRRG already rejects the premise that removal necessarily requires 3D.

## Negative results and controls

Static scenes have no dynamic-removal target: DA=N/A. Cleaning cannot create missing corridor constraints. Persistent change requires separate addition/removal/occlusion and map-update tests; frozen-map localization does not evaluate updating. A native SRRG graph-merge numerical crash is an implementation diagnostic, not proof that the paper's assumptions fail.

The earlier [Guard/Depth/Search exploration](HYPOTHESES.md) changes pose estimation with frozen maps. It does not validate M5 mapping. SRRG's mapping-tracker error also does not replace a separate AMCL localization-B test.
