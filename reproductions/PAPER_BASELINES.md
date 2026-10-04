# 论文报告值 Paper Baselines

> **这份文件存在的理由**：复现的前提是**先知道要复现出什么数**。
> 在 2026-10-05 之前，本仓库 17 个复现文件夹里只有"论文标题 + 计划"，
> **没有一篇记录原论文到底做出了什么数字**——于是"复现"没有验收标准，
> 跑通了也只能说"它能跑"，不能说"复现了"。
>
> 这一页把每篇原文的**自报结果**集中列出，并指出**能不能在这台机器上复现它**。
> 每个文件夹里的 `paper_baseline.md` 是详细版（含表号、页码、消融、参数、阻塞分析）。

**核对日期**：2026-10-05 · **原文来源**：本地 `Localise/01_task_books/materials/papers_pdf/`（134 篇）
+ 本次补取 3 篇（RIO/3RScan、原始 ERASOR、OASIS-Map）· **覆盖 16/17，缺 1 篇（Removert，闭源）**

---

## 一、总表：每篇论文自报的头号数字

| # | 复现对象 | Venue | 论文自报的头号结果 | 本机可行性 | 详细 |
| :-- | :--- | :--- | :--- | :--- | :--- |
| **01-01** | DynamicMap_Benchmark | ITSC 2023 | KITTI 00，Octomap w GF：SA/DA/AA = **93.06 / 98.67 / 95.83** | 🟢 数据已到手（Zenodo 直链） | [→](01_robust_localization_slam_dynamic/01_dynamicmap_benchmark/paper_baseline.md) |
| **01-02** | KISS-ICP | RA-L 2023 | KITTI 00–10 相对平移误差 **0.50%** | 🟡 **代码已跑通（0.409 %）但论文数字未复现**——论文四套数据集全部要注册 | [→](01_robust_localization_slam_dynamic/02_kiss_icp/paper_baseline.md) |
| **01-03** | ERASOR | RA-L 2021 | SemanticKITTI 00，voxel-wise PR/RR/F1 = **93.980 / 97.081 / 0.955** | 🟡 CPU 可跑，数据需注册 | [→](01_robust_localization_slam_dynamic/03_erasor/paper_baseline.md) |
| **01-04** | Removert | IROS 2020 | ⚠️ **原文已拿到（在作者仓库里），但全文没有数字表** | ✅ 已复现（基准口径） | [→](01_robust_localization_slam_dynamic/04_removert/paper_baseline.md) |
| **01-05** | DUFOMap | RA-L 2024 | KITTI 00，SA/DA/AA = **97.96 / 98.72 / 98.34** | ✅ **已复现（精确命中）** | [→](01_robust_localization_slam_dynamic/05_dufomap/paper_baseline.md) |
| **01-06** | BeautyMap | RA-L 2024 | KITTI 01，SA/DA/HA = **99.17 / 92.99 / 95.98** | 🟡 CPU 可跑，数据需注册 | [→](01_robust_localization_slam_dynamic/06_beautymap/paper_baseline.md) |
| **01-07** | DynoSAM | T-RO 2025 | OMD (S4U) 相机 ATE **0.11 m** | 🔴 需 CUDA + TensorRT | [→](01_robust_localization_slam_dynamic/07_dynosam/paper_baseline.md) |
| **01-08** | NGD-SLAM | IROS 2025 | TUM f3/w xyz **ATE 0.015 m**，CPU 16.72 ms/帧 | ✅ **已复现（ATE / RPE-平移命中）** | [→](01_robust_localization_slam_dynamic/08_ngd_slam/paper_baseline.md) |
| **01-09** | LT-mapper | ICRA 2022 | delta map **85.7 MB vs 213.6 MB**，**9.8 s vs 87/160 s** | 🟡 ROS 1（EOL），关键序列需联系作者 | [→](01_robust_localization_slam_dynamic/09_lt_mapper/paper_baseline.md) |
| **02-01** | 3RScan / RIO | ICCV 2019 | 1482 scans / 478 场景 / 1004 rescan；RIO-D Recall@<0.2m,20° = **23.76** | 🟡 本机已有 1 对（32 物体）；全量需申请 | [→](02_semantic_mapping_visual_anchoring_navigation/01_3rscan/paper_baseline.md) |
| **02-02** | OASIS-Map | arXiv 2026-07 | 3RScan **moved F1 0.353** / static F1 0.663；Car Park Replaced F1 **0.783** | 🔴 代码未发布 | [→](02_semantic_mapping_visual_anchoring_navigation/02_oasis_map/paper_baseline.md) |
| **02-03** | ConceptGraphs | ICRA 2024 | Replica **mAcc 40.63 / F-mIoU 35.95** | 🔴 需 GPU + 付费 GPT-4 | [→](02_semantic_mapping_visual_anchoring_navigation/03_concept_graphs/paper_baseline.md) |
| **02-04** | DualMap | RA-L 2025 | 地图修订后 SR **60.3%**（未修订 47.2%）；Replica FmIoU 0.5207 | 🔴 需 RTX 4090 | [→](02_semantic_mapping_visual_anchoring_navigation/04_dualmaps/paper_baseline.md) |
| **02-05** | HOV-SG | RSS 2024 | ScanNet **mIOU 0.222 / F-mIoU 0.303 / mAcc 0.431** | 🔴 需 GPU | [→](02_semantic_mapping_visual_anchoring_navigation/05_hov_sg/paper_baseline.md) |
| **02-06** | Clio | RA-L 2024 | Replica **mAcc 37.95 / F-mIoU 36.98** | 🔴 需 RTX 3090 | [→](02_semantic_mapping_visual_anchoring_navigation/06_clio/paper_baseline.md) |
| **02-07** | AnyLoc | RA-L 2023 | Baidu Mall **R@1 75.2** | 🔴 需 GPU（ViT-G14） | [→](02_semantic_mapping_visual_anchoring_navigation/07_anyloc/paper_baseline.md) |
| **02-08** | Revisit Anything | ECCV 2024 | Baidu Mall **R@1 78.5**（SegVLAD-PreT） | 🔴 需 GPU + 6.65 GB 描述子库 | [→](02_semantic_mapping_visual_anchoring_navigation/08_revisit_anything/paper_baseline.md) |

