<!-- HYPOTHESIS_PART:common -->
A builds the maps; B is acquired independently. $M_0$ is the baseline and $M_1$ the intervention. Freeze both maps and share B scans, odometry, AMCL parameters and initialization; truth is used only for scoring.

| Symbol | Meaning |
| --- | --- |
| $T_k^o,T_k$ | Wheel-derived / corrected sensor pose at frame $k$, both sensor-to-map transforms |
| $c,\mathbf x_c,b$ | A 5 cm cell, its center, a 0.5 s time bin |
| $\mathbf1[\cdot],M$ | Indicator function, set of occupied-cell centers; coordinates in m |

Maps and static scoring references must be nonempty. Score point sets in the same frame before inflation and generate AMCL maps identically. Transforms use homogeneous coordinates; distances use XY.

**XY localization RMSE on frozen maps:**

$$
E_{{\rm loc},m}=\sqrt{\frac{1}{|\mathcal T|}\sum_{k\in\mathcal T}\|\hat{\mathbf p}_{m,k}-\mathbf p_k^*\|_2^2}.
$$

$\hat{\mathbf p}_{m,k},\mathbf p_k^*$ are estimated and true positions. $\mathcal T$ contains common valid times: 10 Hz after 5 s warmup, output age at most 0.15 s. Pool common samples across trials; this is not output success rate or navigation arrival rate.
<!-- /HYPOTHESIS_PART:common -->

<!-- HYPOTHESIS_PART:h1 -->
**H1: scan-pose correction and dynamic-trace cleaning.** Raw accumulates wheel poses only; the intervention adds the following alignment and filtering.

Wheel increments initialize the pose; let $\mathbf p=T_k\mathbf z$, where $\mathbf z$ is a scan point and $\mathbf q$ its nearest point in the prior reference:

$$
\begin{aligned}
T_{k,0}&=T_{k-1}(T_{k-1}^o)^{-1}T_k^o,\\
w_{\mathbf p}&=\min\!\left(1,\frac{0.05}{\max(\|\mathbf p-\mathbf q\|_2,10^{-9})}\right).
\end{aligned}
$$

**Robust alignment:** $\mathcal C_k$ contains selected correspondence pairs. References are retained prior-map positions with neighborhood support in at least three bins. Iteratively solve a 2D rigid increment and update the pose; fall back to wheel prediction for insufficient references or excessive correction.

$$
\begin{gathered}
\boxed{\boldsymbol{\Delta T=\arg\min_{U\in\mathrm{SE}(2)}\sum_{(\mathbf p,\mathbf q)\in\mathcal C_k}w_{\mathbf p}\|U\mathbf p-\mathbf q\|_2^2}}\\
T_k\leftarrow\Delta T T_k.
\end{gathered}
$$

Under corrected poses, count direct hits $h$, hits within 10 cm $s$, and free crossings $f$. Each evidence type counts at most once per bin; rays stop 15 cm before returns:

$$
\begin{aligned}
h(c)&=\sum_b\mathbf1[\text{hit at }c\text{ in bin }b],\quad\widetilde M=\{\mathbf x_c:h(c)>0\},\\
s(c)&=\sum_b\mathbf1[\exists c':\|\mathbf x_{c'}-\mathbf x_c\|_2\le0.10,\ \text{hit at }c'\text{ in bin }b],\\
f(c)&=\sum_b\mathbf1[\text{free ray through }c\text{ in bin }b].
\end{aligned}
$$

**Occupancy retention:** delete only when $f\ge3$ and $f\ge1.5s$; low hit count alone does not trigger deletion. The retained map and temporal support inform the next alignment.

$$
\boxed{\boldsymbol{M_1=\{\mathbf x_c\in\widetilde M:f(c)<3\ \lor\ f(c)<1.5s(c)\}}}
$$

Score against shared static references $S$ and historical dynamic references $D$ from A, deduplicated in 10 cm cells. $D$ must later be verified free by rays and exclude overlap with static support or current obstacles. Set $r=0.15\,\mathrm m$:

$$
\begin{aligned}
d(\mathbf q,M)&=\min_{\mathbf x\in M}\|\mathbf q-\mathbf x\|_2,\\
\mathrm{SA}(M)&=\frac{\sum_{\mathbf q\in S}\mathbf1[d(\mathbf q,M)\le r]}{|S|},\\
\mathrm{DA}(M)&=\frac{\sum_{\mathbf q\in D}\mathbf1[d(\mathbf q,M)>r]}{|D|}.
\end{aligned}
$$

SA measures static coverage; DA measures removal of trace-reference coverage. Neither is geometric accuracy. Formulas use 0–1, tables use percentages; DA is omitted for empty $D$. **H1 requires all three conditions:**

$$
\mathrm{DA}(M_1)>\mathrm{DA}(M_0),\qquad\mathrm{SA}(M_1)\ge\mathrm{SA}(M_0)-0.01,\qquad E_{{\rm loc},1}<E_{{\rm loc},0}.
$$

Here 0.01 is one percentage point; ablations separate alignment and cleaning contributions.
<!-- /HYPOTHESIS_PART:h1 -->

<!-- HYPOTHESIS_PART:h2 -->
**H2: point-time motion compensation.** $\mathbf z_i$ is a homogeneous point acquired at $t_i$; $\hat T(t)$ is the wheel-interpolated sensor-to-map transform and $t_e$ is scan end:

$$
\boxed{\boldsymbol{\bar{\mathbf z}_i=\hat T(t_e)^{-1}\hat T(t_i)\mathbf z_i}}
$$

$M_0$ omits compensation; $M_1$ expresses points at $t_e$ first. Both integrate with $\hat T(t_e)$ without H1 filtering. This compensates robot motion. Score one-way map error against static support $S$ from this A:

$$
E_{\rm map}(M)=\sqrt{\frac1{|M|}\sum_{\mathbf x\in M}d(\mathbf x,S)^2}.
$$

This score does not measure completeness. Maps and static references must be nonempty; an empty map is a mapping failure. **H2 requires lower map and independent localization error:**

$$
E_{\rm map}(M_1)<E_{\rm map}(M_0)\quad\land\quad E_{{\rm loc},1}<E_{{\rm loc},0}.
$$
<!-- /HYPOTHESIS_PART:h2 -->

<!-- HYPOTHESIS_PART:comparison -->
**Design difference: neighborhood temporal evidence jointly selects registration references and decides trace deletion.** Compare concepts with SRRG only; literature novelty and metric superiority are unproven. [SRRG paper, Section III](https://iris.uniroma1.it/handle/11573/1340118).

| Aspect | SRRG | Current H1 |
| --- | --- | --- |
| Registration | Point/normal correspondences with odometry | Robust point-to-point alignment to temporally supported positions |
| Map maintenance | Common-view projection, range comparison and point-cloud fusion | Bin-wise neighborhood hits and free counterevidence; delete only at threshold |
| System scope | Pose-graph optimization and long-term multi-session maintenance | Local sequential processing; independent B tests downstream localization |

H2 uses standard relative-pose compensation and is not claimed as a separate innovation.
<!-- /HYPOTHESIS_PART:comparison -->
