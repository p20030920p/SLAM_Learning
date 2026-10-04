# 01-08 · NGD-SLAM — 论文报告值 Paper-reported baseline

| 项 Item | 内容 |
| :--- | :--- |
| 论文 | NGD-SLAM: Towards Real-Time Dynamic SLAM without GPU |
| Venue / 年 | IEEE/RSJ International Conference on Intelligent Robots and Systems (IROS) **2025**（PDF 首页页眉：`© 2025 IEEE – Accepted to IEEE//RSJ International Conference on Intelligent Robots and Systems (IROS) 2025`；arXiv:2405.07392v5。官方 repo 补充：pp. 3467–3473, DOI 10.1109/IROS60139.2025.11246202 —— **页码与 DOI 来自 repo，不在本 PDF 内**） |
| 本地 PDF | `Localise/01_task_books/materials/papers_pdf/007_NGD_SLAM.pdf`（结果表在第 5–6 页：Tab. I / Tab. II @p.5；Tab. III / Tab. IV / Tab. V @p.6） |
| 官方代码 | https://github.com/yuhaozhang7/NGD-SLAM （论文摘要末尾给出"Since most existing dynamic SLAM systems are not open-source, we make our code publicly available at: https://github.com/yuhaozhang7/NGD-SLAM"） |
| 任务 | **纯 CPU 实时**的动态环境视觉 SLAM，基于 **ORB-SLAM3**：① mask propagation 机制把相机跟踪与深度学习分割**解耦**（用上一帧的 mask 预测当前帧，不等 YOLO）；② ORB 特征 + 光流的**混合跟踪策略**（非关键帧用 LK 光流、关键帧用 ORB），选择性分配算力 |
| 数据集 | ① TUM RGB-D 的**全部 highly dynamic 序列**：`f3/w xyz`、`f3/w rpy`、`f3/w half`、`f3/w static`（即 `rgbd_dataset_freiburg3_walking_{xyz,rpy,halfsphere,static}`，两数据集相机均 30 Hz）；② BONN Dynamic 数据集的 9 条序列：`crowd`、`crowd2`、`crowd3`、`mov no box`、`mov no box2`、`person track`、`person track2`、`synchronous`、`synchronous2` |
| 指标 | 论文原文定义：**ATE (Absolute Trajectory Error)** 与 **RPE (Relative Pose Error)** [37]，**RPE 的测量间隔设为 1 秒**（TUM 与 BONN 均为 30 帧）。注意单位：**ATE (m)**、**RPE translation (m/s)**、**RPE rotation (°/s)** —— RPE 报的是**速率**，不是位移/角度本身。效率指标：**每帧跟踪时间（ms）**；以及 **Ratio = 该系统跟踪时间 / ORB-SLAM2 跟踪时间**（ORB-SLAM2 是静态环境的强基线、作为共同基座） |
| 硬件 | **laptop, AMD Ryzen 7 4800H CPU + NVIDIA GeForce RTX 2060 GPU**，论文明确 **"GPU is not used for our method"**（p.5 §IV-A）。ORB-SLAM2 在其设备上**平均跟踪时间约 20 ms**，因此**论文定义 Ratio < 1.65 即视为实时（30 FPS）**（p.5 §IV-C）。所有结果**处理了序列中的全部帧**，即使对非实时方法也如此 |

> **读表须知**：`Ours*` 是本文方法（复现目标），其余为对比方法。Tab. I 中带 `*` 的方法表示"real-time or near real-time"（TRS-SLAM、CFP-SLAM、Ours），原文还用红色标"全部算法中最好"、蓝色标"全部（近）实时算法中最好"——**这些颜色标记无法从 PDF 文本中读出**，下表只保证数值准确，不标注颜色归属。论文说明对比数字**均取自各自原论文**（"the information is obtained from their source paper"），**不是作者重跑的**。

## 论文报告的数字 Reported numbers

### Tab. I（p.5）—— TUM Highly Dynamic 序列：ATE (m) / RPE (m/s) / RPE (°/s)

