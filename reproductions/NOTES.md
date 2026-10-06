# 复现区 · 分析笔记 Notes

[`README.md`](README.md) 只留**索引 + 复现清单 + 约定**。这一页放**背景分析**：
两个研究方向、传感器契合度、与任务书和 [`car.md`](../docs/car.md) 的对应、论文报告值、链接核验。
**结论都在这里，主页不必再读一遍。**

---

## 这两个方向是什么

老师给的两个方向：

| 代号 | 俄文 | 中文 | 英文 |
| :--- | :--- | :--- | :--- |
| **D1** | робастная локализация и SLAM в динамических средах | 动态环境下的鲁棒定位与 SLAM | Robust localization and SLAM in dynamic environments |
| **D2** | семантическое картирование, визуальная привязка и навигация | 语义建图、视觉定位与导航 | Semantic mapping, visual anchoring and navigation |

D1 的三个关键词是**鲁棒**、**定位**、**动态环境**；D2 的三个关键词是**语义地图**、
**视觉锚定**（视觉定位 / 位置识别）、**导航**。两个方向共用「地图」这个对象：
D1 关心地图在变化中还能不能用来定位，D2 关心地图里有什么、怎么用它导航。

### 三个推进方向 S / D / V

老师的两条原题，展开成**三个可独立推进的方向**；任务书 §0.3 给出了它们各自的难点清单。
文件夹分组仍然照着**老师的原两行**排（01 = D1，02 = D2），三方向与原两行的对应关系如下：

| 代号 | 推进方向 | 难度 | 顺序 | 落在哪个文件夹 |
| :--- | :--- | :--- | :--- | :--- |
| **S** | 语义建图 | ★☆☆ 有成熟开源底座 | **第 1 个做** | `02_…/` 的 01–06（3RScan · OASIS-Map · ConceptGraphs · DualMap · HOV-SG · Clio） |
| **D** | 动态环境下的鲁棒定位与 SLAM | ★★★ | 进阶，与 V 同等重要 | 整个 `01_…/`（01–09） |
| **V** | 视觉定位与导航 | ★★★ 任务书缺口最大 | 进阶，与 D 同等重要 | `02_…/` 的 07–08（AnyLoc · Revisit Anything）+ 05（HOV-SG 的语言导航部分） |

> **为什么先做 S**：先把**表示层**建起来 —— 开放词汇地图产出的「物体节点 + 身份 + 标签」
> 正是 D 的地图修订与 V 的语义导航都要用的东西；而且 S 不需要新硬件。
> ⚠️ **但从论文报告值看，S 线的四个底座（ConceptGraphs / DualMap / HOV-SG / Clio）全都要 GPU**，
> 真正"不需要新硬件"的是 **D 线的 CPU 部分** —— 只看计划是看不出这一点的。

---

## 传感器契合度：17 个复现 vs 实物「D435i + 2D 雷达」

> 实物设定见任务书 §0.1：**Intel RealSense D435i（双目 IR + 深度 + Bosch BMI055 IMU）+
> 2D 激光雷达（单线水平扫描）**。
> 本目录 17 个复现**没有一个消费这套配置**，也**没有一个属于"多传感器融合"**（VIO/LIO/LIV）——
> 这句话必须写在明面上，否则"我们复现了 D 线"会被误读成"我们复现了你的传感器配置"。
> 平台侧（Gazebo）的传感器细节见 [`../docs/platform.md`](../docs/platform.md)。

| 编号 | 复现对象 | 它真正吃的传感器 | 与你的配置的关系 |
| :--- | :--- | :--- | :--- |
| 01-01 | DynamicMap_Benchmark | KITTI **3D 雷达**（HDL-64） | ❌ 不同模态。它给的是**点级评测口径**，不是传感器方案 |
| 01-02 | KISS-ICP | **3D 雷达** | ❌ 3D；但"扫描匹配 + 无回环"的思路可直接搬到 2D 扫描匹配 |
| 01-03 / 01-04 / 01-05 / 01-06 | ERASOR · Removert · DUFOMap · BeautyMap | 全部 **3D 雷达**（KITTI / SemanticKITTI / MulRan） | ❌ **四个清理方法都靠"体素/体积"**，单线 2D 雷达地图没有它们需要的结构 |
| 01-07 | DynoSAM | 双目 / RGB-D（**无 IMU、无雷达**） | ⚠️ **半个**：视觉动态 SLAM 有，惯性没有。而且它连 configure 都要 CUDA（本机跑不了） |
| 01-08 | NGD-SLAM | **RGB-D**（TUM，无 IMU、无雷达） | ⚠️ **半个**：深度相机的动态检测可以移植到 D435i；但同样依赖 COCO 语义，未知动态物体漏 |
| 01-09 | LT-mapper | **3D 雷达** | ❌ 多会话建图的思想可用，"变化检测"的几何判据是 3D 体素的 |
| 02-01 | 3RScan | RGB-D 多会话 | ⚠️ 数据/协议层：跨会话物体身份，与传感器无关 |
| 02-02 … 02-06 | OASIS-Map · ConceptGraphs · DualMap · HOV-SG · Clio | RGB-D / 视觉 | ⚠️ 只吃图像，D435i 的 RGB 通道可用；与 2D 雷达无关 |
| 02-07 / 02-08 | AnyLoc · Revisit Anything | 单目图像 | ⚠️ 图像检索，D435i 的 RGB 可用；与雷达无关 |

