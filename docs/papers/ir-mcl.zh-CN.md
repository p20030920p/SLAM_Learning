# IR-MCL

[English](ir-mcl.md) | 中文

**波恩 IPBLab 室内实验室，官方公开的唯一一个定位序列（1543 帧扫描，1041 线束下采样到 32 线）。** 神经占据场（NOF）为每个粒子渲染一条合成扫描，渲染距离与真实距离之差即为粒子滤波的观测模型。

![IR-MCL](../../results/reference/ir-mcl/media/preview.gif)

[完整视频](../../results/reference/ir-mcl/media/replay/replay.mp4) · [原始记录](../../results/reference/ir-mcl/runs/ir-mcl-wsl/record.json) · [时间核对](../../results/reference/ir-mcl/media/timing.json)

## 结果

使用官方配置与官方权重做全局定位，由仓库自带的 evo 评估在其 1354 帧窗口上打分：位置 RMSE **5.32 cm**，偏航 RMSE **1.07°**。论文对同一序列、同一窗口给出 5.13 cm 与 1.05°。

[论文](https://arxiv.org/abs/2210.03113) · [论文 HTML](https://ar5iv.labs.arxiv.org/html/2210.03113) · [作者源库](https://github.com/PRBonn/ir-mcl/tree/aab8c91b37e59f94442d8eddfa2f920ab1ecc4c5) · [兼容性补丁](../../results/reference/ir-mcl/runs/ir-mcl-wsl/compatibility.patch)

## 运行

[环境与命令](../guides/REPRODUCE.zh-CN.md) · [源码来源](../guides/ATTRIBUTION.zh-CN.md)

## 范围

只做全局定位，且只用官方公开的那一个序列。其余四个自录序列与三个公开数据集的观测模型实验不在本次运行内，内存占用数值未重测。源码有两行调整、C++ 扩展改用环境自带的 pybind11 编译，两者都在补丁中说明。
