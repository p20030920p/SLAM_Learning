# Research note: shared pose errors and persistent map updates

**Open problem.** How should a robot commit geometric and semantic map changes when observations share uncertain localization, without simply freezing its map? The target is reliable change evidence at the localization–map-maintenance interface, with consequences for locating semantic navigation targets.

## Structural issue

Many pipelines first establish world-space correspondence using estimated poses, then associate objects, clear points or accumulate semantics. Exact sources are in the [literature matrix](LITERATURE.md). Decisions can be individually sensible and jointly wrong: one pose error shifts several objects, changes depth residuals and misassigns semantic observations.

Our inference is a possible feedback loop: pose error induces mistaken edits, later localization uses the edited map, and evidence for the original geometry is lost. This submission does not claim to have observed the full loop in a deployed system. It isolates mechanisms and tests one author's real-data sensitivity.

[Khronos](https://arxiv.org/html/2402.13817v2) already jointly optimizes poses and structure and reasons about visibility. [SuperMap](https://arxiv.org/html/2608.22896v1) separates unobservable from disappeared objects; [PerSeM](https://arxiv.org/html/2609.19542v2) preserves/refines semantic memory. Neither “joint SLAM,” “add memory,” nor “three states” is claimed as new.

The narrower question is whether **destructive-update confidence is calibrated to shared pose uncertainty and correlated revisits**, including the interval before pose correction. Memory alone cannot guarantee correct world-space correspondence; PerSeM's limitations explicitly leave correlated geometric errors open.

## More than a threshold choice

A linearized mapped-object residual is

$$r_{it} \approx J^p_{it}\delta\xi_t+J^o_{it}\delta o_i+\epsilon_{it}.$$

The pose error $\delta\xi_t$ is shared; object displacement $\delta o_i$ and independent sensor noise $\epsilon_{it}$ are separate. Thus, assuming otherwise independent errors,

$$\operatorname{Cov}(r_{it},r_{jt})=J^p_{it}\Sigma_{\xi_t}(J^p_{jt})^\top.$$

A full SLAM posterior has further correlations. These equations are our analysis, not attributed to the reviewed papers.

In one dimension, readings $r_k=b+\delta+\epsilon_k$ with shared pose bias $b$ give

$$\operatorname{Var}(\bar r\mid\delta=0)=\sigma_p^2+\sigma_s^2/N.$$

Treating pose noise as independent instead gives $(\sigma_p^2+\sigma_s^2)/N$, incorrectly shrinking toward zero. A persistent bias can look increasingly decisive with no new independent pose evidence. Wider thresholds can reduce false edits but suppress real changes; they do not express this information limit.

There is also an identifiability boundary. Coherent motion of every observed object can mimic camera motion without an external reference. A median correction assumes stable anchors dominate. More frames of the same ambiguity supply no missing reference. IMU constraints, stable background, independent localization or an informative new view may be necessary.

## Falsifiable hypothesis

**At matched observation budget, query coverage and update latency, marginalizing shared pose uncertainty before destructive updates will reduce false deletion and stale-target errors relative to visibility-aware fixed-pose and independent-noise baselines, when stable geometry or external constraints make pose identifiable.**

The intervention would retain shared pose latent variables, propagate uncertainty into association/change residuals, and discount correlated evidence. Ambiguous existence or correspondence would defer irreversible edits. Queries would expose current validity; later pose corrections would permit re-association or rollback of provisional changes.

These are established estimation ideas. A prospective contribution would be a practical update interface and calibrated map-change/query-risk evaluation under correlated drift, not the first Bayesian map or temporal graph. The complete intervention is not implemented here. Synthetic common-mode correction is a limited mechanism prototype, not probabilistic SE(3) SLAM.

## Evidence obtained

Two pinned author-method runs establish geometric baselines; both differ from paper targets. Six DUFOMap runs vary pose margin and inject a smooth translation into real scans. They show a retention/detection tradeoff and modest, nonmonotonic perturbation effects, not catastrophic failure or semantic-navigation gains.

Paired object trials separate visibility handling from common-mode correction. With 20% movers, 0.3 m shared pose bias and 50% occlusion, combining them reduces static false-change rate from 100% to 0.83%. At 80% coherent movers it fails, exposing the anchor assumption. A Gaussian evidence experiment shows overconfidence from an incorrect independent-noise model; shared-latent inference remains calibrated with known scales but detects fewer changed objects. See [coverage and negative findings](RESULTS.md).

Perfect identities/visibility and oracle noise scales deliberately remove frontend difficulty. Success under those assumptions is insufficient evidence for real semantic performance.

## Next discriminating experiment

Hold the frontend and pose trajectory fixed on a dynamic multi-session scene with independent pose, identity, visibility and target-coordinate ground truth. Score using independently annotated correspondence; nearest-neighbor map scoring alone may mask misregistration. Compare swept fixed-pose thresholds/margins, visibility gating, independent pose variance, shared-latent inference, and an informed joint system such as Khronos where feasible.

Vary translation, rotation, temporal correlation at fixed marginal error, pose-correction delay, anchor fraction, occlusion and removed objects. Compare exact poses, independent noise and correlated drift. Select parameters on separate validation scenes and report held-out per-scene intervals.

Measure false deletion, motion recall, identity fragmentation, calibration, target-coordinate risk, query coverage, update latency and compute. Use risk–coverage and risk–latency curves so abstention cannot masquerade as improvement. The current KITTI teaser has no semantic instance/navigation labels and cannot answer this next question.

Reject or revise the hypothesis if benefits vanish at matched coverage/latency, independent variance performs equally well under correlated drift, realistic estimated covariance removes the benefit, or reduced deletion merely leaves obsolete targets longer. Failure without a stable reference is expected; claiming to solve it without information would contradict identifiability.

## Contribution boundary

The completed contribution is a cross-paper structural argument, an executable evidence pipeline, author-code measurements and controlled tests with failure boundaries. Full semantic integration, active viewpoint selection and robot navigation remain future work and are never marked complete.