**结论（写死，避免以后再混）：**

1. **D 线现在是"3D 雷达上的方法论验证"**，它证明的是**评测口径与清理判据**（比如 H1′ 的排名翻转），
   不是"D435i + 2D 雷达能跑"。要落到实物，缺的是 **2D 雷达的可观测性**这一层。
2. **多传感器融合这一块目前是空白**。任务书 §0 定位栏要 VIO + LIO，而实物只有一颗 IMU
   （D435i 的 BMI055，见 §0.1），两者抢同一个零偏；**没有任何复现在处理这件事**。

### 缺口与候选官方实现（都实测可达、都能纯 CPU 跑）

这套实物可以**拆成两个各自有公开数据的半边**，都不需要等自采：

| 半边 | 候选官方实现 | 仓库 / 数据（实测） | 本机可行性 |
| :--- | :--- | :--- | :--- |
| **相机 + IMU（VIO）** —— D435i 的立体惯性半边 | **VINS-Fusion**（HKUST，双耳惯性 + 回环） | 仓库 HTTP 200 · 数据用 **EuRoC MAV**（ETH 官方页可达） | 🟢 纯 CPU |
| 同上（另一条对照路线） | **ORB-SLAM3**（UZ-SLAMLab，stereo-inertial） | 仓库 HTTP 200 · **TUM VI** 官方页可达 | 🟢 纯 CPU |
| **2D 雷达 + IMU** —— 你的雷达半边 | **Google Cartographer**（2D SLAM，官方就吃 2D + IMU） | 仓库 HTTP 200 · **Deutsches Museum** 官方 bag 直链实测 **200 / 493 MB** | 🟢 纯 CPU |
| **三者合起来**（D435i + 2D 雷达 + 同一颗 IMU） | **RTAB-Map**（官方支持 2D 雷达 + RGB-D + IMU 融合） | 仓库 HTTP 200 | 🟢 纯 CPU；但**没有匹配的公开数据**，只能自采 |
| 仿真侧 | 本仓库 Gazebo（车已有 **2D 雷达**） | — | 🟡 需补 **深度相机 + IMU** |

> **一个已经对上的地方**：本仓库 Gazebo 的 `omni_car_ros2_control.urdf` 里，
> `lidar` 只有水平 `<scan>`（720 采样、360°、12 m、10 Hz）**没有 `<vertical>`**，
> 所以它**本来就是单线 2D 雷达**，话题 `/scan` —— 正好对实物那台雷达。
> 缺的是 **D435i**：当前 `front_camera` 是普通 RGB（640×480、15 Hz），**无深度、无 IMU**。

**已经补进去的**：[`01-12 ORB-SLAM3`](01_robust_localization_slam_dynamic/12_orb_slam3/) ——
双目惯性（相机 + IMU 那半边），而且仓库自带 `Examples/Stereo-Inertial/stereo_inertial_realsense_D435i`
例子，正好对上实物相机；[`01-10 GenZ-ICP`](01_robust_localization_slam_dynamic/10_genz_icp/)、
[`01-11 ELite`](01_robust_localization_slam_dynamic/11_elite/)、
[`01-13 Khronos`](01_robust_localization_slam_dynamic/13_khronos/) 是同一轮检查后加进来的、
本机能跑的 D1 候选。

**还缺入口的**：**2D 雷达 + IMU 那半边**（候选 **Cartographer** / **RTAB-Map**，两个仓库实测可达、
纯 CPU，官方数据分别是 Deutsches Museum bag（493 MB 直链）与自采）—— 本机是 ROS 2，
而 Cartographer 官方是 ROS 1，得走和 ERASOR/Removert 同一套 micromamba 路线。
再把 Gazebo 的传感器补齐成 **D435i + 2D 雷达**，"仿真验证 → 自采确认"才能闭环。

