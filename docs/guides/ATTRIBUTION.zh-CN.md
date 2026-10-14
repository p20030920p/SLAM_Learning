# 来源、署名及资产范围

[English](ATTRIBUTION.md) | 中文

仓库 [MIT 许可](../../src/LICENSE)覆盖本库研究代码。上游实现、数据、权重及派生观测保留其原有条款，本库许可不替代它们。[CITATION.cff](../CITATION.cff)记录仓库维护者；复现方法的来源仍是原论文。

| 来源 | 检查的许可／来源 |
| --- | --- |
| DUFOMap、DynamicMap Benchmark | 固定源码快照中的 BSD 3-Clause；作者及提交见 [upstreams.json](../../src/configs/upstreams.json) |
| BeautyMap | 检查的源码根目录无独立许可文件；[作者源码](https://github.com/MKJia/BeautyMap)下载至私有缓存，披露补丁及来源 |
| AdaM_MCL（DSOM、AdaM MCL） | 固定快照 [Runjian-Chen/AdaM_MCL](https://github.com/Runjian-Chen/AdaM_MCL/tree/e8aedd2bae03816aabd5300e5ca2fe181b39d830) 提交 `e8aedd2bae` 为 MIT；作者 `Dataset/` 与 `Trained_models/` 上游为空目录，未再分发 |
| KITTI-00 teaser | [DynamicMap 发布](https://zenodo.org/records/10886629)；数据配置固定完整归档哈希，不提交原始扫描 |
| IR-MCL | 仓库无许可文件；固定快照 [作者源库](https://github.com/PRBonn/ir-mcl/tree/aab8c91b37e59f94442d8eddfa2f920ab1ecc4c5) 及其预训练权重仅用于研究复现。取自 range-mcl 的文件头部标注 MIT 并署名作者 |
| 录制呈现 | [RECORDING](RECORDING.zh-CN.md)标明 Sim2Real-AlgoBench 约定来源，未复制其源码 |
| 机器人模型扩展 | [Sim2Real-AlgoBench](https://github.com/p20030920p/Sim2Real-AlgoBench) 的 MIT 机器人 URDF 与桥接配置；保留[上游许可](../../config/robot_profiles/omni-3d-v1/LICENSE)，固定来源与资产哈希见[模型检查](../testing/robot-model.json) |

PDF 嵌入本机许可中文字体的子集，不单独分发字体文件。[AI 披露](DISCLOSURE.zh-CN.md)披露 AI 参与及申请人需要亲自核查的内容。每张图都链接实测运行，或明确标记为未执行实验的预留。
