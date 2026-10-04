# 01-09 · LT-mapper — 论文报告值 Paper-reported baseline

| 项 Item | 内容 |
| :--- | :--- |
| 论文 | LT-mapper: A Modular Framework for LiDAR-based Lifelong Mapping |
| Venue / 年 | ICRA 2022（pp. 7995–8002）——**注意：PDF 本身是 arXiv 预印本 arXiv:2107.07712v1, 2021-07-16，页眉页脚未印任何 venue**；ICRA 2022 的出处信息来自官方 repo 的 BibTeX："2022 International Conference on Robotics and Automation (ICRA), pages 7995--8002" |
| 本地 PDF | `Localise/01_task_books/materials/papers_pdf/068_LT_mapper.pdf`（结果表在第 6 页：Tab. I @p.6、Tab. II @p.6；**Fig. 8 的轨迹误差在第 5–6 页，但只有图形、无任何可提取的数值**） |
| 官方代码 | https://github.com/gisbi-kim/lt-mapper （论文 p.2 脚注给出同一 URL；另有两个配套仓库：数据生成工具 <https://github.com/gisbi-kim/SC-LIO-SAM>、变化检测引擎 <https://github.com/gisbi-kim/removert>） |
| 任务 | LiDAR 终身建图（lifelong mapping）的三模块框架：**LT-SLAM**（多会话 SLAM / MSS，anchor node 跨会话回环对齐）、**LT-removert**（高动态 HD 点去除 + 低动态 LD 变化检测，分 PD/ND，并用 weak ND preservation 处理遮挡）、**LT-map**（地图更新与变化复合，产出 live map 与 meta map，用 delta map 节省内存/算力） |
| 数据集 | ① **MulRan**：KAIST 序列（01、02、**以及扩展序列 04**）与 **DCC** 序列（01、02）——论文原文"**We used the KAIST and DCC sequences to identify long-term changes**"（p.5 §V-A2）；② **LT-ParkingLot**（自采）：**6 个 session、跨 3 天**、各 session 原点不同、初始全局对齐未知（p.5 §V-A2） |
| 指标 | ① **轨迹评估**：用 **RPG trajectory evaluation tool [38]**，报 **translation error [%]** 与 **yaw error [deg]**（**仅出现在 Fig. 8 的图中，无数值表**）；② **变化检测精度**：**Chamfer distance (CD)** 的 **Max / Avg / Var**，做法是把对齐后的地图切成 **5 m³ 立方体 patch**，只统计**至少含 25 个点**的 patch（记为 **NP_valid**），并统计距离大于阈值 τ∈{1,2,3} 的 patch 数（**NP_CD>τ**）；③ **效率**：**Memory Usage [MB]**（merged map）与 **Computation Time [sec]**，以及 **efficiency ratio**（相对 snapshot baseline） |
| 硬件 | **未找到**。检索关键词 CPU / GPU / Intel / NVIDIA / GHz / core / hardware / desktop / laptop，PDF 全文无任何运行硬件描述。论文只说明实现方式：**全部模块用 C++ 编写**，位姿图优化用 **GTSAM [37] 的 iSAM2 [36]**，采用了公开的 **Scan Context [10]** 与 **Removert [8]** 源码（p.5 §V-A1） |

## 论文报告的数字 Reported numbers

### Tab. I（p.6）—— 变化复合（Fig. 10）的 Chamfer distance 精度评估

| 出处（表/图 + 页） | 数据集 / 序列 | 方法 | 指标 | 数值 |
| :--- | :--- | :--- | :--- | ---: |
| **表 I, p.6** | MulRan，Pos. Pair（KAIST 01 ↔ **Restored** 01） | Ours（LT-map 变化复合） | CD Max | **6.41** |
| **表 I, p.6** | MulRan，Pos. Pair（01 ↔ Restored 01） | Ours | CD Avg | **0.29** |
| **表 I, p.6** | MulRan，Pos. Pair（01 ↔ Restored 01） | Ours | CD Var | **0.31** |
| **表 I, p.6** | MulRan，Pos. Pair（01 ↔ Restored 01） | Ours | NP_CD>τ，τ=1 / 2 / 3 | **38 / 9 / 1** |
| **表 I, p.6** | MulRan，Pos. Pair（01 ↔ Restored 01） | Ours | NP_valid（≥25 点的 patch 数） | **1424** |
| 表 I, p.6 | MulRan，Neg. Pair（KAIST 01 ↔ 04，即两张真实的不同时期地图） | 对照（负样本） | CD Max | 29.22 |
| 表 I, p.6 | MulRan，Neg. Pair（01 ↔ 04） | 对照（负样本） | CD Avg | 0.51 |
| 表 I, p.6 | MulRan，Neg. Pair（01 ↔ 04） | 对照（负样本） | CD Var | 1.67 |
| 表 I, p.6 | MulRan，Neg. Pair（01 ↔ 04） | 对照（负样本） | NP_CD>τ，τ=1 / 2 / 3 | 100 / 20 / 8 |
| 表 I, p.6 | MulRan，Neg. Pair（01 ↔ 04） | 对照（负样本） | NP_valid | 1386 |