| 出处（表/图 + 页） | 数据集 / 序列 | 方法 | 指标 | 数值 |
| :--- | :--- | :--- | :--- | ---: |
| 表 I, p.5 | TUM f3/w xyz | DynaSLAM | ATE / RPE_t / RPE_r | 0.015 / 0.021 / 0.452 |
| 表 I, p.5 | TUM f3/w rpy | DynaSLAM | 同上 | 0.036 / 0.045 / 0.902 |
| 表 I, p.5 | TUM f3/w half | DynaSLAM | 同上 | 0.027 / 0.028 / 0.737 |
| 表 I, p.5 | TUM f3/w static | DynaSLAM | 同上 | 0.007 / 0.008 / 0.258 |
| 表 I, p.5 | TUM f3/w xyz | DS-SLAM | 同上 | 0.025 / 0.033 / 0.826 |
| 表 I, p.5 | TUM f3/w rpy | DS-SLAM | 同上 | 0.444 / 0.150 / 3.004 |
| 表 I, p.5 | TUM f3/w half | DS-SLAM | 同上 | 0.030 / 0.030 / 0.814 |
| 表 I, p.5 | TUM f3/w static | DS-SLAM | 同上 | 0.008 / 0.010 / 0.269 |
| 表 I, p.5 | TUM f3/w xyz | RDS-SLAM | 同上 | 0.057 / 0.042 / 0.922 |
| 表 I, p.5 | TUM f3/w rpy | RDS-SLAM | 同上 | 0.160 / 0.132 / 13.169 |
| 表 I, p.5 | TUM f3/w half | RDS-SLAM | 同上 | 0.081 / 0.048 / 1.883 |
| 表 I, p.5 | TUM f3/w static | RDS-SLAM | 同上 | 0.008 / 0.022 / 0.494 |
| 表 I, p.5 | TUM f3/w xyz | TRS-SLAM* | 同上 | 0.019 / 0.023 / 0.636 |
| 表 I, p.5 | TUM f3/w rpy | TRS-SLAM* | 同上 | 0.037 / 0.047 / 1.058 |
| 表 I, p.5 | TUM f3/w half | TRS-SLAM* | 同上 | 0.029 / 0.042 / 0.965 |
| 表 I, p.5 | TUM f3/w static | TRS-SLAM* | 同上 | 0.011 / 0.011 / 0.287 |
| 表 I, p.5 | TUM f3/w xyz | CFP-SLAM* | 同上 | 0.015 / 0.019 / 0.620 |
| 表 I, p.5 | TUM f3/w rpy | CFP-SLAM* | 同上 | 0.041 / 0.054 / 1.052 |
| 表 I, p.5 | TUM f3/w half | CFP-SLAM* | 同上 | 0.023 / 0.027 / 0.785 |
| 表 I, p.5 | TUM f3/w static | CFP-SLAM* | 同上 | 0.007 / 0.009 / 0.254 |
| 表 I, p.5 | TUM f3/w xyz | USD-SLAM | 同上 | 0.035 / – / – |
| 表 I, p.5 | TUM f3/w rpy | USD-SLAM | 同上 | 0.035 / – / – |
| 表 I, p.5 | TUM f3/w half | USD-SLAM | 同上 | 0.020 / – / – |
| 表 I, p.5 | TUM f3/w static | USD-SLAM | 同上 | – （未报） |
| 表 I, p.5 | TUM f3/w xyz | DFS-SLAM | 同上 | 0.013 / – / – |
| 表 I, p.5 | TUM f3/w rpy | DFS-SLAM | 同上 | 0.027 / – / – |
| 表 I, p.5 | TUM f3/w half | DFS-SLAM | 同上 | 0.018 / – / – |
| 表 I, p.5 | TUM f3/w static | DFS-SLAM | 同上 | 0.006 / – / – |
| **表 I, p.5** | **TUM f3/w xyz** | **Ours\*** | **ATE / RPE_t / RPE_r** | **0.015 / 0.020 / 0.470** |
| **表 I, p.5** | **TUM f3/w rpy** | **Ours\*** | 同上 | **0.034 / 0.044 / 0.889** |
| **表 I, p.5** | **TUM f3/w half** | **Ours\*** | 同上 | **0.024 / 0.025 / 0.695** |
| **表 I, p.5** | **TUM f3/w static** | **Ours\*** | 同上 | **0.007 / 0.009 / 0.262** |

### Tab. II（p.5）—— BONN 数据集：ATE (m)

