<div align="center">

# SLAM Learning

**Does correcting poses also repair the map?**

Dynamic robust mapping · Semantic mapping and localization

[![CPU reproducibility](https://github.com/p20030920p/SLAM_Learning/actions/workflows/ci.yml/badge.svg)](https://github.com/p20030920p/SLAM_Learning/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.10-3776AB)](pyproject.toml)

English | [中文](README.zh-CN.md)

[Analysis](docs/STUDY.md) · [Results](docs/PAIRED_RESULTS.md) · [Hardware plan](docs/REAL_WORLD.md)

</div>

> **room2:** 28 cells executed; analysis pending. AI-only labels; H1 unverified. [Study](docs/IDENTITY_BUDGET.md).

![Measured author-map replay](docs/figures/replication_hero.gif)

*Saved-map replay; GT only for evaluation/coloring. [Source](results/reference/reproduction-media-wsl/record.json).*

Four 2024 mapping cores using supplied poses. Trajectory estimation and navigation are outside these runs.

## Direction choice and analysis

- **Dynamic SLAM:** preserve stable geometry when objects move.
- **Semantic mapping, visual localization and navigation:** connect objects to reliable coordinates.

SLAM jointly estimates motion and builds a map.

```text
Sensor data → Front end → Back end (optimize) → Map build
                  ↓              ↑
             Loop detection ─────┘
```

| SLAM element | Dynamic robustness | Semantic grounding |
| --- | --- | --- |
| Sensor data | Motion, occlusion | RGB-D alignment |
| Front end | Stable correspondences | Masks, features, association |
| Back end | Robust pose constraints | Consistent coordinates |
| Loop detection | Recognize changed places | Refresh object anchors |
| Map build | Remove dynamic traces | Maintain identities and targets |

Our four cores study **pose → correspondence → map decisions**; a common failure mechanism remains unproven.

## Open research question

**At the same candidate cap, does reassociation improve target recovery after a late pose correction?**

## Related works

These GIFs replay core outputs. LiDAR colors show removal outcomes; semantic highlights are unverified query candidates. [Media scope](docs/RECORDING.md).

| [DUFOMap](docs/papers/dufomap.md) | [BeautyMap](docs/papers/beautymap.md) |
| --- | --- |
| ![DUFOMap core replay](docs/media/dufomap/preview.gif) | ![BeautyMap core replay](docs/media/beautymap/preview.gif) |
| Void-space filtering removes dynamic returns. **141 scans.** | Binary occupancy and restoration clean the map. **141 scans.** |

| [ConceptGraphs](docs/papers/conceptgraphs.md) | [HOV-SG](docs/papers/hovsg.md) |
| --- | --- |
| ![ConceptGraphs core replay](docs/media/conceptgraphs/preview.gif) | ![HOV-SG core replay](docs/media/hovsg/preview.gif) |
| SAM/CLIP association produces objects and query candidates. **40 frames, 39 representations.** | Segment fusion produces a queryable feature map. **8 frames, 50 segments; no hierarchy/navigation.** |

Larger official runs live on [`reproduce/author-originals`](https://github.com/p20030920p/SLAM_Learning/tree/reproduce/author-originals), snapshot **`3b0b9a8`**; the four GIFs above show the earlier subsets.

| Work | Official-run evidence | Remaining issue |
| --- | --- | --- |
| DUFOMap | 1,997 scans; [Table IV](https://github.com/p20030920p/SLAM_Learning/blob/3b0b9a88ac7c77431268b6c869c369e01bd19b3e/docs/DUFOMAP_TABLE4.zh-CN.md): 15 accuracy entries match two decimals | Pose sensitivity despite tolerances; needs observed empty space |
| BeautyMap | 1,997 scans; historical KITTI-02 [Table III](https://github.com/p20030920p/SLAM_Learning/blob/3b0b9a88ac7c77431268b6c869c369e01bd19b3e/docs/KITTI_PAPER_PROTOCOL.zh-CN.md): 9 entries match two decimals | Alignment and grid-size trade-offs despite restoration |
| ConceptGraphs | [room0](https://github.com/p20030920p/SLAM_Learning/blob/3b0b9a88ac7c77431268b6c869c369e01bd19b3e/docs/CONCEPTGRAPHS_ROOM0_RESULTS.zh-CN.md): 400 frames, semantic scoring complete | Missed/duplicate objects and caption errors |
| HOV-SG | [20-frame variant](https://github.com/p20030920p/SLAM_Learning/blob/3b0b9a88ac7c77431268b6c869c369e01bd19b3e/docs/HOVSG_HOME_RESULTS.zh-CN.md): 156 segments, scoring pending; 200-frame fusion timed out | Static-scene assumption, slow construction |

<details>
<summary>Five more GIFs: recorded 3D viewing</summary>

| DUFOMap RViz | BeautyMap RViz |
| --- | --- |
| ![DUFOMap recorded RViz](results/reference/homepage-media/dufomap-rviz.gif) | ![BeautyMap recorded RViz](results/reference/homepage-media/beautymap-rviz.gif) |

| ConceptGraphs RViz | HOV-SG RViz |
| --- | --- |
| ![ConceptGraphs recorded RViz](results/reference/homepage-media/conceptgraphs-rviz.gif) | ![HOV-SG recorded RViz](results/reference/homepage-media/hovsg-rviz.gif) |

Earlier core outputs in RViz; saved-map viewing, no new inference. Full videos: [DUFOMap](docs/media/rviz/dufomap.mp4) · [BeautyMap](docs/media/rviz/beautymap.mp4) · [ConceptGraphs](docs/media/rviz/conceptgraphs.mp4) · [HOV-SG](docs/media/rviz/hovsg.mp4).

![ConceptGraphs original author viewer](results/reference/homepage-media/conceptgraphs-author-viewer.gif)

400-frame author map: RGB/instance colors and orbit controls, without query/graph display. [60-second video](https://github.com/p20030920p/SLAM_Learning/blob/3b0b9a88ac7c77431268b6c869c369e01bd19b3e/evidence/videos/conceptgraphs-room0-original-window.mp4) · [Sources](results/reference/homepage-media/record.json).

</details>

**Metrics:**

![Separate LiDAR core and original semantic measurements](results/reference/homepage-media/baseline-metrics.png)

| Run | Metric | Result |
| --- | --- | ---: |
| DUFOMap, 141 scans | Static retention SA / dynamic removal DA | 97.9798% / 98.7029% |
| BeautyMap, same inputs | SA / DA | 96.9529% / 98.3382% |
| ConceptGraphs, author room0 | mIoU / frequency-weighted IoU | 21.3460% / 50.1379% |
| HOV-SG, author 20 frames | Semantic accuracy | Pending |

Separate protocols: LiDAR uses 5 cm map-neighbor scoring; room0 uses 23 classes and 4,085,377 scoring points. Counts are not accuracy. [Definitions/sources](results/reference/homepage-media/record.json) · [Renderer](scripts/build_homepage_media.py).

## Hypothesis

**H1, untested:** version observation sources, mark affected targets stale, then replay associations within a bounded cache after pose correction.

![Recovery and exposed-candidate cost](results/reference/homepage-media/recovery-cost.png)

room1, immediate correction at 30 cm: fixed-history recovery **11.1%**, oracle **66.7%**, post-hoc support-1 **100%**; candidates **8.3 / 25 / 117**, respectively. Three-seed means, partial AI labels, unequal caps. [Results](docs/DELAYED_RESULTS.md).

room2 compares fixed history, threshold/visibility guards and full replay at equal caps; equal caps do not match memory. Simple controls matching oracle would weaken H1. [Protocol and decision rule](docs/IDENTITY_BUDGET.md). Map reconciliation and memory updates already exist in [Khronos](https://arxiv.org/html/2402.13817v2) and [DovSG](https://arxiv.org/html/2410.11989v2).

## Branches

| Branch | Focus |
| --- | --- |
| [`study/identity-budget-v2`](https://github.com/p20030920p/SLAM_Learning/tree/study/identity-budget-v2) | Late pose correction and candidate-budget experiments; H1 unverified. |
| [`reproduce/author-originals`](https://github.com/p20030920p/SLAM_Learning/tree/reproduce/author-originals) | Four official pipelines, metric checks and recordings. |
| [`notes/personal-study-guide-20261008`](https://github.com/p20030920p/SLAM_Learning/tree/notes/personal-study-guide-20261008) | [Research notes: H1 and rejection controls](https://github.com/p20030920p/SLAM_Learning/blob/71a2e7556e231c1d0e6814febb085bea9d225f44/notes/OPEN_QUESTION_AND_HYPOTHESIS.zh-CN.md). |
| [`Personal-Learning-Physical`](https://github.com/p20030920p/SLAM_Learning/tree/Personal-Learning-Physical) | [D435/L2 capture, mapping trials and eight-frame semantic-loader checks](https://github.com/p20030920p/SLAM_Learning/blob/4e5a5e8b703e5072ca5e11cf6893d03bca244473/README.zh-CN.md). |

D435 has no IMU. LiDAR odometry failed the drift check; fusion and semantic quality remain unvalidated.

## Inspect and reproduce

[Commands](docs/REPRODUCE.md) · [Paper cards, videos and PDFs](docs/papers/README.md) · [Paired experiments](docs/PAIRED_RESULTS.md) · [Docs](docs/README.md)

[AI use](docs/DISCLOSURE.md) · [Sources/licenses](docs/ATTRIBUTION.md) · [Citation](CITATION.cff) · [License](LICENSE)
