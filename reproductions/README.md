<div align="center">

# 复现区 Reproductions

**一篇论文一个文件夹：用作者自己的代码，跑到作者自己的数字。跑得通的给出数字，跑不通的把缺什么写在明面上。**

![rule](https://img.shields.io/badge/rule-%E6%9C%89%E5%BA%93%E6%89%8D%E5%A4%8D%E7%8E%B0-2ea043)
![driver](https://img.shields.io/badge/driver-run__all.py-6f42c1)
![backtest](https://img.shields.io/badge/backtest-baselines.json-1c7ed6)

[复现清单](#复现清单-reproduction-checklist) &nbsp;•&nbsp; [自动化](#自动化) &nbsp;•&nbsp; [约定](#约定) &nbsp;•&nbsp; [候选论文目录](CANDIDATES.md) &nbsp;•&nbsp; [开放问题](OPEN_PROBLEMS.md) &nbsp;•&nbsp; [背景分析](NOTES.md)

*[仓库主页](../README.md) &nbsp;•&nbsp; [D1](01_robust_localization_slam_dynamic/README.md) &nbsp;•&nbsp; [D2](02_semantic_mapping_visual_anchoring_navigation/README.md)*

</div>

|  |  |
| :--- | :--- |
| 编号 | 方向（D1/D2）加两位序号，一篇论文一个文件夹 |
| 驱动 | `python3 reproductions/run_all.py` 发现、运行、回测、刷新下面的清单 |
| 回测 | 每个跑通项在 `baselines.json` 里记了指标，重跑时自动比对 |
| 规则 | 有上游代码才复现，没有库就不自己照着论文写一份 |

每个文件夹里有六样东西：

| 文件 | 是什么 |
| :--- | :--- |
| `README.md` | 这一篇的页面：快速开始、结果、说明（人读的） |
| `baselines.json` | 论文数字、元数据与回测基线（机器读的） |
| `paper_baseline.md` | 论文自报数字与出处，表号页码写清楚 |
| `reproduce.py` | `require(ctx)` 说清缺什么，`run(ctx)` 产出指标 |
| `work/` | 我们写的脚本、协议与实测记录 |
| `code/` · `data/` | 上游仓库与数据集，不进 git |

<!-- PROGRESS:START -->

## 复现清单 Reproduction checklist

**按「越好复现 + 越能对上原库结果」排序** —— 完成 12 · 半完成 2 · 阻塞 7（共 21） · 更新于 2026-10-06 22:50 CST

| # | 状态 | 复现库 | 论文 | 一句话 |
| :-- | :-- | :-- | :-- | :-- |
| 01-05 | 完成 | [KTH-RPL/dufomap](https://github.com/KTH-RPL/dufomap) | [doi:10.1109/LRA.2024.3387658](https://doi.org/10.1109/LRA.2024.3387658) | 能。与论文表 I 两位小数一致。 |
| 01-06 | 完成 | [MKJia/BeautyMap](https://github.com/MKJia/BeautyMap) | [arXiv:2405.07283](https://arxiv.org/abs/2405.07283) | 能。命中论文表 I。 |
| 01-01 | 完成 | [KTH-RPL/DynamicMap_Benchmark](https://github.com/KTH-RPL/DynamicMap_Benchmark) | [arXiv:2307.07260](https://arxiv.org/abs/2307.07260) | 能。官方评测器加 Zenodo 免注册数据，四个方法同表。 |
| 01-03 | 完成 | [LimHyungTae/ERASOR](https://github.com/LimHyungTae/ERASOR) | [arXiv:2103.04316](https://arxiv.org/abs/2103.04316) | 能，需 ROS 1。官方仓库对上论文表 II。 |
| 01-04 | 完成 | [irapkaist/removert](https://github.com/irapkaist/removert) | [doi:10.1109/IROS45743.2020.9340856](https://doi.org/10.1109/IROS45743.2020.9340856) | 能，需 ROS 1。官方实现 SA/DA/AA 99.62/89.25/94.29。 |
| 01-08 | 完成 | [yuhaozhang7/NGD-SLAM](https://github.com/yuhaozhang7/NGD-SLAM) | [arXiv:2405.07392](https://arxiv.org/abs/2405.07392) | 能。纯 CPU，ATE 0.0157 m。 |
| 01-02 | 完成 | [PRBonn/kiss-icp](https://github.com/PRBonn/kiss-icp) | [doi:10.1109/LRA.2023.3236571](https://doi.org/10.1109/LRA.2023.3236571) | 能。PyPI 包加官方 KITTI 00–10，均值 0.53 %。 |
| 01-10 | 完成 | [cocel-postech/genz-icp](https://github.com/cocel-postech/genz-icp) | [arXiv:2411.06766](https://arxiv.org/abs/2411.06766) | 能。均值 0.52 %，论文 0.51 %。 |
| 01-09 | 半完成 | [gisbi-kim/lt-mapper](https://github.com/gisbi-kim/lt-mapper) | [arXiv:2107.07712](https://arxiv.org/abs/2107.07712) | 半能。仓库只有变化检测半边。 |
| 01-11 | 完成 | [dongjae0107/ELite](https://github.com/dongjae0107/ELite) | [arXiv:2502.13452](https://arxiv.org/abs/2502.13452) | 能。AC 0.9708，论文 0.969，纯 CPU。 |
| 01-12 | 完成 | [UZ-SLAMLab/ORB_SLAM3](https://github.com/UZ-SLAMLab/ORB_SLAM3) | [arXiv:2007.11898](https://arxiv.org/abs/2007.11898) | 能。纯 CPU，RMSE ATE 0.035 至 0.045 m。 |
| 01-13 | 阻塞 | [MIT-SPARK/Khronos](https://github.com/MIT-SPARK/Khronos) | [arXiv:2402.13817](https://arxiv.org/abs/2402.13817) | 不能。实测需要 13.5 GB 以上内存。 |
| 02-01 | 半完成 | [WaldJohannaU/3RScan](https://github.com/WaldJohannaU/3RScan) | [arXiv:1908.06109](https://arxiv.org/abs/1908.06109) | 半能。只有数据集与工具，全量数据需申请。 |
| 02-06 | 阻塞 | [MIT-SPARK/Clio](https://github.com/MIT-SPARK/Clio) | [arXiv:2404.13696](https://arxiv.org/abs/2404.13696) | 不能。论文用 RTX 3090。 |
| 02-07 | 完成 | [AnyLoc/AnyLoc](https://github.com/AnyLoc/AnyLoc) | [arXiv:2308.00688](https://arxiv.org/abs/2308.00688) | 能。纯 CPU 约 3.3 h，R@1 65.0 与论文一致。 |
| 02-08 | 完成 | [AnyLoc/Revisit-Anything](https://github.com/AnyLoc/Revisit-Anything) | [arXiv:2409.18049](https://arxiv.org/abs/2409.18049) | 能。纯 CPU 约 25 min，R@1 95.32 与论文一致。 |
| 02-03 | 阻塞 | [concept-graphs/concept-graphs](https://github.com/concept-graphs/concept-graphs) | [arXiv:2309.16650](https://arxiv.org/abs/2309.16650) | 不能。需 16 至 24 GB 显存与 GPT-4 key。 |
| 02-04 | 阻塞 | [Eku127/DualMap](https://github.com/Eku127/DualMap) | [arXiv:2506.01950](https://arxiv.org/abs/2506.01950) | 不能。论文用 RTX 4090。 |
| 02-05 | 阻塞 | [hovsg/HOV-SG](https://github.com/hovsg/HOV-SG) | [arXiv:2403.17846](https://arxiv.org/abs/2403.17846) | 不能。四篇底座里算力最重，论文未写门槛。 |
| 01-07 | 阻塞 | [ACFR-RPG/DynoSAM](https://github.com/ACFR-RPG/DynoSAM) | [arXiv:2501.11893](https://arxiv.org/abs/2501.11893) | 不能。configure 阶段就要求 CUDA。 |
| 02-02 | 阻塞 | — | [arXiv:2607.14899](https://arxiv.org/abs/2607.14899) | 不能。代码未发布。 |

> 状态：完成 = 已对上原库数字 · 半完成 = 只做了仓库里有的那一半 · 阻塞 = 本机做不了（缺硬件或没有代码）。
> 每一行的字段写在对应文件夹的 `baselines.json` 里，本表由 `python3 reproductions/run_all.py` 生成，块内不要手改。
<!-- PROGRESS:END -->

## 自动化

```bash
python3 reproductions/run_all.py                 # 跑所有能跑的复现，回测，刷新清单
python3 reproductions/run_all.py --only 02-01    # 只跑一篇
python3 reproductions/run_all.py --check         # 不重跑，按现有 status.json 重画清单
python3 reproductions/run_all.py --no-backtest   # 跳过与基线的比对
```

每次运行做四件事：发现文件夹，运行有 `reproduce.py` 的复现（缺数据就报阻塞而不是假装失败），
把本次指标与 `baselines.json` 比对（超出容差判为回归），刷新 `status.json` 与上面那张清单。

## 约定

`reproduce.py` 的返回值里，`checks` 与 `findings` 是两回事：

| 字段 | 含义 | 不成立会怎样 |
| :--- | :--- | :--- |
| `checks` | 不变量：协议声称的事实 | 判为失败，说明复现坏了 |
| `findings` | 测量结果：关于数据的客观事实 | 只记录，不阻塞 |

新增一篇复现：建 `reproductions/<方向>/<NN_名称>/`，写 `README.md` 与 `reproduce.py`，
把元数据与论文数字写进 `baselines.json` 的 `meta` 字段，然后跑一次 `run_all.py`。

## ROS 1 上游仓库

01-03 与 01-04 需要 ROS 1 Noetic。本机是 ROS 2 Jazzy 且没有 root，用 micromamba 建在
`reproductions/.venvs/ros1noetic`：

```bash
bash reproductions/tools/ros1_env.sh          # 剥掉 ROS 2 的库，避免符号冲突
bash reproductions/tools/build_ros1_catkin.sh # catkin 构建，含 vtk 头文件与 DSO 两个坑
```

## 选下一篇做什么

上面那张表只写了**已经做了什么**。要决定**下一篇做什么**，看这两页：

| 文件 | 内容 |
| :--- | :--- |
| [`CANDIDATES.md`](CANDIDATES.md) | 87 条候选论文，每条都有公开代码，每个仓库都实测可达。按「有库 → 纯 CPU → 不要 ROS 1 → 数据免注册」分三档，22 条四条全过 |
| [`OPEN_PROBLEMS.md`](OPEN_PROBLEMS.md) | 从这 87 条里抽出来的 14 个开放问题，每条都带「最小实验」与「什么结果会证伪它」 |

选型规则和本目录一致：**先看有没有库，再看能不能在这台机器上跑，最后才看它重不重要。**
`CANDIDATES.md` 里的「不建议复现」那一档也保留着，用来记住哪些论文是**因为没库或要 GPU** 才出局的。