> 读法：**Pos. Pair 的 CD 应显著小于 Neg. Pair**。论文以此为"回滚（rollback）得到的地图与真实地图一致"的间接证据——因为 3D 变化**没有点级 GT**（论文原文 p.6 §V-D："**Because there exist no point-wise ground-truth for the 3D changes over time**, we propose an implicit way to qualitatively evaluate our LD change detection performance via composing changes"）。**该表没有"其他方法"的对比列**，负样本是同一方法下的内部对照。

### Tab. II（p.6）—— 效率评估（Fig. 10 场景；注明 100 个 KF(01) 与近 200 个 KF(04)）

| 出处（表/图 + 页） | 数据集 / 序列 | 方法 | 指标 | 数值 |
| :--- | :--- | :--- | :--- | ---: |
| 表 II, p.6 | MulRan KAIST（100 KF 的 01 + 近 200 KF 的 04） | Baseline（保存整张快照） | Memory Usage（merged map） | 213.6 MB |
| 表 II, p.6 | 同上 | Baseline | Computation Time（between 04 and 01），**w/o HD removal** | 87.0 s |
| 表 II, p.6 | 同上 | Baseline | Computation Time，**w/ HD removal** | 160.0 s |
| **表 II, p.6** | **同上** | **Ours（LT-map, delta map chaining）** | **Memory Usage（merged map）** | **85.7 MB** |
| **表 II, p.6** | **同上** | **Ours（LT-map, delta map chaining）** | **Computation Time** | **9.8 s** |
| **表 II, p.6** | **同上** | **Ours vs Baseline** | **Efficiency ratio** | **省 60% 内存；快 8.9 (16.3) 倍** |

### 仅在正文、无表格的数字

| 出处（表/图 + 页） | 数据集 / 序列 | 方法 | 指标 | 数值 |
| :--- | :--- | :--- | :--- | ---: |
| 正文 p.5（§IV-C） | MulRan KAIST 01↔04（Fig. 5 场景） | Baseline（整图快照传输） | 点数 | **11 M points** |
| 正文 p.5（§IV-C） | 同上 | Ours（delta map） | 点数 | **0.47 M points** |
| 正文 p.5（§IV-C） | 同上 | Ours | delta map 占整图比例 | **仅 4.3%** |
| 正文 p.6（§V-D） | — | Ours | 变化复合（change composition）耗时 | **每关键帧约 0.05 s**（线性于关键帧数） |
| 正文 p.6（§V-D） | — | Ours vs Baseline | 内存节省 / 加速 | **省近 60%** 内存；**快 8.9 倍** |
| 正文 p.6（§V-D） | — | LT-removert 单次复杂度 | 复杂度 | **O(nm)**，n = 关键帧数、m = 地图点数 |

### 未找到的数字（明确记录搜索范围）

| 想要的数字 | 状态 | 搜索说明 |
| :--- | :--- | :--- |
| LT-SLAM 在 KAIST 01/02 上的 **translation error [%]** 与 **yaw error [deg]** 具体数值 | **未找到** | Fig. 8（p.5–6）只有曲线图。已用 `pdftotext -layout` 与 `pdftotext -raw` 提取第 5–6 页，**只得到坐标轴标签与刻度**（Translation error [%] 轴 0/20/40/60；Yaw error [deg] 轴 0/50/100/150；第三个子图轴 0/1/2/3，**其轴标签未能从文本层恢复**；横轴 `distance traveled (m)`，刻度 612.0 / 1225.0 / 1838.0 / 2450.0 / 3063.0；图例为 `LO` 与 `LT-SLAM`）。论文正文亦未复述这些数值，仅作定性陈述 |
| LT-SLAM 相对 LIO-SAM baseline 的误差下降百分比 | **未找到** | 同上；正文只有定性表述"errors are noticeably reduced" |

## 关键结论（论文自己声称的）

