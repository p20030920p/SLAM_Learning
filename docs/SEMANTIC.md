# ConceptGraphs frontend reproduction

English | [中文](SEMANTIC.zh-CN.md)

On 8 October 2026, the pinned author **class-agnostic ConceptGraphs** frontend executed on local WSL2 Ubuntu 22.04 and RTX 4070 SUPER. Forty Replica `room0` observations produced **39 postprocessed objects**. Four CLIP text queries returned three object candidates and supplied-world coordinates each. [Run record](../results/reference/conceptgraphs-wsl/record.json), [output](../results/reference/conceptgraphs-wsl/summary.json), [native mapping log](../results/reference/conceptgraphs-wsl/mapping.log).

This establishes an executable RGB-D segmentation, object association/fusion and coordinate-query baseline. Query correctness, semantic benchmark scores, dynamic-scene performance and navigation success are **not evaluated**. A returned coordinate is not proof of a correct target. The camera-to-world poses are supplied, not estimated by SLAM. LLaVA captions, LLM scene-graph construction and planning are outside this run.

## Run the separate environment

In `~/projects/SLAM_Learning`, after [Linux setup](WSL.md):

```bash
bash scripts/setup_semantic.sh
.venv-semantic/bin/python scripts/run_conceptgraphs.py
```

The CPU `uv.lock` environment stays separate. [Semantic requirements](../environments/semantic/requirements.txt) pin the installed distributions; [semantic.json](../configs/semantic.json) pins author commits, checkpoints, the PyTorch3D binary and method settings. Tested Python is 3.10.12, PyTorch 2.0.1+cu118 and PyTorch3D 0.7.4. The script installs the author-recommended Linux binary with a SHA-256 check into this project's semantic environment, without requiring a system CUDA toolkit. Setup was executed, not merely drafted.

## Data and poses

The [author instructions](https://github.com/concept-graphs/concept-graphs) use the [NICE-SLAM rendered Replica trajectory](https://github.com/cvg/nice-slam/blob/master/scripts/download_replica.sh). The public ZIP is 12,442,855,671 bytes. HTTP ranges fetch only source frames `000000, 000005, …, 000195`, their depth images and `traj.txt`; whole-archive SHA-256 is not claimed. ZIP CRC validates fetched members, and the saved [manifest](../results/reference/conceptgraphs-wsl/dataset-manifest.json) binds extracted-file SHA-256 values, archive length and ETag.

The 40 corresponding original pose matrices are placed in matching compact order. The author loader runs with stride 1 on this subset, equivalent to selecting stride 5 from the first 200 source entries. Mapping uses the original 480×640 image setting with rescaled intrinsics and supplied world poses. This is a short rendered static scene, not a real robot deployment or full Replica paper evaluation.

Each run receives an isolated copy of the RGB-D subset and author code. It cannot reuse old detections or a previous object map as a new result. Model weights and RGB-D data are excluded from Git.

## Compatibility and resource adaptations

The [complete patch](../results/reference/conceptgraphs-wsl/compatibility.patch) records headless Matplotlib, skipping unused GroundingDINO/RAM imports and initialization for `class_set=none`, local checkpoint selection, and SAM point batching. Geometry, association equations and decision thresholds are not patched.

The author default batches all 144 sampled SAM prompts at once. On this 12 GiB GPU, the first frame saturated memory and stalled; that run was deliberately interrupted and retained as [an interrupted run](../results/reference/conceptgraphs-wsl-batch144-interrupted/record.json). The completed run keeps the 12×12 sampling grid and processes batches of 36. Batch partitioning is an explicit resource adaptation; identical masks to an unadapted reference are not claimed. Segmentation completed all 40 inputs before the mapping stage.

SAM ViT-H comes from a revision-pinned Hugging Face mirror after the Meta download stalled; CLIP ViT-H comes from the LAION model repository. Both full file hashes are checked before model loading. The mirror source and revisions are explicit in the configuration. Full-system timing or peak-memory claims are not made from the parent process.

## What the baseline tells us

The original mapping log contains object additions, filtering and merging; these operations execute on real RGB-D observations and foundation-model features rather than oracle object identities. The final object count alone cannot measure fragmentation or correct association. The published query scores are cosine similarity, not calibrated probabilities.

Next, add annotated object identities and query targets, then compare exact, independent and temporally correlated pose errors with the segmentation/features fixed. Include threshold sweeps and matched coverage/latency. The shared-pose hypothesis remains a candidate until these controls and held-out scenes are defined. [Stage plan](PLAN.md).
