# 任务书引用核查 Paper & Code Audit

**核查日期**：2026-10-05 · **核查对象**：[`TASK_BOOK.md`](TASK_BOOK.md) §2「难点清单 + 对应论文与库」的全部引用
· **方法**：DOI 逐条查 **Crossref API**（不采信文档自述）；仓库逐条查**论文原文 / 作者页面 / 项目页**，
并对每个上报 URL 实测 HTTP 状态码 · **详细分组记录**：[`audit/`](audit/)

> 任务书 §2 自己写着"**venue 全部经 Crossref 独立核验**"。这一页就是去验这句话。

---

## 一、结论先说

| 问题 | 结论 |
| :--- | :--- |
| **这些是真论文吗？** | ✅ **33/33 全部真实存在**，DOI 全解析成功，标题与引用名一一对应 |
| **venue 写对了吗？** | ✅ **32/33 完全正确**（含年份）；**1 条年份需修正**（见 §4） |
| **有库吗？** | ⚠️ **33 篇里 7 篇没有官方代码**，另有 1 篇仓库里**只有数据集与评测工具、没有方法代码** |
| **库能跑吗？** | ⚠️ 有库的里面，多数是 **ROS 1**（本机是 ROS 2 Jazzy、无 Docker、无 sudo），且多个数据集需注册 |

**按你定的规则「没有库的先不复现」，§2 的 33 篇里有 8 篇直接出局。**

---

## 二、真实性核验：33 条 DOI 全部通过

每一条都用 `https://api.crossref.org/works/<doi>` 取回官方元数据，与任务书写的名称、venue、年份对照：

