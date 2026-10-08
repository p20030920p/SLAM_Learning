# 作者原始方法复现

本分支 `reproduce/author-originals` 从空白历史建立，单独运行 DUFOMap、BeautyMap、ConceptGraphs 和 HOV-SG 的作者仓库。原库以固定提交的 Git 子模块保存；实际执行和大文件在这台电脑的 WSL 独立目录。主分支的展示与简化实验不作为这里的复现结果。

**状态：原始 LiDAR 流程与作者评价已完成公开 00 样例；语义方法仍在推进。尚未完成四篇论文的全部实验。**

[English](README.md) · [运行与结果](docs/STATUS.zh-CN.md) · [Windows 起步和命令](docs/RUNBOOK.zh-CN.md) · [原库和复现范围](docs/SCOPE.zh-CN.md) · [执行证据](evidence/README.md)

| 方法 | 作者原库 | 本分支固定提交 |
|---|---|---|
| DUFOMap | [KTH-RPL/dufomap](https://github.com/KTH-RPL/dufomap) | `9e239ddd` |
| BeautyMap | [MKJia/BeautyMap](https://github.com/MKJia/BeautyMap) | `98bce4a9` |
| ConceptGraphs | [concept-graphs/concept-graphs](https://github.com/concept-graphs/concept-graphs) | `93277a02` |
| HOV-SG | [hovsg/HOV-SG](https://github.com/hovsg/HOV-SG) | `d6e65a53` |
| 动态点云评价 | [KTH-RPL/DynamicMap_Benchmark](https://github.com/KTH-RPL/DynamicMap_Benchmark) | `8b60f36a` |

作者源码保持原样。依赖、编译器、数据路径或 API 模型的变化必须单独记录。DeepSeek 只属于替代模型实验，不能算原论文 GPT-4 的复现；本轮费用上限为 1 美元，密钥和大文件不提交 Git。
