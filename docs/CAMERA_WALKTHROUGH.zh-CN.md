# 从打开 WSL 开始：用相机看到算法结果

本机相机是 D435，没有 IMU。本教程第一步用左右红外图运行 **RTAB-Map Stereo 视觉里程计**：估计相机移动轨迹并产生稀疏局部地图。彩色深度图用来检查传感器，但这一算法没有消费深度图。RGB-D 稠密彩色建图、回环和主分支语义算法属于后续步骤，不能把当前输出叫作已经完成的彩色房间地图。

当前方式为 **Windows 采集 → WSL 回放运行算法 → Windows 打开结果视频**。录制时不会出现实时算法窗口；算法视频明确标为已保存输出回放。原始数据留在本机 `data/`。

辨认窗口：`PS C:\...>` 是 Windows PowerShell；`qzl@电脑名:...$` 是 Ubuntu Bash。PowerShell 的 `Set-Location`、`Get-Date`、`Invoke-Item` 不能贴进 Bash。若出现 `-bash: syntax error near unexpected token '('`，先只输入 `exit` 回车，确认回到 `PS ...>` 后再逐行输入 Windows 命令。若回到的是没有 `PS` 的 `C:\...>`，先输入 `powershell`。每次只按当前窗口的语法执行；不确定时先看提示符。

## 1. 打开 Ubuntu 窗口

按 **Win+X**，选“终端”或“Windows PowerShell”，输入：

```powershell
wsl -d Ubuntu-22.04
```

出现类似 `qzl@电脑名:~$` 后，说明已进入 Ubuntu。下面是 **Ubuntu 命令**：

```bash
cd /mnt/d/workspace/be2/Personal-Learning-Physical
source /opt/ros/humble/setup.bash
ros2 pkg prefix rtabmap_odom
```

最后应输出 `/opt/ros/humble`。先保留这个窗口。进入时可能提示 localhost 代理未映射；若上述本地检查成功，本教程的离线算法不依赖联网。

## 2. 再打开 Windows 窗口，只看 5 秒场景

再次按 Win+X，打开一个新的 PowerShell。保持它在 Windows 中，不执行 `wsl`。USB 相机由 Windows SDK 访问，不需要把相机转交给 WSL。

先将镜头朝向 1–3 m 的有纹理墙角、纸箱或家具，移开挡在镜头前的近物，避开直射灯和亮屏；相机保持不动。复制下面**唯一一行 PowerShell 命令**，整行粘贴后回车；不需要先切换目录或设置变量：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File D:\workspace\be2\Personal-Learning-Physical\scripts\preview_camera.ps1
```

脚本自行选择新输出目录；5 秒结束后才打开图片，它是本段约第 2 秒的截图。`-ExecutionPolicy Bypass` 仅用于这次运行，不修改全局执行策略。若采集失败，脚本停止并给出记录路径，先查看 `capture.json` 的 `error`，不要继续后续导出。相机被其他查看器占用时，先关闭查看器。若使用教程后面的多行命令，应逐行执行，不要把多条命令拼成一行。

图片的四格分别为 RGB、伪彩深度、左 IR、右 IR。普通哑光墙角应有可辨认的深度结构，两路 IR 应清楚、能看到场景纹理；玻璃、反光、轮廓边缘和黑亮物有空洞并不罕见。深度黑色表示无效；整幅大面积无效或近物占满镜头时先改摆位。这四格仍是传感器检查，没有算法轨迹。

## 3. 做一次 50 秒、1 m 往返

在地面标记 A、B，相距约 1 m。相机镜头方向、高度尽量保持一致，沿视线方向从 A 慢移到 B，再后退回 A，**不要转身**。让起终点相机尽量回到同一位置和朝向；路线前方场景最好仍在约 1–3 m 范围。

| 录制时间 | 动作 |
| --- | --- |
| 0–10 秒 | 在 A 保持稳定，给初始化留时间 |
| 10–25 秒 | 沿直线缓慢前移约 1 m 到 B |
| 25–30 秒 | 在 B 保持稳定 |
| 30–45 秒 | 镜头朝向不变，缓慢后退回 A |
| 45–50 秒 | 在 A 保持稳定 |

计时以采集启动后为准，可用单独的秒表。手持停留仍会有真实抖动，不用于固定设备的毫米级噪声验收。保存实际动作时间、尺量距离和起终点摆位偏差；建议先用文字记在该会话目录里。

下面为了检查自然场景特征，暂时关闭 IR 投射器；脚本退出会恢复原值，并记录 `temporary_options_restored`。关闭后 IR 太暗或纹理不足时，应改善照明或更换场景，不以强投射光斑作为移动可靠性的证明。这个设置也可能降低深度填充率，需与双目跟踪效果分别解释。

在 **Windows PowerShell** 运行：

```powershell
$taskWalk = 'data\camera-walk-' + (Get-Date -Format 'yyyyMMdd-HHmmss')
.venv\Scripts\python.exe scripts\capture_camera.py --seconds 50 --record-raw --emitter off --output $taskWalk
```

命令运行时执行上表动作。SDK 启动可能先等待几秒，最终以录制视频时间及动作记录对齐。结束后确认 `status=received`；没有成功时先查看 `error`。

## 4. 核验和导出，仍在 Windows 窗口

使用刚才同一个 PowerShell 窗口，保留 `$taskWalk` 变量：

```powershell
.venv\Scripts\python.exe scripts\verify_camera_recording.py (Join-Path $taskWalk 'raw.db3')
.venv\Scripts\python.exe scripts\export_stereo.py (Join-Path $taskWalk 'raw.db3') --output (Join-Path $taskWalk 'stereo')
Split-Path -Leaf $taskWalk
```

核验应为 `status=verified`；导出应为 `status=exported`，并显示非零 `pairs`。导出跳过约前 2 秒，每三帧取一对，约 10 Hz；真实左右标定来自原始录制。最后显示 `camera-walk-YYYYMMDD-HHMMSS`，下一步要用该**实际目录名**。

## 5. 回到 Ubuntu 窗口，运行算法

将下一段第一行的目录名替换为第 4 步实际输出，不要原样粘贴日期占位符：

```bash
task_walk=data/camera-walk-YYYYMMDD-HHMMSS
python3 scripts/run_odometry_baseline.py "$task_walk/stereo" \
  --session-type motion --output "$task_walk/odom-motion"
