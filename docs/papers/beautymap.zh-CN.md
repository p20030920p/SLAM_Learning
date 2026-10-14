# BeautyMap

[English](beautymap.md) | 中文

**KITTI-00，141 帧雷达扫描。** 通过占据关系去除动态残留，并用恢复步骤保护静态结构。

## 原文数据集与场景

| 评估 | 数据／场景 |
| --- | --- |
| 动态点去除主对照 | KITTI 00／01／05驾驶序列与半室内16线扫描，选取动态较多的片段。KITTI标注来自SemanticKITTI、位姿来自SuMa；半室内位姿来自simple-ndt。 |
| 单独实验 | KITTI 02：表III栅格大小权衡。KITTI 01：运行时间和模块消融。 |
| 被评估任务 | 离线清理已有完整三维地图，不估计位姿，也不更新机器人位姿分布。 |

[原文§IV](https://arxiv.org/html/2405.07283v1#S4)。多层地面、在线里程计接入、长期变化检测与地图更新在§V列为未来工作。历史KITTI-02第860–950帧与最新KITTI-00的141帧现场运行是不同实验。

## 看视频前：本次观察效果

| 方法 | 地图类型 | 指标效果 |
| --- | --- | --- |
| BeautyMap | 三维离线清理地图 | SA 96.95% / DA 98.34%；清理有效 |

**待排查假设：**地图与扫描的配准、栅格大小、地面层级及被遮挡的静态结构可能影响清理。原文模块消融说明静态结构恢复对保留点很重要。还需检查二维投影是否保留了三维清理差异；本实验尚未确认为定位失效原因。

下面保留的是历史结果回放；[最新真实执行](../../results/reference/desktop-live-beautymap/execution.mp4)观察的是一次新的原生运行。

![BeautyMap](../../results/reference/beautymap/media/preview.gif)

[完整视频](../../results/reference/beautymap/media/replay/replay.mp4) · [原始记录](../../results/reference/beautymap/runs/beautymap-wsl/record.json) · [时间核对](../../results/reference/beautymap/media/timing.json)

## 结果

保留的封装试跑 SA／DA／HA 为 96.9529／98.3382／97.6407%。另一组历史 KITTI-02 Table III 实验在两位小数精度下匹配全部 9 个准确率数值。

[原始代码与论文协议](https://github.com/p20030920p/SLAM_Learning/blob/535a2780af7ca7eb3aa02f722e1340fe90bc2dcf/docs/KITTI_PAPER_PROTOCOL.zh-CN.md)

## 运行

[环境与命令](../guides/REPRODUCE.zh-CN.md) · [源码来源](../guides/ATTRIBUTION.zh-CN.md)

## 范围

使用给定位姿，只检查已声明的建图阶段。视频是保存结果的回放；完整 SLAM、导航与硬件精度未验证。
