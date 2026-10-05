<div align="center">

# 01-10 · GenZ-ICP

**GenZ-ICP: Generalizable and Degeneracy-Robust LiDAR Odometry**

按残差稀疏 / 稠密自适应加权的退化鲁棒 LiDAR 里程计。

[![venue](https://img.shields.io/badge/venue-RA--L%202025-22314E)](https://arxiv.org/abs/2411.06766)
![result](https://img.shields.io/badge/result-0.52%25%20vs%200.51%25%20paper-2ea043)
[![code](https://img.shields.io/badge/code-cocel--postech%2Fgenz--icp-181717?logo=github&logoColor=white)](https://github.com/cocel-postech/genz-icp)
![data](https://img.shields.io/badge/data-KITTI%2000--10%20%28reused%29-1c7ed6)
![compute](https://img.shields.io/badge/compute-CPU%20%C2%B7%20PyPI-6f42c1)

[Quick start](#quick-start) &nbsp;•&nbsp; [Results](#results) &nbsp;•&nbsp; [Notes](#notes)

*[← 复现区索引](../README.md) &nbsp;•&nbsp; [复现脚本](reproduce.py) &nbsp;•&nbsp; [回测基线](baselines.json)*

</div>

在 KISS-ICP 那套「点到点 ICP + 体素哈希图」的骨架上，把**几何误差度量**换成**自适应加权**：
不是只用点到点距离，而是同时看**点到面/平面性**（`planarity_threshold`），
按局部结构决定每个点更该相信哪个度量 —— 因此在**退化环境**（长廊、隧道、开阔地）里不会
像纯点到点 ICP 那样在无约束方向上漂。

代码位置：`genz_icp/genz_icp.py` 的 `register_frame`；配置项
`mapping.planarity_threshold` / `mapping.desired_num_voxelized_points` / `mapping.voxel_size`。

|  |  |
| :--- | :--- |
| **方法** | 同一份 KITTI 00–10，23,201 帧 · 论文 论文 |
| **GenZ-ICP** | **0.52 %** · 论文 0.51 %（表 III） |
| **KISS-ICP（同表对照）** | 0.53 % · 论文 0.50 % |
| **Platform** | CPU · 20 核 · Ubuntu 24.04 + ROS 2 Jazzy |
| **Reproduce** | [`reproduce.py`](reproduce.py) · [`baselines.json`](baselines.json) |

两条方法在同一份数据、同一套指标下并排，也正是论文表 III 的排法。

---

## Quick start

| 依赖 | 版本 / 说明 |
| :--- | :--- |
| Python | PyPI `genz-icp`（自带预调好的 `kitti.yaml`） |
| 数据 | 复用 01-02 已下好的官方 KITTI 00–10（软链接，不重复下载） |
| 对照 | 论文表 III 把 GenZ-ICP 与 KISS-ICP 并排，本复现保持同样的排法 |

```bash
python3 reproductions/01_robust_localization_slam_dynamic/10_genz_icp/work/run_genz.py
python3 reproductions/run_all.py --only 01-10
```

## Results

```bash
../../.venvs/genz/bin/python work/run_kitti_benchmark.py --out results/genz_icp_kitti.json
```

| 指标 | GenZ-ICP（本次） | KISS-ICP（01-02，同数据） | 论文表 III |
| :--- | ---: | ---: | ---: |
| **Average Translation Error** | **0.52 %** | 0.53 % | GenZ **0.51** / KISS 0.50 |
| Average Rotational Error | 0.0012 deg/m | 0.0015 deg/m | — |
| ATE | 4.94 m | 1.85 m | — |
| 帧数 / 总耗时 | 23,201 帧 / 1001 s | 23,201 帧 / 534 s | — |

逐序列（相对平移误差 %，同一份 KITTI 00–10）：

| 序列 | GenZ-ICP | KISS-ICP | 差 pp |
| :-- | --: | --: | --: |
| 00 | 0.509 | 0.528 | -0.019 |
| 01 | 0.917 | 0.786 | +0.131 |
| 02 | 0.507 | 0.537 | -0.029 |
| 03 | 0.721 | 0.677 | +0.043 |
| 04 | 0.396 | 0.385 | +0.011 |
| 05 | 0.277 | 0.342 | -0.065 |
| 06 | 0.281 | 0.281 | +0.000 |
| 07 | 0.317 | 0.375 | -0.058 |
| 08 | 0.830 | 0.820 | +0.010 |
| 09 | 0.500 | 0.534 | -0.034 |
| 10 | 0.458 | 0.512 | -0.053 |
| **均值** | **0.519** | **0.525** | **-0.006** |

**怎么读**：

1. **0.52 % vs 论文 0.51 %，差 0.01 pp** —— 论文表 III 那个数复现出来了。
2. **与 KISS-ICP 是同一份数据上的对照**：论文写两者只差 0.01 pp（0.50 vs 0.51），
   本机测出来是 **0.52 vs 0.53（差 0.01 pp，方向相反）** ——
   两边都在「打平」的量级里，**说「并列」是诚实的读法**。
3. **ATE 差别大（4.94 m vs 1.85 m）不是矛盾**：论文表 III 只报相对平移误差，
   两种配准（平面性加权 vs 纯点到点）的绝对轨迹本来就会不同；这里只把它当**测量**记着。
4. 完整机器可读结果：[`results/genz_icp_kitti.json`](results/genz_icp_kitti.json)（逐序列 + KISS-ICP 并排）。

## Notes

1. **必须用 `kitti.yaml` 预调参数**。用通用默认参数跑，KITTI 04 会得到
   **5.23 % / ATE 10.10 m**；换成包里自带的 `kitti.yaml`（`deskew: false`、`voxel_size: 0.6`、
   `planarity_threshold: 0.18` …）才是 **0.39 % / ATE 0.86 m**。
   差的不是小数 —— **参数集就是论文的一部分**，README 里写了要用预调 config。
2. **`save_poses_tum_format` 在 NumPy 2 下崩溃**：`pipeline.py:134` 对 KITTI 加载器给出的
   `(1,)` 形状时间戳调用 `float()`（与 kiss-icp 1.3.0 同一个 bug、同一个位置）。
   崩点在**指标算完之后**（`run()` 里 `_run_evaluation()` 先于 `_write_result_poses()`），
   所以指标可信；脚本里用一个等价替换绕开写盘那一步。

```bash
../../.venvs/genz/bin/python work/run_kitti_benchmark.py \
    --out results/genz_icp_kitti.json
```

结果同时会把 01-02 测到的 KISS-ICP 数字并排打出来（论文表 III 就是这么排的）。

## Documentation

- 论文自报数字与出处：[`paper_baseline.md`](paper_baseline.md)
- 复现脚本：[`reproduce.py`](reproduce.py) · 回测基线：[`baselines.json`](baselines.json)
- 本文件夹的脚本、协议与实测记录：[`work/`](work/)
- 复现区索引与约定：[`../README.md`](../README.md) · 状态账本：[`../../status.json`](../../status.json)

<!-- run_all.py 读下面这几行生成索引表，改动请保持同样的 | 键 | 值 | 形式 -->

| 元数据 | 内容 |
| :--- | :--- |
| 论文 | GenZ-ICP: Generalizable and Degeneracy-Robust LiDAR Odometry Using an Adaptive Weighting |
| 论文链接 | [arXiv:2411.06766](https://arxiv.org/abs/2411.06766) |
| 代码 | [cocel-postech/genz-icp](https://github.com/cocel-postech/genz-icp) ✅ PyPI 包 `genz-icp`（自带预调好的 `kitti.yaml`） |
| 方向 | D1 · 动态环境下的鲁棒定位与 SLAM |
| 任务书对应 | §2 难点 3 退化场景下的鲁棒定位 |
| 能否复现 | ✅ 能：`pip install genz-icp pyyaml` + 已经在手的 KITTI 00–10，跑 `kitti.yaml` 预调参数即出论文表 III。 |
| 复现完成 | ☑ 2026-10-05 · 均值 0.52 %（论文 0.51 %，差 +0.01 pp） |
| 复现顺序 | 8 |
| 项 | 内容 |
| 本机怎么跑 | 纯 CPU · PyPI `genz-icp`，复用 01-02 已经下好的 KITTI 00–10 |
| 论文报告值 | 表 III, p.5：KITTI 00–10 相对平移误差 **0.51 %**（同一张表里 KISS-ICP 0.50 %） |
| 数据 | ✅ **已经在手**：01-02 下的官方 KITTI odometry 00–10（23,201 帧，43 GB，免注册），本文件夹用软链接复用 |
| 为什么在这 | 与 01-02 是**同一份数据、同一套指标**的对照组：论文表 III 把两者并排，可以直接比 |
