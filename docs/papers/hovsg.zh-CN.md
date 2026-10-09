# HOV-SG：分段特征地图复现

[English](hovsg.md) | 中文 | [PDF](../../output/pdf/hovsg.zh-CN.pdf)

**已执行：**8 次给定位姿 Replica 观测上的作者三维分段特征建图。属于第四篇相关论文的建图核心；楼层／房间层级及导航未复现。

![HOV-SG 原生观测与最终特征地图](../media/hovsg/poster.png)

[MP4](../media/hovsg/replay.mp4) · [GIF](../media/hovsg/preview.gif) · [运行记录](../../results/reference/hovsg-wsl/record.json) · [媒体来源](../../results/reference/paper-media-hovsg/record.json)

## 1. 方法与执行

[HOV-SG（RSS 2024）](https://arxiv.org/html/2403.17846v2)把 SAM 分段、CLIP 特征投影至参考几何，合并多次观测、筛选稳健特征，再构造楼层／房间／对象层级。本次调用作者 Graph.create_feature_map()，包括原生几何合并及特征筛选，版本 d6e65a53c8be6faec3f01f00d1644d967f89e605。

```bash
bash scripts/setup_hovsg.sh
.venv-hovsg/bin/python scripts/run_hovsg.py
```

独立环境与 ConceptGraphs 共享经过校验的权重及 40 观测 Replica 子集。skip_frames=5 处理源索引 0,25,...175。RGB／深度缩放为 640×360，两个内参轴分别从固定的 1200×680 标定缩放。SAM 批量 36、CLIP 批量 4 属于资源适配，作者分割／合并阈值不变；未声称与原始分辨率掩码完全相同。

## 2. 实测输出及保留失败

| 项目 | 实测结果 |
| --- | --- |
| 处理的给定位姿观测 | 8 |
| 最终分段 | 50；不一定对应 50 个物理对象 |
| 参考点 | 166,777 |
| 查询 | 4 文本 × 3 候选，正确性未标注 |
| 建图进程 PyTorch 分配峰值 | 10,030,088,704 字节，不含驱动分配 |

首次 40 观测尝试已完成前端提取，随后层次合并进程被终止，退出码 137。其记录、日志及中间结果哈希[已保留](../../results/reference/hovsg-wsl-interrupted/record.json)。原因尚未确定，不附加地图成绩或“已确认 OOM”的说法。成功缩小子集是另一个运行，不覆盖原记录。

不能把 50 分段与 ConceptGraphs 的 39 对象排名：观测数量、图像设置、关联／合并定义不同。余弦分数不是校准概率。未报告语义 mIoU 或完整图／导航成绩。

## 3. 缺陷与研究关联

论文明确指出静态场景、处理时间和参数限制（V），投影依赖准确里程计（III-A）。持续的静态特征地图缺少移动目标的时间有效性；几何误差可能在语言查询前就把像素语义证据分配给错误参考点。

开放问题是：如何保留足够观测来源，在位姿修正后重新考虑语义分配，同时避免无限存储或让所有查询都等待？共享位姿／暂定更新模块可先在分段层实现，扩展楼层／房间层级是额外工作。测试不变／移动／移除／遮挡，对照阈值和可见性基线，并匹配查询覆盖率、召回和延迟。[共性瓶颈及反例](../STUDY.zh-CN.md)。

## 4. 视频如何解读

8 个原生 SAM 观测旁显示最终世界 XZ 分段地图。红色分段是查询候选，不是已验证真值。坐标由给定绝对 camera-to-world 矩阵确定。这是最终地图实测回放，不是实时导航、逐步层级增长或运行速度测试。
