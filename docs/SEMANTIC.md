# ConceptGraphs frontend reproduction

English | [中文](SEMANTIC.zh-CN.md)

[Paired results](PAIRED_RESULTS.md) add 97 cells and simple controls. Baseline PDFs retain their original source snapshots.

On 8 October 2026, the pinned author **class-agnostic ConceptGraphs** frontend executed on local WSL2 Ubuntu 22.04 and RTX 4070 SUPER. Forty Replica `room0` observations produced **39 postprocessed objects**. Four CLIP text queries returned three object candidates and supplied-world coordinates each. [Run record](../results/reference/conceptgraphs-wsl/record.json), [output](../results/reference/conceptgraphs-wsl/summary.json), [native mapping log](../results/reference/conceptgraphs-wsl/mapping.log).

This establishes an executable RGB-D segmentation, object association/fusion and coordinate-query baseline. Query correctness, semantic benchmark scores, dynamic-scene performance and navigation success are **not evaluated**. A returned coordinate is not proof of a correct target. The camera-to-world poses are supplied, not estimated by SLAM. LLaVA captions, LLM scene-graph construction and planning are outside this run.

## 1. Run the separate environment

In `~/projects/SLAM_Learning`, after [Linux setup](REPRODUCE.md):

```bash
bash scripts/setup_semantic.sh
.venv-semantic/bin/python scripts/run_conceptgraphs.py
```

The CPU `uv.lock` environment stays separate. [Semantic requirements](../environments/semantic/requirements.txt) pin the installed distributions; [semantic.json](../configs/semantic.json) pins author commits, checkpoints, the PyTorch3D binary and method settings. Tested Python is 3.10.12, PyTorch 2.0.1+cu118 and PyTorch3D 0.7.4. The script installs the author-recommended Linux binary with a SHA-256 check into this project's semantic environment, without requiring a system CUDA toolkit. Setup was executed, not merely drafted.

## 2. Data and poses

The [author instructions](https://github.com/concept-graphs/concept-graphs) use the [NICE-SLAM rendered Replica trajectory](https://github.com/cvg/nice-slam/blob/master/scripts/download_replica.sh). The public ZIP is 12,442,855,671 bytes. HTTP ranges fetch only source frames `000000, 000005, …, 000195`, their depth images and `traj.txt`; whole-archive SHA-256 is not claimed. ZIP CRC validates fetched members, and the saved [manifest](../results/reference/conceptgraphs-wsl/dataset-manifest.json) binds extracted-file SHA-256 values, archive length and ETag.

The 40 corresponding original pose matrices are placed in matching compact order. The author loader runs with stride 1 on this subset, equivalent to selecting stride 5 from the first 200 source entries. Mapping uses the original 480×640 image setting with rescaled intrinsics and supplied world poses. This is a short rendered static scene, not a real robot deployment or full Replica paper evaluation.

Each run receives an isolated copy of the RGB-D subset and author code. It cannot reuse old detections or a previous object map as a new result. Model weights and RGB-D data are excluded from Git.

## 3. Compatibility and resource adaptations

The [complete patch](../results/reference/conceptgraphs-wsl/compatibility.patch) records headless Matplotlib, skipping unused GroundingDINO/RAM imports and initialization for `class_set=none`, local checkpoint selection, and SAM point batching. Geometry, association equations and decision thresholds are not patched.

The author default batches all 144 sampled SAM prompts at once. On this 12 GiB GPU, the first frame saturated memory and stalled; that run was deliberately interrupted and retained as [an interrupted run](../results/reference/conceptgraphs-wsl-batch144-interrupted/record.json). The completed run keeps the 12×12 sampling grid and processes batches of 36. Batch partitioning is an explicit resource adaptation; identical masks to an unadapted reference are not claimed. Segmentation completed all 40 inputs before the mapping stage.

SAM ViT-H comes from a revision-pinned Hugging Face mirror after the Meta download stalled; CLIP ViT-H comes from the LAION model repository. Both full file hashes are checked before model loading. The mirror source and revisions are explicit in the configuration. Full-system timing or peak-memory claims are not made from the parent process.

## 4. What the baseline tells us

The original mapping log contains object additions, filtering and merging; these operations execute on real RGB-D observations and foundation-model features rather than oracle object identities. The final object count alone cannot measure fragmentation or correct association. The published query scores are cosine similarity, not calibrated probabilities.

The paired extension adds four partial-surface targets, fixed-feature pose-error pairs and threshold controls. Full identity ground truth, dynamic-semantic recall and matched coverage/latency remain open. [Results and limitations](PAIRED_RESULTS.md). H1 remains a candidate; held-out confirmation has not started.

## 5. HOV-SG: fourth mapping core

`bash scripts/setup_hovsg.sh` prepares independent `.venv-hovsg`; then run `.venv-hovsg/bin/python scripts/run_hovsg.py`. It shares verified Replica data/checkpoints, installs [pinned HOV-SG dependencies](../environments/hovsg/requirements.txt), and needs no PyTorch3D.

The original installed-distribution snapshot included an HF Hub 2.x / OpenAI 1.3.7 dependency conflict. The install recipe resolves this with HF Hub 0.23.5 for local-checkpoint loading, removes the unused incompatible httpx2 distribution, and runs `uv pip check`. Original run environments remain recorded unchanged.

The completed run processes 8 observations at source indices 0,25,...175, giving 50 segments and 166,777 reference points. RGB/depth are 640×360 with separately rescaled intrinsic axes; SAM batch is 36 and CLIP batch 4. Native geometric merging and feature selection execute with unchanged thresholds. Floor/room hierarchy, semantic mIoU and navigation are not evaluated. Fifty segments cannot rank against 39 objects.

The first 40-observation attempt completed extraction, then its merge worker was killed with exit 137; the cause is not established and OOM is not confirmed. [Failed evidence](../results/reference/hovsg-wsl-interrupted/record.json) and [successful evidence](../results/reference/hovsg-wsl/record.json) are separate. The successful mapper records peak PyTorch allocation of 10,030,088,704 bytes, excluding driver allocations. Four text queries return candidate coordinates without correctness evaluation. [Card/video/PDF](papers/hovsg.md).

The actual ConceptGraphs batch mapper reads absolute `dataset.poses`, bypassing the loader default normalization. Thirty-nine saved camera matrices match supplied poses; historical world coordinates are correct, without an extra first-frame transformation. Both semantic clips replay final maps, not online evolution. [Recording and coordinate audit](RECORDING.md).

The corrected install was executed again with a compatible 142-package environment. A fresh [resolved-environment repeat](../results/reference/hovsg-wsl-resolved/record.json) completes all 8 observations and reproduces 50 segments/166,777 points; its map PLY and segment-feature NPY are byte-identical to the earlier core run. This local repeat does not establish determinism on other hardware or settings.
