# 新增作者原流程：哪些结果能支持研究判断

[English](AUTHOR_RESULTS_ANALYSIS.md) · [个人索引](README.zh-CN.md) · [独立复现分支](https://github.com/p20030920p/SLAM_Learning/tree/reproduce/author-originals)

2026-10-09 更新。这里分析新的独立原流程；本分支旧表格仍是原有子集和探索实验的记录，不覆盖、不拼接成同一实验。实时完成范围看复现分支的 [状态表](https://github.com/p20030920p/SLAM_Learning/blob/reproduce/author-originals/docs/STATUS.zh-CN.md)。

## 已达到的效果

DUFOMap C++ 和 BeautyMap Python 均完成作者公开的四份标注数据，每种方法 1997 扫描；使用作者 PCL 导出及评分脚本。下表为原始入口的单次运行，单位为百分比。

| 数据 | DUFOMap SA / DA | BeautyMap SA / DA | 能直接看到什么 |
|---|---:|---:|---|
| 00 release，141 扫描 | 97.9635 / 98.7196 | 96.9529 / 98.3382 | 两项均较高，不能据此论证普遍失效 |
| 05 release，321 扫描 | 97.3035 / 96.7986 | 96.7933 / 98.2248 | 静态保留和动态剔除的优劣方向不同 |
| AV2 release，575 扫描 | 96.6651 / 88.8985 | 92.4013 / 85.1671 | 两者 DA 均比上述 KITTI 公开包低；BeautyMap 参数迁移需单独标注 |
| 半室内，960 扫描 | 99.6373 / 83.0049 | 94.7785 / 90.4048 | DUFOMap 更保留静态点，BeautyMap 更移除动态点 |

可复查来源：[原始评分日志](https://github.com/p20030920p/SLAM_Learning/blob/cf21494/evidence/runs/released-lidar-01/scores/run.log)、[参数与图表](https://github.com/p20030920p/SLAM_Learning/blob/cf21494/docs/STATUS.zh-CN.md)。论文清理表格使用选定帧段，并非整条 KITTI 序列。BeautyMap 的 AV2 沿用室外示例参数，属于该论文未报告的补充迁移实验。没有重复运行区间或显著性结论。

新增 [DUFOMap 表 IV 消融](https://github.com/p20030920p/SLAM_Learning/blob/reproduce/author-originals/docs/DUFOMAP_TABLE4.zh-CN.md)：五组 SA/DA/AA 均与论文两位小数一致，无误差补偿时 SA 为 14.89%，完整设置为 97.96%。这确认误差补偿是已经存在的强基线；不能将“考虑位姿误差”本身写成新贡献，也不能从该消融推出 H1 已有效。H1 仍须验证迟到修正后的对象对应和查询坐标恢复。

## 与 H1 的关联和界限

| 新证据 | 对问题选择的作用 | 不能从中推出什么 |
|---|---|---|
| 同时报告 SA、DA，半室内出现取舍 | 新机制应在匹配变化召回时比较误删风险，综合分数不足以说明错误类型 | 不能说 DA 较低一定由共享位姿误差造成 |
| 两种方法都读取给定扫描位姿 | 明确可干预的接口是“位姿→空间对应→地图决策” | 没测 ATE/RPE，不能声称改善定位或 SLAM 轨迹 |
| BeautyMap 用先验地图的 XYZ，GT 标签未参与清理决策 | 必须交代先验几何来源，避免把 GT 文件名和使用标签混为一谈 | 有先验地图的离线结果不能直接代表无先验在线建图 |
| DUFOMap 默认 Python 体素结果在 0.05 m 近邻评分中 SA 明显较低 | 先排除输出表示和评价阈值的影响，再讨论误删机制 | 不能将体素中心偏移当作算法删除了同样比例的静态点 |
| room0 的 400 帧 ConceptGraphs 前端、原始映射与 RGB 表面已完成；最终地图为 77 个对象记录，原语义评价修复 CUDA 依赖后重试 | 完整空间表示与资源失败阶段可复查；作者窗口已能检查 RGB 和实例结构 | 对象记录数不是实例准确率；没有语义分数或 H1 恢复性证据 |
| HOV-SG 的 200/200 原分辨率特征提取完成，层级合并 OOM，最终特征图未保存 | 需要区分特征提取进度与完整地图交付，当前在重试 | Replica 不提供 HM3D 多楼层层级评价；提取进度不能代替语义分数 |

这批基线没有施加迟到位姿修正、没有运行 H1，也没有测对象变化后的过期时长。它们支持继续研究接口及评价取舍，尚未证明四篇论文有共同主导失效原因。

资源问题应单列。代码检查提示一个待测因素：HOV-SG 的 [合并函数](https://github.com/hovsg/HOV-SG/blob/d6e65a53c8be6faec3f01f00d1644d967f89e605/hovsg/utils/graph_utils.py#L373)接受 `voxel_size`，但该函数内没有执行体素下采样，而是追加点再运行 DBSCAN。这可能增加后续邻域计算成本；需要逐轮点数、内存/交换空间峰值和阶段耗时才能验证，当前不能断言它是全部 OOM 的原因，更不能当作 H1 的有效性证据。SAM 微批量解决的是显存压力，不保证 CPU 合并阶段可容纳完整地图。

新增原始 KITTI 下载也暴露了协议差异：当前作者 50 m 预处理重建的 00 与旧发布包，141 帧点数均不同，提供的位姿也不完全相同。[下载、预处理与对照记录](https://github.com/p20030920p/SLAM_Learning/blob/reproduce/author-originals/docs/DATA_ACCESS.zh-CN.md)。因此，新 01/02 结果与旧发布包分开报告；差异本身不能证明算法退化或反驳论文，也不能当作 H1 的效果。

在同一份新 02 输入上，DUFOMap 的 SA/DA 为 68.6114/89.2862%，BeautyMap 默认为 83.4254/84.6594%。[原始评分与三组网格结果](https://github.com/p20030920p/SLAM_Learning/blob/reproduce/author-originals/docs/KITTI_SELECTED_RESULTS.zh-CN.md)。这里出现了更明显的静态保留问题，可作为配对干预候选；仍须固定观测与评价协议，分别干预位姿、可见性和参数，不能从跨场景分数直接确定原因。

新增 [60 秒作者三维窗口实录](https://github.com/p20030920p/SLAM_Learning/blob/reproduce/author-originals/evidence/videos/conceptgraphs-room0-original-window.mp4)，展示同一份验证地图的 RGB／实例颜色与视角操作。颜色差异来自查看器切换，不是语义准确率对照。HOV-SG 的完整特征图重试正在运行。

## 可以怎样简洁地写

> 原始动态清理流程在四份公开数据上均能运行，但静态保留与动态剔除存在场景相关取舍。本文据此将问题收窄到：给定历史位姿后来被修正时，地图中的对象对应与查询坐标应如何更新？当前基线不足以回答恢复性和过期风险，后续用同一观测序列比较几何修正、重新关联和有界回放，并同时报告变化召回、查询覆盖、更新延迟及内存成本。

上段是问题动机的写法示例，不是创新已成立的结论。若只修正几何已达到全量回放效果，关联恢复的额外机制就缺少依据；若低误删仅靠保留更多过期目标，也应否定相应收益。[原有否定控制与分析空白](LAB_ANALYSIS.zh-CN.md)。

比较 ConceptGraphs 与 HOV-SG 时还要保留各自的 GT 支持面、类别排除项和插值规则；原作者同名 mIoU 不能直接用于跨方法排名。[原始评价协议对照](https://github.com/p20030920p/SLAM_Learning/blob/reproduce/author-originals/docs/SCOPE.zh-CN.md)。
