# Open question analysis for dynamic robust localization and SLAM

English | [中文](DESIGN.zh-CN.md)

**Direction: Robust localization and SLAM in dynamic environments.** Retain the open question: **What strategies enable localization self-recovery under degradation and substantial environmental change?** Deliver author-code reproductions and progressively harder point-cloud mapping/localization tests on the Sim2Real-AlgoBench robot.

## Is the question reasonable

Yes: nominal accuracy, avoiding failure during interference and recovering after failure are distinct capabilities. Dynamic map traces, weak geometric constraints and persistent map mismatch can affect localization. A low average error does not establish recovery from a failed state.

Recovery is an existing research topic: [AdaM-MCL](https://arxiv.org/abs/2009.00211) addresses global localization/kidnapping, [IR-MCL](https://arxiv.org/abs/2210.03113) studies observation models, [X-ICP](https://arxiv.org/abs/2211.16335) considers localizability, and [LILocBench](https://www.ipb.uni-bonn.de/html/projects/localization_benchmark/) evaluates environmental change. These establish relevance, not an empty field or novelty of this proposal.

## Why it remains broad

| Term | Specify | Risk otherwise |
| --- | --- | --- |
| Degradation | Geometry, occlusion, sensor quality or engineering errors | Mix different failure mechanisms |
| Substantial change | Temporary motion versus persistent visible structural change | Equal change percentages need not imply equal difficulty |
| Self-recovery | Correct pose in the original map frame versus continued output/new local map | Continue moving without recovering global location |
| Effective | Success, latency, false recovery, recurrence, normal-operation cost | Reward a system that always outputs an incorrect pose |
| Strategy | Observation/map processing, relocalization, fusion or active motion | Expand across too many system layers |

Narrow conditions, recovery target and comparison scope before choosing an implementation.

## Two mechanisms

Degradation weakens constraints. Characterize weak pose directions and whether information returns. If distinct poses remain indistinguishable under available observations/history/priors, unique recovery cannot be guaranteed.

Persistent change makes a prior map partly obsolete. Rich observations can still conflict with it. Relocalization alone need not fix mismatch, while sufficiently visible unchanged structure can still support the old map. Measure its geometry and visibility rather than only global change percentage.

These mechanisms can coexist. Test factors separately before combining them; exclude TF, timing and calibration faults with a healthy engineering baseline.

## Recovery definition

Without a human providing the correct pose, recover a trustworthy pose in the **original map frame** after failure and maintain position/orientation limits. Keep relocalization, fusion, observation processing and map interventions open as strategies.

Small covariance, concentrated particles or resumed output do not independently establish correctness. Score local-map restart, connection to the original map and original-frame recovery separately. Ground truth evaluates decisions but never triggers them.

Report fault-to-recovery and information-return-to-recovery time separately; the former includes waiting for usable constraints.

## Ways to narrow

| Path | Question | Stage |
| --- | --- | --- |
| A Temporary dynamic occlusion | After occlusion removal, can stable structure support automatic recovery; how do duration/severity affect it? | First single-factor recovery experiment |
| B Persistent local change | Which remaining unchanged structure supports recovery, and which part is solved by map processing versus relocalization? | Once visible change is quantified |
| C Exit from degradation | After drift in a repetitive corridor, can returning to informative geometry restore the original-frame pose? | Once directional failure is reproducible |

Suggested discussion question: **After dynamic interference or local map change causes localization failure, under what conditions can the system automatically recover a trustworthy original-frame pose once informative structure is observed again?**

Start with one path, possibly A; extend to B/C using measured failure evidence. This narrows the failure/recovery conditions without prescribing temporal triggering or another method.

## Subquestions

1. Which observations, map mismatches or motion-estimation conditions cause failure?
2. When information returns, does the system recover, remain confidently wrong or require an additional action?
3. Which intervention addresses that measured failure without harming healthy operation?

## Deliverable one Author-code reproduction

| Group | Native reproduction | Connection |
| --- | --- | --- |
| DUFOMap/BeautyMap | Author data/config and map-quality evaluation | Traces versus preserved static constraints |
| IR-MCL | Author weights, released sequence and native evaluation window | Observation model/global localization |
| AdaM-MCL | Author data/weights/training and global localization/kidnapping protocol; disclose inaccessible parts | Proposal sampling and mixture updates |
| Later registration/SLAM baselines | Verify public source/data after 3D input readiness | Coupling of pose drift, map corruption and degeneration |

Running code, compatible reproduction, native-protocol score matching and platform adaptation are distinct completion levels. A custom map and shortened training cannot replace the paper experiment. Retain revisions, data/weights, settings, patches, logs, raw outputs and scores. Use each paper's own metrics; robot-transfer comparisons belong to the second deliverable.

## Deliverable two Progressive robot tests

Use the [Sim2Real-AlgoBench](https://github.com/p20030920p/Sim2Real-AlgoBench) three-wheel omnidirectional chassis. Keep the native 2D profile and add an independently versioned 3D LiDAR profile. [Test protocol](../testing/PROTOCOL.md).

Separate supplied-pose point-cloud mapping, fixed-map localization and estimated-pose mapping/SLAM. Progress from interface acceptance to rich static geometry, moving objects, temporary occlusion, geometric degradation, persistent change and combined stress. Increase one factor per family and measure actual difficulty.

## Relationships to test

| Relationship | Control | Counterexample |
| --- | --- | --- |
| Cleaner map versus easier recovery | Common input on raw/filtered maps; normal accuracy and recovery separately | Filtering removes useful constraints |
| Better nominal model versus larger recovery range | Match budget/map; vary initial error and occlusion | Improves converged accuracy but not recovery |
| Stable structure versus obsolete-map recovery | Vary visible unchanged structure/distribution | Large change still permits recovery, or small symmetric change prevents it |

Reproducible counterexamples help narrow the question. Assess algorithmic novelty after mechanism analysis and strong baselines.

## Evaluation and delivery

Evaluate static preservation/dynamic traces/observed-region geometry, full-time pose errors/failure incidence, sustained recovery, censored failures, latency, incorrect recovery, recurrence and human interventions. Include healthy-operation disruption and resources. Freeze scoring on validation data and retain failed episodes.

Deliver **verifiable native reproductions, progressive mapping/localization tests, and evidence-based failure/recovery boundaries** before selecting a new recovery method. [Chinese talk](TALK.zh-CN.md) · [Status](STATUS.zh-CN.md).
