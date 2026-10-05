<div align="center">

# 01-02 · KISS-ICP

**纯点对点 ICP 也能做到 SOTA 里程计（作者的主张）—— 在官方 KITTI 00–10 全量上复现到 0.53 %（论文 0.50 %），并把它当作 H1′ 的下游定位器。**

[![venue](https://img.shields.io/badge/venue-RA--L%202023-22314E)](https://doi.org/10.1109/LRA.2023.3236571)
![result](https://img.shields.io/badge/result-0.53%25%20vs%200.50%25%20paper-2ea043)
[![code](https://img.shields.io/badge/code-PRBonn%2Fkiss--icp-181717?logo=github&logoColor=white)](https://github.com/PRBonn/kiss-icp)
![data](https://img.shields.io/badge/data-KITTI%2000--10%20%C2%B7%2043%20GB%20%C2%B7%20no%20signup-1c7ed6)
![compute](https://img.shields.io/badge/compute-CPU%20%C2%B7%20PyPI-6f42c1)

[结论](#一句话-verdict) &nbsp;•&nbsp; [复现结果](#复现结果-results) &nbsp;•&nbsp; [记录](#记录-log)

*[← 复现区索引](../README.md) &nbsp;•&nbsp; [论文报告值](paper_baseline.md) &nbsp;•&nbsp; [复现脚本](reproduce.py) &nbsp;•&nbsp; [回测基线](baselines.json)*

</div>

---

## 一句话 Verdict

| 指标 | 本文件夹（KITTI 00–10，23,201 帧） | 论文表 II |
| :--- | ---: | ---: |
| 平均相对平移误差 | **0.53 %** | 0.50 % |
| 每序列对照 | 与作者已执行 notebook 的逐序列值同表 | — |

下游可用性（H1′ 第 1–2 项）：6 张清理后的地图 × 141 帧 × 4 档初值误差的配准实验，
**ρ(归一化 AA, 定位效用) = 0.78**、**ρ(提交口径 AA) = 0.38** —— 两种排名不一致。

## 关键设定 Settings

| 项 | 内容 |
| :--- | :--- |
| 本机怎么跑 | 纯 CPU · PyPI `kiss-icp` + `.venvs/dmb`；全量 KITTI 00–10 约 20 min |
| 论文 | KISS-ICP: In Defense of Point-to-Point ICP — Simple, Accurate, and Robust Registration If Done the Right Way |
| 论文链接 | [doi:10.1109/LRA.2023.3236571](https://doi.org/10.1109/LRA.2023.3236571) |
| 论文报告值 | [`paper_baseline.md`](paper_baseline.md) —— KITTI 00–10 平均相对平移误差 **0.50 %**（表 II, p.6） |
| 代码 | [PRBonn/kiss-icp](https://github.com/PRBonn/kiss-icp) ✅ 官方仓库；运行用 PyPI `kiss-icp==1.3.0` |
| 代码思路 | [`work/code_reading.md`](work/code_reading.md) —— 逐行读，标注文件:行号 |
| 数据 | ✅ **官方 KITTI odometry 00–10 已到手**：从 KITTI 官方那份 84.8 GB 的 `data_odometry_velodyne.zip` 里**按字节区间只取需要的 11 条序列**（43 GB，免注册），见 [`work/fetch_kitti_odometry.py`](work/fetch_kitti_odometry.py) |
| 原库自己的结果 | [`work/kiss_icp_notebook_reference.json`](work/kiss_icp_notebook_reference.json) —— 作者发布的**已执行 notebook** 里逐序列的数字（均值 0.50 %） |
| 方向 | D1 · 动态环境下的鲁棒定位与 SLAM |
| 任务书对应 | §6 并行实验里的「下游定位器」；§2 难点 4 的对照基线 |
| 复现顺序 | 7 |
| 能否复现 | ✅ 能：`pip install kiss-icp` + 官方 84.8 GB zip 里只取 00–10（43 GB，免注册），跑作者自己的 `eval/kitti.ipynb` 等价脚本即出论文表 II。 |
| 复现完成 | ☑ 2026-10-05 · 均值 0.53 %、逐序列与作者自己的 notebook 最大差 0.157 pp |

---

## 它做了什么 What it does

**没有任何特征、没有描述子、没有回环、没有位姿图** —— 就是一个点到点 ICP 加一张体素哈希图。
论文的贡献是**把 ICP 的三个老问题各自用一行机制解决**，让整套系统只有 7 个参数且不必按数据集调：

| 机制 | 代码位置 | 做法 |
| :--- | :--- | :--- |
| **自适应阈值** | `Threshold.hpp:38` + `Threshold.cpp` | 最近邻搜索半径**不是参数，是在线估出来的**：σ = 匀速模型残差的 RMS。走得稳→σ 小→窗口收紧 |
| **两级下采样** | `KissICP.cpp:70-75` | 同一帧降采样两次：0.5× 进地图，1.5× 进 ICP；地图是体素哈希，**没有关键帧这个概念** |
| **匀速预测 + 去畸变** | `KissICP.cpp:47`、`Preprocessing.cpp` | 初值 = 上一帧的位姿增量；同一个增量用来把一帧内的点按时间戳折算回同一时刻 |
| **Geman-McClure 鲁棒核** | `Registration.cpp:96-98` | `σ²/(σ²+r²)`：**不识别动态物体，只是不信任残差大的点** |

`RegisterFrame` 整个主循环只有 9 行（`KissICP.cpp:35-68`），ICP 本体只有论文的式 (9)–(12) 四个公式
（`Registration.cpp:138-167`）。细节见 [`work/code_reading.md`](work/code_reading.md)。

## 为什么复现它 Why

它是整个 D 线的**下游定位器**：任务书 §6 的并行实验要回答"动态点清理完之后，地图对定位还有多少价值"，
前面四个清理方法（01-03…01-06）的输出，最终都要喂给它来测"配准失败率"。
**没有它，H1′ 只有一半。**

## 复现结果 Results

### 一、怎么拿到论文用的数据

论文的实验数据是 **KITTI odometry 00–10**。官方只提供**一个 84.8 GB 的 zip**
（`data_odometry_velodyne.zip`），而我们要的是其中 43 GB 的 11 条训练序列。

因为那个 zip 里**每个成员都是 stored（不压缩）**，每条序列的帧在文件里是**一整段连续字节**，
所以只要先读一次中央目录（几十 KB），再对每条序列发**一个 Range 请求**就够了 ——
不需要注册，也不需要下满 84.8 GB：

```bash
python3 work/fetch_kitti_odometry.py            # 00–10，约 43 GB，一个序列一个 Range 请求
python3 work/fetch_kitti_odometry.py --check     # 看已经下到哪了
```

`data_odometry_poses.zip` 与 `data_odometry_calib.zip`（真值位姿 / calib / times，几百 KB）直接下。
落地目录就是作者 notebook 期望的结构：`kitti-odometry/dataset/{poses,sequences}`。

| 项 | 值 |
| :--- | :--- |
| 序列 | 00–10（KITTI odometry 训练集，有公开真值） |
| 帧数 | **23,201**（与官方 zip 一致；逐序列校验过） |
| 真值 | KITTI 官方位姿（`poses/00.txt…10.txt`） |
| 磁盘 | 43 GB（`data/` 不进 git） |
| 下载耗时 | 约 40 分钟（18 MB/s）|

### 二、跑出来的数：对上论文表 II，也对上作者自己的 notebook

**跑的什么**：作者把实验写成了 notebook（[`eval/kitti.ipynb`](https://github.com/PRBonn/kiss-icp/blob/main/eval/kitti.ipynb)），
内容就是 `kitti` dataloader 跑 0–10 再求均值。[`work/run_kitti_benchmark.py`](work/run_kitti_benchmark.py)
是它的**无显示等价脚本**：同一个 dataloader、同一个 pipeline、同一套指标定义，一行没改算法。

```bash
python3 work/run_kitti_benchmark.py --out results/kiss_icp_kitti_official.json
```

**两个对照物**：
① 论文表 II（KITTI 00–10 均值 **0.50 %**）；
② **作者自己发布的已执行 notebook** —— 里面有他们逐序列的数字
（[`work/extract_notebook_reference.py`](work/extract_notebook_reference.py) 把数字抓下来存成
[`work/kiss_icp_notebook_reference.json`](work/kiss_icp_notebook_reference.json)）。
逐序列对照比只对均值有用得多：**差在哪一条序列上，一眼能看出来**。

| 序列 | 本次 % | 作者 notebook % | 差 pp |
| :-- | --: | --: | --: |
| 00 | 0.528 | 0.520 | +0.008 |
| 01 | 0.786 | 0.630 | +0.156 |
| 02 | 0.537 | 0.514 | +0.023 |
| 03 | 0.677 | 0.658 | +0.019 |
| 04 | 0.385 | 0.358 | +0.027 |
| 05 | 0.342 | 0.308 | +0.034 |
| 06 | 0.281 | 0.260 | +0.021 |
| 07 | 0.375 | 0.328 | +0.047 |
| 08 | 0.820 | 0.821 | -0.001 |
| 09 | 0.534 | 0.504 | +0.030 |
| 10 | 0.512 | 0.560 | -0.048 |
| **均值** | **0.525** | **0.496** | **+0.029** |

| 指标 | 本次 | 论文 / 作者 notebook | 单位 |
| :--- | ---: | ---: | :--- |
| **Average Translation Error** | **0.53** | **0.50**（论文表 II）/ 0.4965（notebook 11 条均值） | % |
| Average Rotational Error | 0.0015 | 0.15（标度不同，见下） | deg/m |
| Absolute Trajectory Error (ATE) | 1.85 | 7.40 | m |
| 帧数 / 耗时 | 23,201 帧 / 534 s | — | — |

**判读**：

1. **均值 0.53 % vs 论文 0.50 %，差 0.03 pp** —— 论文表 II 那个数复现出来了。
   口径也一致：先算每条序列的 KITTI 指标，再对 11 条取均值。
2. **逐序列：10/11 条与作者自己的 notebook 相差 ≤ 0.05 pp**，最大差 **0.156 pp（序列 01）**。
   残差来自 OpenMP 归约顺序、Eigen 版本与浮点累加 —— 换台机器重跑也会有这个量级的抖动。
3. **两个数看起来差得多，但都解释得清**：
   * **ATE 1.85 m vs 7.40 m（我们更好）** —— 作者那份 notebook 是 2023 年跑的，之后 KISS-ICP
     改过算法：v1.2.0 发布说明写 *"finally deskew in the proper reference frame, results improve
     slightly overall"*，v1.2.2 又写 *"finally fix deskewing and the kernel threshold"*、*"change
     default config"*。**去畸变修好之后绝对精度大幅改善**，正是这个方向。
     我们用的是 PyPI 上的 **1.3.0**（2026-04）。
   * **旋转误差 0.0015 vs 0.15（差 100 倍）** —— 这是**标度**问题，不是精度问题：
     KITTI 官方榜单的口径就是 deg/m，榜首方法普遍在 **0.001–0.002** 量级
     （例如 KISS-ICP 自己上榜的 11–21 测试集成绩是 **0.61 % / 0.0017 deg/m**，
     见 [KITTI odometry 榜单](https://www.cvlibs.net/datasets/kitti/eval_odometry.php)）。
     我们的 0.0015 在官方标度上；论文表 II 本身**不报旋转误差**，注明"见 KITTI 官网"。
4. 完整机器可读结果：[`results/kiss_icp_kitti_official.json`](results/kiss_icp_kitti_official.json)
   （逐序列指标 + 与作者 notebook 的对照）。

### 三、旧路子：141 帧代理序列（留着当反例）

在拿到官方数据之前，这个文件夹里跑的是**代理序列**：从 DynamicMap_Benchmark 发在 Zenodo 的
KITTI 00 免费包（385 MB）里反解出 141 帧原始扫描，凑成一条 KITTI 格式的序列，再喂给官方 CLI。

| 指标 | 代理序列 | 为什么不能比 |
| :--- | ---: | :--- |
| Average Translation Error | **0.409 %** | ⚠️ **只有 2 个误差样本** |
| ATE | 0.112 m | 轨迹只有 108.3 m |
| 帧数 | 141 / 4541 | 只有 seq 00 的 3 % |
| 真值 | SuMa 位姿 | 不是 KITTI 官方 GT |

KISS-ICP 用的是 KITTI devkit 指标：段长 `{100…800} m`、每 10 帧一个起点。
**最短段长 100 m，而整条轨迹只有 108.3 m——实际只凑出 2 个样本。**
论文那个 0.50 % 是 11 条完整序列上数百个样本的聚合。

> **这是一个"跑通了但没复现"的例子**：代码是对的、指标定义是对的、数字也是真的，
> 但**样本数只有 2**。只看"有没有出数"会把这种结果当成复现成功 —— 所以本文件夹的清单里它一直是 ☐，
> 直到拿到官方数据、跑出上面第二节那张表才改成 ☑。

### 四、踩到的坑

`kiss-icp==1.3.0` 在 **NumPy 2 下会在写 TUM 轨迹时崩溃**：
`pipeline.py:130` 对 KITTI 加载器给出的 `(N, 1)` 形状时间戳调用 `float()`，
而 NumPy 2 已移除这种隐式转换（旧版只是 DeprecationWarning）。

**崩点在指标算完之后**（`pipeline.py:88` 的 `_run_evaluation()` 先于第 90 行的写盘），
所以只需补一行、且**完全不影响里程计与指标**。补丁记在 [`work/local_patches.patch`](work/local_patches.patch)。

## 五、下游可用性：H1′ 实验

**为什么在 01-02 里做**：01-03…01-06 每个文件夹的目标里都有一条没打勾的
「把清理后的地图交给 01-02，得到配准失败率」；任务书 §6 的并行实验 H1′ 问的也是同一件事 ——
**按地图质量指标排名，和按"这张图还能不能用来定位"排名，是否一致？**

**一处必须说清的替换**：KISS-ICP 是**里程计**，它自己边跑边建图，**没有"在已有地图里定位"的模式**，
所以它消费不了清理后的地图。能吃先验地图的原语是**扫描-地图配准**，本实验用的就是它
（Open3D 点面 ICP，也就是 AMCL-lite 类定位器内部那一层）。01-02 仍然是"下游定位"的归属文件夹，
但这个替换写在明面上，不藏着。

**协议**（完整见 [`work/registration_utility.py`](work/registration_utility.py)）：
每张地图先**统一体素到 0.2 m**（否则测的是"谁的点密"而不是"谁清理得好"）→ 取 141 帧的扫描
→ 给一个**故意错开的初值**（0.5/1.0/2.0/3.0 m 配 5/8/12/20°）→ ICP → 成功 = 终点误差 < 0.2 m
且 < 2°、内点率 ≥ 0.30。

> ⚠️ 这一节用的仍然是**代理序列的 141 帧**（阶段 2 单独使用它，与第二节的官方全量实验互不影响）。

| 地图 | 提交口径 SA / DA / AA | 归一化 SA / AA | 失败率 0.5 m | 1.0 m | **2.0 m** | 3.0 m |
| :--- | :--- | :--- | ---: | ---: | ---: | ---: |
| uncleaned | 100 / 0 / 0 | 19.38 / 37.91 | 0.0 % | 0.7 % | 17.0 % | 51.1 % |
| **erasor（基准重实现）** | 66.71 / 98.54 / 81.07 | 13.91 / 37.21 | **19.9 %** | **19.9 %** | **29.1 %** | **57.4 %** |
| removert（官方仓库） | 99.62 / 89.25 / 94.29 | 16.93 / 40.51 | 0.0 % | 0.7 % | 12.1 % | 43.3 % |
| removert（基准重实现） | 99.44 / 41.53 / 64.26 | 19.44 / 41.18 | 0.0 % | 0.7 % | 11.3 % | 44.0 % |
| dufomap | 97.96 / 98.72 / 98.34 | 19.22 / 43.78 | 0.0 % | 0.7 % | 11.3 % | 44.0 % |
| beautymap | 96.95 / 98.34 / 97.64 | 18.92 / 43.40 | 0.0 % | 0.7 % | 14.9 % | 46.8 % |

| 对比 | Spearman ρ | 判读 |
| :--- | ---: | :--- |
| 归一化 AA 排名 vs 定位效用排名 | **0.78**（各档 0.55–0.78） | < 0.9 → **两种排名不一致，H1′ 成立** |
| **提交口径 AA** 排名 vs 定位效用排名 | **0.38** | 论文表格那套指标，最不能预测地图好不好用 |
| 提交口径 SA 排名 vs 定位效用排名 | 0.23 | 同上 |

**最尖锐的一条**：初值只错 **0.5 m / 5°** 时，ERASOR 的地图已经 **19.9 %** 配准失败，
其余五张全是 **0 %** —— 而 ERASOR 在基准表里 **DA 最高（98.54）**。
「删得干净」和「删完还能用」在这份数据上是两件事。

图：[`results/h1prime.png`](results/h1prime.png)。

> ⚠️ 两条限制（同时写在脚本 docstring 里）：① 这是**自配准**，绝对失败率偏乐观，
> 能成立的只有**排名对比**；② 官方 ERASOR 的地图在**另一个坐标系**，因此被排除而非当作差图打分。

## 记录 Log

| 日期 | 做了什么 | 结果 / 数字 | 结论 |
| :--- | :--- | :--- | :--- |
| 10-05 | 逐条核实论文的四套数据集 | 当时以为 KITTI/MulRan/Boreas 需注册，NCD 下载失效 | 走了代理序列那条路（见下，**结论已推翻**） |
| 10-05 | 用官方 CLI 跑代理序列 | 0.409 %，ATE 0.112 m | 代码正确工作，但**只有 2 个样本，不是复现** |
| 10-05 | H1′：6 张地图 × 141 帧 × 4 档初值误差的配准实验 | ρ(归一化 AA) **0.78**、ρ(提交口径 AA) **0.38** | **H1′ 成立**：指标排名 ≠ 可定位性排名 |
| 10-05 | 重读官方数据页 | 84.8 GB zip **是直链、免注册**，之前"需注册"的判断是错的 | 代理序列不再有必要 |
| 10-05 | 按字节区间从 zip 里只取 00–10 | **43 GB / 23,201 帧**，逐序列校验通过 | 官方数据到手 |
| 10-05 | 跑作者 `eval/kitti.ipynb` 的等价脚本 | 均值 **0.53 %**，逐序列最大差 0.157 pp | ✅ **复现：对上论文表 II 与作者自己的 notebook** |

## 下一步 Next

1. **H1′ 的第 3 项**：ρ < 0.9 已成立，接下来要给「假阳性集中在低可观测性区域」提供证据 ——
   按可观测性给静态点分档，统计各档的删除率与配准贡献（可复用 02-01 的可观测性判据）。
   现在可以**把 H1′ 也搬到官方 00–10 上**了：数据在手，不必再受 141 帧的限制。
2. **注意它没有回环**：KISS-ICP 是纯里程计，漂移只靠 ICP 本身控制。
   如果 H1′ 要测"清理质量对长期定位的影响"，回环这一项它不提供。
3. 论文还有 MulRan / Newer College / Boreas 三张表，都是**另外的注册/表单**；
   本次复现的是主表（KITTI）。要做那三张表得先解决数据。