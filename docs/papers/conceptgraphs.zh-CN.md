# ConceptGraphs

[English](conceptgraphs.md) | 中文 | [PDF](../pdf/conceptgraphs.zh-CN.pdf)

**已执行：**40 次给定位姿的 Replica room0 观测，运行作者无类别 SAM／CLIP 前端及原生对象关联／融合。属于核心子集，不是完整论文评价。

![ConceptGraphs 完整 RViz 录像](../../results/reference/conceptgraphs-full-media/conceptgraphs-rviz.gif)

**完整录像：69.6 秒，348 帧，保留原始 5 fps。**展示五个建图快照（第 1／10／20／30／39 次观测），随后展示四个文本查询阶段，包括开头、阶段切换和结尾。这是保存结果的查看录像；高亮候选尚未经独立验证。

[完整 MP4](../media/rviz/conceptgraphs.mp4) · [GIF](../../results/reference/conceptgraphs-full-media/conceptgraphs-rviz.gif) · [运行记录](../../results/reference/conceptgraphs-wsl/record.json) · [时序与来源](../../results/reference/conceptgraphs-full-media/record.json)

## 方法

[ConceptGraphs（ICRA 2024）](https://arxiv.org/html/2309.16650v1)把二维分割及特征提升至三维，按几何和语义相似度匹配，再增量融合对象表示。论文已展示定位及动态更新，不能笼统描述为只支持静态世界。

```bash
bash src/scripts/setup/setup_semantic.sh
.venv-semantic/bin/python src/scripts/methods/run_conceptgraphs.py
```

独立 CUDA 环境固定 PyTorch 2.0.1+cu118、PyTorch3D 0.7.4。数据为 NICE-SLAM Replica 归档的源帧 0,5,...195。范围下载清单记录 CRC 和解压文件 SHA-256，不声称完整归档校验。加载前校验 SAM／CLIP 完整权重哈希。

## 结果

| 项目 | 实测结果 |
| --- | --- |
| 给定位姿 RGB-D 观测 | 40 |
| 后处理对象表示 | 39 |
| 查询 | chair、sofa、table、lamp，各 3 候选 |
| 位姿坐标核查 | 39 个保存相机矩阵与给定绝对位姿一致 |
| 查询／语义准确率 | 未评价；余弦相似度不是概率 |

SAM 保留 12×12 提示网格，把批量从 144 改为 36。首次大批量运行中断并保留。补丁还记录无界面绘图、本地权重及无类别路径跳过未用检测模块；几何和关联阈值不变。未声称与未适配版本产生完全相同掩码。

实际批处理入口读取绝对 dataset.poses，绕过加载器 __getitem__ 的归一化位姿。因此历史 center_world_m 已在 Replica 世界坐标。观测 0 初始化不保存快照；1–39 的矩阵构成核查依据。再乘第一帧变换反而错误。

## 局限

作者报告薄物体漏检、重复对象与描述错误（III-H）。即便 CLIP 特征合理，错误空间对齐也可能分裂身份或合并相似物体。这一位姿机制是我们的假设，尚未成为跨论文实测失效。对象个数不能证明关联正确。

开放问题是：关联／融合后，迟到的位姿修正能否恢复身份及目标坐标？保留帧号、位姿版本、掩码／特征和暂定对应的附加模块具有实现可行性，需标注、阈值／可见性基线及相同覆盖率／延迟控制。Khronos 已有联合优化和修复，不能仅以记忆／重放作为创新。

该方法直接联系语义建图、视觉定位与几何可信度。LLaVA 描述、LLM 图推理、完整语义指标及导航不在本次范围。[环境与限制](../guides/SEMANTIC.zh-CN.md) · [共享问题](../research/STUDY.zh-CN.md)。

## 作者查看器

![ConceptGraphs 完整作者查看器](../../results/reference/conceptgraphs-full-media/conceptgraphs-author-viewer.gif)

**完整录像：60 秒，900 帧，保留原始 15 fps。**来自独立的 [room0 400 观测运行](https://github.com/p20030920p/SLAM_Learning/blob/535a2780af7ca7eb3aa02f722e1340fe90bc2dcf/docs/CONCEPTGRAPHS_ROOM0_RESULTS.zh-CN.md)。在作者查看器中旋转保存地图，切换 RGB／实例颜色，未展示查询或场景图关系。[完整 MP4](https://github.com/p20030920p/SLAM_Learning/blob/3b0b9a88ac7c77431268b6c869c369e01bd19b3e/evidence/videos/conceptgraphs-room0-original-window.mp4)。

## 回放说明

原主 GIF 来自另一份 **13.33 秒摘要**，只展示 20 个选定观测、最终世界 XZ 地图与红色查询候选，并非完整 RViz 或作者查看器录像。交付展示已改用上面的两份完整录像。[历史摘要 MP4](../media/conceptgraphs/replay.mp4) · [历史媒体记录](../../results/reference/paper-media-conceptgraphs/record.json)。
