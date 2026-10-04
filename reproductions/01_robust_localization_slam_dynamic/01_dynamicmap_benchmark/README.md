# 01-01 · DynamicMap_Benchmark

| 项 Item | 内容 |
| :--- | :--- |
| 论文 | A Dynamic Points Removal Benchmark in Point Cloud Maps |
| Venue | **ITSC 2023**（arXiv:2307.07260） |
| 论文链接 | [arXiv:2307.07260](https://arxiv.org/abs/2307.07260) |
| 论文报告值 | [`paper_baseline.md`](paper_baseline.md) —— KITTI 00，Octomap w GF：SA/DA/AA = **93.06 / 98.67 / 95.83** |
| 代码 | [KTH-RPL/DynamicMap_Benchmark](https://github.com/KTH-RPL/DynamicMap_Benchmark) ✅ 已克隆 |
| 数据 | ✅ **已到手**：[Zenodo 10886629](https://zenodo.org/records/10886629) 的 `00.zip`（385 MB，**免注册**）= KITTI 00 选定帧段 + 人工 GT |
| 方向 | D1 · 动态环境下的鲁棒定位与 SLAM |
| 任务书对应 | §6 并行实验（恢复自原 T1） |
| 复现状态 | 🟡 地基已跑通（数据 + 评测器 + 交叉验证）；四个方法的数字待跑 |

## 它做了什么 What it does

把「动态点删除」变成可横向比较的任务：提供人工标注的真值、统一的点级指标，并把 ERASOR、Removert、DUFOMap、BeautyMap 等方法重构成无 ROS 的统一实现，让它们第一次可比。

## 为什么复现它 Why

**所有对比的地基。** 没有同一套 GT 与同一套指标，四个清理方法的排名就不可比，任务书 §6 的 H1′ 也无从检验。

---

## 复现结果 Results（2026-10-05）

### 一、数据：KITTI 注册这一硬阻塞被绕开了

[`paper_baseline.md`](paper_baseline.md) 里分析出的最大阻塞是"KITTI / SemanticKITTI / Argoverse 2 全部需要注册下载"。
**但基准作者自己把选定帧段连同人工 GT 打包发在了 Zenodo 上，直链、免注册：**

```bash
wget https://zenodo.org/records/10886629/files/00.zip   # 384,805,963 B，66 秒
unzip 00.zip -d data/raw/
```

| 项 | 值 |
| :--- | :--- |
| 序列 | KITTI **00**（small town） |
| 帧数 | **141** 帧（`pcd/004390.pcd` … ），每帧 PCD 的 `VIEWPOINT` 就是传感器位姿 |
| GT | `gt_cloud.pcd`，**17,362,230** 点 |
| GT 标签分布 | 静态 **17,266,247** · 动态 **95,983**（动态仅占 **0.55%**） |

> **帧段对上了**：论文没写明用了哪些帧，但释出的数据是 4390–4530，
> 而这正是 [01-03 ERASOR](../03_erasor/paper_baseline.md) 论文里写死的 seq 00 帧段。**两个独立来源互相确认了评测集。**

### 二、评测器：官方 C++ 工具已编译，并且被第二条实现验证

基准的评测链是三步，我们全部保留：

| 步骤 | 工具 | 状态 |
| :--- | :--- | :--- |
| 1. 方法输出清理后的地图 | 各方法自己的 `work/` | ✅ |
| 2. 按最近邻重标 GT | `scripts/build/export_eval_pcd`（PCL `KdTreeFLANN`） | ✅ 已编译 |
| 3. 统计四个象限 | `work/evaluate.py` | ✅ 已写 |

规则：GT 点若在清理后的地图里 **0.05 m** 内找不到邻居，就判为「被删除」（label 1），否则 label 0。

**两条独立实现必须给出一致的标签**（`work/evaluate.py --impl both`）：

| 实现 | 语言 / 数据结构 | 在 01-05 的 DUFOMap 地图上 |
| :--- | :--- | :--- |
| `export_eval_pcd` | C++ / PCL `KdTreeFLANN` | SA 97.9635 / DA 98.7196 / AA 98.3408 |
| 本文件 `work/evaluate.py` | Python / scipy `cKDTree` | 同上 |

→ **17,362,230 个 GT 点，标签分歧 = 0。**

### 三、⚠️ 一处必须修正的口径：指标不是 PR/RR/F1

本 README 原来写的目标是"`evaluate.py` 输出 **PR / RR / F1**"。**对着仓库实际代码核实后，这是错的。**
基准释出的评测器（`scripts/py/eval/evaluate_all.py`）算的是：

```
SA = #(et=0 & gt=0) / #(gt=0)      静态点保留率
DA = #(et=1 & gt=1) / #(gt=1)      动态点删除率
AA = sqrt(SA × DA)                 几何平均 —— 注意：不是 F1 的调和平均
HA = 2·SA·DA / (SA + DA)           调和平均
```

**AA 用几何平均是论文的刻意选择**（对较小值更敏感），和 F1 不是一回事。
更要紧的是：**动态点只占 0.55%，所以 AA 几乎完全由 SA 决定**——
这一点在 01-05 的复现里已经被数字证实（两个完全不同的 `d_p` 配置，SA/DA 各差约 2 pp，AA 却只差 0.09）。

⚠️ **三套口径互不可比**，引用时必须写明：

| 口径 | 出处 | voxel | 谁在用 |
| :--- | :--- | :--- | :--- |
| **SA / DA / AA**（点级） | 本基准 | 无（point-wise） | 01-01 · 01-05 |
| **PR / RR / F1**（voxel-wise） | 原始 ERASOR 表 II | 0.2 | 01-03 自报值 |
| **HA**（调和平均） | BeautyMap 论文 | 无 | 01-06 自报值 |

### 四、产物与用法

```bash
# 评测任意一个方法输出的清理地图（官方 + 独立实现 + 交叉检查）
python3 work/evaluate.py --seq-dir data/raw/00 --map <cleaned.pcd> \
                         --method <name> --impl both --out results/<name>_score.json
```

脚本 [`work/evaluate.py`](work/evaluate.py)；上游代码在 `code/DynamicMap_Benchmark/`（gitignore）；
数据在 `data/raw/00/`（gitignore，385 MB）。**四个方法共用一个数据目录，地图产物落在各自的方法文件夹里。**

## 记录 Log

| 日期 | 做了什么 | 结果 / 数字 | 结论 |
| :--- | :--- | :--- | :--- |
| 10-05 | 从 Zenodo 取回 teaser 数据 | 385 MB，141 帧 + 17.4M 点 GT | **KITTI 注册阻塞被绕开** |
| 10-05 | 克隆仓库 + 初始化 4 个方法子模块 | dufomap / ERASOR / removert / BeautyMap | 四个方法代码就位 |
| 10-05 | 编译 `scripts/` 的三个 C++ 工具 | 全部成功（PCL 1.14 / g++ 13） | 用官方评测器 |
| 10-05 | 写 `work/evaluate.py`，双实现交叉验证 | **分歧 0 / 17,362,230 点** | 评测口径可信 |
| 10-05 | 核对指标定义 | 仓库算 SA/DA/AA/HA，**不是** PR/RR/F1 | 修正本 README 原计划 |

## 下一步 Next

1. **跑 01-03 / 01-04 / 01-06**：ERASOR、Removert、BeautyMap 三个方法子模块已就位，数据与评测器都已验证，
   直接按各自 README 构建并输出清理地图 → 得到**同一口径下的四组 SA/DA/AA**。
2. **补 KITTI 05**（Zenodo `05.zip`，864 MB）作为第二个序列，检验参数泛化。
3. **接回任务书 §6 的 H1′**：四组数字到位后，先回答"四个方法的 SA 排名与它们在下游定位里的失败率排名是否一致"。
   → 注意：**这一步现在就已经有一条线索**——ERASOR 自报 PR 93.98（voxel-wise）却在基准里 SA 只有 66.70，
   而 Removert 自报 85.50 在基准里是 99.44。**排名本身就已经翻转了**，见 [PAPER_BASELINES.md §3.1](../PAPER_BASELINES.md)。
4. **回答复现目标第 4 条**：GT 覆盖范围之外怎么办（自采数据必然遇到）。
