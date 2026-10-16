"""Shared mathematical definitions for the homepage and presentation notebook."""

import re


def raw_baselines(zh):
    if zh:
        return """**Raw的含义。** Raw是本库对“未做地图动态清理的累积基线”的标签，不是一个独立SLAM或定位算法，也不表示完全未经预处理的数据。

| 使用位置 | Raw如何生成 | 后续定位 |
| --- | --- | --- |
| 自写H1 | 用已知起点、轮速里程计和传感器外参，把有效二维回波变到同一坐标系；5 cm栅格至少命中一次就保留，只累计、不回撤，不用H1时序过滤。 | 冻结后用AMCL |
| Practice：SRRG二维对照 | 用SRRG每帧当时估计的传感器位姿直接累计回波；历史累计点不按最终图优化结果重新投影。SRRG输出另含地图维护与图优化。 | 冻结后用AMCL |
| Practice：Raw／DUFOMap／BeautyMap三维对照 | 用受控建图A提供的传感器位姿变换并拼接三维扫描，不调用DUFOMap或BeautyMap清理。该A使用提供的仿真位姿。 | 冻结后用GICP；B不输入真值 |

因此，不同实验的Raw不是同一张图，位姿来源也不相同；只能在各自匹配的对照内比较。SRRG这一组是包含位姿优化与地图维护的端到端对照，不是只改变删除规则的消融。当前H1干预还包含自写位姿对齐，Raw不含该对齐；仅清理／仅对齐消融区分两者贡献。H2基线另称Off，只关闭逐点运动补偿；FAST-LIO实践的Off仍保留LiDAR–IMU估计。
"""
    return """**Meaning of Raw.** Raw labels this repository's accumulated baseline without dynamic-map cleaning. It is not a standalone SLAM/localization algorithm or completely unprocessed sensor data.

| Context | How Raw is built | Downstream localization |
| --- | --- | --- |
| Own H1 | Transform valid 2D returns using the known start, wheel odometry and sensor extrinsic; retain each 5 cm cell hit at least once, without retracting earlier occupied cells or applying H1 temporal filtering. | Frozen-map AMCL |
| Practice: SRRG 2D comparison | Accumulate returns using SRRG's online sensor-pose estimate at each frame; do not reproject accumulated historical points with the final optimized graph. SRRG output additionally includes map maintenance and graph optimization. | Frozen-map AMCL |
| Practice: Raw / DUFOMap / BeautyMap 3D comparison | Transform and concatenate 3D scans using provided sensor poses from controlled mapping A, without DUFOMap/BeautyMap cleaning. A uses supplied simulation poses. | Frozen-map GICP; no truth input in B |

These Raw maps and pose sources differ between experiments; compare within the matched experiment. The SRRG comparison includes pose optimization and map maintenance, not just a deletion-rule ablation. Current H1 also adds own pose alignment, which Raw does not use; filter-only / alignment-only ablations distinguish their contributions. H2 calls its baseline Off: only point-time compensation is disabled. FAST-LIO Practice Off still retains LiDAR–IMU estimation.
"""


