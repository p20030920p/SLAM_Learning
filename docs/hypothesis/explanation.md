<!-- HYPOTHESIS_PART:common -->
**Core: use temporal support for scan alignment and dynamic-trace cleaning to build a 2D map for subsequent localization.** H2 separately tests point-time compensation. Each equation group is explained below; **the three bold, boxed equations are the core algorithm equations**.

**Experiment convention.** A builds the maps; B is acquired independently. Within each experiment, $M_0$ is the baseline and $M_1$ the intervention. Build both from the same A, freeze them, then evaluate with identical B scans, odometry, AMCL parameters and initialization. Truth enters post-run evaluation only.

| Symbol | Meaning |
| --- | --- |
| $T_k^o$ / $T_k$ | Wheel-derived sensor pose / H1-corrected pose at frame $k$, both sensor-to-fixed-map transforms |
| $c$ / $\mathbf x_c$ | A 5 cm grid cell / its center |
| $b$ | A 0.5 s time bin; each evidence type contributes at most once per bin |
| $\mathbf1[\cdot]$ | Indicator: 1 if true, otherwise 0 |
| $M$ | A nonempty set of occupied-cell centers, distinguished from the full grid used by AMCL |

Coordinates are in metres; experiment tables convert distance errors to cm. Score point sets in the same frame before inflation; generate and inflate AMCL grids by the same rule across controls. An empty map is a mapping failure.

**1. Common evaluation equation: localization RMSE on frozen maps.**

$$
E_{{\rm loc},m}=\sqrt{\frac{1}{|\mathcal T|}\sum_{k\in\mathcal T}\|\hat{\mathbf p}_{m,k}-\mathbf p_k^*\|_2^2}.
$$

$\hat{\mathbf p}_{m,k}$ is the estimated 2D robot position on $M_m$; $\mathbf p_k^*$ is position truth at the same time; $m\in\{0,1\}$. Square each position distance, average, then take the square root. Test localization improvement with $E_{{\rm loc},1}<E_{{\rm loc},0}$.

$\mathcal T$ contains only common times with valid outputs from both controls. Current scoring uses 10 Hz times after 5 s warmup and outputs no older than 0.15 s; an empty set is not scored. Across H1 trials, $k$ indexes both trial and time, pooling all common valid samples. Missing-output times are excluded, so this RMSE is not localization success rate. Complete navigation arrival outcomes were not measured.

**Spoken explanation:** freeze the A maps, apply the same localizer to independent B, and check whether the map change reduces pose error. This is an evaluation requirement; the algorithm does not directly minimize AMCL error.
<!-- /HYPOTHESIS_PART:common -->

<!-- HYPOTHESIS_PART:h1 -->
**H1: first correct each 2D scan's position and heading, then use repeated observations to decide which occupied records to remove, and finally test whether the resulting map improves a separate localization session.**

**During mapping:** wheel odometry supplies an approximate scan pose. Align it to structure observed in multiple earlier time bins to reduce the accumulation of the same wall at different positions. This includes pose correction as well as point removal.

**When to delete:** divide the map into 5 cm cells and observations into 0.5 s bins. Repeated measurements within one bin contribute once per evidence type. For each cell, separately count bins with a return within 10 cm and bins with a valid free ray crossing the cell. Rays stop 15 cm before returns. Delete an occupied record only when free crossings occur in at least three bins and their count is at least 1.5 times neighborhood hit support. Being rarely observed or subsequently occluded is not sufficient evidence of motion.

**What to test:** hypothesize that alignment plus cleaning removes more dynamic traces than wheel-pose accumulation while losing at most one percentage point of observed static-reference coverage. Stop updating the maps, acquire independent B, and run the same AMCL on both frozen maps to test for lower XY position RMSE on the intervention map. A's DA/SA evaluate cleaning and retention; B's localization RMSE evaluates the downstream effect. Assess these separately.

**Presentation wording:** “I first place each scan more accurately. For every map position, I then check whether returns repeatedly support nearby structure or whether measurement rays repeatedly pass through the position. I clear an occupied record only with enough crossing evidence relative to nearby hit support. Finally, I freeze the maps and use a separate acquisition to test whether localization error decreases while static structure is retained.”

