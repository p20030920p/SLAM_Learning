<div align="center">

# 02-01 · 3RScan

**同房间多次扫描 + 物体重排标注的标准数据集 —— 用官方工具箱把 A/B 会话协议与「可观测性」判据落地。**

[![venue](https://img.shields.io/badge/venue-ICCV%202019%20dataset-22314E)](https://arxiv.org/abs/1908.06109)
![result](https://img.shields.io/badge/result-protocol%20%2B%20observability-2ea043)
[![code](https://img.shields.io/badge/code-WaldJohannaU%2F3RScan-181717?logo=github&logoColor=white)](https://github.com/WaldJohannaU/3RScan)
![data](https://img.shields.io/badge/data-public%20sample%20pair-1c7ed6)
![compute](https://img.shields.io/badge/compute-CPU%20%C2%B7%20C%2B%2B%20tools-6f42c1)

[结论](#一句话-verdict) &nbsp;•&nbsp; [复现结果](#复现结果-results) &nbsp;•&nbsp; [怎么跑](#怎么跑-how-to-run) &nbsp;•&nbsp; [坑与注意](#坑与注意-pitfalls) &nbsp;•&nbsp; [记录](#记录-log)

*[← 复现区索引](../README.md) &nbsp;•&nbsp; [论文报告值](paper_baseline.md) &nbsp;•&nbsp; [复现脚本](reproduce.py) &nbsp;•&nbsp; [回测基线](baselines.json)*

</div>

---

## 一句话 Verdict

| | 本文件夹 | 全量数据集 |
| :--- | :--- | :--- |
| 数据 | **1 对 A/B 会话**（51 帧 · 32 个物体） | 1482 scans / 478 场景 / 1004 rescan（需申请表） |
| 已落地 | 官方三个二进制全跑通；A/B 协议 v1（容差 1.0 m，标定自实测噪声 0.639 m） | — |
| 可观测性 | 9 可见 / 4 被遮挡 / 16 视场外；库的可见性分数与自写 OBB 估计器 **22/31 一致**（分歧处库对） |
| 一条硬结论 | 最小真实位移 0.265 m **小于**最大对齐噪声 0.639 m → **纯几何分不开「移动」与「噪声」** | — |

## 关键设定 Settings

| 项 | 内容 |
| :--- | :--- |
| 本机怎么跑 | 纯 CPU · 官方三个 C++ 二进制（`rio_example` / `align_poses` / `rio_renderer_render_all`） |
| 论文 | 3RScan（数据集）—— 源自 RIO: 3D Object Instance Re-Localization in Changing Indoor Environments |
| 论文链接 | [arXiv:1908.06109](https://arxiv.org/abs/1908.06109) |
| 论文报告值 | [`paper_baseline.md`](paper_baseline.md) —— 原论文自报结果与复现阻塞分析 |
| 代码 | [WaldJohannaU/3RScan](https://github.com/WaldJohannaU/3RScan) ✅ 实测 200 |
| 数据 | 3RScan 本体（需同意条款后下载），约 1.5k 次扫描 / 数百个房间 |
| 方向 | D2 · 语义建图、视觉定位与导航 |
| 任务书对应 | §4.1 地图更新策略；物体级变化检测题目的评测数据 |
| 复现顺序 | 13 |
| 能否复现 | 🟡 半能：仓库只有数据集 + 工具（数据要签协议），三个二进制可跑，没有方法代码。 |
| 复现完成 | ◐ 工具已按官方说明跑通，待全量数据 |

---

## 它做了什么 What it does

同一个房间被**多次扫描**，并对房间内物体做了实例级标注与**重排（rearrangement）**标注——也就是「哪个物体在第几次扫描里被移动/替换了」。

## 为什么复现它 Why

**这是整个变化检测题目的数据瓶颈所在。** 现有语义建图数据集几乎都是「静态单次采集」，没有重访协议；3RScan 是少数例外，也是 OASIS-Map 用的室内数据。没有它，跨会话身份一致率这类指标根本无从计算。

## 复现目标（可验收）Goals

- [ ] 拿到数据，确认标注文件格式（物体 ID / 6DoF 位姿 / 扫描间对应关系）
- [ ] **组装出至少一对 A/B 会话**：A 建图，B 是同一房间物体被移动后的重访
- [ ] 写死二次访问协议：会话划分、真值类别（未变/移动/移除/新增/替换）、**容差半径**
- [ ] 输出：协议文档 + 一对可用会话的数据清单

## 怎么跑 How to run

1. 到仓库 README 指定入口申请/同意条款并下载
2. 解压后先只处理**一个房间**，把 A/B 两次扫描的物体标注对齐成一张表
3. 把协议写进本文件夹的 `work/protocol.md`（**先写死再跑**，不能事后调）

## 坑与注意 Pitfalls

- 需要同意条款，**不是直接 clone 就能用**；先办手续再排时间。
- 标注是**扫描级**的，不是天然按「会话」组织，A/B 会话要自己组装 —— 这步是主要工作量。
- 容差半径（判断「同一个物体」的位置阈值）必须写进报告，默认建议 0.5 m 并说明理由。

## 复现结果 Results

### 一、按库复现：把仓库自带的三个二进制跑起来

严格按 [`c++/README.md`](https://github.com/WaldJohannaU/3RScan/tree/master/c%2B%2B) 的说明搭建并运行
（数据也已按仓库要求摆成 `data/3RScan/<scan_id>/...`）：

| 二进制 | 仓库文档里的命令 | 本机实际产出 |
| :--- | :--- | :--- |
| `rio_example` | `./bin/rio_example ../../../data/3RScan 754e884c-…198d` | ✅ `mesh.refined.v2.align.obj`、`labels.instances.annotated.v2.align.ply`、`.global.ply`、31 条标签清单、原始位姿 + 归一化位姿、`frame-000028.cloud.ply` |
| `align_poses` | `./bin/align_poses ../../../data/3RScan <scan>` | ✅ 每个扫描 **51 个** `frame-XXXXXX.align.pose.txt` |
| `rio_renderer_render_all` | `./rio_renderer_render_all … <scan> sequence 0` | ✅ 每帧 `rendered.color.jpg` / `.depth.png` / `.labels.png` / `.instances.png` / `bb.txt` / **`visibility.txt`**，共 51 帧 |

**两个必须记录的坑**（环境/年代问题，不是代码问题）：

1. **README 的示例命令 `render_mode=1` 不会输出 occlusion**。看源码 `render_all_main.cc`：
   `save_occlusion = (render_mode == 0)`，而 `1 = only images`。要拿遮挡分数**必须传 `0`**。
2. **编译期两处要补**：`libglfw3-dev` / `libglm-dev` 装不了（无 sudo）
   → 用 `apt-get download` + `dpkg-deb -x` 解到本地前缀，再用 `GLFW_ROOT` /
   `CMAKE_PREFIX_PATH` 指过去；另外新版 CMake 的 `FindGLEW` 只设 `GLEW_LIBRARIES`（复数），
   而这是 2020 年的工程、读 `${GLEW_LIBRARY}`（单数）→ 必须显式
   `-DGLEW_LIBRARY=/usr/lib/x86_64-linux-gnu/libGLEW.so`，否则 `__glew*` 全部未定义。

### 二、库自己的对齐结果，反过来验证了协议

`align_poses` 写出的归一化位姿，与按 `3RScan.json` 的 `transform` 算出的结果**完全一致**：

| 读法 | 相机中心在参考系中的位置误差 |
| :--- | :--- |
| **行向量 `p @ M`** | ✅ **0.0000 m**（精确一致） |
| 列向量 `M @ p` | ❌ 1.5862 m |

→ 协议里靠内部一致性推出的矩阵约定，现在**被库自身的输出独立确认**。

### 三、库的 occlusion scores：比我自己那套更准

`visibility.txt` 每行（语义取自 `Renderer::CalcOcclusions` / `CalcTruncations`）：

```
instance_id  trunc_orig  trunc_full  trunc_ratio  occ_orig  occ_full  occ_ratio
```

- **occlusion ratio** = 全场景里可见的像素 ÷ **单独渲染该物体时**的像素 → 低 = 被别的物体挡住
- **truncation ratio** = 正常视场内的像素 ÷ **2 倍宽视场**内的像素 → 低 = 被视场/图像边界切掉

用库自己的分数汇总（51 帧，阈值 occ≥0.5 且 trunc≥0.2，至少 3 帧）：

| gt_class | visible | occluded | out_of_view | insufficient | not_in_B_scene |
| :--- | ---: | ---: | ---: | ---: | ---: |
| unchanged | 9 | 0 | 15 | 2 | 0 |
| moved | 3 | 0 | 2 | 0 | 0 |
| **absent_unlabelled** | 0 | 0 | 0 | 0 | **1** |

**与 OBB 估计器对比：31 个可比物体里 22 个一致（71%）。**

| 分歧 | 数量 | 谁对 |
| :--- | ---: | :--- |
| 我 `occluded` → 库 `visible` | 4 | **库对**：我采样 OBB 表面，含背对相机的面和底面，会虚报遮挡 |
| 我 `visible` → 库 `insufficient` | 2 | 阈值不同（库更严） |
| 我 `insufficient` → 库 `out_of_view` | 2 | **库对**：我采样点太少 |

→ **遮挡以库的渲染结果为准**，我那套只在库覆盖不到的地方用。

### 四、库覆盖不到的一格（这才是 OBB 估计器的价值）

那个「消失了却没被标成 removed」的垫子（id=23），库的工具给的是 **`not_in_B_scene`**：
渲染器画的是**该扫描自己的 mesh 和标注**，B 的标注里根本没有它 —— 所以库**对它沉默**，
而沉默不是证据。

要回答「它消失的位置当时可不可观测」，必须**拿 A 的 mesh 从 B 的位姿渲染**（跨扫描渲染），
库没有直接提供这条路。OBB 估计器给的答案是 **out_of_view**（51 帧从未进入视场）。

→ 准确说法：**库的渲染分数是权威的可观测性测量，但它测不了"已经消失的物体"；
而恰恰这一格承载了 H1a 那个问题。**

### 五、自动化与产物

协议 [`work/protocol.md`](work/protocol.md)；脚本
[`work/build_ab_pair.py`](work/build_ab_pair.py) · [`work/observability.py`](work/observability.py) ·
[`work/analyze_observability.py`](work/analyze_observability.py) · [`work/repo_visibility.py`](work/repo_visibility.py)；
产物 [`results/`](results/)（`ab_pair.*`、`observability.*`、`repo_visibility.*`）。

```bash
python3 reproductions/run_all.py --only 02-01
```

### 每次运行自动验的七条不变量（`checks`）

| 检查 | 内容 | 本次结果 |
| :--- | :--- | :--- |
| `matrix_layout` | 行向量读法把结构物放在原位，列向量读法甩出几米 —— **反证法证明约定** | ✅ 0.324 m vs ≥1.849 m（差 5.7 倍） |
| `object_transform_alignment` | `rigid[i].transform` 已含会话对齐 | ✅ `T·c_A` 复现 `c_B` 到 0.1117 m |
| `class_partition` | 32 个实例每个恰好落进一个类别 | ✅ 32/32 |
| `tolerance_above_noise` | 容差必须大于未动物体的对齐残差 | ✅ 0.639 m < 1.0 m |
| `depth_scale_plausible` | `m_depthShift` 是除数不是乘数（读反了深度差 1000 倍，`visible` 类会被静默清空） | ✅ 0.748–7.218 m |
| `poses_are_rigid` | 位姿必须是正交旋转 | ✅ 51/51 |
| `observability_partition` | 可观测性分层是完备划分 | ✅ 32/32 |

### 记录为 finding 的测量结果（不阻塞运行）

| finding | 内容 |
| :--- | :--- |
| `obb_estimator_versus_repo_renderer` | 两套可观测性测量在 22/31 个物体上一致（71%）；**分歧处库对** |
| `vanished_objects_are_not_all_observable` | 1/1 个从 B 消失的物体，其位置在 B 里不可观测 → 数据集的沉默不能读成「被移除」 |
| `observability_spreads_even_within_one_gt_class` | 同为 `unchanged` 的物体：visible 6 / occluded 4 / out_of_view 13 / insufficient 3 |
| `frame_coverage_is_partial` | 只发了 **51/753** 帧（轨迹前缀），`out_of_view` 是暂定结论 |
| `geometric_separation` | 最小真实位移 0.265 m < 最大对齐噪声 0.639 m —— 纯几何分不开 |

## 记录 Log

| 日期 | 做了什么 | 结果 / 数字 | 结论 |
| :--- | :--- | :--- | :--- |
| 10-05 | **按库编译并运行 `rio_example` / `align_poses`** | 产出 align.obj / align.ply / global.ply / 51×align.pose.txt | 仓库自带的复现路径全部跑通 |
| 10-05 | **编译并运行 `rio_renderer_render_all`（mode 0）** | 51 帧 × {color,depth,labels,instances,bb.txt,**visibility.txt**} | 拿到库自己的 occlusion / truncation 分数 |
| 10-05 | 交叉验证：库的归一化位姿 vs 协议的 `M` | **0.0000 m**（列向量读法 1.5862 m） | 矩阵约定被库独立确认 |
| 10-05 | 库的可见性分数 vs 我的 OBB 估计器 | 22/31 一致（71%） | **分歧处库对**（它渲染真 mesh） |
| 10-05 | 库对"已消失物体"的覆盖 | `not_in_B_scene`（库对它沉默） | 跨扫描渲染才是那一格的解 |
| 10-04 | 克隆官方仓库（8.5 MB，含 `rio_lib` C++ 与 `setup.sh`） | 200 | 仓库本体不含数据，只有读取工具 |
| 10-04 | 按 `setup.sh` 拉公开示例数据 | `3RScan.json` 3.1 MB + `3RScan.v2.zip` 39.9 MB | **无需申请表**；全量数据集才需要 |
| 10-04 | 解析 `3RScan.json` | 478 场景 / 1004 次 rescan；rigid 982、removed 240、nonrigid 274 | 多会话结构确认 |
| 10-04 | 确认示例数据是一对 A/B | 两个扫描恰为同一场景的 reference + rescan | 可以直接做变化检测 |
| 10-04 | 写 `build_ab_pair.py` 并跑通 | 32 物体 → 26/5/0/0/1/0 | 协议 v1 落地 |
| 10-04 | 标定对齐噪声 | 未动物体残差 mean 0.151 / p95 0.528 / max 0.639 m | **容差改 1.0 m** |

## 下一步 Next

1. **申请全量数据集**：项目页 <https://waldjohannau.github.io/RIO/> 的下载表单
   （<https://forms.gle/NvL5dvB4tSFrHfQH6>，3RScan Terms of Use）→ 拿到下载脚本后按 scan id 拉取。
   本机现有数据只有 **1 对**会话，统计上不足以支撑任何 F1 结论。
2. **造可观测性分层**：用 A、B 的相机位姿 + 深度图渲染「每个物体在 B 中是否可见 / 被遮挡 / 视场外」。
   这是协议目前最大的缺口，也是 H1a 的直接检验手段。
3. 有了分层后，才能把「可观测性分层 F1」和「未观测区分率」算出来。