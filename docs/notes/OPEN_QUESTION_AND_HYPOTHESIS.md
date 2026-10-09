# Late pose correction and trustworthy semantic targets

English | [中文](OPEN_QUESTION_AND_HYPOTHESIS.zh-CN.md)

This is a candidate research design, not a completed recovery module. The current frozen implementation/protocol is on [identity-budget-v2](https://github.com/p20030920p/SLAM_Learning/blob/4361d4f353a7449c7d6964887643915d2fc72a11/docs/IDENTITY_BUDGET.md). Hardware execution is recorded on the separate [physical branch](https://github.com/p20030920p/SLAM_Learning/tree/notes/personal-study-guide-20261008/src/physical).

## 1. Question and motivation

After late pose correction, can bounded provenance restore object identities and query coordinates while limiting exposure of stale answers?

DUFOMap/BeautyMap expose geometric map decisions; ConceptGraphs/HOV-SG expose semantic correspondence and retrieval. Supplied-pose cores do not evaluate ATE/RPE or navigation. Existing protections are strong: DUFOMap Table IV matches 15 entries and BeautyMap Table III matches nine.

Paired tests reject universal correlation harm. At 30 cm, DUFOMap drift retains more static points than shuffled errors; HOV-SG can retain geometry while queries degrade. Partial AI surfaces, shared mapping/reference frames and three seeds from one scene do not establish a common dominant cause. [Author evidence](AUTHOR_RESULTS_ANALYSIS.md) · [Paired results](../research/PAIRED_RESULTS.md).

## 2. Output and prior work

Distinguish a correct identity at a wrong coordinate, wrong identity near valid geometry and a moved/removed object with a stale answer. Report coordinate frame, source pose version, support time and valid/provisional/stale/unrecoverable state. Version consistency alone does not prove current object existence.

[Khronos](https://arxiv.org/html/2402.13817v2) and [DovSG](https://arxiv.org/html/2410.11989v2) already reconcile or update maps. Memory/replay alone is not novel. The candidate contribution is a measurable interface between late correction, provenance limits, target validity and abstention cost; neither is reproduced as a comparative baseline here.

## 3. H1-R and H1-U

**H1-R, candidate:** with recoverable observations/dependencies, replaying association/fusion from a checkpoint improves identity/coordinates over corrected geometry with fixed associations, at matched coverage/latency. Full replay B5 is an author-core reference, not independent truth.

The proposed source cache holds at most 16 observations or 512 MiB, whichever binds first. Checkpoints, indexes, map, RSS and VRAM cost extra. Record evictions and out-of-window failures. Recoverability needs a suitable checkpoint and closed contributor/candidate dependencies; otherwise rebuild or report unrecoverable. Start with the whole retained window before claiming selective replay is exact.

**H1-U, separate candidate:** at identical provenance/replay/budgets, a calibrated shared-pose uncertainty estimator improves risk–coverage–latency over independent variance. A shared version number is not that estimator; known injected covariance is oracle information. H1-R success does not prove H1-U.

## 4. Proposed tests and rejection

The older hardware/recovery proposal uses 40 observations, world-x 0→10 cm error on observations 8–15 and corrections at 16/24/36. It is a deterministic intervention, distinct from the newer frozen room2 protocol. Device sessions use static/occluded/moved/removed-visible events, independent labels and measured references; D435 has no IMU, and L2 is not a calibrated fusion system.

Hold inputs, masks, features, thresholds and evaluation fixed. First compare native/simple guards/geometry-only/full replay and replay-only B4-R. Only later compare B3 against B4-U with the same replay, changing the uncertainty model alone.

Reject extra recovery benefit if corrected geometry or simple guards match the independent quality/coverage/latency frontier. Retaining stale objects is a cost, not a free deletion improvement. Without stable anchors, pose and coherent motion can be unidentifiable. Predeclare meaningful differences and reference tolerances; an inconclusive sample is not equivalence.

The [Chinese design](OPEN_QUESTION_AND_HYPOTHESIS.zh-CN.md) preserves detailed controls. Current evidence has not verified either hypothesis; no bounded-memory result or confidence interval is prefilled.