python3 scripts/render_odometry_video.py "$task_walk/stereo" "$task_walk/odom-motion"
```

算法回放接近原录制时长，之后渲染视频；终端会打印处理进度和结果。`odom-motion` 必须是新目录，失败后保留它，重跑改用 `odom-motion-02`，后面的渲染路径也同步修改。

`--session-type motion` 只改变会话说明、轨迹统计和视频解释，**不修改 RTAB-Map 跟踪参数或强迫轨迹形状**。不加选项时保留原来的静止模式。

## 6. Windows 打开结果，怎样判断算法是否工作

回到保留变量的 **Windows PowerShell**：

```powershell
Invoke-Item (Join-Path $taskWalk 'odom-motion\preview.mp4')
Get-Content (Join-Path $taskWalk 'odom-motion\result.json')
```

| 视频位置／字段 | 算法内容及正常预期 |
| --- | --- |
| 上方左右 IR | 实际算法输入；场景清楚、左右对应合理，无严重运动模糊 |
| `TRACKING`／`LOST`、`inliers` | 跟踪状态及实际内点；慢移时尽量连续跟踪。TRACKING 本身不保证几何正确，也没有适用于所有场景的固定“内点合格数” |
| 左下 X/Z 轨迹 | 初始相机坐标系的投影，X 向右、Z 朝前；前移时轨迹平滑延伸、停下时趋于稳定、后退时大致沿原路返回。突然飞走、长时间冻结或无实际转动却跳变异常 |
| 右下稀疏局部地图 | **最终**算法局部地图的参考投影，并非逐时刻稠密地图。稀疏点正常；此节点没有全局回环 |
| `observed_output_fraction`、`lost_status_fraction` | 初期运动排查目标是正常慢移跟踪可用比例 >95%，同时报告缺口和丢失；不等于运动精度通过 |
| `translation_excursion_max_m` | 估计轨迹距离起点的最大位移；这次约 1 m 往返应呈同量级，不能拿它作为“静止漂移” |
| `translation_endpoint_separation_m` | 估计起终点间距；只有确认物理上回到相同位置和朝向，才能结合摆位误差讨论终点漂移 |
| `estimated_path_length_m` | 估计轨迹逐段长度之和，理想往返约 2 m；手持抖动会增加长度，不用它单独验收尺度 |
| `time_estimation_s.p95`、`timing_gate` | 本次约 10 Hz 输入周期约 100 ms；计算 p95 应小于周期，软件排队不应持续增加。这是离线回放时延，不是传感器实时端到端延迟 |

运动模式中 `static_gate`／`static_gate_passed` 为 `null`，不是失败，也不是自动通过。当前没有独立参考轨迹，ATE／RPE 不计算。正常地回到 A 也不代表回环优化运行过。

第一遍先判断跟踪是否连续、移动方向与轨迹响应是否一致。看过实际视频并记录起终点后，再决定做固定 60 秒、尺量单程、90°转动、重复会话或 RGB-D 建图；不要直接把这次往返成绩当作所有相机算法已通过。

软件验证说明：新增运动模式已在旧静止录制的 30 对真实图像上检查 ROS 输出、运动统计和视频标签；这只是兼容性检查，不是新的物理运动成绩。证据见 [运动模式软件检查](../evidence/motion-mode-software-check.json)。
