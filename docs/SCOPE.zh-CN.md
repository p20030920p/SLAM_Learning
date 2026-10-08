# 原库对照与完成标准

这里的“完整”以作者公开的阶段、数据和评价为准。跑出一个点云或截图不代表论文全部实验复现。

| 方法 | 作者公开链路 | 本轮覆盖 | 完整复现仍需 |
|---|---|---|---|
| DUFOMap | 读取带位姿点云 → 动态清理 → 点云输出 → DynamicMap 评价 | Python 默认演示、原始 C++、141 帧 teaser、作者 PCL 与 SA/DA/AA/HA | 完整数据序列、论文参数/消融、性能与位姿来源对照 |
| BeautyMap | 先验全局地图 + 位姿/扫描 → 二进制地面矩阵 → 清理 → 同一评价 | 原始 main.py、141 帧 teaser、作者评价 | 完整 benchmark、先验地图/地面/稀疏性实验、论文消融 |
| ConceptGraphs | RGB-D/位姿 → SAM 或 RAM+DINO+SAM → CLIP → 对象关联/融合 → LLaVA 描述 → GPT-4 精炼/关系 → 语义/规划评价 | 固定原库与作者推荐 GSA/LLaVA；新环境安装中 | 完整 8 场景、两种前端、语义 GT、LLaVA 基础权重、原始 GPT-4、规划任务 |
| HOV-SG | RGB-D/位姿 → SAM+CLIP → 融合语义地图 → 楼层/房间/对象图 → 查询/导航/评价 | 固定原库、全新作者 YAML 环境、完整 Replica；room0 首次运行被重启中断 | Replica/ScanNet 语义 GT；8 个 HM3DSem 场景及完整层级评价；导航 |

逐行核查入口：

- [DUFOMap 固定版 README](https://github.com/KTH-RPL/dufomap/blob/9e239ddd5995136e14f5212f33382a6ebc59e518/README.md)
- [BeautyMap 固定版 README](https://github.com/MKJia/BeautyMap/blob/98bce4a97db96ddd0d5342e31425c7679f58ba2e/README.md)
- [ConceptGraphs 固定版 README](https://github.com/concept-graphs/concept-graphs/blob/93277a02bd89171f8121e84203121cf7af9ebb5d/README.md)
- [HOV-SG 固定版 README](https://github.com/hovsg/HOV-SG/blob/d6e65a53c8be6faec3f01f00d1644d967f89e605/README.md)
- [作者 PCL 评价源码](https://github.com/KTH-RPL/DynamicMap_Benchmark/blob/8b60f36a735a910b8c54b7eb12438db76fb32460/scripts/cpp/export_eval_pcd.cpp)

HOV-SG 原始 `application/create_graph.py` 对 Replica/ScanNet 跳过层级图构建；Replica 语义特征地图不能代替 HM3D 多楼层图。原 README 的 HM3D 生成命令存在路径漂移，固定提交实际入口为 `hovsg/data/hm3dsem/gen_hm3dsem_walks_from_poses.py`。

机器人实机导航需要对应设备和作者机器人栈。这台电脑可以检查公开数据上的算法和仿真部分，但实机成功率不能用屏幕演示代替。DeepSeek 替换 GPT-4 属于独立变体，必须记录模型、提示、使用量、费用和图结构差异。
