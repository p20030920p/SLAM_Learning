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

新增 [BeautyMap 表 III 与历史协议](https://github.com/p20030920p/SLAM_Learning/blob/reproduce/author-originals/docs/KITTI_PAPER_PROTOCOL.zh-CN.md)：在作者注明的历史 benchmark 预处理、原始 GT／PCL 导出和原作者 HA 评分下，02 的 0.5/1/2 m 三组 SA/DA/HA 共 9 项匹配论文两位小数。该场景中更粗网格提高 DA、降低 SA，属于作者已有的参数取舍，不是 H1 的收益。旧评分只有 AA，核对论文 HA 时另跑原作者含 HA 的评分器；不能混用两列。01 的差距尚未解决，也不能从 02 匹配推定全部历史设置一致。

## 与 H1 的关联和界限

| 新证据 | 对问题选择的作用 | 不能从中推出什么 |
|---|---|---|
| 同时报告 SA、DA，半室内出现取舍 | 新机制应在匹配变化召回时比较误删风险，综合分数不足以说明错误类型 | 不能说 DA 较低一定由共享位姿误差造成 |
| 两种方法都读取给定扫描位姿 | 明确可干预的接口是“位姿→空间对应→地图决策” | 没测 ATE/RPE，不能声称改善定位或 SLAM 轨迹 |
| BeautyMap 用先验地图的 XYZ，GT 标签未参与清理决策 | 必须交代先验几何来源，避免把 GT 文件名和使用标签混为一谈 | 有先验地图的离线结果不能直接代表无先验在线建图 |
| DUFOMap 同一 Python 参数：0.05 m 下原始点／体素 SA 为 99.8860/51.6256%；体素阈值改为 0.10 m 后 SA 为 98.9436% | 输出表示与评价阈值强烈影响评分；同时观察 DA，放宽阈值也改变动态点匹配 | 不能将体素低 SA 当作同等静态结构被删；Python d_p=2，与 C++ 默认 d_p=1 不同，不能把二者差异归为单一因素 |
| room0 的 400 帧 ConceptGraphs 原始链路完成，mIoU 21.3460%、频率加权 IoU 50.1379%；混淆矩阵复算通过 | 现在可以检查原始语义分类；宏平均与常见类别加权的差距提示需要逐类分析 | 单场景、场景 GT 词表与原支持面；不是开放世界检索、对象身份准确率或 H1 恢复性证据 |
| HOV-SG 默认 200 帧融合先 OOM、后超时；另取 20 帧地图完成，修正包装脚本后原评价 mIoU 34.7500%、F-mIoU 62.8725% | 已有可复查的家用语义基线；地图保存、资源失败和配置错误分别判定 | 20 帧不能代表默认 benchmark；原生分数不能与 CG 直接排名，也不能代替 HM3D 层级评价 |

这批基线没有施加迟到位姿修正、没有运行 H1，也没有测对象变化后的过期时长。它们支持继续研究接口及评价取舍，尚未证明四篇论文有共同主导失效原因。

新增 [CG room0 原评分与分母](https://github.com/p20030920p/SLAM_Learning/blob/reproduce/author-originals/docs/CONCEPTGRAPHS_ROOM0_RESULTS.zh-CN.md)：23 个有效类别、4,085,377 个重建点计入混淆矩阵。对象标签先用 1NN 填充 RGB 表面，不能将这项语义分数解释为几何准确率；`all` 只含 room0。作者 mF1 为 25.2661%，其分母使用 `max(1,p+r)`；标准调和宏 F1 的补充值为 25.8221%，不替换原 CSV。原生分数与本分支旧八观测探索指标分别报告。

现在另完成了 office0/office1 SAM-only，以及 room0/office0 Detect，新增四份混淆矩阵独立复算通过。下表均取原 CSV 的场景行，非部分 benchmark 均值。

| 场景 | SAM-only mIoU / F-mIoU % | Detect mIoU / F-mIoU % | 对研究判断的限制 |
|---|---:|---:|---|
| room0 | 21.3460 / 50.1379 | 25.5987 / 45.6541 | Detect 宏平均提高、加权平均下降；零 IoU 类还从 10/23 增至 12/23 |
| office0 | 20.4157 / 33.0546 | 17.5151 / 30.4729 | Detect 两项均下降，不能从 room0 推出前端普遍更好 |
| office1 | 14.9755 / 14.7128 | 尚未完成 | 先保留失败模式，不能补出缺失结果 |

[原 CSV、图表与协议解释](https://github.com/p20030920p/SLAM_Learning/blob/reproduce/author-originals/docs/CONCEPTGRAPHS_SCENE_RESULTS.zh-CN.md)。两种原流程的检测与映射参数同时不同，不能隔离单一组件原因。场景行按 GT 出现类别计分，`all` 按矩阵非零 GT 支持类别裁行、裁列；office1 SAM-only 的两行 mIoU 为 14.9755/16.3958%，加权 IoU 也不同。room0 两行相同只是特例，不能平均单场景 `all` 来冒充原八场景评分。后续 H1 继续固定同一前端、支持面与类别集合，以免把这些协议差异当成恢复收益。

逐类拆分进一步限制归因：blinds / sofa 的 IoU 为 94.77 / 74.78%，而 rug / table 均为 0，后两类分别占计分表面 GT 的 18.34 / 6.36%，却没有对应类别预测点。23 类中 10 类 IoU 为 0，不能只解释为稀有类别拖低宏平均。这说明语义分类基线本身仍有明确缺口；零预测不等于没有几何，也没有确定是 CLIP、掩码、关联或位姿造成。后续 H1 实验须固定前端，单独检查对象身份与坐标恢复，不能把原始语义缺口一并当作恢复模块收益。[图表、逐类 CSV 与来源哈希](https://github.com/p20030920p/SLAM_Learning/blob/reproduce/author-originals/evidence/runs/conceptgraphs-room0-class-analysis-01/summary.json)。

[Python 输出与阈值的完整对照](https://github.com/p20030920p/SLAM_Learning/blob/reproduce/author-originals/docs/DUFOMAP_OUTPUT_AUDIT.zh-CN.md)采用原始入口和原评价；0.10 m 为单独的敏感性分析，不替换论文 0.05 m 指标，也不支持 H1 已有效。

资源问题应单列。代码检查提示一个待测因素：HOV-SG 的 [合并函数](https://github.com/hovsg/HOV-SG/blob/d6e65a53c8be6faec3f01f00d1644d967f89e605/hovsg/utils/graph_utils.py#L373)接受 `voxel_size`，但该函数内没有执行体素下采样，而是追加点再运行 DBSCAN。这可能增加后续邻域计算成本；需要逐轮点数、内存/交换空间峰值和阶段耗时才能验证，当前不能断言它是全部 OOM 的原因，更不能当作 H1 的有效性证据。SAM 微批量解决的是显存压力，不保证 CPU 合并阶段可容纳完整地图。

新增原始 KITTI 下载也暴露了协议差异：当前作者 50 m 预处理重建的 00 与旧发布包，141 帧点数均不同，提供的位姿也不完全相同。[下载、预处理与对照记录](https://github.com/p20030920p/SLAM_Learning/blob/reproduce/author-originals/docs/DATA_ACCESS.zh-CN.md)。切回历史版后 141 帧点数相同，但文件仍不同，00/01 的差距仍在。因此，新版预处理、历史重建与旧发布包分别报告；差异本身不能证明算法退化或反驳论文，也不能当作 H1 的效果。

在同一份新 02 输入上，DUFOMap 的 SA/DA 为 68.6114/89.2862%，BeautyMap 默认为 83.4254/84.6594%。[原始评分与三组网格结果](https://github.com/p20030920p/SLAM_Learning/blob/reproduce/author-originals/docs/KITTI_SELECTED_RESULTS.zh-CN.md)。这里出现了更明显的静态保留问题，可作为配对干预候选；仍须固定观测与评价协议，分别干预位姿、可见性和参数，不能从跨场景分数直接确定原因。

新增 [60 秒作者三维窗口实录](https://github.com/p20030920p/SLAM_Learning/blob/reproduce/author-originals/evidence/videos/conceptgraphs-room0-original-window.mp4)，展示同一份验证地图的 RGB／实例颜色与视角操作。颜色差异来自查看器切换，不是语义准确率对照。HOV-SG 默认采样 03 重试已超时；[20 帧家用结果](https://github.com/p20030920p/SLAM_Learning/blob/reproduce/author-originals/docs/HOVSG_HOME_RESULTS.zh-CN.md)修正包装脚本后已完成原评分：mIoU 34.7500%、F-mIoU 62.8725%、mAcc 43.7114%、pAcc 72.1861%。审计只核对绑定日志，作者未保存混淆矩阵，不声称独立复算。采样改变观测和融合规模，不能把成功单独归因某个内存机制，也不能算默认 benchmark。[超时记录](https://github.com/p20030920p/SLAM_Learning/blob/reproduce/author-originals/evidence/runs/hovsg-room0-batch16-stages-03-features/diagnostics/timeout-diagnosis.json)。

默认 04 已排队等 CG 队列结束，沿用 200 帧采样和原算法，显式延长特征阶段至 6 小时、配置 16G/48G；尚未开始计算，不预填成功或分数。重启中断的 office1 Detect 虽有 400/400 日志，缺退出码，已保留后从头重跑；完成标记要求退出记录与产物契约一起通过。

## 可以怎样简洁地写

> 原始动态清理流程在四份公开数据上均能运行，但静态保留与动态剔除存在场景相关取舍。本文据此将问题收窄到：给定历史位姿后来被修正时，地图中的对象对应与查询坐标应如何更新？当前基线不足以回答恢复性和过期风险，后续用同一观测序列比较几何修正、重新关联和有界回放，并同时报告变化召回、查询覆盖、更新延迟及内存成本。

上段是问题动机的写法示例，不是创新已成立的结论。若只修正几何已达到全量回放效果，关联恢复的额外机制就缺少依据；若低误删仅靠保留更多过期目标，也应否定相应收益。[已填写的分析简稿](LAB_ANALYSIS.zh-CN.md)与[完整开放问题／假设稿](OPEN_QUESTION_AND_HYPOTHESIS.zh-CN.md)分别给出短版和可否证实验。

比较 ConceptGraphs 与 HOV-SG 时还要保留各自的 GT 支持面、类别排除项和插值规则；原作者同名 mIoU 不能直接用于跨方法排名。[原始评价协议对照](https://github.com/p20030920p/SLAM_Learning/blob/reproduce/author-originals/docs/SCOPE.zh-CN.md)。
