# Scope and completion criteria

English | [中文](SCOPE.zh-CN.md)

A saved point cloud establishes one stage, not reproduction of every paper experiment.

## 1. Four methods

| Method | Executed | Still missing |
| --- | --- | --- |
| DUFOMap | Original C++, four labelled releases; Table IV matched; unlabelled campus/twofloor; selected KITTI intervals | Online DUFOMap⋆, pose-source and speed comparisons; unresolved input versions |
| BeautyMap | Four releases; current/historical KITTI; historical Table III matched | Table IV module ablations, runtime, remaining parameter/input checks |
| ConceptGraphs | 400-frame SAM-only on three scenes and Detect on two, original scoring and matrix audits | Remaining scenes, LLaVA, original GPT-4, planning |
| HOV-SG | 20-frame feature map and original semantic scoring | Default 200-frame run, full Replica/ScanNet, HM3D hierarchy and navigation |

The selected KITTI intervals are the paper inputs; full sequences are not required for those tables. Current preprocessing, historical reconstruction and released data remain distinct. No public module switches were found for BeautyMap Table IV in the pinned snapshot; do not modify the algorithm and label it the original ablation.

## 2. Semantic protocols

| Item | ConceptGraphs | HOV-SG |
| --- | --- | --- |
| GT | Author HDF5 and Semantic-NeRF trajectory | Original Replica mesh vertices and class JSON |
| Vocabulary | Scene-present GT classes, one prompt per class | Scene semantic JSON and text templates |
| Support | Object predictions transferred by 1NN to RGB PointFusion | 5NN voting at GT mesh vertices |
| Exclusions | `n_exclude=6`: other/floor/wall/ceiling/door/window | -1/0 plus excluded structural/background names |

Native scores check each author's workflow; they cannot rank the methods directly. A common-protocol comparison is a separate experiment. Replica feature mapping also does not reproduce HM3D multi-floor hierarchy: the original entry skips hierarchy on Replica/ScanNet.

## 3. Sources and boundaries

[Pinned upstreams](../../src/configs/upstreams.json) · [Data access](../guides/DATA_ACCESS.md) · [Author status](STATUS.md) · [Original source links and evaluator references](SCOPE.zh-CN.md).

DeepSeek is a separately disclosed replacement-model experiment, not original GPT-4 reproduction. Robot success requires the actual robot stack and evaluation; a screen demonstration cannot replace it.
