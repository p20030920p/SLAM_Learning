# 来源、署名及资产范围

[English](ATTRIBUTION.md) | 中文

仓库 [MIT 许可](../LICENSE)覆盖本库研究代码。上游实现、数据、权重及派生观测保留其原有条款，根许可不替代它们。[CITATION.cff](../CITATION.cff)记录仓库维护者；复现方法的来源仍是原论文。

| 来源 | 检查的许可／来源 |
| --- | --- |
| DUFOMap、DynamicMap Benchmark | 固定源码快照中的 BSD 3-Clause；作者及提交见 [upstreams.json](../configs/upstreams.json) |
| ConceptGraphs | [MIT](https://github.com/concept-graphs/concept-graphs/blob/main/LICENSE)；固定版本见 [semantic.json](../configs/semantic.json) |
| HOV-SG | [MIT](https://github.com/hovsg/HOV-SG/blob/main/LICENSE)；固定版本见 [hovsg.json](../configs/hovsg.json) |
| BeautyMap | 检查的源码根目录无独立许可文件；[作者源码](https://github.com/MKJia/BeautyMap)下载至私有缓存，披露补丁及来源 |
| KITTI-00 teaser | [DynamicMap 发布](https://zenodo.org/records/10886629)；数据配置固定完整归档哈希，不提交原始扫描 |
| Replica room0 渲染 | 基于 [Replica](https://github.com/facebookresearch/Replica-Dataset) 的 [NICE-SLAM 数据](https://github.com/cvg/nice-slam/blob/master/scripts/download_replica.sh)，保存解压成员哈希 |
| SAM／CLIP 权重 | [semantic.json](../configs/semantic.json)固定来源版本及完整哈希，不提交权重 |
| 录制呈现 | [RECORDING](RECORDING.zh-CN.md)标明 Sim2Real-AlgoBench 约定来源，未复制其源码 |

Replica 的[研究条款](https://github.com/facebookresearch/Replica-Dataset/blob/main/LICENSE)限定非商业或非营利研究／教育的数据使用及发布，并规定访问条件。语义 GIF／MP4／封面包含为本研究生成的 Replica 派生观测，不作为重新 MIT 授权的数据集。数据／权重依据其条款从原文档来源下载。

PDF 嵌入本机许可中文字体的子集，不单独分发字体文件。[INTERVIEW](INTERVIEW.zh-CN.md)披露 AI 参与及申请人需要亲自核查的内容。每张图都链接实测运行，或明确标记为未执行实验的预留。
