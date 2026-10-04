# 01-02 · KISS-ICP

| 项 Item | 内容 |
| :--- | :--- |
| 论文 | KISS-ICP: In Defense of Point-to-Point ICP — Simple, Accurate, and Robust Registration If Done the Right Way |
| Venue | **RA-L 2023** |
| 论文链接 | [doi:10.1109/LRA.2023.3236571](https://doi.org/10.1109/LRA.2023.3236571) |
| 论文报告值 | [`paper_baseline.md`](paper_baseline.md) —— KITTI 00–10 平均相对平移误差 **0.50 %** |
| 代码 | [PRBonn/kiss-icp](https://github.com/PRBonn/kiss-icp) ✅ 官方仓库 `1ffa7d7`；运行用 PyPI `kiss-icp==1.3.0` |
| 代码思路 | [`work/code_reading.md`](work/code_reading.md) —— 逐行读，标注文件:行号 |
| 数据 | ⚠️ 论文用 KITTI / MulRan / NCD / Boreas，**四套全部需要注册或表单**；本次用 Zenodo 免费包重建的 KITTI 00 子序列 |
| 方向 | D1 · 动态环境下的鲁棒定位与 SLAM |
| 任务书对应 | §6 并行实验里的「下游定位器」；§2 难点 4 的对照基线 |
| 复现状态 | 🟡 **代码跑通并出数**（0.409 %）；⚠️ **数字与论文不可直接比**，原因见下 |

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

## 复现结果 Results（2026-10-05）

### 一、数据：论文的四套数据集全部拿不到

| 数据集 | 论文里的角色 | 获取状态 |
| :--- | :--- | :--- |
| KITTI odometry | 主实验（00–10 = 0.50 %） | ❌ 需注册，约 80 GB |
| MulRan | KAIST 序列 2.28 % | ❌ 需注册 |
| Newer College (NCD) | 01-short 0.51 % | ❌ 官网下载页**没有直链**，只有表单；社区已记录其下载失效（[evalio#21](https://github.com/contagon/evalio/issues/21)） |
| Boreas | 表 IV | ❌ 需表单 |

**但有一条免费的绕道**：DynamicMap_Benchmark 发在 Zenodo 上的 KITTI 00 包（385 MB，免注册），
里面的 141 帧是**世界系**点云 + `VIEWPOINT` 里的传感器位姿。
这些点云当初正是用这些位姿把原始 Velodyne 扫描变换出来的，**所以逆变换能把原始扫描还原回来**：

```
p_sensor = R(q)ᵀ · (p_world − t)
```

[`work/make_kitti_seq.py`](work/make_kitti_seq.py) 做这件事，并写成 KITTI odometry 目录结构
（`sequences/00/velodyne/*.bin` + `calib.txt` + `poses/00.txt` + `times.txt`），
于是官方的 `--dataloader kitti` 路径**一行没改**就能跑。

| 项 | 值 |
| :--- | :--- |
| 帧数 | **141**（KITTI 00 的第 4390–4530 帧；完整 seq 00 有 4541 帧） |
| 轨迹长度 | **108.3 m** |
| 时长 | 约 14.1 s（10 Hz） |
| 真值来源 | ⚠️ **SuMa 估计位姿**（SemanticKITTI 的口径），不是 KITTI 官方位姿 |

### 二、跑出来的数

```bash
python3 work/make_kitti_seq.py --seq-dir <benchmark>/data/raw/00 --out data/raw/kitti00_sub
kiss_icp_pipeline --dataloader kitti --sequence 00 data/raw/kitti00_sub
```

| 指标 | 本次 | 单位 |
| :--- | ---: | :--- |
| **Average Translation Error** | **0.409** | % |
| Average Rotational Error | 0.005 | deg/m |
| Absolute Trajectory Error (ATE) | **0.112** | m |
| Absolute Rotational Error (ARE) | 0.006 | rad |
| 平均频率 | 50 | Hz |
| 平均单帧耗时 | 20 | ms |

完整输出存档在 [`results/kiss_icp_metrics.log`](results/kiss_icp_metrics.log)。

### 三、⚠️ 为什么这个 0.409 % 不能拿去和论文的 0.50 % 比

**能比的只有"同一个指标定义"，不能比"同一个数"。** 三条差距，逐条量过：

1. **样本数只有 2。** KISS-ICP 用的是 KITTI odometry 官方指标（`Metrics.cpp:35`）：
   段长 `{100, 200, …, 800} m`，起点每 10 帧一个，逐段算相对位姿误差再除以段长。
   **最短段长 100 m**，而我们整条轨迹只有 108.3 m —— 实际只凑出 **2 个样本**
   （起点 0 的 100 m 段、起点 10 的 100 m 段）。论文那个 0.50 % 是 11 条**完整**序列
   （每条数千米）上数百个样本的聚合。**2 个样本的均值不能叫复现。**
2. **序列不完整。** 141 / 4541 帧，只有 seq 00 的 3 %。
3. **真值不同源。** 我们用的是包里的 SuMa 位姿，论文用 KITTI 官方 GT。

→ **结论：这次复现验证的是"官方代码能在真实 KITTI 00 数据上正确工作"（ATE 0.112 m、50 Hz、免调参），
而不是"复现了 0.50 % 这个数"。要复现那个数，必须先注册 KITTI odometry。**

### 四、踩到的坑

`kiss-icp==1.3.0` 在 **NumPy 2 下会在写 TUM 轨迹时崩溃**：
`pipeline.py:130` 对 KITTI 加载器给出的 `(N, 1)` 形状时间戳调用 `float()`，
而 NumPy 2 已移除这种隐式转换（旧版只是 DeprecationWarning）。

**崩点在指标算完之后**（`pipeline.py:88` 的 `_run_evaluation()` 先于第 90 行的写盘），
所以只需补一行、且**完全不影响里程计与指标**。补丁记在 [`work/local_patches.patch`](work/local_patches.patch)。

## 记录 Log

| 日期 | 做了什么 | 结果 / 数字 | 结论 |
| :--- | :--- | :--- | :--- |
| 10-05 | 逐条核实论文的四套数据集 | KITTI/MulRan/Boreas 需注册，NCD 下载失效 | **论文的数字无法直接复现** |
| 10-05 | 从 Zenodo 的 KITTI 00 包反解出传感器系原始扫描 | 141 帧 / 108.3 m | 免费绕道成立 |
| 10-05 | 读官方代码，逐行标注 | 见 [`work/code_reading.md`](work/code_reading.md) | 主循环只有 9 行 |
| 10-05 | 用官方 CLI 跑通 | **0.409 %，ATE 0.112 m，50 Hz，20 ms** | 代码正确工作 |
| 10-05 | 数了一下指标实际样本数 | **只有 2 个** | ⚠️ 这个数不能当复现结果 |
| 10-05 | 修 NumPy 2 崩溃（写 TUM 轨迹处） | 补一行 | 崩点在指标之后，不影响数字 |

## 下一步 Next

1. **要复现 0.50 %，只有一条路：注册 KITTI odometry**（<https://www.cvlibs.net/datasets/kitti/eval_odometry.php>）。
   拿到后本文件夹的脚本可直接复用，只需把 `--seq-dir` 换成完整序列。
2. **接回 H1′**：现在 01-03…01-06 的四张清理后地图已经在了，
   下一步是把它们喂给 KISS-ICP 测"配准失败率"。
   ⚠️ 但先要定两件事（见 [01-01 的 README](../01_dynamicmap_benchmark/README.md) 第五节）：
   清理后的地图是**累积地图**而 KISS-ICP 吃**连续扫描**；且 ERASOR 的输出被下采样了 10 倍。
3. **注意它没有回环**：KISS-ICP 是纯里程计，漂移只靠 ICP 本身控制。
   如果 H1′ 要测"清理质量对长期定位的影响"，回环这一项它不提供。
