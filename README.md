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

These are saved-result replays from supplied-pose mapping runs. [GIF sources](results/reference/media-previews-v2/record.json).

### [DUFOMap](docs/papers/dufomap.md)

![DUFOMap core replay](results/reference/media-previews-v2/dufomap.gif)

**KITTI-00 outdoor scene, 141 LiDAR scans.** Observed empty space identifies dynamic points; pose margins protect static geometry. The GIF selects 21 scans to compare input, removed and retained points against the final map. [MP4](docs/media/dufomap/replay.mp4).

### [BeautyMap](docs/papers/beautymap.md)

![BeautyMap core replay](results/reference/media-previews-v2/beautymap.gif)

**KITTI-00 outdoor scene, 141 LiDAR scans.** Occupancy comparisons remove dynamic traces; restoration protects static geometry. The GIF selects 21 scans to compare input, removed and retained points against the final map. [MP4](docs/media/beautymap/replay.mp4).

### [ConceptGraphs](docs/papers/conceptgraphs.md)

![ConceptGraphs core replay](results/reference/media-previews-v2/conceptgraphs.gif)

**Replica room0 indoor scene, 40 RGB-D frames.** Geometry/CLIP matching fuses observations into 39 object representations. The GIF selects 20 frames, showing image segments, the final map and a red text-query candidate. Candidate correctness is unverified. [MP4](docs/media/conceptgraphs/replay.mp4).

### [HOV-SG](docs/papers/hovsg.md)

![HOV-SG core replay](results/reference/media-previews-v2/hovsg.gif)

**Replica room0 indoor scene, 8 RGB-D frames.** Multiview segment/CLIP fusion produces 50 3D segments. The GIF shows input segments, the final feature map and a red query candidate, whose correctness is unverified. This run covers segment mapping; the paper's floor/room hierarchy and navigation are not reproduced. [MP4](docs/media/hovsg/replay.mp4).

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

Each clip records a 3D viewer displaying saved results. No new inference; query highlights are unverified.

**DUFOMap · RViz**

![DUFOMap recorded RViz](results/reference/media-previews-v2/dufomap-rviz.gif)

**KITTI-00, 141-scan run.** RViz switches between input, removed and retained point clouds to inspect dynamic-point removal. [MP4](docs/media/rviz/dufomap.mp4).

**BeautyMap · RViz**

![BeautyMap recorded RViz](results/reference/media-previews-v2/beautymap-rviz.gif)

**KITTI-00, 141-scan run.** RViz compares input, removed and retained point clouds in the same 3D view. [MP4](docs/media/rviz/beautymap.mp4).

**ConceptGraphs · RViz**

![ConceptGraphs recorded RViz](results/reference/media-previews-v2/conceptgraphs-rviz.gif)

**Replica room0, 40 RGB-D frames.** The GIF takes chronological excerpts from five saved maps (observations 1/10/20/30/39) and four text-query stages. [MP4](docs/media/rviz/conceptgraphs.mp4).

**HOV-SG · RViz**

![HOV-SG recorded RViz](results/reference/media-previews-v2/hovsg-rviz.gif)

**Replica room0, 8 RGB-D frames.** RViz shows the final 50-segment feature map and text-query candidates. [MP4](docs/media/rviz/hovsg.mp4).

**ConceptGraphs · Author viewer**

![ConceptGraphs original author viewer](results/reference/media-previews-v2/conceptgraphs-author-viewer.gif)

**Replica room0, 400 RGB-D frames.** The original author viewer rotates the saved map and switches RGB/instance colors. Queries and scene-graph relations are not displayed. [60-second video](https://github.com/p20030920p/SLAM_Learning/blob/3b0b9a88ac7c77431268b6c869c369e01bd19b3e/evidence/videos/conceptgraphs-room0-original-window.mp4) · [Sources](https://github.com/p20030920p/SLAM_Learning/blob/4361d4f353a7449c7d6964887643915d2fc72a11/results/reference/homepage-media/record.json).

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
