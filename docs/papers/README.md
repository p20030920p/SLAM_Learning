# Paper reproduction status and retained subsets

English | [中文](README.zh-CN.md)

The common interface is posed observation → spatial correspondence → map decision. These four 2024 papers connect dynamic robust mapping and semantic mapping/localization. Their tasks and output definitions differ; this index is not a common leaderboard.

| Paper | Executed scope | Report | Recording | PDF |
| --- | --- | --- | --- | --- |
| DUFOMap | Full 141-scan public teaser; dynamic point removal | [Card](dufomap.md) | [MP4](../media/dufomap/replay.mp4) / [GIF](../../results/reference/media-previews-v3/dufomap.gif) | [EN](../pdf/dufomap.en.pdf) / [中文](../pdf/dufomap.zh-CN.pdf) |
| BeautyMap | Full same teaser; author map cleaning | [Card](beautymap.md) | [MP4](../media/beautymap/replay.mp4) / [GIF](../../results/reference/media-previews-v3/beautymap.gif) | [EN](../pdf/beautymap.en.pdf) / [中文](../pdf/beautymap.zh-CN.pdf) |
| ConceptGraphs | 40 posed Replica observations; SAM/CLIP and object fusion | [Card](conceptgraphs.md) | Full 69.6 s [MP4](../media/rviz/conceptgraphs.mp4) / [GIF](../../results/reference/conceptgraphs-full-media/conceptgraphs-rviz.gif) | [EN](../pdf/conceptgraphs.en.pdf) / [中文](../pdf/conceptgraphs.zh-CN.pdf) |
| HOV-SG | **Not reproduced**; default 200-frame run and complete paper experiments unfinished | [Status](hovsg.md) | Removed from delivery showcase | Historical subset PDFs only |

These GIFs, cards and PDFs describe earlier supplied-pose subsets. Later original-code runs include paper-table checks and scoped semantic scoring: [author scope at 535a278](https://github.com/p20030920p/SLAM_Learning/blob/535a2780af7ca7eb3aa02f722e1340fe90bc2dcf/docs/SCOPE.md). Full SLAM, complete benchmarks, scene-graph reasoning and navigation remain incomplete.

PDFs in [docs/pdf](../pdf) retain their recorded generation snapshots, including earlier study/hardware text; they are not the current submission narrative. Read [STUDY](../research/STUDY.md) and [PLAN](../research/PLAN.md) for the current question and decision. Failures and resource adaptations remain recorded.

Follow [RECORDING](../guides/RECORDING.md) to regenerate media/reports from verified local outputs. [paper_suite.json](../../src/configs/paper_suite.json) binds this selection to native records, commands and language editions.