Raw accumulates wheel-derived poses only. The current intervention includes both alignment and cleaning; alignment-only / filter-only ablations distinguish their contributions. The equations below explain each step.

**2. Predict the current pose using the wheel increment.**

$$
T_{k,0}=T_{k-1}(T_{k-1}^o)^{-1}T_k^o.
$$

$(T_{k-1}^o)^{-1}T_k^o$ is the wheel-derived motion between frames. Compose it with the previously corrected pose $T_{k-1}$ to obtain the current initial estimate $T_{k,0}$. Initialize the first frame using the known start and wheel pose; the algorithm does not read pose truth.

**Spoken explanation:** wheel odometry supplies the short motion increment, and prediction continues from the previous corrected pose.

**3. Downweight poorer correspondences.** At each iteration set $\mathbf p=T_k\mathbf z$, where $\mathbf z$ is a 2D scan point; $\mathbf q$ is its nearest point in the previous reference:

$$
w_{\mathbf p}=\min\!\left(1,\frac{0.05}{\max(\|\mathbf p-\mathbf q\|_2,10^{-9})}\right).
$$

Distances up to 5 cm receive weight 1; larger distances receive progressively smaller weights. $10^{-9}$ prevents division by zero. The weight describes correspondence reliability, not a probability of motion, and does not identify every moving object.

**4. Core equation I: robust scan alignment.**

$$
\boxed{\boldsymbol{\Delta T=\arg\min_{U\in\mathrm{SE}(2)}\sum_{(\mathbf p,\mathbf q)\in\mathcal C_k}w_{\mathbf p}\|U\mathbf p-\mathbf q\|_2^2}}
$$

$$
T_k\leftarrow\Delta T T_k.
$$

$U\in\mathrm{SE}(2)$ permits only 2D rotation and translation; $\mathcal C_k$ is the current correspondence set. Minimize the sum of weighted squared transformed distances, update the pose by the rigid increment $\Delta T$, and recompute correspondences each iteration, up to 12 iterations.

The reference $\mathcal R_{k-1}$ contains only retained prior-map positions with neighborhood support from at least three time bins. Correspondences must be within 0.30 m; retain the closest 70% with at least 30 pairs. Fall back to wheel prediction with fewer than 80 reference points, fewer than 30 pairs, or a total correction exceeding 0.15 m / 0.05 rad relative to prediction. These are implementation parameters, not novelty claims.

**Spoken explanation:** use repeatedly supported prior structure to correct the current pose, while correspondence selection and weighting reduce unreliable matches. This is local sequential correction, without global pose-graph optimization.

**5. Direct-hit evidence and candidate map.** Accumulate under corrected poses:

$$
h(c)=\sum_b\mathbf1[\text{hit at }c\text{ in bin }b],\qquad\widetilde M=\{\mathbf x_c:h(c)>0\}.
$$

$h(c)$ counts bins that directly hit cell $c$; repeated high-rate returns within a bin count once. $\widetilde M$ contains positions hit at least once. It uses corrected poses and differs from the wheel-pose baseline $M_0$.

**6. Neighborhood hit support.**

$$
s(c)=\sum_b\mathbf1[\exists c':\|\mathbf x_{c'}-\mathbf x_c\|_2\le0.10,\ \text{hit at }c'\text{ in bin }b].
$$

$s(c)$ counts bins with a hit within 10 cm of $c$. Returns from the same wall can still contribute support when small measurement or pose errors place them in adjacent cells. Neighborhood evidence changes decisions; it does not invent occupied points at unobserved positions.

**Spoken explanation:** check whether nearby structure continues to be observed while allowing small shifts between neighboring cells.

**7. Free-crossing evidence.**

$$
f(c)=\sum_b\mathbf1[\text{free ray through }c\text{ in bin }b].
$$

