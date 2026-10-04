# 01-03 · ERASOR

| 项 Item | 内容 |
| :--- | :--- |
| 论文 | ERASOR: Egocentric Ratio of Pseudo Occupancy-Based Dynamic Object Removal for Static 3D Point Cloud Map Building |
| Venue | **RA-L 2021** |
| 论文链接 | [arXiv:2103.04316](https://arxiv.org/abs/2103.04316) |
| 论文报告值 | [`paper_baseline.md`](paper_baseline.md) —— 表 II, p.8：PR/RR/F1 = 93.980 / 97.081 / 0.955 |
| 代码 | [LimHyungTae/ERASOR](https://github.com/LimHyungTae/ERASOR) ✅ **官方仓库已编译并跑通** |
| 数据 | ✅ **官方 seq-00 rosbag + 全部 PCD/GT 直链可下**（作者服务器，免注册） |
| 方向 | D1 · 动态环境下的鲁棒定位与 SLAM |
| 任务书对应 | §2 难点 4 高变动场景的地图维护；§6 并行实验 H1′ |
| 复现状态 | 🟢 **官方实现复现成功：PR/RR/F1 = 95.62 / 94.41 / 0.950**（论文表 II 93.98 / 97.08 / 0.955，作者自己在 master 上重跑是 95.79 / 95.64 / 0.957） |

| 复现顺序 | 4 |
| 能否复现 | ✅ 能，但要 ROS 1（本机已用 micromamba 建好）：官方仓库跑通，对上论文表 II 的 PR/RR/F1。 |
| 复现完成 | ☑ 2026-10-05 · 官方实现 PR/RR/F1 = 95.62 / 94.41 / 0.950 |

## 它做了什么 What it does

把地图切成极坐标的「伪占据」体素，用每个体素在单次扫描中占据的高度比（egocentric ratio）与阈值判断它是不是动态，然后删除。

## 为什么复现它 Why

**阈值敏感方法的代表**：不同数据集要用不同阈值，换场景就要重调。这正是任务书 §1 H9 说的「删除决策没有被标定」的最直接物证——如果它的 F1 很高但定位效果一般，H1′ 就成立了一半。

## 复现目标（可验收）Goals

- [x] **用作者自己的仓库编译并跑通**，在官方 seq 00 上产出清理后的地图
- [x] 用**作者自己的评测器与 GT** 打分，与论文表 II 对比
- [x] 记录阈值（全部保留上游 `config/seq_00.yaml`，只改路径）
- [ ] 换阈值做一次敏感性扫描（`scan_ratio_threshold` 上游 2026-05 已从 0.2 改成 0.1，值得单独跑一遍）
- [ ] 把清理后的地图交给 01-02，得到配准失败率
- [ ] 产出：阈值—F1—定位失败率 的三者关系图

## 步骤 Steps（全部可重跑）

```bash
# 0. 一次性：ROS 1 Noetic 环境（本机是 ROS 2 Jazzy、无 sudo、无 Docker）
#    完整命令与两个坑见 ../README.md「ROS 1 上游仓库怎么跑」
micromamba create -y -p reproductions/.venvs/ros1noetic \
  -c https://conda.anaconda.org/robostack-staging -c conda-forge \
  ros-noetic-ros-base ros-noetic-catkin ros-noetic-pcl-ros ros-noetic-cv-bridge \
  ros-noetic-tf ros-noetic-laser-geometry ros-noetic-roslaunch \
  ros-noetic-message-generation ros-noetic-jsk-recognition-msgs \
  pcl eigen boost-cpp "empy=3.3.4"

# 1. 官方仓库 + 官方数据（作者直链，免注册）
git clone https://github.com/LimHyungTae/ERASOR code/ERASOR
wget https://urserver.kaist.ac.kr/publicdata/erasor/erasor_paper_pcds.zip -P data/official \
  && unzip data/official/erasor_paper_pcds.zip -d data/official
wget https://urserver.kaist.ac.kr/publicdata/erasor/rosbag/00_4390_to_4530_w_interval_2_node.bag \
  -P data/official            # 406 MB；服务器支持 Range，可 8 路并行分段下（见下）

# 2. 编译（两个 PCL/API 漂移补丁，记录在 work/local_patches.patch）
micromamba run -p reproductions/.venvs/ros1noetic \
  bash reproductions/tools/build_ros1_catkin.sh \
       reproductions/.ws/erasor_ws erasor <本文件夹>/code/ERASOR

# 3. 一条命令跑完（mapgen → ERASOR → 官方评测 → 回测）
python3 reproductions/run_all.py --only 01-03
```

> 下载小技巧：`Content-Length: 425895181`、`Accept-Ranges: bytes`，所以
> `curl -r a-b` 分 8 段并行能把 30 分钟的等待压到 2 分钟。
> 单线程 wget 在这个服务器上只有 ~200 KB/s。

## 坑与注意 Pitfalls

| 坑 | 症状 | 处理 |
| :--- | :--- | :--- |
| Noetic 消息生成 | `AttributeError: module 'em' has no attribute 'RAW_OPT'` | 装 `empy=3.3.4`（robostack 默认给 4.x） |
| 缺 jsk 消息 | `fatal error: jsk_recognition_msgs/PolygonArray.h` | `ros-noetic-jsk-recognition-msgs` |
| PCL 的 VTK 头 | `vtkSmartPointer.h: No such file` | 构建脚本补 `-I$ENV/include/vtk-9.2` |
| PCL 的 VTK 库 | 链接期 `libvtksys-9.2.so.1: DSO missing from command line` | 构建脚本补 `-Wl,--copy-dt-needed-entries` |
| PCL ≥ 1.11 智能指针 | `load_pcd(std::string, boost::shared_ptr<...>)` 无匹配重载 | 改成 `std::shared_ptr`（`work/local_patches.patch`） |
| `PassThrough` API | `no member named 'setFilterLimitsNegative'` | 改成 `setNegative(true)` |
| **两个 wget 写同一个文件** | `rosbag info` 之前看不出问题，之后才发现 | 用 `rosbag info` 校验；本次已按 Range 重新完整下载 |
| 坐标帧 | 基准 Zenodo 的世界系与官方 GT **不是同一帧**（实测中位差 1.6 m，仅 6% 点在 0.2 m 内） | 官方 GT 只能用官方 bag 跑，不能混用 |

## 复现结果 Results（2026-10-05）

### 一、官方实现：PR/RR/F1 = 95.62 / 94.41 / 0.950

跑法：官方 `kitti_mapgen` 建朴素地图 → 官方 `offline_map_updater` 跑 ERASOR
（`config/seq_00.yaml` 原样，只改路径）→ 官方 `scripts/analysis_runner.py`
对官方 GT `erasor_paper_pcds/gt/00_voxel_0_2.pcd` 打分。
评测流程本身先自检：**把作者自己发布的 `estimate/00_ERASOR.pcd` 放进去，得到
93.979 / 97.081 / 0.9550，与论文表 II 的 93.980 / 97.081 / 0.955 完全一致** ——
说明评测器、GT、体素规则都是论文的那一套。

| | PR [%] | RR [%] | F1 |
| :--- | ---: | ---: | ---: |
| 作者发布的输出（我们重打分，用于自检） | 93.979 | 97.081 | 0.9550 |
| **ERASOR 论文 表 II, p.8** | 93.980 | 97.081 | 0.955 |
| 作者在 master 上重跑（仓库 README） | 95.790 | 95.642 | 0.957 |
| **本次：官方代码 + 官方 bag + 官方评测器** | **95.622** | **94.412** | **0.9501** |

**结论**：PR 与作者重跑差 0.17 pp，F1 差 0.007；与论文表 II 的 F1 差 0.005。
RR 比作者的 95.64 低 1.2 pp —— 我们的地图留下 268 个动态 GT 点，作者留下 140 个。
差异来源可查（mapgen 的朴素地图点数、`rosbag play` 的送帧时序、上游 2026-05 的阈值改动），
**不是随机的：整条链路的每一步都有日志**。

### 二、低 SA 不是"删太多"，是**下采样**（基准口径）

输出地图只有 **1,417,955** 点，而 GT 有 **17,362,230** 点 —— 少了一个数量级。
原因是 ERASOR 的 `MapUpdater` 以 `map_voxel_size: 0.1` 做体素化。

于是 `export_eval_pcd` 的「0.05 m 内找不到邻居就判为删除」把**大量下采样掉的静态点读成了删除**：
`false_removal = 5,748,315`，而真正漏掉的动态点只有 `1,406`。
**SA 66.71 里的绝大部分是分辨率损失，不是算法错误。**

### 三、同一个 ERASOR，两套口径差 29 个百分点

| 口径 | 数据集 | 指标 | 数值 |
| :--- | :--- | :--- | ---: |
| **ERASOR 论文 表 II, p.8** | SemanticKITTI 00（4390–4530） | voxel-wise PR / RR / F1（voxel 0.2） | **95.62** / 94.41 / 0.950（本次） |
| **DynamicMap_Benchmark 表 I, p.5** | KITTI 00（同段，141 帧） | 点级 SA / DA / AA | **66.71** / 98.54 / 81.07（本次） |

**同一个方法，从 95.62 掉到 66.71。** 而 Removert 在同样两套口径下是 **85.50 → 99.44**——
**换一套指标，两个方法的排名直接翻转**。这就是任务书 §6 并行实验 H1′ 要问的问题，
现在两个方法各自都有了官方实现的数字，见 [`../PAPER_BASELINES.md`](../PAPER_BASELINES.md) §3.1。

> ⚠️ 与 01-04 的差别值得单独记一句：**Removert 的官方实现与基准重实现差 47.7 pp（DA），
> ERASOR 的官方实现与基准重实现在各自口径下都能自洽**。
> 也就是说，"基准里的重实现不可信"不是普遍规律，是**逐个方法都要查**的事情。

```bash
python3 reproductions/run_all.py --only 01-03
```

## 记录 Log

| 日期 | 做了什么 | 结果 / 数字 | 结论 |
| :--- | :--- | :--- | :--- |
| 2026-10-05 | 跑基准无 ROS 重实现，命中基准表 I 行 | SA/DA/AA = 66.7078 / 98.5352 / 81.0744 | ✅ 基准可复现 |
| 2026-10-05 | 建 ROS 1 Noetic 环境（micromamba/robostack） | `rosversion -d` → noetic | ROS 1 阻塞解除 |
| 2026-10-05 | 编译官方仓库 | 2 处 PCL API 补丁 + VTK 头/库 | 算法源码未改 |
| 2026-10-05 | 下载官方 bag（406 MB）与 paper PCDs | 8 路 Range 并行，2 分钟 | 作者服务器免注册 |
| 2026-10-05 | 评测链自检：重打分作者发布的输出 | 93.979 / 97.081 / 0.9550 | 与论文表 II 一致，评测器可信 |
| 2026-10-05 | 官方 mapgen + ERASOR 全流程 | 47 s，374,393 点静态图 | 官方实现跑通 |
| 2026-10-05 | 官方评测器打分 | **PR 95.622 / RR 94.412 / F1 0.9501** | 与论文 F1 差 0.005，与作者重跑差 0.007 |