---

## 任务书与这两个方向的关联

对照对象：[`docs/task-book/TASK_BOOK.md`](../docs/task-book/TASK_BOOK.md)
—— **《退化与高变动场景下的鲁棒定位与预判停车》**（§0.3 即三方向难点对照）。

### 与 D1：主体一致，几乎是同一件事

| 任务书位置 | 对应 D1 的哪一部分 |
| :--- | :--- |
| §1 H8 六类退化场景（白墙 / 暗光 / 运动模糊 / 空旷 / 家具移动 / 门开关） | 「退化 + 动态」的**测试矩阵**，逐条对应 |
| §2 难点 3 退化场景下的鲁棒定位（X-ICP / LOG-LIO / GenZ-ICP / Switch-SLAM / FAST-LIVO2） | **鲁棒定位**的核心 |
| §2 难点 4 高变动场景的地图维护（DUFOMap / DynPurge / Ephemerality / Khronos） | **动态环境**的核心 → 就是本目录 01-01…01-06 |
| §2 难点 7 连续时间轨迹、难点 8 位姿图与鲁棒关联 | 支撑鲁棒性的传统组件 |
| §5 H1 标定化置信度 | 「知道自己什么时候不知道」，D1 的空白点 |

**结论：任务书约有七成落在 D1 上。**

### 与 D2：只覆盖了「语义建图」一角

| 任务书位置 | 与 D2 的关系 |
| :--- | :--- |
| §0 地图层「关键帧稀疏语义 + ROI 实例级动态检测」 | ✅ 语义建图的**算力调度**，与 D2 直接相关 |
| §2 难点 5（Clio / Mobile-Seed / NGD-SLAM） | ✅ 稀疏语义表示 → 本目录 02-06 |
| §2 难点 6 语义辅助的在线标定 | ⚠️ 语义的**用途**是标定，不是建图 |
| §3 优化层「语义约束的特征匹配」 | ⚠️ 语义用于数据关联 |
| §4.1 地图更新策略里的「修订语义」 | ✅ 语义地图的**维护**，与 D2 相关 |

**两个明确缺口：**

1. **视觉锚定（визуальная привязка）几乎没有。** 任务书自己在 §0.2 写明：原 T3「内容变化下的
   VPR」→ **❌ 基本未保留**。也就是说 D2 的中点（视觉定位 / 位置识别）在任务书里是空的。
2. **导航只有「停」，没有「走」。** §3 决策层是「提前减速 → 功能停车」，
   没有目标点、没有路径规划、没有语义导航。D2 的第三段（навигация）在任务书里不成立。

**所以：若老师的两个方向都要覆盖，任务书还差「视觉锚定」和「语义导航」两块。**
本目录把这两块各留了入口（02-07 AnyLoc 对应视觉锚定；02-05 HOV-SG 自带语言导航）。

---

## 与「语义辅助的物体级变化检测」的关联

对象：
`Semantic-assisted object-level change detection between mapping sessions on a mobile robot`

