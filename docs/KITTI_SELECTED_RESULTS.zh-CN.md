# KITTI 01/02：作者原始流程与论文数值对照

[English](KITTI_SELECTED_RESULTS.md) | 中文

2026-10-09，在本机完成当前固定版作者预处理、DUFOMap C++、BeautyMap Python、作者 PCL 近邻导出与原始 Python 评分。01 为 150–250，共 101 帧；02 为 860–950，共 91 帧，均包含端点。原始源仓库保持干净。

本轮采用当前作者的 50 m 预处理与官方 SemanticKITTI SuMa 位姿。00 的协议检查已确认它与旧发布包不等价；本表单列为当前原始流程的结果，不与旧发布数据拼成同一组论文复现。[数据与差异说明](DATA_ACCESS.zh-CN.md)、[完整流程记录](../evidence/runs/kitti-author-selected-02/outcomes.json)。

## 1. 实际原始评分

| 帧段 | 方法 / XY 网格 | SA % | DA % | AA % | HA % |
| --- | --- | ---: | ---: | ---: | ---: |
| 01，101 帧 | DUFOMap 默认 | 98.9445 | 93.9332 | 96.4063 | 96.3737 |
| 01，101 帧 | BeautyMap，1 m | 99.3033 | 92.3692 | 95.7735 | 95.7108 |
| 02，91 帧 | DUFOMap 默认 | 68.6114 | 89.2862 | 78.2691 | 77.5953 |
| 02，91 帧 | BeautyMap，0.5 m | 83.2957 | 86.0901 | 84.6814 | 84.6699 |
| 02，91 帧 | BeautyMap，1 m | 83.4254 | 84.6594 | 84.0401 | 84.0378 |
| 02，91 帧 | BeautyMap，2 m | 74.5822 | 90.6875 | 82.2416 | 81.8502 |

来源：[01 原始评分日志](../evidence/runs/kitti-author-selected-02/01-scores/run.log)、[02 原始评分日志](../evidence/runs/kitti-author-selected-02/02-scores/run.log)、[机器可读结果](../evidence/runs/kitti-author-selected-02/metrics.json)。`record.json` 包含退出码、源提交、原日志哈希与完整命令。

[六份最终点云检查](../evidence/runs/kitti-result-validation-01/validation.json)已通过：全部 PCD 点数/字节结构正确，XYZ 为有限数值，文件 SHA-256 与成功运行记录一致，两个原始评分日志的哈希也相符。这些是产物检查，准确率仍取上面的原始评分。

DUFOMap 使用原默认 `resolution=0.1`、`inflate_hits_dist=0.2`、`inflate_unknown=1`。BeautyMap 三组只改变公开 `xy_resolution`，保持 `dis_range=40`、`h_res=0.5`；原脚本没有模块开关，本轮尚未完成表 IV 模块消融。02 的 DUFOMap 为补充场景，不是该论文表 I 的 KITTI 场景。

## 2. 与论文的差距

下表的论文数字只作目标对照，不能忽略输入差异认定等价。最后一项指标在两篇论文中不同，已逐行注明；均取两位小数便于阅读。

| 项目 | 论文 SA / DA / 综合指标 % | 本轮 SA / DA / 综合指标 % |
| --- | ---: | ---: |
| DUFOMap 表 I，01，AA | 98.09 / 94.20 / 96.12 | 98.94 / 93.93 / 96.41 |
| BeautyMap 表 IV 完整方法，01，HA | 99.17 / 92.99 / 96.03 | 99.30 / 92.37 / 95.71 |
| BeautyMap 表 III，02，0.5 m，HA | 83.92 / 84.14 / 84.03 | 83.30 / 86.09 / 84.67 |
| BeautyMap 表 III，02，1 m，HA | 83.40 / 82.41 / 82.90 | 83.43 / 84.66 / 84.04 |
| BeautyMap 表 III，02，2 m，HA | 74.92 / 88.83 / 81.28 | 74.58 / 90.69 / 81.85 |

论文：[DUFOMap 表 I](https://arxiv.org/html/2403.01449v1)、[BeautyMap 表 III/IV](https://arxiv.org/html/2405.07283v1)。这些新数值未复现到论文的两位小数精度。

BeautyMap 论文未在表 III 单列 z 分辨率，本轮固定为 README 的 0.5 m，不能假定该参数已核实一致。旧 00 发布包上的 [DUFOMap 表 IV 五组匹配](DUFOMAP_TABLE4.zh-CN.md)仍成立，两个结论分开保留。

## 3. 如何解释、还缺什么

02 上 DUFOMap 的静态保留明显低于其 01 结果；在同一份 02 输入上，BeautyMap 三组网格也有 SA/DA 取舍。这里只能说明当前流程的输出和评价结果。不能仅据跨场景差异归因于定位误差、稀疏性或遮挡，也没有运行 H1 的恢复机制。该场景可用于后续固定观测与评价协议、分别干预位姿/可见性/参数的配对实验。

所有原始点云与 GT 保持全量，作者评价阈值为 0.05 m。资源限额为 4G RAM / 6G swap / 两核 CPU 配额，且与 HOV-SG 并行；不把本轮耗时作为论文性能复现或公平速度比较。

尚需核对旧发布数据的精确位姿/预处理来源、BeautyMap 模块消融、DUFOMap 在线版本与位姿来源实验。重做下载和方法运行的命令见 [数据文档](DATA_ACCESS.zh-CN.md)。
