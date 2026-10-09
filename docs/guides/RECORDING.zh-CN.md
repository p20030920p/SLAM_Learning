# 可视化与录制范围

[English](RECORDING.md) | 中文

## 实际 RViz 图形窗口

本轮录制实际打开的 RViz 三维窗口，而不是只拍终端。左侧显示方法、阶段、来源与观测，右侧显示真实保存的点云。**这是实测输出查看，不是重新执行算法或实时建图性能演示。**

| 方法 | 窗口中显示什么 | 查看 | 时长 |
| --- | --- | --- | ---: |
| DUFOMap | 前 21 个源扫描的相同抽样点，原始／移除／保留分类；GT 仅用于着色 | [MP4](../media/rviz/dufomap.mp4) · [画面](../media/rviz/dufomap.png) | 34.4 s |
| BeautyMap | 同一空间视角下的原始／移除／保留分类 | [MP4](../media/rviz/beautymap.mp4) · [画面](../media/rviz/beautymap.png) | 34.4 s |
| ConceptGraphs | 作者保存的观测 1／10／20／30／39 历史地图快照，再切换四个最终地图查询候选和原生 SAM 观测 | [MP4](../media/rviz/conceptgraphs.mp4) · [画面](../media/rviz/conceptgraphs.png) | 69.6 s |
| HOV-SG | 最终分段特征地图、四个文本查询候选及对应输入观测图 | [MP4](../media/rviz/hovsg.mp4) · [画面](../media/rviz/hovsg.png) | 34.4 s |

每段使用独立 Xvfb，软件 OpenGL 避免争用 CUDA；真实屏幕按单调时钟 5 fps 捕获，H.264 完整解码并检查所有显示阶段。显示抽稀不影响此前全量评分。Replica 的 `(x,y,z)→(x,z,-y)` 仅用于 RViz 坐标显示，不改保存地图。橙色候选并不等于标注正确。

[来源、逐阶段检查帧、日志与脚本快照](../../results/reference/visual-review/record.json)绑定发布字节。`prepare_visual_review.py` 校验原生输出；`view_measured_rviz.py` 发布 ROS2 PointCloud2 并显示观测；`record_visual_review.sh` 打开真实 RViz。HOV-SG 没有用最终地图伪造逐步增长，当前四个作者入口也没有运行 Gazebo。

## 本地全过程执行录制

另有四份完整 xterm／PTY 原片，从新命令启动到退出码 0：DUFOMap 36.6 s、BeautyMap 42.0 s、ConceptGraphs 256.6 s、HOV-SG 168.8 s。它们证明命令执行，画面主要为终端。大原片留本地；[轻量证据](../../results/reference/full-recordings/record.json)保留命令、日志、时序与哈希。

`record_session.py` 创建私有 Xvfb／xterm，在捕获开始后放行真实命令，按单调时钟抓屏。旧视频没有打开地图 GUI，本轮图形视频将 RViz 作为实际子进程录入同一私有屏幕。两类时长均不能当作算法 FPS 或严谨性能基准。

## 主页回放与 PDF

论文卡原有 GIF／MP4 是已测最终地图的绘制回放。LiDAR 原始／移除／保留来自原 PCL 分类；语义面板显示原生观测、最终地图和查询候选。ConceptGraphs 世界坐标按实际绝对位姿入口及 39 个相机矩阵核查，不额外乘第一帧变换。

首页使用[经过时序核对的 v3 GIF](../../results/reference/media-previews-v3/record.json)。原顶部动图将 21 个快照压在 2.52 秒内；新版播放 13.99 秒，与对应 14 秒回放一致。作者查看器原先从 15 fps 降为 5 fps，丢掉三分之二帧；新版保留 48 秒片段的全部 720 帧。ConceptGraphs RViz 改为连续 59 秒，保留全部九阶段之间的切换过程。

| GIF | 原片／显示帧率 | 编码帧数 | GIF 秒数 |
| --- | --- | ---: | ---: |
| dufomap | 12/1 | 168 | 14.01 |
| beautymap | 12/1 | 168 | 14.01 |
| conceptgraphs | 12/1 | 160 | 13.33 |
| dufomap-rviz | 5/1 | 120 | 24.00 |
| beautymap-rviz | 5/1 | 120 | 24.00 |
| conceptgraphs-rviz | 5/1 | 295 | 59.00 |
| conceptgraphs-author-viewer | 15/1 | 720 | 47.99 |
| replication-hero | 1.5 快照／秒 | 21 | 13.99 |

全部帧完整解码。帧数与所选原片区间一致，累计时间误差不超过 20 毫秒，包含 GIF 百分之一秒量化误差。地图 MP4 原本就是 12 fps、每个观测保持八帧：稀疏观测仍逐次切换，保留视频时序不会生成更密的传感器运动。RViz 原录制只有 5 fps；不添加插值帧，不声称实时性能。HOV-SG 论文复现未完成，因此不再导出其交付预览。早期媒体与记录保持原样。


使用现有 `ffmpeg` 与 `ffprobe` 重新导出；Windows 添加 `--wsl Ubuntu-22.04`。脚本校验源视频哈希，拒绝覆盖已有输出目录。

```bash
uv run --project src python src/scripts/media/export_media_previews.py \
  --author-video /path/to/conceptgraphs-room0-original-window.mp4 \
  --output results/runs/my-previews
```

16 份双语 PDF 保留各自生成源快照、字节哈希和逐页检查证据；当前文字修订不静默覆盖历史报告。[论文媒体与报告](../papers/README.zh-CN.md) · [配对报告及检查](../../results/reference/paired-report-review/record.json)。完整手动录制、安装与本机操作步骤放个人本地手册。

Room1 迟到修正实验另增三段完整本地终端录像：前端 82.4 秒、35 单元主实验 509.4 秒、6 单元事后对照 189.8 秒。最后一段有一次画面保持；全部 MP4 已完整解码。[哈希、命令、日志和检查图](../../results/reference/delayed-recordings/record.json)绑定对应科学记录。这些是执行录像；上方独立 RViz 视频查看已有基线的保存输出。[实验结果](../research/DELAYED_RESULTS.zh-CN.md)。