$f(c)$ counts bins with a valid measurement ray crossing $c$. Rays stop 15 cm before the return to allow endpoint uncertainty. Unobserved or occluded positions cannot simply be marked free. A bin can contribute to both $s,f$: these are evidence counts, not mutually exclusive probabilities. Different bins are not necessarily statistically independent either.

**8. Core equation II: trace-cleaning rule.**

$$
\boxed{\boldsymbol{M_1=\{\mathbf x_c\in\widetilde M:f(c)<3\ \lor\ f(c)<1.5s(c)\}}}
$$

Equivalently, delete only when $f(c)\ge3$ and $f(c)\ge1.5s(c)$: at least three distinct bins supply free-space counterevidence, reaching 1.5 times the neighborhood hit support. A corner seen only once and never revisited is not deleted merely for being rare. The rule does not guarantee removal of every moving object.

**Spoken explanation: deletion requires sufficient counterevidence; rare observations alone do not justify deletion.** The retained map and temporal support then inform the next alignment step, forming sequential feedback.

**9. Nearest distance used for scoring.**

$$
d(\mathbf q,M)=\min_{\mathbf x\in M}\|\mathbf q-\mathbf x\|_2.
$$

Find the map point nearest reference position $\mathbf q$. A smaller distance means the reference position is closer to the map. This definition serves evaluation, not the algorithm's motion decision.

**10. Static coverage SA and trace removal DA.** $S$ is a nonempty set of observed static reference positions from A. $D$ contains historical dynamic positions later verified free by rays, excluding overlap with static support or current obstacles. Both controls share $S,D$, deduplicated in 10 cm cells, with matching tolerance $r=0.15\,\mathrm m$:

$$
\mathrm{SA}(M)=\frac{\sum_{\mathbf q\in S}\mathbf1[d(\mathbf q,M)\le r]}{|S|},\qquad\mathrm{DA}(M)=\frac{\sum_{\mathbf q\in D}\mathbf1[d(\mathbf q,M)>r]}{|D|}.
$$

SA is the fraction of static reference positions still covered by the map; DA is the fraction of historical trace positions no longer covered. Formulas use 0–1; tables show percentages. DA is undefined for empty $D$. These are 2D position-coverage scores, not exact source-point retention or geometric accuracy. Truth and object labels construct evaluation references only and do not enter the algorithm.

**11. Cleaning-improvement condition and H1 prediction.**

$$
\mathrm{DA}(M_1)>\mathrm{DA}(M_0)\quad\land\quad\mathrm{SA}(M_1)\ge\mathrm{SA}(M_0)-0.01.
$$

The study defines improved cleaning as removing more traces while losing at most one percentage point of static coverage relative to baseline. This concerns observed support; it establishes neither global completeness, geometric accuracy nor a solution to mirror artifacts.

H1 also requires independent-B localization improvement. The full prediction can be written together:

$$
\mathrm{DA}(M_1)>\mathrm{DA}(M_0),\qquad\mathrm{SA}(M_1)\ge\mathrm{SA}(M_0)-0.01,\qquad E_{{\rm loc},1}<E_{{\rm loc},0}.
$$

**Spoken explanation:** first check trace removal and static support, then check independent localization on the frozen maps. Old B is used for development ablation; parameters are fixed before final fresh B. The joint gain cannot be attributed entirely to dynamic removal.
<!-- /HYPOTHESIS_PART:h1 -->

<!-- HYPOTHESIS_PART:h2 -->
**H2: bring point samples to a common reference time, then test map geometry and localization separately.**

**12. Core equation III: motion-distortion compensation.** $\mathbf z_i=(x_i,y_i,1)^{\mathsf T}$ is a local homogeneous point acquired at $t_i$. Wheel-odometry interpolation plus sensor extrinsics provides $\hat T(t)\in\mathrm{SE}(2)$ from that sensor frame to the fixed map frame. $t_e$ is scan end:

$$
\boxed{\boldsymbol{\bar{\mathbf z}_i=\hat T(t_e)^{-1}\hat T(t_i)\mathbf z_i}}
$$

