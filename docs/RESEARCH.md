# From reproduction to a candidate bottleneck

English | [中文](RESEARCH.zh-CN.md)

The research order is **reproduction → observations → structural bottleneck → candidate hypothesis → held-out experiments**. Existing controlled results are exploratory: they helped select the question and cannot serve as independent confirmation of that selected hypothesis. This order is a workflow, not a rewritten history of when earlier runs occurred.

## 1. Start with the measured outputs

DUFOMap and BeautyMap completed the same 141-frame teaser on Windows and Ubuntu. Their map-level scores agree across those platforms, but both differ from the corresponding paper targets. DUFOMap's direct-label sensitivity diagnostic also yields a different zero-perturbation score from the output-map nearest-neighbor evaluation. The cause of that gap has not been isolated. [Numbers, artifacts and exact limits](RESULTS.md).

The first unresolved task is therefore a **measurement question**: which points are being judged, under which correspondence rule and implementation path? Before claiming a method fails, reconcile those protocols. Small injected pose errors sometimes improve scores in the current diagnostic; the observations do not justify universal degradation claims.

## 2. What might be shared across methods?

The [literature matrix](LITERATURE.md) traces how poses establish spatial correspondence before cleaning, association or semantic fusion. The possible bottleneck is **insufficient independent constraints on the geometry used to interpret a change**. It has three related parts:

| Part | Why it is structural | Evidence level now |
| --- | --- | --- |
| Identifiability | Shared camera error and coherent object motion can produce the same residual without a stable reference | Controlled counterexample; not a deployed-system observation |
| Evidence dependence | Many points or revisits can share one pose error, so their count is not their independent information content | Analytic derivation and matched synthetic model |
| Commitment before correction | Association/fusion/deletion can be committed before a later pose correction resolves the geometry | Pipeline inference; full feedback loop not reproduced |

[Khronos](https://arxiv.org/html/2402.13817v2) already jointly optimizes poses and structure. [SuperMap](https://arxiv.org/html/2608.22896v1) has visibility/disappearance states; [PerSeM](https://arxiv.org/html/2609.19542v2) has persistent semantic memory and acknowledges correlated geometric limitations. These are constraints on the claim. “Add memory,” “use visibility” or “jointly optimize” cannot be presented as the new idea.

The present cross-field argument is partly inferred. A real semantic-map frontend must be reproduced before asserting that the same empirical failure is common to fields 1 and 2.

## 3. Minimal mechanism

A linearized residual for object i at time t can be written as

$$r_{it}\approx J^p_{it}\delta\xi_t+J^o_{it}\delta o_i+\epsilon_{it}.$$

Pose error $\delta\xi_t$ is shared. With otherwise independent errors,

$$\operatorname{Cov}(r_{it},r_{jt})=J^p_{it}\Sigma_{\xi_t}(J^p_{jt})^\top.$$

In one dimension, readings $r_k=b+\delta+\epsilon_k$ sharing bias b give

$$\operatorname{Var}(\bar r\mid\delta=0)=\sigma_p^2+\sigma_s^2/N.$$

An independent-pose-noise model instead uses $(\sigma_p^2+\sigma_s^2)/N$. That model can become too certain while the shared error remains. These are our simplifying derivations, not equations attributed to a reviewed paper. A full SLAM posterior contains additional correlations.

When most visible objects move together, a median correction can select that moving group as the stable reference. Better thresholds cannot create a missing anchor. IMU constraints, static geometry or an independently localized view may be necessary.

## 4. Candidate hypothesis, not a conclusion

**H1.** At matched observation budget, query coverage and update latency, a change update that accounts for shared pose uncertainty will reduce false deletion and stale-target error relative to visibility-aware thresholds and independent-noise inference, when enough stable geometry or external constraints make pose identifiable.

One possible design keeps shared pose latent variables through association and change decisions, discounts correlated evidence, and defers ambiguous edits. Provisional semantic/geometric updates could be re-associated after pose correction. This complete interface is not implemented here; known estimation ideas alone do not establish novelty.

**Additional conjectures:** stable-anchor selection may matter more than adding semantic memory in high-motion scenes; reversible updates may be useful when pose corrections arrive late. Neither conjecture is tested by the current full-system evidence.

## 5. What the exploratory experiments say

Common-mode correction plus supplied visibility helps in the minority-motion synthetic case, then fails with a moving majority. Shared-latent inference avoids overconfidence in a Gaussian model with known noise scales, but has lower changed-object recall. These results motivate the hypotheses; they do not show an improvement at matched coverage/latency in real semantic navigation. [Full interpretation](RESULTS.md).

## 6. What would count as a test?

First finish evaluator reconciliation and one semantic frontend. Then freeze factors, validation/held-out scenes, thresholds, decision budgets and rejection criteria before the confirmatory run. Keep the existing exploratory seeds out of the confirmation set. [Staged experiment plan](PLAN.md).

Reject or narrow H1 if a swept threshold performs equally well at matched coverage/latency; an independent-noise model does equally well under correlated drift; estimated covariance removes the benefit; or fewer deletions merely leave stale objects longer. A system with no stable reference is outside the identifiable case. Negative results should revise the hypothesis, not trigger a new scoring rule.

<!-- MEDIA: bottleneck-diagram -->
*Figure slot: `docs/figures/bottleneck_diagram.svg`. Show the pose–correspondence–update interface and identify empirical observations separately from conjectured feedback.*
