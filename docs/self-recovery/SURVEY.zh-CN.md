# 论文地图：退化与大变动场景下的定位自恢复

**核验规则**：本文件每一条都经过实际打开页面核验（arXiv abs 页 / DOI 注册记录 / 出版社或机构库落地页）。凡未能核验的条目，一律集中列在最后一节"未核验线索"，**不进入假设论证**。

> 状态：A（退化与失败检测）、C（长期定位与地图维护）、D（鲁棒后端与失效恢复）、E（评测方法与基准）四组已完成；B（全局重定位与绑架机器人）待补。

---

## 组 A｜退化与失败检测、自诊断（12 篇）

| 论文 | 年份 / 出处 | 机制一句话 | 对自恢复的意义与缺口 |
| --- | --- | --- | --- |
| [X-ICP: Localizability-Aware LiDAR Registration](https://arxiv.org/abs/2211.16335) | arXiv 2024（投稿 IEEE T-RO） | 用 scan–map 对应在主优化方向上分析对齐强度，得六轴可定位性，耦合进带约束 ICP | 退化感知范式最完整的一篇；但**不判断定位整体是否可信**，退化时靠外部里程计顶住——是"避免失效"不是"失效后恢复" |
| [Informed, Constrained, Aligned: Degeneracy-aware Point Cloud Registration in the Wild](https://arxiv.org/abs/2408.11809) | IEEE T-FR（接收），arXiv 2025 | 大规模对比主动/被动退化缓解（TSVD、不等式约束、Tikhonov 正则化） | 给出"检测到退化之后怎么办"的方法学地图；**只管优化内部**，无系统级可信度判断与恢复 |
| [LF-GICP: Parameter-Free Degeneracy-Aware LiDAR Odometry](https://arxiv.org/abs/2608.19522) | arXiv 2026-08 预印本 | 指出体素化 GICP 的协方差正则化会**掩盖**退化；构造无正则化体素法向可定位性场（方向各向异性 + 绝对信息量） | 免调参 + 物理解释；**关键否定性结论**：直匀隧道对纯 LiDAR 配准在轴向永远不可观测。仍无恢复动作 |
| [LiLi: Lie Theory Based 3D LiDAR Scan Alignment Degeneracy Detection](https://arxiv.org/abs/2609.17145) | arXiv 2026-09 预印本 | 用 se(3) 生成元扰动已优化解、重新优化后比对，识别退化的完整变换集合 | "检测器本身可不可信"这一层的推进：430 m 往返隧道中 Hessian 基线失败而它成功。仍止于检测 |
| [Degenerate in Whose Frame? An Equivariance Condition for Degeneracy Detection](https://arxiv.org/abs/2608.15532) | arXiv 2026-08（投稿 RA-L） | 信息矩阵在机体系变化下按**合同变换** $H'=\mathrm{Ad}(T)^\top H\,\mathrm{Ad}(T)$；逐轴脚印与阈值化谱**不等变**；给出等变度量的充要条件 | 对主线最锋利的一篇：**逐轴退化标签可能只是坐标系产物**，而现有恢复方案都无条件相信这类触发信号 |
| [A Comprehensive Survey on the Integrity of Localization Systems](https://hal.science/hal-05044835v1) | Sensors 2025, 25(2):358 | 把 GNSS 的完好性/保护级概念推广到优化型、融合型、SLAM 型定位 | 量化了空白：73.3% 的完好性研究仍集中在 GNSS。但**只回答"能不能信自己"，不回答"信不了怎么回来"** |
| [Lifelong Localization in Dynamic Indoor Environments Combining Odometry with Sparse Distance Sampling](https://arxiv.org/abs/2607.17852) | ICRA 2026 | 用 16 个稀疏距离采样给出位置先验（实时解 kidnapped robot，至多到对称性），再与里程计融合收敛；静态环境可证收敛到真值 | **全组唯一接近"检测→恢复闭环"的工作**：失效后无需重启、无需人工，在线重建可信定位。缺口正是它的前提——"变化的性质已被正确学到"，真正未知的大改造下保证失效 |
| [DELO: Deep Evidential LiDAR Odometry using Partial Optimal Transport](https://arxiv.org/abs/2308.07153) | ICCV 2023 Workshop | 部分最优传输做帧间匹配，联合学习里程计与预测不确定性 | 提供第二类自诊断信号（学习置信度，与几何退化互补）；失败处理只停留在"提示该做位姿图优化" |
| [Introspective Perception for Mobile Robots](https://arxiv.org/abs/2306.16698)（配套 [CPIP, RA-L 2022](https://arxiv.org/abs/2109.13974)） | arXiv 2023 | 用感知冗余与一致性约束自主监督学习误差分布；把"感知错误学习"与"任务失败预测"分解 | 把自省从单一指标提升为可学习框架；但闭环落在规划侧（绕开），不是把定位拉回可信 |
| [A General Framework for Lifelong Localization and Mapping in Changing Environment](https://arxiv.org/abs/2111.10946) | arXiv 2021 | 多会话地图表示 + 地图更新与稀疏化（Chow-Liu 最大互信息生成树控内存）；真实超市部署一个多月 | 代表"用持续更新地图避免失败"的路线；**把恢复问题转化为地图维护**，单次会话内跑飞后无回收机制 |
| [Sensor Resetting Localization for Poorly Modelled Mobile Robots](http://www.cs.cmu.edu/~coral/old/publications/b2hd-icra00-srl.html) | ICRA 2000（DOI 10.1109/ROBOT.2000.844766） | 短/长期观测似然比值跌破阈值即判定定位可能已错，从传感器模型采样注入随机粒子 | **你系统里已存在的恢复机制**（AMCL 至今保留）：隐式检测（单标量）→ 盲目重采样；不知道退化发生在哪个方向、也不报告恢复是否成功 |
| [RTMap: Real-Time Recursive Mapping with Change Detection and Localization](https://arxiv.org/abs/2507.00980)（对照 [ELite, ICRA 2025](https://arxiv.org/abs/2502.13452)） | arXiv 2025 | 一次遍历同时做元素不确定性建模、相对先验地图的概率化定位、道路结构变化实时检测；地图作为自我演化记忆 | 覆盖"地图与现状不一致"且有在线闭环，但**闭环在地图侧（改地图）而非定位侧（把跑飞的位姿拉回）** |

### A 组共同假设
1. 退化是"当前帧 vs 地图"的局域几何属性，可从单帧/短窗口的信息矩阵或残差算出——**没人把"历史轨迹已经错了"作为检测输入**。
2. 地图可信：除 RTMap/ELite 外都默认先验地图与现状一致。
3. 退化方向与优化器主方向对齐，检测量都在优化器自己的坐标系里报告（第 5 条正是打这个假设）。
4. 外部里程计/IMU 是可信兜底。
5. 失败是慢性、可平滑加权的，不会突然整体翻转，因此不需要离散的"宣布失效"决策。
6. **恢复 ≈ 抑制**：不让错误更新进来就算解决。

### A 组共同盲区
1. **"知道错了"与"回到对的位置"之间是断的**：12 篇里只有稀疏距离采样那一篇在失效后重建了可信定位并给收敛保证。
2. **没有"恢复成功"的判据**。
3. **没有失败归因**：不可观测 vs 地图过期 vs 动态遮挡在检测信号上高度混叠，而恢复动作恰恰依赖归因。
4. **检测器的自指问题被回避**。
5. 主动恢复（用运动把可观测性挣回来）几乎空白。
6. 被跳过的一类状态：**长期"局部可信但整体已漂"**。

---

## 组 D｜鲁棒后端与"事后撤销/恢复"（12 篇）

| 论文 | 年份 / 出处 | 机制一句话 | 对自恢复的意义与缺口 |
| --- | --- | --- | --- |
| [Robust Loop Closing Over Time（RRR）](https://doi.org/10.1177/0278364913498910) | IJRR 2013（会议版 RSS 2012） | 同区域候选回环聚组后用 $\chi^2$ 检验自洽性；不一致则暂接受、重优化、复检，确认为假就**整体回退**图状态，再用剩余一致约束重新优化 | 唯一把"发现→撤销→恢复"写成完整闭环的早期工作，可撤销后端的直接祖先；撤销窗口只覆盖刚加入的回环组，不处理退化与动态造成的整段漂移 |
| [LTA-OM: Long-term association LiDAR–IMU odometry and mapping](https://doi.org/10.1002/rob.22337) | JFR 41(7):2455–2474, 2024 | 回环被判假阳性时**不执行 PGO，直接把图恢复到上一状态**；配子图级地图维护 | 最贴近主线的"事后撤销"落地实现，把回滚提升为后端一等操作；回滚深度只有"上一个状态"。*机制描述取自正文片段，未逐节通读* |
| [DARE-SLAM](https://arxiv.org/abs/2102.05117) | JIRS 2021 | 把在线退化/可观测性度量作为地点识别与回环几何验证的门控信号 | 从"防错"到"少犯错"；但仍是进入优化前的门控，**没有对已提交约束的撤销** |
| [Pairwise Consistent Measurement Set Maximization（PCM）](https://doi.org/10.1109/ICRA.2018.8460217) | ICRA 2018 | 对每对候选做两两一致性检验，取最大团作为一致集，只让集合内回环进入优化 | 把鲁棒性从"逐边降权"抬到"集合级一致性"，能剔除**共谋式错误**；只在优化前筛，不回滚已污染地图 |
| [Switchable Constraints](https://doi.org/10.1109/IROS.2012.6385590) | IROS 2012 | 每条回环边引入开关变量 $s\in[0,1]$ 缩放信息矩阵，与位姿联合优化 | 奠基性软开关，额外给出"哪些约束被关掉"的可解释信号；对共谋错误与退化无效 |
| [Robust Map Optimization using Dynamic Covariance Scaling（DCS）](https://doi.org/10.1109/ICRA.2013.6630557) | ICRA 2013 | 由残差闭式解出缩放因子，等价于迭代重加权，无额外状态 | 最易落地；**无撤销语义**，对"多个互相自洽的错回环"无能为力——恰是大变动场景的典型失败模式 |
| [Inference on Networks of Mixtures for Robust Robot Mapping（max-mixtures）](https://doi.org/10.1177/0278364913479413) | IJRR 2013（RSS 2012） | 每条回环用含宽先验（null 分量）的高斯混合建模，多模态被保留而非提前平均 | "延迟决策"的思想源头；不给"最终提交哪个假设"的判据，也不支持提交后撤销 |
| [Graduated Non-Convexity for Robust Spatial Perception（GNC）](https://arxiv.org/abs/1909.08605) | RA-L 2020（ICRA 2020 最佳论文） | Black-Rangarajan 对偶 + 渐进非凸，逐步收紧控制参数并闭式更新权重，无需初值即可拒绝大量离群点 | 最强批量离群剔除工具；批处理——在线化需要"检测失效→触发全局重算"的调度，且仍假定存在足够内点 |
| [MH-iSAM2: Multi-hypothesis iSAM using Bayes Tree and Hypo-tree](https://doi.org/10.1109/ICRA.2019.8793854) | ICRA 2019 | 扩展 Bayes tree 支持多假设推断，用 Hypo-tree 追踪并剪枝 | 把"延迟决策"做成增量后端原语；**只延迟、不撤销**，一旦提交无回退路径 |
| [On Degeneracy of Optimization-based State Estimation Problems](https://doi.org/10.1109/ICRA.2016.7487211) | ICRA 2016 | 特征分解识别退化方向，只在良态方向求解、退化方向保持先前估计 | 退化感知的基石；**只保证不再恶化，没有回到正确历史的机制** |
| [ORB-SLAM3](https://arxiv.org/abs/2007.11898) | IEEE T-RO 2021 | 多地图 Atlas：跟踪丢失时另起新地图，重访时通过场景识别把新旧地图合并 | "失效→新建→重新接回"最成熟的系统级范式；恢复等于重新开始而非撤销过去，错误合并无通用回滚 |
| [Dynamic Pose Graph SLAM](https://doi.org/10.1109/IROS.2012.6385561) | IROS 2012 | 对同区域不同时刻的激光做变化检测；变化超阈值时删除不再匹配的旧位姿与扫描（可撤销的地图更新） | 唯一直接回答"位姿/地图被推翻后历史数据如何一致"的经典工作；它删的是**过期的正确历史**而非错误约束，且假定当前估计正确 |

### D 组共同假设
1. 错误约束是"少数、彼此独立、残差大"的离群点，内点占多数且自洽（SC / DCS / max-mixtures / GNC / PCM 全建立在此）。
2. 退化与失效短暂且可等待，系统终会回到有信息的区域。
3. 世界几何静态或缓慢变化，"正确"以最新观测为准。

### D 组共同盲区
1. **决策不可逆**：几乎都在"接受/拒绝"时刻一次性提交，没有"检查点 + 全局重算"式的可撤销后端。
2. **从错误收敛中拉回**没有保证：鲁棒后端只保证对离群点不敏感，不保证从已污染初值回到真解。
3. **共谋离群点**（对称结构、动态遮挡造成的重复几何）仍是公认难题。
4. **地图一致性恢复**几乎无人处理。
5. 评价几乎全是最终 ATE，**缺"恢复时间/恢复成功率/撤销代价"**这类自恢复专属指标。

---

## 组 E｜评测方法、指标与基准（12 条，含 2 条与 A/D 重复）

| 论文 / 资源 | 年份 / 出处 | 提供什么 | 对自恢复可测性的意义 |
| --- | --- | --- | --- |
| [Synthetic Datasets for Data-Driven Localization Monitoring](https://proc.logistics-journal.de/article/view/1186) | Logistics Journal: Proceedings 2025, Nr. 21 | 物理仿真中**系统性诱发**动态障碍/无特征/地图歧义并自动打失效标签 | 把"制造坏"标准化；几乎可逐项搬到 Gazebo——是**故障注入协议模板** |
| [Self-Healing Visual Recovery for Autonomous Ground Vehicles](https://arxiv.org/abs/2607.11686) | arXiv 2026（同行评审状态未核验） | 119 次故障注入回合，成功率 86.6%，中位恢复 3.26 s，MAPE-K 闭环嵌在 50 ms 控制周期内 | 目前唯一同时报"恢复率 + 恢复时延"的实证工作，是恢复侧指标的先例；但只报中位数、无检测器指标、无误报代价、无复发率 |
| [LILocBench](https://www.ipb.uni-bonn.de/html/projects/localization_benchmark/) | IROS 2025 | 室内长期定位基准：**2D 激光 + RGB-D + 轮式里程计**，21 序列 3034.8 m，分组 = mapping 1 / static 7 / dynamics 5 / long-term changes 6 / changes+dynamics 2；公开真值在单一全局坐标系（无需轨迹对齐）；附官方 occupancy map 与评测代码 | **与你的平台同模态**，是"仿真结论能否在真实数据上成立"的最短路径；lt_changes_4/5 明确是"与建图序列完全不一致"的区域 |
| [Nothing Stands Still（NSS）](https://arxiv.org/abs/2311.09346) | ISPRS J. P&RS 2025 | 三难度场景，量化跨空间与跨时间的配准泛化 | "变化强度"分级的设计参考（3D 点云，不能直接用于 2D AMCL） |
| [SLAMFuse](https://arxiv.org/abs/2410.04242) | IROS 2024 | 用数据 fuzzing 找关键扰动阈值，做可复现基准与性能诊断 | 阈值扫描（$k^*$）方法学模板，可搬到 Gazebo |
| [Runtime Verification and Field-based Testing for ROS-based Robotic Systems](https://arxiv.org/abs/2404.11498) | IEEE TSE 2024 | ROS 系统的运行时验证与现场测试指南 | 软件层失效（节点崩溃、话题丢帧）与精度退化是两回事，但提供了监控点清单 |
| [Hilti SLAM Challenge](https://arxiv.org/abs/2109.11316)（+ [Hilti-Oxford](https://arxiv.org/abs/2208.09825)） | RA-L 2022 / 2023 | 建筑工地序列，含长走廊等退化场景；毫米级稀疏真值 | 数据用不上（3D、无 2D 激光），但"构造真实退化序列"的思路可借鉴 |
| [Boreas](https://arxiv.org/abs/2203.10168) | IJRR 2023 | 一年重复路线、>350 km、厘米级真值、含 metric localization 排行榜 | 多季节/多会话定位的评测组织方式可借鉴 |
| [NCLT](http://robots.engin.umich.edu/nclt/) | IJRR 2016 | 27 个 session / 15 个月 / 34.9 h / 147.4 km，含关键帧真值协方差 | 长期定位的经典评测集；同样不能直接用于 2D AMCL |
| [MCD: Multi-Campus Dataset](https://arxiv.org/abs/2403.11496) | CVPR 2024 | 三校园、连续时间真值 + 大规模先验地图 | "先验地图 + 定位"的评测组织方式可借鉴 |
| Integrity 综述（同 A 组第 6 条） | Sensors 2025 | 保护级/完好性框架 | 见 A 组 |
| Zhang & Kaess 退化分析（同 D 组第 10 条） | ICRA 2016 | 退化方向分解 | 见 D 组 |

### E 组的核心结论（已核实）
**没有任何一篇同时具备**「检测混淆矩阵 + 恢复成功率 + 恢复时延 + 复发率 + 误报代价」。这就是主线的立足点，也是可以自己做出来的差异化。

### 可直接落到小规模仿真上的最小指标集
见 [HYPOTHESES.zh-CN.md](HYPOTHESES.zh-CN.md) 第 0 节（含每项指标"现在能否计算"的标注）。

---

## 组 B｜全局重定位、绑架机器人与多假设定位
*（待补：侦察进行中）*

## 组 C｜长期/终身定位、地图维护与变化检测（12 篇）

| 论文 | 年份 / 出处 | 机制一句话 | 对自恢复的意义与缺口 |
| --- | --- | --- | --- |
| [Topology-Aware Decision Making for Multi-Session Localization and Mapping](https://arxiv.org/abs/2602.17226) | arXiv 2026 | 在联合位姿图上算谱连通度，识别断连与弱约束区域，只在"结构支撑不足"时触发局部建图与回环 | **最贴近"检测到地图不能支撑定位"的一篇**；但它检测的是"几何约束不足"，不是"环境变了"，对大规模改造导致的语义过时没有建模 |
| [ExelMap: Explainable Element-based HD-Map Change Detection and Update](https://arxiv.org/abs/2409.10178) | arXiv 2024 | 用在线建图 + 过时地图先验，显式定位并提取发生变化的地图**元素** | 把地图更新提升到可解释元素层；离线/数据集驱动，**没有闭环到定位系统** |
| [CDSD: Online Geometric Change Detection via Scene Decomposition](https://arxiv.org/abs/2609.17302) | arXiv 2026 预印本 | 把地图按空间分解成"场景"，只在对应子图之间做稠密局部比较 | 为"在线检测 + 重建"给出工程路径，是 DUFOMap/BeautyMap 离线清理的自然延伸；仍假设子图对齐可信 |
| [DREAM: Dynamic Resilient Spatio-Semantic Memory](https://arxiv.org/abs/2606.00576) | arXiv 2026 预印本 | 在线时空语义体素记忆 + 位姿图感知的记忆剪枝，回环修正后更新历史观测并把记忆控制在有界规模 | 少见的把"记忆过期 + 存储上界 + 变化"放在同一框架；不处理"地图整体不可用"，无多地图切换 |
| [ELite: Ephemerality meets LiDAR-based Lifelong Mapping](https://arxiv.org/abs/2502.13452) | ICRA 2025 | 世界按**两阶段 ephemerality**（两个时间尺度）建模，据此决定地图里保留什么、遗忘什么 | DUFOMap 路线的直接升级对象；**默认可以持续多会话采集**——正是你缺的条件 |
| [OASIS-Map: Object-Level Change Detection in Multi-Session Mapping](https://arxiv.org/abs/2607.14899) | arXiv 2026 预印本 | patch 级稠密语义对应建立时空一致的对象级地图，重访时增量关联对象 | 变化粒度推到对象实例（对应"家具重排"）；对"隔断增删"这类改变自由空间拓扑的改造无专门处理 |
| [Lifelong Localization with Sparse Distance Sampling](https://arxiv.org/abs/2607.17852) | ICRA 2026 | 见 A 组第 7 条 | 文献里最接近"回退到保守定位模式"且有收敛保证的一篇 |
| [Changing-SLAM: Visual Localization and Mapping in Dynamic and Changing Environments](https://arxiv.org/abs/2209.10710) | arXiv 2022 | 贝叶斯滤波 + 长期数据关联；动态关键点过滤保留框内非动态特征，避免特征枯竭导致跟踪丢失 | 少见的"不给定位姿、不知地图"且实时的工作，与你现在**全部实验都给定位姿**形成直接对照 |
| [SEAM: Submap-Anchored Evidence for Lifelong LiDAR Mapping under Trajectory Deformation](https://arxiv.org/abs/2609.18819) | arXiv 2026，**单作者预印本** | 子图级锚定 + 重投影让证据在轨迹被修正后仍可用；用 DOP 置信度抑制几何不可靠的回环边 | 突出贡献是"置信度门槛决定一条约束要不要用"——可迁移到 AMCL 的观测门控；单作者无 venue，**只作参考不作基线** |
| [Pole-Image: Pole-Anchored Descriptor for Long-Term Localization and Map Maintenance](https://arxiv.org/abs/2510.17237) | arXiv 2025，4 页技术报告 | 以杆为锚点，把周围结构编码成"以杆为原点的极坐标图"，显式编码"稳定锚点 vs 变化环境" | 同时服务定位与变化检测；但"锚点稳定"这一假设在结构大改造下被直接击穿，**是很好的批判对象** |
| [When LiDAR Fades, Radar Takes Over](https://arxiv.org/abs/2610.13788) | arXiv 2026 预印本 | 单类时序学习（只用正常数据训练 LSTM-AE）得到 LiDAR 可靠性估计，据此在 LIO/RIO 之间转移定位权 | 把"检测退化 → 切换定位来源"做成闭环的最完整例子；但它**关心传感器退化，不关心地图过时**——是你论文里现成的对照 |
| [SCD4VPR: Multi-modal Scene Change Detection for Long-term VPR Database Update](https://arxiv.org/abs/2604.11402) | arXiv 2026 预印本 | VLM 语义 + 视觉特征跨模态融合，输出多类变化掩码；发布 NYC-CD 基准 | 量化了"不更新则检索大幅下降、更新后恢复（最大间隔 +30.1 R@1）"，是"过期证据必须维护"的硬数据；不闭环到定位精度与恢复决策 |

### C 组共同假设
1. **存在稳定骨架**：除传感器退化那篇外，几乎全部默认"变化之外仍有静态结构/稀疏锚点可锚定"（ELite 靠静态骨架、OASIS-Map 靠结构背景、Pole-Image 靠杆）。**隔断增删攻击的正是这条。**
2. **变化相对于锚点是局部的**：子图切分、元素清单、对象实例、时间尺度分层，本质都是"把变化装进局部容器"，容器之外照旧可用。
3. **变化渐进且可被多次观测**：终身/多会话路线都假设你会反复回来。**一次性的大改造不在它们的设定里。**
4. **对齐本身可信**：变化检测几乎都建立在"跨会话对齐已经做对"的前提上；SEAM 是唯一把对齐可靠性当显式变量的。
5. **更新地图 = 恢复能力**：默认"地图更新好了定位自然就好"，很少保证"更新之前/期间定位还能不能输出"。

### C 组共同盲区
1. **没有"地图不可用"的显式判据**：全都在检测"哪里变了"，没有人给出"当前地图已不足以支撑可信定位"这个判据。
2. **保守/降级模式没有形式化**：只有稀疏距离采样与雷达切换两个兜底例子，且分别限定"平面室内 + 变化类型已学到"与"传感器而非地图"。
3. **没有多地图/地图切换机制**：多会话工作全在"合并成一张图"的范式里，**没有一篇把"保留多张历史地图并按当前可信度选择/融合"当成一等公民**。
4. **地图置信度/过期没有可比度量**：各用各的差异度量（TSDF 变化、ephemerality、对象持久性、DOP），彼此不可比，也都接不到定位协方差上。→ 这是最可能做出统一贡献的地方，且用 AMCL 粒子协方差 + 现有 RMSE 表就能起步。

---

## 未核验线索（**不可引用**，仅备查）

| 线索 | 状态 |
| --- | --- |
| Large-scale Indoor Mapping with Failure Detection and Recovery in SLAM（IEEE 10802593 / Amazon Science 收录） | 标题与存在性已核验；IEEE Xplore 返回空页、Amazon Science 页超时，**机制未核验**。这篇标题与主线最接近，必须优先核实 |
| A Deep-Learning-based Strategy for Kidnapped Robot Problem in Similar Indoor Environment（JIRS 100(3-4):765–775, 2021） | 已核验（作者单位页面）：2D LiDAR + CNN 回归 3-DOF 位姿，约 2 m / 5° 精度，场景分类 98% —— 2D 激光 KRP 的既有做法，作为对照工作记录 |
| Dual-Process LiDAR Localization with Run-Time Mode Switching（MDPI Electronics 15(19):4417） | MDPI 两次 403，**未核验**；与"3D LiDAR ↔ 2D 粒子滤波运行时切换"最贴近，需换渠道核 |
| PL-RAS: Robust Localization with Real-Time Protection Level Calculation（IEEE 11097747） | Xplore 返回空页，**未核验** |
| Egger et al., A systematic literature review on long-term localization and mapping for mobile robots（J. Field Robotics 40(5), 2023, DOI 10.1002/rob.22170） | Wiley 页 403（Cloudflare）、DOI 跳转被拦，**未核验**；作为长期定位综述线索备查 |
