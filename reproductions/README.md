# 复现区 Reproductions

按 **方向 → 论文** 两级编号，一篇论文一个文件夹。**这个页面只有索引、清单和约定**；
背景分析（两个方向、传感器契合度、与任务书 / `car.md` 的对应、论文报告值、链接核验）
在 [`NOTES.md`](NOTES.md)。

每个文件夹里：

| 文件 | 是什么 |
| :--- | :--- |
| `README.md` | 复现方案（目标 / 数据 / 步骤 / 验收）+ **复现状态**（清单就是从这几行生成的） |
| `paper_baseline.md` | **原文报告的数字**，即复现的验收标准（表号 + 页码都写清楚） |
| `reproduce.py` | 可重跑的复现脚本：`require(ctx)` 说清缺什么，`run(ctx)` 产出指标 |
| `work/` | 我们自己写的脚本、协议、坑的记录（进 git） |
| `results/` | 产物与图表（小 JSON 进 git，`*.pcd` 不进） |
| `code/` · `data/` | 克隆的上游仓库与数据集（**不进 git**，留在本机） |

<!-- PROGRESS:START -->

## 复现清单 Reproduction checklist

**按「越好复现 + 越能对上原库结果」排序** —— ☑ 10 · ◐ 2 · ☐ 1 · ⛔ 8（共 21） · 更新于 2026-10-06 01:18 CST

