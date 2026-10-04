# 01-09 · LT-mapper

| 项 Item | 内容 |
| :--- | :--- |
| 论文 | LT-mapper: A Modular Framework for LiDAR-based Lifelong Mapping |
| Venue | **ICRA 2022** |
| 论文链接 | [arXiv:2107.07712](https://arxiv.org/abs/2107.07712) |
| 论文报告值 | [`paper_baseline.md`](paper_baseline.md) —— 原论文自报结果与复现阻塞分析 |
| 代码 | [gisbi-kim/lt-mapper](https://github.com/gisbi-kim/lt-mapper) ✅ 实测 200 |
| 数据 | MulRan / KITTI（多会话序列） |
| 方向 | D1 · 动态环境下的鲁棒定位与 SLAM |
| 任务书对应 | §2 难点 4 地图维护；car.md 难点 3「终身 SLAM」与参考库 |
| 复现状态 | 🟢 **变化检测半边已跑通**（官方 `ltremovert`，KITTI 00 双会话切分，SA/DA/AA = 69.14/74.51/71.78）；**LT-map / delta-map 半边仓库里没有代码**，论文 85.7 MB / 9.8 s 不可复现；`ltslam` 需 GTSAM（本机未装，未安装任何东西） |

| 复现顺序 | 8 |
| 能否复现 | 🟡 半能：要 ROS 1 + MulRan（需注册）+ 先有 SC-LIO-SAM 会话；仓库只有 ltremovert 半边，lt-map 无代码。 |
| 复现完成 | ◐ 变化检测半边已跑通，建图半边仓库里没有 |

## 它做了什么 What it does

模块化的长期 LiDAR 建图流水线：**多会话 SLAM（MSS）→ 高/低动态变化检测 → 正/负变化管理**，并在会话间维护位姿图，因此不要求好的初始对齐。

## 为什么复现它 Why

它是任务书 §4.1「地图更新策略」和 car.md 难点 3「终身 SLAM」共同指向的那篇工作。关键复现点在于它的**变化检测是几何的、体素阈值化的**——能报出变化区域，却分不清「结构真的变了」和「只是这次被挡住了」。这句话如果能在实验里复现出来，就直接支撑了「可观测性」这个切入点。

## 仓库里有什么、没有什么 What is and is not in the checkout

| 论文模块 | 包 | 本次是否运行 | 原因 |
| :--- | :--- | :--- | :--- |
| 多会话 SLAM（MSS, LT-SLAM） | `ltslam` | ❌ | `ltslam/CMakeLists.txt:26` 要 GTSAM，本机 `find .venvs/ros1noetic -iname '*gtsam*'` 无结果；本次不安装任何东西 |
| 变化检测（LT-removert） | `removert`（目录 `ltremovert/`） | ✅ **本次运行** | 不链接 GTSAM（`ltremovert/CMakeLists.txt:27,88-94`），依赖齐全 |
| LT-map / delta-map（论文 85.7 MB / 9.8 s） | — | ❌ | **仓库里根本没有代码**：全仓库 grep `delta_map\|meta_map` 0 命中，`Removerter.cpp:1671` 只是注释 |

## 复现目标（可验收）Goals

- [ ] 跑通多会话对齐，得到跨会话的位姿图 → **需要 GTSAM，本次未做**（见上表）
- [x] 复现它的变化检测，记录**用了什么阈值** → 用的是上游自己的 `config/params_ltmapper.yaml`，一字未改（阈值为 `remove_resolution_list [2.5]`、`revert_resolution_list [2.2]`、`num_nn_points_within 2`、`dist_nn_points_within 0.01`、`downsample_voxel_size 0.05`）
- [ ] **关键实验**：构造一个「结构未变但本次被遮挡」的场景，看它是否误报变化 → 本次数据（同一条 KITTI 00 连续行驶的先后两段）里，遮挡/视角差异**已经**是「变化」的一部分；见下面 Results 的 finding
- [x] 产出：官方实现的实测数字 + 覆盖度分析（`results/*.json`）

## 复现怎么跑 How to reproduce

```bash
# 1) 只构建 removert 包（SRC 必须是*包目录*，给仓库根目录 catkin 会去编 ltslam 然后卡在 GTSAM）
micromamba run -p reproductions/.venvs/ros1noetic bash reproductions/tools/build_ros1_catkin.sh \
    reproductions/.ws/lt_mapper_ws ltremovert \
    reproductions/01_robust_localization_slam_dynamic/09_lt_mapper/code/lt-mapper/ltremovert

# 2) 一条命令跑完：生成两会话输入 → 生成 rosparams → 跑官方节点 → 打分
python3 reproductions/run_all.py --only 01-09
```

`reproduce.py` 里的每一步都是独立可复跑的脚本（都在 `work/`）：

| 文件 | 作用 |
| :--- | :--- |
| [`work/make_ltmapper_sessions.py`](work/make_ltmapper_sessions.py) | 从 benchmark 的 world-frame 点云反解出**传感器坐标系** `.pcd` 扫描 + 12 数一行的位姿文件，切出两个会话 |
| [`work/verify_sessions.py`](work/verify_sessions.py) | 校验三条不变量：扫描数=位姿行数、编号与位姿一一对应、坐标系是传感器系（用位姿把扫描变回世界系能与源点云对上，实测 ~4e-6 m） |
| [`work/gen_params.py`](work/gen_params.py) | 读上游 `params_ltmapper.yaml`，**只改 4 个路径 + start/end idx**，其余算法参数原样写出 |
| [`work/run_official.sh`](work/run_official.sh) | roscore + `rosparam load` + `rosrun removert removert_removert`（上游是离线的，ROS 只当参数服务器用） |
| [`work/merge_cleaned_scans.py`](work/merge_cleaned_scans.py) | 把 `scans_updated/` 的 81 张干净扫描按位姿合并成一张全局图（上游 `mergeScansWithinGlobalCoord` 的做法） |
| [`work/make_coverage_matched_gt.py`](work/make_coverage_matched_gt.py) | 按「本次真正喂进去的扫描看到过」筛 GT，得到公平对比的 GT（覆盖度由**输入**定义，不由输出定义，所以不循环论证） |
| [`work/local_patches.patch`](work/local_patches.patch) | 唯一一处源码改动，见下 |

### 唯一的源码补丁

[`work/local_patches.patch`](work/local_patches.patch)：`ltremovert/src/Removerter.cpp:938` 的
`boost::shared_ptr<std::vector<int>>` → `pcl::IndicesPtr`（PCL ≥ 1.11 的 `ExtractIndices::setIndices` 收
`pcl::IndicesPtr`）。这是整个 checkout 编译期的**唯一**一个 error（`grep 'error:' → 1`），没有碰任何算法行；
与 04_removert 需要的是同一类修复（那边还多一个 `<opencv/cv.h>`，ltremovert 没有这个问题）。

## Input 是怎么造出来的 Why not the paper's dataset

论文的 ParkingLot 数据是 **6 个会话 / 3 天**，但下下来是 **raw Ouster + IMU**，还得先过 SC-LIO-SAM 才能喂给
ltremovert；作者 Docker 镜像 2.2 GB 而本机没有 docker；MulRan 的 KAIST 04 要发邮件索取。本机**已有**的是
benchmark 的 KITTI 00：141 帧 world-frame 点云，`VIEWPOINT` 字段里存着传感器位姿，可以反解回传感器系
（和 [`02_kiss_icp/work/make_kitti_seq.py`](../02_kiss_icp/work/make_kitti_seq.py) 同一个反演，只是这次写 `.pcd`，
因为 ltremovert 的 `.bin` 分支在 `Session.cpp:277-281` 被注释掉了）。两个会话的位姿**本来就在同一个世界系**，
所以不需要 `ltslam`、也就不需要 GTSAM。

```
central session（待清理的地图）  KITTI 00 第 4390..4470 帧，81 张
query   session（清洁工）        KITTI 00 第 4451..4530 帧，80 张 → 被 10 m ROI 规则（Session.cpp:234）自动裁到 29 张
```

## Results

所有数字由 `01_dynamicmap_benchmark/work/evaluate.py --impl both` 打出，官方 `export_eval_pcd` 与 scipy 复实现
**逐点一致**（`disagreeing_points: 0`）。地图都是官方 `removert_removert` 二进制的输出。

### 1. 本次头条行（map-side 输出 `updated_map.pcd`，公平 GT = 两个会话都看到过的区域）

| map | GT | 点数 | SA | DA | AA | HA |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: |
| `updated_map.pcd` | 覆盖度匹配 GT（两会话，12,363,618 static / 88,508 dynamic） | 758,035 | **69.14** | **74.51** | **71.78** | 71.73 |
| `updated_map.pcd` | 完整 141 帧 GT（sibling 用的协议） | 758,035 | 49.51 | 76.50 | 61.54 | 60.11 |
| `OriginalNoisyCentralMapGlobal.pcd`（**未清理**原始图，对照组） | 完整 141 帧 GT | 2,675,552 | 66.22 | 49.11 | 57.03 | 56.40 |

**为什么两个 SA 差 20 pp**：本次只跑了整条轨迹里的 110 帧，其中 GT static 点只有 **71.61%** 落在这些扫描
看得见的范围内（dynamic 92.21%）。拿它去比完整 141 帧 GT，等于把「没开过去的地方」算成误删。所以 headline
用覆盖度匹配的 GT；完整 GT 那一行照样记下来，但它**不能**和 sibling 行并排比。表里第 3 行是同一个道理的极端例子：**什么都没删**的原始图
在完整 GT 上也只有 SA 66.22 —— 覆盖度是天花板，不是方法的问题。

### 2. 关键对照：同一块 GT 上，「没做变化检测」vs「做了」

GT 固定为 central 会话自己的覆盖范围（11,497,294 static / 49,658 dynamic），三张图都出自**同一次运行**：

| map | 点数 | SA | DA | AA | HA |
| :--- | ---: | ---: | ---: | ---: | ---: |
| `OriginalNoisyCentralMapGlobal.pcd`（**未清理**的原始图，对照组） | 2,675,552 | 99.44 | 1.65 | 12.82 | 3.25 |
| `updated_map.pcd`（map-side，Step 3 结果） | 758,035 | 69.75 | 79.22 | 74.33 | 74.18 |
| `scans_updated_merged.pcd`（scan-side，81 张干净扫描合并） | 7,100,333 | 64.08 | 79.85 | 71.53 | 71.10 |

即：这次配置下，变化检测**用 29.7 pp 的静态保留换了 77.6 pp 的动态剔除**。原始图 SA 99.44 是「什么都不删」
换来的 DA 1.65。

对照 [04_removert](../04_removert/) 在同种数据上的官方运行（SA 99.62 / DA 89.25）：差距主要来自**上游自己的配置**
——04 用 `params_kitti.yaml` 的 `dist_nn_points_within: 0.1`，ltremovert 用 `params_ltmapper.yaml` 的
`0.01`，严格 10 倍（要求两个会话的表面一致到 1 cm）。这不是我们调出来的，是上游给不同数据集写的配置。

### 3. 两个上游输出，以及 ND/PD 不对称

- **两个输出这次靠得很近**：同一块 GT 上 map-side AA 74.33 vs scan-side AA 71.53，只差 2.8 pp。这一点和
  01-04 不同（那边 Removert 的两个输出位于 trade-off 的两个对角，AA 差 33 pp），所以「ltremovert 的分数」
  在这里主要由**打分用哪块 GT**决定，而不是由交哪个输出决定。
- **ND/PD 严重不对称**：`nd_map.pcd`（只在 central 出现）218,931 点 vs `pd_map.pcd`（只在 query 出现）
  43,853 点，**5.0 倍**。原因是 query 会话只覆盖 central 会话 40.8 m 轨迹里约 15 m 的一段，大量 central 结构
  根本不在 query 视野里。真正「两次访问同一个停车场」的多会话数据不会有这个形状——这也正是本次数据与论文
  实验的差距所在。
- `map_static/` 与 `map_dynamic/` **是空的**：这一版代码里 `saveCurrentStaticAndDynamicPointCloudGlobal`
  在 `run()` 能走到的路径上只被 `_MVM` 那个调试调用触发，所以没有 map-side static map 落盘。地图级的交付物
  就是 `updated_map.pcd`。
- 运行时间：官方节点处理 81+29 个关键帧约 **38 s**（同一输入热缓存时约 8 s；全部工作在构造函数里做完，之后 `ros::spin()`）。这**不是**
  论文的 9.8 s——那个数属于 LT-map 的 delta-map 更新，代码不在此仓库里。

## 结论与诚实的边界 Verdict and honest limits

1. **能复现的部分已经复现**：官方 `ltremovert` 二进制、上游自己的参数、KITTI 00 双会话输入，SA/DA/AA =
   **69.14 / 74.51 / 71.78**（覆盖度匹配 GT；完整 GT 下 49.51 / 76.50 / 61.54）。打分链路双实现逐点一致。
2. **这不是论文的实验**：一条连续行驶切两段 ≠ 3 天 6 会话的停车场。这里的「变化」是**运动的车 + 遮挡与视角
   差异**，重叠区只有约 15 m 轨迹。任何与论文 ParkingLot 结论的对照都是在比实验，不是在比实现。
3. **论文头条数字不可复现**：delta map 85.7 MB / 9.8 s 属于 LT-map 模块，**仓库里没有这个模块**（0 grep 命中），
   且 Tab. I/II 还要 MulRan KAIST 04（需邮件索取）。本 checkout 在任何环境下都跑不出那两个数。
4. **和 sibling 行不可直接并排比**：01-03/01-04/01-05 的地图覆盖完整 141 帧，本次只覆盖 110 帧（GT static 的
   71.61%）。要做真正可比的对照，得让 central 会话覆盖整条轨迹——但那样 query 就成了 central 的子集，
   变化检测会退化成自比较。这个取舍本身是本次复现最值得记下来的结论。

## 坑与注意 Pitfalls

- ROS1，与本仓库的 ROS 2 环境隔离；`tools/ros1_env.sh` 会把 `/opt/ros/jazzy*` 从各路径里剔掉。
- 它的模块是分步的（MSS / CD / CM），**按模块验收**，不要指望一条命令跑到底——本次只验收了 CD。
- `catkin_make` 的 SRC **必须是包目录** `.../lt-mapper/ltremovert`；给仓库根目录会把 `ltslam` 一起软链进
  `src/`，然后停在 `find_package(GTSAM REQUIRED QUIET)`。
- 扫描必须是**传感器系**：`precleaningKeyframes(2.5)`（`Session.cpp:506-533`）会以扫描原点为球心挖掉 2.5 m 球，
  喂 world-frame 点云等于在世界原点挖球，而车早在 20 m 外。
- 文件名排序必须等于位姿行序；Release 构建把 `assert` 编掉了，不匹配不会报错，只会静默错位。
- 大文件（`*.pcd`、`data/`）按设计被 gitignore；提交的是 JSON 指标和脚本。

## 记录 Log

| 日期 | 做了什么 | 结果 / 数字 | 结论 |
| :--- | :--- | :--- | :--- |
| 2026-10-05 | 只读可行性评估（`work/feasibility.md`） | 2 个 catkin 包；GTSAM 缺失只挡 `ltslam`；LT-map 代码不存在 | 变化检测半边可做，零安装 |
| 2026-10-05 | 只构建 `ltremovert` 包（SRC 指向包目录） | 首次编译 **1 个 error**：`Removerter.cpp:938` 的 `boost::shared_ptr`；打补丁后编译通过，产物 `reproductions/.ws/lt_mapper_ws/devel/lib/removert/removert_removert` | PCL 1.13 API 漂移，补丁入库为 `work/local_patches.patch` |
| 2026-10-05 | 生成两会话传感器系输入（81 + 80 帧） | `data/raw/kitti00_two_sessions/`；反演回世界系误差 max 4.1e-6 m；IOU 区 = 29/80 帧，与 `Session.cpp:234` 的 10 m 规则重算一致 | 输入合法且与评估口径互证 |
| 2026-10-05 | 跑官方节点（上游参数零改动） | 81 central + 29 query 关键帧，~38 s；`updated_map.pcd` 758,035 点；`scans_updated/` 81 张 | 官方 CD 模块在本机跑通 |
| 2026-10-05 | 修驱动：完成标记复用了上一轮的残留文件 | 上一轮 `run_all.py` 其实在节点跑完前就 kill 了它（日志块缓冲导致误判），改成「先删标记 + 运行前清空输出目录 + 按每目录 81 个文件验收」 | 复现脚本必须能证明是**本轮**跑出来的，否则绿灯是假的 |
| 2026-10-05 | benchmark 打分（`--impl both`） | 覆盖度匹配 GT：**SA/DA/AA = 69.14 / 74.51 / 71.78**；完整 141 帧 GT：49.51 / 76.50 / 61.54；两实现逐点一致 | 覆盖率（GT static 71.61%）是完整 GT 分数的主因，已单独记录 |
| 2026-10-05 | 同 GT 对照实验（未清理原始图） | 原始图 SA 99.44 / DA 1.65 → 清理后 69.75 / 79.22（central GT） | 量化了「29.7 pp 静态换 77.6 pp 动态」的取舍；也与 04 的 `dist_nn 0.1` vs 本次 `0.01` 配置差异对上 |
