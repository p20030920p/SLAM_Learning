# IR-MCL

[English](ir-mcl.md) | 中文

**波恩 IPBLab 室内实验室，官方公开的唯一一个定位序列（1543 帧扫描，1041 线束下采样到 32 线）。** 神经占据场（NOF）为每个粒子渲染一条合成扫描，渲染距离与真实距离之差即为粒子滤波的观测模型。

## 原文数据集与场景

| 评估 | 数据／场景 |
| --- | --- |
| 全局定位／位姿跟踪 | 波恩IPBLab办公室、走廊、厨房；Kuka YouBot与Hokuyo UTM-30LX二维激光。31,608帧建图序列训练占据场，另有五条短序列测试定位。 |
| 观测模型对照 | Freiburg Building 079、Intel Lab、MIT CSAIL Lab室内二维扫描，分别切为训练／验证／测试子集；评估预测扫描精度，不是全局定位性能。 |
| 被评估任务 | 在已训练神经占据场表示的已知环境中定位；分别报告全局初始化与跟踪。 |

[原文§IV-A–C](https://ar5iv.labs.arxiv.org/html/2210.03113#S4)。原文实验并未证明在本项目的走廊扫描限制或大幅持久地图变化下仍可恢复。本次仅覆盖已公开的IPBLab Seq 1。

## 看视频前：本次观察效果

| 方法 | 地图类型 | 指标效果 |
| --- | --- | --- |
| IR-MCL | 神经占据场 | RMSE 5.31 cm / 1.07°；Seq 1定位有效 |

**待排查假设：**过期的学习地图可能渲染错误的预期扫描；重复走廊结构或信息充分的线束太少，可能留下多个合理位姿。可检查预测／实测扫描残差及粒子覆盖。这些是诊断推断，本次Seq 1没有验证这些失效。

下面保留的是历史证据；[最新真实执行](../../results/reference/desktop-live-ir-mcl/execution.mp4)观察的是重新运行的作者代码推理。

![IR-MCL](../../results/reference/ir-mcl/media/preview.gif)

[结果回放](../../results/reference/ir-mcl/media/replay/replay.mp4) · [完整执行实录](../../results/reference/ir-mcl/media/session/full-session.mp4) · [原始记录](../../results/reference/ir-mcl/runs/ir-mcl-wsl/record.json) · [时间核对](../../results/reference/ir-mcl/media/timing.json)

## 结果

使用官方配置与官方权重做全局定位，由仓库自带的 evo 评估在其 1354 帧窗口上打分：位置 RMSE **5.32 cm**，偏航 RMSE **1.07°**。论文对同一序列、同一窗口给出 5.13 cm 与 1.05°。

此处只展示位置与偏航 RMSE；原生估计轨迹、真值轨迹、配置和完整评分仍可重算。Seq 1 评测既有地图中的定位，不计算 DA/SA；动态地图下的自恢复仍是独立实验。

[论文](https://arxiv.org/abs/2210.03113) · [论文 HTML](https://ar5iv.labs.arxiv.org/html/2210.03113) · [作者源库](https://github.com/PRBonn/ir-mcl/tree/aab8c91b37e59f94442d8eddfa2f920ab1ecc4c5) · [兼容性补丁](../../results/reference/ir-mcl/runs/ir-mcl-wsl/compatibility.patch)

## 运行

[环境与命令](../guides/REPRODUCE.zh-CN.md) · [源码来源](../guides/ATTRIBUTION.zh-CN.md)

## 范围

只做全局定位，且只用官方公开的那一个序列。其余四个自录序列与三个公开数据集的观测模型实验不在本次运行内，内存占用数值未重测。源码有两行调整、C++ 扩展改用环境自带的 pybind11 编译，两者都在补丁中说明。
