<div align="center">

# SLAM Learning

**When should a map believe that the world changed?**

Dynamic robust mapping · Semantic mapping and localization · Shared pose uncertainty

[![CPU reproducibility](https://github.com/p20030920p/SLAM_Learning/actions/workflows/ci.yml/badge.svg)](https://github.com/p20030920p/SLAM_Learning/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.10-3776AB)](pyproject.toml)
[![Papers](https://img.shields.io/badge/author%20cores-4-147D85)](docs/papers/README.md)

[Four papers](#four-related-reproductions) &nbsp;•&nbsp; [Research question](#research-question) &nbsp;•&nbsp; [Physical tests](#d435i-and-unitree-l2-without-a-robot)

English &nbsp;|&nbsp; [中文](README.zh-CN.md)

</div>

![Measured author-map replay](docs/figures/replication_hero.gif)

*Measured final-map replay: 21 selected scans, fixed world view, raw → removed → retained. Green: removed dynamic; red: removed static; blue: retained dynamic. GT is used only for scoring/coloring. [Source and rendering settings](results/reference/reproduction-media-wsl/record.json).*

This study connects the two selected laboratory themes through one interface: **posed observations → spatial correspondence → map decision**. We reproduce author pipelines first, audit their measurements, then formulate a testable hypothesis. The supplied-pose mapping runs do not estimate a SLAM trajectory.

## Four related reproductions

| Paper | Actually executed | Report | Watch | PDF |
| --- | --- | --- | --- | --- |
| DUFOMap, 2024 | Author dynamic-point removal, full 141-scan KITTI-00 teaser | [Card](docs/papers/dufomap.md) | [MP4](docs/media/dufomap/replay.mp4) / [GIF](docs/media/dufomap/preview.gif) | [EN](output/pdf/dufomap.en.pdf) / [中文](output/pdf/dufomap.zh-CN.pdf) |
| BeautyMap, 2024 | Author map cleaning, same full teaser | [Card](docs/papers/beautymap.md) | [MP4](docs/media/beautymap/replay.mp4) / [GIF](docs/media/beautymap/preview.gif) | [EN](output/pdf/beautymap.en.pdf) / [中文](output/pdf/beautymap.zh-CN.pdf) |
| ConceptGraphs, ICRA 2024 | SAM/CLIP and native association/fusion; 40 posed Replica observations, 39 objects | [Card](docs/papers/conceptgraphs.md) | [MP4](docs/media/conceptgraphs/replay.mp4) / [GIF](docs/media/conceptgraphs/preview.gif) | [EN](output/pdf/conceptgraphs.en.pdf) / [中文](output/pdf/conceptgraphs.zh-CN.pdf) |
| HOV-SG, RSS 2024 | Native segment feature-map core; 8 posed observations, 50 segments | [Card](docs/papers/hovsg.md) | [MP4](docs/media/hovsg/replay.mp4) / [GIF](docs/media/hovsg/preview.gif) | [EN](output/pdf/hovsg.en.pdf) / [中文](output/pdf/hovsg.zh-CN.pdf) |

The semantic runs are **explicit core subsets**: complete semantic paper benchmarks, full graph reasoning and navigation are unfinished. Object/segment counts are not accuracy and cannot rank the two systems. The interrupted HOV-SG 40-observation attempt is retained. [Scope and failures](docs/SEMANTIC.md).

| ConceptGraphs: native observations + final object map | HOV-SG: native observations + final segment map |
| --- | --- |
| ![ConceptGraphs replay](docs/media/conceptgraphs/preview.gif) | ![HOV-SG replay](docs/media/hovsg/preview.gif) |

*Red is a text-query candidate, not annotated correctness. Both maps are final world-XZ projections; the clips are measured-output replays, not live screen recordings or FPS benchmarks. [Recording convention and coordinate audit](docs/RECORDING.md).*

## What the numbers establish

| Author method | SA % ↑ | DA % ↑ | Aggregate | Paper-table agreement |
| --- | ---: | ---: | --- | --- |
| DUFOMap 1.1.1 | 97.9798 | 98.7029 | Geometric AA 98.3407 | Not all values within 0.01 pp |
| BeautyMap, pinned source | 96.9529 | 98.3382 | Harmonic HA 97.6407 | Not all values within 0.01 pp |

All 141 scans and 17,362,230 labeled points are evaluated with 5 cm map proximity. Windows, fresh Ubuntu CI and WSL counts agree. Original PCL and SciPy agree **pointwise with zero disagreements** for both maps. This excludes that evaluator implementation as the cause of the remaining paper-table gaps. AA and HA are different aggregates. [Full counts, targets and controls](docs/RESULTS.md).

Changing only the scoring of the same DUFOMap retained points, from original identities to map proximity, raises SA by **5.347532 pp**. This is a measurement effect, not an algorithm gain. The actual ConceptGraphs mapper uses absolute poses; 39 saved camera matrices verify the coordinate convention. These audits matter before drawing a research conclusion.

## Research question

**Can map updates remain reliable under temporally correlated pose errors, at equal change recall, query coverage and update delay, when stable anchors exist?**

The shared dependency is spatial correspondence, not a claim that all four methods ignore noise or assume static scenes. DUFOMap already has tolerances, BeautyMap protects hidden geometry, ConceptGraphs supports updates, and HOV-SG explicitly acknowledges its static-scene limit. Wrong correspondence may cause false removal or incorrect semantic assignment; a shared empirical failure has not yet been established across all four.

Candidate H1 keeps one shared pose variable and observation provenance, delays ambiguous edits, and replays affected observations after a correction. A bounded object/submap sidecar is feasible. Stable anchors are required; known covariance is an oracle diagnostic. Khronos already jointly optimizes and reconciles maps, so memory or joint optimization alone is not a novelty claim.

Reject H1 if a simple threshold/visibility baseline matches its risk at the same recall, coverage and delay, or if deferred edits merely increase stale-target time. Existing room0 and synthetic trials informed the idea and remain exploratory. [Careful four-paper analysis](docs/STUDY.md) · [EN PDF](output/pdf/study.en.pdf) / [中文 PDF](output/pdf/study.zh-CN.pdf).

![Measured correspondence effect](docs/figures/metric_correspondence.png)

<!-- MEDIA: bottleneck-diagram / pose-drift-video / risk-coverage -->
*Reserved research figures: pose/correspondence mechanism, matched-error drift video and held-out risk–coverage–delay curves. [Inputs and publication gates](docs/figures/README.md).*

## D435i and Unitree L2 without a robot

**Planned; hardware data has not been collected.** A robot is unnecessary for testing map decisions and object-coordinate queries.

| Setup | Distinguishing test | Required control |
| --- | --- | --- |
| Fixed D435i tripod | Static / occluded / moved / removed object, semantic identity and target coordinates | Identity sensor pose; background reference and annotated visibility |
| Fixed L2 tripod | Static geometry retention, rays through genuinely empty space | Raw point/time/ring data and verified sensor pose |
| Handheld loop | Same pixels/features, independent versus correlated injected pose errors | Estimated odometry separated from reference; equal achieved pose RMS |
| Rigid D435i + L2 mount | Whether an independent geometric source helps association | Extrinsics, timestamp-offset measurement and RGB-D/LiDAR interference control |

The detailed protocol specifies room layout, calibration, native/ROS capture, event states, labels, validation/test sessions, failure cases, metrics and publication files. D435i IMU is not ground-truth position. A shared-clock assumption is not made for L2. [Executable physical plan](docs/REAL_WORLD.md) · [EN PDF](output/pdf/real-world.en.pdf) / [中文 PDF](output/pdf/real-world.zh-CN.pdf).

<!-- MEDIA: physical-capture-video -->
*Physical video slot: real sensor input + map decision + independent annotation/event view, with session ID and pose source. No synthetic score occupies this slot.*

## Quick start

```bash
uv sync --frozen --python 3.10 --extra methods --extra dev
uv run slam-study fetch
uv run slam-study run --method dufomap
uv run slam-study run --method beautymap
uv run python scripts/verify_evidence.py
uv run python scripts/check_docs.py
```

For Linux/WSL CUDA cores, use `bash scripts/setup_semantic.sh` then `.venv-semantic/bin/python scripts/run_conceptgraphs.py`; use `bash scripts/setup_hovsg.sh` then `.venv-hovsg/bin/python scripts/run_hovsg.py`. Separate environments pin their dependencies and verify checkpoints. [WSL](docs/WSL.md) · [Full reproduction commands](docs/REPRODUCE.md).

## Reading and interview route

| Read | Purpose |
| --- | --- |
| [Four paper cards](docs/papers/README.md) / [Results](docs/RESULTS.md) | Exact executed scope, media, PDF, numbers and retained failures |
| [Cross-paper study](docs/STUDY.md) / [Literature](docs/LITERATURE.md) | Structural question, stated limitations, existing solutions and novelty boundary |
| [Experiment gates](docs/PLAN.md) / [Physical protocol](docs/REAL_WORLD.md) | Reproduce → annotate → freeze hypothesis → held-out comparisons |
| [Recording](docs/RECORDING.md) / [Media index](docs/figures/README.md) | Regenerate measured clips and bilingual reports; reserve future figures |
| [Submission checklist](docs/SUBMISSION.md) / [AI disclosure](docs/INTERVIEW.md) | A reviewer can trace claim → figure → metric → run → command |
| [Measured ledger](results/REPORT.md) / [Source audit](docs/AUDIT.md) | Machine-readable provenance and historical migration |

Every narrative has an independent [Chinese edition](docs/README.zh-CN.md). Historical material is recoverable at `af1e58b` and contributes no current score.
