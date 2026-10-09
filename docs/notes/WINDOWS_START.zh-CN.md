# 从 Windows 打开文档、运行方法、查看结果

[English](WINDOWS_START.md) | [索引](README.zh-CN.md)

本手册中的运行命令对应保留的旧版 WSL 环境；该环境本次没有迁移。当前仓库的 `src/` 布局与新环境安装命令见[运行说明](../guides/REPRODUCE.zh-CN.md)。

这份手册针对**这台已配置的电脑**。Windows 用来读文档、录屏和连接设备；作者方法在 WSL Ubuntu-22.04 运行。下面每块代码只复制到标明的终端，不要把 Bash 命令粘到 PowerShell。

## 1. 打开学习入口

打开 Windows Terminal，选择 PowerShell：

```powershell
Set-Location 'D:\workspace\be2\SLAM_Personal_Guide'
git branch --show-current
Get-Content -Encoding utf8 .\notes\README.zh-CN.md
explorer.exe 'D:\workspace\be2\SLAM_Personal_Guide\docs\notes'
```

分支应是 `notes/personal-study-guide-20261008`。在 GitHub 上打开该分支的 `notes/README.zh-CN.md` 可直接点击索引；本机可用现有 Markdown 编辑器打开文件。Windows 主仓库 `SLAM_Learning` 仍在 main，不需要切换它。

## 2. 进入真正运行代码的 Ubuntu

**PowerShell：**

```powershell
wsl --list --verbose
wsl -d Ubuntu-22.04 -u qzl
```

进入后提示符类似 `qzl@...:~$`。以下为 **WSL Bash**：

```bash
cd /home/qzl/projects/SLAM_Learning
pwd
git branch --show-current
git status --short
ls .venv/bin/python .venv-semantic/bin/python .venv-hovsg/bin/python
nvidia-smi
```

应找到三个 Python，运行仓库当前在 main；个人分支只提供文档，不必让这个有缓存的运行仓库切分支。`nvidia-smi` 先查看其他任务占用，再决定何时启动语义推理。不要中断其他窗口正在运行的实验。

Windows 盘 `D:\...` 在 WSL 对应 `/mnt/d/...`；WSL 的 `/home/qzl/...` 则在 Windows 文件管理器中这样打开：

```powershell
explorer.exe '\\wsl.localhost\Ubuntu-22.04\home\qzl\projects\SLAM_Learning'
```

这条仍在 **PowerShell** 执行，另开标签页即可。读源码／看输出不要求安装 VS Code。

## 3. 三个环境分别用于什么

| 环境 | 用途 | 运行方式 |
| --- | --- | --- |
| `.venv` | LiDAR 作者核心、评价、配对调度、文档检查 | `.venv/bin/python ...` |
| `.venv-semantic` | ConceptGraphs、SAM／CLIP | `.venv-semantic/bin/python ...` |
| `.venv-hovsg` | HOV-SG 原生核心 | `.venv-hovsg/bin/python ...` |
| ROS2 系统 Python | RViz 点云发布／查看 | `source /opt/ros/humble/setup.bash` 后用 `python3` |

命令使用解释器全路径，不必 `activate`。CPU 的 `uv.lock` 不要装进两个 CUDA 环境。数据主要在 `.cache/datasets/00`、语义准备目录和 `.cache/semantic-weights`；原库在 `.cache/upstream`；每次输出在 `results/runs`。

先做无推理的自检，**WSL Bash**：

```bash
.venv/bin/python -m slam_learning.cli doctor
.venv/bin/python -m slam_learning.cli --help
```

`doctor` 输出 CPU 环境版本与数据存在状态，不能代替实际运行、语义权重或设备接入验证。

## 4. 按顺序手动运行四个作者核心

所有命令的当前目录都是 `/home/qzl/projects/SLAM_Learning`。每条结束后再执行下一条。

### 4.1 DUFOMap

```bash
.venv/bin/python -m slam_learning.cli run --method dufomap
echo $?
```

