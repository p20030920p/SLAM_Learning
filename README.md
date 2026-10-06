<div align="center">

# SLAM_Learning

**One paper per folder, reproduced with the authors' own public code, up to the authors' own numbers. What runs gets a number. What does not gets its missing piece written down in the open.**

[![rule](https://img.shields.io/badge/rule-%E6%9C%89%E5%BA%93%E6%89%8D%E5%A4%8D%E7%8E%B0-2ea043)](reproductions/README.md)
[![driver](https://img.shields.io/badge/driver-run__all.py-6f42c1)](reproductions/run_all.py)
[![layout](https://img.shields.io/badge/layout-one%20paper%20per%20folder-1c7ed6)](reproductions/)
[![License](https://img.shields.io/badge/license-MIT-3DA639)](LICENSE)

[Reproduction checklist](#复现清单-reproduction-checklist) &nbsp;•&nbsp; [How to run](#how-to-run) &nbsp;•&nbsp; [Layout](#layout) &nbsp;•&nbsp; [Reproductions](reproductions/)

*English &nbsp;|&nbsp; [中文](README.zh-CN.md)*

</div>

## What this is

A ledger of paper reproductions. Every entry starts from the authors' own repository, runs on this
machine, and is checked back against the numbers the paper or the upstream repository itself
reports. Entries that cannot run here are kept and labelled with the exact missing piece, because
"we could not run it, and here is what was missing" is a result worth recording.

One rule decides what gets in:

> **No upstream code, no reproduction.** A paper is never re-implemented from its prose.

|  |  |
| :--- | :--- |
| Entries | 21 folders across 2 research directions, one paper each |
| Rule | authors' own code only; no code means the entry stays blocked and says so |
| Driver | `python3 reproductions/run_all.py` discovers, runs, backtests and rewrites the checklist below |
| Backtest | each working entry records its metrics in `baselines.json`; a re-run is compared against them |
| Machine | CPU only, no CUDA. Every green entry runs here; GPU-bound ones are listed as blocked with the reason |

This is not a benchmark and not a leaderboard. There is no fixed protocol, and the numbers below are
the papers' own, reproduced on one machine — not a ranking.

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

## How to run

```bash
git clone https://github.com/p20030920p/SLAM_Learning.git
cd SLAM_Learning
python3 reproductions/run_all.py                 # discover, run, backtest, refresh the checklist
python3 reproductions/run_all.py --only 02-01    # one entry
python3 reproductions/run_all.py --check         # no re-run: re-render the checklist from status.json
python3 reproductions/run_all.py --no-backtest   # skip the comparison against baselines.json
```

Upstream checkouts and datasets are deliberately **not** in git — they are hundreds of megabytes per
entry. Each folder's `README.md` says how to fetch what it needs, and `reproduce.py` declares the
requirement before it runs, so a missing dataset is reported as *blocked*, never as a pass.

Some upstreams are still catkin-based. They are built inside this repository, without root:

```bash
bash reproductions/tools/ros1_env.sh            # micromamba ROS 1 Noetic, ROS 2 libs stripped
bash reproductions/tools/build_ros1_catkin.sh   # catkin build, with the vtk-header and DSO pitfalls handled
```

## Layout

| Path | What it holds |
| :--- | :--- |
| [`reproductions/`](reproductions/) | **the repository**: 21 folders, one paper each, plus the checklist above |
| [`reproductions/README.md`](reproductions/README.md) | the rule, the six-file folder contract, the driver's four passes |
| [`reproductions/PAPER_BASELINES.md`](reproductions/PAPER_BASELINES.md) | what each paper claims, so a run has an acceptance threshold at all |
| [`reproductions/NOTES.md`](reproductions/NOTES.md) | background analysis: the two directions, fit to the task, reported numbers, link checks |
| [`reproductions/CANDIDATES.md`](reproductions/CANDIDATES.md) | **what to reproduce next**: 87 candidate papers that all ship public code, every repository fetched live, ranked by how many of the four gates they clear |
| [`reproductions/OPEN_PROBLEMS.md`](reproductions/OPEN_PROBLEMS.md) | 14 open problems drawn from those 87, each with a minimal experiment and a stated falsifier |
| [`reproductions/status.json`](reproductions/status.json) | machine-readable ledger, written by the driver |
| [`docs/task-book/TASK_BOOK.md`](docs/task-book/TASK_BOOK.md) | the task book the two directions come from |
| [`docs/car.md`](docs/car.md) | the eight difficulties, each with a falsifiable hypothesis |
| [`docs/platform.md`](docs/platform.md) | **archived**: the ROS 2 / Gazebo simulator that used to ship here |

The ROS 2 simulator this repository was originally built around (the `race_*` and `algo_*`
packages) has been removed; the repository is now the reproduction ledger plus its background
documents. `docs/platform.md` keeps that platform's arena geometry, sensor rig and sim-to-hardware
notes, marked as archived. To run the simulator again, take `src/` from
[Sim2Real-AlgoBench](https://github.com/p20030920p/Sim2Real-AlgoBench) or restore it from this
repository's git history.

## Status vocabulary

| Status | Meaning |
| :--- | :--- |
| 完成 · done | ran here and landed on the number the upstream reports |
| 半完成 · half | the upstream repository only ships part of the method; that part was reproduced |
| 阻塞 · blocked | cannot run on this machine, with the measured missing piece named (RAM, CUDA, no code) |
| 计划 · planned | folder and plan exist, `reproduce.py` does not yet |

## Licence

MIT, see [LICENSE](LICENSE). Derived from
[Sim2Real-AlgoBench](https://github.com/p20030920p/Sim2Real-AlgoBench) by p20030920p and zfyyyyy.
