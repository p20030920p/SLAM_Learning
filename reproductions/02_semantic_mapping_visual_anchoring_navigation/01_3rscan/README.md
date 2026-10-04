# 02-01 · 3RScan

| 项 Item | 内容 |
| :--- | :--- |
| 论文 | 3RScan（数据集）—— 源自 RIO: 3D Object Instance Re-Localization in Changing Indoor Environments |
| Venue | **ICCV 2019**（数据集）；多会话重访标准集 |
| 论文链接 | [arXiv:1908.06109](https://arxiv.org/abs/1908.06109) |
| 代码 | [WaldJohannaU/3RScan](https://github.com/WaldJohannaU/3RScan) ✅ 实测 200 |
| 数据 | 3RScan 本体（需同意条款后下载），约 1.5k 次扫描 / 数百个房间 |
| 方向 | D2 · 语义建图、视觉定位与导航 |
| 任务书对应 | §4.1 地图更新策略；物体级变化检测题目的评测数据 |
| 复现状态 | 🟢 协议已跑通（1 对会话），待全量数据 |

## 它做了什么 What it does

同一个房间被**多次扫描**，并对房间内物体做了实例级标注与**重排（rearrangement）**标注——也就是「哪个物体在第几次扫描里被移动/替换了」。

## 为什么复现它 Why

**这是整个变化检测题目的数据瓶颈所在。** 现有语义建图数据集几乎都是「静态单次采集」，没有重访协议；3RScan 是少数例外，也是 OASIS-Map 用的室内数据。没有它，跨会话身份一致率这类指标根本无从计算。

## 复现目标（可验收）Goals

- [ ] 拿到数据，确认标注文件格式（物体 ID / 6DoF 位姿 / 扫描间对应关系）
- [ ] **组装出至少一对 A/B 会话**：A 建图，B 是同一房间物体被移动后的重访
- [ ] 写死二次访问协议：会话划分、真值类别（未变/移动/移除/新增/替换）、**容差半径**
- [ ] 输出：协议文档 + 一对可用会话的数据清单

## 步骤 Steps

1. 到仓库 README 指定入口申请/同意条款并下载
2. 解压后先只处理**一个房间**，把 A/B 两次扫描的物体标注对齐成一张表
3. 把协议写进本文件夹的 `work/protocol.md`（**先写死再跑**，不能事后调）

## 坑与注意 Pitfalls

- 需要同意条款，**不是直接 clone 就能用**；先办手续再排时间。
- 标注是**扫描级**的，不是天然按「会话」组织，A/B 会话要自己组装 —— 这步是主要工作量。
- 容差半径（判断「同一个物体」的位置阈值）必须写进报告，默认建议 0.5 m 并说明理由。

## 复现结果 Results（2026-10-04）

> 完整协议见 [`work/protocol.md`](work/protocol.md)；脚本 [`work/build_ab_pair.py`](work/build_ab_pair.py)；
> 产物 [`results/ab_pair.json`](results/ab_pair.json) · [`results/ab_pair.csv`](results/ab_pair.csv)。

**已自动化**：本文件夹有 [`reproduce.py`](reproduce.py)，由 `python3 reproductions/run_all.py` 驱动，
指标与 [`baselines.json`](baselines.json) 比对做回测。

```bash
python3 reproductions/run_all.py --only 02-01
```

### 每次运行自动验的四条不变量（`checks`）

| 检查 | 内容 | 本次结果 |
| :--- | :--- | :--- |
| `matrix_layout` | 行向量读法把结构物放在原位，列向量读法甩出几米 —— **用反证法证明约定** | ✅ 行向量误差 ≤ 0.324 m，列向量 ≥ 1.849 m（差 5.7 倍） |
| `object_transform_alignment` | `rigid[i].transform` 已含会话对齐：`T·c_A` 复现 `c_B` | ✅ 5 个移动物体，最大误差 0.1117 m |
| `class_partition` | 32 个实例每个恰好落进一个类别 | ✅ 32 / 32 |
| `tolerance_above_noise` | 容差必须大于未动物体的对齐残差 | ✅ 0.639 m < 1.0 m |

### 记录为 finding 的测量结果（不阻塞运行）

| finding | 内容 |
| :--- | :--- |
| `geometric_separation` | **最小真实位移 0.265 m < 最大对齐噪声 0.639 m** —— 纯几何质心差分在这一对上**分不开**移动与未动 |

> 这条 finding 本身就是那条假设的第一个证据：几何阈值不可靠，所以「可观测性感知」才有存在空间。

**已跑通一对真实会话**（公开示例数据自带的 reference + rescan）：

| 项 | 值 |
| :--- | :--- |
| 场景 A / 重访 B | `4acaebcc-…410d` / `754e884c-…198d`（train split） |
| 物体总数 | 32 |
| unchanged / moved / nonrigid / removed / **absent_unlabelled** / appeared | **26 / 5 / 0 / 0 / 1 / 0** |
| 会话间全局平移 | 1.604 m |

**三条实测结论**（都是协议必须写死的约定）：

1. **矩阵是行向量约定**（平移在最后一行）。用列向量解析会把地板/墙/天花板放到 3.2–4.9 m 之外；
   行向量下残差 0.03–0.32 m。
2. **`rigid[i].transform` 已包含会话对齐**：`T·c_A` 复现 `c_B` 到 0.014–0.112 m。
   所以它的平移量（1.15–3.03 m）**不是**物体位移；真实位移 = `|M·T·c_A − c_A|` = 0.26–1.09 m。
3. **容差 0.5 m 偏小**：26 个未动物体的对齐残差最大 **0.639 m**，已超过 0.5 m
   —— 意味着不动物体仅凭噪声就会被判成「移动」。协议改用 **1.0 m**，且换场景需重标定。

**发现的数据集缺口**（不是脚本的 bug，必须写进报告）：

- **id=23（cushion）从 B 的实例标注里消失，却不在 `removed` 表中**。
  数据集没有区分「真被拿走」和「本次没分割出来」——**这正是那道题目要解决的问题本身**，
  所以脚本把它单列为 `absent_unlabelled`，绝不并进 `removed`。
- 数据集**没有 `added` 表**，`appeared` 只能推导。
- 数据集**不标注可观测性**，因此这套 GT 只能验证「变化检测准不准」，
  无法直接验证「系统是否知道自己不确定」——要检验 H1a 必须自己造遮挡与部分视角。

## 记录 Log

| 日期 | 做了什么 | 结果 / 数字 | 结论 |
| :--- | :--- | :--- | :--- |
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
