# 可行性评估：这些论文的思路，能不能用现有 Static and dynamic localization recordings 那套仿真验证？

> 历史工作草案。当前实验协议以[研究设计](DESIGN.zh-CN.md)为准。本文中的普遍性研究缺口、原理推断与预计工期不能当作已核验结论；历史厘米级地图对照尚未证明定位失效或自恢复。

**结论先说**：能验证的部分比预期多——因为你的定位平台是 **ROS 2 + nav2_amcl**，而 `nav2_amcl` 会发布**带权重的粒子云**（`nav2_msgs/ParticleCloud`：`header` + `Particle[]`，每个 `Particle` 含 `pose` 与 `weight`；已在 WSL 的 `/opt/ros/humble/share/nav2_msgs/msg/` 与上游 `main` 分支双向核对）。这意味着"失效判据"的大部分特征量**不需要给 AMCL 打补丁**就能从话题里录下来。

但要说清楚两件事，避免自我误导：

1. **现有录像里没有恢复相关的量**。42 次回放录的是轨迹、误差与地图，没有粒子云/权重/注入事件。所以 H1、H4 不是"把旧数据再挖一遍"就能得到，需要**重跑一遍（不改场景、不改世界）**，把内部量补录上。
2. **"大变动"这个轴目前不存在**。现有三档（纯静态 / 三移动箱子 / 干净地图+动态测试）全是"地图不变、世界里有动态物体"。要验证"地图与现状不一致"，必须新增"建图后世界被改"的档位。

---

## 一、平台能力清单（已核对你仓库里的实际配置）

`SLAM-Physical/config/localization.yaml`：

| 项 | 值 | 对自恢复实验的意义 |
| --- | --- | --- |
| 定位器 | `nav2_amcl`（DifferentialMotionModel） | augmented MCL 内置恢复行为可用作基线 |
| 观测模型 | `likelihood_field`，`max_beams: 90`，`laser_max_range: 12.0`，`sigma_hit: 0.15`，`z_hit/z_rand = 0.9/0.1` | 似然场可直接给出"未解释观测"的原始材料 |
| 粒子数 | 500–2000 | 粒子云统计（多峰性/ESS）在 2D 上足够稳定 |
| 更新阈值 | `update_min_d/a = 0.02` | 更新很密，TTR 的时间分辨率足够 |
| 运动噪声 | `alpha1..4 = 0.2` | 需要固定，否则 TTR 分位数会被运行间抖动淹没 |
| **恢复参数** | **未显式配置** `recovery_alpha_slow/fast` | Nav2 默认值为 0.0 / 0.0；0.001 / 0.1 是建议试验值。旧配置不能据此认定恢复已开启；需显式配置并记录运行时参数 |
| 初始位姿 | `set_initial_pose: true`，固定 `{x: 6.25, y: 6.15, yaw: 0.12}` | 每次回放从同一点出发；做 kidnapping 实验时要改成可注入 |

**可直接录、不需要补丁的量**：`/amcl_pose`（含协方差）、`/particle_cloud`（位姿 + 权重）、`/scan`、`/odom`、`/tf`，加上 Gazebo 真值——由此可离线算：有效样本数 $\mathrm{ESS}=1/\sum \tilde w_i^2$、最大权重、粒子云加权协方差、簇数与最大簇占比（多峰性）、粒子云熵、最优粒子似然、扫描残差统计（未解释观测占比及其**空间持久性**）。

**必须新写的东西**：注入事件的时间戳与类型（瞬移 / 初始位姿偏移 / 地图更换）、地图改动比例 $k$ 的定义与记录、恢复动作的触发日志。

---

## 二、三级判定总表

**级别说明**：**A 直接可用** = 现有仿真 + 记录改造即可；**B 需改装** = 要新增场景/模块（通常 1—3 天）；**C 不可用** = 模态、平台或数据条件不满足，只能引用或批判。

