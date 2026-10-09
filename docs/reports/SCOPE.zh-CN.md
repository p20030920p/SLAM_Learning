# 原库对照与完成标准

[English](SCOPE.md) | 中文

这里的“完整”以作者公开的阶段、数据和评价为准。跑出一个点云或截图不代表论文全部实验复现。

| 方法 | 作者公开链路 | 本轮覆盖 | 完整复现仍需 |
| --- | --- | --- | --- |
| DUFOMap | 读取带位姿点云 → 动态清理 → 点云输出 → DynamicMap 评价 | 四份公开标注数据完成原始 C++ 与作者评价；论文表 IV 五组 SA/DA/AA 匹配两位小数；两份无标注 campus/twofloor 全部 3323 帧运行成功；新增当前预处理的 01/02 原始方法和评分 | 新 01 与论文的数据/位姿版本核对；在线 DUFOMap⋆、性能、位姿来源对照及其余定性数据 |
| BeautyMap | 先验全局地图 + 位姿/扫描 → 二进制地面矩阵 → 清理 → 同一评价 | 四份公开数据共 1997 帧；AV2 为补充迁移；当前与历史预处理 01/02 均完成；历史 02 的 XY=0.5/1/2m 三组 SA/DA/HA 共 9 项匹配论文两位小数 | 01 数据/位姿版本、未报告参数核对；表 IV 模块消融、运行时间对照；先验与稀疏性实验属于额外分析 |
| ConceptGraphs | RGB-D/位姿 → SAM 或 RAM+DINO+SAM → CLIP → 对象关联/融合 → LLaVA 描述 → GPT-4 精炼/关系 → 语义/规划评价 | SAM-only 的 room0/office0/office1，以及 Detect 的 room0/office0，均完成 400 帧链路与原评分；矩阵复算通过；真实窗口实录 | SAM-only 余 5 场景、Detect 余 6 场景及原八场景评价；LLaVA 基础权重、原始 GPT-4、规划任务 |
| HOV-SG | RGB-D/位姿 → SAM+CLIP → 融合语义地图 → 楼层/房间/对象图 → 查询/导航/评价 | 默认采样 200 帧融合超时，无最终图；另取 20 帧完成 156 分段、399,663 点及原评分：mIoU 34.7500%、F-mIoU 62.8725% | 默认采样完成、完整 Replica/ScanNet 语义评价；8 个 HM3DSem 场景及完整层级评价；导航 |

“论文完整复现”须按论文实际使用的选定帧段核对，不能把整条 KITTI 序列当成这些表格的完成条件。DUFOMap 定量表包含 00、01、AV2、半室内；BeautyMap 的表格及消融还涉及 01/02。

作者 Zenodo 发布包不含 01/02。本轮已从 KITTI 官方 S3 下载 00/01/02 所需的 333 帧，核对原始 ZIP CRC、SHA-256 与对应标签点数，标签/SuMa 位姿及标定归档也已完整通过 CRC。

作者原始提取与评分已接入运行；当前预处理与旧发布包存在输入版本差异，详情见 [数据文档](../guides/DATA_ACCESS.zh-CN.md)。论文来源：[DUFOMap §IV/V](https://arxiv.org/html/2403.01449v1#S4)、[BeautyMap §IV](https://arxiv.org/html/2405.07283v1#S4)；已完成的 [DUFOMap 表 IV 对照](DUFOMAP_TABLE4.zh-CN.md)。

逐行核查入口：

- [DUFOMap 固定版 README](https://github.com/KTH-RPL/dufomap/blob/9e239ddd5995136e14f5212f33382a6ebc59e518/README.md)
- [BeautyMap 固定版 README](https://github.com/MKJia/BeautyMap/blob/98bce4a97db96ddd0d5342e31425c7679f58ba2e/README.md)
- [ConceptGraphs 固定版 README](https://github.com/concept-graphs/concept-graphs/blob/93277a02bd89171f8121e84203121cf7af9ebb5d/README.md)
- [HOV-SG 固定版 README](https://github.com/hovsg/HOV-SG/blob/d6e65a53c8be6faec3f01f00d1644d967f89e605/README.md)
- [作者 PCL 评价源码](https://github.com/KTH-RPL/DynamicMap_Benchmark/blob/8b60f36a735a910b8c54b7eb12438db76fb32460/scripts/cpp/export_eval_pcd.cpp)

HOV-SG 原始 `application/create_graph.py` 对 Replica/ScanNet 跳过层级图构建；Replica 语义特征地图不能代替 HM3D 多楼层图。原 README 的 HM3D 生成命令存在路径漂移，固定提交实际入口为 `hovsg/data/hm3dsem/gen_hm3dsem_walks_from_poses.py`。

BeautyMap 表 IV 的地面／静态恢复模块消融尚未执行。核对本分支固定版的 [main.py](https://github.com/MKJia/BeautyMap/blob/98bce4a97db96ddd0d5342e31425c7679f58ba2e/main.py)及公开入口，未找到对应模块开关；目前不自行修改算法来冒充原消融。

[论文表 IV](https://arxiv.org/html/2405.07283v1#S4.T4)仍列为待完成。这一判断只针对固定快照，不能断言作者所有版本均无实现。

## 1. 语义评价的协议也要对照

| 项目 | ConceptGraphs 作者评价 | HOV-SG 作者评价 |
| --- | --- | --- |
| GT | 作者公开 HDF5 语义点云 + Semantic-NeRF 轨迹 | 原始 Replica 语义网格面片的顶点与实例类别 JSON |
| 预测类别 | 对象 CLIP 特征与每类一个文本提示比较；限制当前场景 GT 类别 | 分段 CLIP 特征与模板文本比较；从场景语义类别 JSON 读词表 |
| 评分支持面 | 先将对象预测用 1NN 转移到 RGB PointFusion 表面，再关联 GT | 在 GT 面片顶点位置对预测点做 5NN 类别多数投票 |
| 本轮忽略项 | `n_exclude=6`：other / floor / wall / ceiling / door / window | -1 / 0，并按类别名排除 wall / floor / ceiling / door / window / background |
| 输出 | mIoU、mrecall（mAcc）、F-mIoU 等 | mIoU、mAcc、F-mIoU、点准确率等 |

依据：[ConceptGraphs 评价入口](https://github.com/concept-graphs/concept-graphs/blob/93277a02bd89171f8121e84203121cf7af9ebb5d/conceptgraph/scripts/eval_replica_semseg.py) / [HOV-SG 评价入口](https://github.com/hovsg/HOV-SG/blob/d6e65a53c8be6faec3f01f00d1644d967f89e605/application/eval/evaluate_sem_seg.py) / [HOV-SG 插值实现](https://github.com/hovsg/HOV-SG/blob/d6e65a53c8be6faec3f01f00d1644d967f89e605/hovsg/utils/eval_utils.py)。

两套作者分数可用于核对各自的公开流程，但 GT 支持面、文本提示和插值规则不同，不能直接据此给两种方法排名。统一协议的配对实验应单独进行，并明确它不再是两套未经改变的作者评价。

机器人实机导航需要对应设备和作者机器人栈。这台电脑可以检查公开数据上的算法和仿真部分，但实机成功率不能用屏幕演示代替。DeepSeek 替换 GPT-4 属于独立变体，必须记录模型、提示、使用量、费用和图结构差异。
