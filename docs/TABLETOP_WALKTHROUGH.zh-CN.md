# 盒子水杯纸质笔记本和鼠标实验操作指南

[English](TABLETOP_WALKTHROUGH.md) | 中文

使用本机已经配置的 D435、L2、Windows PowerShell、Ubuntu-22.04、ROS2 Humble 和 RViz。先固定设备，记录物体变化；后面再单独测设备移动。每个代码块只有一条命令，**粘贴一个块，回车，等待，再执行下一个块**。

第一轮目标是得到每台传感器各五段可回放原始数据、真实预览视频和事件记录：原四事件加一段单独移动鼠标，每台有效计时共 6 分 40 秒，不含准备与收尾。第二轮才做定位对照与作者建图核心。计时工具已做软件检查，本指南中的新物体摆放与新录制尚未执行。

## 1. 摆放与目标

| 物品 | 编号与摆放 | 作用 |
| --- | --- | --- |
| 盒子 | B01，中央，较大正面朝设备；标记初始位置 A | 主要目标；遮挡、移除和移动都针对它 |
| 水杯 | C01，盒子左侧，分开约一个杯宽，保持原位 | 静态对照、语义查询目标。先用空杯；透明／亮面杯的深度空洞单列，优先使用不透明杯 |
| 纸质笔记本 | N01，盒子右侧，封面朝设备，放稳 | 静态语义目标；仅遮挡实验把它移到盒子前方作挡板 |
| 鼠标 | M01，放在盒子旁的独立空位，不被其他物品遮住，标记 M_A／M_B | 第二个移动目标；另录一段只移动鼠标，原四事件中保持不动 |

背景留墙角、桌面与纹理，四个物体不要占满画面。相机先离物体约 1–2 m，稍向下看桌面；实际按深度有效性调整，之后同模态四段保持设备位置和参数一致。笔记本能稳立就立放，不能稳立就平放；不要靠盒子支撑，以免搬盒子时一起移动。平放时只评价可见封面，不期待 L2 给薄纸书脊很多回波。

给盒子标 A、B 两个位置，有尺时量 **30 cm**，并记录误差；没有尺就记“约一个盒宽、未测量”，只作定性移动实验，不能计算厘米级准确率。手机拍一张完整布局，正式事件评价可用独立手机视频核对动作。测量与参考不确定性记录在额外场景说明中，不覆盖原始采集文件。

鼠标另设 M_A、M_B，有尺时同样量 30 cm，位置与盒子移动路径分开。它是实验物体，倒计时后不要拿它操作电脑，改用 Alt+Tab 切换 A／B 窗口、键盘空格标记。有线鼠标预留松弛线缆，移动时不牵动设备或其他物品。

遮挡时笔记本本身在移动，所以它不属于该段的静态评价对象；稳定对照用水杯、墙面和桌面。分别从相机画面与 L2 点云确认盒子确实被遮住；两台的视场不同，遮挡布置可分别调整并记下。

四类测试要回答：静止是否误删／产生假运动；遮挡是否被误当消失；可见移除后旧空间是否更新；移动后新位置与旧坐标是否处理正确。原作者核心未必提供全部事件能力，缺失项填不适用，不能自动判通过。

## 2. 打开正确终端与检查环境

房间先开灯，设备固定并接好 USB。当前相机实际为 **D435，无 IMU**；L2 使用独立供电和 CH343 USB 转串口。

按 **Win+X → 终端／Windows PowerShell**，窗口叫 A。确认提示符为 `PS ...>`。若是 `qzl@...$`，先输入 `exit` 回车回到 PowerShell。

在 A 执行：

```powershell
Set-Location -LiteralPath D:\workspace\be2\Personal-Learning-Physical
```

检查磁盘剩余 GiB：

```powershell
[math]::Round((Get-PSDrive D).Free / 1GB, 1)
```

本次准备时约 71 GiB 可用。原始四路相机录制很大，先预留约 30 GiB 做五段及检查，录完复查空间；这不是固定文件大小承诺。