---

## 二、本机可行性：能真跑的是哪些（2026-10-05 更新）

这台机器**没有 GPU**（`nvidia-smi` 不存在，20 核 CPU / 15 GB RAM / 381 GB 空闲）。

| 类别 | 数量 | 哪些 |
| :--- | ---: | :--- |
| 🟢 **本机已跑通** | 8 | **D 线清理链路 01-01 / 01-03 / 01-04 / 01-05 / 01-06**（全部命中基准表 I；01-03 与 01-04 现在跑的是**官方仓库**）· **01-08 NGD-SLAM**（ATE 与 RPE-平移命中）· **01-02 KISS-ICP**（代码跑通，0.409 %，但论文的 0.50 % 需要注册 KITTI）· **02-01 3RScan**（本机那一对会话） |
| 🟡 **CPU 可跑，缺数据或论文数字不可比** | 1 | 01-09 LT-mapper（官方仓库已克隆；见其 `work/feasibility.md`） |
| 🔴 **需要 GPU（硬门槛）** | 7 | 01-07 DynoSAM（**构建期就要 CUDA**，见 `work/feasibility.md`）· 02-03 ConceptGraphs · 02-04 DualMap · 02-05 HOV-SG · 02-06 Clio · 02-07 AnyLoc · 02-08 Revisit Anything |
| ⚫ **上游没有可跑的代码** | 1 | 02-02 OASIS-Map（项目页至今 *Code Soon*） |

> 这 17 个文件夹现在**每个都有一份 `reproduce.py`**：能跑的会跑并自报指标，
> 跑不了的由 `require()` 直接说明缺什么（哪张卡、哪个数据集、还是上游没发代码）。
> 于是进度表里的 ⛔ 是**带理由的阻塞**，不是"没做"。

> **这解释了一件事**：任务书 §0.3 把 S（语义建图）排在第 1 位，理由是"不需要新硬件"。
> 但从**论文报告值**看，S 线的四个底座（ConceptGraphs / DualMap / HOV-SG / Clio）**全都要 GPU**。
> 真正"不需要新硬件"的是 **D 线的 CPU 部分**，而它现在已经复现出了四组数字。

