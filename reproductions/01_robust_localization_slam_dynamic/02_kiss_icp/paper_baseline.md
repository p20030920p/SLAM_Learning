# 01-02 · KISS-ICP — 论文报告值 Paper-reported baseline

| 项 Item | 内容 |
| :--- | :--- |
| 论文 | KISS-ICP: In Defense of Point-to-Point ICP – Simple, Accurate, and Robust Registration If Done the Right Way |
| Venue / 年 | IEEE Robotics and Automation Letters (RA-L), 2023（PDF 为 preprint 版，首页标注 *ACCEPTED DECEMBER, 2022*；Manuscript received 2022-09-14 / accepted 2022-12-27；arXiv:2209.15397v2, 2023-07-07。arXiv v2 未印卷期页码） |
| 本地 PDF | `Localise/01_task_books/materials/papers_pdf/057_KISS_ICP.pdf`（结果表在第 6–7 页） |
| 官方代码 | https://github.com/PRBonn/kiss-icp （论文 p.2 正文给出） |
| 任务 | 纯 point-to-point ICP 的 LiDAR 里程计：自适应对应阈值 + 鲁棒核 + 匀速模型去畸变 + 体素降采样；**不用 IMU、不用轮速计、不做回环、不做位姿图优化** |
| 数据集 | ① KITTI odometry（00–10 训练集 + 11–21 测试集）；② KITTI **raw**（仅去运动补偿的消融，对应 00–10 的那几条）；③ MulRan（KAIST / DCC / Riverside / Sejong，每条用 3 次重复运行的均值）；④ Newer College（NCD 01-short、NCD 02-long）；⑤ NCLT（2012-01-08） |
| 指标 | 论文原文口径：**relative translational error in %** 与 **relative rotational error**，均"using the KITTI [13] metrics"；MulRan 表另加 **ATE**（translation 单位 m、rotation 单位 rad）与 **Avg. tra. / Avg. rot.**；消融表（Tab. V）另报 **runtime（Hz）**。KITTI 官方定义（来自 KITTI 官方 benchmark 页，非本 PDF）：对长度 100–800 m 的全部子序列取平均，translation 以 % 计，rotation 以 deg/m 计 |
| 硬件 | **未找到**。检索关键词 CPU / GPU / Intel / NVIDIA / GHz / core / hardware / desktop / laptop / thread，PDF 全文无任何运行硬件描述。（外部佐证：KITTI 官方排行榜该条目记为 `1 core @ 4.5 Ghz (Python/C++)`、runtime 0.05 s —— 来源 <https://www.cvlibs.net/datasets/kitti/eval_odometry.php>，**不是论文里的数字**） |

> **读表须知**：下表"方法"列中 `**Ours**` 是论文自己方法（复现目标），其余为论文报告的对比方法。KISS-ICP 在 MulRan / NCD 上的对比值基本是自己重跑的；但 **Tab. IV 里 CT-ICP 的 NCLT 数值是直接引用原论文**（p.7 原文："We could not reproduce the results reported in CT-ICP [10] and therefore report the results given in the original paper [10] in Tab. IV."）。

## 论文报告的数字 Reported numbers

### Tab. I（p.6）—— 全部 7 个参数（同一套参数用于所有实验）

| 出处（表/图 + 页） | 数据集 / 序列 | 方法 | 指标 | 数值 |
| :--- | :--- | :--- | :--- | ---: |
| 表 I, p.6 | — | Ours | Initial threshold τ₀ | 2 m |
| 表 I, p.6 | — | Ours | Min. deviation threshold δ_min | 0.1 m |
| 表 I, p.6 | — | Ours | Max. points per voxel N_max | 20 |
| 表 I, p.6 | — | Ours | Voxel size map v | 0.01 r_max |
| 表 I, p.6 | — | Ours | Factor voxel size map merge α | 0.5 |
| 表 I, p.6 | — | Ours | Factor voxel size registration β | 1.5 |
| 表 I, p.6 | — | Ours | ICP convergence criterion γ | 10⁻⁴ |

补充：论文（p.6）说明对比方法的参数量为 **MULLS 107 个、SuMa 49 个、CT-ICP 30 个**；KISS-ICP 只有 7 个。`r_max` 被明确排除在"系统参数"之外（取决于具体传感器）。