def math_sections(zh):
    def s(cn, en):
        return cn if zh else en

    common = s(
        """**实验约定。** A用于建图，B为另一次独立采集。每项实验中，$M_0$是基线图，$M_1$是干预图；两图由同一份A生成，再冻结，用同一份B、相同AMCL参数与初始化配置评价定位。

$M$在下式中表示地图占据格中心组成的非空点集。点集评分在同一坐标系、膨胀前进行；AMCL使用各组对应的完整栅格图，生成与膨胀规则一致。坐标以米计，展示表将误差换算成cm。空图记为建图失败。

**定位是否改善。** $\\hat{\\mathbf p}_{m,k}$是在地图$M_m$中估计的机器人二维位置，$\\mathbf p_k^*$是同一时刻的真值；$m\\in\\{0,1\\}$。$\\mathcal T$为两组都有有效输出的共同评分时间集合：
""",
        """**Experiment convention.** A builds the maps; B is acquired independently. In each experiment, $M_0$ is the baseline and $M_1$ the intervention. Build both from the same A, freeze them, and evaluate with the same B, AMCL parameters and initialization configuration.

$M$ denotes a nonempty point set of occupied-cell centers in the formulas below. Score pre-inflation points in the same frame; AMCL uses each arm's corresponding full grid, generated and inflated by the same rule. Coordinates are in metres; tables convert errors to cm. Empty maps are mapping failures.

**Localization improvement.** $\\hat{\\mathbf p}_{m,k}$ is the estimated 2D robot position on $M_m$, and $\\mathbf p_k^*$ is truth at that time; $m\\in\\{0,1\\}$. $\\mathcal T$ contains common scoring times with valid outputs from both controls:
""")
    common += r"""
$$
E_{{\rm loc},m}=
\sqrt{\frac{1}{|\mathcal T|}\sum_{k\in\mathcal T}
\|\hat{\mathbf p}_{m,k}-\mathbf p_k^*\|_2^2}.
$$
"""
    common += s(
        "直接比较$E_{{\\rm loc},1}<E_{{\\rm loc},0}$，不再另设差值符号。当前使用预热5秒后的10 Hz时间点，输出滞后不超过0.15秒；不为空的共同时间集才评分。H1多轮时，$k$同时索引轮次与时刻，合并全部共同有效样本。真值只用于事后评分，B评的是定位，尚未测完整导航到达效果。\n",
        "Compare $E_{{\\rm loc},1}<E_{{\\rm loc},0}$ directly, without another difference symbol. Current scoring uses 10 Hz times after 5 s warmup and outputs no older than 0.15 s; an empty common set is not scored. Across H1 trials, $k$ indexes both trial and time, pooling all common valid samples. Truth is used only for post-run evaluation. B tests localization; complete navigation outcomes were not measured.\n")

    h1 = s(
        """**H1：先定义“动态残影清理改善”，再检验规则。**

$S$是A中已观测静态参考位置组成的非空集合，$D$是A中后来被射线验证为空、且不与静态支持或当前障碍物重叠的历史动态位置集合。两组共用相同$S,D$；本轮按10 cm格去重，位姿真值与物体标签只用于构造评分参照，不输入清图算法。

$d(\\mathbf q,M)$是参考位置到最近地图点的距离，匹配容差固定为$r=0.15\\,\\mathrm m$：
""",
        """**H1: define improved dynamic-trace cleaning before testing the rule.**

$S$ is a nonempty set of observed static reference positions from A. $D$ contains historical dynamic positions later verified free by measured rays, excluding overlap with static support or current obstacles. Both controls share $S,D$; current scoring deduplicates in 10 cm cells. Pose truth and object labels construct evaluation references only and never enter the cleaner.

$d(\\mathbf q,M)$ is the distance to the nearest map point, with fixed tolerance $r=0.15\\,\\mathrm m$:
""")
    h1 += r"""
$$
d(\mathbf q,M)=\min_{\mathbf x\in M}\|\mathbf q-\mathbf x\|_2.
$$

$$
\mathrm{SA}(M)=\frac{\sum_{\mathbf q\in S}\mathbf1[d(\mathbf q,M)\le r]}{|S|},
\qquad
\mathrm{DA}(M)=\frac{\sum_{\mathbf q\in D}\mathbf1[d(\mathbf q,M)>r]}{|D|}.
$$
"""
    h1 += s(
        """公式中的比例取0–1，表格换成百分数。$D$为空时不定义DA；静态对照只看SA。这是二维参考位置的覆盖／未覆盖比例，不是逐个原始点的保留追踪。

**本研究的相对定义：动态残影删除更多，且静态保留相对基线损失不超过1个百分点，才称“动态残影清理改善”。**
""",
        """Ratios in formulas are 0–1; tables display percentages. DA is undefined for empty $D$; static controls use SA only. These are coverage / noncoverage rates of 2D reference positions, not exact source-point retention.

**Operational relative definition: more dynamic traces are removed, with at most one percentage point of static-retention loss relative to the baseline.**
""")
    h1 += r"""
$$
\mathrm{DA}(M_1)>\mathrm{DA}(M_0)
\quad\land\quad
\mathrm{SA}(M_1)\ge\mathrm{SA}(M_0)-0.01.
$$
"""
    h1 += s(
        """该定义只针对已观测支持上的动态残影；不据此宣称整张地图完整、几何准确或镜面问题已解决。

**修订为联合建图方法。** Raw仍用轮速位姿直接累积。干预先用前序时序支持点修正逐帧对齐，再清理动态残影；这包含位姿修正与清理，不是只改变删除规则。两项贡献由“只清理／只对齐”消融区分。

$T_k^o$是第$k$帧的轮速传感器位姿，$T_k$是修正位姿；均从传感器系到固定地图系。$\\mathcal R_{k-1}$来自前序保留地图中至少3个时间箱支持的点，算法不读取真值。轮速增量给出预测：
""",
        """This definition concerns dynamic traces on observed support; it does not establish global completeness, geometric accuracy or removal of mirror artifacts.

**Revised joint mapping method.** Raw still accumulates wheel-odometry poses. The intervention first aligns scans to preceding temporally supported points, then cleans dynamic traces. It changes both pose alignment and cleaning; filter-only / alignment-only ablations separate their contributions.

$T_k^o$ is the wheel-derived sensor pose and $T_k$ its correction, both sensor-to-map transforms. $\\mathcal R_{k-1}$ contains retained points supported by at least three earlier time bins. No truth enters the algorithm. Predict with the wheel increment:
""")
    h1 += r"""
$$
T_{k,0}=T_{k-1}(T_{k-1}^o)^{-1}T_k^o.
$$

"""
    h1 += s(
        "$\\mathbf z$为二维扫描点，$T\\mathbf z$指旋转和平移后的二维坐标。每次迭代令$\\mathbf p=T_k\\mathbf z$，在$\\mathcal R_{k-1}$找最近点$\\mathbf q$；从距离小于0.30 m的对应中保留最接近的70%（至少30对），组成$\\mathcal C_k$。按下式求二维刚体增量，最多12次：\n",
        "$\\mathbf z$ is a 2D scan point; $T\\mathbf z$ denotes its rotated and translated 2D coordinates. At each iteration set $\\mathbf p=T_k\\mathbf z$ and find its nearest $\\mathbf q$ in $\\mathcal R_{k-1}$. From correspondences within 0.30 m keep the closest 70% (at least 30 pairs) as $\\mathcal C_k$. Solve the weighted 2D rigid increment below, at most 12 times:\n")
    h1 += r"""
$$
w_{\mathbf p}=\min\!\left(1,\frac{0.05}{\max(\|\mathbf p-\mathbf q\|_2,10^{-9})}\right),
$$

$$
\Delta T=\arg\min_{U\in\mathrm{SE}(2)}\sum_{(\mathbf p,\mathbf q)\in\mathcal C_k}
w_{\mathbf p}\|U\mathbf p-\mathbf q\|_2^2,
\qquad T_k\leftarrow\Delta T T_k.
$$
"""
    h1 += s(
        "参照不足80点、对应不足30对或总修正超过0.15 m／0.05 rad时使用轮速预测。初帧使用已知起点与轮速位姿。然后在修正位姿下统计5 cm栅格：$h(c)$为该格命中时间箱数，$s(c)$为0.10 m近邻命中支持箱数，$f(c)$为空闲穿越箱数；每箱各最多一次。自由射线在回波前15 cm停止。\n",
        "Use the wheel prediction when reference support is below 80 points, correspondences below 30, or the total correction exceeds 0.15 m / 0.05 rad. Initialize from the known start and wheel pose. In the corrected 5 cm grid, $h(c)$ counts own hits, $s(c)$ counts hits within 0.10 m, and $f(c)$ counts free crossings, each once per 0.5 s bin. Free rays stop 15 cm before returns.\n")
    h1 += r"""
$$
h(c)=\sum_b\mathbf1[\text{hit at }c\text{ in bin }b],
\qquad \widetilde M=\{\mathbf x_c:h(c)>0\}.
$$

$$
s(c)=\sum_b\mathbf1[\exists c':\|\mathbf x_{c'}-\mathbf x_c\|_2\le0.10,
\ \text{hit at }c'\text{ in bin }b].
$$

$$
f(c)=\sum_b\mathbf1[\text{free ray through }c\text{ in bin }b].
$$

$$
M_1=\{\mathbf x_c\in \widetilde M:f(c)<3\ \lor\ f(c)<1.5s(c)\}.
$$
"""
    h1 += s("即：至少3个空闲时间箱，且空闲证据至少为近邻命中支持的1.5倍，才删除。同一箱可同时计入$s,f$，它们是证据计数，不是互斥概率。少见本身不等于动态；邻域支持允许同一墙面的回波落在相邻格中，不向未观测格补点。算法不使用语义标签或真值；两组距离筛选、栅格化、自由区与膨胀规则相同。\n\n",
            "Delete only with at least three free bins and free evidence at least 1.5 times neighborhood hit support. A bin can contribute to both $s,f$; these are evidence counts, not mutually exclusive probabilities. Rare observations alone do not imply motion. Neighborhood support accommodates hits landing in adjacent cells without adding unobserved occupied cells. No semantics or truth enters the algorithm; range filtering, gridding, free-space generation and inflation are shared.\n\n")
    h1 += s(
        "**要检验的H1：**联合方法相对轮速Raw满足清理改善条件，并降低另采B的定位误差。所有参数在最终新B采集前固定；旧B用于开发消融。旧逐格规则和只清理版本的负结果全部保留，不能将联合方法的收益全归因于动态去除。\n",
        "**H1 to test:** the joint method meets the cleaning criterion relative to wheel-pose Raw and reduces error on fresh B. All parameters are fixed before final B acquisition; old B is for development ablation. Preserve negative results from per-cell filtering and filter-only revisions. Do not attribute the joint gain entirely to dynamic removal.\n")

    h2 = s(
        """**H2：统一采样时刻，再分别检验几何与定位。**

$\\mathbf z_i=(x_i,y_i,1)^{\\mathsf T}$是在$t_i$采集的传感器局部齐次点；$\\hat T(t)\\in\\mathrm{SE}(2)$为轮式里程计加传感器外参得到的估计变换，从$t$时刻传感器坐标系变到固定地图坐标系。$t_e$为扫描末时刻：
""",
        """**H2: align point timestamps, then test geometry and localization separately.**

$\\mathbf z_i=(x_i,y_i,1)^{\\mathsf T}$ is a sensor-local homogeneous point acquired at $t_i$. Wheel odometry plus the sensor extrinsic provides $\\hat T(t)\\in\\mathrm{SE}(2)$, mapping the instantaneous sensor frame to a fixed map frame. $t_e$ is the scan-end time:
""")
    h2 += r"""
$$
\bar{\mathbf z}_i=\hat T(t_e)^{-1}\hat T(t_i)\mathbf z_i.
$$
"""
    h2 += s(
        """先变到固定坐标系，再变回扫描末时刻坐标系。$M_0$不补偿，直接把混合时刻的点当作$t_e$采集；$M_1$先按上式补偿。两图融合时都用$\\hat T(t_e)$，其他步骤相同；H2不额外开启H1过滤。

从本项A重新构造静态参照$S$，沿用最近距离$d$，当前几何评分明确定义为：
""",
        """Transform first to the fixed frame, then to the scan-end sensor frame. $M_0$ treats mixed-time points as acquired at $t_e$; $M_1$ applies the compensation above. Both are integrated using $\\hat T(t_e)$ with all other steps fixed; H2 does not additionally enable H1 filtering.

Construct $S$ afresh from this experiment's A and use the same nearest-distance definition $d$. Current geometry scoring is:
""")
    h2 += r"""
$$
E_{\rm map}(M)=
\sqrt{\frac1{|M|}\sum_{\mathbf x\in M}d(\mathbf x,S)^2}.
$$
"""
    h2 += s(
        """这是“地图到已观测静态支持”的单向距离RMSE，不能单独评价地图完整性；空图判为建图失败，不算几何改善。

**要检验的H2：**
""",
        """This is a one-way map-to-observed-static-support distance RMSE; it does not alone measure completeness. An empty map is a mapping failure, not a geometric improvement.

**H2 to test:**
""")
    h2 += r"""
$$
E_{\rm map}(M_1)<E_{\rm map}(M_0)
\quad\land\quad
E_{{\rm loc},1}<E_{{\rm loc},0}.
$$
"""
    h2 += s("若只有前一项成立，只支持几何评分改善；不能推断定位改善。当前均为单轮探索，稳定收益仍需重复验证。\n",
            "If only the first inequality holds, only the geometry-score claim is supported. These are single exploratory trials; repeat trials are needed to establish consistent benefit.\n")
    return {"common": common.strip(), "h1": h1.strip(), "h2": h2.strip()}


