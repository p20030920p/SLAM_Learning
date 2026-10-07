# Four related paper reproductions

English | [中文](README.zh-CN.md)

The common interface is posed observation → spatial correspondence → map decision. These four 2024 papers connect dynamic robust mapping and semantic mapping/localization. Their tasks and output definitions differ; this index is not a common leaderboard.

| Paper | Executed scope | Report | Recording | PDF |
| --- | --- | --- | --- | --- |
| DUFOMap | Full 141-scan public teaser; dynamic point removal | [Card](dufomap.md) | [MP4](../media/dufomap/replay.mp4) / [GIF](../media/dufomap/preview.gif) | [EN](../../output/pdf/dufomap.en.pdf) / [中文](../../output/pdf/dufomap.zh-CN.pdf) |
| BeautyMap | Full same teaser; author map cleaning | [Card](beautymap.md) | [MP4](../media/beautymap/replay.mp4) / [GIF](../media/beautymap/preview.gif) | [EN](../../output/pdf/beautymap.en.pdf) / [中文](../../output/pdf/beautymap.zh-CN.pdf) |
| ConceptGraphs | 40 posed Replica observations; SAM/CLIP and object fusion | [Card](conceptgraphs.md) | [MP4](../media/conceptgraphs/replay.mp4) / [GIF](../media/conceptgraphs/preview.gif) | [EN](../../output/pdf/conceptgraphs.en.pdf) / [中文](../../output/pdf/conceptgraphs.zh-CN.pdf) |
| HOV-SG | 8 posed observations; segment feature-map core | [Card](hovsg.md) | [MP4](../media/hovsg/replay.mp4) / [GIF](../media/hovsg/preview.gif) | [EN](../../output/pdf/hovsg.en.pdf) / [中文](../../output/pdf/hovsg.zh-CN.pdf) |

All use supplied poses. Full SLAM, semantic paper benchmarks, scene-graph reasoning and navigation are not completed. Failed runs and resource adaptations are retained. The [cross-paper analysis](../STUDY.md) and [D435i/L2 protocol](../REAL_WORLD.md) have separate bilingual PDFs in [output/pdf](../../output/pdf).

Follow [RECORDING](../RECORDING.md) to regenerate media/reports from verified local outputs. [paper_suite.json](../../configs/paper_suite.json) binds this selection to native records, commands and language editions.
