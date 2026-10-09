<div align="center">

# SLAM Learning

**When should a map believe that the world changed?**

Dynamic robust mapping · Semantic mapping and localization

[![CPU reproducibility](https://github.com/p20030920p/SLAM_Learning/actions/workflows/ci.yml/badge.svg)](https://github.com/p20030920p/SLAM_Learning/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.10-3776AB)](pyproject.toml)

English | [中文](README.zh-CN.md)

[Research analysis](docs/STUDY.md) · [Experimental results](docs/PAIRED_RESULTS.md) · [Home validation design](docs/REAL_WORLD.md)

</div>

> **In progress:** [room2 identity-budget study](docs/IDENTITY_BUDGET.md), with AI-only labels. All 28 native cells have run; analysis is pending. H1 remains unverified.

![Measured author-map replay](docs/figures/replication_hero.gif)

*Saved-map replay, not live inference; GT is used for evaluation and coloring. [Source](results/reference/reproduction-media-wsl/record.json).*

Four 2024 mapping cores, followed by controlled pose-error experiments. These runs use supplied poses; they do not estimate trajectories.

## Direction choice and analysis

**I choose:**

- Robust localization and SLAM in dynamic environments;
- Semantic mapping, visual anchoring and navigation.

**Analysis:**

SLAM means **Simultaneous Localization and Mapping**: *an agent uses sensor data to build a map of an initially unknown environment while estimating its own motion.*

The two coupled tasks are localization and mapping. Real-time processing is a goal of online SLAM; practical systems may also use prior information.

```text
Sensor data → Front end → Back end (optimization) → Map
                  │              ↑
                  └─ Loop closure ┘
```

**Direction 1:**

<!-- Dynamic environments: to be completed. -->

**Direction 2:**

<!-- Semantic mapping, visual anchoring and navigation: to be completed. -->

## Open research question

<!-- To be completed. -->

## Related works

<!-- To be completed. -->

## Hypothesis

<!-- To be completed. -->

## Reproduction scope

| Work | Actually completed | Inspect | Bilingual reports |
| --- | --- | --- | --- |
| DUFOMap | Author 1.1.1; all 141 KITTI teaser scans and 17,362,230 points | [Card](docs/papers/dufomap.md) · [Video](docs/media/dufomap/replay.mp4) · [RViz](docs/media/rviz/dufomap.mp4) | [EN](output/pdf/dufomap.en.pdf) / [中文](output/pdf/dufomap.zh-CN.pdf) |
| BeautyMap | Author map cleaning on the same teaser; GT excluded from algorithm inputs | [Card](docs/papers/beautymap.md) · [Video](docs/media/beautymap/replay.mp4) · [RViz](docs/media/rviz/beautymap.mp4) | [EN](output/pdf/beautymap.en.pdf) / [中文](output/pdf/beautymap.zh-CN.pdf) |
| ConceptGraphs | SAM/CLIP and association/fusion on 40 posed room0 observations; 39 objects | [Card](docs/papers/conceptgraphs.md) · [Video](docs/media/conceptgraphs/replay.mp4) · [RViz](docs/media/rviz/conceptgraphs.mp4) | [EN](output/pdf/conceptgraphs.en.pdf) / [中文](output/pdf/conceptgraphs.zh-CN.pdf) |
| HOV-SG | Segment feature-map core on 8 room0 observations; 50 segments | [Card](docs/papers/hovsg.md) · [Video](docs/media/hovsg/replay.mp4) · [RViz](docs/media/rviz/hovsg.mp4) | [EN](output/pdf/hovsg.en.pdf) / [中文](output/pdf/hovsg.zh-CN.pdf) |

Semantic reproductions are explicit core subsets. Complete semantic benchmarks, LLM graph reasoning, floor/room hierarchy and navigation remain unfinished. The interrupted 40-observation HOV-SG attempt is retained. [Scope and failures](docs/SEMANTIC.md).

| ConceptGraphs object map | HOV-SG segment map |
| --- | --- |
| ![ConceptGraphs](docs/media/conceptgraphs/preview.gif) | ![HOV-SG](docs/media/hovsg/preview.gif) |

*Red denotes a text-query candidate, not annotated correctness. Both clips replay saved outputs.*

## How the results revise the question

![Paired measurements and seed ranges](results/reference/paired-pose/figures/paired-results.png)

**76 primary cells + 21 exploratory parameter controls** show that at 30 cm RMS, monotone drift preserves more static LiDAR points than shuffled errors, while ConceptGraphs loses more partial-surface coverage. This rejects “temporal correlation is always worse.” A common dominant shared-uncertainty bottleneck remains unproven; simple threshold changes already improve some outcomes.

Changing only correspondence in the scoring of the same DUFOMap output changes SA by **5.347532 percentage points**. This is a measurement effect, not an algorithm gain. One teaser, one static room and four partial surfaces without independent human annotation review limit the claims.

**Narrowed open question:** when a later pose correction changes historical correspondence, how can object identity and query coordinates become valid again, while exposing results that remain stale? Candidate H1 retains observation provenance, pose versions and bounded replay. No prototype benefit has been established.

[Standalone analysis: achievements, gaps, metrics and H1](docs/STUDY.md) · [Full paired results](docs/PAIRED_RESULTS.md) · [Protocol](docs/PAIRED_PROTOCOL.md) · [Paired report EN](output/pdf/paired-study.en.pdf) / [中文](output/pdf/paired-study.zh-CN.pdf)

## Delayed correction on a new scene

**35 frozen room1 cells + 6 separate post-hoc controls** revise the diagnosis. At 30 cm, immediate recovery is 11.1% with corrected geometry and fixed history versus 66.7% with oracle reassociation. Lowering the support gate from 3 to 1 raises fixed-history recovery to 100%, while exposed candidates rise from 8.3 to 117.0. Labels are partial and await independent human review. Reassociation is not yet shown necessary; test identity quality and equal candidate budgets before implementing H1. [New results and decision](docs/DELAYED_RESULTS.md) · [EN report](output/pdf/delayed-study.en.pdf) / [中文](output/pdf/delayed-study.zh-CN.pdf).

The D435i / Unitree L2 [home experiment design](docs/REAL_WORLD.md) begins with separate fixed-sensor static, occlusion, movement and removal sessions, followed by handheld revisits. **No physical validation results are available yet.**

## Inspect and reproduce

[Minimal reproduction commands](docs/REPRODUCE.md) · [Paper cards and raw results](docs/papers/README.md) · [Visualization scope](docs/RECORDING.md) · [Document index](docs/README.md)

`src/`, `scripts/` and `configs/` contain study code and pinned settings; `results/reference/` contains portable raw evidence and failures; `output/pdf/` contains 16 report snapshots. Full datasets, weights, maps and personal operating notes stay outside main.

[AI use and research boundaries](docs/DISCLOSURE.md) · [Sources and licenses](docs/ATTRIBUTION.md) · [Citation](CITATION.cff) · [License](LICENSE)
