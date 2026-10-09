<div align="center">

# SLAM Learning

**Does correcting poses also repair the map?**

Dynamic robust mapping · Semantic mapping and localization

[![CPU reproducibility](https://github.com/p20030920p/SLAM_Learning/actions/workflows/ci.yml/badge.svg)](https://github.com/p20030920p/SLAM_Learning/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.10-3776AB)](pyproject.toml)

English | [中文](README.zh-CN.md)

[Analysis](docs/STUDY.md) · [Evidence](docs/README.md) · [Setup](docs/REPRODUCE.md)

</div>

![Measured author-map replay](docs/figures/replication_hero.gif)

*Saved-map replay; GT only for evaluation/coloring. [Source](results/reference/reproduction-media-wsl/record.json).*

Four 2024 mapping works → pose-error controls → a candidate recovery hypothesis. **H1 remains unverified.**

## SLAM and our two directions

**SLAM — Simultaneous Localization and Mapping:** estimate sensor motion while building a map from its observations.

- **Robust localization and SLAM in dynamic environments:** estimate motion and maintain a stable map despite moving objects.
- **Semantic mapping, visual localization and navigation:** describe objects and their locations, estimate pose from images, and reach a target.

Five elements organize this process:

```text
Sensor data → Front end → Back end (optimize) → Map build
                  ↓              ↑
             Loop detection ─────┘
```

| SLAM element | Effect of improving it | Dynamic direction | Semantic direction |
| --- | --- | --- | --- |
| Sensor data | Cleaner, synchronized observations | Observe motion and occlusion | Align RGB and depth |
| Front end | More reliable matches | Match stable structure | Extract masks/features; associate observations |
| Back end | More consistent poses | Reject bad motion constraints | Align object coordinates |
| Loop detection | Revisit constraints help reduce drift | Recognize places despite changes | Support relocalization |
| Map build | A more usable map | Remove dynamic traces | Maintain identities and query targets |

The first direction emphasizes reliable motion and geometry. The second adds object meaning and target retrieval. Our four reproductions use supplied poses to isolate **map construction**, not complete SLAM or navigation.

## Related works

The GIFs show earlier core subsets; semantic highlights are unverified query candidates.

| [DUFOMap](docs/papers/dufomap.md) | [BeautyMap](docs/papers/beautymap.md) |
| --- | --- |
| ![DUFOMap core replay](docs/media/dufomap/preview.gif) | ![BeautyMap core replay](docs/media/beautymap/preview.gif) |
| **Map build.** Void-space tests remove dynamic points; pose margins protect static geometry. **GIF: 141 scans.** | **Map build.** Binary occupancy finds dynamic traces; restoration protects static geometry. **GIF: 141 scans.** |

| [ConceptGraphs](docs/papers/conceptgraphs.md) | [HOV-SG](docs/papers/hovsg.md) |
| --- | --- |
| ![ConceptGraphs core replay](docs/media/conceptgraphs/preview.gif) | ![HOV-SG core replay](docs/media/hovsg/preview.gif) |
| **Association and semantic map.** Geometry/CLIP matching fuses object observations for text queries. **GIF: 40 frames, 39 representations.** | **Semantic map hierarchy.** The paper organizes floors, rooms and objects for language queries. **GIF: segment core only, 8 frames, 50 segments.** |

## Common dependency and open question

DUFOMap and BeautyMap remove dynamic traces while retaining static geometry. ConceptGraphs and HOV-SG organize objects and semantics for language queries.

All four depend on **pose alignment → correspondence → map decisions**. Misalignment can affect point removal, object fusion or feature assignment. Pose margins, static restoration and association rules already provide protection.

**After pose correction, how can a map repair decisions made under the earlier poses?**

For example, corrected coordinates may still leave one object split or two objects merged. This is a candidate failure mode, not a proven shared defect. We first test ConceptGraphs association under identical pose corrections and candidate caps. [Test and limits](docs/STUDY.md).

## Reproduction results

Later original-code runs use separate protocols, pinned at **535a278**:

| Work | Scored scope | Result |
| --- | --- | --- |
| [DUFOMap](https://github.com/p20030920p/SLAM_Learning/blob/535a2780af7ca7eb3aa02f722e1340fe90bc2dcf/docs/DUFOMAP_TABLE4.md) | Table IV, 141 released scans | SA 97.9635%, DA 98.7196%; 15 entries match paper rounding |
| [BeautyMap](https://github.com/p20030920p/SLAM_Learning/blob/535a2780af7ca7eb3aa02f722e1340fe90bc2dcf/docs/KITTI_PAPER_PROTOCOL.md) | Historical KITTI-02, 91 scans | At XY=1 m: SA 83.3978%, DA 82.4092%; 9 Table III entries match rounding |
| [ConceptGraphs](https://github.com/p20030920p/SLAM_Learning/blob/535a2780af7ca7eb3aa02f722e1340fe90bc2dcf/docs/CONCEPTGRAPHS_ROOM0_RESULTS.md) | room0, 400 observations | mIoU 21.3460%, frequency-weighted IoU 50.1379% |
| [HOV-SG](https://github.com/p20030920p/SLAM_Learning/blob/535a2780af7ca7eb3aa02f722e1340fe90bc2dcf/docs/HOVSG_HOME_RESULTS.md) | room0, 20-frame resource variant | mIoU 34.7500%, F-mIoU 62.8725%; default 200-frame run incomplete |

SA/DA measure static retention/dynamic removal. Semantic scoring uses scene-GT classes and different supports/exclusions, not identity recovery or open-world query success. These scores cannot rank the four methods; complete trajectories and robot navigation remain untested. [Scope](https://github.com/p20030920p/SLAM_Learning/blob/535a2780af7ca7eb3aa02f722e1340fe90bc2dcf/docs/SCOPE.md).

<details>
<summary>Five more GIFs: recorded 3D viewing</summary>

| DUFOMap RViz | BeautyMap RViz |
| --- | --- |
| ![DUFOMap recorded RViz](https://raw.githubusercontent.com/p20030920p/SLAM_Learning/4361d4f353a7449c7d6964887643915d2fc72a11/results/reference/homepage-media/dufomap-rviz.gif) | ![BeautyMap recorded RViz](https://raw.githubusercontent.com/p20030920p/SLAM_Learning/4361d4f353a7449c7d6964887643915d2fc72a11/results/reference/homepage-media/beautymap-rviz.gif) |

| ConceptGraphs RViz | HOV-SG RViz |
| --- | --- |
| ![ConceptGraphs recorded RViz](https://raw.githubusercontent.com/p20030920p/SLAM_Learning/4361d4f353a7449c7d6964887643915d2fc72a11/results/reference/homepage-media/conceptgraphs-rviz.gif) | ![HOV-SG recorded RViz](https://raw.githubusercontent.com/p20030920p/SLAM_Learning/4361d4f353a7449c7d6964887643915d2fc72a11/results/reference/homepage-media/hovsg-rviz.gif) |

Earlier core outputs in RViz; saved-map viewing, no new inference. Full videos: [DUFOMap](docs/media/rviz/dufomap.mp4) · [BeautyMap](docs/media/rviz/beautymap.mp4) · [ConceptGraphs](docs/media/rviz/conceptgraphs.mp4) · [HOV-SG](docs/media/rviz/hovsg.mp4).

![ConceptGraphs original author viewer](https://raw.githubusercontent.com/p20030920p/SLAM_Learning/4361d4f353a7449c7d6964887643915d2fc72a11/results/reference/homepage-media/conceptgraphs-author-viewer.gif)

400-frame author map: RGB/instance colors and orbit controls, without query/graph display. [60-second video](https://github.com/p20030920p/SLAM_Learning/blob/3b0b9a88ac7c77431268b6c869c369e01bd19b3e/evidence/videos/conceptgraphs-room0-original-window.mp4) · [Sources](https://github.com/p20030920p/SLAM_Learning/blob/4361d4f353a7449c7d6964887643915d2fc72a11/results/reference/homepage-media/record.json).

</details>

## Evidence that narrowed the question

![Recovery and exposed-candidate cost](https://raw.githubusercontent.com/p20030920p/SLAM_Learning/4361d4f353a7449c7d6964887643915d2fc72a11/results/reference/homepage-media/recovery-cost.png)

room1, immediately after 30 cm correction: fixed-history recovery **11.1%**, oracle **66.7%**, post-hoc support-1 **100%**; candidates **8.3 / 25 / 117**. Three-seed means, partial AI labels, unequal caps. [Results](docs/DELAYED_RESULTS.md).

A lower support gate closes this selected recovery gap while exposing more fragments; later observations also repair part of it. **Reassociation is not yet shown necessary.** The next test matches candidate caps and checks identities separately.

## Candidate H1 and next test

Retain observation sources and pose versions, then replay affected associations within a bounded cache to recover more valid targets than simple guards. The bounded implementation is **not built or tested**.

room2 freezes one frontend, five AI-labelled instances and exact correction after observation eight. Four arms compare fixed history, threshold-1.0, visibility guards and oracle reassociation at support 1/2/3 and caps 25/50/100/unlimited. **All 28 mapping cells ran; analysis remains pending.** [Protocol](https://github.com/p20030920p/SLAM_Learning/blob/4361d4f353a7449c7d6964887643915d2fc72a11/docs/IDENTITY_BUDGET.md).

Only plan a prototype if oracle gains ≥10 percentage points over every simple control at two finite caps, with ≥2/3 positive paired seeds and no seed increasing labelled duplicates/mixes. Otherwise narrow or stop H1. Equal caps do not match memory; AI-only labels cannot confirm H1. [Decision and remaining work](docs/PLAN.md).

[Khronos](https://arxiv.org/html/2402.13817v2) and [DovSG](https://arxiv.org/html/2410.11989v2) already reconcile/update maps. A contribution must demonstrate a recovery–cost benefit over existing protections; replay alone is not novel.

## Branches

| Branch | Role |
| --- | --- |
| main | Curated submission: question, four reproductions, counterevidence and candidate H1. |
| [reproduce/author-originals](https://github.com/p20030920p/SLAM_Learning/tree/reproduce/author-originals) | Original pipelines, paper-table/semantic scoring and recordings. |
| [study/identity-budget-v2](https://github.com/p20030920p/SLAM_Learning/tree/study/identity-budget-v2) | Exploratory late-correction and equal-cap identity experiments. |

Optional: [personal learning notes](https://github.com/p20030920p/SLAM_Learning/tree/notes/personal-study-guide-20261008) explain H1 and rejection controls; [hardware branch](https://github.com/p20030920p/SLAM_Learning/tree/Personal-Learning-Physical) contains D435/L2 trials, separate from H1 validation.

[AI use](docs/DISCLOSURE.md) · [Sources/licenses](docs/ATTRIBUTION.md) · [Citation](CITATION.cff) · [License](LICENSE)
