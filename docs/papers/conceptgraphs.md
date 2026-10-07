# ConceptGraphs — mapping core reproduction

English | [中文](conceptgraphs.zh-CN.md) | [PDF](../../output/pdf/conceptgraphs.en.pdf)

**Executed:** author class-agnostic SAM/CLIP frontend and native object association/fusion on 40 posed Replica room0 observations. This is a core subset, not complete paper evaluation.

![ConceptGraphs native observations and final map](../media/conceptgraphs/poster.png)

[MP4](../media/conceptgraphs/replay.mp4) · [GIF](../media/conceptgraphs/preview.gif) · [Run](../../results/reference/conceptgraphs-wsl/record.json) · [Media provenance](../../results/reference/paper-media-conceptgraphs/record.json)

## Method and execution

[ConceptGraphs (ICRA 2024)](https://arxiv.org/html/2309.16650v1) lifts 2D segments/features into 3D, matches them using geometric and semantic similarity, and incrementally fuses object representations. The paper also demonstrates localization and dynamic updates; it must not be described as universally static.

```bash
bash scripts/setup_semantic.sh
.venv-semantic/bin/python scripts/run_conceptgraphs.py
```

The isolated CUDA environment pins PyTorch 2.0.1+cu118 and PyTorch3D 0.7.4. Dataset source frames are 0,5,...195 from the NICE-SLAM Replica archive. The range-download manifest records CRC and extracted SHA-256, not a whole-archive checksum. Full SAM/CLIP checkpoint hashes are verified.

## Measured output and adaptations

| Item | Observed result |
| --- | --- |
| Posed RGB-D observations | 40 |
| Postprocessed object representations | 39 |
| Queries | chair, sofa, table, lamp; 3 candidates each |
| Pose-coordinate audit | 39 saved camera matrices agree with supplied absolute poses |
| Query/semantic accuracy | Not evaluated; cosine similarity is not probability |

SAM uses the same 12×12 prompt grid, with batches of 36 instead of 144. The first high-batch run was interrupted and preserved. The patch also records headless/local loading and skipping unused detection modules for the class-agnostic path; geometry and association thresholds are unchanged. Equal masks to an unadapted run are not claimed.

The executed batch mapper uses absolute dataset.poses, bypassing the loader's normalized __getitem__ poses. Historical center_world_m is therefore already in Replica world coordinates. Initialization at observation 0 saves no snapshot; observations 1–39 provide the audited matrices. An additional first-camera transformation would be wrong.

## Limitation and research relevance

The authors report missed thin objects, duplicates and caption errors (III-H). A wrong spatial alignment may fragment identities or fuse two similar objects even when CLIP features are plausible. That additional pose mechanism is our hypothesis, not a measured cross-paper failure. An object count cannot establish association accuracy.

The open question is whether later pose corrections can recover identity and target coordinates after an association/fusion decision. A sidecar retaining frame ID, pose version, masks/features and provisional correspondences is implementable without rebuilding the entire backend. It needs annotations and threshold/visibility controls at equal coverage and delay. Khronos already has joint optimization and reconciliation, so memory/replay alone is not novel.

This method directly connects semantic mapping and visual localization to geometric reliability. LLaVA captions, LLM graph reasoning, complete semantic metrics and navigation are outside this run. [Setup and limitations](../SEMANTIC.md) · [Shared question](../STUDY.md).

## Video interpretation

Native SAM observations appear beside the final world-XZ map and a red query candidate. Gray is other mapped geometry. The map is final, not an online timeline; a highlighted candidate is not a labeled correct answer. Twenty selected source observations are shown. The clip records measured outputs, not a live screen capture.