| 出处（表/图 + 页） | 数据集 / 序列 | 方法 | 指标 | 数值 |
| :--- | :--- | :--- | :--- | ---: |
| 表 II, p.5 | BONN crowd | DynaSLAM / ReFusion / ACEFusion* / USD | ATE (m) | 0.016 / 0.204 / 0.016 / – |
| **表 II, p.5** | **BONN crowd** | **Ours\*** | **ATE (m)** | **0.024** |
| 表 II, p.5 | BONN crowd2 | DynaSLAM / ReFusion / ACEFusion* / USD | ATE (m) | 0.031 / 0.155 / 0.027 / 0.028 |
| **表 II, p.5** | **BONN crowd2** | **Ours\*** | **ATE (m)** | **0.025** |
| 表 II, p.5 | BONN crowd3 | DynaSLAM / ReFusion / ACEFusion* / USD | ATE (m) | 0.038 / 0.137 / 0.023 / 0.026 |
| **表 II, p.5** | **BONN crowd3** | **Ours\*** | **ATE (m)** | **0.033** |
| 表 II, p.5 | BONN mov no box | DynaSLAM / ReFusion / ACEFusion* / USD | ATE (m) | 0.232 / 0.071 / 0.070 / – |
| **表 II, p.5** | **BONN mov no box** | **Ours\*** | **ATE (m)** | **0.016** |
| 表 II, p.5 | BONN mov no box2 | DynaSLAM / ReFusion / ACEFusion* / USD | ATE (m) | 0.039 / 0.179 / 0.029 / 0.178 |
| **表 II, p.5** | **BONN mov no box2** | **Ours\*** | **ATE (m)** | **0.036** |
| 表 II, p.5 | BONN person track | DynaSLAM / ReFusion / ACEFusion* / USD | ATE (m) | 0.061 / 0.289 / 0.070 / 0.028 |
| **表 II, p.5** | **BONN person track** | **Ours\*** | **ATE (m)** | **0.046** |
| 表 II, p.5 | BONN person track2 | DynaSLAM / ReFusion / ACEFusion* / USD | ATE (m) | 0.078 / 0.463 / 0.071 / 0.041 |
| **表 II, p.5** | **BONN person track2** | **Ours\*** | **ATE (m)** | **0.062** |
| 表 II, p.5 | BONN synchronous | DynaSLAM / ReFusion / ACEFusion* / USD | ATE (m) | 0.015 / 0.441 / 0.014 / – |
| **表 II, p.5** | **BONN synchronous** | **Ours\*** | **ATE (m)** | **0.028** |
| 表 II, p.5 | BONN synchronous2 | DynaSLAM / ReFusion / ACEFusion* / USD | ATE (m) | 0.009 / 0.022 / 0.010 / – |
| **表 II, p.5** | **BONN synchronous2** | **Ours\*** | **ATE (m)** | **0.009** |

### Tab. III（p.6）—— 跟踪时间比（Tracking Time Ratio，分母为 ORB-SLAM2）

| 出处（表/图 + 页） | 数据集 / 序列 | 方法 | 指标 | 数值 |
| :--- | :--- | :--- | :--- | ---: |
| 表 III, p.6 | TUM（静态环境基线） | ORB-SLAM2 | Ratio / 实时 / 设备 | 1.00 / ✓ / CPU |
| 表 III, p.6 | TUM | ORB-SLAM3 | Ratio / 实时 / 设备 | 0.98 / ✓ / CPU |
| 表 III, p.6 | TUM | DynaSLAM | Ratio / 实时 / 设备 | 15.94 / ✗ / CPU + GPU |
| 表 III, p.6 | TUM | DS-SLAM | Ratio / 实时 / 设备 | 2.07 / ✗ / CPU + GPU |
| 表 III, p.6 | TUM | RDS-SLAM | Ratio / 实时 / 设备 | 2.00 / ✗ / CPU + GPU |
| 表 III, p.6 | TUM | TRS-SLAM | Ratio / 实时 / 设备 | 1.06 / ✓ / CPU + GPU |
| 表 III, p.6 | TUM | CFP-SLAM | Ratio / 实时 / 设备 | 1.72 / ✓ (near) / CPU + GPU |
| 表 III, p.6 | TUM | USD-SLAM | Ratio / 实时 / 设备 | 2.77 / ✗ / CPU + GPU |
| 表 III, p.6 | TUM | DFS-SLAM | Ratio / 实时 / 设备 | 3.13 / ✗ / CPU + GPU |
| **表 III, p.6** | **TUM** | **NGD-SLAM（Ours）** | **Ratio / 实时 / 设备** | **0.84 / ✓ / CPU** |