完整 teaser 是 141 扫描。命令会打印新的日志路径和最终 `record.json`。`echo $?` 要紧跟运行命令，0 表示普通执行成功。`--frames 10` 是另一种冒烟检查，只能证明短流程可运行，不产生论文成绩。

### 4.2 BeautyMap

```bash
.venv/bin/python -m slam_learning.cli run --method beautymap
echo $?
```

同样是完整 teaser。每次产生新目录，兼容补丁和无标签输入在该目录中隔离保存。

### 4.3 ConceptGraphs

```bash
.venv-semantic/bin/python scripts/run_conceptgraphs.py
echo $?
```

处理 40 次提供姿态的 room0 RGB-D 观测；依次生成 SAM／CLIP 特征、运行作者关联／融合，再保存对象及查询摘要。包装器把中间输出写入 `segmentation.log` 和 `mapping.log`，终端暂时安静不等于卡死。

### 4.4 HOV-SG

```bash
.venv-hovsg/bin/python scripts/run_hovsg.py
echo $?
```

处理八次提供姿态观测。得到分段特征地图，尚不是完整楼层／房间图或导航流程。不要直接删除脚本的跳帧／批量设置来追求“完整复现”。

### 4.5 确认自己这次产物

把运行打印的目录记下来；下方 `你的新运行目录` 必须替换，不能原样复制或拿旧目录冒充新结果：

```bash
cat results/runs/你的新运行目录/record.json
ls -lh results/runs/你的新运行目录
tail -n 30 results/runs/你的新运行目录/run.log
```

`run.log` 用于 LiDAR；ConceptGraphs 看 `segmentation.log`／`mapping.log`；HOV-SG 看 `mapping.log`。运行时另开 WSL 标签页，先 `cd` 同一仓库，再对自己的日志执行 `tail -f 路径`；按 `Ctrl+C` 只退出该日志查看。

| 方法 | 主要产物 | 需要核对 |
| --- | --- | --- |
| LiDAR 两种 | `cleaned.pcd`、`metrics.json`、`worker.json`、日志、`record.json` | `status=executed`、退出码0、全量范围、SA／DA及评分定义 |
| ConceptGraphs | `objects.pkl.gz`、`summary.json`、历史快照、两个日志、补丁 | 40 观测、对象数、实际绝对位姿、输入／输出哈希 |
| HOV-SG | `map.ply`、`objects/*.ply`、`segment_features.npy`、`summary.json`、有效配置 | 八观测、分段数、内参缩放、源帧索引、退出状态 |

LiDAR 完整性检查示例（替换路径）：

```bash
.venv/bin/python -m slam_learning.cli verify results/runs/你的LiDAR目录/record.json --full
```

公开 `results/reference` 是轻量证据；没有完整原生地图。`--full` 要对有真实产物的本地记录使用。普通执行成功不要求论文数值完全相等；`--strict-paper` 会对论文容差不满足返回2。

## 5. 真正打开 RViz，看它做了什么

先看[录屏手册](MANUAL_RECORDING.zh-CN.md)的来源说明。复现命令不会自动弹出 Gazebo 或 RViz；现在的 RViz 是查看已保存输出的独立步骤。

**第一次使用现有已核查的 ConceptGraphs 基线，WSL Bash：**

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

第一次创建 `my-cg-visual-01`；若已存在，换 `02`，不覆盖。命令最后应打开 Windows 桌面中的 WSLg RViz 窗口。

**第二个 WSL 标签页：**

```bash
cd /home/qzl/projects/SLAM_Learning
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID=71
export ROS_LOCALHOST_ONLY=1
python3 scripts/view_measured_rviz.py \
  results/runs/my-cg-visual-01/manifest.json --seconds-per-step 10 --cycles 0
```

此时 RViz 显示点云，旁边来源面板显示观测和阶段。左键拖动旋转、滚轮缩放；仔细看对象是否碎裂、查询高亮是否合理。`--cycles 0` 表示循环，按 `Ctrl+C` 停止发布，再关闭 RViz。