### Tab. II（p.6）—— KITTI Benchmark，motion compensated 数据，平均相对平移误差 %

| 出处（表/图 + 页） | 数据集 / 序列 | 方法 | 指标 | 数值 |
| :--- | :--- | :--- | :--- | ---: |
| 表 II, p.6 | KITTI seq. 00–10（训练集，有 GT） | SuMa++（SLAM，含位姿图） | 相对平移误差 % | 0.70 |
| 表 II, p.6 | KITTI seq. 11–21（测试集，无公开 GT） | SuMa++ | 相对平移误差 % | 1.06 |
| 表 II, p.6 | KITTI seq. 00–10 | MULLS（SLAM） | 相对平移误差 % | 0.52 |
| 表 II, p.6 | KITTI seq. 11–21 | MULLS（SLAM） | 相对平移误差 % | 未报（"-"） |
| 表 II, p.6 | KITTI seq. 00–10 | CT-ICP（SLAM，含回环） | 相对平移误差 % | 0.53 |
| 表 II, p.6 | KITTI seq. 11–21 | CT-ICP（SLAM） | 相对平移误差 % | 0.59 |
| 表 II, p.6 | KITTI seq. 00–10 | IMLS-SLAM（SLAM） | 相对平移误差 % | 0.55 |
| 表 II, p.6 | KITTI seq. 11–21 | IMLS-SLAM（SLAM） | 相对平移误差 % | 0.69 |
| 表 II, p.6 | KITTI seq. 00–10 | MULLS（纯里程计） | 相对平移误差 % | 0.55 |
| 表 II, p.6 | KITTI seq. 11–21 | MULLS（纯里程计） | 相对平移误差 % | 0.65 |
| 表 II, p.6 | KITTI seq. 00–10 | F-LOAM（纯里程计） | 相对平移误差 % | 0.84 |
| 表 II, p.6 | KITTI seq. 11–21 | F-LOAM | 相对平移误差 % | 1.87 |
| 表 II, p.6 | KITTI seq. 00–10 | SuMa（纯里程计） | 相对平移误差 % | 0.80 |
| 表 II, p.6 | KITTI seq. 11–21 | SuMa | 相对平移误差 % | 1.39 |
| **表 II, p.6** | **KITTI seq. 00–10** | **Ours（KISS-ICP）** | **相对平移误差 %** | **0.50** |
| **表 II, p.6** | **KITTI seq. 11–21** | **Ours（KISS-ICP）** | **相对平移误差 %** | **0.61** |

表注原文：相对旋转误差被省略，官方数值见 KITTI 官网（<https://www.cvlibs.net/datasets/kitti/eval_odometry.php>）。本实验对 KISS-ICP 与 CT-ICP **关闭了运动补偿**，使用 KITTI 已补偿的扫描数据。

### Tab. III（p.7）—— MulRan 数据集（每条序列取 3 次运行的平均）

列顺序：Avg. tra. (%) / Avg. rot. / ATE tra. (m) / ATE rot. (rad)