| # | ✓ | 复现库 | 对应论文 | 能不能复现（一句话） |
| :-- | :-- | :-- | :-- | :-- |
| 01-05 | ☑ | [KTH-RPL/dufomap](https://github.com/KTH-RPL/dufomap) | [doi:10.1109/LRA.2024.3387658](https://doi.org/10.1109/LRA.2024.3387658) | ✅ 能，而且最简单：`pip install dufomap` + KITTI 00 免注册数据，官方评测脚本直接出论文表 I。 |
| 01-06 | ☑ | [MKJia/BeautyMap](https://github.com/MKJia/BeautyMap) | [arXiv:2405.07283](https://arxiv.org/abs/2405.07283) | ✅ 能：官方仓库 `python main.py`，配同一套官方评测，命中论文表 I。 |
| 01-01 | ☑ | [KTH-RPL/DynamicMap_Benchmark](https://github.com/KTH-RPL/DynamicMap_Benchmark) | [arXiv:2307.07260](https://arxiv.org/abs/2307.07260) | ✅ 能：官方评测脚本 + Zenodo 免注册数据 `00.zip`，出论文里那张方法对比表。 |
| 01-03 | ☑ | [LimHyungTae/ERASOR](https://github.com/LimHyungTae/ERASOR) | [arXiv:2103.04316](https://arxiv.org/abs/2103.04316) | ✅ 能，但要 ROS 1（本机已用 micromamba 建好）：官方仓库跑通，对上论文表 II 的 PR/RR/F1。 |
| 01-04 | ☑ | [irapkaist/removert](https://github.com/irapkaist/removert) | [doi:10.1109/IROS45743.2020.9340856](https://doi.org/10.1109/IROS45743.2020.9340856) | ✅ 能，但要 ROS 1：官方仓库跑通；原论文没有数字表，对上的是官方仓库自己的输出。 |
| 01-08 | ☑ | [yuhaozhang7/NGD-SLAM](https://github.com/yuhaozhang7/NGD-SLAM) | [arXiv:2405.07392](https://arxiv.org/abs/2405.07392) | ✅ 能：官方代码明确「无 GPU」，TUM RGB-D 免注册直链，对上论文的 ATE / RPE 表。 |
| 01-02 | ☑ | [PRBonn/kiss-icp](https://github.com/PRBonn/kiss-icp) | [doi:10.1109/LRA.2023.3236571](https://doi.org/10.1109/LRA.2023.3236571) | ✅ 能：`pip install kiss-icp` + 官方 84.8 GB zip 里只取 00–10（43 GB，免注册），跑作者自己的 `eval/kitti.ipynb` 等价脚本即出论文表 II。 |
| 01-10 | ☑ | [cocel-postech/genz-icp](https://github.com/cocel-postech/genz-icp) | [arXiv:2411.06766](https://arxiv.org/abs/2411.06766) | ✅ 能：`pip install genz-icp pyyaml` + 已经在手的 KITTI 00–10，跑 `kitti.yaml` 预调参数即出论文表 III。 |
| 01-09 | ◐ | [gisbi-kim/lt-mapper](https://github.com/gisbi-kim/lt-mapper) | [arXiv:2107.07712](https://arxiv.org/abs/2107.07712) | 🟡 半能：要 ROS 1 + MulRan（需注册）+ 先有 SC-LIO-SAM 会话；仓库只有 ltremovert 半边，lt-map 无代码。 |
| 01-11 | ☑ | [dongjae0107/ELite](https://github.com/dongjae0107/ELite) | [arXiv:2502.13452](https://arxiv.org/abs/2502.13452) | 🟡 能：`python3.10 + open3d 0.18 + loguru`，跑官方 `run_elite.py`（两段 config：先建 01 的图，再把 02 对齐上去），再用官方定义算 AC/RMSE/CD 对表 I；纯 CPU（CUDA 只用于可选的加速匹配）。 |
| 01-12 | ☑ | [UZ-SLAMLab/ORB_SLAM3](https://github.com/UZ-SLAMLab/ORB_SLAM3) | [arXiv:2007.11898](https://arxiv.org/abs/2007.11898) | ✅ **能，而且完全不需要 GPU**：自编 Pangolin(v0.8) + ORB-SLAM3，跑 `stereo_inertial_euroc`，再用**仓库自带的** `evaluation/evaluate_ate_scale.py` 对表 II。 |
| 01-13 | ☐ | [MIT-SPARK/Khronos](https://github.com/MIT-SPARK/Khronos) | [arXiv:2402.13817](https://arxiv.org/abs/2402.13817) | ✅ **能，而且环境正好命中**：Ubuntu 24.04 + ROS 2 Jazzy 就是官方要求的组合，`colcon build` 已在本机跑通；数据（模拟 bag + GT）与评测套件都是官方直链。剩下的是跑一遍 + 用官方 `evaluate_pipeline.sh` 出表。 |
| 02-01 | ◐ | [WaldJohannaU/3RScan](https://github.com/WaldJohannaU/3RScan) | [arXiv:1908.06109](https://arxiv.org/abs/1908.06109) | 🟡 半能：仓库只有数据集 + 工具（数据要签协议），三个二进制可跑，没有方法代码。 |
| 02-06 | ⛔ | [MIT-SPARK/Clio](https://github.com/MIT-SPARK/Clio) | [arXiv:2404.13696](https://arxiv.org/abs/2404.13696) | ⛔ 按论文规模不现实：FastSAM + CLIP ViT-L 在 CPU 上每分钟只能处理少量帧，而论文是对整段 Replica 序列建图。**注意**：TensorRT 是可选的（README 明说不是必须），所以卡住的不是「有没有 GPU」这一句话，而是 CPU 的吞吐。 |
| 02-07 | ⛔ | [AnyLoc/AnyLoc](https://github.com/AnyLoc/AnyLoc) | [arXiv:2308.00688](https://arxiv.org/abs/2308.00688) | 🟡 **CPU 可以跑，只是慢**：论文的表格要 ViT-G/14 提特征（GPU 才现实），但官方 README 明确给了**小数据集 17places** 的快速入口，CPU 上做小规模检索是可行的 —— 复现目标是「同一套评测口径下的 Recall@1」，不是全量 12 个数据集。 |
| 02-08 | ⛔ | [AnyLoc/Revisit-Anything](https://github.com/AnyLoc/Revisit-Anything) | [arXiv:2409.18049](https://arxiv.org/abs/2409.18049) | 🟡 **CPU 可以跑，只是慢**：仓库自己建议先用 **17places**（约 340 张图）跑通；DINOv2 + SAM 在 CPU 上是分钟级/张，整套小数据集是小时级 —— 可行但要有耐心。 |
| 02-03 | ⛔ | [concept-graphs/concept-graphs](https://github.com/concept-graphs/concept-graphs) | [arXiv:2309.16650](https://arxiv.org/abs/2309.16650) | ⛔ 按论文规模不现实：CPU 上 PyTorch3D 与 SAM/CLIP/LLaVA 都能装能跑，但论文是对 Replica/ScanNet 整段序列建图，CPU 吞吐差两三个数量级；另外 LLaVA-7B 光权重就 ~14 GB（本机 15 GB 内存）。 |
| 02-04 | ⛔ | [Eku127/DualMap](https://github.com/Eku127/DualMap) | [arXiv:2506.01950](https://arxiv.org/abs/2506.01950) | ⛔ 按论文规模不现实：GroundingDINO + SAM 在 CPU 上能跑但每帧几十秒，论文的 Replica 序列是几千帧；本机内存 15 GB 也吃紧。 |
| 02-05 | ⛔ | [hovsg/HOV-SG](https://github.com/hovsg/HOV-SG) | [arXiv:2403.17846](https://arxiv.org/abs/2403.17846) | ⛔ 按论文规模不现实：habitat-sim 本身可以 headless 跑，CLIP/SAM 在 CPU 上也能推理，但 HM3DSem 是数千帧的大场景，CPU 上不现实。 |
| 01-07 | ⛔ | [ACFR-RPG/DynoSAM](https://github.com/ACFR-RPG/DynoSAM) | [arXiv:2501.11893](https://arxiv.org/abs/2501.11893) | 🟡 **原来的判读要改**：CUDA 不是死结 —— `nvcc` 可以**在没有 GPU 的机器上安装**（已实测：conda-forge `cuda-nvcc` 装上 CUDA 13.4 编译器），`-DDYNOSAM_NN_USE_TRT=OFF` 又能去掉 TensorRT，两者一起就把 configure 阶段的 CUDA 门去掉了。真正剩下的是**一整套 ROS 2 + GTSAM 工作区**（上游对着 ROS 2 Kilted 写，本机是 Jazzy）。 |
| 02-02 | ⛔ | — | [arXiv:2607.14899](https://arxiv.org/abs/2607.14899) | ⛔ 不能复现：代码未发布（项目页仍写 Code Soon），没有库可跑。 |

> ✓ 的含义：**☑ 已完成并对上原库/论文的结果 · ◐ 只做了一半 · ☐ 还没做 · ⛔ 本机做不了（无 GPU / 无代码）**。
> 每一行的三个字段写在对应文件夹的 `README.md` 里（`复现库` / `论文链接` / `能否复现` / `复现顺序` / `复现完成`），
> 本表由 `python3 reproductions/run_all.py` 从这些字段生成，**块内内容不要手改**；跑完一个就把那个文件夹的 `复现完成` 改成 ☑。

<!-- PROGRESS:END -->

## 目录约定 Layout

```
reproductions/
├── README.md      ← 本文件：索引 + 复现清单 + 约定
├── NOTES.md       ← 分析笔记：方向、传感器契合度、任务书关联、论文报告值
├── PAPER_BASELINES.md          ← 17 篇论文报告值总表
├── run_all.py     ← 跑复现 + 回测 + 刷新清单
├── status.json    ← 上一次运行的机器可读结果
├── tools/         ← 跨复现共享：ROS 1 环境脚本、catkin 构建脚本
├── .venvs/ · .ws/ ← 本机环境与构树（gitignore）
├── 01_robust_localization_slam_dynamic/   ← D1
└── 02_semantic_mapping_visual_anchoring_navigation/   ← D2
```

**为什么 `code/` 和 `data/` 不进 git**：上游仓库有自己的 git 历史，数据集动辄几十 GB。
本仓库只保留**我们写的**东西——步骤、脚本、配置、结论；点云产物同理。

## 自动化 Automation

```bash
python3 reproductions/run_all.py             # 跑所有能跑的复现 + 回测 + 刷新清单
python3 reproductions/run_all.py --only 02-01
python3 reproductions/run_all.py --check      # 不重跑，只按现有 status.json 重画清单
python3 reproductions/run_all.py --no-backtest
```

每次运行做四件事：**发现**每个文件夹 → **运行**有 `reproduce.py` 的复现（缺数据就标 ⛔ 而不是假装失败）
→ **回测**本次指标与 `baselines.json`（超出容差判 ❌ regressed）→ **刷新** `status.json` 与 README 里的清单。

### 约定：`checks` 与 `findings` 是两回事

| | 含义 | 失败会怎样 |
| :--- | :--- | :--- |
| **`checks`** | **不变量**：协议声称的事实，必须成立 | 判 ❌ failed，说明复现坏了 |
| **`findings`** | **测量结果**：关于数据的客观事实 | 只记录，**不阻塞**任何东西 |

### 新增一个复现

1. 建文件夹 `reproductions/<方向>/<NN_名称>/`，写好 `README.md`，里面要有这几行：
   `| 论文 |` `| Venue |` `| 论文链接 |` `| 代码 |` `| 能否复现 |` `| 复现顺序 |` `| 复现完成 |`；
2. 放一个 `reproduce.py`，实现 `require(ctx) -> None | str` 与
   `run(ctx) -> {"metrics", "checks", "findings", "artifacts"}`；
3. 跑一次 `run_all.py`，把 `status.json` 里的指标抄进 `baselines.json` 作为基线；
4. 复现对上原文之后，把那个文件夹的 `复现完成` 改成 `☑`，重跑 `run_all.py --check`。

## ROS 1 上游仓库怎么跑（01-03 ERASOR / 01-04 Removert 用这一套）

本机是 **ROS 2 Jazzy**，而这两个方法的官方仓库都是 **ROS 1 catkin** 包。
可复现的做法是 **micromamba + robostack**，不需要 root，也不需要容器：

```bash
# 一次性：建 ROS 1 Noetic 环境（empy 必须钉 3.3.4，否则消息生成会失败）
micromamba create -y -p reproductions/.venvs/ros1noetic \
  -c https://conda.anaconda.org/robostack-staging -c conda-forge \
  ros-noetic-ros-base ros-noetic-catkin ros-noetic-pcl-ros ros-noetic-cv-bridge \
  ros-noetic-tf ros-noetic-image-transport ros-noetic-jsk-recognition-msgs \
  pcl eigen boost-cpp "empy=3.3.4"

# 编译某个上游仓库（例子：Removert）
micromamba run -p reproductions/.venvs/ros1noetic \
  bash reproductions/tools/build_ros1_catkin.sh \
       reproductions/.ws/removert_ws removert <复现文件夹>/code/removert
```

两个坑已经封装进工具脚本：ROS 1 / ROS 2 同名库导致的 `symbol lookup error`
（`tools/ros1_env.sh` 把 `/opt/ros/jazzy*` 从环境里剥掉）、conda 的 PCL 不导出 VTK
（构建脚本自动补 VTK include 与 `-Wl,--copy-dt-needed-entries`）。
上游源码需要的 **API 漂移补丁** 逐个记在对应复现的 `work/local_patches.patch`，**算法逻辑不改**。
