# 复现区 Reproductions

按 **方向 → 论文** 两级编号。每个文件夹里的 `README.md` 是**复现方案**（目标 / 数据 / 步骤 / 验收），
克隆的上游代码、数据集与产物都放进同一个文件夹，目录约定见文末。

> 索引里的每条链接都在建目录时实测过 HTTP 状态码；本文档末尾注明了检查结果与修正。

---

## 目录 Index

| 编号 | 方向 | 复现对象 | Venue | 为什么在这 | 状态 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **01-01** | D1 | [DynamicMap_Benchmark](01_robust_localization_slam_dynamic/01_dynamicmap_benchmark/) | ITSC 2023 | 点级变化 GT + 统一指标，全部对比的地基 | ⬜ |
| **01-02** | D1 | [KISS-ICP](01_robust_localization_slam_dynamic/02_kiss_icp/) | RA-L 2023 | 下游定位器基线，CPU 可跑 | ⬜ |
| **01-03** | D1 | [ERASOR](01_robust_localization_slam_dynamic/03_erasor/) | RA-L 2021 | 阈值敏感方法的代表 | ⬜ |
| **01-04** | D1 | [Removert](01_robust_localization_slam_dynamic/04_removert/) | IROS 2020 | 唯一带显式回滚（revert）的方法 | ⬜ |
| **01-05** | D1 | [DUFOMap](01_robust_localization_slam_dynamic/05_dufomap/) | RA-L 2024 | 用光线投射区分「被遮挡」与「真动态」 | ⬜ |
| **01-06** | D1 | [BeautyMap](01_robust_localization_slam_dynamic/06_beautymap/) | RA-L 2024 | 二值编码地面矩阵，免调参路线 | ⬜ |
| **01-07** | D1 | [DynoSAM](01_robust_localization_slam_dynamic/07_dynosam/) | T-RO 2025 | 物体级动态 SLAM，联合相机-物体评测 | ⬜ |
| **01-08** | D1 | [NGD-SLAM](01_robust_localization_slam_dynamic/08_ngd_slam/) | IROS 2025 | **纯几何**动态检测，不依赖语义先验 | ⬜ |
| **01-09** | D1 | [LT-mapper](01_robust_localization_slam_dynamic/09_lt_mapper/) | ICRA 2022 | 多会话长期建图 + 变化检测 | ⬜ |
| **02-01** | D2 | [3RScan](02_semantic_mapping_visual_anchoring_navigation/01_3rscan/) | ICCV 2019 数据 | 多会话物体重排的标准数据集 | ⬜ |
| **02-02** | D2 | [OASIS-Map](02_semantic_mapping_visual_anchoring_navigation/02_oasis_map/) | arXiv 2026-07 | **直接对手**，几乎同题；代码未发布 | ⬜ |
| **02-03** | D2 | [ConceptGraphs](02_semantic_mapping_visual_anchoring_navigation/03_concept_graphs/) | ICRA 2024 | 开放词汇场景图底座 | ⬜ |
| **02-04** | D2 | [DualMap](02_semantic_mapping_visual_anchoring_navigation/04_dualmaps/) | RA-L 2025 | 少数会**自我编辑**的开放词汇地图 | ⬜ |
| **02-05** | D2 | [HOV-SG](02_semantic_mapping_visual_anchoring_navigation/05_hov_sg/) | RSS 2024 | 分层开放词汇图 + 语言导航 | ⬜ |
| **02-06** | D2 | [Clio](02_semantic_mapping_visual_anchoring_navigation/06_clio/) | RA-L 2024 | 机载实时分层场景图 | ⬜ |
| **02-07** | D2 | [AnyLoc](02_semantic_mapping_visual_anchoring_navigation/07_anyloc/) | RA-L 2023 | 视觉锚定 / 场景识别（整图检索） | ⬜ |
| **02-08** | D2 | [Revisit Anything](02_semantic_mapping_visual_anchoring_navigation/08_revisit_anything/) | ECCV 2024 | 视觉锚定（**分割级检索**） | ⬜ |

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
> 正是 D 的地图修订与 V 的语义导航都要用的东西；而且 S 不需要新硬件，
> 四个底座都有公开代码，是唯一能先出结果的一条线。

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

