# Paired pose exploration: protocol before execution

[English](PAIRED_PROTOCOL.md) | [中文](PAIRED_PROTOCOL.zh-CN.md)

This is an exploratory extension on already inspected KITTI teaser and Replica room0, not a held-out confirmation. H1 remains a candidate. The protocol, annotation coordinates and code are committed before collecting paired results. Failed attempts are retained rather than silently overwritten.

## Frozen factors

`configs/paired_pose.json` specifies 141 LiDAR scans and eight RGB-D observations at original indexes 0,25,...175. All four author cores get a zero-error control and 18 perturbations: translation RMS 3/10/30 cm, three seeds, two temporal orders. There are 76 primary cells. Only world-x translation changes; rotation is not tested.

The first pose is fixed. Normal samples for later poses are centred and rescaled to the requested RMS over all frames. The correlated version sorts the same scalar samples in time. Every pair therefore has identical mean, RMS, extrema and marginal histogram. We report measured lag-one correlation. This is deliberate monotone-drift stress, including an initial jump; it is not a realistic stochastic deployment model. The shuffled samples are conditioned by centring and RMS normalization, so strict iid independence is not claimed.

Raw RGB/depth, masks, CLIP features, calibration and native mapping settings remain fixed within each method. The two semantic methods use the same eight source indexes with their previously disclosed native resolution adaptations. ConceptGraphs uses its original batch mapper from frozen detections. HOV-SG reconstitutes native pixel features from saved F_p using the same CUDA accumulation/normalization/cast, then calls the original `Graph.create_feature_map()`. Zero-error `map.ply` and `segment_features.npy` must match the previous native HOV run byte for byte before interpreting perturbations.

## Objects and targets

`annotations/room0/targets.json` contains four visually labelled instances/parts: cabinet, lamp shade and two ottomans, using raw source frames 0 and 150. These are AI-assisted polygons inspected by Codex, not human-reviewed labels or official Replica semantic ground truth. Annotation overlays are reviewable. No model mask is used as ground truth, and annotations never enter a mapper.

Provided rendered depth and camera-to-world poses backproject visible surface samples. A two-canvas-pixel boundary band is removed to reduce mixed-depth pixels. These are partial visible surfaces, not complete 3D objects or exact object centres. Each target has an independent visible-surface anchor.

For each map, report best 10 cm reference-surface coverage, the number of qualifying fragments, top-1 query hit and anchor-to-selected-segment distance. A segment qualifies at coverage >=20% and projected visible precision >=50% in the annotated source image; depth visibility uses a 10 cm tolerance. An `ottoman` category query can return either labelled instance. The scores are annotation-dependent diagnostics, not paper mIoU, navigation success or calibrated probabilities. A map-wide segment cannot qualify merely by covering an anchor.

## LiDAR evaluation

Translate both world XYZ and sensor origin, preserving original point identities and original dynamic/static labels outside the algorithm. Raw map and scan files passed to author code contain only XYZ and VIEWPOINT. Evaluate cleaned-map membership at each point's **own perturbed coordinates**, using a fixed 5 cm nearest-neighbour rule; do not score shifted maps against unshifted GT. This isolates decisions from a trivial global-coordinate penalty, although the correspondence rule can still affect scores. Also report DUFOMap's direct per-point segment labels to expose that measurement effect.

## Decision and limits

Report every seed and paired difference, alongside zero-error controls; seed repetition on one scene is not independent-scene replication. A correlation effect may improve, worsen or leave results unchanged. Opposite effects across methods weaken a universal-bottleneck claim. Static Replica scenes cannot measure semantic motion/change recall, and offline final maps cannot measure update latency or recoverability after delayed correction. These results can motivate or narrow H1 but cannot establish its matched-recall/coverage/delay benefit.

Next evidence gates are independently reviewed annotations, additional rooms/real captures, actual dynamic events and a frozen comparison against simple tolerance/visibility/pose-correction baselines. No candidate method is declared validated from these perturbations.

Implementation amendment: the CLI threshold parser was changed from `float` to JSON numeric parsing before the parameter-control runs, because the DUFOMap binding requires an integer `d_p`. Primary cells do not override thresholds. The original implementation snapshot and each cell's actual script hash are retained; final aggregation verifies completed cells without rerunning or overwriting them. Follow-up controls were declared after seeing initial DUFOMap results and are explicitly exploratory.
