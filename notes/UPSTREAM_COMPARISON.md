# Author repositories versus this reproduction repository

English | [中文](UPSTREAM_COMPARISON.zh-CN.md) | [Index](README.md)

This compares the earlier execution layer and subsets. New independent pins, full public data and status are in the [author-originals branch](https://github.com/p20030920p/SLAM_Learning/tree/reproduce/author-originals); see [the added analysis](AUTHOR_RESULTS_ANALYSIS.md).

This repository runs, adapts, evaluates and records **author cores**. It does not reimplement all four algorithms or reproduce every paper experiment. Compare pinned snapshots and actual per-run copies; current author default branches may differ.

## Original repositories and pins

| Original | Pinned source | Record |
| --- | --- | --- |
| [DUFOMap](https://github.com/KTH-RPL/dufomap) | [9e239ddd](https://github.com/KTH-RPL/dufomap/tree/9e239ddd5995136e14f5212f33382a6ebc59e518) | [upstreams.json](../configs/upstreams.json). **Execution uses authors' PyPI `dufomap==1.1.1`, not a claimed build from this Git commit** |
| [BeautyMap](https://github.com/MKJia/BeautyMap) | [98bce4a9](https://github.com/MKJia/BeautyMap/tree/98bce4a97db96ddd0d5342e31425c7679f58ba2e) | [upstreams.json](../configs/upstreams.json) |
| [ConceptGraphs](https://github.com/concept-graphs/concept-graphs) | [93277a02](https://github.com/concept-graphs/concept-graphs/tree/93277a02bd89171f8121e84203121cf7af9ebb5d) | [semantic.json](../configs/semantic.json) |
| [HOV-SG](https://github.com/hovsg/HOV-SG) | [d6e65a53](https://github.com/hovsg/HOV-SG/tree/d6e65a53c8be6faec3f01f00d1644d967f89e605) | [hovsg.json](../configs/hovsg.json) |
| [DynamicMap_Benchmark](https://github.com/KTH-RPL/DynamicMap_Benchmark) | [8b60f36a](https://github.com/KTH-RPL/DynamicMap_Benchmark/tree/8b60f36a735a910b8c54b7eb12438db76fb32460) | Author PCL evaluator cross-checked pointwise against SciPy |
| [gradslam](https://github.com/gradslam/gradslam) | [59ca872e](https://github.com/gradslam/gradslam/tree/59ca872e3d265ad09f63c4793d011fad67064452) | ConceptGraphs dependency; supplied-pose mapping is not a trajectory-estimation run |

SAM/CLIP repositories, revisions and weight hashes are also fixed in `semantic.json`. CPU, ConceptGraphs and HOV-SG use separate environments.

## Native entry points and adaptations

| Core | Author entry | This repository and adaptations |
| --- | --- | --- |
| DUFOMap | [main.py](https://github.com/KTH-RPL/dufomap/blob/9e239ddd5995136e14f5212f33382a6ebc59e518/main.py), Python binding | [adapters.py](../src/slam_learning/adapters.py) calls `run`, `oncePropagateCluster`, `outputMap`; native binding unchanged. World PCD/VIEWPOINT, 0.2–50 m integration range and isolated outputs. `resolution=0.1,d_s=0.2,d_p=1,threads=2`; paper `d_p=1` differs from author demo `d_p=2` |
| BeautyMap | [main.py](https://github.com/MKJia/BeautyMap/blob/98bce4a97db96ddd0d5342e31425c7679f58ba2e/main.py), `lib/bee_tree.py` | [adapters.py](../src/slam_learning/adapters.py) invokes a per-run author copy. Python `map`→list and explicit `np.int64` fix compatibility/Windows overflow. GT intensity is physically stripped from scans and raw map; XYZ/VIEWPOINT retained. Parameters `40,1,0.5` |
| ConceptGraphs | [generate_gsa_results.py](https://github.com/concept-graphs/concept-graphs/blob/93277a02bd89171f8121e84203121cf7af9ebb5d/conceptgraph/scripts/generate_gsa_results.py), [cfslam_pipeline_batch.py](https://github.com/concept-graphs/concept-graphs/blob/93277a02bd89171f8121e84203121cf7af9ebb5d/conceptgraph/slam/cfslam_pipeline_batch.py) | [run_conceptgraphs.py](../scripts/run_conceptgraphs.py) runs class-agnostic SAM/CLIP and native association/fusion. Agg backend, unused DINO/RAM initialization skipped, pinned local CLIP weights, SAM batch144→36 with the same 12×12 prompt grid. Mask equality to batch144 is unproven. Baseline association threshold1.2; 1.0/1.4 are separate controls |
| HOV-SG | [semantic_segmentation.py](https://github.com/hovsg/HOV-SG/blob/d6e65a53c8be6faec3f01f00d1644d967f89e605/application/semantic_segmentation.py), [graph.py](https://github.com/hovsg/HOV-SG/blob/d6e65a53c8be6faec3f01f00d1644d967f89e605/hovsg/graph/graph.py) | [run_hovsg.py](../scripts/run_hovsg.py) constructs native `Graph` and calls `create_feature_map()`. Images/depth 640×360, intrinsics scaled separately in x/y; SAM batch36, CLIP batch4, staged40 observations with skip5→eight. Native segmentation/merging thresholds retained |

ConceptGraphs has detector-free and detector-based paths; only `class_set=none` ran. HOV-SG's `application/create_graph.py` is the fuller hierarchy path, not executed here. [Pinned ConceptGraphs README](https://github.com/concept-graphs/concept-graphs/blob/93277a02bd89171f8121e84203121cf7af9ebb5d/README.md), [pinned HOV-SG README](https://github.com/hovsg/HOV-SG/blob/d6e65a53c8be6faec3f01f00d1644d967f89e605/README.md).

Author command forms, for comparison with actual run `commands`, are below. Each belongs in its own author checkout with README-prepared data/weights, not this repository root.

| Author workflow | Entry form | Wrapper difference |
| --- | --- | --- |
| DUFOMap | `python main.py --data_dir data/00`, or C++ `dufomap_run` | Pin binding/parameters and isolate recording, output and evaluation |
| BeautyMap | `python main.py --data_dir data/00 --dis_range 40 --xy_resolution 1 --h_res 0.5` | Isolate patches, strip GT fields and record inputs/results |
| ConceptGraphs | `python scripts/generate_gsa_results.py ... --class_set none --stride 5`, then `python slam/cfslam_pipeline_batch.py ... stride=5` | Author commands run from `conceptgraph/`. We stage40 observations at source stride5 first, then use internal stride1 to avoid sampling twice |
| HOV-SG | `python application/semantic_segmentation.py main.dataset=replica main.dataset_path=Replica/office0 main.save_path=data/sem_seg/office0` | Directly call the same `Graph.create_feature_map()` core on the adapted room0 subset; official semantic scoring remains unrun |

Patches: [BeautyMap](../results/reference/beautymap-wsl/compatibility.patch), [ConceptGraphs](../results/reference/conceptgraphs-wsl/compatibility.patch), [HOV-SG](../results/reference/hovsg-wsl/compatibility.patch). BeautyMap's file is a replacement/count summary, not a directly applicable unified diff. Author caches remain clean; compare actual runtime files for exact differences.

## Reproduction coverage and result gaps

| Method | Executed coverage | Gap to the complete paper |
| --- | --- | --- |
| DUFOMap | Full public KITTI00 **teaser**, 141 scans/17,362,230 labeled points. SA/DA/AA: 97.979798/98.702895/98.340682%, paper97.96/98.72/98.34% | Not the full original KITTI driving sequence; not every metric meets 0.01 percentage-point tolerance; no trajectory or full multi-dataset efficiency evaluation |
| BeautyMap | Same teaser. SA/DA/HA: 96.952945/98.338247/97.640683%, paper96.76/98.38/97.56% | Paper-era differences unexplained; no full multi-scene evaluation |
| ConceptGraphs | room0 source0,5,…195:40 supplied-pose observations,39 objects | No full Replica semantic benchmark, detector-based path, LLM relation graph or navigation |
| HOV-SG | Source0,25,…175:eight observations,50 segments,166,777 points | Forty-observation attempt exited137 for an unconfirmed reason. No complete floor/room hierarchy, semantic benchmark, navigation or online update |

At the 5 cm map-neighbor threshold, native PCL and SciPy agree pointwise on saved maps. This rules out that evaluator difference on those maps, not all paper-era differences. DUFOMap AA is geometric; BeautyMap HA harmonic. Object/segment counts are not semantic accuracy.

Our partial-surface annotations, restricted queries, pose perturbations, provenance and RViz review are additional diagnostics, not official paper benchmarks or an implemented H1. [Results](../docs/RESULTS.md), [semantic boundaries](../docs/SEMANTIC.md), [research connection](../docs/STUDY.md).

## Inspect on this machine

**PowerShell:**

```powershell
explorer.exe '\\wsl.localhost\Ubuntu-22.04\home\qzl\projects\SLAM_Learning\.cache\upstream'
wsl -d Ubuntu-22.04 -u qzl
```

**WSL Bash:**

```bash
cd /home/qzl/projects/SLAM_Learning
git -C .cache/upstream/conceptgraphs rev-parse HEAD
git -C .cache/upstream/conceptgraphs status --short
less .cache/upstream/conceptgraphs/README.md
```

Press `q` to leave `less`. Substitute `beautymap`, `dufomap` or `hovsg` for other author caches. Do not edit pinned caches; runners check their commit/clean state.

Compare the existing ConceptGraphs baseline:

```bash
cat results/runs/conceptgraphs-7795d7b47007/compatibility.patch
diff -u .cache/upstream/conceptgraphs/conceptgraph/scripts/generate_gsa_results.py \
  results/runs/conceptgraphs-7795d7b47007/author-code/conceptgraph/scripts/generate_gsa_results.py
cat results/runs/conceptgraphs-7795d7b47007/record.json
```

`diff` exit1 means differences, exit2 an error. The record's `commands` provides the exact invocation. For BeautyMap compare `utils/pcdpy3.py`, `main.py`, `lib/bee_tree.py`; for HOV compare `hovsg/utils/clip_utils.py` and read `effective-config.yaml`, `derived-input.json`, `frame_observations.json`.

Use the [Windows guide](WINDOWS_START.md) for executable wrappers. A separate unmodified-author experiment needs its own environment, complete inputs and weights; copying README placeholders is not reproducing the recorded run.