- **跨会话对齐无需良好初始对齐，且能压住各自漂移**：论文称"Two sessions with different origins successfully suppressed each other's drifts"，即 LT-SLAM 通过 inter-session anchor node-based loops **同时降低 intra-session 的平移与旋转（尤其 yaw）误差**，且"**no initial alignment of KAIST 02 being known**"（Fig. 8 标题与 p.5 §V-B）。**注意：这条结论的具体数值只存在于 Fig. 8 的曲线中，无法从 PDF 读出**。
- **delta map 在内存与算力上都有数量级收益**：Tab. II 中内存 **85.7 MB vs 213.6 MB（省约 60%）**，计算时间 **9.8 s vs 87.0 s（快 8.9 倍）/ 160.0 s（快 16.3 倍）**；配合正文"传输整图需 11 M 点，而 delta map 只需 0.47 M 点（4.3%）"（p.5 §IV-C）。
- **变化复合（change composition）在精度上可自洽**：Tab. I 中正样本对（01 ↔ 由 04 回滚得到的 Restored 01）的 **CD Avg = 0.29**，明显低于负样本对（01 ↔ 04）的 **0.51**，且不一致 patch 数更少（τ=1 时 **38 vs 100**）；论文据此主张"the restored KAIST 01 from 04 is well-matched to the real map of KAIST 01"，并称该机制等价于**地图回滚**，可在不保存全部快照的前提下恢复任意时刻的地图（p.6 §V-D）。
- **可自动解析 ephemeral（短时）物体**：从 PD/ND 图中可直接聚类分割出短时物体的点（Fig. 11），论文预期这能反过来作为 LT-removert 的先验（p.6 §V-E）。
- **定位为该方向的首个开源模块化框架**：论文称"to the best of our knowledge, LT-mapper is **the first open modular framework** that supports LiDAR-based lifelong mapping in complex urban sites"（p.1）。
- **可扩展性主张**：LT-removert 只需对**相邻会话**跑一次（O(nm)），此后任意两个会话之间的比较只需做**轻量的变化复合（约 0.05 s/关键帧）**，复杂度线性于关键帧数（p.6 §V-D）。

## 对我们的复现意味着什么

- **可复现的前提**：
  - **运行环境是 ROS 1**。官方 repo 明确 prerequisites：**ROS（tested with Melodic and Noetic）**，需 `ros-<distro>-navigation`、`robot-localization`、`robot-state-publisher`；**GTSAM** 走 PPA（`ppa:borglab/gtsam-release-4.0`，`libgtsam-dev libgtsam-unstable-dev`）；用 `catkin build ltslam removert` 编译。→ **ROS 1 已 EOL，与本机现有 ROS 2 环境不兼容**。
  - **官方提供 Docker 镜像，这是最稳路径**：repo 提供 `docker/build.sh` + `run.sh`，或直接 `docker pull dongjae0107/lt-mapper:latest`（外部核实，来自官方 README）。
  - **必须先造输入数据**：LT-mapper **不是**一个能从原始 rosbag 直接开跑的系统。官方流程是先用 **SC-LIO-SAM**（或其 saver 工具，SC-A-LOAM / FAST_LIO_SLAM 里也有）生成每个 session 的三件套：**关键帧点云 + 关键帧 Scan Context 描述子 + 位姿图文件（.g2o）**。这一步的工程量最大，且**换用不同的 LO 前端会直接改变后续所有结果**。
  - 运行顺序（论文 §III 给出 console 命令）：`./ltslam` → `./ltremovert` → `./ltmap`，各自的 yaml（`params_ltslam.yaml` / `params_ltremovert.yaml` / `params_ltmap.yaml`）在 repo 内，论文明确"refer the readers to our open source codes for the specific parameters"。
  - **无 GPU 需求**（纯 CPU：GTSAM iSAM2 + Scan Context + Removert + kd-tree）。
  - 数据许可 / 注册情况（已逐条核实官方页面）：
    - **LT-ParkingLot：免费、免注册**。官方 README 给出的下载链接 `https://bit.ly/ltmapper_parkinglot_data` **已实测 301 重定向到 Google Drive 文件夹**（无需登录），含 6 个 session、跨 3 天。
    - **MulRan（KAIST / DCC）：免费**，官方 Download 页 <https://sites.google.com/view/mulran-pr/download> 提供 Google Drive 链接。**但官方 NEWS 有一条关键提示：2023-05-09 更新了 MulRan 的 licence（条款在 Citation 页），需先确认**。该页为 Google Sites 动态内容，**未能以文本方式确认是否有额外表单，标为待核实**。
    - **⚠️ KAIST 04 可能不在常规下载包里**：论文 Fig. 1 图注明确写"**KAIST 04, recently released in extended sequences (February 2021)**"，而 MulRan 官网 NEWS 对应日期写着"**07/02/2021: We are constructing extended sequences for the same environments (if you are interested in it, please contact us)**"。→ **图 1 / 图 10 / Tab. I / Tab. II 用到的 KAIST 04 属于"扩展序列"，可能需要联系作者（irapkaist@gmail.com / paulgkim@kaist.ac.kr）才能获取**。这是复现 LT-mapper 变化检测部分（也就是论文的核心实验）的**最大单点风险**。