检查相机入口及录像依赖，**不打开设备**：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\start_live.ps1 -Sensor camera -Video -CheckOnly
```

预期结尾为 `Environment check passed. Sensors were not opened.`。有 WSL 代理警告但检查成功时保留记录继续；有红色报错或检查失败先按[环境排错](ENVIRONMENT.zh-CN.md)处理。

## 3. 先看相机画面并调整一次

在 A 执行：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\start_live.ps1 -Sensor camera
```

脚本自动启动 WSL 和 RViz。确认四个物体都入镜，RGB 静止时封面／盒面文字清楚；Depth 中盒面有连续深度，黑色表示无效。杯子反光／透明处黑洞可发生，不能只看杯子判断相机损坏。左右 IR 的投射亮点正常。

在 RViz 左侧 Displays 勾选 RGB、Depth 0-5m、Left IR、Right IR、Current cloud；只想看某项就取消其余项。3D 视图滚轮缩放、鼠标拖动；改变屏幕视角不算移动设备。弱光彩色点云偏暗时，点云 `Color Transformer` 可切 `FlatColor`，它只改变显示。

这是原始预览，**没有轨迹是正常的**。摆放合适后，不再碰相机。回 A 按 Ctrl+C，等打印 `Saved session` 并返回 `PS ...>`。只关 RViz 不会停止采集。

## 4. 第一段相机静止实验

