# Four papers, one research question

English | [中文](STUDY.zh-CN.md)

The core set is **DUFOMap (2024), BeautyMap (2024), ConceptGraphs (ICRA 2024) and HOV-SG (RSS 2024)**. They connect the two selected themes through a common interface: posed observations become spatial correspondences, then a map decision. The LiDAR methods remove points; the RGB-D methods associate and fuse semantic segments. They solve different tasks, so one aggregate leaderboard would be misleading.

## What each paper establishes, and what remains

| Paper / primary section | Contribution and existing protection | Remaining question relevant to this study |
| --- | --- | --- |
| [DUFOMap](https://arxiv.org/html/2403.01449v1), III-B, V-C, V-E | Void-space evidence; explicit pose and range tolerances. Authors discuss pose sensitivity, sparse returns and regions never seen empty. | Can conservative tolerance separate a shared registration error from a true change without sacrificing change recall? More rays do not guarantee an independently observed void. |
| [BeautyMap](https://arxiv.org/html/2405.07283v1), III-A/C, V | Global binary occupancy, ground adaptation and restoration of out-of-view static points. | A common coordinate system enables comparison but does not certify registration. Which apparent occupancy differences persist because of pose error, and which are actual scene changes? Ground structure is a separate limitation. |
| [ConceptGraphs](https://arxiv.org/html/2309.16650v1), II-A, III-G/H | Geometric and semantic association, incremental fusion; localization and dynamic updates are demonstrated. Authors report missed thin objects, duplicates and caption errors. | When shared pose error causes a wrong association, can later geometric correction recover the original identity and query location? A detection count is not independent geometric evidence. |
| [HOV-SG](https://arxiv.org/html/2403.17846v2), III-A, V | Segment merging, robust semantic feature selection and floor/room/object hierarchy. Authors explicitly identify static-scene, runtime and parameter limitations. | A static feature map cannot express a moved target's temporal validity. How should changing observations be assigned to reference geometry before storing semantic evidence? |

The last column contains our research questions, not claims that the authors measured these failures. The implementation evidence and the paper's stated limitation are different sources of support.

## Shared structure, different failure mechanisms

The shared dependency is **the correctness of the spatial correspondence at the moment a decision is made**. A wrong pose may move a ray into a static surface in DUFOMap, create different occupancy bits in BeautyMap, split/merge object instances in ConceptGraphs, or assign pixel features to the wrong reference points in HOV-SG. Semantic similarity and geometric tolerance are useful protections; neither automatically provides a joint posterior over pose and scene change.

This does **not** mean that all four assume a static world, ignore noise, or lack visibility reasoning. HOV-SG explicitly assumes static scenes; ConceptGraphs already supports updates. DUFOMap models tolerances and BeautyMap restores hidden points. Nor does a narrow code path prove that an entire paper lacks a possible extension.

There are three distinct questions:

1. **Identifiability:** if all visible objects move coherently and no stable reference is observed, camera error and scene motion may be indistinguishable.
2. **Evidence dependence:** many points and repeated frames can share one pose error; counting them as separate information can exaggerate confidence.
3. **Recovery after correction:** a compact fused map may lose which observation caused an association or deletion. Reversible updates need observation provenance, memory and replay time.

These are candidate common limitations of the selected mapping interfaces. The current runs do not establish the same empirical failure across all four systems. Their object counts and LiDAR accuracies measure different quantities.

## A narrower open problem

**Can map updates remain reliable under temporally correlated pose errors, at matched change recall, query coverage and update delay, when stable anchors exist?** The desired result is fewer false static deletions and fewer stale/wrong target coordinates. ATE alone does not answer this question: equal trajectory error can have different temporal structure and downstream effects.

For a locally linear residual, our model is

$$r_{it}=J^p_{it}\delta\xi_t+J^o_{it}\delta o_i+\epsilon_{it}.$$

One shared pose perturbation induces cross-object covariance. In the simplified scalar case, averaging $N$ observations with a common bias leaves variance $\sigma_p^2+\sigma_s^2/N$, rather than $(\sigma_p^2+\sigma_s^2)/N$. This is a mechanism model, not an equation attributed to one of these papers. It cannot identify motion in a scene without independent anchors.

## Feasible hypothesis and its limits

**Candidate H1:** retain a shared pose variable and observation provenance; defer ambiguous association/deletion; after a pose correction, replay only affected observations. With adequate static anchors, this may reduce wrong map decisions against tolerance/visibility and independent-noise baselines at equal coverage, recall and delay.

The smallest implementable version is an object/submap sidecar, not a replacement SLAM backend. Store frame ID, pose version, masks/features and candidate correspondences. Estimate common residuals from static planes or fiducials; use uncertainty to gate a provisional update. Bound the buffer and record replay cost. Without a calibrated estimate, a confidence score is not a probability. Known injected covariance is an **oracle diagnostic**, separate from estimated covariance.

[Khronos](https://arxiv.org/html/2402.13817v2), V-B/C, already performs joint optimization and reconciliation. Consequently, “add memory,” “jointly optimize,” and “undo an update” are not defensible novelty claims. The possible contribution is a small, measured interface between pose corrections and open-vocabulary associations, with dependence calibration and a matched-budget evaluation. Its novelty still requires a broader prior-art check.

## Experiments that can reject the idea

| Control | Keep fixed | Measure / rejection |
| --- | --- | --- |
| Exact, independent and correlated poses | RGB-D, masks/features, marginal translation/rotation RMS, anchors | Association identity and target errors. Equal RMS is not equal time correlation. |
| Tolerance / threshold sweep | Validation data and observation budget | If a simple threshold matches risk at the same recall/coverage/delay, reject an H1 gain. |
| Fixed camera: static, occluded, moved, removed object | Sensor pose and illumination | Visibility errors remain even with exact pose; an uncertainty model must not explain them all away. |
| Few versus coherent-majority movers | Sensor data and reference availability | With no stable anchor, failure is an information boundary; report it. |
| Immediate versus delayed pose correction | Correction magnitude, buffer size | Recovery, stale duration, memory and replay cost; saving objects forever is not success. |

Room0 and the existing synthetic seeds have already informed the proposal. They remain exploratory. Freeze the protocol before viewing a new room or the held-out physical scene. Use scenes/sessions as sampling units, not millions of correlated points as independent samples. Report annotated identity/query correctness, coverage, recall, static loss and delay together.

## What the reproductions currently support

DUFOMap and BeautyMap executed their full 141-frame teaser pipelines; their map evaluation agrees pointwise with the original PCL implementation. The large direct-label/map-score discrepancy is primarily a correspondence effect. It is not an H1 gain or evidence of a shared structural failure.

ConceptGraphs executes SAM/CLIP and original association/fusion on 40 observations. HOV-SG is the fourth selected author pipeline; its delivered scope is listed on [its paper card](papers/hovsg.md). Semantic subset runs establish executable cores, not complete paper benchmark or navigation reproduction. [Paper index](papers/README.md), [physical tests](REAL_WORLD.md), [submission preparation](SUBMISSION.md).
