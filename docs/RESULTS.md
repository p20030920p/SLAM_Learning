# Reproduction results and exploratory diagnostics

English | [中文](RESULTS.zh-CN.md)

Measured on 7 October 2026. Portable records bind commands, versions, source hashes, data checksums and output hashes. Windows author/controlled experiments use Python 3.10.19. Both author methods and all six real-data sensitivity cells also **executed successfully on GitHub Actions Ubuntu 22.04**, with a fresh download and environment. [Linux run](https://github.com/p20030920p/SLAM_Learning/actions/runs/37622082701), [execution metadata](../results/ci/linux-run.json). Docker was not locally built. On 8 October, local WSL2 author, PCL and semantic-subset runs completed; see sections 5–6 and [WSL](WSL.md).

Existing synthetic trials informed the candidate hypothesis. They are exploratory, not independent confirmation after hypothesis selection.

## 1. Author-method execution and paper disagreement

Dataset: [DynamicMap benchmark public KITTI-00 teaser](https://zenodo.org/records/10886629), **141 frames**, **17,362,230 labeled points**: 17,266,247 static and 95,983 dynamic. It is a selected fragment with supplied poses, not the complete KITTI odometry sequence or a SLAM trajectory-estimation experiment.

| Method / metric | Measured % | Paper % | Difference, percentage points |
| --- | --- | --- | --- |
| DUFOMap SA | 97.979798 | 97.96 | +0.019798 |
| DUFOMap DA | 98.702895 | 98.72 | −0.017105 |
| DUFOMap AA | 98.340682 | 98.34 | +0.000682 |
| BeautyMap SA | 96.952945 | 96.76 | +0.192945 |
| BeautyMap DA | 98.338247 | 98.38 | −0.041753 |
| BeautyMap HA | 97.640683 | 97.56 | +0.080683 |

Paper targets are [DUFOMap Table I](https://arxiv.org/html/2403.01449v1) and [BeautyMap Table I](https://arxiv.org/html/2405.07283v1). The declared tolerance is **0.01 percentage points**, fixed before comparison. Both methods executed; neither matches every target. The tolerance was not expanded to turn this table green.

Evidence: [DUFOMap record](../results/reference/dufomap/record.json), [raw metrics](../results/reference/dufomap/metrics.json), [log](../results/reference/dufomap/run.log); [BeautyMap record](../results/reference/beautymap/record.json), [raw metrics](../results/reference/beautymap/metrics.json), [compatibility changes](../results/reference/beautymap/compatibility.patch). The [first BeautyMap failure](../results/reference/beautymap-windows-failure/record.json) records a Windows integer overflow, fixed with explicit 64-bit masks.

These scores use an independent SciPy nearest-neighbor evaluator. A kept map point within 5 cm preserves the GT point, regardless of which input point generated it. Close retained geometry can therefore mask individual dynamic labels. Original PCL agreement was established on 8 October for both stored maps (section 5); newer author versions can still differ from paper-era code. No single cause of the table mismatch is established.

Linux repeats produced **identical author-method confusion counts and scores** for this snapshot: [DUFOMap Linux](../results/reference/dufomap-linux/record.json), [BeautyMap Linux](../results/reference/beautymap-linux/record.json). That CI run used `9f3a9ef`: scan intensity was available but unused by the author geometry code. The subsequent final Windows run physically removes scan annotations and gives unchanged results. This distinction is preserved rather than retroactively rewriting Linux evidence. Linux direct-label sensitivity has its own [record](../results/reference/pose-stress-linux/record.json) and [cells](../results/reference/pose-stress-linux/sensitivity.csv).

## 2. Real-data pose sensitivity

The DUFOMap binding's `segment` path assigns labels to original point identities. Before scoring, every GT coordinate was verified to match the concatenated scans. A smooth translation $A\sin(2\pi i/(N-1))$ is applied to both world-space scan coordinates and their sensor origin. Orientation is unchanged. This represents a temporally correlated pose error while preserving each scan's sensor-relative geometry.

| Pose margin `d_p` | Translation amplitude m | Direct-label SA % | Direct-label DA % |
| --- | --- | --- | --- |
| 1 | 0.0 | 92.6340 | 98.9675 |
| 1 | 0.1 | 92.6811 | 99.0352 |
| 1 | 0.3 | 91.4288 | 99.0540 |
| 2 | 0.0 | 99.7816 | 96.3921 |
| 2 | 0.1 | 99.7923 | 96.4139 |
| 2 | 0.3 | 99.3983 | 96.4254 |

![Real-data sensitivity](../results/reference/pose-stress/sensitivity.png)

Larger pose tolerance retains more static points and detects fewer dynamic ones. A 0.3 m perturbation reduces static retention here; 0.1 m does not. This is **counterevidence against a claim that any pose noise necessarily degrades performance**. One deterministic perturbation and one short sequence cannot establish typical deployment failure.

This table uses another binding API and direct identities, so it must not be merged with the nearest-neighbor table. The same-instance control in section 5 attributes most of this SA gap to correspondence scoring; the smaller native-export remainder is still not independently isolated. Small variations in integer counts occurred between local executions, consistent with a nondeterministic native path; no bitwise determinism is claimed. [Record](../results/reference/pose-stress/record.json), [six cells](../results/reference/pose-stress/sensitivity.csv), [846 frame-level rows](../results/reference/pose-stress/per_frame.csv).

## 3. Exploratory: visibility and common-mode ambiguity

Thirty objects, known instance identities, supplied true visibility, sensor noise σ=0.02 m, coherent mover displacement 1 m. Four pose biases × four mover fractions × two occlusion fractions × four methods × thirty held-out seeds = **3,840 paired trials**. A 99th-percentile noise threshold is selected using separate validation seeds. Confidence intervals bootstrap seed outcomes for each method/cell; methods share the same underlying randomized trials. These are intervals on means, not paired difference intervals.

At 0.3 m bias, 20% movers and 50% occlusion:

| Method | Static false-change rate % | Returned-target coordinate error m | Query coverage % |
| --- | --- | --- | --- |
| Raw residual | 100.00 | 0.3004 | 49.22 |
| Visibility only | 50.97 | 0.3004 | 49.22 |
| Common-mode only | 49.86 | 0.0053 | 49.22 |
| Combined | 0.83 | 0.0053 | 49.22 |

Combined false-change 95% interval: **0.28–1.67%**. All-mover recall is only **42.22%** at this cell; unseen changes are unknown. The roughly 49% coverage is necessary context for the low coordinate error. This is a synthetic object-coordinate query, not SLAM ATE or executed navigation.

![Mechanism and failure boundary](../results/reference/mechanism/mechanism.png)

With 80% coherent movers, 0.3 m bias and no occlusion, the combined method's static false-change rate is **100%**, pose error **0.9917 m**, and query error **0.9985 m**. The moving majority is incorrectly chosen as the common pose offset. This failure is expected from the stable-anchor assumption, and remains in the result set. [Record](../results/reference/mechanism/record.json), [all raw trials](../results/reference/mechanism/trials.csv), [cell summaries and intervals](../results/reference/mechanism/summary.json).

## 4. Exploratory: correlated observations and confidence

A 1D Gaussian model uses 1,000 paired seeds, change prior 0.1, pose σ=0.15 m, sensor σ=0.02 m and changed-object displacement σ=0.5 m. The same pose bias persists through 1, 5, 20 or 100 readings; deletion requires posterior change probability >0.9. Three inference assumptions give **12,000 trials**. Class prior and noise scales are known exactly; this is not an implementation of SuperMap or PerSeM.

| Model | Readings | Static false deletion % | Changed-object recall % | Brier score ↓ |
| --- | --- | --- | --- | --- |
| Independent pose noise | 1 | 0.1134 | 33.05 | 0.0582 |
| Independent pose noise | 100 | 68.2540 | 94.92 | 0.6278 |
| Shared pose latent | 1 | 0.1134 | 33.05 | 0.0582 |
| Shared pose latent | 100 | 0.1134 | 35.59 | 0.0574 |

![Correlated evidence calibration](../results/reference/evidence-stress/calibration.png)

The experiment demonstrates the variance-floor mechanism under a matched generative model. It also shows the tradeoff: shared-latent inference has substantially lower changed-object recall. It does not prove superiority at matched recall, nor calibration with realistically estimated pose uncertainty. Brier measures probabilistic prediction quality; that score alone is not a complete calibration test. [Record](../results/reference/evidence-stress/record.json), [trials](../results/reference/evidence-stress/trials.csv), [all cells](../results/reference/evidence-stress/summary.json).

## 5. Local WSL and evaluator controls — 8 October

Both CPU author runs completed again under WSL2 Ubuntu 22.04/Python 3.10.12, with unchanged confusion counts. All BeautyMap map/scan intensity annotations were physically stripped. [DUFOMap WSL](../results/reference/dufomap-wsl/record.json), [BeautyMap WSL](../results/reference/beautymap-wsl/record.json).

The **unmodified original PCL evaluator** at pinned benchmark commit, compiled with GCC 11.4/PCL 1.12.1, agrees with SciPy on all 17,362,230 point identities for each map: **0 disagreements and 0 pp differences**. [Comparison](../results/reference/evaluation-check-wsl/summary.json), [compile and execution provenance](../results/reference/evaluation-check-wsl/record.json). This excludes the evaluator implementation as the cause on these stored maps. It does not explain source-version/parameter differences with paper tables.

A second control uses one trained DUFOMap instance and zero injected error. It first obtains direct `segment` labels, builds a map from those kept points, and then calls native `outputMap`.

| Definition | SA % | DA % |
| --- | ---: | ---: |
| Direct `segment` identity | 92.634271 | 98.957107 |
| Same kept points, 5 cm map NN | 97.981802 | 98.686226 |
| Native output, 5 cm map NN | 97.979798 | 98.702895 |

![Measured correspondence effect](../docs/figures/metric_correspondence.png)

Changing only the scoring of the direct-label-derived map increases SA by **5.347532 pp**. The additional native-map difference is −0.002004 pp SA and +0.016670 pp DA. This localizes most of the large SA gap to map correspondence, without attributing the smaller remainder exclusively to a binding defect: native variation and operation order are not independently isolated. These are measurement definitions, not three algorithms. [Record and binding signatures](../results/reference/api-check-wsl/record.json), [raw counts](../results/reference/api-check-wsl/summary.json).

The [21-frame replay](../docs/figures/replication_hero.gif) uses original PCL labels, common world bounds and named source frames. It shows final offline maps. Counts precede display thinning/cropping. [Rendering metadata](../results/reference/reproduction-media-wsl/render.json).

## 6. First semantic frontend

ConceptGraphs class-agnostic SAM/CLIP segmentation and native 3D association/fusion completed on **40 posed Replica `room0` observations**, producing **39 postprocessed objects**. Four text queries return candidate coordinates in the supplied world frame. Correct retrieval, semantic benchmark accuracy and navigation success have not been evaluated. The SAM batch adaptation and interrupted first run are disclosed in [SEMANTIC](SEMANTIC.md), with exact setup and raw records.

## Verification and remaining work

Local checks: **36 passed**, Ruff clean; Matplotlib dependencies emit deprecation warnings without failing the checks. Portable evidence hashes were verified before export and against committed Git bytes. Most Windows measurements use snapshot `01e2105aeb8a26bf5cdbe7420b56c0dddf81272c`; the final BeautyMap run uses `17591fa` after physically stripping scan intensity annotations while preserving VIEWPOINT. Its metrics are unchanged. Earlier failures remain separately retained. Per-record source hashes specify each executed snapshot.

PCL/SciPy cross-checking and an executable semantic subset with text-coordinate retrieval are complete. Full semantic benchmark evaluation, annotated target correctness, robot navigation and multi-session identity evaluation remain open. The real-data and synthetic results support a focused research question and explicit follow-up protocol, not a system-level performance claim.

Next: investigate paper-version differences, annotate semantic associations/targets and define paired pose-error controls before freezing the hypothesis. [Stage gates](PLAN.md).

## 7. Four-paper media and HOV-SG core — 8 October

HOV-SG's author segment-level feature mapper processes 8 supplied-pose observations (source 0,25,...175), producing 50 segments and 166,777 reference points. Peak mapper PyTorch allocation is 10,030,088,704 bytes, excluding driver allocations. Four CLIP texts return candidate coordinates; accuracy is not annotated. The first 40-observation merge was killed with exit 137 after extraction; cause remains unconfirmed. [Success](../results/reference/hovsg-wsl/record.json), [failure](../results/reference/hovsg-wsl-interrupted/record.json), [resource adaptations](papers/hovsg.md).

Four per-paper H.264/GIF replays are published with full decode checks and metadata. Semantic clips use final maps, not progressive mapping. The actual ConceptGraphs entrypoint uses absolute poses, confirmed by 39 saved matrices; no extra first-frame transformation is applied. [Media/reports](papers/README.md), [coordinate audit](RECORDING.md). These semantic subsets and counts are not full paper benchmark validation.
