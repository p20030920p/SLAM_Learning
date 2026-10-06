<div align="center">

# 候选论文目录 Candidate catalog

**87 条候选，每条都有公开代码，每个仓库都实测可达。按「有库 → 纯 CPU → 不要 ROS 1 → 数据免注册」四条筛，22 条全过。**

![candidates](https://img.shields.io/badge/candidates-87%20with%20public%20code-1c7ed6)
![verified](https://img.shields.io/badge/repos-87%2F87%20fetched%20live-2ea043)
![venue](https://img.shields.io/badge/venue-77%2F87%20IEEE%20or%20Elsevier%20RAS-6f42c1)

[怎么来的](#怎么来的) &nbsp;•&nbsp; [第一梯队](#第一梯队22-条四条全过) &nbsp;•&nbsp; [按方向](#按方向) &nbsp;•&nbsp; [不建议复现](#不建议复现17-条) &nbsp;•&nbsp; [开放问题](OPEN_PROBLEMS.md)

*[仓库主页](../README.md) &nbsp;•&nbsp; [复现区](README.md) &nbsp;•&nbsp; [分析笔记](NOTES.md) &nbsp;•&nbsp; [论文报告值](PAPER_BASELINES.md)*

</div>

## 怎么来的

这一页针对的是一个具体的问题：任务书 §2 选中的论文里，**有 7 篇根本没有官方代码**
（TerrainNet、DuLoc、X-ICP、Switch-SLAM、Active Illumination、DynPurge、OJ-ITS 2025），
按本仓库「没有库就不复现」的规则直接出局；剩下有库的里面，又有一批是 ROS 1 only 或者数据要注册。

所以这次换了顺序：**先立门槛，再看论文**。不先找「重要的工作」，先找「能在这里跑起来的工作」。

| 门槛 | 为什么立这一条 |
| :--- | :--- |
| **1 · 作者自己的公开代码** | 本仓库的硬规则。没有库的论文不进目录，不管它多重要。 |
| **2 · 纯 CPU 能跑** | 本机没有 CUDA GPU（20 核 / 15 GB 内存 / 251 GB 空闲）。 |
| **3 · 不需要 ROS 1** | 本机是 ROS 2 Jazzy，没有 docker 也没有 sudo。ROS 1 要建 micromamba 环境，是真实成本，不是「跑不跑得动」的问题。 |
| **4 · 数据免注册** | KITTI / SemanticKITTI 那类注册墙已经拖慢过 01-01 与 01-05，是第三条共同的坎。 |

**核验方式 —— 这一页和通常的「论文推荐」不同的地方：**

1. 87 个仓库**逐一实测**，记下真实元数据：HTTP 状态、星标数、最近提交日期、是否归档、有没有许可证文件。
   URL 不是从论文标题猜出来的，**87/87 全部可达，0 个编造**。
2. 抽查了 agent 自报的星标数与实测值的一致性：**82 条里有 81 条对得上**（唯一一条偏差见 `8bit-nyk/hslam_ros2`，
   自报 25、实测 8）。也就是说表里的仓库元数据可以直接信。
3. 检索做了**两轮独立**（不同 agent、不同检索路径）。两轮都命中的 11 条在表里标了 **⟳**，这几条最值得先看。
4. 又抽查了 agent 对「仓库最近还在动」这类时间声明：7 条里 6 条与抓到的提交日期相符，
   唯一不相符的是 `8bit-nyk/hslam_ros2`（自报「3 天前有提交」，实测最后提交是 2025-07-23），**已按实测值改写**。

| 统计 | 数量 |
| :--- | ---: |
| 候选总数 | 87 |
| 仓库实测可达 | 87 |
| IEEE RAS venue（ICRA / IROS / RA-L / T-RO / CASE） | 68 |
| Elsevier *Robotics and Autonomous Systems* | 7 |
| 其他 IEEE / RAS 相关 | 2 |
| **RAS 相关合计** | **77 / 87** |
| 四条门槛全过（第一梯队） | 22 |
| 本机能跑但有代价（第二梯队） | 48 |
| 本机做不了（不建议） | 17 |

> **门槛里的「ROS 1」值得单独说一句。** 本仓库已经有 `reproductions/tools/ros1_env.sh` 与
> `build_ros1_catkin.sh`，ERASOR / Removert / LT-mapper 就是这么跑起来的。所以 ROS 1 **不是不能做**，
> 而是每条要多花半天到一天。第二梯队里有 30 条属于这一档 —— 它们是本仓库扩充时性价比最高的一批。

## 怎么读这几张表

| 符号 | 含义 |
| :--- | :--- |
| ✅ | 代码 / CPU / 无 ROS 1 / 数据免注册，四条全过，可以直接开工 |
| 🟡 | 本机能跑，但有代价，代价写在「门槛」列里 |
| ⛔ | 本机做不了，原因写在「拦在哪」列里 |
| **⟳** | 两轮独立检索都命中了同一个仓库，可信度最高 |
| ★ | GitHub 星标数，实测值，不是自报 |
| 最近提交 | 该仓库最后一次提交的年月，用来看它是不是已经没人维护 |

---

<!-- 本文件的表格由已验证的候选集生成；改动请改数据，不要手改表格。 -->

## 第一梯队：22 条四条全过

这一档可以直接开工：clone 下来就能编，数据不用申请，不需要容器。

| 论文 | venue | 仓库 | ★ | 最近提交 | 为什么值得做 |
| :--- | :--- | :--- | ---: | :--- | :--- |
| GLIM: 3D Range-Inertial Localization and Mapping wit… | Elsevier Robotics and Autonomous S… | [koide3/glim](https://github.com/koide3/glim) | 1858★ | 2026-09 | 这是台账缺失的后端：固定滞后平滑里程计、关键帧与子图因子、直接最小化子图间配准误差的全局轨迹优化，外加手动回环校正、多会话合并与离线地图编辑器，全部基于因子图与 ROS 2；CPU 运行只是配置开关。 |
| DM-VIO: Delayed Marginalization Visual-Inertial Odom… | IEEE RA-L 2022 | [lukasvst/dm-vio](https://github.com/lukasvst/dm-vio) | 1235★ | 2024-10 | 典型的纯 CPU 稠密光度视觉惯性系统，发表于 RAS，方法与评估工具都在作者仓库里，且无需 ROS；延迟边缘化加位姿图 BA 是已复现目录未覆盖的机制，也是 ORB-SLAM3 类条目最强的非特征法对照。 |
| Hydra: A Real-time Spatial Perception System for 3D … | RSS 2022 | [MIT-SPARK/Hydra](https://github.com/MIT-SPARK/Hydra) ⟳ | 1172★ | 2026-01 | D2 最干净：唯一把 Ubuntu 24.04 + ROS 2 Jazzy 列为已测试配置的候选；它构建四层场景图，用嵌入形变图做分层回环，整条 ESDF/place/room 流水线都是 CPU C++。 |
| CT-ICP: Real-time Elastic LiDAR Odometry with Loop C… | IEEE ICRA | [jedeschaud/ct_icp](https://github.com/jedeschaud/ct_icp) | 907★ | 2022-07 | 连续时间弹性轨迹表示：每次扫描内位姿连续，从而消除运动畸变，并在其上做回环；MIT 许可、独立、很适合 20 核 CPU，是已复现的点式 KISS-ICP 的干净补充。 |
| KISS-Matcher: Fast and Robust Point Cloud Registrati… | IEEE ICRA 2025 | [MIT-SPARK/KISS-Matcher](https://github.com/MIT-SPARK/KISS-Matcher) | 792★ | 2026-08 | 台账缺少的可复用前端原语：靠图论不变量（ROBIN）与 TEASER++ 估计，在极高离群率与极小重叠下仍稳健的全局配准，仅用 CPU 即达亚度旋转与亚厘米平移误差，并以 C++ 库或 pip 包发布。 |
| TARE: A Hierarchical Framework for Efficiently Explo… | RSS 2021 | [caochao39/tare_planner](https://github.com/caochao39/tare_planner) | 734★ | 2024-06 | 唯一在 Ubuntu 24.04 加 ROS 2 Jazzy 上经 README 测试的候选，因此搭建成本近乎为零；地面机器人分层探索器，纯 CPU，无数据集门槛。 |
| Swarm-SLAM: Sparse Decentralized Collaborative Simul… | IEEE RA-L 2024 | [MISTLab/Swarm-SLAM](https://github.com/MISTLab/Swarm-SLAM) ⟳ | 711★ | 2025-04 | 唯一活跃、MIT 许可、真正基于 ROS 2 的协作视觉/LiDAR SLAM 栈，适配 Jazzy 与 CPU 运行；它覆盖已复现目录未触及的多机器人/多会话轴，机器人间回环优先级值得单独设目录。 |
| A Robust Approach for LiDAR-Inertial Odometry Withou… | IEEE RA-L 2026 | [PRBonn/rko_lio](https://github.com/PRBonn/rko_lio) | 672★ | 2026-10 | 三道门槛全过：RA-L 2026、MIT、零 CUDA，可用 pip 无 ROS 运行，也可作 Jazzy 节点；延续同组 KISS-ICP 的 CPU 路线，一套配置覆盖旋转式、固态与手持 LiDAR。 |
| KISS-SLAM: A Simple, Robust, and Accurate 3D LiDAR S… | IROS 2025 | [PRBonn/kiss-slam](https://github.com/PRBonn/kiss-slam) | 533★ | 2025-12 | 唯一跨过三道门槛的候选：作者提供 pip 可安装的建图与回环代码，不需要 ROS 1 或 CUDA，另有 rko_slam 的 ROS 2 Jazzy 多会话对齐路径。 |
| OKVIS2-X: Open Keyframe-based Visual-Inertial SLAM C… | IEEE Transactions on Robotics | [ethz-mrl/OKVIS2-X](https://github.com/ethz-mrl/OKVIS2-X) | 413★ | 2026-03 | 最强会场跨过三道门槛：T-RO 2025、BSD-3、无 GPU、ROS 2 Jazzy 就绪；它为纯 CPU 提供 VI-SLAM 基线加稠密体积占据地图，关掉子图与 IMU 即退化为 OKVIS2。 |
| MAD-ICP: It Is All About Matching Data - Robust and … | IEEE RA-L 2024 | [rvp-group/mad-icp](https://github.com/rvp-group/mad-icp) | 334★ | 2026-02 | 成本最低的条目：pip install mad-icp，无 ROS、无 CUDA；informed odometry 逐关键帧度量自身数据关联质量，为 KISS-ICP 系条目提供第二个 CPU 基线。 |
| G3Reg: Pyramid Graph-Based Global Registration Using… | IEEE Transactions on Automation Sc… | [HKUST-Aerial-Robotics/G3Reg](https://github.com/HKUST-Aerial-Robotics/G3Reg) | 330★ | 2025-05 | 无初始位姿的全局配准是描述子论文含糊带过的重定位另一半；这项工作是纯 CPU C++，带开放基准与演示点云对，提供无 GPU、无 ROS、MIT 许可且模块可分开测试的配准后端。 |
| S-Graphs 2.0 - A Hierarchical-Semantic Optimization … | IEEE RA-L 2025 | [snt-arg/lidar_situational_graphs](https://github.com/snt-arg/lidar_situational_graphs) ⟳ | 323★ | 2026-07 | 唯一同时满足 IEEE RA-L 论文、Jazzy 上 ROS 2 原生、文档说明可纯 CPU 运行的候选；它从 LiDAR 给出关键帧到房间与楼层的四层语义图并做分层回环。 |
| OverlapTransformer: An Efficient and Yaw-Angle-Invar… | IEEE RA-L 2022 | [haomo-ai/OverlapTransformer](https://github.com/haomo-ai/OverlapTransformer) | 294★ | 2024-07 | 少见的能在无 GPU 条件下复现的 transformer 位置识别论文：预训练 KITTI 权重已提交进仓库，描述子提取与 PR/topN 评估都能在 CPU 上重跑，Haomo 序列另提供反向视角测试。 |
| Continuous-Time Radar-Inertial and Lidar-Inertial Od… | IEEE T-RO | [utiasASRL/steam_icp](https://github.com/utiasASRL/steam_icp) | 270★ | 2026-02 | 一个代码库涵盖 STEAM-LO/LIO/RO/RIO：用白噪声加速度高斯过程运动先验做连续时间雷达与 LiDAR 惯性里程计；它同时覆盖 4D 雷达与连续时间两个领域，纯 CPU 且代码完整。 |
| Narrowing your FOV with SOLiD: Spatially Organized a… | IEEE RA-L 2024 | [sparolab/SOLiD](https://github.com/sparolab/SOLiD) ⟳ | 210★ | 2025-05 | 一次跨过三道门槛，成本最低的真实复现：无 GPU、无 ROS、无学习权重、无需下载数据集，20 核 CPU 几分钟内可重算描述子与初始航向搜索；它补上台账缺失的受 FOV 约束全局描述子。 |
| CoLRIO: LiDAR-Ranging-Inertial Centralized State Est… | IEEE ICRA 2024 | [zhongshp/Co-LRIO](https://github.com/zhongshp/Co-LRIO) | 119★ | 2025-03 | ROS 2、无 GPU、自包含的协作状态估计包，数据集是普通的 Hugging Face 下载；它用 UWB 相对观测做 LiDAR-测距-惯性融合而非相机回环，并带显式的离群点剔除/GNC 后端。 |
| 3D VSG: Long-term Semantic Scene Change Prediction t… | IEEE ICRA 2023 | [ethz-asl/3d_vsg](https://github.com/ethz-asl/3d_vsg) | 102★ | 2023-07 | 唯一依赖文件明确锁定 CPU 的候选，用小型 GCN/transformer 补上 D2 的对象级变化位置，20 核 15 GB 上数小时即可复现；3RScan 虽在不复现名单中，但那是数据集论文而非本工作。 |
| DeRO: Dead Reckoning Based on Radar Odometry With Ac… | IEEE/RSJ IROS | [hoangvietdo/dero](https://github.com/hoangvietdo/dero) | 92★ | 2025-10 | 该工作用 4D FMCW 雷达多普勒速度加陀螺做递推，用雷达距离与加速度计做更新，构成随机克隆 EKF；计算量很轻，RAS 会场的全开放 C++，且 4D 毫米波雷达是已复现清单中缺失的模态。 |
| Visual place recognition for aerial imagery: A surve… | Elsevier Robotics and Autonomous S… | [prime-slam/aero-vloc](https://github.com/prime-slam/aero-vloc) | 81★ | 2024-11 | 综述那一半的答案：一篇 Elsevier RAS 综述，作者不只给论文列表，还附带自己可用的基准框架；aero-vloc 是 Apache-2.0、可用 CPU，把综述的核心问题变成可运行的实验。 |
| SubT-MRS Dataset: Pushing SLAM Towards All-weather E… | IEEE/CVF CVPR | [superxslam/Robustness_Metric](https://github.com/superxslam/Robustness_Metric) | 49★ | 2025-08 | 实现论文的鲁棒性指标：基于 RPE 的精度/完整度曲线与 AUC，补上了 ATE/RPE 对间断与发散的盲区；在 CPU 上数秒即完成，可作为已复现系统之外的额外评分层直接接入。 |
| Bag-of-Word-Groups (BoWG): A Robust and Efficient Lo… | IEEE/RSJ IROS 2025 | [EdgarFx/BoWG](https://github.com/EdgarFx/BoWG) | 22★ | 2025-07 | 2025 年 RAS 会场的位置识别论文，在纯 CPU 上完全可复现：只有 C++、无 ROS、无 GPU、BSD-3；仓库把词组构建、相似度方面与时序几何后验证作为库、演示与词表训练工具给出。 |

## 第二梯队：48 条本机能跑但有代价

左边一列写明代价：`ROS 1` 表示要建 micromamba 环境（本仓库 `reproductions/tools/ros1_env.sh` 已经会用），`数据要注册` 表示数据集要申请或走网盘，`CPU 存疑` 表示作者只在更强机器上报过时间。

| 论文 | venue | 仓库 | ★ | 最近提交 | 代价 | 为什么值得做 |
| :--- | :--- | :--- | ---: | :--- | :--- | :--- |
| FUEL: Fast UAV Exploration Using Incremental Frontie… | IEEE RA-L 2021 | [HKUST-Aerial-Robotics/FUEL](https://github.com/HKUST-Aerial-Robotics/FUEL) ⟳ | 1486★ | 2024-11 | ROS 1 | frontier 信息结构探索加分层规划器的经典开源实现，1486 星、GPL-3.0，自 2021 年起明确无 GPU，是任何信息路径规划条目都可对照的最安全基线；它也是多数后续 UAV 探索器的祖先。 |
| BALM 2.0: Bundle Adjustment for LiDAR Mapping (effic… | T-RO | [hku-mars/BALM](https://github.com/hku-mars/BALM) | 946★ | 2024-08 | ROS 1 | 用标准引用与一个无需下载数据集即可运行的合成基准填补 LiDAR 捆集调整的位置，20 核 CPU 就能复现其一致性结果。 |
| RACER: Rapid Collaborative Exploration with a Decent… | IEEE T-RO 2023; 2023 T-RO Best Pap… | [Robotics-STAR-Lab/RACER](https://github.com/Robotics-STAR-Lab/RACER) | 799★ | 2024-11 | ROS 1 + 数据要注册 | T-RO 最佳论文奖的去中心化多机器人探索，带均衡覆盖路径；多进程仿真适合 20 核；为台账加入区别于单 UAV FUEL 的多智能体条目。 |
| STD: A Stable Triangle Descriptor for 3D Place Recog… | IEEE ICRA 2023 | [hku-mars/STD](https://github.com/hku-mars/STD) | 743★ | 2023-04 | ROS 1 + 数据要注册 | 这里是星标最多的纯 CPU 3D 位置识别描述子；在 KITTI 上确定、几何式且无需注册，因此仍是一个强验证基线。 |
| Voxel-SLAM: A Complete, Accurate, and Versatile LiDA… | T-RO / arXiv | [hku-mars/Voxel-SLAM](https://github.com/hku-mars/Voxel-SLAM) | 688★ | 2025-04 | ROS 1 + 数据要注册 | 一次覆盖四个领域：多会话回环、滑动窗口与分层 LiDAR BA、发散检测、高效体素地图；纯 CPU，且有公开测试数据。 |
| Dynablox: Real-time Detection of Diverse Dynamic Obj… | IEEE RA-L 2023 | [ethz-asl/dynablox](https://github.com/ethz-asl/dynablox) ⟳ | 604★ | 2025-03 | ROS 1 | 本领域星标最高、许可最干净的动态场景条目（BSD-3），全程无学习，CPU 上最易推理；它维护体素地图与逐对象动态状态，在拥挤真实场景中标记运动物体，自带评估工具与数据集，纯 CPU 复现可被打分。 |
| SR-LIO: LiDAR-Inertial Odometry with Sweep Reconstru… | IROS | [ZikangYuan/sr_lio](https://github.com/ZikangYuan/sr_lio) | 555★ | 2025-08 | ROS 1 | 检验这里其他工作都没做的 CPU 专用杠杆：通过重建扫描把 LIO 更新率提高到扫描率之上，使 20 核在无 GPU 的情况下超过扫描率 iEKF。 |
| LTA-OM: Long-Term Association LiDAR-Inertial Odometr… | Journal of Field Robotics 2024 | [hku-mars/LTAOM](https://github.com/hku-mars/LTAOM) | 509★ | 2024-10 | ROS 1 + 数据要注册 | 显式的多会话终身模式，消费先验地图、先验关键位姿与先验 STD 数据库；JFR 2024 会场、509 星、纯 CPU，为台账补上会话关联这一环。 |
| MapEval: Towards Unified, Robust and Efficient SLAM … | IEEE RA-L | [JokerJohn/Cloud_Map_Evaluation](https://github.com/JokerJohn/Cloud_Map_Evaluation) | 489★ | 2026-03 | 数据要注册 | 实现 AC、COM、Chamfer、MME 以及新的 AWD 与 SCS 最优传输指标；只需要估计地图与 GT 地图，因此纯 CPU 运行，为仓库在 DUFOMap/BeautyMap 之外补上地图质量层。 |
| Structure PLP-SLAM: Efficient Sparse Mapping and Loc… | IEEE ICRA 2023 | [PeterFWS/Structure-PLP-SLAM](https://github.com/PeterFWS/Structure-PLP-SLAM) | 476★ | 2026-07 | 数据要注册 | 以几乎零环境税跨过三道门槛：无 GPU、无 ROS、无需注册，词袋内置；一套二进制覆盖单目、双目与 RGB-D，2026 年仍在修复问题，是已复现纯点特征基线的结构对应物。 |
| COVINS-G: A Generic Back-end for Collaborative Visua… | IEEE ICRA 2023 | [VIS4ROB-lab/covins](https://github.com/VIS4ROB-lab/covins) | 461★ | 2023-05 | ROS 1 + 数据要注册 | 唯一直接针对异构团队与地图合并一侧的候选：同一个服务器后端在一次任务中合并来自不同 VIO 前端的地图，全部在 CPU 上用公开数据集；整个系统都已内置，边际成本只是协作后端与通信层。 |
| Swarm-LIO2: Decentralized, Efficient LiDAR-inertial … | IEEE Transactions on Robotics | [hku-mars/Swarm-LIO2](https://github.com/hku-mars/Swarm-LIO2) | 460★ | 2026-01 | ROS 1 + 数据要注册 | T-RO 2025 的去中心化集群 LiDAR 惯性里程计，带因子图全局外参标定、边缘化与 UDP 通信模块；仓库更新到 2026 年，纯 CPU。 |
| DynaVINS: A Visual-Inertial SLAM for Dynamic Environ… | IEEE RA-L 2022 | [url-kaist/dynaVINS](https://github.com/url-kaist/dynaVINS) | 447★ | 2025-08 | ROS 1 | 这是本集中的刻意反例：它从不删点，而是让估计器对动态点鲁棒，补上被移除式启发法占满的 D1 所需的“穿过人群做估计”基线；视觉惯性拓宽了原本全是 LiDAR 的传感器轴，VIODE 序列可按动态密度分级扫描。 |
| Effectively Detecting Loop Closures using Point Clou… | ICRA 2024 | [PRBonn/MapClosures](https://github.com/PRBonn/MapClosures) | 444★ | 2026-08 | 数据要注册 | 能挺过运动物体与外观变化的会话关联是终身地图合并的前提；零 ROS 与 GPU 门槛，MIT 许可，且在 2026 年仍在维护。 |
| LiLoc: Lifelong Localization using Adaptive Submap J… | IEEE ICRA 2025 | [Yixin-F/LiLoc](https://github.com/Yixin-F/LiLoc) ⟳ | 418★ | 2025-03 | ROS 1 + 数据要注册 | 它攻的是点清理论文忽略的长期维护一半：保留一个中心会话并主动生成、选择与退役先验子图，使内存有界；dataManager 与 egoOptimization 等关键模块都在代码树内。 |
| MS-Mapping: An Uncertainty-Aware Large-Scale Multi-S… | ICRA@40 2024 | [JokerJohn/MS-Mapping](https://github.com/JokerJohn/MS-Mapping) | 386★ | 2025-08 | ROS 1 + 数据要注册 | 会话合并是台账缺失的另一半：分布感知的关键帧选择加协方差加权位姿图融合，纯 CPU，已被 RAS 接收，且仍在活跃开发。 |
| Kinematic-ICP: Enhancing LiDAR Odometry with Kinemat… | IEEE ICRA 2025 | [PRBonn/kinematic-icp](https://github.com/PRBonn/kinematic-icp) | 333★ | 2025-07 | 数据要注册 | 唯一 ROS 支持与目标完全吻合的候选（README 点名 Jazzy），不需要 GPU，并带来其他条目没有的硬运动学先验：ICP 内部在 LiDAR 与轮式里程计之间动态重加权，动机正是退化的弱特征走廊。 |
| DCL-SLAM: A Distributed Collaborative LiDAR SLAM Fra… | IEEE Sensors Journal | [zhongshp/DCL-SLAM](https://github.com/zhongshp/DCL-SLAM) | 324★ | 2025-03 | ROS 1 | 分布式集群 LiDAR SLAM，其三个可互换的全局描述子（Scan Context、M2DP、LiDAR Iris）在 CPU 上检验带宽感知的协作位置识别。 |
| BoW3D: Bag of Words for Real-Time Loop Closing in 3D… | IEEE RA-L 2023 | [YungeCui/BoW3D](https://github.com/YungeCui/BoW3D) | 318★ | 2023-05 | ROS 1 + 数据要注册 | 零 GPU 的回环与重定位，社区采用度高；核心库无需 ROS 即可编译，KITTI 无需注册，最坏情况只是一个 micromamba 环境。 |
| UV-SLAM: Unconstrained Line-based SLAM Using Vanishi… | IEEE RA-L 2022 | [url-kaist/UV-SLAM](https://github.com/url-kaist/UV-SLAM) | 302★ | 2023-08 | ROS 1 + 数据要注册 | 不需要 GPU，数据可直接下载，唯一代价是台账已接受的 ROS 1 环境；它是无曼哈顿世界假设的线特征结构 SLAM 中最强的纯 CPU 答案，用消失点残差加 Fisher 信息可观测性论证。 |
| R-VIO2: Square-Root Robocentric Visual-Inertial Odom… | IEEE RA-L | [rpng/R-VIO2](https://github.com/rpng/R-VIO2) | 292★ | 2024-09 | ROS 1 | 为一个原本由 LiDAR 与动态地图系统主导的 CPU 台账加入带在线时空标定的单目增量 VIO。 |
| OKVIS2: Realtime Scalable Visual-Inertial SLAM with … | IEEE/RSJ IROS | [ethz-mrl/okvis2](https://github.com/ethz-mrl/okvis2) | 237★ | 2025-12 | 数据要注册 | 这里是唯一能在目标操作系统与 ROS 2 Jazzy 上构建、无需 CUDA 也无需容器的顶级 VIO；完整的关键帧 VI-SLAM 加回环，而不是一个库。 |
| Distributed Certifiably Correct Pose-Graph Optimizat… | IEEE T-RO 2021 | [mit-acl/dpgo](https://github.com/mit-acl/dpgo) | 205★ | 2023-04 | 数据要注册 | 纯 CPU 台账最干净的条目：分布式求解器、鲁棒 GNC 变体、异步版本与全部基准图都在一个 MIT 许可的 C++ 仓库里；它也是 Kimera-Multi、Swarm-SLAM 式后端所依赖的理论骨干。 |
| LOG-LIO: A LiDAR-Inertial Odometry with Efficient Lo… | RA-L | [tiev-tongji/LOG-LIO](https://github.com/tiev-tongji/LOG-LIO) | 185★ | 2024-05 | ROS 1 | 典型的 CPU 低成本平面/边缘关联加高效局部几何信息估计；是拿地图表示成本与 KISS-ICP 对比的可控基线。 |
| GroundSLAM: A Robust Visual SLAM System for Warehous… | IEEE ICRA | [sair-lab/GroundSLAM](https://github.com/sair-lab/GroundSLAM) | 151★ | 2026-07 | ROS 1 + 数据要注册 | 最干净的全 CPU 目录：没有深度前端、没有 GPU、自包含的里程计加回环加地图复用，可作为对特征法台账的 CPU 基线。 |
| SG-SLAM: Leveraging Semantic Graphs for Efficient an… | IROS | [nubot-nudt/SG-SLAM](https://github.com/nubot-nudt/SG-SLAM) | 150★ | 2025-10 | 数据要注册 | 这里是唯一在语义图上做回环、重定位与 PGO 的 2025 时代仓库，纯 CPU、MIT、同时支持 ROS1 与 ROS2；它补上已复现系统缺失的全局一致性层。 |
| Multi-Mapcher: Loop Closure Detection-Free Heterogen… | IEEE Transactions on Intelligent V… | [url-kaist/multi-mapcher](https://github.com/url-kaist/multi-mapcher) | 144★ | 2026-08 | 数据要注册 | 本批唯一跨过三道门槛：作者公开代码、真实 ROS 2 路径、数据免注册；它不做回环检测与位置识别，直接融合多个异构 LiDAR 会话，配离群点鲁棒全局配准与锚点节点位姿图，GPL-3.0-only。 |
| ARiADNE: A Reinforcement Learning Approach Using Att… | ICRA 2023 | [marmotlab/ARiADNE-ROS-Planner](https://github.com/marmotlab/ARiADNE-ROS-Planner) | 141★ | 2025-08 | 数据要注册 | 三道门槛全清：作者代码、纯 CPU 推理、ROS2 分支省去容器成本；桌面 CPU 上每次规划 0.17 s，是成熟的探索基线。 |
| IR-MCL: Implicit Representation-Based Online Global … | IEEE RA-L 2023 | [PRBonn/ir-mcl](https://github.com/PRBonn/ir-mcl) | 140★ | 2023-02 | 数据要注册 | 直接的 MCL 进展：神经占据场取代波束模型，权重随仓库发布，CPU 推理，无 ROS，无需注册，因此整条流水线可在目标机器上复现。 |
| ESVO2: Direct Visual-Inertial Odometry with Stereo E… | IEEE T-RO | [NAIL-HNU/ESVO2](https://github.com/NAIL-HNU/ESVO2) | 136★ | 2025-10 | ROS 1 + 数据要注册 | 少见的把纯 CPU 实时作为核心主张的论文，并附带直接法事件 VI 流程与结果轨迹供交叉核对。 |
| Graph-Based SLAM-Aware Exploration With Prior Topo-M… | IEEE RA-L 2024 | [bairuofei/Graph-Based_SLAM-Aware_Exploration](https://github.com/bairuofei/Graph-Based_SLAM-Aware_Exploration) ⟳ | 127★ | 2025-01 | ROS 1 + 数据要注册 | 图谱主动回环的自包含、MIT 许可、纯 CPU 复现：SLAM 感知规划器、TSP 与 frontier 基线、Stage 世界与真机 launch 都在代码树中；配套的多机器人论文 CGE 同样开源。 |
| mola_lidar_odometry: A flexible framework for accura… | IJRR | [MOLAorg/mola_lidar_odometry](https://github.com/MOLAorg/mola_lidar_odometry) | 127★ | 2026-10 | 数据要注册 | 唯一在 Ubuntu 24.04 上有可用 ROS 2 Jazzy build-farm 发布的候选；地图表示加位姿图与里程计可零摩擦在 CPU 上复现，且仍在积极维护。 |
| DVM-SLAM: Decentralized Visual Monocular Simultaneou… | IEEE ICRA 2025 - RAS venue | [proroklab/DVM-SLAM](https://github.com/proroklab/DVM-SLAM) | 99★ | 2025-03 | 数据要注册 | 首个开源的去中心化单目 C-SLAM：异步分布式 PGO 加外部关键帧与地图点交换；ROS 2 原生，无 CUDA，公开 TUM-VI，与已收录条目互补。 |
| vS-Graphs: Tightly Coupling Visual SLAM and 3D Scene… | IEEE RA-L 2026, vol 11 no 8 | [snt-arg/visual_sgraphs](https://github.com/snt-arg/visual_sgraphs) | 79★ | 2026-07 | 数据要注册 | 技术栈完全吻合（ROS2 Jazzy/Ubuntu 24.04）、GPL-3.0、2026 年仍活跃；基于 ORB-SLAM3 构建的墙/地面/房间/走廊可优化场景图，而 ORB-SLAM3 已在台账中。 |
| GV-Bench: Benchmarking Local Feature Matching for Ge… | IEEE/RSJ IROS | [jarvisyjw/GV-Bench](https://github.com/jarvisyjw/GV-Bench) ⟳ | 71★ | 2026-06 | 数据要注册 | 提供几何验证的工具、标签、逐序列配置与 mAP / Max-Recall@1.0 评分，而几何验证正是仓库中 AnyLoc、Revisit-Anything 这类位置识别流水线实际失败的阶段。 |
| iRotate: Active Visual SLAM for Omnidirectional Robo… | Elsevier Robotics and Autonomous S… | [eliabntt/irotate_active_slam](https://github.com/eliabntt/irotate_active_slam) | 70★ | 2022-11 | ROS 1 + 数据要注册 | 完整的三层主动 V-SLAM 系统，MPC、RTAB-Map 与评估 notebook 都在作者仓库里；它基于 RGB-D/Gazebo，是纯 CPU 上最强的主动 SLAM 复现目标。 |
| ESVIO: Event-based Stereo Visual Inertial Odometry | IEEE RA-L | [arclab-hku/ESVIO](https://github.com/arclab-hku/ESVIO) | 63★ | 2024-11 | 数据要注册 | 首个双目事件相机 VIO：事件角点通过时空指数衰减核关联，紧耦合进滑动窗口 BA；纯 CPU、无学习组件，便于与台账中已有的 ORB-SLAM3 比较。 |
| Efficient Dynamic LiDAR Odometry for Mobile Robots w… | IEEE/RSJ IROS 2024 | [tu-darmstadt-ros-pkg/dynamic_direct_lidar_odometry](https://github.com/tu-darmstadt-ros-pkg/dynamic_direct_lidar_odometry) | 55★ | 2025-02 | ROS 1 | 少数把动态物体当作 LiDAR 里程计内一等跟踪实体的工作：检测、关联、Kalman 跟踪后再从地图移除；trajectory_server 可导出带 ID 的逐对象轨迹，MIT 许可使构建风险最低。 |
| Observation Time Difference: an Online Dynamic Objec… | IEEE ICRA 2024 | [NEU-REAL/OTD](https://github.com/NEU-REAL/OTD) | 54★ | 2024-11 | ROS 1 | 线索是时间而非几何：体素晚于其下方地面出现或早于其消失即判为动态，因此不推理可见性或自由空间，是 D1 的独立证据而非清理基线的换皮；它是可通读的小型 catkin 包，在线运行，复用标准 KITTI 序列。 |
| DRACo-SLAM: Distributed Robust Acoustic Communicatio… | IEEE/RSJ IROS 2022 | [jake3991/DRACo-SLAM](https://github.com/jake3991/DRACo-SLAM) | 45★ | 2023-05 | ROS 1 | 唯一从带宽侧而非图侧处理通信受限协作的候选：机器人只交换场景描述子，仅在机器人间回环可能时才调取原始声呐数据；纯 CPU、MIT 许可，为偏重 LiDAR/视觉的台账加入新模态与带宽预算。 |
| TripletLoc: One-Shot Global Localization Using Seman… | IEEE RA-L 2025 | [Weixin-Ma/TripletLoc](https://github.com/Weixin-Ma/TripletLoc) | 36★ | 2025-03 | ROS 1 | 无初始猜测、查询时不需学习的一次性 6-DoF 全局重定位，来自 2025 RA-L 论文，作者代码、地图、标签与真值均已公开；流程构建实例与道路法向先验、组成三元组并用 GTSAM 验证。 |
| Multi-Robot Active Graph Exploration with Reduced Po… | IEEE/RSJ IROS 2024 | [bairuofei/CGE](https://github.com/bairuofei/CGE) | 35★ | 2025-02 | 数据要注册 | 一次清掉三道杀手：公开代码、完全无 ROS、无受限数据集，是本轮搭建成本最低的候选；它也是真正的主动 SLAM，用子模最大化挑选主动回环以降低位姿图不确定度，并带位姿图与路径规划机制。 |
| DISO: Direct Imaging Sonar Odometry | IEEE ICRA | [SenseRoboticsLab/DISO](https://github.com/SenseRoboticsLab/DISO) | 35★ | 2025-01 | ROS 1 | 对声学强度做直接法光度式优化，配数据关联策略与声学离群点剔除；成像声呐是真正未被覆盖的模态，而这是来自顶级 RAS 会场、唯一的近期开源声呐里程计。 |
| P-GAT: Pose-Graph Attentional Graph Neural Network f… | IEEE RA-L 2024 | [csiro-robotics/P-GAT](https://github.com/csiro-robotics/P-GAT) | 30★ | 2024-01 | 数据要注册 | 序列级位置识别可直接用仓库提供的 pickle 运行，因此 CPU 机器无需 MinkowskiEngine 或 CUDA 也能复现检索指标；RAS 会场、无 ROS、无需数据表单。 |
| Multi-Robot Object SLAM using Distributed Variationa… | IEEE RA-L 2024 | [hwcao17/distributed_msckf](https://github.com/hwcao17/distributed_msckf) | 25★ | 2024-05 | 数据要注册 | 本轮摩擦最小的候选：零 GPU、零 ROS、零数据集申请，作者自己的评估代码及输入都在一个 25 星的 MIT 仓库里；它把分布式推断（镜像下降/一致性 MSCKF）的多机器人 SLAM 表述放进台账。 |
| 3D Active Metric-Semantic SLAM | IEEE RA-L 2024 | [KumarRobotics/kr_3d_active_ms_slam](https://github.com/KumarRobotics/kr_3d_active_ms_slam) | 17★ | 2025-07 | ROS 1 | 唯一经验证、用真实纯 CPU 安装路径把语义感知、度量语义 SLAM 不确定度与下一最佳视角规划闭合起来的候选，发表于 RA-L；它补上语义引导的主动 SLAM 轴，并给出针对地图不确定度规划的实例。 |
| ETIO: Edge-Based Monocular Thermal-Inertial Odometry… | IEEE RA-L | [HITSZ-NRSL/ETIO](https://github.com/HITSZ-NRSL/ETIO) ⟳ | 12★ | 2026-01 | ROS 1 | 热成像相机加 IMU 的里程计，可在可见光 SLAM 失效的烟雾、粉尘与黑暗中工作；基于边缘而非学习，因此能在 CPU 上运行，也是 RAS 会场唯一持续维护的开放热惯性里程计。 |
| H-SLAM: Hybrid direct–indirect visual SLAM | Elsevier Robotics and Autonomous S… | [8bit-nyk/hslam_ros2](https://github.com/8bit-nyk/hslam_ros2) | 8★ | 2025-07 | 数据要注册 | Elsevier RAS 的 SLAM 论文，本批唯一 ROS 2 原生的候选；混合直接/间接单目系统，专为削减计算与内存而设计，纯 CPU 的 20 核机器正是它的目标工作点。 |

## 不建议复现：17 条

列在这里是为了留证：这些论文的仓库都真实可达（实测 HTTP 200），但**在这台机器上或按本仓库的规则做不了**。

| 论文 | venue | 仓库 | ★ | 拦在哪 | 仓库里的方法完整度 |
| :--- | :--- | :--- | ---: | :--- | :--- |
| Gaussian Splatting SLAM | IEEE/CVF CVPR 2024 | [muskie82/MonoGS](https://github.com/muskie82/MonoGS) | 2173★ | 要 GPU | full |
| PIN-SLAM: LiDAR SLAM Using a Point-Based Impli… | IEEE T-RO 2024 | [PRBonn/PIN_SLAM](https://github.com/PRBonn/PIN_SLAM) | 627★ | CPU 存疑 | full |
| PALoc: Advancing SLAM Benchmarking With Prior-… | IEEE/ASME Transactions on Me… | [JokerJohn/PALoc](https://github.com/JokerJohn/PALoc) | 404★ | CPU 存疑 | full |
| BotanicGarden: A High-Quality Dataset for Robo… | IEEE RA-L | [robot-pesg/BotanicGarden](https://github.com/robot-pesg/BotanicGarden) | 308★ | 仓库只有数据集 | dataset-only |
| Open3DSG: Open-Vocabulary 3D Scene Graphs from… | CVPR 2024 | [boschresearch/Open3DSG](https://github.com/boschresearch/Open3DSG) | 166★ | 上游已归档 | full |
| RayFronts: Open-Set Semantic Ray Frontiers for… | IEEE/RSJ IROS 2025, pp. 5930… | [RayFronts/RayFronts](https://github.com/RayFronts/RayFronts) | 147★ | 数据要注册 + CPU 存疑 | full |
| Multiview Scene Graph | NeurIPS 2024 | [ai4ce/MSG](https://github.com/ai4ce/MSG) | 131★ | CPU 存疑 | full |
| MapEx: Indoor Structure Exploration with Proba… | IEEE ICRA 2025 | [castacks/MapEx](https://github.com/castacks/MapEx) | 110★ | CPU 存疑 | full |
| Open-Vocabulary Online Semantic Mapping for SL… | IEEE RA-L 2025 | [tberriel/OVO](https://github.com/tberriel/OVO) | 100★ | CPU 存疑 | full |
| DARE: Diffusion Policy for Autonomous Robot Ex… | ICRA 2025 | [marmotlab/DARE](https://github.com/marmotlab/DARE) | 91★ | 数据要注册 + CPU 存疑 | full |
| Open-Vocabulary Affordance Detection in 3D Poi… | IEEE/RSJ IROS 2023 | [Fsoft-AIC/Open-Vocabulary-Affordance-Detection-in-3D-Point-Clouds](https://github.com/Fsoft-AIC/Open-Vocabulary-Affordance-Detection-in-3D-Point-Clouds) ⟳ | 89★ | CPU 存疑 | full |
| A Benchmark Dataset for Collaborative SLAM in … | IEEE RA-L 2024 | [vision3d-lab/CSE_Dataset](https://github.com/vision3d-lab/CSE_Dataset) | 48★ | 仓库只有数据集 | dataset-only |
| Improving Indoor Localization Accuracy by Usin… | IEEE ICRA 2025 | [PRBonn/enm-mcl](https://github.com/PRBonn/enm-mcl) | 46★ | CPU 存疑 | full |
| Quantitative 3D Map Accuracy Evaluation Hardwa… | IEEE ICCAS | [SangwooJung98/3D_Map_Evaluation](https://github.com/SangwooJung98/3D_Map_Evaluation) | 30★ | 仓库只有方法的一半 | partial |
| Optimizing Exploration with a New Uncertainty … | Elsevier Robotics and Autono… | [Seba-san/UncertaintyMap](https://github.com/Seba-san/UncertaintyMap) | 9★ | 仓库只有方法的一半 | partial |
| FIT-SLAM 2: Efficient 3D exploration with Fish… | Elsevier Robotics and Autono… | [suchetanrs/FIT-SLAM](https://github.com/suchetanrs/FIT-SLAM) | 8★ | 数据要注册 + CPU 存疑 | full |
| Map point selection for visual SLAM | Elsevier Robotics and Autono… | [ChristiaanM/MapSelect](https://github.com/ChristiaanM/MapSelect) | 3★ | 仓库只有方法的一半 | partial |

## 按方向

### 动态环境与终身建图 `dynamic-map` — 10 条

| 论文 | venue | 仓库 | ★ | 最近提交 | 门槛 |
| :--- | :--- | :--- | ---: | :--- | :--- |
| Dynablox: Real-time Detection of Diverse Dynamic O… | IEEE RA-L 2023 | [ethz-asl/dynablox](https://github.com/ethz-asl/dynablox) ⟳ | 604★ | 2025-03 | 🟡 ROS 1 |
| KISS-SLAM: A Simple, Robust, and Accurate 3D LiDAR… | IROS 2025 | [PRBonn/kiss-slam](https://github.com/PRBonn/kiss-slam) | 533★ | 2025-12 | ✅ 四条全过 |
| LTA-OM: Long-Term Association LiDAR-Inertial Odome… | Journal of Field Robotics 2024 | [hku-mars/LTAOM](https://github.com/hku-mars/LTAOM) | 509★ | 2024-10 | 🟡 ROS 1 + 数据要注册 |
| DynaVINS: A Visual-Inertial SLAM for Dynamic Envir… | IEEE RA-L 2022 | [url-kaist/dynaVINS](https://github.com/url-kaist/dynaVINS) | 447★ | 2025-08 | 🟡 ROS 1 |
| Effectively Detecting Loop Closures using Point Cl… | ICRA 2024 | [PRBonn/MapClosures](https://github.com/PRBonn/MapClosures) | 444★ | 2026-08 | 🟡 数据要注册 |
| LiLoc: Lifelong Localization using Adaptive Submap… | IEEE ICRA 2025 | [Yixin-F/LiLoc](https://github.com/Yixin-F/LiLoc) ⟳ | 418★ | 2025-03 | 🟡 ROS 1 + 数据要注册 |
| MS-Mapping: An Uncertainty-Aware Large-Scale Multi… | ICRA@40 2024 | [JokerJohn/MS-Mapping](https://github.com/JokerJohn/MS-Mapping) | 386★ | 2025-08 | 🟡 ROS 1 + 数据要注册 |
| Multi-Mapcher: Loop Closure Detection-Free Heterog… | IEEE Transactions on Intellige… | [url-kaist/multi-mapcher](https://github.com/url-kaist/multi-mapcher) | 144★ | 2026-08 | 🟡 数据要注册 |
| Efficient Dynamic LiDAR Odometry for Mobile Robots… | IEEE/RSJ IROS 2024 | [tu-darmstadt-ros-pkg/dynamic_direct_lidar_odometry](https://github.com/tu-darmstadt-ros-pkg/dynamic_direct_lidar_odometry) | 55★ | 2025-02 | 🟡 ROS 1 |
| Observation Time Difference: an Online Dynamic Obj… | IEEE ICRA 2024 | [NEU-REAL/OTD](https://github.com/NEU-REAL/OTD) | 54★ | 2024-11 | 🟡 ROS 1 |

### LiDAR 里程计与后端 `lidar-odometry` — 12 条

| 论文 | venue | 仓库 | ★ | 最近提交 | 门槛 |
| :--- | :--- | :--- | ---: | :--- | :--- |
| GLIM: 3D Range-Inertial Localization and Mapping w… | Elsevier Robotics and Autonomo… | [koide3/glim](https://github.com/koide3/glim) | 1858★ | 2026-09 | ✅ 四条全过 |
| BALM 2.0: Bundle Adjustment for LiDAR Mapping (eff… | T-RO | [hku-mars/BALM](https://github.com/hku-mars/BALM) | 946★ | 2024-08 | 🟡 ROS 1 |
| KISS-Matcher: Fast and Robust Point Cloud Registra… | IEEE ICRA 2025 | [MIT-SPARK/KISS-Matcher](https://github.com/MIT-SPARK/KISS-Matcher) | 792★ | 2026-08 | ✅ 四条全过 |
| Voxel-SLAM: A Complete, Accurate, and Versatile Li… | T-RO / arXiv | [hku-mars/Voxel-SLAM](https://github.com/hku-mars/Voxel-SLAM) | 688★ | 2025-04 | 🟡 ROS 1 + 数据要注册 |
| A Robust Approach for LiDAR-Inertial Odometry With… | IEEE RA-L 2026 | [PRBonn/rko_lio](https://github.com/PRBonn/rko_lio) | 672★ | 2026-10 | ✅ 四条全过 |
| PIN-SLAM: LiDAR SLAM Using a Point-Based Implicit … | IEEE T-RO 2024 | [PRBonn/PIN_SLAM](https://github.com/PRBonn/PIN_SLAM) | 627★ | 2025-09 | 🟡 CPU 存疑 |
| SR-LIO: LiDAR-Inertial Odometry with Sweep Reconst… | IROS | [ZikangYuan/sr_lio](https://github.com/ZikangYuan/sr_lio) | 555★ | 2025-08 | 🟡 ROS 1 |
| MAD-ICP: It Is All About Matching Data - Robust an… | IEEE RA-L 2024 | [rvp-group/mad-icp](https://github.com/rvp-group/mad-icp) | 334★ | 2026-02 | ✅ 四条全过 |
| Kinematic-ICP: Enhancing LiDAR Odometry with Kinem… | IEEE ICRA 2025 | [PRBonn/kinematic-icp](https://github.com/PRBonn/kinematic-icp) | 333★ | 2025-07 | 🟡 数据要注册 |
| LOG-LIO: A LiDAR-Inertial Odometry with Efficient … | RA-L | [tiev-tongji/LOG-LIO](https://github.com/tiev-tongji/LOG-LIO) | 185★ | 2024-05 | 🟡 ROS 1 |
| SG-SLAM: Leveraging Semantic Graphs for Efficient … | IROS | [nubot-nudt/SG-SLAM](https://github.com/nubot-nudt/SG-SLAM) | 150★ | 2025-10 | 🟡 数据要注册 |
| mola_lidar_odometry: A flexible framework for accu… | IJRR | [MOLAorg/mola_lidar_odometry](https://github.com/MOLAorg/mola_lidar_odometry) | 127★ | 2026-10 | 🟡 数据要注册 |

### 视觉 / 视觉惯性 / 神经 SLAM `visual-neural` — 10 条

| 论文 | venue | 仓库 | ★ | 最近提交 | 门槛 |
| :--- | :--- | :--- | ---: | :--- | :--- |
| Gaussian Splatting SLAM | IEEE/CVF CVPR 2024 | [muskie82/MonoGS](https://github.com/muskie82/MonoGS) | 2173★ | 2024-05 | ⛔ 要 GPU |
| DM-VIO: Delayed Marginalization Visual-Inertial Od… | IEEE RA-L 2022 | [lukasvst/dm-vio](https://github.com/lukasvst/dm-vio) | 1235★ | 2024-10 | ✅ 四条全过 |
| Swarm-SLAM: Sparse Decentralized Collaborative Sim… | IEEE RA-L 2024 | [MISTLab/Swarm-SLAM](https://github.com/MISTLab/Swarm-SLAM) ⟳ | 711★ | 2025-04 | ✅ 四条全过 |
| Structure PLP-SLAM: Efficient Sparse Mapping and L… | IEEE ICRA 2023 | [PeterFWS/Structure-PLP-SLAM](https://github.com/PeterFWS/Structure-PLP-SLAM) | 476★ | 2026-07 | 🟡 数据要注册 |
| OKVIS2-X: Open Keyframe-based Visual-Inertial SLAM… | IEEE Transactions on Robotics | [ethz-mrl/OKVIS2-X](https://github.com/ethz-mrl/OKVIS2-X) | 413★ | 2026-03 | ✅ 四条全过 |
| UV-SLAM: Unconstrained Line-based SLAM Using Vanis… | IEEE RA-L 2022 | [url-kaist/UV-SLAM](https://github.com/url-kaist/UV-SLAM) | 302★ | 2023-08 | 🟡 ROS 1 + 数据要注册 |
| R-VIO2: Square-Root Robocentric Visual-Inertial Od… | IEEE RA-L | [rpng/R-VIO2](https://github.com/rpng/R-VIO2) | 292★ | 2024-09 | 🟡 ROS 1 |
| OKVIS2: Realtime Scalable Visual-Inertial SLAM wit… | IEEE/RSJ IROS | [ethz-mrl/okvis2](https://github.com/ethz-mrl/okvis2) | 237★ | 2025-12 | 🟡 数据要注册 |
| GroundSLAM: A Robust Visual SLAM System for Wareho… | IEEE ICRA | [sair-lab/GroundSLAM](https://github.com/sair-lab/GroundSLAM) | 151★ | 2026-07 | 🟡 ROS 1 + 数据要注册 |
| ESVO2: Direct Visual-Inertial Odometry with Stereo… | IEEE T-RO | [NAIL-HNU/ESVO2](https://github.com/NAIL-HNU/ESVO2) | 136★ | 2025-10 | 🟡 ROS 1 + 数据要注册 |

### 语义建图与场景图 `semantic-scene-graph` — 9 条

| 论文 | venue | 仓库 | ★ | 最近提交 | 门槛 |
| :--- | :--- | :--- | ---: | :--- | :--- |
| Hydra: A Real-time Spatial Perception System for 3… | RSS 2022 | [MIT-SPARK/Hydra](https://github.com/MIT-SPARK/Hydra) ⟳ | 1172★ | 2026-01 | ✅ 四条全过 |
| S-Graphs 2.0 - A Hierarchical-Semantic Optimizatio… | IEEE RA-L 2025 | [snt-arg/lidar_situational_graphs](https://github.com/snt-arg/lidar_situational_graphs) ⟳ | 323★ | 2026-07 | ✅ 四条全过 |
| Open3DSG: Open-Vocabulary 3D Scene Graphs from Poi… | CVPR 2024 | [boschresearch/Open3DSG](https://github.com/boschresearch/Open3DSG) | 166★ | 2024-09 | ⛔ 上游已归档 |
| RayFronts: Open-Set Semantic Ray Frontiers for Onl… | IEEE/RSJ IROS 2025, pp. 5930-5… | [RayFronts/RayFronts](https://github.com/RayFronts/RayFronts) | 147★ | 2026-07 | 🟡 数据要注册 + CPU 存疑 |
| Multiview Scene Graph | NeurIPS 2024 | [ai4ce/MSG](https://github.com/ai4ce/MSG) | 131★ | 2025-09 | 🟡 CPU 存疑 |
| 3D VSG: Long-term Semantic Scene Change Prediction… | IEEE ICRA 2023 | [ethz-asl/3d_vsg](https://github.com/ethz-asl/3d_vsg) | 102★ | 2023-07 | ✅ 四条全过 |
| Open-Vocabulary Online Semantic Mapping for SLAM | IEEE RA-L 2025 | [tberriel/OVO](https://github.com/tberriel/OVO) | 100★ | 2026-06 | 🟡 CPU 存疑 |
| Open-Vocabulary Affordance Detection in 3D Point C… | IEEE/RSJ IROS 2023 | [Fsoft-AIC/Open-Vocabulary-Affordance-Detection-in-3D-Point-Clouds](https://github.com/Fsoft-AIC/Open-Vocabulary-Affordance-Detection-in-3D-Point-Clouds) ⟳ | 89★ | 2024-09 | 🟡 CPU 存疑 |
| vS-Graphs: Tightly Coupling Visual SLAM and 3D Sce… | IEEE RA-L 2026, vol 11 no 8 | [snt-arg/visual_sgraphs](https://github.com/snt-arg/visual_sgraphs) | 79★ | 2026-07 | 🟡 数据要注册 |

### 地点识别与重定位 `place-recognition` — 10 条

| 论文 | venue | 仓库 | ★ | 最近提交 | 门槛 |
| :--- | :--- | :--- | ---: | :--- | :--- |
| STD: A Stable Triangle Descriptor for 3D Place Rec… | IEEE ICRA 2023 | [hku-mars/STD](https://github.com/hku-mars/STD) | 743★ | 2023-04 | 🟡 ROS 1 + 数据要注册 |
| G3Reg: Pyramid Graph-Based Global Registration Usi… | IEEE Transactions on Automatio… | [HKUST-Aerial-Robotics/G3Reg](https://github.com/HKUST-Aerial-Robotics/G3Reg) | 330★ | 2025-05 | ✅ 四条全过 |
| BoW3D: Bag of Words for Real-Time Loop Closing in … | IEEE RA-L 2023 | [YungeCui/BoW3D](https://github.com/YungeCui/BoW3D) | 318★ | 2023-05 | 🟡 ROS 1 + 数据要注册 |
| OverlapTransformer: An Efficient and Yaw-Angle-Inv… | IEEE RA-L 2022 | [haomo-ai/OverlapTransformer](https://github.com/haomo-ai/OverlapTransformer) | 294★ | 2024-07 | ✅ 四条全过 |
| Narrowing your FOV with SOLiD: Spatially Organized… | IEEE RA-L 2024 | [sparolab/SOLiD](https://github.com/sparolab/SOLiD) ⟳ | 210★ | 2025-05 | ✅ 四条全过 |
| IR-MCL: Implicit Representation-Based Online Globa… | IEEE RA-L 2023 | [PRBonn/ir-mcl](https://github.com/PRBonn/ir-mcl) | 140★ | 2023-02 | 🟡 数据要注册 |
| Improving Indoor Localization Accuracy by Using an… | IEEE ICRA 2025 | [PRBonn/enm-mcl](https://github.com/PRBonn/enm-mcl) | 46★ | 2025-03 | 🟡 CPU 存疑 |
| TripletLoc: One-Shot Global Localization Using Sem… | IEEE RA-L 2025 | [Weixin-Ma/TripletLoc](https://github.com/Weixin-Ma/TripletLoc) | 36★ | 2025-03 | 🟡 ROS 1 |
| P-GAT: Pose-Graph Attentional Graph Neural Network… | IEEE RA-L 2024 | [csiro-robotics/P-GAT](https://github.com/csiro-robotics/P-GAT) | 30★ | 2024-01 | 🟡 数据要注册 |
| Bag-of-Word-Groups (BoWG): A Robust and Efficient … | IEEE/RSJ IROS 2025 | [EdgarFx/BoWG](https://github.com/EdgarFx/BoWG) | 22★ | 2025-07 | ✅ 四条全过 |

### 主动 SLAM 与探索 `active-slam` — 10 条

| 论文 | venue | 仓库 | ★ | 最近提交 | 门槛 |
| :--- | :--- | :--- | ---: | :--- | :--- |
| FUEL: Fast UAV Exploration Using Incremental Front… | IEEE RA-L 2021 | [HKUST-Aerial-Robotics/FUEL](https://github.com/HKUST-Aerial-Robotics/FUEL) ⟳ | 1486★ | 2024-11 | 🟡 ROS 1 |
| RACER: Rapid Collaborative Exploration with a Dece… | IEEE T-RO 2023; 2023 T-RO Best… | [Robotics-STAR-Lab/RACER](https://github.com/Robotics-STAR-Lab/RACER) | 799★ | 2024-11 | 🟡 ROS 1 + 数据要注册 |
| TARE: A Hierarchical Framework for Efficiently Exp… | RSS 2021 | [caochao39/tare_planner](https://github.com/caochao39/tare_planner) | 734★ | 2024-06 | ✅ 四条全过 |
| ARiADNE: A Reinforcement Learning Approach Using A… | ICRA 2023 | [marmotlab/ARiADNE-ROS-Planner](https://github.com/marmotlab/ARiADNE-ROS-Planner) | 141★ | 2025-08 | 🟡 数据要注册 |
| Graph-Based SLAM-Aware Exploration With Prior Topo… | IEEE RA-L 2024 | [bairuofei/Graph-Based_SLAM-Aware_Exploration](https://github.com/bairuofei/Graph-Based_SLAM-Aware_Exploration) ⟳ | 127★ | 2025-01 | 🟡 ROS 1 + 数据要注册 |
| MapEx: Indoor Structure Exploration with Probabili… | IEEE ICRA 2025 | [castacks/MapEx](https://github.com/castacks/MapEx) | 110★ | 2026-02 | 🟡 CPU 存疑 |
| DARE: Diffusion Policy for Autonomous Robot Explor… | ICRA 2025 | [marmotlab/DARE](https://github.com/marmotlab/DARE) | 91★ | 2025-12 | 🟡 数据要注册 + CPU 存疑 |
| Multi-Robot Active Graph Exploration with Reduced … | IEEE/RSJ IROS 2024 | [bairuofei/CGE](https://github.com/bairuofei/CGE) | 35★ | 2025-02 | 🟡 数据要注册 |
| 3D Active Metric-Semantic SLAM | IEEE RA-L 2024 | [KumarRobotics/kr_3d_active_ms_slam](https://github.com/KumarRobotics/kr_3d_active_ms_slam) | 17★ | 2025-07 | 🟡 ROS 1 |
| Optimizing Exploration with a New Uncertainty Fram… | Elsevier Robotics and Autonomo… | [Seba-san/UncertaintyMap](https://github.com/Seba-san/UncertaintyMap) | 9★ | 2026-02 | 🟠 仓库只有方法的一半 |

### 多机协同 SLAM `multi-robot` — 8 条

| 论文 | venue | 仓库 | ★ | 最近提交 | 门槛 |
| :--- | :--- | :--- | ---: | :--- | :--- |
| COVINS-G: A Generic Back-end for Collaborative Vis… | IEEE ICRA 2023 | [VIS4ROB-lab/covins](https://github.com/VIS4ROB-lab/covins) | 461★ | 2023-05 | 🟡 ROS 1 + 数据要注册 |
| Swarm-LIO2: Decentralized, Efficient LiDAR-inertia… | IEEE Transactions on Robotics | [hku-mars/Swarm-LIO2](https://github.com/hku-mars/Swarm-LIO2) | 460★ | 2026-01 | 🟡 ROS 1 + 数据要注册 |
| DCL-SLAM: A Distributed Collaborative LiDAR SLAM F… | IEEE Sensors Journal | [zhongshp/DCL-SLAM](https://github.com/zhongshp/DCL-SLAM) | 324★ | 2025-03 | 🟡 ROS 1 |
| Distributed Certifiably Correct Pose-Graph Optimiz… | IEEE T-RO 2021 | [mit-acl/dpgo](https://github.com/mit-acl/dpgo) | 205★ | 2023-04 | 🟡 数据要注册 |
| CoLRIO: LiDAR-Ranging-Inertial Centralized State E… | IEEE ICRA 2024 | [zhongshp/Co-LRIO](https://github.com/zhongshp/Co-LRIO) | 119★ | 2025-03 | ✅ 四条全过 |
| DVM-SLAM: Decentralized Visual Monocular Simultane… | IEEE ICRA 2025 - RAS venue | [proroklab/DVM-SLAM](https://github.com/proroklab/DVM-SLAM) | 99★ | 2025-03 | 🟡 数据要注册 |
| DRACo-SLAM: Distributed Robust Acoustic Communicat… | IEEE/RSJ IROS 2022 | [jake3991/DRACo-SLAM](https://github.com/jake3991/DRACo-SLAM) | 45★ | 2023-05 | 🟡 ROS 1 |
| Multi-Robot Object SLAM using Distributed Variatio… | IEEE RA-L 2024 | [hwcao17/distributed_msckf](https://github.com/hwcao17/distributed_msckf) | 25★ | 2024-05 | 🟡 数据要注册 |

### 新模态与新表示 `emerging-sensing` — 6 条

| 论文 | venue | 仓库 | ★ | 最近提交 | 门槛 |
| :--- | :--- | :--- | ---: | :--- | :--- |
| CT-ICP: Real-time Elastic LiDAR Odometry with Loop… | IEEE ICRA | [jedeschaud/ct_icp](https://github.com/jedeschaud/ct_icp) | 907★ | 2022-07 | ✅ 四条全过 |
| Continuous-Time Radar-Inertial and Lidar-Inertial … | IEEE T-RO | [utiasASRL/steam_icp](https://github.com/utiasASRL/steam_icp) | 270★ | 2026-02 | ✅ 四条全过 |
| DeRO: Dead Reckoning Based on Radar Odometry With … | IEEE/RSJ IROS | [hoangvietdo/dero](https://github.com/hoangvietdo/dero) | 92★ | 2025-10 | ✅ 四条全过 |
| ESVIO: Event-based Stereo Visual Inertial Odometry | IEEE RA-L | [arclab-hku/ESVIO](https://github.com/arclab-hku/ESVIO) | 63★ | 2024-11 | 🟡 数据要注册 |
| DISO: Direct Imaging Sonar Odometry | IEEE ICRA | [SenseRoboticsLab/DISO](https://github.com/SenseRoboticsLab/DISO) | 35★ | 2025-01 | 🟡 ROS 1 |
| ETIO: Edge-Based Monocular Thermal-Inertial Odomet… | IEEE RA-L | [HITSZ-NRSL/ETIO](https://github.com/HITSZ-NRSL/ETIO) ⟳ | 12★ | 2026-01 | 🟡 ROS 1 |

### 基准与评测方法 `benchmarks-eval` — 6 条

| 论文 | venue | 仓库 | ★ | 最近提交 | 门槛 |
| :--- | :--- | :--- | ---: | :--- | :--- |
| MapEval: Towards Unified, Robust and Efficient SLA… | IEEE RA-L | [JokerJohn/Cloud_Map_Evaluation](https://github.com/JokerJohn/Cloud_Map_Evaluation) | 489★ | 2026-03 | 🟡 数据要注册 |
| PALoc: Advancing SLAM Benchmarking With Prior-Assi… | IEEE/ASME Transactions on Mech… | [JokerJohn/PALoc](https://github.com/JokerJohn/PALoc) | 404★ | 2026-01 | 🟡 CPU 存疑 |
| BotanicGarden: A High-Quality Dataset for Robot Na… | IEEE RA-L | [robot-pesg/BotanicGarden](https://github.com/robot-pesg/BotanicGarden) | 308★ | 2025-09 | ⛔ 仓库只有数据集 |
| GV-Bench: Benchmarking Local Feature Matching for … | IEEE/RSJ IROS | [jarvisyjw/GV-Bench](https://github.com/jarvisyjw/GV-Bench) ⟳ | 71★ | 2026-06 | 🟡 数据要注册 |
| SubT-MRS Dataset: Pushing SLAM Towards All-weather… | IEEE/CVF CVPR | [superxslam/Robustness_Metric](https://github.com/superxslam/Robustness_Metric) | 49★ | 2025-08 | ✅ 四条全过 |
| Quantitative 3D Map Accuracy Evaluation Hardware a… | IEEE ICCAS | [SangwooJung98/3D_Map_Evaluation](https://github.com/SangwooJung98/3D_Map_Evaluation) | 30★ | 2026-07 | 🟠 仓库只有方法的一半 |

### Elsevier RAS 期刊与路线图 `ras-venues` — 6 条

| 论文 | venue | 仓库 | ★ | 最近提交 | 门槛 |
| :--- | :--- | :--- | ---: | :--- | :--- |
| Visual place recognition for aerial imagery: A sur… | Elsevier Robotics and Autonomo… | [prime-slam/aero-vloc](https://github.com/prime-slam/aero-vloc) | 81★ | 2024-11 | ✅ 四条全过 |
| iRotate: Active Visual SLAM for Omnidirectional Ro… | Elsevier Robotics and Autonomo… | [eliabntt/irotate_active_slam](https://github.com/eliabntt/irotate_active_slam) | 70★ | 2022-11 | 🟡 ROS 1 + 数据要注册 |
| A Benchmark Dataset for Collaborative SLAM in Serv… | IEEE RA-L 2024 | [vision3d-lab/CSE_Dataset](https://github.com/vision3d-lab/CSE_Dataset) | 48★ | 2025-06 | ⛔ 仓库只有数据集 |
| H-SLAM: Hybrid direct–indirect visual SLAM | Elsevier Robotics and Autonomo… | [8bit-nyk/hslam_ros2](https://github.com/8bit-nyk/hslam_ros2) | 8★ | 2025-07 | 🟡 数据要注册 |
| FIT-SLAM 2: Efficient 3D exploration with Fisher i… | Elsevier Robotics and Autonomo… | [suchetanrs/FIT-SLAM](https://github.com/suchetanrs/FIT-SLAM) | 8★ | 2025-07 | 🟡 数据要注册 + CPU 存疑 |
| Map point selection for visual SLAM | Elsevier Robotics and Autonomo… | [ChristiaanM/MapSelect](https://github.com/ChristiaanM/MapSelect) | 3★ | 2023-07 | 🟠 仓库只有方法的一半 |
## 这批候选补上了本仓库的哪几个空白

对照 [`NOTES.md`](NOTES.md) 的覆盖表与 [`../docs/task-book/PAPER_AUDIT.md`](../docs/task-book/PAPER_AUDIT.md) 的无库清单：

| 空白 | 目录里现在的状态 | 这批候选 | 先看哪几条 |
| :--- | :--- | ---: | :--- |
| 多机协同 SLAM / 协作建图 | ⬜ **完全没有入口** | 8 | `MISTLab/Swarm-SLAM` · `zhongshp/Co-LRIO` |
| 主动 SLAM / 探索与不确定度决策 | ⬜ **完全没有入口** | 10 | `caochao39/tare_planner` · `HKUST-Aerial-Robotics/FUEL` · `marmotlab/ARiADNE-ROS-Planner` |
| 新模态：4D 雷达 / 事件相机 / 热成像 | ⬜ **完全没有入口** | 6 | `utiasASRL/steam_icp` · `hoangvietdo/dero` · `NAIL-HNU/ESVO2` · `HITSZ-NRSL/ETIO` |
| 连续时间轨迹与运动畸变 | 🟡 任务书难点 7，无对应复现 | 3 | `jedeschaud/ct_icp` · `utiasASRL/steam_icp` |
| 难点 3 退化场景鲁棒定位 | 🟡 X-ICP / Switch-SLAM / Active Illumination 全部无库 | 12 | `MIT-SPARK/KISS-Matcher` · `rvp-group/mad-icp` · `HKUST-Aerial-Robotics/G3Reg` |
| 难点 2 神经 SLAM 实时性 | ⬜ 目录里仍然空白 | 10 | ⚠️ 仍然过不去：`muskie82/MonoGS` 要 GPU，这一格**这批也没补上** |
| 难点 1 未知动态物体检测 | 🟡 有基线，缺评测口径 | 10 | `ethz-asl/dynablox`（ROS 1）· `hku-mars/M-detector`（ROS 1） |
| 难点 4 动态 SLAM 评测基准碎片化 | 🟢 已有 01-01 | 6 | `JokerJohn/Cloud_Map_Evaluation` · `SangwooJung98/3D_Map_Evaluation` |
| 难点 7 VPR / 视觉锚定 | 🟢 已有 02-07 / 02-08 | 10 | `sparolab/SOLiD` · `haomo-ai/OverlapTransformer` · `hku-mars/STD` |
| 难点 5 / 6 语义建图与场景图 | 🟡 有场景图，缺关系推理与时间一致性 | 9 | `MIT-SPARK/Hydra` · `snt-arg/lidar_situational_graphs` · `ethz-asl/3d_vsg` |
| 位姿图优化与鲁棒数据关联 | 🟡 任务书难点 8 | 5 | `MIT-SPARK/KISS-Matcher` · `utiasASRL/steam_icp` |

**一句话结论**：多机协同、主动 SLAM、新模态这三格从「零入口」变成「有 24 条可选」；
难点 3（退化鲁棒定位）从「三篇都没库」变成「12 条有库」；
**难点 2（神经 SLAM 实时性）这批仍然没补上** —— 它 GPU 密集这个事实没有变，
目录里凡是这一格的候选都标了 ⛔，不要指望在 CPU 上绕过去。

## 建议的开工顺序

如果只挑 8 条先做，按「门槛最低 × 补空白最大」排：

| 顺序 | 候选 | 理由 |
| ---: | :--- | :--- |
| 1 | `PRBonn/rko_lio` | RA-L 2026，MIT，**昨天还有提交**，`pip` 就能装，不需要 ROS，也不需要下载数据集就能起跑。 |
| 2 | `rvp-group/mad-icp` | 同样是 `pip install`，无 ROS 无 CUDA；它的「informed odometry」思路和已复现的 KISS-ICP 直接可比。 |
| 3 | `sparolab/SOLiD` | 无 GPU、无 ROS、无预训练权重、demo 扫描件随仓库带；四条门槛全过里成本最低的一条。 |
| 4 | `MIT-SPARK/KISS-Matcher` | ICRA 2025，792★，2026-08 还在更新；**全局配准**是重定位里最常被跳过的一半，补的是共性缺口。 |
| 5 | `MISTLab/Swarm-SLAM` | 补「多机协同」这一整格。MIT，ROS 2，数据免注册，本机能跑。 |
| 6 | `caochao39/tare_planner` | 补「主动 SLAM」这一整格。README 自己在 Ubuntu 24.04 + ROS 2 Jazzy 上测过，几乎零搭建成本。 |
| 7 | `snt-arg/lidar_situational_graphs` | D2 方向唯一同时满足 RA-L + ROS 2 Jazzy + 纯 CPU 的层级语义图，和已复现的 ORB-SLAM3 能接。 |
| 8 | `utiasASRL/steam_icp` | T-RO，一套代码覆盖 LiDAR / 雷达 / 惯性 / 连续时间四种组合，一次投入换四个对照组。 |

前四条都**不需要 ROS 环境**，可以在同一天里跑起来；第 5 到第 8 条开始需要 ROS 2 或少量配置。

## venue 分布

| venue | 条数 | 属于 RAS |
| :--- | ---: | :--- |
| IEEE RA-L（Robotics and Automation Letters） | 29 | ✅ |
| IEEE ICRA | 19 | ✅ |
| IEEE/RSJ IROS | 11 | ✅ |
| IEEE T-RO（Transactions on Robotics） | 8 | ✅ |
| Elsevier *Robotics and Autonomous Systems* | 7 | ✅ |
| IEEE T-ASE / CASE | 1 | ✅ |
| Journal of Field Robotics | 1 | ✅ |
| IEEE Sensors Journal | 1 | IEEE，非 RAS |
| RSS | 2 | ❌ |
| CVPR / ICCV / ECCV / 3DV | 3 | ❌ |
| IJRR / T-IV / T-MECH / NeurIPS / ICCAS | 5 | ❌ |

**RAS 相关合计 77 / 87。** 这批是按「IEEE RAS 会议与期刊 + Elsevier RAS 期刊」优先检索的，
非 RAS 的 10 条留在表里是因为方法本身对口（例如 `MIT-SPARK/Hydra` 发在 RSS，但它是 D2 方向最完整的底座）。

## 这一页是怎么产生的

- 检索：10 个方向各自独立检索，每个方向只收「有公开代码」的论文；两轮独立复核。
- 核验：87 个仓库逐一 `web_fetch` + HTTP 状态实测 + 元数据抓取（星标 / 最近提交 / 归档 / LICENSE）。
- 已知偏差：`8bit-nyk/hslam_ros2` 的星标自报值与实测值不一致（25 vs 8），已按实测值修正；
  其余 81 条自报星标与实测一致。上游已归档的只有 `boschresearch/Open3DSG` 一条，已标 ⛔。
- 未做的事：这一页**没有验证任何一条能否真的编译通过**。门槛是「看起来能跑」，不是「已经跑通」——
  真正的判定标准仍然是 `reproduce.py` 里对上了原论文的数字。