---

## 二之二、已经复现出来的东西（2026-10-05）

四个清理方法在同一份数据（KITTI 00，141 帧，Zenodo 免注册）、同一套官方评测器下跑完：

| 方法 | 本次 SA | 本次 DA | 本次 HA | 本次 AA | 论文参照值 | 差值 |
| :--- | ---: | ---: | ---: | ---: | :--- | :--- |
| Removert（01-04） | **99.4361** | **41.5313** | **58.591** | **64.2628** | 99.44 / 41.53 / 58.59 / 64.26 | < 0.01 pp |
| ERASOR（01-03） | **66.7078** | **98.5352** | **79.5563** | **81.0744** | 66.70 / 98.54 / 79.55 / 81.07 | < 0.01 pp |
| BeautyMap（01-06） | 96.9529 | 98.3382 | **97.6407** | 97.6431 | 96.76 / 98.38 / 97.56 | ≤ 0.19 pp |
| DUFOMap（01-05） | **97.9635** | **98.7196** | 98.3401 | **98.3408** | 97.96 / 98.72 / — / 98.34 | < 0.01 pp |

**四个方法、两个独立的论文来源（DynamicMap_Benchmark / DUFOMap / BeautyMap），数字全部对上。**

### 01-03 ERASOR 与 01-04 Removert：换成官方仓库之后（2026-10-05 补）

这两条原先跑的是基准里的无 ROS 重实现。现在官方仓库都能编译并跑通（ROS 1 由
micromamba + robostack 提供，见 §二之三），于是**「重实现能不能代表原方法」这个问题第一次有了数字**：

| | 官方实现 | 基准重实现 | 差 |
| :--- | ---: | ---: | ---: |
| **ERASOR**（各自的口径） | PR/RR/F1 = **95.622 / 94.412 / 0.950**（论文表 II：93.980 / 97.081 / 0.955） | SA/DA/AA = 66.71 / 98.54 / 81.07（基准表 I，命中） | 口径不同，**两边都自洽** |
| **Removert**（同一份 141 帧、同一个点级评测器） | SA/DA/AA = **99.62 / 89.25 / 94.29** | SA/DA/AA = 99.44 / **41.53** / 64.26（基准表 I，命中） | **DA 差 47.7 pp** |

**结论分两半，两半都重要：**

1. **ERASOR 的重实现是可信的**：官方版本在论文自己的口径下复现到 F1 差 0.005，重实现在基准口径下
   命中表 I —— 差异来自**指标定义**（voxel-wise vs 点级、0.2 m 体素 vs 0.05 m 最近邻），不是实现质量。
2. **Removert 的重实现不是可信的替代品**：静态保留率几乎一样（99.62 vs 99.44），
   **动态剔除率差 47.7 pp**。基准里"Removert 几乎不删"的形象是重实现的产物。
   于是任务书 §6 H1′ 的前提要改一句：**比较方法排名之前，先确认每个方法跑的是它自己的代码。**

> 两条都记在各自文件夹的 README 与 `baselines.json` 里，且都由 `run_all.py` 自动回测。

### 01-02 KISS-ICP：论文的四套数据集全都拿不到

KISS-ICP 的论文在 **KITTI odometry / MulRan / Newer College / Boreas** 上评测，**四套全部需要注册或表单**
（NCD 的官网下载页没有直链，且其下载已被社区记录为失效）。

只用免费数据能做到的：基准的 Zenodo KITTI 00 包（385 MB，免注册）里的 141 帧是**世界系**点云 + 位姿，
逆变换可以把**原始扫描还原回来**，于是官方的 `--dataloader kitti` 一行不改就能跑：

| | 值 |
| :--- | ---: |
| 本次平均相对平移误差 | **0.409 %** |
| ATE | 0.112 m |
| 频率 / 单帧耗时 | 50 Hz / 20 ms |
| 轨迹长度 | 108.3 m |
| **指标实际样本数** | **2** |
| 论文（KITTI 00–10） | 0.50 % |

⚠️ **0.409 % 不是论文那个数**：KISS-ICP 用的是 KITTI devkit 指标，段长 **{100…800} m**、起点每 10 帧一个，
而这条轨迹只有 108.3 m → **只凑得出 2 个样本**；论文是 11 条完整序列上数百个样本的聚合。
**要复现 0.50 % 必须先注册 KITTI。**

