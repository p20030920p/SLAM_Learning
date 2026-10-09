# 自己走一遍作者复现和可视化录制

[English](MANUAL_RECORDING.md) | [索引](README.zh-CN.md)

这份手册只放个人文档分支。研究结论见[独立分析](../docs/STUDY.zh-CN.md)，设备操作见[居家手册](HOME_RUNBOOK.zh-CN.md)。

## 1. 先弄清已有视频分别拍了什么

| 视频 | 实际内容 | 能证明什么 |
| --- | --- | --- |
| 原来的四份 full-session.mp4 | Xvfb 内真实 xterm／PTY，从命令开始到退出码 0，5 fps 以单调时钟抓取窗口 | 该命令确实完成；不是三维建图画面或 FPS 测试 |
| 主页原来的 GIF／短 MP4 | 已算好的最终地图，用 Python 绘制原始／移除／保留或语义查询面板 | 实测输出长什么样；不是实时算法运行 |
| 本轮 RViz 视频 | 实际运行 RViz，显示保存的点云、ConceptGraphs 原生历史快照、查询候选和观测图 | 真实可视化窗口查看了什么；算法没有在录制时重新推理 |

原终端视频目录：`D:\workspace\be2\SLAM_Recordings\2026-10-08\VIDEO_INDEX.md`。新图形视频目录：`D:\workspace\be2\SLAM_Recordings\2026-10-08\rviz-review-v3\VIDEO_INDEX.md`。

原流程没有 Gazebo 场景，也没有 ROS 发布器自动打开 RViz。Gazebo 是仿真器，不能用临时模拟场景冒充这些论文的复现。现在添加的 RViz 只是对真实保存输出的查看接口；明确区分它和作者算法。

## 2. 手动重跑一次作者方法

打开 Windows Terminal，进入 WSL：

```powershell
wsl -d Ubuntu-22.04 -u qzl
```

在 Ubuntu 终端执行：

```bash
cd /home/qzl/projects/SLAM_Learning
git status --short
nvidia-smi
.venv/bin/python -m slam_learning.cli run --method dufomap
```

命令会打印新 `results/runs/dufomap-.../record.json` 和 `run.log`。别复制旧成绩，别覆盖 `paired-*-v1`。另开终端对**这次打印的日志路径**执行 `tail -f`，运行结束退出 `tail`，检查记录里的 `status=executed`、退出码和本次输出。普通退出码 0 不代表论文表格完全一致。

其余三种，逐个运行，不并发：

```bash
.venv/bin/python -m slam_learning.cli run --method beautymap
.venv-semantic/bin/python scripts/run_conceptgraphs.py
.venv-hovsg/bin/python scripts/run_hovsg.py
```

ConceptGraphs 是 40 次观测；HOV-SG 是 8 次观测。不要为了拍视频临时把它们说成完整 SLAM、导航或全量论文 benchmark。新运行的路径和耗时会与旧视频不同。

## 3. 打开真实三维结果窗口

ROS2 Humble 和 RViz2 已在本机 WSL 中找到。本轮不依赖相机或雷达接入。准备数据阶段使用各自的 Python；显示阶段使用 ROS2 的系统 Python，避免把 ROS 包装入 CUDA 环境。

下面先用已经核验的本地 ConceptGraphs 基线走一遍。新输出名自己换，已有目录会拒绝覆盖：

```bash
cd /home/qzl/projects/SLAM_Learning
.venv-semantic/bin/python scripts/prepare_visual_review.py conceptgraphs \
  results/runs/conceptgraphs-7795d7b47007/record.json \
  --output results/runs/my-cg-visual-01
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID=71
export ROS_LOCALHOST_ONLY=1
rviz2 -d /mnt/d/workspace/be2/SLAM_Recordings/2026-10-08/rviz-review-v3/conceptgraphs/data/review.rviz
```

第二个 WSL 终端使用同一 ROS domain：

```bash
cd /home/qzl/projects/SLAM_Learning
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID=71
export ROS_LOCALHOST_ONLY=1
python3 scripts/view_measured_rviz.py \
  results/runs/my-cg-visual-01/manifest.json --seconds-per-step 10 --cycles 0
```

这会循环展示来源快照和四项查询。鼠标左键拖动旋转，滚轮缩放；手动改变视角后停留几秒，让人看清三维结构。关闭时 `Ctrl+C`。面板说明保存快照与最终查询阶段；源码中的 Replica→RViz 轴变换仅供显示，不改存盘地图。

其他准备命令：

