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

## Three tests derived from the focused question

The chain is **joint removal/retention → contamination-dependent localization benefit → geometric conditions for that benefit**. M1 combines the former M1/M2; M4/M5 retain their identifiers for historical traceability. The following hypotheses and plans do not imply that new experiments have run.

| ID | Testable claim | Part of the open question |
| --- | --- | --- |
| M1 (former M1/M2 combined) | With repeated observations and trustworthy mapping poses, a cleaning operating point can substantially reduce ghosts while keeping static loss within a preset limit. | Can removal and retention succeed jointly? |
| M4 (rewritten) | With static support and the localizer controlled, greater ghost contamination in test matching regions produces a larger paired error/failure reduction from cleaning; low contamination may yield little gain. | Under which contamination conditions does map improvement help localization? |
| M5 (rewritten) | At comparable DA/SA, point and compute budgets, preserving stable, repeatably observable, distinctive and complementary static structures helps localization more than uniform/threshold-only retention. | Which geometric conditions make retained static structure useful? |

### M1: one joint removal/retention hypothesis

Fix source observations, timestamps, mapping poses and representation. Compare Raw, author cleaners and simple visibility/support thresholds. Report DA and SA jointly, thin-structure coverage and resources; do not turn the two metrics into separate success claims or rely only on an aggregate average. Choose minimum removal, maximum static loss and tolerances on independent development data, then freeze them before new tests.

Existing single-run 3D DA/SA is 46.59%/99.998% for DUFOMap and 74.36%/81.15% for BeautyMap. These observations show a trade-off, not universal static preservation. Native SRRG's 42.31% ghost removal and 99.51% coverage use a different 2D definition and form a separate system observation; estimated SRRG poses cannot be pooled into a supplied-pose controlled ranking.

**Falsification:** within the declared scenes, tolerances and budget, no operating point meets both removal and retention requirements, or apparent retention only follows a relaxed tolerance. Passing M1 alone does not establish localization gains.

### M4: map contamination versus independent localization benefit

Build maps from session A and freeze them. Replay the same independent B with a fixed localizer, common initializations and paired random seeds. Predefine low/medium/high contamination and its location using A geometry or scene design; do not select regions after seeing B errors. Record contamination in matchable regions and repeated/misleading structure, alongside the global dynamic-point fraction.

Prefer explicitly documented controlled-contamination replays with fixed observations and poses. If different dynamic conditions require new acquisitions, report changed static visibility separately rather than treating them as a pure contamination intervention. Within each condition, all methods receive the same inputs. Compare Raw, cleaned maps and simple threshold controls at comparable static retention and resource budgets; report trade-off curves when matching is infeasible.

Define benefit in advance as `Raw error - cleaned-map error`, positive for improvement. Also report orientation/tail errors, matching/tracking failures and output coverage. Score common time windows and retain each group's full-time coverage so missing outputs cannot create an apparently low RMSE. Separate independent scenes/acquisitions from repeated seeds on identical input.

Existing dynamic GICP XYZ RMSE Raw/DUFO/Beauty=0.98/0.98/1.04 cm establishes no gain. The roughly 1% global dynamic fraction is a candidate explanation, not evidence of a contamination-benefit relationship. The controlled relationship, independent repeats and SRRG localization B remain pending.

**Falsification:** the predicted paired-benefit relationship is absent over the declared contamination range after controlling static support, or tuning, missing outputs or extra static data explain the benefit. No localization gain in one scene is distinct from failure to remove dynamic points.

### M5: retained geometry, without prescribing another sensor

Fix map sources, dimension, localizer and B observations. Compare uniform/threshold-only retention with geometry-preserving retention. Select candidate structures using only A geometry and multi-frame stability, such as distributed corners, end walls and differently oriented surfaces; B truth/errors must not determine retained points. Match DA/SA, point count, resolution and compute on development data before held-out evaluation. When exact matching is infeasible, report the frontier rather than attributing gains from simply retaining more points to geometry selection.

Use geometry-rich rooms, parallel corridors and separately labeled visible-corner/end-wall controls. Record spatial/directional coverage, correspondence distribution and weak directions before comparing independent localization. Added-structure controls are different scene conditions, not recovery of the original corridor. Cleaning or selection cannot create complementary structure absent from the original observations.

**Status:** no geometry-retention ablation with matched DA/SA and resources has run. Corridor failure is a boundary observation; earlier Depth trials change localization observations and do not test map selection. A depth camera remains an optional later extension, not the definition of M5.

**Falsification:** no repeatable held-out gain over simple retention, or point count, aggregate SA/DA, additional inputs or compute explains the gain. In that case the extra value of geometry protection is unsupported.

## Former M3: representation and scoring diagnostic

2D projection is a representation/evaluation interface choice. Different 3D point and 2D cell percentages do not alone imply lost cleaning benefit. Retain the existing 8.33%/33.33% projected dynamic-cell removal results, without labeling them partial support or rejection of M3.

To investigate projection, fix source observations and poses and trace remaining support cell by cell under one occupancy definition. Inspect height-band selection, multiple points per cell, dilation and unknown/free-space handling, then test independent localization. Score native 2D SRRG and projected 3D maps separately; unequal denominators cannot establish a cross-representation conclusion.

## Negative results and controls

Static scenes have no dynamic-removal target: DA=N/A. Cleaning cannot create missing corridor constraints. Persistent change requires separate addition/removal/occlusion and map-update tests; frozen-map localization does not evaluate updating. A native SRRG graph-merge numerical crash is an implementation diagnostic, not proof that the paper's assumptions fail.

The earlier [Guard/Depth/Search exploration](HYPOTHESES.md) changes pose estimation with frozen maps; it does not validate M4's contamination relationship or M5's geometry-retention mechanism. SRRG's mapping-tracker error also does not replace a separate AMCL localization-B test.