### 01-08 NGD-SLAM：论文用的不是几何方法

**这是读代码推翻了计划里的一条判断。** 本目录原来把 NGD-SLAM 描述成「不用神经网络做分割，
改用光流 + 深度方差」——**错的**。它的官方仓库（论文自己给的地址）里 `System.cc:217` 明确创建了
YOLO-fastest-xl 语义线程。它真正的贡献是**让追踪不再等网络**：

| 机制 | 代码位置 | 效果 |
| :--- | :--- | :--- |
| 掩码传播 | `Tracking.cc:4286`（腐蚀 → 15 px 栅格采样 → LK 光流 → DBSCAN → 画回掩码） | 网络只需要偶尔给一次真值，中间帧用光流推 |
| 追踪不阻塞 | `Tracking.cc:1592` 的 `else if(mFrameNum > 1) break;` | 除第 1 帧外，追踪从不等待语义线程 |
| 非关键帧不提 ORB | `Tracking.cc:1602` 建空帧 + `ORBmatcher.cc:2012` 纯光流匹配 | 省掉描述子计算 |
| 兜底 | `Tracking.cc:3381` 分级规则（内点 <20 立即切，<75 隔 5 帧，<300 隔 30 帧） | 光流不可靠时退回完整 ORB |

复现结果：**ATE 0.0157 m（论文 0.015）、RPE 平移 0.0201 m/s（论文 0.020）都命中**；
RPE 旋转按 RMSE 是 0.604 而论文 0.470，按**均值**是 0.475——论文表头没写是哪个统计量，**未解差异**。

→ 对计划的影响：**car.md 难点 1 不能拿 NGD-SLAM 当「纯几何运动视差」的证据**，
它依赖 YOLO 的 COCO 类别，未知动态物体同样漏。

### 顺带得到的两条结论

1. **排名随指标翻转**：按 SA 排是 Removert > DUFOMap > BeautyMap > ERASOR，
   按 AA 排是 DUFOMap > BeautyMap > ERASOR > Removert。
   **SA 第一的 Removert 在综合指标里是倒数第一** —— 因为它几乎不删，而动态点只占 GT 的 **0.55%**。
   这正是任务书 §6 H1′ 的问题（排名是否稳定），现在有了它自己的数字。
2. **SA 低 ≠ 算法差**：ERASOR 输出地图只有 1,417,955 点（它内部按 0.1 m 体素化），
   而 GT 有 17,362,230 点，于是"0.05 m 内无邻居即判删除"把 **5,748,315** 个静态点读成删除，
   真正漏掉的动态点只有 **1,406**。**评测器把分辨率损失算成了删除错误** ——
   任何"用下游定位来衡量清理质量"的实验都必须先扣掉这一项。

---

## 二之三、一个必须澄清的问题：哪些是"按原文复现"，哪些不是

**2026-10-05 更新：这条已经全部解决。** 之前被标为"不符合、待重做"的 01-03 / 01-04，
现在跑的**都是官方仓库**，用的是官方数据与官方评测器 —— 见下表与每个文件夹的 README。

| 复现 | 跑的是谁的代码 | 目标数字来自 | 判定 |
| :--- | :--- | :--- | :--- |
| **01-05 DUFOMap** | ✅ **官方 PyPI 包**（KTH-RPL 自己的 `dufomap`） | ✅ DUFOMap 论文 表 I | **符合** |
| **01-06 BeautyMap** | ✅ **官方仓库 MKJia/BeautyMap** | ✅ BeautyMap 论文 表 I | **符合** |
| **01-08 NGD-SLAM** | ✅ **官方仓库 yuhaozhang7/NGD-SLAM** | ✅ NGD-SLAM 论文 表 I | **符合** |
| 02-01 3RScan | ✅ 官方工具箱 WaldJohannaU/3RScan | 数据集论文 | **符合** |
| **01-03 ERASOR** | ✅ **官方仓库 LimHyungTae/ERASOR**（`kitti_mapgen` + `offline_map_updater`） | ✅ **ERASOR 论文表 II**（评测器与 GT 都是作者的） | **✅ 已重做，符合** |
| **01-04 Removert** | ✅ **官方仓库 irapkaist/removert**（`removert_removert`） | ⚠️ 原文没有编号表格 → 以官方输出 + 基准同口径对比为目标 | **✅ 已重做，符合** |
| 01-01 基准 | — | 它是基准本身，不是方法 | — |