| 引用名（任务书） | DOI | 任务书写 | Crossref 实际 venue | 年 |
| :--- | :--- | :--- | :--- | :--- |
| TerrainNet | `10.15607/rss.2023.xix.103` | RSS 2023 | Robotics: Science and Systems XIX | 2023 |
| DuLoc | `10.1109/IROS60139.2025.11246422` | IROS 2025 | 2025 IEEE/RSJ International Conference on In | 2025 |
| LT-mapper | `10.1109/ICRA46639.2022.9811916` | ICRA 2022 | 2022 International Conference on Robotics an | 2022 |
| Trans4Trans | `10.1109/tits.2022.3161141` | T-ITS 2022 | IEEE Transactions on Intelligent Transportat | 2022 |
| Segmenting Transparent Objects in the Wild | `10.1007/978-3-030-58601-0_41` | ECCV 2020 | Lecture Notes in Computer Science | 2020 |
| Glass Detection in Real-World Scenes | `10.1109/CVPR42600.2020.00374` | CVPR 2020 | 2020 IEEE/CVF Conference on Computer Vision  | 2020 |
| Seeing Through Fog Without Seeing Fog | `10.1109/cvpr42600.2020.01170` | CVPR 2020 | 2020 IEEE/CVF Conference on Computer Vision  | 2020 |
| X-ICP | `10.1109/TRO.2023.3335691` | T-RO 2024 | IEEE Transactions on Robotics | 2024 |
| LOG-LIO | `10.1109/LRA.2023.3332020` | RA-L 2024 | IEEE Robotics and Automation Letters | 2024 |
| GenZ-ICP | `10.1109/LRA.2024.3498779` | RA-L 2025 | IEEE Robotics and Automation Letters | 2025 |
| Switch-SLAM | `10.1109/LRA.2024.3421792` | RA-L 2024 | IEEE Robotics and Automation Letters | 2024 |
| FAST-LIVO2 | `10.1109/TRO.2024.3502198` | T-RO 2025 | IEEE Transactions on Robotics | 2025 |
| Active Illumination for Visual Ego-Motion in | `10.1109/icra55743.2025.11127536` | ICRA 2025 | 2025 IEEE International Conference on Roboti | 2025 |
| R3LIVE | `10.1109/icra46639.2022.9811935` | ICRA 2022 | 2022 International Conference on Robotics an | 2022 |
| DUFOMap | `10.1109/LRA.2024.3387658` | RA-L 2024 | IEEE Robotics and Automation Letters | 2024 |
| DynPurge | `10.1109/LRA.2025.3623005` | RA-L 2025 | IEEE Robotics and Automation Letters | 2025 |
| Ephemerality | `10.1109/ICRA55743.2025.11127618` | ICRA 2025 | 2025 IEEE International Conference on Roboti | 2025 |
| Khronos | `10.15607/RSS.2024.XX.081` | RSS 2024 | Robotics: Science and Systems XX | 2024 |
| NGD-SLAM | `10.1109/IROS60139.2025.11246202` | IROS 2025 | 2025 IEEE/RSJ International Conference on In | 2025 |
| Mobile-Seed | `10.1109/lra.2024.3373235` | RA-L 2024 | IEEE Robotics and Automation Letters | 2024 |
| Clio | `10.1109/LRA.2024.3451395` | RA-L 2024 | IEEE Robotics and Automation Letters | 2024 |
| FAST-LIO2 | `10.1109/TRO.2022.3141876` | T-RO 2022 | IEEE Transactions on Robotics | 2022 |
| Online LiDAR-Camera Extrinsic Calibration Us | `10.1109/ojits.2025.3555574` | IEEE OJ-ITS 2025 | IEEE Open Journal of Intelligent Transportat | 2025 |
| Online Temporal Calibration for Monocular Vi | `10.1109/IROS.2018.8593603` | IROS 2018 | 2018 IEEE/RSJ International Conference on In | 2018 |
| SR-LIVO | `10.1109/lra.2024.3389415` | RA-L 2024 | IEEE Robotics and Automation Letters | 2024 |
| Traj-LO | `10.1109/LRA.2024.3352360` | RA-L 2024 | IEEE Robotics and Automation Letters | 2024 |
| DLIO | `10.1109/ICRA48891.2023.10160508` | ICRA 2023 | 2023 IEEE International Conference on Roboti | 2023 |
| Kimera-Multi | `10.1109/tro.2021.3137751` | T-RO 2022 | IEEE Transactions on Robotics | 2022 |
| D²SLAM | `10.1109/TRO.2024.3422003` | T-RO 2024 | IEEE Transactions on Robotics | 2024 |
| Swarm-SLAM | `10.1109/lra.2023.3333742` | RA-L 2024 | IEEE Robotics and Automation Letters | 2024 |
| GNC | `10.1109/LRA.2020.2965893` | RA-L 2020 | IEEE Robotics and Automation Letters | 2020 |
| Active Neural Topological Mapping | `10.1109/LRA.2023.3331892` | RA-L 2023 | IEEE Robotics and Automation Letters | 2024 |
| Control Barrier Functions: Theory and Applic | `10.23919/ECC.2019.8796030` | ECC 2019 综述 | 2019 18th European Control Conference (ECC) | 2019 |

**唯一一处不符**：`Active Neural Topological Mapping` 任务书写 **RA-L 2023**，
Crossref 的 `issued` / `published-print` 是 **2024-01**（vol. 9, no. 1, pp. 303–310）。
2023 是 online-first 的日期（DOI 字符串里带 2023 也是这个原因）。
**正式引用年份应为 2024**；建议写成 "RA-L 2024（online 2023-11-10）"。

### 非 DOI 的引用也一并核了

| 条目 | 任务书写 | 核查结果 |
| :--- | :--- | :--- |
| DynamicMap_Benchmark | ITSC 2023 | ✅ 实际发表于 ITSC 2023（arXiv:2307.07260）；本仓库已复现其表 I |
| **ActLoc** | **CoRL 2025** | ✅ 真实：*ActLoc: Learning to Localize on the Move via Active Viewpoint Selection*，Jiajie Li 等，PMLR **v305**（CoRL 2025） |
| Kalibr / g2o / GTSAM / Ceres | 库 | ✅ 4 个官方仓库链接全部 HTTP 200 |
| ISO 3691-4 / IEC 61496 | 标准 | ✅ 标准号真实存在（工业车辆安全 / 电敏防护设备） |

