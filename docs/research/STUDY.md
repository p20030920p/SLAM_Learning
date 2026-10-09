# Research analysis

English | [中文](STUDY.zh-CN.md)

## open questions:

How can multi-frame mapping prevent localization errors from causing persistent mistakes in static-structure filtering and object association?

## Shared interface

The two directions meet at **pose → correspondence → map decisions**. Dynamic mapping decides which geometry to retain; semantic mapping decides which observations belong to an object and where a query points. Correcting coordinates need not revise decisions made under the earlier alignment. This is our inference, not an observed common dominant defect.

| Related paper | Pose-dependent decision | Existing protection / unresolved boundary |
| --- | --- | --- |
| [DUFOMap](../papers/dufomap.md) | Rays establish void regions used for point classification | Pose/measurement margins already exist; never-observed empty space remains ambiguous |
| [BeautyMap](../papers/beautymap.md) | Registered occupancy drives removal/restoration | Static restoration already exists; alignment and grid/ground assumptions still matter |
| [ConceptGraphs](../papers/conceptgraphs.md) | Geometric/semantic similarity drives object fusion | Thresholds and later observations may suffice; corrected geometry does not itself reassign fixed members/features |
| [HOV-SG](../papers/hovsg.md) | | In progress |

The executed mapping experiments use supplied poses. Larger original-code runs and scoped semantic scores are [pinned separately](https://github.com/p20030920p/SLAM_Learning/blob/535a2780af7ca7eb3aa02f722e1340fe90bc2dcf/docs/SCOPE.md). They do not establish trajectory accuracy or navigation success.

## ConceptGraphs

Its association traces expose observation membership, support counts and fused features. With one frozen frontend and identical exact historical correction, fixed membership can be compared with reassociation. This separates coordinate error, low-support filtering and association history. DUFOMap/BeautyMap motivate the geometric interface; their reproduction scores do not test this delayed-correction hypothesis.

## Evidence

The [delivery evidence](../../README.md#evidence) compares each reproduced method only with its own paper: DUFOMap Table IV, BeautyMap Table III and ConceptGraphs Table II. Dataset, sequence, frame count and metric definitions are stated beside the values. ConceptGraphs room0 has different coverage from the paper benchmark and is labelled as reference-only.

Earlier [room0 pose controls](PAIRED_RESULTS.md) and [room1 delayed-correction controls](DELAYED_RESULTS.md) remain exploratory records, separate from paper reproduction. They show that simple safeguards and later observations can also recover selected targets; they do not establish the necessity of reassociation.

## Hypothesis

We hypothesize that retaining the observation evidence behind map updates and revisiting these updates as pose estimates improve will reduce persistent mapping errors and preserve more consistent geometric and semantic maps

This research hypothesis remains unverified. Existing exploratory experiments diagnose object association after supplied pose corrections; they do not yet test revisiting static-structure filtering or establish a benefit across methods. Object annotations have not been independently reviewed, and this wording does not turn historical experiments into confirmatory tests.

## Next decision

Simple threshold, visibility and support controls test whether any reassociation benefit warrants additional complexity. Bounded replay is a possible later implementation, not the hypothesis tested by the current full-history oracle experiments; no bounded implementation has been built or tested.

room2 fixes five AI-labelled instances, held-out reference frames and one frontend. All 28 mapping cells ran; analysis remains pending. Support 1/2/3 and caps 25/50/100/unlimited are readouts of complete pre-filter snapshots. Category-query hits and physical identities are separate; unlabelled candidates are unknown. [Frozen exploratory protocol](https://github.com/p20030920p/SLAM_Learning/blob/4361d4f353a7449c7d6964887643915d2fc72a11/docs/IDENTITY_BUDGET.md).

At matched RMS, support and endpoint, oracle must beat every simple control by ≥10 mean percentage points at two finite caps, with ≥2/3 positive paired seeds and no seed increasing labelled duplicates/mixes. Only then propose a bounded prototype. Matching controls weaken the case for that prototype; this gate is separate from testing reassociation against the fixed-association baseline. Equal caps do not match points or memory; AI-only labels cannot confirm H1. [Next steps](PLAN.md).

[Khronos](https://arxiv.org/html/2402.13817v2) already reconciles maps; [DovSG](https://arxiv.org/html/2410.11989v2) already updates scene graphs. The potential contribution is a measured recovery–cost benefit over existing protections, not memory/replay alone. Shared uncertainty as a universal cause, dynamic change recall and hardware H1 validation remain unestablished.
