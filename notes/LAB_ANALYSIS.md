# Lab requirements, current evidence and personal analysis outline

English | [中文](LAB_ANALYSIS.zh-CN.md) | [Index](README.md)

Numbers below retain the earlier subset and exploratory records. See [new author-workflow evidence](AUTHOR_RESULTS_ANALYSIS.md) for four public releases; keep the experiments distinct.

The supplied email asks for an argued open research question and a testable hypothesis, based on relevant work from roughly the past 3–5 years. Reproduction, numbers and figures should substantiate the reasoning. Deliver a carefully organized GitHub repository link by October 9 inclusive. The email does not specify a timezone or an exact final hour.

## Connecting topics 1 and 2

Topic 1 covers robust localization/SLAM in dynamic environments; topic 2 covers semantic mapping, visual localization and navigation. This project studies a narrower interface: **poses establish spatial correspondences, which affect dynamic-point decisions, object fusion and language-query coordinates.**

DUFOMap, BeautyMap, ConceptGraphs and HOV-SG are 2024 papers; the ConceptGraphs preprint began in 2023. The first pair addresses dynamic map cleaning, the second open-vocabulary 3D representations. They provide a tractable entry into the selected topics, rather than full coverage. The executed cores use supplied poses; trajectory estimation, visual-localization benchmarks and robot navigation were not evaluated.

## Requirements and evidence

| Requirement | Current material | Your remaining judgment |
| --- | --- | --- |
| Select recent, relevant work | [Cards](../docs/papers/README.md), [literature](../docs/LITERATURE.md), [upstream comparison](UPSTREAM_COMPARISON.md) | Explain why these methods isolate the interface; avoid ranking unlike tasks |
| Choose sources and describe the problem carefully | Original sections, pinned author versions, configurations, patches and safeguards | Read the key sections yourself; check whether the proposed gap is already addressed |
| Argue an open problem | [Study](../docs/STUDY.md), [paired results](../docs/PAIRED_RESULTS.md) | Separate observations, compatible explanations and counterexamples |
| Refine a hypothesis | Candidate H1, B0–B5 comparisons, budgets and rejection rules | State exactly what changes and what outcome makes the extra mechanism unnecessary |
| Support with reproducible numbers and figures | Two full LiDAR teasers, two semantic subsets, 97 main/control cells | Manually verify inputs, outputs, denominators and adaptations; execution is not complete paper agreement |
| Communicate and discuss face to face | Focused main page, separate analysis, attribution/disclosure | Explain the strongest counterexample and limitations in your own words |

The email assigns no numerical weights and does not require training a new model, completing every paper experiment or obtaining positive results. Practical execution supports the argument; it does not replace it.

## What each reproduction contributes

| Method | Achieved evidence | Missing scope or challenged claim |
| --- | --- | --- |
| DUFOMap | 141 scans; map-neighbor SA 97.9798%, DA 98.7029%; PCL/SciPy agree pointwise. At 30 cm, direct SA is 76.5854% shuffled versus 88.5977% drift | Not every paper difference is within 0.01 percentage point; no trajectory evaluation. Existing pose tolerance and the drift counterexample rule out simplistic claims |
| BeautyMap | Same teaser; SA 96.9529%, DA 98.3382%. At 30 cm, map-neighbor SA is 93.2688% shuffled versus 95.8456% drift | Paper differences remain unexplained; existing occlusion recovery must be acknowledged |
| ConceptGraphs | 40 observations, 39 objects. In the common eight-observation test, coverage drops from 0.9256 to 0.3984 under drift | Object count is not accuracy; zero-error restricted query hits are already 2/3. No full semantic benchmark, LLM relation graph or navigation |
| HOV-SG | Eight observations, 50 segments, 166,777 points. Drift coverage remains 0.9136 while restricted hits fall from 2/3 to 1/3 | The 40-observation attempt exited 137 for an unconfirmed reason. No complete hierarchy, navigation or online recovery |