**01-03 / 01-04 是怎么重做的**（原先的判断是"ROS 1 + 无 Docker + 无 sudo ⇒ 跑不了原版"，**这条不成立**）：

1. **ROS 1 不需要 root**：micromamba + robostack-staging 把 Noetic 装进
   `reproductions/.venvs/ros1noetic`（不需要 sudo，也不需要 Docker）。
   empy 必须钉在 3.3.4，否则 Noetic 的消息生成会报 `module 'em' has no attribute 'RAW_OPT'`。
2. **ROS 2 会污染 ROS 1**：本机 shell 里 source 了 Jazzy，而两代 ROS 有同名库
   （`libimage_transport.so` 等），ROS 1 二进制会在运行时加载到 ROS 2 的库并崩在
   `symbol lookup error`。`reproductions/tools/ros1_env.sh` 负责剥掉 `/opt/ros/jazzy*`。
3. **上游源码要打 API 漂移补丁**（PCL ≥ 1.11 的 `shared_ptr`、`PassThrough::setNegative`、
   OpenCV 4 删掉的 `<opencv/cv.h>`），逐条记在各自的 `work/local_patches.patch`，
   **算法本身一行未改**。
4. **数据**：ERASOR 官方 README 自己提供 seq-00 rosbag 与全部 PCD/GT（直链可下）；
   Removert 的上游只要求 KITTI 格式的 `.bin` + `poses.txt`，基准的 Zenodo 包可以反变换出来。

> 复现这两条的直接后果见 01-04 的 README：**Removert 在基准重实现下的"最保守"形象是重实现的产物**
> （官方 DA 89.25 vs 重实现 41.53）。也就是说，**要比较方法排名，先确认每个方法跑的是它自己的代码。**

> 另外按「**没有库的先不复现**」的规则：**02-02 OASIS-Map 仍排除**（代码未发布，只有项目页写着 Code Soon）。

## 三、三处只有对着原文才会发现的坑

### 3.1 ⚠️ 同一个方法，换一套口径，结论反过来

| 方法 | 它自己论文里的静态点保留 | 在 DynamicMap_Benchmark 里的点级 SA |
| :--- | ---: | ---: |
| **ERASOR** | **93.98 %**（voxel-wise PR，SemanticKITTI 00） | **66.70 %**（KITTI 00） |
| **Removert** | **85.50 %**（voxel-wise PR，SemanticKITTI 00） | **99.44 %**（KITTI 00） |

**ERASOR 自报最好，在基准里却最差；Removert 自报较差，在基准里却最好。**
两边的差异都不是噪声，是**指标定义**（voxel-wise vs 点级）与**数据/帧段**的差异。

→ 这正是任务书 **§6 并行实验 H1′**（F1 排名 vs 定位效用排名是否一致）要问的问题，
而它**已经出现了一次，且不需要任何新数据**。这是本次最值得往下列的一条线。

### 3.2 ⚠️ 上游示例的参数与论文不一致（已用数字证明）

`DynamicMap_Benchmark/methods/dufomap/main.py` 写的是 `dufomap(0.1, 0.2, 2)`，
注释说 `# resolution, d_s, d_p same with paper`。**但论文的默认值是 `d_p = 1`**（表 IV, p.7）。

| 配置 | SA | DA | AA |
| :--- | ---: | ---: | ---: |
| `d_p=2`（上游示例写的） | 99.8853 | 96.6338 | 98.2461 |
| **`d_p=1`（论文的默认）** | **97.9635** | **98.7196** | **98.3408** |
| **论文表 I, p.5** | **97.96** | **98.72** | **98.34** |

**只有 `d_p=1` 才命中论文。** 而 `d_p=2` 的 AA（98.25）看起来也只差 0.09 —— 因为
**AA 是几何平均，而动态点只占 0.55%，所以 AA 几乎就是 SA**，它区分不出"保守的清理器"和"激进的清理器"。
换句话说：**如果只看 AA，我们会误以为上游示例是对的。**