| 出处（表/图 + 页） | 数据集 / 序列 | 方法 | 指标 | 数值 |
| :--- | :--- | :--- | :--- | ---: |
| 表 III, p.7 | MulRan KAIST | MULLS | Avg.tra. / Avg.rot. / ATE tra. / ATE rot. | 2.94 / 0.86 / 37.24 / 0.11 |
| 表 III, p.7 | MulRan KAIST | SuMa | 同上 | 5.59 / 1.73 / 43.61 / 0.14 |
| 表 III, p.7 | MulRan KAIST | F-LOAM | 同上 | 3.43 / 0.99 / 46.17 / 0.15 |
| **表 III, p.7** | **MulRan KAIST** | **Ours** | 同上 | **2.28 / 0.68 / 17.40 / 0.06** |
| 表 III, p.7 | MulRan DCC | MULLS | 同上 | 2.96 / 0.98 / 38.35 / 0.12 |
| 表 III, p.7 | MulRan DCC | SuMa | 同上 | 5.20 / 1.71 / 36.22 / 0.11 |
| 表 III, p.7 | MulRan DCC | F-LOAM | 同上 | 3.83 / 1.14 / 42.70 / 0.13 |
| **表 III, p.7** | **MulRan DCC** | **Ours** | 同上 | **2.34 / 0.64 / 15.16 / 0.05** |
| 表 III, p.7 | MulRan Riverside | MULLS | 同上 | 5.42 / 2.21 / 91.16 / 0.16 |
| 表 III, p.7 | MulRan Riverside | SuMa | 同上 | 13.86 / 2.13 / 227.24 / 0.38 |
| 表 III, p.7 | MulRan Riverside | F-LOAM | 同上 | 5.47 / 1.18 / 138.09 / 0.22 |
| **表 III, p.7** | **MulRan Riverside** | **Ours** | 同上 | **2.89 / 0.64 / 49.02 / 0.08** |
| 表 III, p.7 | MulRan Sejong* | MULLS | 同上 | 5.93 / 0.84 / 2151.00 / 0.49 |
| 表 III, p.7 | MulRan Sejong* | F-LOAM | 同上 | 7.87 / 1.20 / 3448.97 / 0.82 |
| **表 III, p.7** | **MulRan Sejong\*** | **Ours** | 同上 | **4.69 / 0.70 / 1369.54 / 0.33** |
| 表 III, p.7 | MulRan（Sejong） | SuMa | — | 未报（该序列 SuMa 无结果） |

\* 原文以 `Sejong*` 标注；论文正文另注：CT-ICP 不支持 MulRan，故未参与该表。

### Tab. IV（p.7）—— Newer College + NCLT，相对平移误差 %

| 出处（表/图 + 页） | 数据集 / 序列 | 方法 | 指标 | 数值 |
| :--- | :--- | :--- | :--- | ---: |
| 表 IV, p.7 | NCD 01-short | MULLS | 相对平移误差 % | 0.82 |
| 表 IV, p.7 | NCD 01-short | F-LOAM | 相对平移误差 % | 2.02 |
| 表 IV, p.7 | NCD 01-short | CT-ICP | 相对平移误差 % | 0.48 |
| **表 IV, p.7** | **NCD 01-short** | **Ours** | 相对平移误差 % | **0.51** |
| 表 IV, p.7 | NCD 02-long | MULLS | 相对平移误差 % | 1.23 |
| 表 IV, p.7 | NCD 02-long | F-LOAM | 相对平移误差 % | fails（失败） |
| 表 IV, p.7 | NCD 02-long | CT-ICP | 相对平移误差 % | 0.58 |
| **表 IV, p.7** | **NCD 02-long** | **Ours** | 相对平移误差 % | **0.96** |
| 表 IV, p.7 | NCLT 2012-01-8 | CT-ICP（**引用原论文，非重跑**） | 相对平移误差 % | 1.17 |
| **表 IV, p.7** | **NCLT 2012-01-8** | **Ours** | 相对平移误差 % | **1.27** |
| 表 IV, p.7 | NCLT 2012-01-8 | MULLS / F-LOAM | — | 未报（"-"） |

### Tab. V（p.7）—— KITTI-**raw**（未做运动补偿），相对平移/旋转误差 % + runtime

| 出处（表/图 + 页） | 数据集 / 序列 | 方法 | 指标 | 数值 |
| :--- | :--- | :--- | :--- | ---: |
| 表 V, p.7 | KITTI-raw（对应 00–10） | MULLS | Avg.tra. % / Avg.rot. / 频率 | 1.41 / 未报 / 12 Hz |
| 表 V, p.7 | KITTI-raw | IMLS-SLAM | 同上 | 0.71 / 未报 / 1 Hz |
| 表 V, p.7 | KITTI-raw | CT-ICP | 同上 | 0.55 / 未报 / 15 Hz |
| 表 V, p.7 | KITTI-raw | Ours **without deskewing** | 同上 | 0.91 / 0.27 / 51 Hz |
| 表 V, p.7 | KITTI-raw | Ours + Deskewing (**IMU**) | 同上 | 0.51 / 0.19 / 38 Hz |
| **表 V, p.7** | **KITTI-raw** | **Ours + Deskewing (CV，匀速模型)** | 同上 | **0.49 / 0.16 / 38 Hz** |

### Tab. VI（p.7）—— 自适应阈值 vs 固定阈值，相对平移误差 %

