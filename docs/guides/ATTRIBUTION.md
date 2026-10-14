# Sources, credits and asset scope

English | [中文](ATTRIBUTION.zh-CN.md)

The repository's [MIT license](../../src/LICENSE) covers its own study code. Upstream implementations, data, weights and derived observations retain their original terms; the repository license does not replace them. [CITATION.cff](../CITATION.cff) identifies the repository maintainers; the original papers remain the sources of the reproduced methods.

| Source | Inspected license / provenance |
| --- | --- |
| DUFOMap; DynamicMap Benchmark | BSD 3-Clause in their pinned source snapshots; authors and exact commits are in [upstreams.json](../../src/configs/upstreams.json) |
| BeautyMap | No standalone license file in the inspected source root; [author source](https://github.com/MKJia/BeautyMap) is fetched into the private cache, with patch/provenance disclosed |
| AdaM_MCL (DSOM, AdaM MCL) | MIT in the pinned snapshot [Runjian-Chen/AdaM_MCL](https://github.com/Runjian-Chen/AdaM_MCL/tree/e8aedd2bae03816aabd5300e5ca2fe181b39d830) at commit `e8aedd2bae`; the authors' `Dataset/` and `Trained_models/` ship empty and are not redistributed |
| KITTI-00 teaser | [DynamicMap release](https://zenodo.org/records/10886629); full archive hash in the dataset specification; raw scans are not committed |
| IR-MCL | No license file in the repository; the pinned [author source](https://github.com/PRBonn/ir-mcl/tree/aab8c91b37e59f94442d8eddfa2f920ab1ecc4c5) and its pre-trained weights are used for research reproduction only. Files borrowed from range-mcl carry MIT headers naming their authors |
| Recording presentation | Sim2Real-AlgoBench conventions credited in [RECORDING](RECORDING.md); no source copied |
| Robot test model | [Sim2Real-AlgoBench](https://github.com/p20030920p/Sim2Real-AlgoBench/tree/53324d40def0dd753b4a99021b8fe596955a1ecd), inspected MIT source. The additive 3D sensor URDF retains its native model elements and [license](../../config/robot_profiles/omni-3d-v1/LICENSE); source/asset hashes are in [robot-model.json](../testing/robot-model.json). |
