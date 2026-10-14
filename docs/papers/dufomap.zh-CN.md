# DUFOMap

[English](dufomap.md) | 中文

**KITTI-00，141 帧雷达扫描。** 利用观测到的空闲空间识别动态点，并用位姿裕量保护静态结构。

## 原文数据集与场景

| 评估 | 数据／场景 |
| --- | --- |
| 三维地图清理定量实验 | KITTI 00城镇／01高速，64线；Argoverse 2城市交通，两个32线传感器；半室内运动行人，16线。 |
| 定性迁移展示 | MCD VIRAL测绘数据：不同离散站位的Leica RTC360扫描；DOALS拥挤车站，128线；两层建筑，Livox Mid-360。 |
| 被评估任务 | 给定位姿下对扫描点分类。原文区分使用全部扫描的后处理，与只使用已累积观测的在线DUFOMap⋆。 |

[原文§IV-A／§V](https://arxiv.org/html/2403.01449v1#S4)。§V-E明确指出稀疏采样是限制，§V-C验证位姿误差会影响分类。本次KITTI-00并未覆盖所有数据集或在线基准。

## 看视频前：本次观察效果

| 有效 | 无效／限制 |
| --- | --- |
| 最新原生KITTI-00，141帧：SA 97.98%、DA 98.70%；大部分动态残留被移除，静态点保留。[现场记录](../../results/reference/desktop-live-dufomap/record.json) | 仍有动态点残留和静态点损失，地图清理不等于位姿恢复。其投影地图在动态Gazebo AMCL单次实验中，相对Raw的RMSE仅降低0.06 cm。[机器人记录](../../results/reference/robot-live-dynamic/record.json) |

**待排查假设：**稀疏射线、遮挡或重访不足可能使空闲空间证据不足；位姿误差也可能破坏这类证据。先检查可见性与具体点的保留决策，再归因定位失效。这是诊断推断，尚未确认是本实验的失效原因。

下面保留的是历史结果回放；[最新真实执行](../../results/reference/desktop-live-dufomap/execution.mp4)观察的是一次新的原生运行。

![DUFOMap](../../results/reference/dufomap/media/preview.gif)

[完整视频](../../results/reference/dufomap/media/replay/replay.mp4) · [原始记录](../../results/reference/dufomap/runs/dufomap-wsl/record.json) · [时间核对](../../results/reference/dufomap/media/timing.json)

## 结果

保留的封装试跑 SA／DA／AA 为 97.9798／98.7029／98.3407%。另一组原始 C++ Table IV 实验在两位小数精度下匹配全部 15 个准确率数值。

[原始代码与论文协议](https://github.com/p20030920p/SLAM_Learning/blob/535a2780af7ca7eb3aa02f722e1340fe90bc2dcf/docs/DUFOMAP_TABLE4.zh-CN.md)

## 运行

[环境与命令](../guides/REPRODUCE.zh-CN.md) · [源码来源](../guides/ATTRIBUTION.zh-CN.md)

## 范围

使用给定位姿，只检查已声明的建图阶段。视频是保存结果的回放；完整 SLAM、导航与硬件精度未验证。