### Tab. IV（p.6）—— 关键帧平均跟踪时间（ms）

| 出处（表/图 + 页） | 数据集 / 序列 | 方法 | 指标 | 数值 |
| :--- | :--- | :--- | :--- | ---: |
| 表 IV, p.6 | TUM | Ours | MP（Mask Propagation） | 7.92 ms |
| 表 IV, p.6 | TUM | Ours | OF Tracking（光流跟踪） | 3.04 ms |
| 表 IV, p.6 | TUM | Ours | ORB Tracking | 19.73 ms |
| **表 IV, p.6** | **TUM** | **Ours** | **Total（每个关键帧）** | **30.69 ms** |

### Tab. V（p.6）—— 消融：不同配置的 ATE RMSE (m)

| 出处（表/图 + 页） | 数据集 / 序列 | 方法 | 指标 | 数值 |
| :--- | :--- | :--- | :--- | ---: |
| 表 V, p.6 | TUM f3/w xyz | ORB3（纯 ORB-SLAM3 基座） | ATE (m) | 0.390 |
| 表 V, p.6 | TUM f3/w xyz | +YOLO | ATE (m) | 0.014 |
| 表 V, p.6 | TUM f3/w xyz | +MP | ATE (m) | 0.014 |
| **表 V, p.6** | **TUM f3/w xyz** | **+MP+HS（完整系统）** | **ATE (m)** | **0.015** |
| 表 V, p.6 | TUM f3/w xyz | 提升幅度 | — | 96% |
| 表 V, p.6 | TUM f3/w rpy | ORB3 / +YOLO / +MP / +MP+HS | ATE (m) | 0.639 / 0.041 / 0.037 / 0.034 |
| 表 V, p.6 | TUM f3/w rpy | 提升幅度 | — | 95% |
| 表 V, p.6 | TUM f3/w half | ORB3 / +YOLO / +MP / +MP+HS | ATE (m) | 0.431 / 0.023 / 0.028 / 0.024 |
| 表 V, p.6 | TUM f3/w half | 提升幅度 | — | 94% |
| 表 V, p.6 | TUM f3/w static | ORB3 / +YOLO / +MP / +MP+HS | ATE (m) | 0.096 / 0.007 / 0.007 / 0.007 |
| 表 V, p.6 | TUM f3/w static | 提升幅度 | — | 93% |
| 表 V, p.6 | TUM | Time / Frame（ORB3 → +YOLO → +MP → +MP+HS） | ms | 20 / 54 / 28 / 17 |
| 表 V, p.6 | TUM | Time / Frame 提升幅度 | — | 15% |

表注：MP = Mask Propagation，HS = Hybrid Tracking Strategy。

### 仅在正文、无表格的数字

| 出处（表/图 + 页） | 数据集 / 序列 | 方法 | 指标 | 数值 |
| :--- | :--- | :--- | :--- | ---: |
| 正文 p.5（§IV-D） | TUM + BONN | Ours | **平均每帧处理时间** | **16.72 ms（≈ 60 FPS）** |
| 正文 p.5（§IV-C） | — | ORB-SLAM2（其设备上） | 平均跟踪时间 | **约 20 ms**；据此 **Ratio < 1.65 视为实时（30 FPS）** |
| 正文 p.6（§IV-D） | — | YOLO 检测 | 每帧耗时 | **30–40 ms**（**不计入跟踪时间**，因跟踪线程与语义线程以不同频率并发运行） |
| 正文 p.6（§IV-D） | — | Ours 关键帧跟踪 | 合计 | 落在 **33.3 ms（30 FPS）** 以内，仍满足 TUM/BONN 的实时判据 |

## 关键结论（论文自己声称的）