**首先一个事实澄清**：我没有检索到以此为标题的已发表论文——这句是你自己在
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

仓库根目录的 [`car.md`](../car.md) 把两个方向拆成 8 个难点，每个都带可验证假设。
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

## 目录约定 Layout

```
reproductions/
├── README.md                      ← 本文件：索引 + 关联分析
├── 01_robust_localization_slam_dynamic/          ← D1
│   ├── README.md                  ← 方向说明 + 本方向复现顺序
│   └── 01_dynamicmap_benchmark/
│       ├── README.md              ← 复现方案（提交进 git）
│       ├── code/                  ← 克隆的上游仓库（.gitignore，不进 git）
│       ├── data/                  ← 数据集（不进 git）
│       ├── work/                  ← 我们自己写的脚本（进 git）
│       └── results/               ← 产物、图表（小的进 git）
└── 02_semantic_mapping_visual_anchoring_navigation/   ← D2
    └── ...（同上）
```

**为什么 code/ 和 data/ 不进 git**：上游仓库有自己的 git 历史，数据集动辄几十 GB。
本仓库只保留**我们写的**东西——步骤、脚本、配置、结论。

---

## 建议顺序 Suggested order

推进顺序是 **S →（D ∥ V）**，与任务书 §0.3 一致：

**第 1 步 · S 语义建图（先做，不需要新硬件）**

1. **02-01 3RScan**：先把**二次访问协议**写死（会话划分 + 真值类别 + 容差半径）——这是后面所有数字的前提
2. **02-03 / 02-04 / 02-06**：任选一个底座跑通，产出「物体节点 + 身份 + 标签」的表示层
3. **02-02 OASIS-Map**：与上面并行做论文精读（代码未发布，只能读）

**第 2 步 · D 与 V 并行（同等重要，进阶）**

4. **D 线**：01-01 评测地基 → 01-02 定位基线 → 01-03…01-06 四个清理方法（纯 CPU，5 天可出数字）
5. **D 线**：01-08 纯几何动态检测（car.md 难点 1 的首选入口）→ 01-09 长期建图对照
6. **V 线**：02-07 → 02-08 视觉锚定成对复现（补上任务书 §0.2 承认缺失的那块）→ 02-05 语言导航入口

**第 3 步 · 交汇**

7. 用 X（物体级变化检测）的指标同时回灌 S 与 D：可观测性分层 F1、身份一致率、ECE

> 备选：01-07 DynoSAM。按需要展开，不要在它上面卡住主线。

> **开工前先读一遍 [`docs/task-book/TASK_BOOK.md`](../docs/task-book/TASK_BOOK.md) 与 [`car.md`](../car.md)**：
> 任务书 §0.3 给出三方向的难点清单，car.md 给出 8 个难点的可验证假设。
> 复现的目标不是「跑通」，而是**为某个具体假设产出证据**——每个文件夹的「复现目标」一栏
> 就是这句话的落地。

---

## 链接核验 Link check

建目录时逐条实测（`curl -o /dev/null -w '%{http_code}'`，跟随重定向），共 23 条链接：

| 结果 | 说明 |
| :--- | :--- |
| ✅ 200 | 21 条代码库 / 论文 / 项目页链接全部可达 |
| ⚠️ **修正 1 条** | `github.com/KTH-RPL/BeautyMap` **返回 404**。BeautyMap 的正确仓库是 [`MKJia/BeautyMap`](https://github.com/MKJia/BeautyMap)（已实测 200）。上游 `Localise/01_task_books/materials/links.md` 记的 KTH-RPL 地址是错的 |
| ℹ️ 1 条非资源 | OASIS-Map 项目页可达，但明确标注 **Code Soon**，无代码可 clone |