```bash
.venv-hovsg/bin/python scripts/prepare_visual_review.py hovsg \
  results/runs/hovsg-0206da9f0145/record.json --output results/runs/my-hov-visual-01
.venv/bin/python scripts/prepare_visual_review.py dufomap \
  results/runs/evaluation-check-6489fe584ba2/record.json \
  --dataset .cache/datasets/00 --output results/runs/my-dufo-visual-01
.venv/bin/python scripts/prepare_visual_review.py beautymap \
  results/runs/evaluation-check-6489fe584ba2/record.json \
  --dataset .cache/datasets/00 --output results/runs/my-beauty-visual-01
```

LiDAR 入口使用原 PCL 评价记录，展示前 21 个源扫描的同一抽样点及最终分类，评分仍是全部 141 扫描。HOV-SG 没有本次可用的逐步地图快照，显示最终分段地图和查询切换，不能叫在线层级增长。

如果换成自己新跑的 LiDAR 结果，要先跑 `slam-study cross-check` 得到**这两张新地图**的评价记录，再准备 RViz，不能用旧评价记录替代新运行。

替换两个目录为自己新运行的完整记录，WSL Bash：

```bash
.venv/bin/python -m slam_learning.cli cross-check \
  results/runs/你的DUFO目录/record.json \
  results/runs/你的Beauty目录/record.json
```

把这条命令打印的新 `evaluation-check-.../record.json` 传给上面的 LiDAR 准备命令。语义准备则直接用自己的完整原生 `record.json`。

## 4. 你手动录屏时的画面和讲解

使用自己熟悉的录屏工具。OBS 可选；本轮没有安装 OBS，也未在其常见安装路径找到程序。Windows 的录屏工具如支持选择区域，也可直接框选实验窗口。先录 10 秒试片并回放，检查 WSLg 窗口是否黑屏、文本是否清楚。

建议 1920×1080、30 fps、H.264；电脑卡顿就用 1280×720。画面至少 70% 给 RViz／RGB-D／三维结果，20% 给输入与查询／事件标签，终端只占剩余区域。不要把播放器回放速度当算法 FPS。

一次完整讲解分三段，可以分文件，不必假装一镜到底：

1. **算法执行**：显示新命令、新运行目录与真实日志，结束拍到退出码和产物。若中间等待很久，完整原片留存，剪辑版标注剪辑。
2. **保存输出检查**：说明“现在查看刚才运行保存的结果”，打开图形窗口，转动／缩放，指出静态保留与误删，或对象候选、坐标与语义误差。
3. **受控对照**：使用已经核验的配对单元展示零误差／打乱／漂移，固定视角与色标，解释为什么漂移并非总更坏。别临时把阈值优化称为 H1。

自己的新运行与图形窗口必须绑定同一来源。当前展示器不会在 mapper 推理过程中自动更新；如果需要边运行边看，需另写监听新快照的接口，不能靠播放旧地图冒充。

## 5. 本轮自动图形录制如何实现

`prepare_visual_review.py` 校验完整本地记录，读取真实输出，确定性抽稀并绑定源文件哈希；ConceptGraphs 另核对历史快照的绝对位姿。`view_measured_rviz.py` 用 ROS2 发布 PointCloud2，并打开来源／观测面板。

`record_visual_review.sh` 打开 RViz；现有 `record_session.py` 在私有 Xvfb 中录整个图形屏幕，实际捕获右侧 RViz，不抓取用户桌面。

使用软件 OpenGL，避免争抢 CUDA 显存；只进行保存结果查看，不重跑 SAM／CLIP。原片完整解码，检查多个阶段的图形帧、命令状态和持续时间。初期失败和调试片留在 v1／v2，不列入最终索引。

如果想复用自动图形录制，先完成上面的 `my-cg-visual-01` 准备、关闭其他 domain71 的查看器，再在 WSL 执行：

```bash
.venv/bin/python scripts/record_session.py \
  --output /mnt/d/workspace/be2/SLAM_Recordings/2026-10-08/manual-cg-review-01 \
  --cwd /home/qzl/projects/SLAM_Learning --fps 5 -- \
  bash scripts/record_visual_review.sh results/runs/my-cg-visual-01/manifest.json
```

输出目录须未存在；结束后打开其中 `full-session.mp4`。这条录的是私有 X 屏幕内自动打开的 RViz；若要录你自己鼠标操作的桌面窗口，使用前面的手动录屏路线。

## 6. 文件该放哪里

主分支：研究分析、原始轻量证据、失败记录、可核查短视频、最少复现命令。个人目录：完整录屏、原始设备文件、面试准备、逐步操作手册。不要把设备序列号、家庭可识别影像或巨大 bag 无意提交。

`local/full-notes-20261008` 保留整理前的本地快照。旧手册副本在 `D:\workspace\be2\SLAM_Private\2026-10-08\original-docs`；以本分支当前手册为准。