| 出处（表/图 + 页） | 数据集 / 序列 | 方法 | 指标 | 数值 |
| :--- | :--- | :--- | :--- | ---: |
| 表 VI, p.7 | KITTI seq. 00 | 固定阈值 0.3 / 0.5 / 1.0 / 2.0 m | 相对平移误差 % | 0.54 / 0.51 / 0.53 / 0.55 |
| **表 VI, p.7** | **KITTI seq. 00** | **Ours（自适应 τ_t = 3σ_t）** | 相对平移误差 % | **0.51** |
| 表 VI, p.7 | KITTI seq. 04 | 固定阈值 0.3 / 0.5 / 1.0 / 2.0 m | 相对平移误差 % | 0.39 / 0.41 / 0.37 / 0.39 |
| **表 VI, p.7** | **KITTI seq. 04** | **Ours（自适应）** | 相对平移误差 % | **0.36** |
| 表 VI, p.7 | KITTI avg. seq. 00–10 | 固定阈值 0.3 / 0.5 / 1.0 / 2.0 m | 相对平移误差 % | 0.53 / 0.51 / 0.51 / 0.53 |
| **表 VI, p.7** | **KITTI avg. seq. 00–10** | **Ours（自适应）** | 相对平移误差 % | **0.50** |

### 仅在正文、无表格的消融数字（p.7 §IV-D2 末）

| 出处（表/图 + 页） | 数据集 / 序列 | 方法 | 指标 | 数值 |
| :--- | :--- | :--- | :--- | ---: |
| 正文 p.7（无表） | KITTI（序列平均） | Ours **不用鲁棒核** | 平移误差 % / 旋转误差 % | 0.67 / 0.25 |

## 关键结论（论文自己声称的）

- **KITTI 上"以简胜繁"**：Tab. II 中 Ours 在 00–10 上拿到 **0.50%**，优于所有纯里程计方法（MULLS 0.55、SuMa 0.80、F-LOAM 0.84）以及含位姿图优化的 SuMa++（0.70）与 IMLS-SLAM（0.55），仅落后完整 SLAM 系统 CT-ICP（0.53）0.03 个百分点；11–21 上 **0.61%** 略逊于 CT-ICP 的 0.59。论文自称"在开源方法中排第 2（仅次于 CT-ICP），在全部提交中排第 9"（p.6）。
- **跨数据集、跨传感器、同一套参数**：MulRan 上论文称"Our method outperforms all state-of-the-art approaches by a large margin in both relative and absolute error"（p.6），如 Riverside ATE tra. **49.02 m** vs MULLS 91.16 m / F-LOAM 138.09 m / SuMa 227.24 m。
- **匀速模型去畸变足够好**：Tab. V 中 CV 去畸变 **0.49% / 0.16**（38 Hz）甚至略优于 IMU 去畸变 0.51% / 0.19；而不去畸变为 0.91% / 0.27。论文据此主张"更复杂的补偿技术对多数机器人里程计而言并非必要"（p.7）。
- **自适应阈值免调参**：Tab. VI 中 seq. 00 最优固定阈值是 0.5 m、seq. 04 是 1.0 m（即固定阈值必须按运动剖面调），而自适应 τ_t = 3σ_t 在 00–10 平均取得最好的 **0.50%**（p.7）。
- **快于传感器帧率**：Tab. V 报 51 Hz（不去畸变）/ 38 Hz（去畸变），论文称"operates faster than the sensor frame rate in all presented datasets"。
- **论文自己给出的负面结论**：NCLT 结果"should be taken with a grain of salt"，原因是 GT 位姿有误、存在丢帧，论文明确 **discourage** 用 NCLT 评估里程计（p.6）。

## 对我们的复现意味着什么

