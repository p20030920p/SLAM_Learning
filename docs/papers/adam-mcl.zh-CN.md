# AdaM-MCL

[English](adam-mcl.md) | 中文

**自建 128 格室内平面、一个留出场景、200 个粒子。** 卷积网络把地图与二维扫描变成可采样的位姿分布，全局定位的粒子因此直接从整张地图上抽取，而不是从均匀先验。

![AdaM-MCL 评测会话录制](../../results/reference/adam-mcl/media/preview.gif)

[完整视频](../../results/reference/adam-mcl/media/replay/replay.mp4) · [原始记录](../../results/reference/adam-mcl/runs/adam-mcl-wsl/record.json) · [时间核对](../../results/reference/adam-mcl/media/timing.json)

## 结果

上游流程端到端跑通：作者的数据生成器、路径规划器、训练入口与 `test_MCL` 评测全部原样执行，仅施加已披露的补丁。同一条 123 次更新的序列重复 10 次，修正后的每次运行位置 RMSE 均值为 34.82 格（末帧误差均值 47.71 格），每次滤波更新耗时 0.43 s。按论文收敛判据折算到本平面后，10 次重复中**没有任何一次**在全局定位阶段或绑架阶段连续 5 次落入误差带。

## 运行

[复现脚本](../../results/reference/adam-mcl/harness/README.md) · [环境与命令](../guides/REPRODUCE.zh-CN.md) · [源码来源](../guides/ATTRIBUTION.zh-CN.md)

## 范围

固定提交里 `Dataset/` 与 `Trained_models/` 均为空目录：作者的 20 张仿真地图、6 条评测序列与预训练权重都在 Google Drive，本地不可达；UPO 与 Bicocca 真实数据集也未获取。因此本次用自建的 128 格平面，交给**作者自己的**生成器与路径规划器产生训练样本和评测序列，DSOM 训练 **2432 次优化步**，作者默认值是 **2 880 000 步**。格不是论文里的米，所以**不与表 I、表 II 的任何数值对照**。本次只覆盖全局定位与绑架；真实数据集实验、PFRNN 与 PF-Net 基线、完整 SLAM、导航与硬件精度均未验证。

[指标勘误](../../results/reference/adam-mcl/ERRATUM.md)：旧导出器把原生距离又取平方根，旧记录原字节保留，指标以修正结果为准。