Perturbation values are means across three seeds. Semantic comparisons use eight common observations. SA/DA, partial-surface coverage and restricted top-1 are different tasks and cannot form a common leaderboard. See [the report](../docs/PAIRED_RESULTS.md) for definitions and denominators.

## Build the argument

1. **Observation:** correspondence affects decisions differently across tasks. LiDAR retains static points better under drift than shuffled errors; HOV-SG can retain annotated geometry while retrieval degrades.
2. **Boundary:** sorting/shuffling changes both local consistency and assignment to viewpoints. Four partial surfaces have AI-assisted annotations without independent human review; reference frames enter mapping. Three seeds are not three scenes.
3. **Rejected strong statements:** correlated errors are always worse; shared uncertainty is already proven to be the common dominant bottleneck; retained geometry guarantees navigation.
4. **Open question:** when a later pose correction changes historical correspondences, how can object identity and query coordinates recover while bounding exposure of stale results? Current offline experiments do not test recovery.
5. **Candidate intervention:** retain bounded observation provenance, shared pose versions and tentative associations; replay affected contributors after correction. Queries return coordinates, pose version, validity and timestamp. Sixteen observations/512 MiB is a proposed budget, not a measured guarantee.
6. **Cheap falsification first:** compare native core, simple threshold/visibility protection, corrected geometry with frozen association, and full-replay oracle. If geometry correction matches full replay, the extra association-recovery claim loses motivation.

DUFOMap `d_p=2` and ConceptGraphs threshold `1.0` are already strong simple controls. Match change recall, query coverage and latency. Keeping stale objects to avoid deletion is not a free improvement. [B0–B5 protocol](../docs/REAL_WORLD.md).

Khronos already includes joint optimization, history and map reconciliation. Memory/rollback alone is not novelty. Even the narrower bounded pose-correction/open-vocabulary validity interface remains a candidate contribution pending prior-work checks. [Original paper](https://arxiv.org/html/2402.13817v2), [literature comparison](../docs/LITERATURE.md).

## Match claims to measurements

| Claim | Measurement | Pitfall |
| --- | --- | --- |
| Preserve static points while removing dynamic ones | SA and DA together, with explicit direct-label/map-neighbor definitions | Higher SA may simply mean deleting less; changing scoring is not an algorithm gain |
| Preserve a target surface | Independent partial-surface coverage within 10 cm; recovery requires ≥50% visible precision and ≥20% coverage | Partial surfaces are not complete instance ground truth; fragment counts are proxies |
| Retrieve the requested target | Restricted top-1 and specified surface distance, separately from geometry | Cosine scores are not calibrated correctness probabilities; unannotated answers may be valid |
| Recover historical associations | B2–B5 identity, coverage and coordinate gaps | Full replay has real time/memory cost |
| Stop exposing stale coordinates | Event/correction-to-invalidation/update times, including abstention coverage loss | A final offline map cannot measure stale exposure |
| Justify H1 cost | Risk curves at matched recall/coverage/latency, peak memory and replay time | Budgets are not measurements; selecting one favorable operating point is insufficient |

## Your own analysis space

These prompts are unfilled, not verified conclusions. Keep each paragraph to one judgment and separate fact, interpretation and boundary.

**Why these four papers, about 100 words:**

> Fill in: the interface I care about is… The two method families expose… This lets me test… Current coverage excludes…

**The counterexample that changed my view, about 150 words:**

> Fill in: I initially expected… Record/figure… instead shows… I therefore abandon… Remaining explanations include…

**Open question, one or two sentences:**

> Fill in: under… existing… does not guarantee… The measurable objective is…

**Hypothesis and rejection rule, about 150 words:**

> Fill in: change only… hold… fixed; compare with… under budget… If… occurs, reject…

| Date / run or session ID | Observation | Effect on the argument | Unresolved explanation |
| --- | --- | --- | --- |
| To fill | To fill | To fill | To fill |

Do not report planned recording, pending adapters or a candidate implementation as completed. Hardware connectivity and data adaptation remain unverified. A workflow demonstration can be useful without becoming a hypothesis result.
