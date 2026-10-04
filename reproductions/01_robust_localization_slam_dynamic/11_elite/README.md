# 01-11 · ELite

| 项 Item | 内容 |
| :--- | :--- |
| 论文 | Ephemerality meets LiDAR-based Lifelong Mapping（代码仓库名 ELite）|
| Venue | **ICRA 2025**（arXiv:2502.13452） |
| 论文链接 | [arXiv:2502.13452](https://arxiv.org/abs/2502.13452) |
| 论文报告值 | 多会话「临时性」判别（ephemerality）与地图更新，数字待从原文补录（HTTP 可达，尚未逐表核对） |
| 代码 | [dongjae0107/ELite](https://github.com/dongjae0107/ELite) ✅ MIT，纯 Python |
| 数据 | 作者自己的 **ParkingLot** 多会话数据集：Google Drive 直链，仓库自带 `scripts/download_parkinglot.sh`（用 `gdown` 下载 01/02 序列） |
| 为什么在这 | 任务书 §2 难点 4「高变动场景的地图维护」；论文里**就是拿这个 ParkingLot 数据集做的主实验**，所以「复现」= 跑官方脚本 + 对上原文的表/图 |
| 方向 | D1 · 动态环境下的鲁棒定位与 SLAM |
| 任务书对应 | §2 难点 4；[`../09_lt_mapper/`](../09_lt_mapper/) 的同题对照（LT-mapper 是 ROS 1 + 需注册数据） |
| 复现状态 | ⬜ 未开始（已检查：代码可达、数据免注册、纯 CPU） |

| 复现顺序 | 10 |
| 能否复现 | 🟡 能（比 LT-mapper 容易）：`conda create -n elite python=3.10` + `gdown` 拉 ParkingLot 示例 → `python3 run_elite.py ./config/parkinglot.yaml`；纯 CPU，CUDA 只用于可选的加速匹配。 |
| 复现完成 | ☐ 待做 |

## 它做了什么 What it does（先记结论，复现时再逐行读代码）

给多会话 LiDAR 地图里的每个体素维护一个「**临时性**」标签：区分
**永久结构 / 半永久物体 / 临时物体（人、车、可移动物）**，据此决定新会话的点该
合并进地图、还是只影响局部、还是丢弃。与 01-05 DUFOMap 的「可观测性」是同一族思路
（都是「没看到 ≠ 不存在」），但判据是**跨会话的时间统计**而不是单次光线投射。

## 复现计划 Steps

1. `conda/mamba create -n elite python=3.10`；`pip install -r requirements.txt`（含 `pygicp` 可选）；
2. `bash scripts/download_parkinglot.sh`（Google Drive，免注册）；
3. `python3 run_elite.py ./config/parkinglot_first.yaml` → 第一会话建图；
4. `python3 run_elite.py ./config/parkinglot.yaml` → 后续会话更新；
5. 与原文的表/图对照；数字写进 `paper_baseline.md`。

> ⚠️ 已知的**人工步骤**：多会话之间需要一次 ICP 初值，作者现在的流程是手动用 CloudCompare 做
> （README 里写明「计划引入 Scan Context 自动全局定位」）。这一步要在复现记录里写清楚，
> 否则「复现」会被误读成全自动。
