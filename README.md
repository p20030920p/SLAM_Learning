<div align="center">

# SLAM Learning

**Reproducing map updates in changing scenes**

Dynamic point removal · Semantic mapping · Localization uncertainty

[![Python](https://img.shields.io/badge/Python-3.10-3776AB)](pyproject.toml)
[![CPU](https://img.shields.io/badge/author%20runs-CPU-356859)](docs/RESULTS.md)

[Reproduction](#reproduction) &nbsp;•&nbsp; [Bottleneck](#bottleneck) &nbsp;•&nbsp; [Quick start](#quick-start)

English &nbsp;|&nbsp; [中文](README.zh-CN.md)

</div>

<!-- MEDIA: replication-hero. Add the image after the measured animation is ready. -->
<!-- ![Raw, removed and retained points across one fixed sequence](docs/figures/replication_hero.gif) -->

> **Animation slot — author-method reproduction.** The same selected teaser entries and fixed view for DUFOMap, BeautyMap and ground truth: raw scan → removed → retained. Green: correctly removed dynamic points; red: removed static points; blue: retained dynamic points. Slot: `docs/figures/replication_hero.gif`.

This repository studies how a robot decides that a mapped surface or object has changed. We start with executable author methods, inspect their outputs and evaluation rules, and then ask which decisions depend on trustworthy localization. The study spans robust mapping in dynamic scenes and persistent semantic maps.

| Current material | Scope |
| --- | --- |
| Author-method reproduction | DUFOMap and BeautyMap; 141-frame KITTI-00 teaser |
| Platforms checked | Windows and fresh Ubuntu 22.04 CI; CPU |
| Measurement | Static retention, dynamic removal; paper comparisons kept separate |
| Exploratory diagnostics | Real-data pose sensitivity; two controlled mechanisms |
| Next prerequisite | Resolve evaluator differences and reproduce a semantic-map frontend |

## Reproduction

Both methods completed all 141 frames and were scored against 17,362,230 labeled points. The cleaned maps use the same 5 cm nearest-neighbor evaluation rule. These are map-cleaning runs with supplied poses, not trajectory-estimation or navigation experiments.

| Author method | SA % ↑ | DA % ↑ | Reported aggregate | Paper-table agreement |
| --- | ---: | ---: | ---: | --- |
| DUFOMap 1.1.1 | 97.9798 | 98.7029 | AA 98.3407 | Difference beyond 0.01 pp tolerance |
| BeautyMap, pinned source | 96.9529 | 98.3382 | HA 97.6407 | Difference beyond 0.01 pp tolerance |

*SA retains static points; DA removes dynamic points. AA is geometric and HA harmonic, so the last column is not one shared ranking. Windows and Ubuntu scores agree. [Full protocol, paper values and raw records](docs/RESULTS.md).*

<!-- MEDIA: replication-frame -->
<!-- ![Author methods and ground truth on the same frame](docs/figures/replication_frame.png) -->

*Qualitative figure slot: one frame, identical spatial bounds and point identities for every panel. Caption must give the frame ID and the run IDs. Slot: `docs/figures/replication_frame.png`.*

A second diagnostic uses DUFOMap's direct point-label API. A larger pose margin preserves more static points but misses more dynamic ones; a small injected pose error does not always reduce the score. Its values cannot be merged into the map-correspondence table above.

![DUFOMap direct-label sensitivity on the real teaser](results/reference/pose-stress/sensitivity.png)

*Three smooth translation amplitudes, two pose margins, one sequence. A sensitivity observation, not a general failure claim.*

## Bottleneck

The working question is **whether a change residual can be separated from localization error, and whether another observation supplies independent evidence**. One pose error can shift many object correspondences together. Without stable anchors, coherent object motion can also resemble camera motion.

This is a candidate structural bottleneck. The real runs establish pose-margin tradeoffs and an evaluation gap; the cross-paper claim also needs a semantic-map reproduction. Khronos already jointly optimizes poses and structure, while newer persistent maps already handle visibility and memory. [Paper-by-paper assumptions and counterexamples](docs/LITERATURE.md).

<!-- MEDIA: bottleneck-diagram -->
<!-- ![Pose uncertainty, association and provisional map updates](docs/figures/bottleneck_diagram.svg) -->

*Diagram slot: supplied/estimated pose → correspondence → change evidence → map update; mark which uncertainty is shared and which edits can be revised. Slot: `docs/figures/bottleneck_diagram.svg`.*

## Candidate hypothesis

At matched query coverage, update latency and observation budget, accounting for shared pose uncertainty before committing changes may reduce false deletion and stale-target error compared with visibility-aware threshold and independent-noise baselines. Enough stable geometry or external pose information must be available.

The hypothesis is **not frozen for confirmation**. First reconcile the measurement protocol and reproduce at least one semantic frontend. The criterion for rejecting it is written in [the research note](docs/RESEARCH.md); [the experiment plan](docs/PLAN.md) specifies the next gates.

## Exploratory experiments

Existing experiments help formulate the question. They are not held-out validation of a hypothesis selected after seeing them.

| Exploration | Observation | Boundary |
| --- | --- | --- |
| Pose–motion ambiguity | Common-mode correction and visibility help with minority movers | A coherent moving majority fools the median correction |
| Correlated evidence | Independent pose-noise inference becomes overconfident under one shared bias | Shared-latent inference has lower changed-object recall and uses known noise scales |

![Confidence under observations that share one pose bias](results/reference/evidence-stress/calibration.png)

*A 1D synthetic model, not a semantic SLAM implementation. Report false deletion, recall and calibration together. [All trials and negative results](docs/RESULTS.md).*

<!-- MEDIA: pose-drift-video / semantic-update-video / risk-coverage -->
*Future comparison slots: `docs/figures/pose_drift.gif`, `docs/figures/semantic_update.mp4`, `docs/figures/risk_coverage.png`. The [media index](docs/figures/README.md) fixes inputs, camera, colors and publication requirements before rendering.*

## Quick start

Python 3.10 and exact dependencies are selected by the lockfile. CUDA is unnecessary for the current author methods.

```bash
uv sync --frozen --python 3.10 --extra methods --extra dev
uv run slam-study fetch
uv run slam-study run --method dufomap
uv run slam-study run --method beautymap
uv run slam-study report --runs results/runs --output results/local-reproduction.md
```

`fetch` verifies a 385 MB public archive and pins upstream commits. `--frames 10` is smoke-only, with no paper score. Fresh output directories prevent an old result from surviving a failed rerun. [Environment, metrics and export commands](docs/REPRODUCE.md).

Inside a prepared Linux/WSL checkout:

```bash
bash scripts/setup_linux.sh
bash scripts/run_reproduction.sh --smoke
bash scripts/run_reproduction.sh
```

The local WSL component is installed, but Ubuntu/platform activation is still required. [WSL setup](docs/WSL.md) distinguishes that prerequisite from completed Ubuntu CI runs.

## Next sequence

1. Reconcile the evaluator and render the author-method comparison.
2. Reproduce a real semantic-map frontend and inspect correspondence failures.
3. Retain or revise the bottleneck, then freeze a hypothesis and held-out protocol.
4. Compare simple baselines at matched coverage and latency; publish figures, failures and raw evidence together.

## Documentation

| Read | Contents |
| --- | --- |
| [Results](docs/RESULTS.md) | Executed methods, exploratory observations and raw records |
| [Literature](docs/LITERATURE.md) | Recent directions, eight core papers, existing solutions |
| [Research note](docs/RESEARCH.md) | Observation → bottleneck → candidate hypothesis |
| [Experiment plan](docs/PLAN.md) | Reproduction gates and future discriminating experiments |
| [Reproduction](docs/REPRODUCE.md) / [WSL](docs/WSL.md) | Installation, execution, scoring and evidence export |
| [Figure and video index](docs/figures/README.md) | Published assets and reserved GIF/video slots |
| [Measured ledger](results/REPORT.md) | Generated from run records |
| [Audit](docs/AUDIT.md) / [Disclosure](docs/INTERVIEW.md) | Source migration and interview preparation |

Every narrative document has an independent [Chinese counterpart](docs/README.zh-CN.md). Historical files remain recoverable at `af1e58b`; they do not contribute scores to the current study.
