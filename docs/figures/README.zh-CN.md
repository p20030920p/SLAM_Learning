# 图、GIF 与视频

[English](README.md) | 中文

这里是唯一媒体索引。首页的关键预留位置放图注和注释中的图片行，全部预留资产在此列出，不渲染缺失图片。`slots.json` 区分已有探索／诊断图、未来作者对照，以及确认性结果。

## 已发布图

| 资产 | 阶段 | 图注 |
| --- | --- | --- |
| [replication-hero](replication_hero.gif) | R0/R2 | 同一批 teaser 条目的 DUFOMap、BeautyMap、真值：固定视角，原始／移除／保留。使用最终离线地图，不表现为在线更新。 |
| [replication-frame](replication_frame.png) | R0/R2 | 明确帧号，同一世界坐标范围、同一点身份，对照各方法和真值。 |
| [metric-correspondence](metric_correspondence.png) | R1 | 同实例 DUFOMap：直接身份、相同保留点的最近邻、原生输出；141 帧，零注入误差。 |
| [pose-margin](../../results/reference/pose-stress/sensitivity.png) | R0 diagnostic | 真实 teaser 的六组直接标签敏感性；不作论文表格或语义导航比较。 |
| [mechanism-ambiguity](../../results/reference/mechanism/mechanism.png) | exploratory E1 | 已知身份／可见性，少数与多数运动；保留中位数失败。 |
| [evidence-calibration](../../results/reference/evidence-stress/calibration.png) | exploratory E0 | 已知尺度的高斯共享偏差；同时报告误删、Brier 与变化召回。 |

## 预留位置

| 文件 | 阶段 | 展示要求 |
| --- | --- | --- |
| `docs/figures/paper_gap.png` | R1 | 实测与论文差值，AA／HA 分开，注明评价器差异。 |
| `docs/figures/bottleneck_diagram.svg` | B0 | 位姿、对应、证据与暂定更新；实测观察与猜测反馈分开。 |
| `docs/figures/pose_drift.gif` | E0 | 相同边际误差下精确／独立噪声／相关漂移；固定前端与视角。 |
| `docs/figures/semantic_update.mp4` | R3 then E2 | 先作者语义地图基线，再迟到修正和对象查询；显示有效性与覆盖率。 |
| `docs/figures/risk_coverage.png` | E2 after H0 | 留出风险—覆盖率／延迟曲线；参数只由验证集选取，带不确定性区间。 |
| `docs/figures/failure_gallery.gif` | R2/E1/E2 | 不变、移动、移除、遮挡、缺锚点情形；不只挑成功序列。 |

## 从评分证据渲染

1. 完成 [PLAN](../PLAN.zh-CN.md) 的对应阶段，保存运行／帧号与数据清单。本机已有两种最终离线清理图，但不能把它们演成在线逐帧决策。
2. 使用**声明的评价器**生成点结果：地图最近邻仍用 5 cm；直接标签用精确身份。真值进评价器／渲染器，不进算法。不同 API 对应独立命名的图和表。
3. 在 [rendering.json](../../configs/rendering.json) 中一次固定空间范围、视角、帧列表和显示采样；各方法／真值共用。抽稀只用于显示，数值按完整声明范围计算。选定 teaser 的帧号不能证明完整 KITTI 连续采样。
4. 渲染原始／移除／保留面板，写运行号和每个数值的**范围**；用实际哈希与生成命令填写 [media_record.template.json](media_record.template.json)。蓝色漏检和红色误删必须可见。
5. 发布 PNG／SVG，或紧凑 GIF 预览加 MP4 链接。GitHub 首页使用 GIF／PNG，不依赖 HTML video 元素。8 MiB GIF 是我们的展示目标，不是平台限制。

## 发布

地图回放与接口诊断已有实测生成器；其余预留资产尚未生成，不创建空图，也不把计划中的生成器标成已测试。实际渲染器完成后，记录命令／版本，将输出哈希绑定到媒体生成记录；`check_docs.py` 会核对已发布图的哈希。

把产物放到约定路径，更新 [slots.json](slots.json) 的来源与状态，再将首页注释改成真实图片。两种语言共用资产、分别翻译图注；需要中文画内标签时，从同一输入／配置生成，不做两套独立选图。

```bash
uv run python scripts/check_docs.py
uv run python scripts/verify_evidence.py
```

不在图片编辑器里改掩码或成绩，失败案例也要公开。原扫描、模型权重、数据文件不放本目录。PNG／SVG 用清楚标签和不透明背景，兼容 GitHub 明暗主题。

## 四篇各自录制

[论文索引](../papers/README.zh-CN.md)连接原生结果、MP4、GIF、封面及双语 PDF。12 项新增媒体在 `slots.json` 中绑定哈希。[录制命令](../RECORDING.zh-CN.md)披露最终地图回放及坐标核查。`docs/figures/physical_capture.mp4` 预留至实物采集完成。

12 份双语 PDF 绑定[生成证据](../../results/reference/paper-pdfs/record.json)，另有[32 页排版检查](../../results/reference/paper-report-review/qa.json)。索引现有 30 个已发布资产、7 个预留位置。