- **纯 CPU 也能实时**：Tab. III 中 NGD-SLAM 的 **Ratio = 0.84、Real-Time ✓、Device = CPU**，是表中唯一在 CPU 上达到实时的动态 SLAM 系统（TRS-SLAM Ratio 1.06 虽标 ✓ 但设备为 CPU + GPU）；配合正文 **16.72 ms/帧（≈ 60 FPS）** 与 Tab. IV 的 **30.69 ms/关键帧**。论文原文："our system achieves real-time performance with only a CPU while maintaining accuracy comparable to state-of-the-art method"（p.5 §IV-C）。
- **精度接近 SOTA，实时方法中最好**：Tab. I 中 Ours 的 ATE 为 0.015 / 0.034 / 0.024 / 0.007 m，与 DynaSLAM（0.015 / 0.036 / 0.027 / 0.007）几乎持平；论文承认 DFS-SLAM 精度更高（0.013 / 0.027 / 0.018 / 0.006）但"due to its extensive extra computations"，且"when real-time performance is considered, it achieves the highest accuracy overall"（p.5 §IV-B）。
- **BONN 上跨序列优于多数方法**：Tab. II 中 Ours 在 `mov no box` 取得 **0.016 m**（DynaSLAM 0.232、ReFusion 0.071、ACEFusion 0.070）、`crowd2` 0.025 m、`person track` 0.046 m、`synchronous2` **0.009 m**；论文称"our system outperforms other methods across several sequences"，并强调对"人搬着静态物体走动"这类场景也有处理能力（得益于深度分割 + 连通域算法）。
- **消融证明两处贡献都必要**：Tab. V 中 ORB-SLAM3 基座在动态场景彻底失败（f3/w xyz **0.390 m**、rpy **0.639 m**），仅加 YOLO mask 就把 ATE 降到 0.014 m 但**每帧耗时从 20 ms 涨到 54 ms**（不再实时）；只加 mask propagation 把耗时压回 28 ms；再加混合跟踪策略后到 **17 ms**，同时 ATE 仍在 0.015 m（p.6 §IV-E）。
- **实时性的评测口径主张**：论文批评现有工作"用全部帧评估即使系统本身不实时"，指出低帧率会导致延迟累积，应当主动丢帧匹配输入帧率；并以 DynaSLAM 为例展示了降帧率后 f3/w rpy 这类快速旋转序列性能下降明显（p.6 §IV-F, Fig. 6）。

## 对我们的复现意味着什么

- **可复现的前提**：
  - **无 GPU 需求（本机适配）**。官方 repo 说明（外部核实，<https://github.com/yuhaozhang7/NGD-SLAM>）：测试于 **Ubuntu 20.04 / 22.04**；依赖 C++11、**Pangolin**、**OpenCV ≥ 4.4**、**Eigen ≥ 3.1.0**；**YOLO 用 YOLO-fastest 的 C++ 版，模型配置与预训练权重已内置在 `Thirdparty/` 文件夹并用 OpenCV DNN 加载**（即 **OpenCV DNN CPU 推理，不需要 CUDA**）；DBoW2 与 g2o 的改动版也已内置；轨迹对齐需要 **Python + numpy**。**不依赖 ROS**。
  - 构建：`./build.sh`。
  - 数据许可 / 注册（已逐条核实官方页面）：
    - **TUM RGB-D：免费、免注册**，官方下载页直接给出每条序列的 `.tgz` 链接（<https://cvg.cit.tum.de/data/datasets/rgbd-dataset/download>），单条 **0.2–2.8 GB**（页面列出 25 个 tgz 的体积，未逐条对应到序列名）。repo 给出的运行示例命令即 `rgbd_dataset_freiburg3_walking_xyz` + `Examples/RGB-D/associations/fr3_walk_xyz.txt`。
    - **BONN Dynamic：免费、免注册**，每条序列一个 `.zip` 直链（<https://www.ipb.uni-bonn.de/data/rgbd-dynamic-dataset/index.html>）。**论文用到的 9 条合计约 3.5 GB**（crowd 515.9 MB + crowd2 498.4 MB + crowd3 482.0 MB + moving_nonobstructing_box 436.2 MB + moving_nonobstructing_box2 513.1 MB + person_tracking 329.5 MB + person_tracking2 324.3 MB + synchronous 182.8 MB + synchronous2 203.5 MB）。**全量 16.4 GB**（若含 static 5.8 GB / static_close_far 1.0 GB / kidnapping 等未使用序列）。数据集格式与 TUM RGB-D 一致，**可直接复用 TUM 的评估工具**（官方页面明示）。
    - **序列名映射（论文缩写 → 官方文件名，需要小心）**：`crowd`→`rgbd_bonn_crowd`；`crowd2`→`rgbd_bonn_crowd2`；`crowd3`→`rgbd_bonn_crowd3`；`mov no box`→`rgbd_bonn_moving_nonobstructing_box`；`mov no box2`→`rgbd_bonn_moving_nonobstructing_box2`；`person track`→`rgbd_bonn_person_tracking`；`person track2`→`rgbd_bonn_person_tracking2`；`synchronous`→`rgbd_bonn_synchronous`；`synchronous2`→`rgbd_bonn_synchronous2`。
