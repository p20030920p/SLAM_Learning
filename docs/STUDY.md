# How the reproductions support and limit the hypothesis

English | [中文](STUDY.zh-CN.md)

**Spatial correspondence affects map decisions; a common dominant shared-pose-uncertainty bottleneck has not been established.** All four cores ran, but optimize different tasks. Author mechanisms, measurements and our inferences are separated below. [Full paired report](PAIRED_RESULTS.md) · [Raw evidence](../results/reference/paired-pose/record.json).

## What each reproduction achieved

| Core and connection to the hypothesis | Achieved scope and metrics | Remaining gap or counterevidence |
| --- | --- | --- |
| DUFOMap: poses determine ray paths and free-space evidence; the author already models pose/measurement tolerances | Full teaser: map-proximity SA 97.9798%, DA 98.7029%; PCL and SciPy agree pointwise | Not all paper values match within 0.01 pp; no trajectory evaluation. Direct identity and proximity scoring differ by 5.347532 pp, not an algorithm benefit |
| BeautyMap: global occupancy comparisons depend on alignment; hidden static geometry has a recovery mechanism | Same teaser: SA 96.9529%, DA 98.3382%; GT physically excluded from algorithm inputs | Paper gaps remain. “Unseen means deleted” is inaccurate; ground structure and visibility remain separate failure sources |
| ConceptGraphs: geometric and semantic similarity determine association/fusion, connecting pose to identity and query coordinates | 40 observations, 39 objects; 39 saved camera matrices confirm absolute poses. The paired eight-observation reference recovers all four annotated surfaces | Reference restricted queries hit only 2/3. Object count is not association accuracy; complete identity GT, LLM reasoning and dynamic-update evaluation remain unfinished |
| HOV-SG: poses assign pixel features to reference geometry before segment merging | Eight observations, 50 segments and 166,777 points; reference cache replay matches map/features bytewise. All paired tests recover the four surfaces | The 40-observation attempt exited 137 for an unconfirmed reason. Full hierarchy, navigation and online recovery are unfinished; more segments do not imply better semantics |

Achievement here means execution and measurement within the stated scope, not reproduction of every paper result. [Paper cards](papers/README.md) retain settings, sources and failures.

## What is empirically shared

The shared dependency is **posed observation → spatial correspondence → map decision**. Losses and assumptions differ: DUFOMap has tolerances, BeautyMap restores hidden geometry, ConceptGraphs supports updates, and HOV-SG states a static-scene limitation.

The following are means over three seeds at 30 cm RMS. Both semantic cores use the same eight source observations. Metrics describe different tasks and cannot rank methods.

| Metric | Reference | Shuffled | Monotone drift | Interpretation |
| --- | ---: | ---: | ---: | --- |
| DUFOMap direct-label SA % | 92.6341 | 76.5854 | 88.5977 | Pose sensitivity, but drift preserves more static points; DA is 98.9654 / 98.9571 / 98.9231% |
| BeautyMap proximity SA % | 96.9529 | 93.2688 | 95.8456 | Same direction; DA is 98.3382 / 98.1861 / 97.9847%, so deletion recall also matters |
| ConceptGraphs partial-surface coverage | 0.9256 | 0.5991 | 0.3984 | Drift harms fixed-world reference coverage more; target recovery is 1 / 0.6667 / 0.5 |
| HOV-SG partial-surface coverage | 0.9256 | 0.9061 | 0.9136 | Annotated geometry remains relatively stable; no common geometric collapse is established |
| HOV-SG restricted query hit | 0.6667 | 0.6667 | 0.3333 | Retrieval can degrade while surfaces remain; geometry and query validity need separate checks |

Thus **“correlation is always worse” is rejected by counterexamples**. Local consistency might protect relative geometry while world coordinates drift. This explanation fits the results but is not uniquely identified: sorting also changes which view receives each error.

Simple controls are strong competitors. Increasing DUFOMap d_p from 1 to 2 raises reference SA from 92.6341% to 99.7817% while DA falls to 96.3900%. Lowering ConceptGraphs association threshold from 1.2 to 1.0 makes all three 30 cm drift seeds hit all three restricted queries. Any new mechanism must improve on these inexpensive choices.

## What the metrics cannot establish

SA/DA measure static retention and dynamic removal. Semantic coverage measures support for annotated partial surfaces; recovery also requires visible projection precision. Restricted query hits check top-1 correspondence to annotated targets. Surface distance is neither full-object center error nor navigation error. Baseline query misses cannot be attributed to injected poses, and an unannotated instance may still be valid.

The four surfaces are AI-assisted annotations without independent human review; reference images are also mapping inputs, and the exact first pose protects some geometry. Three seeds are not three scenes and their range is not a confidence interval. Both arrangements share pose error across all points in a frame; **shared-variable and independent-variance estimators were not compared**. Static room0 cannot measure real change recall, and final offline maps cannot measure staleness or delayed-correction recovery.

## Open question and candidate H1

**When a later pose correction changes historical correspondence, how can object identity and query coordinates recover, with a measurable bound on exposure to stale results?** Pose sensitivity and the separation between geometry and retrieval motivate the question. They do not yet demonstrate that a recovery mechanism is necessary or beneficial.

Candidate H1 retains observation provenance, shared pose versions, tentative associations and a pre-window checkpoint. After correction it replays every contributor to affected components; queries return coordinates, pose version, validity and timestamp. Start with ConceptGraphs and a proposed 16-observation / 512 MiB budget. Neither the budget nor benefit is measured yet.

First compare the native core, threshold/visibility protection, coordinate correction alone and oracle full replay. If replay adds nothing over coordinate correction, the motivation to recover historical decisions weakens. Only then add independent-variance and candidate shared-pose protection, reporting estimated uncertainty separately from oracle covariance.

Freeze new scenes and independent annotations before inspecting results. Measure coverage, identity fragments, current coordinate error, change recall, stale duration, update latency, replay time and peak memory. Reject the corresponding H1 benefit if simple protection reaches the same frontier, pose correction explains all gains, or lower deletion risk merely retains stale objects longer. Without stable anchors, camera drift and coherent object motion may be unidentifiable.

[Khronos](https://arxiv.org/html/2402.13817v2) already provides joint optimization and map reconciliation; memory or rollback alone is not novel. A bounded interface between pose correction and open-vocabulary target validity is only a potential contribution, pending a broader prior-work check. [Source analysis](LITERATURE.md) · [Next experiment design](REAL_WORLD.md).