---

## 三、仓库核查：按任务书难点逐条列出

图例：✅ 官方仓库可用 · ⚠️ 有仓库但有实质缺陷 · ❌ **无官方代码**

### 难点 1 · 提前数秒的预判停车

| 论文 | 官方代码 | 说明 |
| :--- | :--- | :--- |
| TerrainNet (RSS 2023) | ❌ **无** | 论文、项目页、作者主页、补充材料全部查过，均无 `[code]`；GitHub 搜索无对应仓库，也**无第三方实现** |
| DuLoc (IROS 2025) | ❌ **无** | 依赖私有港口数据集（32 台 IGV、2856 h、RTK 真值），代码与数据均未发布 |
| LT-mapper (ICRA 2022) | ✅ [gisbi-kim/lt-mapper](https://github.com/gisbi-kim/lt-mapper) | MIT · **ROS 1**；会话数据须先用外部 SC-LIO-SAM 等生成 |

### 难点 2 · 特殊障碍物感知

| 论文 | 官方代码 | 说明 |
| :--- | :--- | :--- |
| Trans4Trans (T-ITS 2022) | ✅ [jamycheung/Trans4Trans](https://github.com/jamycheung/Trans4Trans) | Apache-2.0 · 权重在网盘；5 个数据集全需注册 |
| Segmenting Transparent Objects in the Wild (ECCV 2020) | ✅ [xieenze/Segment_Transparent_Objects](https://github.com/xieenze/Segment_Transparent_Objects) | Apache-2.0 · README 警告 **torch 必须恰为 1.1.0**（更高会掉点） |
| Glass Detection（Don't Hit Me!, CVPR 2020） | ⚠️ [Mhaiyang/CVPR2020_GDNet](https://github.com/Mhaiyang/CVPR2020_GDNet) | 只有 `infer.py`，**训练流程未公开**；GDD 数据集需提交申请 |
| Seeing Through Fog (CVPR 2020) | ⚠️ [princeton-computational-imaging/SeeingThroughFog](https://github.com/princeton-computational-imaging/SeeingThroughFog) | **名为 Code，实为数据集+评测工具**：不含融合网络训练代码与权重，方法本身要重写 |

### 难点 3 · 退化场景下的鲁棒定位

| 论文 | 官方代码 | 说明 |
| :--- | :--- | :--- |
| X-ICP (T-RO 2024) | ❌ **无** | 论文与项目页均无代码；同作者后来的 `perfectlyconstrained` 只含退化检测模块，不是系统 |
| LOG-LIO (RA-L 2024) | ✅ [tiev-tongji/LOG-LIO](https://github.com/tiev-tongji/LOG-LIO) | GPLv2 · **ROS 1**；须先编译其 RingFalsNormal 依赖 |
| GenZ-ICP (RA-L 2025) | ✅ [cocel-postech/genz-icp](https://github.com/cocel-postech/genz-icp) | MIT · 只是里程计前端，无建图/回环 |
| Switch-SLAM (RA-L 2024) | ❌ **无** | 一作主页与实验室页只有 paper+video，GitHub 检索无仓库 |
| FAST-LIVO2 (T-RO 2025) | ✅ [hku-mars/FAST-LIVO2](https://github.com/hku-mars/FAST-LIVO2) | GPLv2 · **ROS 1**；需作者 fork 的 rpg_vikit 与非模板 Sophus。**勿与 FAST-LIO2 混** |
| Active Illumination (ICRA 2025) | ❌ **无** | arXiv 全文里唯一的 GitHub 链接是 evo；还需物理云台光源 + 自采数据 |
| R3LIVE (ICRA 2022) | ✅ [hku-mars/r3live](https://github.com/hku-mars/r3live) | GPLv2 限学术；OpenCV 编译版与运行版不一致会崩 |

### 难点 4 · 高变动场景的地图维护

| 论文 | 官方代码 | 说明 |
| :--- | :--- | :--- |
| DUFOMap (RA-L 2024) | ✅ [KTH-RPL/dufomap](https://github.com/KTH-RPL/dufomap) | BSD-3 · **本仓库已复现，命中论文** |
| DynPurge (RA-L 2025) | ❌ **无** | 只有一页伪代码+结果截图，作者身份未确认；arXiv 无预印本。**无可运行实现** |
| Ephemerality / ELite (ICRA 2025) | ✅ [dongjae0107/ELite](https://github.com/dongjae0107/ELite) | MIT · 多会话需人工用 CloudCompare 做 ICP 初值 |
| Khronos (RSS 2024) | ✅ [MIT-SPARK/Khronos](https://github.com/MIT-SPARK/Khronos) | BSD-3 · 要求 Ubuntu 24.04 + ROS 2 Jazzy，官方自述 ROS2 版"不稳定" |
| DynamicMap_Benchmark (ITSC 2023) | ✅ [KTH-RPL/DynamicMap_Benchmark](https://github.com/KTH-RPL/DynamicMap_Benchmark) | BSD-3 · 仓库已漂移出论文快照（8 个方法 vs 论文 5 个）→ **须锁定 commit** |

### 难点 5 · 算力受限下的稀疏表示 + 语义

| 论文 | 官方代码 | 说明 |
| :--- | :--- | :--- |
| NGD-SLAM (IROS 2025) | ✅ [yuhaozhang7/NGD-SLAM](https://github.com/yuhaozhang7/NGD-SLAM) | GPL-3.0 · **本仓库已复现，ATE 与 RPE-平移命中** |
| Mobile-Seed (RA-L 2024) | ✅ [WHU-USI3DV/Mobile-Seed](https://github.com/WHU-USI3DV/Mobile-Seed) | BSD-2 · 权重在 OneDrive/百度网盘；Cityscapes 需注册 |
| Clio (RA-L 2024) | ✅ [MIT-SPARK/Clio](https://github.com/MIT-SPARK/Clio) | BSD-2 · **ROS 1/catkin**；须关闭 TensorRT；数据在 Dropbox |
| FAST-LIO2 (T-RO 2022) | ✅ [hku-mars/FAST_LIO](https://github.com/hku-mars/FAST_LIO) | GPL-2.0 · **ROS 1**；同一仓库同时装 FAST-LIO 1 和 2 |

### 难点 6 · 语义辅助的在线标定

| 论文 | 官方代码 | 说明 |
| :--- | :--- | :--- |
| Online LiDAR-Camera Extrinsic Calibration (OJ-ITS 2025) | ❌ **无** | 9 页开放获取正式版**无任何代码链接**；还需自备图像分割与 Cylinder3D 两套预训练模型 |
| Online Temporal Calibration (IROS 2018) | ⚠️ [HKUST-Aerial-Robotics/VINS-Mono](https://github.com/HKUST-Aerial-Robotics/VINS-Mono) | GPL-3.0 · **没有专属仓库**：论文自己写明"时间标定源码已集成进 VINS-Mono"，且**论文里的实验脚本从未发布** |
| Kalibr | ✅ [ethz-asl/kalibr](https://github.com/ethz-asl/kalibr) | ⚠️ 任务书称其为"事实标准工具"，**但它已停更**：master 最后提交 **2024-03-08**，2025–2026 零提交；仅 ROS 1 |

### 难点 7 · 连续时间轨迹与运动畸变

| 论文 | 官方代码 | 说明 |
| :--- | :--- | :--- |
| SR-LIVO (RA-L 2024) | ✅ [ZikangYuan/sr_livo](https://github.com/ZikangYuan/sr_livo) | GPL-2.0 · 建在 R3LIVE 上，只有 NTU/R3LIVE 配置 |
| Traj-LO (RA-L 2024) | ✅ [kevin2431/Traj-LO](https://github.com/kevin2431/Traj-LO) | MIT · 官方自述仍 beta，**只支持单一 LiDAR 配置** |
| DLIO (ICRA 2023) | ✅ [vectr-ucla/direct_lidar_inertial_odometry](https://github.com/vectr-ucla/direct_lidar_inertial_odometry) | MIT · 默认 **ROS 1**；ROS2/Livox 需切分支；LiDAR-IMU 必须严格时间同步 |

### 难点 8 · 位姿图优化与鲁棒数据关联

| 论文 / 库 | 官方代码 | 说明 |
| :--- | :--- | :--- |
| Kimera-Multi (T-RO 2022) | ✅ [MIT-SPARK/Kimera-Multi](https://github.com/MIT-SPARK/Kimera-Multi) | 索引仓库，无 LICENSE，需 `vcs import` 拉子仓库 |
| D²SLAM (T-RO 2024) | ✅ [HKUST-Aerial-Robotics/D2SLAM](https://github.com/HKUST-Aerial-Robotics/D2SLAM) | ⚠️ 搜索先命中的是**别人的 fork**；无 LICENSE |
| Swarm-SLAM (RA-L 2024) | ✅ [MISTLab/Swarm-SLAM](https://github.com/MISTLab/Swarm-SLAM) | MIT · 论文摘要里直接写了这个 URL |
| GNC (RA-L 2020) | ⚠️ [MIT-SPARK/GNC-and-ADAPT](https://github.com/MIT-SPARK/GNC-and-ADAPT) | BSD-2 · **只有 MATLAB**，2021-01 后冻结；实用 C++ 版在 GTSAM 的 `GncOptimizer` |
| g2o | ✅ [RainerKuemmerle/g2o](https://github.com/RainerKuemmerle/g2o) | ⚠️ 许可混杂：部分 GPL3+/LGPL，仓库根部无 LICENSE 文件 |
| GTSAM | ✅ [borglab/gtsam](https://github.com/borglab/gtsam) | Simplified BSD（含第三方组件各自许可） |
| Ceres Solver | ✅ [ceres-solver/ceres-solver](https://github.com/ceres-solver/ceres-solver) | New BSD |

### 难点 9 · 主动感知 / 行为观测定位

| 论文 | 官方代码 | 说明 |
| :--- | :--- | :--- |
| ActLoc (CoRL 2025) | ✅ [cvg/ActLoc](https://github.com/cvg/ActLoc) | 2025-09 首次发布，无 LICENSE，README 仍标 WIP |
| Active Neural Topological Mapping | ✅ [yang-xy20/mantm](https://github.com/yang-xy20/mantm) | MIT · README 仍用旧标题；torch 1.5.1 + 改过的 habitat 分支 |

### 难点 10 · 安全停车与制动

| 资源 | 官方代码 | 说明 |
| :--- | :--- | :--- |
| Control Barrier Functions: Theory and Applications (ECC 2019) | ❌ **无** | **它是综述/tutorial，不是方法论文**，无作者代码属正常；arXiv 全文无代码链接 |
| ISO 3691-4 / IEC 61496 | — | 标准，无论文代码 |

---

## 四、没有库的清单 —— 按你的规则直接出局

**7 篇完全没有官方代码：**

| # | 论文 | 难点 | 缺什么 |
| :-- | :--- | :--- | :--- |
| 1 | **TerrainNet** (RSS 2023) | 难点 1 | 无代码、无权重、无数据，**连第三方实现都没有** |
| 2 | **DuLoc** (IROS 2025) | 难点 1 | 私有港口数据，代码与数据均未发布 |
| 3 | **X-ICP** (T-RO 2024) | 难点 3 | 无代码 |
| 4 | **Switch-SLAM** (RA-L 2024) | 难点 3 | 无代码 |
| 5 | **Active Illumination** (ICRA 2025) | 难点 3 | 无代码，且需物理云台光源与自采数据 |
| 6 | **DynPurge** (RA-L 2025) | 难点 4 | 无可运行实现，仅伪代码页 |
| 7 | **Online LiDAR-Camera Extrinsic Calibration** (OJ-ITS 2025) | 难点 6 | 无代码 |

**外加 1 篇"有仓库但没有方法代码"**：

| # | 论文 | 仓库实际内容 |
| :-- | :--- | :--- |
| 8 | **Seeing Through Fog** (CVPR 2020) | 仓库只有数据集与评测工具，**融合网络与权重都没有** → 方法本身无法复现 |

> ⚠️ **这对任务书 §2 的打击是具体的**：难点 1 的三篇里有 **2 篇没库**（TerrainNet、DuLoc），
> 剩下唯一能跑的 LT-mapper 还是 ROS 1、且需要先自己造会话数据。
> 难点 3 的七篇里有 **3 篇没库**，而这一节本来是"鲁棒定位"的核心参考。

---

## 五、需要改任务书的地方

| # | 位置 | 现状 | 建议 |
| :-- | :--- | :--- | :--- |
| 1 | §2 难点 9 | `Active Neural Topological Mapping` 写 **RA-L 2023** | 改为 **RA-L 2024**（vol. 9, no. 1, pp. 303–310；2023 是 online-first） |
| 2 | §2 难点 6 | Kalibr 被称为"事实标准工具" | 补一句**已停更**（master 最后提交 2024-03-08，2025–2026 零提交），仅 ROS 1 |
| 3 | §2 难点 1 | 三篇论文并列，未标可用性 | 标注 **TerrainNet / DuLoc 无代码**，该难点实际只剩 LT-mapper |
| 4 | §2 难点 3 | 七篇并列 | 标注 **X-ICP / Switch-SLAM / Active Illumination 无代码** |
| 5 | §2 难点 4 | DynPurge 与 DUFOMap 等并列 | 标注 **DynPurge 无代码** |
| 6 | §2 难点 6 | 语义辅助标定两篇 | 标注 **OJ-ITS 2025 那篇无代码**，该行实际只剩"时间标定"一半可做 |
| 7 | §2 难点 2 | 四篇并列 | 标注 **Seeing Through Fog 的"Code"链接实为数据集仓库**，方法代码未发布 |
| 8 | §2 表头 | 声称"venue 全部经 Crossref 独立核验" | **基本属实**（32/33），改掉上面第 1 条即可 |

---

## 六、这次核查改变了什么

1. **"有论文"不等于"能复现"。** 33 篇全是真论文，但 8 篇按规则直接出局——
   而且出局的集中在**难点 1 和难点 3**，正好是任务书里最核心的两节。
2. **ROS 1 是比"没代码"更隐蔽的障碍。** 在有代码的 25 篇里，LT-mapper、LOG-LIO、FAST-LIVO2、Clio、
   FAST-LIO2、DLIO、Kalibr 都是 ROS 1；本机是 ROS 2 Jazzy、无 Docker、无 sudo。
   **这不是"跑不跑得动"的问题，是"能不能编译"的问题。**
3. **数据集注册是第三条共同的坎**：Trans4Trans、Mobile-Seed、Glass Detection、R3LIVE
   以及 KITTI/SemanticKITTI 系全部要注册或走网盘。
4. **已复现的 6 个，恰好全部绕开了上面三条**：
   01-05 DUFOMap 用官方 PyPI 包、01-06 BeautyMap 用官方仓库、01-08 NGD-SLAM 无 ROS、
   01-01 数据走 Zenodo 直链、02-01 用公开示例包。**这不是巧合，是选型的必然结果。**