在 A 开始无限时原始采集和录像：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\start_live.ps1 -Sensor camera -Algorithm sensor -SessionType stationary -Record -Video
```

这里 `stationary` 声明整段设备固定，包括计时前后；物体是否运动由事件另记。程序不会自动判断设备是否固定。保持 A 开着，等真实 RViz 图像开始更新。

再按 Win+X 打开**第二个 PowerShell 窗口 B**，进入同一目录：

```powershell
Set-Location -LiteralPath D:\workspace\be2\Personal-Learning-Physical
```

在 B 启动本段计时：

```powershell
.venv\Scripts\python.exe scripts\scene_timeline.py --latest camera --event static --fixed-sensor
```

核对 B 打印的 `SESSION` 与 A 的 `Session` 一致。工具会记录固定声明、物品编号和计划事件，倒数 5 秒后开始 80 秒；静止段全程不碰设备、物体，尽量离开视野。`--latest` 只适合当前只开一个对应设备会话；不要在计时期间再启动新采集。

看到 `Trial ended` 后，回 A 按 Ctrl+C。等待 `Saved session`、文件哈希及录像收尾完成；视频会自动打开。B 的工具只负责计时，**不会关闭 A 的采集**。

## 5. 另外三段相机事件

每段先恢复布局，再在 A 重新执行第 4 节的采集命令，等 RViz 更新；然后 B 只执行该事件的一条计时命令。每段结束都去 A 按 Ctrl+C 等保存，不能在同一段重复启动计时。

| 屏幕时刻 | 你的动作 |
| --- | --- |
| 0–20 s | 所有物体保持初始位置 |
| 20 s，出现 `action` | 开始该事件，争取 25 s 前完成；完成后在 B **按空格**记录 |
| 25–60 s | 保持事件后的状态；动作晚于 25 s 完成也如实按空格 |
| 60 s，出现 `restore` | 恢复初始摆放，争取 65 s 前完成；完成后在 B **再按空格** |
| 65–80 s | 保持恢复后的状态 |
| 80 s，出现 `end` | 回 A 按 Ctrl+C，等待保存 |

**遮挡：**20 s 把纸质笔记本放在盒子前，盒子不动；尽量别让手臂长期挡住水杯。笔记本不够大时记录为部分遮挡，不补写成完全遮挡。60 s 把笔记本放回原位。

```powershell
.venv\Scripts\python.exe scripts\scene_timeline.py --latest camera --event occlusion --fixed-sensor
```

**移除：**20 s 搬走盒子，让旧位置和后方背景完整可见；60 s 把盒子按原朝向放回 A。

```powershell
.venv\Scripts\python.exe scripts\scene_timeline.py --latest camera --event removal --fixed-sensor
```

**移动：**20 s 把盒子从 A 移到 B；水杯、笔记本与鼠标不动。60 s 放回 A。

```powershell
.venv\Scripts\python.exe scripts\scene_timeline.py --latest camera --event move --fixed-sensor
```

### 新增一段只移动鼠标

恢复全部物品初始位置，在 A 按第 4 节重新启动采集，等 RViz 更新；B 执行：

```powershell
.venv\Scripts\python.exe scripts\scene_timeline.py --latest camera --event move --target mouse --fixed-sensor
```

20 s 把鼠标从 M_A 移到 M_B，完成后空格；盒子、水杯、笔记本都不动。60 s 把鼠标按原朝向移回 M_A，再按空格。80 s 去 A 停止并保存。未指定 `--target` 时默认盒子，不要把两者一起移动后记成单目标实验。

鼠标是小目标，先看静止 0–20 s 中 RGB 是否清楚、鼠标表面是否有有效深度。分别记录盒子与鼠标的深度支持、查询命中、旧位置残留和坐标更新，不用大盒子的结果平均掉小鼠标的失败。目标参考不足时保留定性结果。

空格记录的是操作者报告的完成时刻，包含回到键盘的延迟，不是自动检测到的真实物理时刻；提示时间也不等于动作已完成。忘按键会保留缺失标记。碰到设备、动作做错或录制异常时在 B 按 Q 中止本段，再去 A 停止；原数据保留，新开一段重做。中止段会撤销固定导出声明，不能用于单位位姿导出。

## 6. 打开文件与核验原始相机录制

每段输出在 A 打印的 `data\live-camera-日期时间`。保存 `raw.db3`、`rviz-live.mp4`、`capture.json`、`live-result.json`、`session-note.json`、`trial-scene.json` 和 `events.csv`。视频是 RGB-D 原始点云预览，尚无 SAM 掩码或语义查询；不因画面好看就判算法质量通过。

建议**静止段刚录完就在 B 执行以下命令**，保存其目录变量供后面使用：

```powershell
$taskCameraStatic = Get-ChildItem -LiteralPath .\data -Directory -Filter 'live-camera-*' | Sort-Object Name -Descending | Select-Object -First 1 -ExpandProperty FullName
```

打开该目录：

```powershell
Invoke-Item -LiteralPath $taskCameraStatic
```

看事件记录：

```powershell
Get-Content -LiteralPath (Join-Path $taskCameraStatic 'trial-scene.json')
```

预期 `status=timeline_completed`。静止段不要求按空格；其余四段应有 `action_complete` 与 `restore_complete`。这些是按键记录，独立事件验证仍为 false；尺量位移初值为 null，要根据真实测量补充参考说明。

鼠标移动段同样应有两个完成标记，`trial-scene.json` 与 `session-note.json` 的 `target` 应为 `M01`；盒子段为 `B01`。鼠标与盒子的新旧位置分别评价，已有录制不会被脚本重新标注。

录制已停止后，核验四路原始回放：

```powershell
.venv\Scripts\python.exe scripts\verify_camera_recording.py (Join-Path $taskCameraStatic 'raw.db3') --output (Join-Path $taskCameraStatic 'raw-replay-check.json')
```

预期 `status=verified`、四路解码计数与文件一致；该证据文件不覆盖，重复检查换新输出名。若 B 已关掉或变量保存晚了，先用资源管理器确认静止段目录，再用 `$taskCameraStatic = '完整目录'` 设置，不能把最新移动段误当静止段。

## 7. 雷达按同样流程录四段

把 L2 固定平放，盒子、水杯、笔记本位于可见扫描范围。相机录制先停止；本轮两设备分别录，分别评分。L2 小目标回波稀疏、纸书脊薄、透明杯难测都可能发生，先看点云决定该目标是否有足够支持。

A 检查雷达入口与录像依赖：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\start_live.ps1 -Sensor lidar -Video -CheckOnly
```