**首先一个事实澄清**：没有检索到以此为标题的已发表论文——这句是自己在
`Localise/Practice_slam/` 里写的**当前主攻题目**。内容上真正同名的工作是
[OASIS-Map](https://arxiv.org/abs/2607.14899)（Oxford, 2026-07, under review），
标题是 *Object-Level Change Detection in Multi-Session Mapping using Semantic
Correspondence Matching*。两者说的是同一件事。

### 它和任务书：强关联，而且是任务书自己指过去的

| 任务书原文位置 | 说的什么 |
| :--- | :--- |
| §4.1 地图更新策略 | 「删除判据必须包含**可观测性**——'没看到' ≠ '不在'……**也是你之前那道题的核心**」 |
| §5 H3 | 「可观测性感知的地图删除判据，比'未观测即删除'的朴素规则产生更少的地图错误」 |
| §1 H9 | 任务书承认缺「地图更新策略」一节 |
| §6 并行实验 H1′ | 「假阳性来自**可观测性低**的区域」——与那道题同一个概念 |
| §0.2 去向表 | 原 T2 的二次访问协议与修订指标（stale label rate / identity consistency）**已移到** `Practice_slam/04_topic_object_change_detection.md` §8 |

**判定：这不是两个题目，是同一个机制的两个视角。** 任务书的 H3 和并行实验 H1′ 要想成立，
必须先有那道题定义的指标（跨会话身份一致率、可观测性分层 F1、未观测区分率）。
反过来说，那道题用的数据（3RScan）和建图底座（ConceptGraphs / DualMap / HOV-SG）
也正好补上任务书 D2 方向的缺口。

### 它和两个方向：正好落在 D1 × D2 的交点上

```
                  D1 动态环境鲁棒定位/SLAM          D2 语义建图/视觉锚定/导航
                  ───────────────────────          ────────────────────────
物体级变化检测  ←  多会话地图维护、动态物体            语义地图、物体身份、开放词汇
（本题目）          §难点 4、DynamicMap_Benchmark       §难点 5、Clio / DualMap
```

它比任务书的并行实验更进一步：并行实验是**点级**（DynamicMap_Benchmark 的 PR/RR/F1），
那道题是**物体级 + 语义 + 跨会话身份**，落在 D2 一侧更多。

### ⚠️ 一处必须修正的判断

`Practice_slam/04_topic_object_change_detection.md` §5 的核心论证是：
「OASIS-Map 用的是对应关系，**无法区分'没看到'与'没有'**」。

OASIS-Map 项目页实际写的是：

> "If an object is not seen in one of the sessions, it remains **Unknown**."

也就是说**它有一个 Unknown 类**。它自述的弱点是另一件事：
"reliable object association across revisits remains a key challenge, especially under
partial views, occlusion, and imperfect segmentation"——是**关联可靠性**问题，不是缺少弃权类。

这直接影响切入角度的写法：差异点不能是「我加一个不确定类」（它已经有了），
只能是把**可观测性变成可标定的量**并**分层测量**（可观测性分层 F1 / ECE /
未观测区分率），并且证明它的 Unknown 判定在低可观测性样本上是否真的可靠。
这个修正让假设更窄、更难被反驳，也更容易被证伪——是好事。

> 另一条硬信息：项目页写着 **"Code Soon" / "Video Soon"**，
> 论文状态 under review，**代码尚未发布**。所以 02-02 目前只能按论文复现，
> 不能 clone 任何东西；若要复现，需要自己实现 semantic correspondence 基线。

---

## 与 `car.md` 八个难点的覆盖对照

[`docs/car.md`](../docs/car.md) 把两个方向拆成 8 个难点，每个都带可验证假设。
本目录的 17 个复现与它们的对应关系如下 —— **没有对应格子的难点，就是还没有复现入口的难点**。

| car.md 难点 | 方向 | 对应复现 | 覆盖度 |
| :--- | :--- | :--- | :--- |
| **1** 未知动态物体检测（几何运动视差，脱离语义先验） | D1 | 01-08 NGD-SLAM · 01-07 DynoSAM · 01-03…01-06 | 🟡 有基线，缺「未知动态物体」的评测口径 |
| **2** 神经 SLAM 实时性（3DGS / NeRF） | D1 | 无 | ⬜ **空白** |
| **3** 灾难性遗忘（终身 SLAM） | D1 | 01-09 LT-mapper · 01-01 DynamicMap_Benchmark | 🟡 有长期建图，缺「遗忘」的实验设计 |
| **4** 动态 SLAM 评测基准碎片化 | D1 | 01-01 DynamicMap_Benchmark · 01-02 KISS-ICP | 🟢 地基已在，扩到视觉/多模态是新增量 |
| **5** 开放词汇建图的空间推理缺失 | D2 | 02-03 ConceptGraphs · 02-05 HOV-SG | 🟡 有场景图，缺「关系推理」评测 |
| **6** 动态场景图的时间一致性 | D2 | 02-01 3RScan · 02-02 OASIS-Map · 02-04 DualMap · 02-06 Clio | 🟢 本目录重点，与变化检测题目重叠 |
| **7** 动态环境下的 VPR（视觉锚定） | D2 | 02-07 AnyLoc · 02-08 Revisit Anything | 🟢 整图 vs 分割级可直接对比 |
| **8** 自然语言导航的指令-场景绑定 | D2 | 02-05 HOV-SG（部分） | 🟡 有导航，缺指令解析 |

**car.md 的优先建议是「先做难点 1 和难点 7」**——本目录里它们分别对应
`01-08 NGD-SLAM` 与 `02-07 / 02-08`，文件夹都已建好，可以直接开工。

> **难点 2（神经 SLAM 实时性）本目录没有入口**：它 GPU 密集，且与当前
> Gazebo + Nav2 底座没有交集。若要展开，`Localise/02_reproductions/dg_slam/`
> 里已有 DG-SLAM 的说明可作起点。

---

## ⚠️ 引用核查：任务书里的论文哪些能复现

2026-10-05 对任务书 §2 的**全部 33 条引用**做了独立核查（DOI 逐条查 Crossref + 每篇查有没有官方代码 +
每个 URL 实测 HTTP）：**33/33 是真论文，32/33 的 venue 与年份完全正确**，
但**7 篇没有官方代码、1 篇有仓库却只有数据集没有方法代码**。

→ 完整结果：[`../docs/task-book/PAPER_AUDIT.md`](../docs/task-book/PAPER_AUDIT.md)

**对本目录的直接影响**：按「没有库的先不复现」，02-02 OASIS-Map 已排除；
另外要注意 **ROS 1** 是比"没代码"更隐蔽的障碍 —— 有代码的 25 篇里，
LT-mapper / LOG-LIO / FAST-LIVO2 / Clio / FAST-LIO2 / DLIO / Kalibr 全是 ROS 1。

## 论文报告值 Paper baselines

> **复现的前提是先知道要复现出什么数。** 每个文件夹里都有一份 `paper_baseline.md`
> （含表号、页码、消融、参数、阻塞分析），总表见 **[`PAPER_BASELINES.md`](PAPER_BASELINES.md)**。

**原文覆盖：16/17。** 唯一缺的是 **01-04 Removert** —— 它的 IROS 2020 原文是闭源的
（OpenAlex 明确 `is_oa: false`，作者给的镜像站 DNS 不通），原因逐条记在
[`04_removert/paper_baseline.md`](01_robust_localization_slam_dynamic/04_removert/paper_baseline.md)。

### 这台机器能跑什么

**没有 GPU**（20 核 CPU / 15 GB RAM / 358 GB 空闲）。按"论文报告值 + 可行性"对齐后：

| 类别 | 数量 | 哪些 |
| :--- | ---: | :--- |
| ✅ 已复现（对上原库/论文） | 7 | 01-05 DUFOMap（两位小数一致）· 01-06 BeautyMap · 01-01 DynamicMap_Benchmark · 01-03 ERASOR · 01-04 Removert · 01-08 NGD-SLAM（ATE / RPE-平移命中）· 01-02 KISS-ICP（官方 KITTI 00–10 全量，0.53 % vs 论文 0.50 %） |
| 🟡 一半 / 待做 | 6 | 01-09 LT-mapper（只有变化检测半边）· 02-01 3RScan（工具跑通，无方法代码）· 01-10 GenZ-ICP · 01-11 ELite · 01-12 ORB-SLAM3 · 01-13 Khronos（四个新候选，已检查、本机能跑） |
| ⛔ 本机不可复现 | 8 | 01-07 · 02-02（无代码）· 02-03 · 02-04 · 02-05 · 02-06 · 02-07 · 02-08（全部要 GPU） |

### 数据：KITTI 注册阻塞已被绕开

01-01 / 01-05 需要的 KITTI 00 + 人工 GT，基准作者自己打包发在 Zenodo 上，**直链、免注册**：

```bash
wget https://zenodo.org/records/10886629/files/00.zip    # 385 MB，66 秒
unzip 00.zip -d reproductions/01_robust_localization_slam_dynamic/01_dynamicmap_benchmark/data/raw/
```

---

## 链接核验 Link check

建目录时逐条实测（`curl -o /dev/null -w '%{http_code}'`，跟随重定向），共 23 条链接。
2026-10-05 复核 16 个上游仓库，全部可达：

| 结果 | 说明 |
| :--- | :--- |
| ✅ 200 | 16 个代码库全部可达（GitHub API 复核，`archived` 全为 false） |
| ⚠️ **修正 1 条** | `github.com/KTH-RPL/BeautyMap` **返回 404**。BeautyMap 的正确仓库是 [`MKJia/BeautyMap`](https://github.com/MKJia/BeautyMap)（已实测 200）。上游 `Localise/01_task_books/materials/links.md` 记的 KTH-RPL 地址是错的 |
| ⚠️ **已迁移 1 条** | `github.com/irapkaist/removert` 现在 301 到 [`gisbi-kim/removert`](https://github.com/gisbi-kim/removert)，链接仍可用 |
| ℹ️ 1 条非资源 | OASIS-Map 项目页可达，但明确标注 **Code Soon**，无代码可 clone |