Read right to left: $\hat T(t_i)$ moves the point to the fixed frame, then $\hat T(t_e)^{-1}$ moves it into the scan-end sensor frame. $M_0$ treats mixed-time points as acquired at $t_e$; $M_1$ compensates first. Integrate both with $\hat T(t_e)$ and hold all other steps fixed. H2 does not additionally enable H1 filtering.

**Spoken explanation:** use estimated robot motion to express points measured at different times in one reference frame. This compensates robot motion, not object motion, and depends on odometry quality.

**13. Map geometry error.** Construct static references $S$ afresh from this experiment's A and reuse nearest distance $d$:

$$
E_{\rm map}(M)=\sqrt{\frac1{|M|}\sum_{\mathbf x\in M}d(\mathbf x,S)^2}.
$$

Find each map point's nearest static reference, square the distance, average and take the square root. This is a one-way map-to-observed-static-support distance and does not alone measure completeness. An empty map is a mapping failure.

**14. Joint H2 test condition.**

$$
E_{\rm map}(M_1)<E_{\rm map}(M_0)\quad\land\quad E_{{\rm loc},1}<E_{{\rm loc},0}.
$$

After a lower geometry score, independently test for lower localization error. If only the first inequality holds, only geometry-score improvement is supported. H2 remains a single exploratory trial; consistent benefit requires repeat validation.
<!-- /HYPOTHESIS_PART:h2 -->

<!-- HYPOTHESIS_PART:comparison -->
**Innovation and conceptual comparison with SRRG.** Here SRRG refers to Lázaro et al., *Efficient Long-term Mapping in Dynamic Environments* (IROS 2018), and its 2D mapping code. It already includes point/normal registration, free-space fusion, a pose graph and long-term multi-session map maintenance. Alignment plus cleaning, or using free space to remove dynamics, is therefore not itself a first-of-its-kind contribution over SRRG. [Paper, Section III](https://iris.uniroma1.it/handle/11573/1340118).

| Aspect | Main idea in the SRRG paper | Current approach |
| --- | --- | --- |
| Map representation | 2D local point clouds with normals and a pose graph | Grid counts of hits, neighborhood support and free crossings |
| Registration | Point/normal correspondences with odometry initialization / prior | Robust point-to-point alignment to previously supported positions |
| Dynamic handling | Project to a common viewpoint, compare ranges, then merge, add or replace points | Accumulate free-space counterevidence across time bins; delete only when conditions hold |
| Small misalignments | Geometric correspondence and point-cloud merging | Neighborhood hits allow returns to fall into adjacent cells |
| System scope | Full SLAM, global graph optimization and long-term maintenance | Current local sequential intervention without global pose-graph or long-term multi-session mechanisms |
| Evaluation focus here | Practice the authors' map-maintenance pipeline | Relate cleaning / retention to independent localization on frozen maps |

**Candidate contribution: explicit neighborhood temporal evidence jointly selects registration references and decides trace deletion, with independent localization testing the map's downstream value.** The concrete difference is the organization of time bins, neighborhood support and deletion counterevidence. Parameter choices, local implementation and standard robust registration do not establish novelty. Independent B is an evaluation design; the algorithm does not directly optimize AMCL error. H2 uses standard relative-pose compensation and is not claimed as a separate first-of-its-kind contribution over SRRG.

Conservative evidence could reduce deletion caused by isolated anomalous observations while delaying adaptation to real changes; both need testing. The open research claim is whether this evidence design better balances static-support retention and trace removal under pose perturbations, sparse observations and dynamic occlusion. **These are implemented design differences, not established literature novelty. Metric effectiveness is not compared with SRRG here, and no performance superiority is claimed.**

**Presentation wording:** we study how dynamic mapping affects later localization. Compared with SRRG's projective fusion and complete graph maintenance, we explicitly accumulate neighborhood support and free-space evidence across time: repeatedly supported structure assists alignment, and sufficient free-space counterevidence removes historical traces. Current validation asks whether this evidence design preserves useful localization structure; comparative performance against SRRG has not been established.
<!-- /HYPOTHESIS_PART:comparison -->