A 预览：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\start_live.ps1 -Sensor lidar
```

RViz 勾选 Current cloud，`Color Transformer=Intensity`；拖动看墙、桌面与物体，滚轮放大。原始模式轨迹为空正常。确认后 Ctrl+C 停止并等待保存。

每段 A 启动：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\start_live.ps1 -Sensor lidar -Algorithm sensor -SessionType stationary -Lines 50 -Record -Video
```

等点云更新后，在 B 按本段事件选一条。动作和空格标记与相机相同：

```powershell
.venv\Scripts\python.exe scripts\scene_timeline.py --latest lidar --event static --fixed-sensor
```

```powershell
.venv\Scripts\python.exe scripts\scene_timeline.py --latest lidar --event occlusion --fixed-sensor
```

```powershell
.venv\Scripts\python.exe scripts\scene_timeline.py --latest lidar --event removal --fixed-sensor
```

```powershell
.venv\Scripts\python.exe scripts\scene_timeline.py --latest lidar --event move --fixed-sensor
```

再新开一段 A 的雷达采集，只移动鼠标；B 执行：

```powershell
.venv\Scripts\python.exe scripts\scene_timeline.py --latest lidar --event move --target mouse --fixed-sensor
```

鼠标贴近桌面且较小，L2 可能没有足够独立回波。先在静止区间检查目标支持；不可分辨就标记“该条件下不可观测”，不能把没扫到当作成功剔除或定位成功。每种方法使用同一资格判定和原始记录。

每段只执行一条计时命令，80 s 后去 A 停止、等待保存，再开始下一段。不要手写 COM3，入口会找实体串口。

雷达静止段刚保存后，在 B 保存目录：

```powershell
$taskLidarStatic = Get-ChildItem -LiteralPath .\data -Directory -Filter 'live-lidar-*' | Sort-Object Name -Descending | Select-Object -First 1 -ExpandProperty FullName
```

审计 UART：

```powershell
.venv\Scripts\python.exe scripts\audit_l2.py $taskLidarStatic
```

看 `audit.json`，预期有效点包／IMU包都非零、CRC及序号缺失很少；正常参考约 216 线包/s、250 IMU 包/s，50 线组约 4.3 Hz。当前实时录制的接收 CSV 不包含审计所需的逐包时间表，因此这个离线审计不一定报告主机频率；同时查看 `capture.json` 的 `102`／`104` 字段。时间比例约 2 仍待解决，这一步不验融合或 LIO。

## 8. 手动进入 WSL 查看话题与 RViz

保持 A 的相机或雷达实时入口运行，另外开 PowerShell 窗口 C，执行：

```powershell
wsl -d Ubuntu-22.04
```

看到 `qzl@...$` 后，以下才是 Ubuntu Bash 命令，每次一个块：

```bash
source /opt/ros/humble/setup.bash
```

相机选 83；看雷达时把下条中的 83 改为 84：

```bash
export ROS_DOMAIN_ID=83 ROS_LOCALHOST_ONLY=1
```

```bash
ros2 topic list
```

相机可以检查：

```bash
ros2 topic hz /physical/camera/color/image
```

Ctrl+C 停频率检查。手动另开相机 RViz：

```bash
rviz2 -d /mnt/d/workspace/be2/Personal-Learning-Physical/configs/rviz/camera_raw.rviz
```

雷达使用 domain 84 和 `lidar_raw.rviz`。手动 RViz 需要自己关闭；自动入口已经有 RViz 时无需重复打开。`exit` 回到 PowerShell。原始相机约 30 Hz、桥接约 8 Hz 与视频 10 fps 是不同量。

## 9. 单独查看定位算法

先完成上述四类事件及鼠标移动段，再恢复静态布局。每次在 A 运行一条，设备与物体整段保持固定 60 s，不运行事件计时工具；命令自动停止保存。

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\start_live.ps1 -Sensor camera -Algorithm stereo -SessionType stationary -Seconds 60 -Record -Video
```

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\start_live.ps1 -Sensor camera -Algorithm rgbd -SessionType stationary -Seconds 60 -Record -Video
```

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\start_live.ps1 -Sensor lidar -Algorithm icp -SessionType stationary -Seconds 60 -Record -Video
```

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\start_live.ps1 -Sensor lidar -Algorithm kiss -SessionType stationary -Seconds 60 -Record -Video
```