def pseudocode():
    return """for test, scene in [(H1, static), (H1, dynamic), (H2, motion)]:
    A = acquire_scans_and_wheel_odometry(scene)
    if test == H1:
        M0 = integrate_A_with_wheel_poses(A)
        corrected_poses = align_scans_to_previous_supported_map(A)  # own implementation
        h, s, f = initialize_grid_evidence()
        for bin in A.project_with(corrected_poses).time_bins(seconds=0.5):
            add_hits_once_per_cell(h, bin)
            add_neighborhood_hit_support_once(s, bin, radius=0.10)
            add_truncated_free_ray_evidence_once(f, bin, stop_before_return=0.15)
        M1 = cell_centers_where((h > 0) & ((f < 3) | (f < 1.5 * s)))
    else:
        M0 = integrate_A(A, point_compensation=False)
        M1 = integrate_A(A, point_compensation=True)  # no H1 filtering
    freeze(M0, M1)
    B = acquire_independent_scans_and_wheel_odometry(scene)
    positions = {}
    for m, map in [(0, M0), (1, M1)]:
        positions[m] = same_AMCL(B.scans, B.odometry, grid_of(map), same_initial_config)
    # Truth enters only here; references are shared across controls
    S, D = scoring_references_from_A_truth(A)
    if test == H1:
        score_SA(M0, M1, S)
        if scene == dynamic: score_DA(M0, M1, D)
    if test == H2: score_map_RMSE(M0, M1, S)
    score_position_RMSE(positions, B_truth, common_valid_times)
"""


def github_math(text):
    fence = chr(96) * 3
    text = re.sub(r"\$\$(.*?)\$\$", lambda m: fence + "math\n" + m[1].strip() + "\n" + fence, text, flags=re.S)
    return re.sub(r"(?<!\$)\$([^$\n]+?)\$(?!\$)", lambda m: "$" + chr(96) + m[1] + chr(96) + "$", text)
