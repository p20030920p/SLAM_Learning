# Sources, credits and asset scope

English | [中文](ATTRIBUTION.zh-CN.md)

The repository's [MIT license](../LICENSE) covers its own study code. Upstream implementations, data, weights and derived observations retain their original terms; the root license does not replace them. [CITATION.cff](../CITATION.cff) identifies the repository maintainers; the original papers remain the sources of the reproduced methods.

| Source | Inspected license / provenance |
| --- | --- |
| DUFOMap; DynamicMap Benchmark | BSD 3-Clause in their pinned source snapshots; authors and exact commits are in [upstreams.json](../configs/upstreams.json) |
| ConceptGraphs | [MIT](https://github.com/concept-graphs/concept-graphs/blob/main/LICENSE); pinned commit in [semantic.json](../configs/semantic.json) |
| HOV-SG | [MIT](https://github.com/hovsg/HOV-SG/blob/main/LICENSE); pinned commit in [hovsg.json](../configs/hovsg.json) |
| BeautyMap | No standalone license file in the inspected source root; [author source](https://github.com/MKJia/BeautyMap) is fetched into the private cache, with patch/provenance disclosed |
| KITTI-00 teaser | [DynamicMap release](https://zenodo.org/records/10886629); full archive hash in the dataset specification; raw scans are not committed |
| Replica room0 renders | [NICE-SLAM source](https://github.com/cvg/nice-slam/blob/master/scripts/download_replica.sh), based on [Replica](https://github.com/facebookresearch/Replica-Dataset); extracted member hashes retained |
| SAM and CLIP weights | Exact source revisions and full hashes in [semantic.json](../configs/semantic.json); checkpoints are not committed |
| Recording presentation | Sim2Real-AlgoBench conventions credited in [RECORDING](RECORDING.md); no source copied |

Replica's [research terms](https://github.com/facebookresearch/Replica-Dataset/blob/main/LICENSE) limit dataset use/publication to noncommercial or nonprofit research/education and specify access conditions. The semantic GIF/MP4/posters contain derived Replica observations for this research study; they are not offered as newly MIT-licensed datasets. Download data/checkpoints from their original documented sources under their terms.

PDFs embed a subset of the licensed local Chinese font; font files are not distributed separately. AI involvement and the applicant's review responsibilities are stated in [AI disclosure](DISCLOSURE.md). Each figure links to measured run evidence, or is explicitly reserved for an unexecuted experiment.

Annotation polygons and query-audit figures in the paired extension derive from the same Replica renders under the terms above. They are AI-assisted study labels, not official or independently reviewed ground truth.
