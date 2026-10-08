# 原库对照与完成标准

这里的“完整”以作者公开的阶段、数据和评价为准。跑出一个点云或截图不代表论文全部实验复现。

| 方法 | 作者公开链路 | 本轮覆盖 | 完整复现仍需 |
|---|---|---|---|
| DUFOMap | 读取带位姿点云 → 动态清理 → 点云输出 → DynamicMap 评价 | 原始 C++ 在全部四份公开标注数据完成作者评价；Python 默认演示单独对照 | KITTI 全序列、论文参数/消融、性能与位姿来源对照 |
| BeautyMap | 先验全局地图 + 位姿/扫描 → 二进制地面矩阵 → 清理 → 同一评价 | 原始 main.py 与作者评价覆盖四份公开数据，共 1997 帧；AV2 参数迁移已标注 | AV2 论文专属参数核验、先验地图/地面/稀疏性实验、论文消融 |
| ConceptGraphs | RGB-D/位姿 → SAM 或 RAM+DINO+SAM → CLIP → 对象关联/融合 → LLaVA 描述 → GPT-4 精炼/关系 → 语义/规划评价 | 独立环境/CUDA 算子、完整 RGB-D 与作者 HDF5 GT；room0 的 400 帧 SAM 前端完成；首次三维融合 cgroup OOM，恢复默认检查点配置后重试已排队；原版 Detect 已排队 | 完整 8 场景与两种前端、三维/语义评价、LLaVA 基础权重、原始 GPT-4、规划任务 |
| HOV-SG | RGB-D/位姿 → SAM+CLIP → 融合语义地图 → 楼层/房间/对象图 → 查询/导航/评价 | 全新作者 YAML 环境、完整 Replica RGB-D 与已通过 CRC 的原始语义 GT；SAM 批量 16、原分辨率的 room0 特征提取正在执行 | 完整 Replica/ScanNet 语义评价；8 个 HM3DSem 场景及完整层级评价；导航 |

逐行核查入口：

- [DUFOMap 固定版 README](https://github.com/KTH-RPL/dufomap/blob/9e239ddd5995136e14f5212f33382a6ebc59e518/README.md)
- [BeautyMap 固定版 README](https://github.com/MKJia/BeautyMap/blob/98bce4a97db96ddd0d5342e31425c7679f58ba2e/README.md)
- [ConceptGraphs 固定版 README](https://github.com/concept-graphs/concept-graphs/blob/93277a02bd89171f8121e84203121cf7af9ebb5d/README.md)
- [HOV-SG 固定版 README](https://github.com/hovsg/HOV-SG/blob/d6e65a53c8be6faec3f01f00d1644d967f89e605/README.md)
- [作者 PCL 评价源码](https://github.com/KTH-RPL/DynamicMap_Benchmark/blob/8b60f36a735a910b8c54b7eb12438db76fb32460/scripts/cpp/export_eval_pcd.cpp)

HOV-SG 原始 `application/create_graph.py` 对 Replica/ScanNet 跳过层级图构建；Replica 语义特征地图不能代替 HM3D 多楼层图。原 README 的 HM3D 生成命令存在路径漂移，固定提交实际入口为 `hovsg/data/hm3dsem/gen_hm3dsem_walks_from_poses.py`。

## 语义评价的协议也要对照

| 项目 | ConceptGraphs 作者评价 | HOV-SG 作者评价 |
|---|---|---|
| GT | 作者公开 HDF5 语义点云 + Semantic-NeRF 轨迹 | 原始 Replica 语义网格面片的顶点与实例类别 JSON |
| 预测类别 | 对象 CLIP 特征与每类一个文本提示比较；限制当前场景 GT 类别 | 分段 CLIP 特征与模板文本比较；从场景语义类别 JSON 读词表 |
| 评分支持面 | 先将对象预测用 1NN 转移到 RGB PointFusion 表面，再关联 GT | 在 GT 面片顶点位置对预测点做 5NN 类别多数投票 |
| 本轮忽略项 | `n_exclude=6`：other / floor / wall / ceiling / door / window | -1 / 0，并按类别名排除 wall / floor / ceiling / door / window / background |
| 输出 | mIoU、mrecall（mAcc）、F-mIoU 等 | mIoU、mAcc、F-mIoU、点准确率等 |

依据：[ConceptGraphs 评价入口](https://github.com/concept-graphs/concept-graphs/blob/93277a02bd89171f8121e84203121cf7af9ebb5d/conceptgraph/scripts/eval_replica_semseg.py) / [HOV-SG 评价入口](https://github.com/hovsg/HOV-SG/blob/d6e65a53c8be6faec3f01f00d1644d967f89e605/application/eval/evaluate_sem_seg.py) / [HOV-SG 插值实现](https://github.com/hovsg/HOV-SG/blob/d6e65a53c8be6faec3f01f00d1644d967f89e605/hovsg/utils/eval_utils.py)。

两套作者分数可用于核对各自的公开流程，但 GT 支持面、文本提示和插值规则不同，不能直接据此给两种方法排名。统一协议的配对实验应单独进行，并明确它不再是两套未经改变的作者评价。

机器人实机导航需要对应设备和作者机器人栈。这台电脑可以检查公开数据上的算法和仿真部分，但实机成功率不能用屏幕演示代替。DeepSeek 替换 GPT-4 属于独立变体，必须记录模型、提示、使用量、费用和图结构差异。