| # | 论文 | 级别 | 要做什么 |
| --- | --- | --- | --- |
| 1 | [Sensor Resetting Localization](http://www.cs.cmu.edu/~coral/old/publications/b2hd-icra00-srl.html)（ICRA 2000，AMCL 内置恢复的祖先） | **A** | 录制粒子云 + 真值即可量化"内置恢复"的检测质量与恢复成败；这是主线的**必做基线** |
| 2 | [Degenerate in Whose Frame?（等变性判据）](https://arxiv.org/abs/2608.15532) | **A** | 纯离线：用已录扫描+地图，平移/旋转机体原点，统计 2D 退化判据的标签翻转率 → H5 |
| 3 | [Integrity 综述](https://hal.science/hal-05044835v1)（Sensors 2025） | **A** | 把保护级/完好性框架套到 `/amcl_pose` 协方差上，算"保护级是否被违反"，无需改装 |
| 4 | [Lifelong Localization with Sparse Distance Sampling](https://arxiv.org/abs/2607.17852)（ICRA 2026） | **A（最省事，最推荐）** | Gazebo raycast 采 16 个距离 + 轮式里程计，与现有回放共享场景与真值，做一条"保守兜底模式"基线 |
| 5 | [Synthetic Datasets for Data-Driven Localization Monitoring](https://proc.logistics-journal.de/article/view/1186)（2025） | **A** | 把它的"系统性诱发失效 + 自动打标签"协议搬到 Gazebo 场景矩阵 |
| 6 | [SLAMFuse](https://arxiv.org/abs/2410.04242)（IROS 2024） | **A** | 阈值扫描（$k^*$）方法学，直接用于"改动比例→失效率"曲线 |
| 7 | [LILocBench](https://www.ipb.uni-bonn.de/html/projects/localization_benchmark/)（IROS 2025） | **A（真实数据捷径）** | 2D 激光 + 轮式里程计 + 公开单帧全局真值 + 官方 occupancy map；4 个公开真值序列可直接用 AMCL 跑 |
| 8 | [Dynamic Pose Graph SLAM](https://doi.org/10.1109/IROS.2012.6385561)（IROS 2012） | **B（离现有实验最近）** | "建图后永久改结构 → 变化检测 → 删过期节点 → 重新一致"；需要 2D 位姿图或子图差分 |
| 9 | [CDSD：在线几何变化检测](https://arxiv.org/abs/2609.17302)（2026 预印本） | **B（小改装）** | 把地图切子图做前后差分；AMCL 读同一份栅格即可，是 DUFOMap/BeautyMap 在线化的自然延伸 |
| 10 | [ELite：两阶段 ephemerality](https://arxiv.org/abs/2502.13452)（ICRA 2025） | **B（toy 版可做）** | 把现有三套数据当"伪会话"，验证"保留 vs 遗忘由暂态性决定"；真实多会话做不了 |
| 11 | [Topology-Aware Decision Making](https://arxiv.org/abs/2602.17226)（2026） | **B** | 需导出位姿图并算谱连通度；把"何时该重建地图"变成有原理的触发条件 |
| 12 | [ExelMap：元素级地图变化](https://arxiv.org/abs/2409.10178)（2024） | **B** | 给 Gazebo 场景定义"地图元素清单"并做变化前后标注；AMCL 栅格无元素概念，需外挂一层 |
| 13 | [RTMap](https://arxiv.org/abs/2507.00980) / [SCD4VPR](https://arxiv.org/abs/2604.11402) | **B（借方法不借数据）** | 借"变化检测→地图更新"的闭环结构；SCD4VPR 的量化（不更新则检索下降、更新后 +30.1 R@1）适合当"地图过期必须维护"的论据 |
| 14 | [A General Framework for Lifelong Localization and Mapping](https://arxiv.org/abs/2111.10946)（2021） | **B（弱形式）** | "旧地图 vs 新会话"看更新后 RMSE 是否回落；长期多会话特性无法复现 |
| 15 | [ORB-SLAM3](https://arxiv.org/abs/2007.11898)（T-RO 2021） | **B（改装量小）** | Gazebo 的 RGB-D 流可直接喂；瞬移模拟跟踪丢失，返回已建图区域看重定位与地图合并，作为"多地图"对照 |
| 16 | [RRR](https://doi.org/10.1177/0278364913498910) / [GNC](https://arxiv.org/abs/1909.08605) / [DCS](https://doi.org/10.1109/ICRA.2013.6630557) / [Switchable Constraints](https://doi.org/10.1109/IROS.2012.6385590) / [PCM](https://doi.org/10.1109/ICRA.2018.8460217) / [max-mixtures](https://doi.org/10.1177/0278364913479413) / [MH-iSAM2](https://doi.org/10.1109/ICRA.2019.8793854) | **B（独立一条轨）** | 都需要一个 2D 位姿图后端（离线 g2o/GTSAM + 注入假回环）。可做，但与 AMCL 主线**并行**，两天内不建议同时开 |
| 17 | [DARE-SLAM](https://arxiv.org/abs/2102.05117) / [LTA-OM](https://doi.org/10.1002/rob.22337) / [X-ICP](https://arxiv.org/abs/2211.16335) / [LiLi](https://arxiv.org/abs/2609.17145) / [LF-GICP](https://arxiv.org/abs/2608.19522) / [Informed-Constrained-Aligned](https://arxiv.org/abs/2408.11809) | **B（部分）** | 都是 3D 配准/退化方向的工作，与 2D 似然场不同构。可做"同构 2D 版"（2×2 信息矩阵的方向各向异性、扰动-重优化判据），但不是复现原文 |
| 18 | [Zhang & Kaess 退化分析](https://doi.org/10.1109/ICRA.2016.7487211)（ICRA 2016） | **B** | AMCL 无分解信息矩阵；最小可行版是给 2D 激光配扫描匹配 + 谱分析 |
| 19 | [Introspective Perception](https://arxiv.org/abs/2306.16698) / [CPIP](https://arxiv.org/abs/2109.13974) | **B** | 干净地图 vs 动态测试的扫描一致性正是它要的冗余信号；但需把自省模块接到 AMCL 观测似然上，并自定"任务级失败"标签 |
| 20 | [When LiDAR Fades, Radar Takes Over](https://arxiv.org/abs/2610.13788)（2026） | **B（只借思想）** | 没有雷达、且需时序训练；"可靠性门控 + 降级切换"的范式可搬到"地图不可信 → 降级" |
| 21 | [DELO](https://arxiv.org/abs/2308.07153)（ICCV 2023 W） | **C** | 需训练与序列级数据；141 帧 KITTI teaser 只能做定性观察 |
| 22 | [Pole-Image](https://arxiv.org/abs/2510.17237)（2025，4 页报告） | **C（作批判对象）** | Gazebo 室内无杆状地标，且没有移动平台沿杆采集；它的"稳定锚点"假设正是大改造击穿的那条 |
| 23 | [SEAM](https://arxiv.org/abs/2609.18819)（单作者预印本） | **C（只作参考）** | 两会话 + 轨迹变形 + DOP 门控，复现成本高、无同行评审 |
| 24 | [OASIS-Map](https://arxiv.org/abs/2607.14899) / [DREAM](https://arxiv.org/abs/2606.00576) | **C（toy 可试）** | 对象级变化检测需 RGB-D 语义分割与 patch 对应；D435i 可做小规模，但短期不划算 |
| 25 | [NSS](https://arxiv.org/abs/2311.09346) / [Boreas](https://arxiv.org/abs/2203.10168) / [NCLT](http://robots.engin.umich.edu/nclt/) / [MCD](https://arxiv.org/abs/2403.11496) / [Hilti](https://arxiv.org/abs/2109.11316) | **C（借评测组织方式）** | 3D / 驾驶 / 大场地数据集，与 2D AMCL 不同模态；只有评测协议与"变化分级"的设计可借鉴 |

---

## 三、三件现在就能做、且成本最低的事

### C1. 等变性实验（H5，纯离线，零场景成本）
用已录的静态回放（扫描 + 地图），在机体原点平移/旋转的多个取值下计算 2D 退化判据（扫描匹配的 Hessian 谱、或 $2\times2$ 信息矩阵的广义特征值），统计标签翻转率，再换算成"会多触发多少次无效恢复"。
**为什么值得第一批做**：如果翻转率显著，你就拿到了"现有失效信号不可信"的**本平台证据**，后面所有"用退化标签触发恢复"的方案都要先过这一关。

### C2. 内置恢复基线量化（H4，只需补录，不改场景）
重跑现有三档场景，额外录 `/particle_cloud`（权重）与真值，算：ESS / 最大权重 / 簇数的时间曲线 vs 真实误差曲线；统计**"粒子云已收敛但真值误差仍大"（unreliable-but-stable）的时段占比**，并对比静态 vs 动态场景。
**为什么值得做**：这是全组文献都缺的"恢复成功判据"问题，而你的系统里现成有这个机制却从没被量化过——低成本、高差异化。

### C3. 地图过期曲线（H1/H6，需要新增一个轴）
先做最省的版本：**直接编辑 `map` 的 pgm/yaml**（在走廊段抹掉/加一堵墙），不重建世界、不重建 Gazebo，只在同一段测试轨迹上跑 AMCL，扫 $k = 0/25/50/75/100\%$。
得到"改动比例 → RMSE/失效率/ESS/未解释观测占比"的曲线。若时间允许，再用"建图后改 Gazebo 世界"复现一次，确认 map 编辑版的结论方向一致。

---

## 四、优先复现建议（若只做三件）

1. **`nav2_amcl` 内置恢复（SRL, ICRA 2000）** —— 免费的基线，不量化它，后面所有"我的恢复更好"都没有对照。
2. **[arXiv:2607.17852](https://arxiv.org/abs/2607.17852)（ICRA 2026，稀疏距离采样 + 里程计）** —— 与你的场景/真值完全共享，实现最省，且它是文献里少见的"失效后在线重建可信定位并有收敛证明"的方案；正好用来检验"保守兜底模式"能到什么程度。
3. **[arXiv:2608.15532](https://arxiv.org/abs/2608.15532)（等变性）** —— 零成本，直接支撑主线的立论（检测侧不可信）。

**真实数据验证**：如果两天内有余力，把同一套指标协议搬到 **LILocBench** 的 4 个公开真值序列（`mapping / static_0 / dynamics_0 / lt_changes_0 / lt_changes_dynamics_0`，`bagfiles_no_cams` 体积很小，例如 `dynamics_0` 约 38 MB、`lt_changes_0` 约 104 MB），用官方 occupancy map 直接喂 AMCL。这能把"仿真里的结论"升级为"真实数据上成立"，成本主要是下载与话题适配。

### 补充：B 组核验后新增的两条同构基线（都属于 A 级）

| 论文 | 级别 | 为什么与你的平台同构 | 它不做什么（你的机会） |
| --- | --- | --- | --- |
| [TIM 2026：稀疏可行假设采样 + 批量多阶段推断的 KRP 重定位](https://arxiv.org/abs/2511.01219)（DOI 10.1109/TIM.2026.3694741） | **A** | 单帧 2D LiDAR vs 占据栅格；RRT 生成稀疏可行位置假设 + SMAD 粗筛 + TAM 度量，**明确针对平移不确定性、非全景扫描与环境变化下的似然场退化**；成功率较最强基线 +26.9 个百分点 | 不判断"何时该触发"，也不报告恢复是否成功；场景只做一次性重定位，不涉及持续运行中的自恢复 |
| [AdaM-MCL / DSOM](https://arxiv.org/abs/2009.00211)（RA-L 2021，[开源](https://github.com/Runjian-Chen/AdaM_MCL)） | **B**（需训练采样模型） | 学习可采样的多模态观测模型再嵌入 MCL，面向**长期变化**环境；与你的粒子滤波栈直接对接 | 同样没有失效检测与恢复确认；训练依赖仿真数据 |

这两条把"全局重定位"这一环的基线抬高了，因此在做对照实验时，**建议把"最好的重定位"当作强基线之一**，而你提出的策略要在"触发时机 + 恢复确认 + 复发率"上体现差异，而不是在纯重定位成功率上比拼。

---

## 五、明确做不了的事（写清楚，避免被面试问穿）

- **多会话采集**：ELite / SEAM / OASIS-Map / DREAM 依赖反复重访与跨会话对齐，你没有移动机器人、也没有长期多会话数据；只能用 Gazebo"伪会话"做 toy 版，必须标注为 toy。
- **3D 配准类方法的原生复现**：X-ICP / LiLi / LF-GICP / DARE-SLAM / LTA-OM 需要 3D LiDAR 序列与 3D 栈；你只有 141 帧 KITTI teaser 与固定安装的 Unitree L2，做不了移动采集。只能做"2D 同构版"。
- **学习类方法**：DELO、雷达切换那篇、SCD4VPR 需要训练数据/多模态传感器，短期不可行。
- **因子图撤销类方法**：RRR / GNC / DCS / SC / PCM / max-mixtures / MH-iSAM2 都需要先有一个 2D 位姿图后端——这是一条**独立的轨**，与 AMCL 主线并行才会快；两天内同时开两条线，结果大概率是两条都半成品。
