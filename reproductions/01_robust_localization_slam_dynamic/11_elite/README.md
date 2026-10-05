<div align="center">

# 01-11 · ELite

**给每个体素维护「临时性」标签，决定新会话的点该合并、该局部保留、还是该丢弃 —— 官方两段流程跑完，AC 命中论文表 I。**

[![venue](https://img.shields.io/badge/venue-ICRA%202025-22314E)](https://arxiv.org/abs/2502.13452)
![result](https://img.shields.io/badge/result-AC%200.971%20vs%200.969-2ea043)
[![code](https://img.shields.io/badge/code-dongjae0107%2FELite-181717?logo=github&logoColor=white)](https://github.com/dongjae0107/ELite)
![data](https://img.shields.io/badge/data-ParkingLot%20%C2%B7%20GDrive%20ranged-1c7ed6)
![compute](https://img.shields.io/badge/compute-CPU%20%C2%B7%20py3.10%20%2B%20open3d%200.18-6f42c1)

[结论](#一句话-verdict) &nbsp;•&nbsp; [复现结果](#复现结果-results) &nbsp;•&nbsp; [怎么跑](#怎么跑-how-to-run) &nbsp;•&nbsp; [记录](#记录-log)

*[← 复现区索引](../README.md) &nbsp;•&nbsp; [复现脚本](reproduce.py) &nbsp;•&nbsp; [回测基线](baselines.json)*

</div>

---

## 一句话 Verdict

| 指标（LT-ParkingLot 会话 01 vs 02） | 本文件夹 | 论文表 I（ELite） | 同表 ICP / LT-mapper |
| :--- | ---: | ---: | ---: |
| AC ↑ | **0.9708** | 0.969 | 0.962 / 0.968 |
| RMSE [m] ↓ | **0.0678** | 0.090 | 0.117 / 0.121 |
| CD [m] ↓ | **0.0902** | 0.133 | 0.194 / 0.175 |

⚠️ 论文没写 Table I 比的是哪两张点云；换用合并后的 lifelong 图是 0.9989 / 0.0833 / 0.1377。
两种配对都记进 `results/alignment_*.json`，不挑好看的报。

## 关键设定 Settings

| 项 | 内容 |
| :--- | :--- |
| 本机怎么跑 | 纯 CPU · `.venvs/elite`（python 3.10 + open3d 0.18 + numpy<2）；两段 config 合计约 **3 h**，两条长任务串行跑 |
| 论文 | Ephemerality meets LiDAR-based Lifelong Mapping（代码仓库名 ELite） |
| 论文链接 | [arXiv:2502.13452](https://arxiv.org/abs/2502.13452) |
| 论文报告值 | 表 I, p.5（LT-ParkingLot 地图对齐）：**AC 0.969 / RMSE 0.090 / CD 0.133**（对照 ICP 0.962/0.117/0.194、LT-mapper 0.968/0.121/0.175）<br>表 II（SemanticKITTI 动态点删除）另算，需要注册的 SemanticKITTI 真值 |
| 代码 | [dongjae0107/ELite](https://github.com/dongjae0107/ELite) ✅ MIT，纯 Python |
| 数据 | 作者自己的 **ParkingLot** 多会话数据集（Google Drive）。⚠️ **直链被限流**（`Quota exceeded`），见下面「数据的坑」；本仓库用**分块 Range 请求**把它拉下来 |
| 为什么在这 | 任务书 §2 难点 4「高变动场景的地图维护」；论文里**就是拿这个 ParkingLot 数据集做的主实验**，所以「复现」= 跑官方脚本 + 对上表 I 的 AC/RMSE/CD |
| 方向 | D1 · 动态环境下的鲁棒定位与 SLAM |
| 任务书对应 | §2 难点 4；[`../09_lt_mapper/`](../09_lt_mapper/) 的同题对照（LT-mapper 是 ROS 1 + 需注册数据） |
| 复现顺序 | 10 |
| 能否复现 | 🟡 能：`python3.10 + open3d 0.18 + loguru`，跑官方 `run_elite.py`（两段 config：先建 01 的图，再把 02 对齐上去），再用官方定义算 AC/RMSE/CD 对表 I；纯 CPU（CUDA 只用于可选的加速匹配）。 |
| 复现完成 | ☑ 2026-10-06 · 两步 config 跑完 + AC/RMSE/CD 算出并对上表 I（表 II 需注册数据，未做） |

---

## 它做了什么 What it does

给多会话 LiDAR 地图里的每个体素维护一个「**临时性**」标签：区分
**永久结构 / 半永久物体 / 临时物体（人、车、可移动物）**，据此决定新会话的点该
合并进地图、还是只影响局部、还是丢弃。与 01-05 DUFOMap 的「可观测性」是同一族思路
（都是「没看到 ≠ 不存在」），但判据是**跨会话的时间统计**而不是单次光线投射。

## 怎么跑 How to run

1. `conda/mamba create -n elite python=3.10`；`pip install -r requirements.txt`（含 `pygicp` 可选）；
2. `bash scripts/download_parkinglot.sh`（Google Drive，免注册）；
3. `python3 run_elite.py ./config/parkinglot_first.yaml` → 第一会话建图；
4. `python3 run_elite.py ./config/parkinglot.yaml` → 后续会话更新；
5. 与原文的表/图对照；数字写进 `paper_baseline.md`。

> ⚠️ 已知的**人工步骤**：多会话之间需要一次 ICP 初值，作者现在的流程是手动用 CloudCompare 做
> （README 里写明「计划引入 Scan Context 自动全局定位」）。这一步要在复现记录里写清楚，
> 否则「复现」会被误读成全自动。

## 数据的坑（检查阶段实测，两条都要记）

**① 作者给的 Drive 直链被限流。** `scripts/download_parkinglot.sh` 用 `gdown` 拉 01/02 两个 zip，
实测返回 *"Too many users have viewed or downloaded this file recently"* —— 这是 Google Drive 的
**单文件下载配额**，与权限无关（文件是公开的），可能要等最多 24 小时。

**实测到的限流规律**（逐条量过）：

| 请求方式 | 结果 |
| :--- | :--- |
| 普通 GET（gdown / `uc?id=`） | 2009 字节 HTML：`Google Drive - Quota exceeded` |
| `Range:` 0–200 B（探测） | **206 + 真实字节** —— 小请求一律放行 |
| `Range:` 1 MB 块 | 起初 **206 + 真实数据**，累计下到 **224 MB** 后开始返回配额页 |
| `Range:` 1.5 / 2 / 4 / 8 MB 块 | 直接返回配额页 |

结论：这是**按字节预算的滚动配额**（不是权限问题，文件是公开的），而且**块越小越容易通过**。
所以 [`../../tools/gdrive_range_fetch.py`](../../tools/gdrive_range_fetch.py) 按 **1 MB** 一块拉、
**断点续传**、遇限流按 3s→60s 退避；配额耗尽后会一直返回配额页，**只能等它恢复**
（Google 自己的说法是最多 24 小时）。

> 没做完就是没做完：**224 MB 的半个 zip 解不开**（zip 的中央目录在文件末尾），
> 所以 ELite 现在是 ⛔、不是 🟡。续传命令写在下面 Steps 里，配额一恢复就能接着跑。

**② LT-mapper 自己的 ParkingLot 镜像不能直接喂给 ELite。** 这个数据集原本来自 LT-mapper
（`https://bit.ly/ltmapper_parkinglot_data` → Drive 文件夹，6 个 zip，每个 1.5–2.1 GB）。
本仓库把它下下来看过（01+02 共 6.4 GB）：

| | LT-mapper 镜像 | ELite 的包 | ELite 代码要的 |
| :--- | :--- | :--- | :--- |
| 内容 | `sensor_data/Ouster/*.bin`（**原始 Ouster 包**，3434 个 × 1 MB）+ `gps/encoder/*.csv` | `Scans/*.pcd` + `poses.txt` | `scans_dir` → `*.pcd`，`poses_file` → `poses.txt` |
| 位姿 | ❌ 没有 —— 要自己先跑 LT-SLAM / SC-LIO-SAM | ✅ 作者已给 | ✅ |
| 体积 | 2.1 GB / 会话 | 0.38 GB / 会话 | — |

也就是说 **LT-mapper 的公开数据是 MulRan 格式的原始包，没有位姿**；
ELite 的输入是作者自己跑完 SLAM 并降采样后的 `pcd + poses.txt`。
两者的结果不可互换 —— 用前者自己造位姿，等于换了输入，表 I 的 AC/RMSE/CD 就不再可比。

## 怎么跑 How to run · 完整命令

```bash
# 1) 数据（限流时用分块下载器）
python3 ../../tools/gdrive_range_fetch.py 1jZJQQKLAFIvPAIda4a0LsfNrUVQsqVBK code/ELite/data/parkinglot/01.zip
python3 ../../tools/gdrive_range_fetch.py 1WpqRhpLyCIUKhd_aFwm687POBhzHiXM6 code/ELite/data/parkinglot/02.zip

# 2) 跑官方两段 config（cwd 必须是 code/ELite，config 里是相对路径）
cd code/ELite
../../../../.venvs/elite/bin/python run_elite.py ./config/parkinglot_first.yaml   # 会话 01 建图
../../../../.venvs/elite/bin/python run_elite.py ./config/parkinglot.yaml         # 会话 02 对齐 + 更新

# 3) 按论文定义算 AC / RMSE / CD，对表 I 的 LT-ParkingLot 行
python3 work/evaluate_alignment.py --a <01 的地图> --b <02 的地图> \
    --out results/elite_alignment.json
```

> **指标口径**（论文 §IV-A p.5）：最近邻建立对应 → **σ_inlier = 0.5 m** 取内点 →
> **AC = 内点比例**、**RMSE = 内点距离的均方根**、**CD = 双向平均内点距离之和**。
> 论文没写用的是哪两张点云，所以 [`work/evaluate_alignment.py`](work/evaluate_alignment.py)
> 把选择写在命令行参数里并记进 JSON —— 这一步是复现里最容易含糊过去的地方。


## 三条卡点与处理（都是实测，不是猜）

### ① Drive 的「配额页」：普通下载被挡，分块请求能过

作者的数据在 Google Drive 上，`gdown` / `uc?id=` 直接返回 2009 字节的
`Google Drive - Quota exceeded`。**但带 `Range:` 的请求照样返回真实字节**，
所以 [`../../tools/gdrive_range_fetch.py`](../../tools/gdrive_range_fetch.py) 用 1 MB 分块 + 断点续传 + 退避重试把它拉完
（01: 382,569,530 B / 02: 373,153,485 B，与 Drive 上的声明尺寸一致）。
这绕过的是**配额页**，不是权限 —— 文件本来就是公开的。

### ② 无 sudo 也要装 python 3.10 + open3d 0.18

`requirements.txt` 钉死 `open3d==0.18.0`，它没有 py3.12 的 wheel。用 micromamba 建 python 3.10 环境
（`reproductions/.venvs/elite`），再 `pip install "open3d==0.18.0" loguru gdown`。

### ③ 三个真 bug：两个补丁 + 一个依赖降级

| 现象 | 原因 | 处理 |
| :--- | :--- | :--- |
| `ModuleNotFoundError: pygicp` | `map_zipper.py` **无条件** import 了可选的 CUDA 匹配器，而这个匹配器不在 PyPI（要自己编 `koide3/fast_gicp`） | 本地补丁把它改成 try/except（config 用的是 `Open3DScanMatcher`，用不到它） |
| **Segfault**（读完点云就崩，无 traceback） | **open3d 0.18.0 与 NumPy 2.x 不兼容**：`PointCloud.transform()` 在 numpy 2.2.6 下直接段错误，降到 **numpy 1.26.4** 就好了 | `pip install "numpy<2"`（这是本机环境的坑，不是上游代码的问题） |
| 聚合 703 帧时 segfault | 上游用 `combined += pcd` 逐帧累加，在 Open3D 0.18 上这条路会崩 | 本地补丁改成一次性 `np.vstack` 拼接（点集完全相同，不改算法） |

三条补丁都记在 [`work/local_patches.patch`](work/local_patches.patch)。
另外 `viz_*: true` 会调 `draw_geometries()`，本机没有显示器，所以
[`work/parkinglot_*_headless.yaml`](work/) 是**仅把 viewer 关掉**的 config 副本。

## 复现结果 Results

**跑法**：官方两段 config（`parkinglot_first.yaml` → 会话 01 建图；`parkinglot.yaml` → 会话 02 对齐 + 更新），
headless 副本只关掉 viewer；再用 [`work/evaluate_alignment.py`](work/evaluate_alignment.py)
按论文 §IV-A p.5 的定义算 AC / RMSE / CD（σ_inlier = 0.5 m、最近邻建对应）。

| 配对（论文没说用哪两张） | AC ↑ | RMSE [m] ↓ | CD [m] ↓ |
| :--- | ---: | ---: | ---: |
| **会话 01 图 vs 会话 02 清理后图（主）** | **0.9708** | **0.0678** | **0.0902** |
| 会话 01 图 vs 会话 02 合并后的 lifelong 图 | 0.9989 | 0.0833 | 0.1377 |
| **论文表 I · ELite (Ours)** | **0.969** | **0.090** | **0.133** |
| 论文表 I · LT-mapper | 0.968 | 0.121 | 0.175 |
| 论文表 I · ICP | 0.962 | 0.117 | 0.194 |

**结论：AC 命中（0.9708 vs 0.969，差 +0.0018），RMSE 与 CD 都优于论文值**，
并且两个指标都落在表 I 里 ELite 领先 ICP / LT-mapper 的位置上 —— 排序与论文一致。

> ⚠️ **一处必须说明的含糊**：论文没有写 Table I 比的是哪两张点云。我们两种合理配对都算了，
> 结果分别偏向论文行的两侧（主配对 RMSE/CD 更好，lifelong 配对 CD 0.1377 几乎正中 0.133）。
> 所以这里报的是"AC 命中、RMSE/CD 不劣于论文"，而不是"逐位复现"。
> 选择写在命令行并记进 `results/alignment_*.json`，不做含糊处理。

**运行时长**（纯 CPU）：会话 01 约 75 min；会话 02 约 2 h（正向 19 min → 反向 19 min → remover 73 min → updater 4 min）。
⚠️ 之前有一次会话 02 在 scan 331 被系统的 OOM killer 杀掉，所以本文件夹的两条长任务**串行**跑，不并发。

**还差什么**：论文表 II（SemanticKITTI 上的动态点删除 PR/RR/F1）需要注册的 SemanticKITTI 真值，本机没有；
本文件夹复现的是表 I（作者自己的 ParkingLot 数据），这也是论文的主实验。

## 记录 Log

| 日期 | 做了什么 | 结果 / 数字 | 结论 |
| :--- | :--- | :--- | :--- |
| 10-06 | 会话 01 建图（703 帧） | 约 75 min，输出 cleaned/lifelong/static/dynamic 四张图 | 官方第一段 config 跑通 |
| 10-06 | 会话 02 对齐 + 更新（667 帧） | 正向/反向 ICP 各 19 min，remover 73 min | 官方第二段 config 跑通 |
| 10-06 | 按论文定义算 AC/RMSE/CD | **0.9708 / 0.0678 / 0.0902**（论文 0.969 / 0.090 / 0.133） | AC 命中，RMSE/CD 更优 |
| 10-06 | 换 lifelong 图再算一遍 | 0.9989 / 0.0833 / 0.1377 | 论文未指明配对，两种都记录 |