RViz 默认显示轨迹和跟踪状态。正常目标：固定时轨迹在原点附近，最大平移偏离 <5 cm、转角 <2°，稳态有效覆盖 >95%；KISS 没有原生 LOST 指标，该项不填 0。旧 L2 固定结果没有达到这些目标，新运行也可能失败，完整保存。四次实采不同，不能据此公平排名；严格定位对照需重放同一录制。

要看 RTAB-Map 全局建图，另开一次，保持四个物体不动，起点静止 5 s，缓慢移动相机看墙角与物体，再回起点：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\start_live.ps1 -Sensor camera -Algorithm rgbd-slam -SessionType motion -Record -Video
```

勾选 RGB-D global map，结束 Ctrl+C。预期关键帧地图逐渐增加，回环只有匹配成功才出现。这段是移动设备演示，不能导出单位位姿，不是 ConceptGraphs／HOV-SG。暂不拿未标定的两设备一起移动。

## 10. 真正接入四个作者核心

新事件记录供后续适配完整时间轴和独立标签。下面先用**静止段**做可执行的接口检查，不填正式质量分数。输出目录存在时换后缀，保留原结果。

在 B（PowerShell）导出相机静止段 8 帧：

```powershell
.venv\Scripts\python.exe scripts\export_rgbd.py (Join-Path $taskCameraStatic 'raw.db3') --fixed-sensor-session --frames 8 --output data\tabletop-static-input-01
```

预期 `status=exported`、`frames=8`；抽取启动后约 3–10 s，是输入检查，不覆盖完整事件。进入 WSL：

```powershell
wsl -d Ubuntu-22.04
```

在 Ubuntu 中依次执行：

```bash
cd /mnt/d/workspace/be2/Personal-Learning-Physical
```

```bash
CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 /home/qzl/projects/SLAM_Learning/.venv-semantic/bin/python scripts/check_main_rgbd.py data/tabletop-static-input-01 --method conceptgraphs --main-repo /mnt/d/workspace/be2/SLAM_Learning --runtime /home/qzl/projects/SLAM_Learning --output data/tabletop-static-input-01/check-conceptgraphs
```

```bash
CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 /home/qzl/projects/SLAM_Learning/.venv-hovsg/bin/python scripts/check_main_rgbd.py data/tabletop-static-input-01 --method hovsg --main-repo /mnt/d/workspace/be2/SLAM_Learning --runtime /home/qzl/projects/SLAM_Learning --output data/tabletop-static-input-01/check-hovsg
```

预期各 `loader_check_passed`、8 帧。**此处没有 SAM／CLIP 推理、文本查询或语义地图窗口。** 真正语义核心的实物入口仍需适配；不要直接把启动参数改成不存在的 `-Algorithm conceptgraphs`。查询文本在看结果前固定为 `a box`、`a cup`、`a paper notebook`、`a computer mouse`；真实 SAM 掩码、候选与坐标必须由算法输出后独立核对。

输入 `exit` 回 PowerShell。雷达静止段使用本机已有官方 SDK 解码器，先转换路径：

```powershell
$taskLinuxLidarStatic = (& wsl.exe -d Ubuntu-22.04 -- wslpath -u $taskLidarStatic).Trim()
```

```powershell
wsl.exe -d Ubuntu-22.04 -- python3 /mnt/d/workspace/be2/Personal-Learning-Physical/scripts/export_l2_clouds.py $taskLinuxLidarStatic --lines 50 --sdk-decoder /mnt/d/workspace/be2/Personal-Learning-Physical/.cache/decode_sdk_lines_checked --output /mnt/d/workspace/be2/Personal-Learning-Physical/data/tabletop-l2-static-50-01
```

预期生成 `clouds.json` 与逐组 NPZ，`decoder` 标明官方转换。本机缓存缺失时先恢复 SDK 编译环境；新克隆不会包含该二进制。然后运行 DUFOMap 固定 40 观测入口：

```powershell
wsl.exe -d Ubuntu-22.04 -- /home/qzl/projects/SLAM_Learning/.venv/bin/python /mnt/d/workspace/be2/Personal-Learning-Physical/scripts/run_main_dufomap.py /mnt/d/workspace/be2/Personal-Learning-Physical/data/tabletop-l2-static-50-01 --main-repo /mnt/d/workspace/be2/SLAM_Learning --fixed-sensor-session --output /mnt/d/workspace/be2/Personal-Learning-Physical/data/tabletop-dufomap-01
```

BeautyMap 复用它的同一输入，原入口仍可能遇到已知的小地图边界错误：

```powershell
wsl.exe -d Ubuntu-22.04 -- /home/qzl/projects/SLAM_Learning/.venv/bin/python /mnt/d/workspace/be2/Personal-Learning-Physical/scripts/run_main_beautymap.py /mnt/d/workspace/be2/Personal-Learning-Physical/data/tabletop-dufomap-01 --main-repo /mnt/d/workspace/be2/SLAM_Learning --upstream /home/qzl/projects/SLAM_Learning/.cache/upstream/beautymap --fixed-sensor-session --output /mnt/d/workspace/be2/Personal-Learning-Physical/data/tabletop-beautymap-original-01
```

诊断扩域另存目录：

```powershell
wsl.exe -d Ubuntu-22.04 -- /home/qzl/projects/SLAM_Learning/.venv/bin/python /mnt/d/workspace/be2/Personal-Learning-Physical/scripts/run_main_beautymap.py /mnt/d/workspace/be2/Personal-Learning-Physical/data/tabletop-dufomap-01 --main-repo /mnt/d/workspace/be2/SLAM_Learning --upstream /home/qzl/projects/SLAM_Learning/.cache/upstream/beautymap --fixed-sensor-session --pad-small-map-control --output /mnt/d/workspace/be2/Personal-Learning-Physical/data/tabletop-beautymap-control-01
```

查看清理前后图，可先生成 DUFOMap 的三列图：

```powershell
wsl.exe -d Ubuntu-22.04 -- python3 /mnt/d/workspace/be2/Personal-Learning-Physical/scripts/render_dufomap_smoke.py /mnt/d/workspace/be2/Personal-Learning-Physical/data/tabletop-dufomap-01
```

```powershell
Invoke-Item -LiteralPath .\data\tabletop-dufomap-01\comparison.png
```

原云／保留／缺失三列不能自动判定正确动态清理。当前入口取约前 40 秒有效观测，也不覆盖全部 80 秒事件，因此先限静止输入检查。完整事件公平比较需使用同一冻结抽样和独立标签，协议见[同场景对比](../METHOD_COMPARISON.zh-CN.md)。

## 11. 每轮的预期和验收

| 阶段 | 预期结果 | 还不能据此宣称什么 |
| --- | --- | --- |
| 本轮五段 | 每模态五个独立目录；盒子与鼠标分开移动，原始数据可回放；事件有真实完成标记 | 尚无独立标签时不报 SA／DA、查询准确率或位置准确率 |
| 固定定位 | 轨迹贴近原点；同时检查有效覆盖、漂移和状态 | 有位姿输出不等于准确，分开实采不是同输入排名 |
| 作者输入 | RGB-D 两加载器各 8/8；L2 官方解码与 DUFOMap 输入成功；BeautyMap 失败单列 | 加载成功不等于语义建图，扩域诊断不等于原实现通过 |
| 正式质量 | 地图保留稳定背景、减少运动支持；查询命中正确物体与有效表面坐标 | 原生核心不保证自动理解遮挡／移除，须真实执行与标注 |

质量初期目标：静态支持误删 <5%、可见移除召回 >80%、独立指定锚点误差 <10 cm；尺量／标注缺失则对应指标留空。先用五段试拍完善可见性和输入，再按对比协议采验证／测试会话；弱光与迟到位姿修正放在之后，逐项改变因素。

原始数据、室内视频和计时记录都留忽略目录 `data/`；脚本与指南推送个人分支。当前不改主分支、不合并。
