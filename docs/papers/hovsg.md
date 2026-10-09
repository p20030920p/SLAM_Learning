# HOV-SG — not reproduced

English | [中文](hovsg.zh-CN.md) | [Historical subset PDF](../pdf/hovsg.en.pdf)

**Delivery status: not reproduced.** No completed default 200-frame run or complete paper benchmark is available. Floor/room hierarchy and navigation are also not reproduced. HOV-SG is excluded from the homepage's completed reproduction showcase.

- **Completed limited attempts:** an 8-observation segment map and a separate 20-frame resource variant with original semantic scoring. These do not reproduce the default paper experiment.
- **Incomplete attempts:** the 40-observation merge exited with code 137; the default 200-frame run did not produce a completed result. A killed process alone does not establish its cause.
- **Unverified outputs:** text-query candidates are not independently annotated; saved segments are not proof of correct physical object identities or navigation success.
- **Retained evidence:** [8-frame run](../../results/reference/hovsg-wsl/record.json), [40-frame failure](../../results/reference/hovsg-wsl-interrupted/record.json), and [20-frame diagnostic/scoring scope](https://github.com/p20030920p/SLAM_Learning/blob/535a2780af7ca7eb3aa02f722e1340fe90bc2dcf/docs/HOVSG_HOME_RESULTS.md). Historical media/PDF bytes remain available for traceability, not as a completed-reproduction claim.

## Method and execution

[HOV-SG (RSS 2024)](https://arxiv.org/html/2403.17846v2) lifts SAM segments and CLIP features to reference geometry, merges observations, selects robust features, and constructs a floor/room/object hierarchy. This run calls the author Graph.create_feature_map(), including native geometric merging and feature selection, at source commit d6e65a53c8be6faec3f01f00d1644d967f89e605.

```bash
bash src/scripts/setup/setup_hovsg.sh
.venv-hovsg/bin/python src/scripts/methods/run_hovsg.py
```

The separate environment shares verified checkpoints and the 40-observation Replica subset with ConceptGraphs. Source indices 0,25,...175 are processed by skip_frames=5. RGB/depth are resized to 640×360; both intrinsic axes are rescaled from the pinned original 1200×680 calibration. SAM batch 36 and CLIP batch 4 are resource adaptations. Native segmentation/merging thresholds remain fixed; identical original-resolution masks are not claimed.

## Retained 8-frame output and failure

| Item | Observed result |
| --- | --- |
| Processed posed observations | 8 |
| Final segments | 50; not necessarily 50 physical objects |
| Reference points | 166,777 |
| Queries | 4 texts × 3 candidates; correctness unannotated |
| Peak PyTorch allocation in mapper | 10,030,088,704 bytes; excludes driver allocations |

The first 40-observation attempt completed frontend extraction, then the hierarchical merge worker was killed with exit 137. Its record, log and intermediate hashes remain [published](../../results/reference/hovsg-wsl-interrupted/record.json). The cause is not established; no map score or confirmed OOM claim is attached to that attempt. The completed reduced subset is a different run, not a replacement result hidden under the original record.

The 50 segments cannot be ranked against ConceptGraphs' 39 objects: observation count, image settings and association/merging definitions differ. Cosine scores are not calibrated probabilities. No semantic mIoU or complete graph/navigation metric is reported.

## Limitation and research relevance

The paper explicitly identifies static-scene, processing-time and parameter limitations (V), and assumes accurate odometry for projection (III-A). A persistent static feature map lacks a moved target's temporal validity. A geometric error can assign a pixel's semantic evidence to the wrong reference point before a language query occurs.

Our open question is how to retain enough observation provenance to reconsider semantic assignments after a pose correction, without unlimited storage or delaying every query. A shared-pose/provisional-update sidecar is feasible for segments; extending it to full floor/room hierarchy is additional work. Test static/moved/removed/occluded cases and compare threshold and visibility controls at matched query coverage, recall and delay. [Common bottleneck and counterexamples](../research/STUDY.md).

## Video interpretation

All eight native SAM observations are replayed beside the final world-XZ segment map. A red segment is a query candidate, not verified ground truth. The supplied absolute camera-to-world matrices determine coordinates. This is measured final-map replay, not live navigation, incremental hierarchy growth or a runtime benchmark.
