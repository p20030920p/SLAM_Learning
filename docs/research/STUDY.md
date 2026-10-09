# From four reproductions to one testable question

English | [中文](STUDY.zh-CN.md)

## Open question

In object-centric semantic mapping, when previously estimated camera poses are corrected, does recomputing the associations between past observations and map objects reduce object fragmentation and false merges compared with updating the map geometry while keeping the original associations unchanged?

If reassociation reduces these mapping errors, does it also improve text-based object retrieval, so that a query such as “chair” is more likely to return a correctly mapped chair as its top-ranked result?

## The common interface, and its limits

The two directions meet at **pose → correspondence → map decisions**. Dynamic mapping decides which geometry to retain; semantic mapping decides which observations belong to an object and where a query points. Correcting coordinates need not revise decisions made under the earlier alignment. This is our inference, not an observed common dominant defect.

| Reproduced work | Pose-dependent decision | Existing protection / unresolved boundary |
| --- | --- | --- |
| [DUFOMap](../papers/dufomap.md) | Rays establish void regions used for point classification | Pose/measurement margins already exist; never-observed empty space remains ambiguous |
| [BeautyMap](../papers/beautymap.md) | Registered occupancy drives removal/restoration | Static restoration already exists; alignment and grid/ground assumptions still matter |
| [ConceptGraphs](../papers/conceptgraphs.md) | Geometric/semantic similarity drives object fusion | Thresholds and later observations may suffice; corrected geometry does not itself reassign fixed members/features |
| [HOV-SG](../papers/hovsg.md) | Poses attach features to geometry before segment fusion | External odometry is a safeguard; static-scene and hierarchy limits differ from object-map association |

These are mapping-core reproductions, using supplied poses. Larger original-code runs and scoped semantic scores are [pinned separately](https://github.com/p20030920p/SLAM_Learning/blob/535a2780af7ca7eb3aa02f722e1340fe90bc2dcf/docs/SCOPE.md). They do not establish trajectory accuracy or navigation success.

## Why start with ConceptGraphs?

Its association traces expose observation membership, support counts and fused features. With one frozen frontend and identical exact historical correction, fixed membership can be compared with reassociation. This separates coordinate error, low-support filtering and association history. DUFOMap/BeautyMap motivate the geometric interface; HOV-SG checks that semantic coverage and retrieval can differ. None is silently counted as another delayed-correction replication.

## What the experiments established

Early room0 controls use three seeds at 30 cm RMS; the semantic cores share eight observations. [Full paired study](PAIRED_RESULTS.md).

| Metric | Zero error | Shuffled error | Monotone drift |
| --- | ---: | ---: | ---: |
| DUFOMap direct-label SA % | 92.6341 | 76.5854 | 88.5977 |
| BeautyMap proximity SA % | 96.9529 | 93.2688 | 95.8456 |
| ConceptGraphs partial-surface coverage | 0.9256 | 0.5991 | 0.3984 |
| HOV-SG partial-surface coverage | 0.9256 | 0.9061 | 0.9136 |
| HOV-SG restricted query hit | 0.6667 | 0.6667 | 0.3333 |

Correlation is not uniformly worse; geometry and retrieval are different outcomes. These metrics do not rank methods. Three seeds are not three scenes, and these controls do not compare shared-latent versus independent-variance estimators.

room1 then tested late correction. At observation eight and 30 cm, fixed history recovers 11.1%, oracle 66.7%, while a post-hoc support-1 control reaches 100% with 117 candidates versus oracle's 25. Later observations also repair part of the deficit. **This counterevidence weakens the necessity of reassociation.** Partial plant/vase labels and unlabelled fragments prevent a full identity conclusion. [35 frozen cells and six separate post-hoc controls](DELAYED_RESULTS.md).

## Hypothesis

For the delayed pose corrections studied here, we hypothesize that reprocessing historical observations with corrected poses to recompute object associations and fusion will reduce duplicate fragments and mixed objects among the annotated instances compared with rebuilding map geometry while keeping the original observation-to-object associations unchanged.

We further hypothesize that reassociation will improve the top-1 hit rate of text-based category queries within the annotated evaluation set compared with the same fixed-association baseline. Both comparisons use the same RGB-D observations, segmentation masks, frontend semantic features, corrected poses, minimum detections per object, and candidate limit.

Identity errors and query hits are evaluated separately: improvement in one does not establish improvement in the other. These hypotheses remain unverified, and the current object annotations have not been independently reviewed. The existing experiments are exploratory; this wording does not make them a new confirmatory test.

## Next decision

Simple threshold, visibility and support controls test whether any reassociation benefit warrants additional complexity. Bounded replay is a possible later implementation, not the hypothesis tested by the current full-history oracle experiments; no bounded implementation has been built or tested.

room2 fixes five AI-labelled instances, held-out reference frames and one frontend. All 28 mapping cells ran; analysis remains pending. Support 1/2/3 and caps 25/50/100/unlimited are readouts of complete pre-filter snapshots. Category-query hits and physical identities are separate; unlabelled candidates are unknown. [Frozen exploratory protocol](https://github.com/p20030920p/SLAM_Learning/blob/4361d4f353a7449c7d6964887643915d2fc72a11/docs/IDENTITY_BUDGET.md).

At matched RMS, support and endpoint, oracle must beat every simple control by ≥10 mean percentage points at two finite caps, with ≥2/3 positive paired seeds and no seed increasing labelled duplicates/mixes. Only then propose a bounded prototype. Matching controls weaken the case for that prototype; this gate is separate from testing reassociation against the fixed-association baseline. Equal caps do not match points or memory; AI-only labels cannot confirm H1. [Next steps](PLAN.md).

[Khronos](https://arxiv.org/html/2402.13817v2) already reconciles maps; [DovSG](https://arxiv.org/html/2410.11989v2) already updates scene graphs. The potential contribution is a measured recovery–cost benefit over existing protections, not memory/replay alone. Shared uncertainty as a universal cause, dynamic change recall and hardware H1 validation remain unestablished.