- **目标数字**（建议验收顺序）：
  1. **TUM `f3/w xyz`：ATE = 0.015 m，RPE_t = 0.020 m/s，RPE_r = 0.470 °/s**（Tab. I, p.5）——最常被引用、最容易对上的单一数字。
  2. **TUM `f3/w rpy` ATE = 0.034 m**（Tab. I, p.5）——这是最能体现混合跟踪策略价值的序列（论文专门用它讨论旋转场景）。
  3. **BONN `mov no box` ATE = 0.016 m**（Tab. II, p.5）——论文相对 DynaSLAM（0.232）优势最大的一条。
  4. **实时性：每帧 16.72 ms（≈ 60 FPS）、Ratio = 0.84、关键帧 30.69 ms**（正文 p.5 + Tab. III/IV, p.6）。
  5. 消融自检：**关掉混合跟踪策略后每帧应从 17 ms 涨到 28 ms 左右**（Tab. V, p.6）——这是判断实现是否真的按论文做的快速试纸。
- **对不上的可能原因**：
  - **RPE 的单位陷阱**：本论文报的是 **m/s 与 °/s**（速率），而 TUM 官方 `evaluate_ate.py` / `evaluate_rpe.py` 默认输出 **m 与 °**。若把 0.020 当成 m 去对，会差约 30 倍（RPE 间隔 1 s = 30 帧）。**必须先确认评估脚本是否按"1 秒间隔 + 除以时间"实现**。
  - **YOLO 在独立线程以较低频率运行**，论文明确"it is not factored into this tracking time since the tracking and semantic threads operate concurrently at different frequencies"（p.6）。→ mask propagation 的效果**对线程调度与 CPU 负载敏感**，同一台机器上跑分也可能波动；纯 CPU 上并发 8 核与 16 核的表现会不同。
  - **论文只报了 TUM 的 4 条 highly dynamic 序列和 BONN 的 9 条**；TUM 的其他动态序列（如 `fr3/sitting_*`、`fr2/desk_*`）**没有参考值**，不要拿它们做验收。
  - **Tab. I 的对比方法数字全部引自各自原论文**（不是重跑），且部分方法已非开源或在别的设备上测过；论文自己也说"a relative fair comparison of efficiency is ensured by displaying a ratio"，即**绝对值不可比，只有 Ratio 可比**。我们的 baseline 对比应尽量同样只用 Ratio。
  - **BONN 序列名缩写容易对错**（见上映射），用错序列会得到完全不同的 ATE。
  - 论文自陈局限：mask propagation **依赖 RGB-D 的深度**（单目/双目需换成分割模型）；**不处理检测类别之外的动态实例**，也不处理"可移动的静态物体"（p.6 §VI）。
  - 换机器后 **16.72 ms / 60 FPS 不应作为硬指标**（论文用的是 Ryzen 7 4800H）；**Ratio = 0.84 更稳健**，因为它对 ORB-SLAM2 做了归一化。
- **阻塞风险**：
  - **这是四篇里阻塞最低的一篇**：无 GPU、无 ROS、数据全部免费免注册、深度学习权重随仓库附带。
  - 唯一实质成本是**下载量**：BONN 论文用到的 9 条约 3.5 GB（全量 16.4 GB），TUM 4 条 highly dynamic 序列若干 GB。
  - 次要风险：OpenCV 必须 ≥ 4.4（Ubuntu 20.04 自带版本偏低，需自行编译或装新版）；Pangolin 需从源码编译。repo 未在 README 中声明 licence（**未标注**），且库内含 ORB-SLAM3 / DBoW2 / g2o 的改动版，引用时需一并遵守上游条款 —— **建议在采用前确认 licence**。
