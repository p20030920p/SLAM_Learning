# Reproduction and experiment plan

English | [中文](PLAN.zh-CN.md)

The hypothesis remains a candidate until the reproduction gates below are met. The existing synthetic seed sets are exploratory and must not be reused as held-out confirmation.

| ID | Work | Exit condition | Current state |
| --- | --- | --- | --- |
| R0 | DUFOMap / BeautyMap author execution | Version, data, return code and output checks; publish measured/table differences | Executed on Windows, Ubuntu CI and local WSL; table differences remain |
| R1 | Reconcile map NN / direct labels / original PCL | Same point identity and threshold; attribute each score difference | PCL/SciPy agree; direct/map scoring effect measured; paper-version and small API remainder open |
| R2 | More real scenes, qualitative output | Same camera/ROI across methods; per-scene rather than one pooled number | Measured replay published; more scenes remain open |
| R3 | One semantic-map frontend | Author baseline, poses, object associations and queried coordinates reproduced | ConceptGraphs 40-observation subset executed; annotated accuracy/full scene remain open |
| B0 | Retain or revise the bottleneck | Identify an observed shared failure and an explicit counterexample | Candidate; geometry-to-semantics inference not yet confirmed |
| H0 | Freeze hypothesis and protocol | Commit held-out scenes/seeds, thresholds, coverage/latency budgets and rejection rule | Not frozen |
| E0 | Pose magnitude versus correlation | Exact poses, independent errors and correlated drift with matched marginal error | Planned |
| E1 | Anchors, visibility and scene changes | Static/moved/removed/occluded identities; minority and majority movers | Exploratory toy exists; real extension planned |
| E2 | Update and query risk | Compare at matched coverage, recall and latency; record stale duration | Planned; current toy alone cannot decide |
| V0 | Publish animation/video | Render from scored labels and bind camera/run/frame metadata | Map replay and API figure published; semantic/drift videos reserved |

## First semantic reproduction

Start with the author's offline object-map construction and query interface, not a navigation stack. [ConceptGraphs code](https://github.com/concept-graphs/concept-graphs) is a candidate because geometry/semantic association is inspectable. Before installing it, pin a runnable revision and record its dataset, checkpoints and depth/pose sources. Check GPU memory against the actual pipeline; the current CPU lockfile is not a ConceptGraphs environment.

The baseline deliverable is one map built from original author settings, object association traces, and a query returning world coordinates. If known poses fail to reproduce that baseline, fix setup before injecting drift. HOV-SG is an alternative if its data/dependencies are easier to establish. The ConceptGraphs subset frontend has now executed; HOV-SG remains unexecuted. [Semantic baseline](SEMANTIC.md).

## Candidate confirmation factors

Hold the frontend fixed. Sweep translation and rotation, stable-anchor fraction, mover fraction, occlusion and pose-correction delay. Separate error magnitude from temporal correlation. Include unchanged and genuinely removed objects; hidden is not removed.

Compare swept thresholds/margins, visibility gating, independent pose variance and shared-latent inference. Joint systems such as Khronos provide an informed counterexample where integration is feasible. Use validation scenes for all parameters; keep held-out environments and seeds unseen until H0 is committed.

## Decision variables

Measure static false deletion, change recall, identity fragmentation, probability calibration, current-target coordinate error, query coverage, stale duration, latency and compute. Publish risk–coverage and risk–latency curves rather than one favorable operating point. Keep world-coordinate query error separate from SLAM ATE and executed navigation success.

## Media tied to the stages

R0/R2 feed the raw–removed–retained animation; R1 feeds the correspondence figure; R3 feeds the semantic-map query video; E0 feeds the pose-drift animation; E2 feeds risk curves. The [media index](figures/README.md) contains filenames, captions and evidence requirements. A reserved filename is not a result.

## Stop or revise

Do not advance to a confirmatory claim if the baseline measurement is unresolved. Revise H1 if simple threshold sweeps match its benefit, independent variance is sufficient, covariance estimates are uncalibrated, or reduced deletion increases stale-target time. Report majority-motion failure as an information boundary rather than excluding the scene.