- **目标数字**（建议验收顺序）：
  1. **Tab. II 的效率数字**：delta map chaining 的 **内存 85.7 MB vs 快照 baseline 213.6 MB**，**计算 9.8 s vs 87.0 s（w/o HD removal）/ 160.0 s（w/ HD removal）**，即"**省 60% 内存、快 8.9 (16.3) 倍**"（Tab. II, p.6）。这是论文里**唯一结构清晰、口径明确**的一组数字，且强依赖于"关键帧数 = 100 (KAIST 01) / 近 200 (KAIST 04)"这一前提。
  2. **Tab. I 的 Chamfer distance**：正样本对 **CD Avg = 0.29 / Max = 6.41 / NP_valid = 1424（τ=1 时 38 个不一致 patch）**，负样本对 **CD Avg = 0.51 / Max = 29.22 / τ=1 时 100 个**（Tab. I, p.6）。**验收判据是"正样本显著优于负样本"，而不是绝对数值本身**。
  3. **delta map 压缩比**：**11 M → 0.47 M 点（4.3%）**（p.5 正文）。
  4. **LT-SLAM 的轨迹误差：无法给出数值目标**（Fig. 8 不可读），只能定性验收——"LT-SLAM 的 translation error 与 yaw error 曲线应明显低于 LIO-SAM 无回环 baseline"。
- **对不上的可能原因**：
  - **3D 变化没有点级 GT**（论文自述），只能靠 CD 这种间接指标；而 CD 结果**强依赖三个可调选择**：patch 切成 **5 m³**、patch 至少含 **25 点**才算有效（NP_valid）、τ 取 1/2/3。换任一设定都会让 0.29 / 0.51 这两个数字变样。
  - **时间与内存数字依赖机器和关键帧数**。论文只给了"100 KF(01) + 近 200 KF(04)"这一条注记，换序列长度或换 LO 前端（关键帧密度变了）都会漂移。
  - **整条链的前置环节由我们自己产生**：LT-mapper 吃的是 SC-LIO-SAM 输出的位姿图与 Scan Context 描述子。不同的 LO 前端 / 不同的 Scan Context 参数 → 不同的初始对齐误差 → 直接改变 LT-removert 的 PD/ND 结果与后续 CD。
  - **LT-SLAM 与 LT-removert / LT-map 的输入对齐方式不同**：LT-SLAM 用 anchor node + Scan Context 跨会话回环 + ICP（带 fitness score 的自适应协方差 Σz）+ radius search 精化，并用 robust back-end（[34],[35]）抗误回环。任一处换实现都会影响 Fig. 8 的曲线走向。
  - **弱 ND 保留（weak ND preservation）是论文的关键实现细节**：遮挡导致的假 ND 要"revert"回静态图，weak PD 要用于生成 live map 而只在 meta map 中剔除。若实现里漏掉这一步，变化检测结果会明显不同，但**它没有对应的数值指标**。
  - **论文自陈 LT-ParkingLot 的 6 个 session 原点各不相同、初始全局对齐未知**——这不是可省的前提，而是实验设计的一部分。
- **阻塞风险**：
  - **ROS 1（Melodic / Noetic）已 EOL**，与本机 ROS 2 环境冲突 → **建议直接走官方 Docker 镜像 `dongjae0107/lt-mapper:latest`**，这是最省事也最不容易走偏的路径。
  - **KAIST 04 属于 MulRan "extended sequences"，官方 NEWS 写明需联系作者** → 拿不到它，就**无法复现论文的核心变化检测实验（Fig. 1 / Fig. 6 / Fig. 10 / Tab. I / Tab. II 全部依赖 01↔04 这一对）**。必须先发邮件确认或找到替代会话对。备选：LT-ParkingLot（6 个 session 免费可得）可作为 Map update 与 delta map 的验证场景，但它**没有论文给出的 CD / 内存 / 时间参考值**。
  - **前置工具链成本**：SC-LIO-SAM（ROS 1）→ 关键帧点云 + SCD + g2o；需要处理 MulRan 的 rosbag 播放（官方推荐 <https://github.com/RPM-Robotics-Lab/file_player_mulran>）。这条链的任何一环失败都会让 LT-mapper 无输入可跑。
  - **MulRan licence 于 2023 年更新过**，采用前需读 Citation 页条款。
  - 论文与 repo 均**未申明运行硬件**，因此 Tab. II 的 9.8 s / 87.0 s 只能作为量级参考，不能逐位对齐。