- **可复现的前提**：
  - 代码：`PRBonn/kiss-icp`（论文承诺"precisely follows the description of this paper"）。官方 README（外部核实）给出 `pip install kiss-icp`；ROS 2 有官方 wrapper，**ROS 1 自 v0.3.0 起已弃用**。无 GPU、无深度学习依赖。
  - 数据许可 / 注册情况（已逐条核实官方页面）：
    - **KITTI odometry：需要注册**。全部下载链接都指向 <https://www.cvlibs.net/datasets/kitti/user_login.php>。体积：grayscale 22 GB / color 65 GB / velodyne 80 GB / calib 1 MB / GT poses 4 MB。**并且 KITTI 官方政策规定新用户注册时须说明身份、工作内容与目标发表 venue**，6 个月内无关联论文的条目会被删除。
    - **KITTI raw：同样需要注册**（同一入口）。
    - **MulRan：免费**。官方 Download 页提供 Google Drive 链接（<https://sites.google.com/view/mulran-pr/download>）。注意官方 NEWS：**2023-05-09 更新了 MulRan 的 licence，需到 Citation 页确认条款**。（该页为 Google Sites 动态内容，未能以文本方式逐条确认是否有额外表单，标为**待核实**。）
    - **Newer College：需填表**。官方 Download 页写着"If you have any problems with the form please email us"，即下载走表单；licence 为 **CC BY-NC-SA 4.0，仅限非商业学术用途**（<https://ori-drs.github.io/newer-college-dataset/download/>）。
    - **NCLT：免费**，官网 <http://robots.engin.umich.edu/nclt/> 有独立的 License 与 Download 页。
  - 论文参数：严格照抄 Tab. I 的 7 个参数（p.6）。`r_max` 需按传感器设定。
- **目标数字**（按可行性排序）：
  1. **KITTI seq. 00–10 平均相对平移误差 = 0.50%**（Tab. II, p.6）——本地可算，因为 00–10 有公开 GT。配套单序列参照 **seq. 04 = 0.36%**、**seq. 00 = 0.51%**（Tab. VI, p.7）。
  2. **KITTI seq. 11–21 = 0.61%** ——**本地不可验证**，必须提交 KITTI 官方 server（见下"阻塞风险"）。
  3. 若 KITTI 拿不到退路：**NCD 01-short = 0.51%**（Tab. IV, p.7）或 **MulRan KAIST = 2.28% / ATE 17.40 m**（Tab. III, p.7）。
  4. 工程性指标：Tab. V 的 **38 Hz（CV 去畸变）** 与 **51 Hz（不去畸变）**。
- **对不上的可能原因**：
  - Tab. II 用的是 KITTI **已做运动补偿**的扫描，并且**关闭**了 KISS-ICP 自身的运动补偿；若用 raw 数据（Tab. V 口径）目标值应改为 0.49%（CV）。两条口径混用是最容易出错的地方。
  - 评估脚本差异：论文用 KITTI [13] 官方指标（子序列 100–800 m 取平均）。自写 RPE 脚本（如取固定帧间隔）会系统性地给出不同数值。
  - **自适应阈值是有状态的**（σ_t 由历史 δ(ΔT_i) 在线估计），轨迹起点、帧序、是否跳帧都会引入小差异；这解释了为什么同一序列的 0.51 与其三处复现（Tab. VI）一致、但与 0.50 的 00–10 平均并不逐条相等。
  - 鲁棒核是必要的：去掉核后从 0.50% 退化到 **0.67% / 0.25%**（p.7 正文），若实现里漏掉 Geman-McClure 核，误差会明显偏大。
  - 论文自己承认 NCLT 的 GT 有问题，**不要把 1.27% 当硬指标**；NCD 02-long 的 0.96% vs CT-ICP 0.58% 的差距论文归因于 CT-ICP 的 loop closing（KISS-ICP 无回环），这条差距是结构性的、不可通过调参消除。
- **阻塞风险**：
  - **KITTI 注册是用户级人工步骤**，且 **seq. 11–21 没有公开 GT**：Tab. II 的 0.61% 只能通过向 KITTI benchmark server 提交结果得到，而官方政策限制"仅接受有显著新颖性、将发表于同行评审论文的提交；学生项目/已有算法的微小改动不允许提交"。→ **0.61% 这一格实际上不可本地复现**，建议把验收标准定为 00–10 的 0.50%。
  - **体积**：KITTI velodyne 80 GB（若要跑 00–10 也建议整包下载）。
  - Newer College 需填表 + 非商业条款；MulRan 的 licence 2023 年更新过，需先读条款。
  - 论文未给运行硬件，因此 runtime（38 / 51 Hz）只能作为量级参考，不能逐位对齐。
