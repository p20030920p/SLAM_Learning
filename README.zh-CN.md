<div align="center">

# SLAM_Learning

**一篇论文一个文件夹：用作者自己的公开代码，跑到作者自己报的数字。跑得通的给出数字，跑不通的把缺什么写在明面上。**

[![rule](https://img.shields.io/badge/rule-%E6%9C%89%E5%BA%93%E6%89%8D%E5%A4%8D%E7%8E%B0-2ea043)](reproductions/README.md)
[![driver](https://img.shields.io/badge/driver-run__all.py-6f42c1)](reproductions/run_all.py)
[![layout](https://img.shields.io/badge/layout-one%20paper%20per%20folder-1c7ed6)](reproductions/)
[![License](https://img.shields.io/badge/license-MIT-3DA639)](LICENSE)

[复现清单](#复现清单-reproduction-checklist) &nbsp;•&nbsp; [怎么跑](#怎么跑) &nbsp;•&nbsp; [目录结构](#目录结构) &nbsp;•&nbsp; [复现区](reproductions/)

*[English](README.md) &nbsp;|&nbsp; 中文*

</div>

## 这是什么

一本复现账本。每一条都从**作者自己的仓库**出发，在这台机器上跑一遍，再回头跟论文或上游
自己报的数字对表。跑不起来的条目照样留在表里，并写清楚**到底缺哪一样**——
「跑不了，以及跑不了的原因」本身就是一条结果。

决定收录与否的只有一条规则：

> **没有上游代码就不复现。** 绝不照着论文正文自己重写一份。

|  |  |
| :--- | :--- |
| 条目 | 21 个文件夹，两个研究方向，一篇论文一个文件夹 |
| 规则 | 只用作者自己的代码；没有代码的条目保持阻塞，并把原因写出来 |
| 驱动 | `python3 reproductions/run_all.py` 负责发现、运行、回测、刷新下面的清单 |
| 回测 | 每个跑通项把指标记在 `baselines.json` 里，重跑时自动比对 |
| 本机 | 只有 CPU，没有 CUDA。所有「完成」条目都在本机跑过；GPU 受限的列为阻塞并写明原因 |

这里不是基准，也没有排行榜。没有固定协议，表里的数字是**论文自己的数字在这台机器上的复现**，
不是排名。

<!-- PROGRESS:START -->

## 复现清单 Reproduction checklist

**按「越好复现 + 越能对上原库结果」排序** —— 完成 12 · 半完成 2 · 阻塞 7（共 21） · 更新于 2026-10-06 20:55 CST

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

## 怎么跑

```bash
git clone https://github.com/p20030920p/SLAM_Learning.git
cd SLAM_Learning
python3 reproductions/run_all.py                 # 发现、运行、回测，并刷新上面的清单
python3 reproductions/run_all.py --only 02-01    # 只跑一篇
python3 reproductions/run_all.py --check         # 不重跑，只按 status.json 重画清单
python3 reproductions/run_all.py --no-backtest   # 跳过与 baselines.json 的比对
```

上游仓库与数据集**故意不进 git**——单个条目就是几百 MB。每个文件夹的 `README.md` 写明怎么取，
`reproduce.py` 在开跑前先声明需要什么，所以缺数据会被报成**阻塞**，永远不会被算成通过。

有几个上游仍是 catkin 体系，在本仓库内构建，不需要 root：

```bash
bash reproductions/tools/ros1_env.sh            # micromamba 建 ROS 1 Noetic，剥掉 ROS 2 的库
bash reproductions/tools/build_ros1_catkin.sh   # catkin 构建，已处理 vtk 头文件与 DSO 两个坑
```

## 目录结构

| 位置 | 内容 |
| :--- | :--- |
| [`reproductions/`](reproductions/) | **本仓库的主体**：21 个文件夹，一篇论文一个，外加上面的清单 |
| [`reproductions/README.md`](reproductions/README.md) | 规则、六件套文件夹约定、驱动的四件事 |
| [`reproductions/PAPER_BASELINES.md`](reproductions/PAPER_BASELINES.md) | 每篇论文自报的数字，让「复现」先有验收标准 |
| [`reproductions/NOTES.md`](reproductions/NOTES.md) | 背景分析：两个方向、与任务的契合度、论文报告值、链接核验 |
| [`reproductions/status.json`](reproductions/status.json) | 机器可读的账本，由驱动写出 |
| [`docs/task-book/TASK_BOOK.md`](docs/task-book/TASK_BOOK.md) | 两个研究方向所依据的任务书 |
| [`docs/car.md`](docs/car.md) | 八个难点，每个配一条可否证的假设 |
| [`docs/platform.md`](docs/platform.md) | **归档**：原先随本仓库发布的 ROS 2 / Gazebo 仿真平台 |

本仓库最初围绕的 ROS 2 仿真平台（`race_*` 与 `algo_*` 六个包）已移除，仓库现在就是复现账本
加上它的背景文档。`docs/platform.md` 保留了那个平台的赛场几何、传感器配置与仿真到实机的差距，
并标为归档。要重新跑起仿真，从
[Sim2Real-AlgoBench](https://github.com/p20030920p/Sim2Real-AlgoBench) 取 `src/`，
或从本仓库的 git 历史里恢复。

## 状态口径

| 状态 | 含义 |
| :--- | :--- |
| 完成 | 在本机跑通，并落在上游报的数字上 |
| 半完成 | 上游仓库只发布了方法的一半；跑的是有代码的那一半 |
| 阻塞 | 本机做不了，并写明实测缺什么（内存、CUDA、没有代码） |
| 计划 | 文件夹与方案已在，`reproduce.py` 还没写 |

## 许可

MIT，见 [LICENSE](LICENSE)。派生自
[Sim2Real-AlgoBench](https://github.com/p20030920p/Sim2Real-AlgoBench)，作者 p20030920p 与 zfyyyyy。