如果本机旧 `.rviz` 文件被移动，直接运行 `rviz2`，设置 Fixed Frame 为 `map`，通过 Add 添加 PointCloud2 `/study/cloud`，设 Color Transformer 为 RGB8；另加 Marker `/study/label`。让发布器运行后调整视角，再通过 File → Save Config As 保存自己的配置。

四种方法的准备命令及如何绑定新结果见[录屏手册](MANUAL_RECORDING.zh-CN.md)。

从 PowerShell 可直接打开已录视频目录：

```powershell
explorer.exe 'D:\workspace\be2\SLAM_Recordings\2026-10-08\rviz-review-v3'
```

本机已有四份[公开 RViz 短片](../media/rviz)。完整 `capture/full-session.mp4` 和 `VIDEO_INDEX.md` 在上述本地目录；不用重新推理就能查看。

## 6. 怎样对照原库、怎样用两台设备

读[原库对照](UPSTREAM_COMPARISON.zh-CN.md)，依次打开固定 README、实际入口、`compatibility.patch`、本次 `record.json`。不要直接改缓存源码。

居家测试先读[公开实验设计](../guides/REAL_WORLD.zh-CN.md)，再按[设备操作手册](HOME_RUNBOOK.zh-CN.md)连接 D435／L2。第一阶段只做固定传感器四事件采集和回放。设备数据适配与 H1 模块尚未实现，不能把采到 bag 等同于完成假设检验。

## 7. 遇到问题先定位在哪层

| 现象 | 下一步 |
| --- | --- |
| Bash 提示路径／命令不存在 | 先 `pwd`；确认是在 WSL `/home/qzl/projects/SLAM_Learning`，不是 Windows 文档分支 |
| 找不到 `.venv-semantic`／`.venv-hovsg` | 先查是否进错目录；确认缺失后才按下节准备对应环境 |
| 语义任务长时间无终端输出 | 看本次日志和 `nvidia-smi`，别同时重开第二个任务 |
| exit137 | 保存未完成记录、日志、系统时间和资源状态；不能仅凭这个码断言 CUDA OOM |
| RViz 空白 | 两终端 ROS_DOMAIN_ID 同为71；`ros2 topic list`、`ros2 topic echo /study/cloud --once --field header`；检查 Fixed Frame、显示话题和视角 |
| RViz 图形异常／黑屏 | 关闭窗口后在其终端 `export LIBGL_ALWAYS_SOFTWARE=1` 再启动；先录十秒试片回放 |
| `--full` 缺文件 | 可能用了公开轻量记录；改用对应本地完整运行目录 |
| 论文数值不一致 | 对照本次版本、参数、输入和评分定义，保留差距，不按预期改成绩 |

## 8. 只有环境确实缺失时才重新准备

本机 2026-10-08 已核查 WSL、三个环境、ROS2 Humble／RViz2、公开数据和原生基线存在。日常重跑跳过安装。若有本地修改，先查 `git status`，不要用 reset／clean 丢弃。

**WSL Bash，按缺少的项目分别执行：**

```bash
# CPU 环境和数据／作者源码
bash scripts/setup_linux.sh
.venv/bin/python -m slam_learning.cli fetch

# ConceptGraphs 环境、固定模型与语义数据
bash scripts/setup_semantic.sh

# HOV-SG 独立环境（依赖已准备的语义数据／权重）
bash scripts/setup_hovsg.sh
```

先确认 `uv --version` 可用。若换成全新 Windows，没有 WSL 时在管理员 PowerShell 执行 `wsl --install -d Ubuntu-22.04`，按提示重启／创建账户，再依[微软安装说明](https://learn.microsoft.com/windows/wsl/install)配置；新的账户和路径不会自动叫 qzl。

`uv` 缺失时用[官方安装说明](https://docs.astral.sh/uv/getting-started/installation/)。新机器的 CUDA、RViz 和设备驱动仍需另验，不能沿用本机成功状态。