### 3.3 ⚠️ 任务书 §0.2 的判断需要再收窄一次

任务书 §0.2 / README 里写的切入角度是"内容变化下的定位/识别没有被评测过"。
对着原文核实后，**这个说法一半对一半错**：

| 论文 | 内容变化（物体被移动/替换）下的表现 | 核实方式 |
| :--- | :--- | :--- |
| AnyLoc（02-07） | `论文未报告` | 10 页全文检索 furniture/rearrang/removed/added/layout/content，仅 2 处无关命中 |
| Revisit Anything（02-08） | `论文未报告` | 29 页含补充材料，零命中；其 Table 3 的 220 个 Baidu OOI 是**同一次访问**的部件-整体匹配，物体没动 |
| **RIO / 3RScan（02-01）** | ✅ **报告了**：静态→动态 RIO-D Recall@<0.2m,20° **17.75 → 23.76**，F1 **85.58 → 94.37** | 原文 §3.4 / §5.2，表 3/4/5 |

→ **准确表述**：*内容变化的 **3D 重定位**评测存在（RIO），但内容变化下的 **VPR（图像检索）**评测不存在* ——
没有人用 AnyLoc/SegVLAD 这类检索方法跑过 3RScan 的 A/B 会话。
这比原来的说法**更窄、更难被反驳**，也更接近可执行的实验。

### 3.4 跨会话物体身份：只有 OASIS-Map 在正式评测它

| 论文 | 是否评测"跨会话物体身份" |
| :--- | :--- |
| ConceptGraphs（02-03）· HOV-SG（02-05）· Clio（02-06） | `论文未报告`（HOV-SG 更是明说"假设静态环境、无法处理动态环境"） |
| DualMap（02-04） | 报的是**单次在线会话内**的物体搬迁恢复（SR 47.2% → 60.3%），仍非跨会话 |
| **OASIS-Map（02-02）** | ✅ 表 I 专门有 `Assoc.` 列 + 表 III 专测身份保持；ConceptGraphs 在该列是 `✗` |

→ 任务书 §0.3 那条修正因此成立：**不能把"缺少跨会话身份"当空白点**（OASIS-Map 有），
只能把**可观测性变成可标定的量并分层测量**当作差异点。

---

## 四、还缺什么

| 缺口 | 状态 |
| :--- | :--- |
| ~~01-04 Removert 原文~~ | ✅ **已在作者仓库 `irapkaist/removert` 根目录找到**（`gkim-2020-iros.pdf`）。我先前据 OpenAlex 判它闭源是错的——`is_oa` 只描述出版商侧。**教训：先克隆仓库再下结论** |
| 17 篇原文 | ✅ **全部在手** |
| 01-04 的可对标数字 | ⚠️ **原文没有编号表格**（`TABLE` 命中 0 次），定量结果是图 8/图 9 的曲线。所以只能以**官方实现自己的输出 + 基准同口径对比**为目标（已完成） |
| ~~01-03 / 01-04 不是官方代码~~ | ✅ **已重做**：micromamba + robostack 装 ROS 1（不要 root），官方仓库编译并跑通，见 §二之三 |
| KITTI / SemanticKITTI / Argoverse 2 原始数据 | 🟡 需注册。**但 01-01/01-05 已用 Zenodo 直链绕过**（KITTI 00 + GT，385 MB，免注册）。**01-03 更彻底：官方 README 里的 seq-00 rosbag 与全部 PCD/GT 都是直链，免注册** |
| 各复现的 `reproduce.py` | **17/17**。其中 8 个会真跑并自报指标（01-01 · 01-02 · 01-03 · 01-04 · 01-05 · 01-06 · 01-08 · 02-01，全部带 `baselines.json` 回测），其余 9 个的 `require()` 直接返回**具体阻塞原因**（无 GPU / 上游未发代码 / 构建期要 CUDA） |
| GPU | 🔴 **本机没有**。这是 D2 线 6 个底座 + 01-07 DynoSAM 的唯一阻塞；数据与代码都已确认可得（见各 `paper_baseline.md` 与 `07_dynosam/work/feasibility.md`） |
