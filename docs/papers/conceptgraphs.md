# ConceptGraphs

English | [中文](conceptgraphs.zh-CN.md) | [PDF](../pdf/conceptgraphs.en.pdf)

**Executed:** author class-agnostic SAM/CLIP frontend and native object association/fusion on 40 posed Replica room0 observations. This is a core subset, not complete paper evaluation.

![ConceptGraphs observations and final map](../../results/reference/media-previews-v3/conceptgraphs.gif)

**Summary replay: 13.33 seconds, 160 video frames at 12 fps.** Twenty selected observations show native image segments beside the final map and text-query candidates. The map is final, not an online mapping timeline; candidate correctness is unverified.

[MP4](../media/conceptgraphs/replay.mp4) · [GIF](../../results/reference/media-previews-v3/conceptgraphs.gif) · [Run](../../results/reference/conceptgraphs-wsl/record.json) · [Timing](../../results/reference/media-previews-v3/record.json)

## Method

[ConceptGraphs (ICRA 2024)](https://arxiv.org/html/2309.16650v1) lifts 2D segments/features into 3D, matches them using geometric and semantic similarity, and incrementally fuses object representations. The paper also demonstrates localization and dynamic updates; it must not be described as universally static.

```bash
bash src/scripts/setup/setup_semantic.sh
.venv-semantic/bin/python src/scripts/methods/run_conceptgraphs.py
```

The isolated CUDA environment pins PyTorch 2.0.1+cu118 and PyTorch3D 0.7.4. Dataset source frames are 0,5,...195 from the NICE-SLAM Replica archive. The range-download manifest records CRC and extracted SHA-256, not a whole-archive checksum. Full SAM/CLIP checkpoint hashes are verified.

## Results

| Item | Observed result |
| --- | --- |
| Posed RGB-D observations | 40 |
| Postprocessed object representations | 39 |
| Queries | chair, sofa, table, lamp; 3 candidates each |
| Pose-coordinate audit | 39 saved camera matrices agree with supplied absolute poses |
| Query/semantic accuracy | Not evaluated; cosine similarity is not probability |

SAM uses the same 12×12 prompt grid, with batches of 36 instead of 144. The first high-batch run was interrupted and preserved. The patch also records headless/local loading and skipping unused detection modules for the class-agnostic path; geometry and association thresholds are unchanged. Equal masks to an unadapted run are not claimed.

The executed batch mapper uses absolute dataset.poses, bypassing the loader's normalized __getitem__ poses. Historical center_world_m is therefore already in Replica world coordinates. Initialization at observation 0 saves no snapshot; observations 1–39 provide the audited matrices. An additional first-camera transformation would be wrong.

## Limits

The authors report missed thin objects, duplicates and caption errors (III-H). A wrong spatial alignment may fragment identities or fuse two similar objects even when CLIP features are plausible. That additional pose mechanism is our hypothesis, not a measured cross-paper failure. An object count cannot establish association accuracy.

The open question is whether later pose corrections can recover identity and target coordinates after an association/fusion decision. A sidecar retaining frame ID, pose version, masks/features and provisional correspondences is implementable without rebuilding the entire backend. It needs annotations and threshold/visibility controls at equal coverage and delay. Khronos already has joint optimization and reconciliation, so memory/replay alone is not novel.

This method directly connects semantic mapping and visual localization to geometric reliability. LLaVA captions, LLM graph reasoning, complete semantic metrics and navigation are outside this run. [Setup and limitations](../guides/SEMANTIC.md) · [Shared question](../research/STUDY.md).

## Playback

The original summary is restored as the main display. Its renderer selects 20 of the 40 observations; a same-layout replay of all 40 has not been exported. [Media record](../../results/reference/paper-media-conceptgraphs/record.json).

Longer recordings remain available separately:

- **RViz:** complete 69.6-second recording, 348 frames at 5 fps; five saved mapping snapshots and four query stages, including opening and ending. [MP4](../media/rviz/conceptgraphs.mp4) · [GIF](../../results/reference/conceptgraphs-full-media/conceptgraphs-rviz.gif).
- **Author viewer:** complete 60-second recording, 900 frames at 15 fps, from a separate [400-observation room0 run](https://github.com/p20030920p/SLAM_Learning/blob/535a2780af7ca7eb3aa02f722e1340fe90bc2dcf/docs/CONCEPTGRAPHS_ROOM0_RESULTS.md). It rotates the saved map and switches RGB/instance colors, without queries or scene-graph relations. [MP4](https://github.com/p20030920p/SLAM_Learning/blob/3b0b9a88ac7c77431268b6c869c369e01bd19b3e/evidence/videos/conceptgraphs-room0-original-window.mp4) · [GIF](../../results/reference/conceptgraphs-full-media/conceptgraphs-author-viewer.gif).

[Complete-recording timing and sources](../../results/reference/conceptgraphs-full-media/record.json). These are saved-result inspections, not continuous recordings of all mapping updates.
