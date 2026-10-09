# 本机环境和重建范围

[English](ENVIRONMENT.md) | 中文

当前硬件项目根目录为仓库下的 `src/physical/`。旧设备录像和缓存仍在保留的原独立目录；它们不会自动迁入新克隆。下面的环境重建命令使用当前目录；历史运行报告保留原路径。

本项目操作目录是 `D:\workspace\be2\SLAM_Personal_Guide\src\physical`，位于个人学习分支。下面是当前电脑的环境说明，不是可移植镜像。仓库保存代码/配置/轻量证据；原始录制、环境、SDK 缓存和模型不随 GitHub 克隆下载。

## 1. 当前环境

| 位置 | 用途 |
| --- | --- |
| `.venv\Scripts\python.exe` | Windows Python 3.12；pyrealsense2、NumPy、OpenCV-headless、pyserial；冻结版本见 requirements.txt |
| WSL `Ubuntu-22.04`，`/opt/ros/humble` | ROS2 Humble、RViz、RTAB-Map 0.23.7、系统 Python 3.10，NumPy/SciPy/OpenCV/Matplotlib/PyQt5、ffmpeg |
| `.cache/kiss-venv`（WSL） | KISS-ICP 1.3.0，隔离 ROS NumPy ABI；冻结依赖 requirements-kiss-wsl.txt |
| `.cache/unilidar_sdk2` | 官方 SDK 提交 `0e3c51f512e6b8ff60b8c32f160b412cb48445c2`，原生解码对照 |
| `/home/qzl/projects/SLAM_Learning/.venv`（WSL） | 原主分支 DUFOMap 环境；本分支只读取使用，不覆盖安装 |

Windows 环境只检查不启动硬件：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File D:\workspace\be2\SLAM_Personal_Guide\src\physical\scripts\start_live.ps1 -CheckOnly
```

检查 KISS 额外依赖：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File D:\workspace\be2\SLAM_Personal_Guide\src\physical\scripts\start_live.ps1 -Sensor lidar -Algorithm kiss -CheckOnly
```

CheckOnly 检查环境，不声称设备在线。实时启动另检查实体设备、端口、数据和算法消息。若当前端口缺失，应插接并供电；不自动改驱动、关闭虚拟串口或附加 USB 到 WSL。

## 2. 另机/环境丢失时

先安装匹配的 Windows Python 3.12、WSL Ubuntu 22.04/WSLg、ROS2 Humble，再安装 `rtabmap_odom`、`rtabmap_slam`、`rtabmap_msgs`、`rtabmap_rviz_plugins`、`rviz2`、Python 科学计算依赖和 ffmpeg。用各项目官方安装流程确认发行版兼容；本仓库不提供全机无人值守安装器。

Windows 目录存在且没有 `.venv` 时，可逐条运行（Python 绝对路径按实际安装位置调整）：

```powershell
Set-Location -LiteralPath D:\workspace\be2\SLAM_Personal_Guide\src\physical
```

```powershell
& C:\Users\qzl\AppData\Local\Programs\Python\Python312\python.exe -m venv .venv
```

```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

KISS 环境仅在 WSL 中、进入本分支目录后逐条创建：

```bash
cd /mnt/d/workspace/be2/Personal-Learning-Physical
```

```bash
python3 -m venv .cache/kiss-venv
```

```bash
.cache/kiss-venv/bin/python -m pip install -r requirements-kiss-wsl.txt
```

原生 Unitree 解码对照需要 g++ 和固定 SDK；新实时入口使用经过对照的 Python 解码，不依赖每次编译 SDK。旧数据导出/原生比对命令见[第二轮报告](archive/DIAGNOSTICS_ROUND2.zh-CN.md)。主分支作者环境/权重另依主分支复现说明配置，不能用这些命令覆盖它。

## 3. 常见启动故障

| 提示/现象 | 处理 |
| --- | --- |
| `-bash ... syntax error ... (` | 把 PowerShell 贴进 Bash；`exit` 回到 `PS ...>` 再运行 Windows 单行入口 |
| `Join-Path ... Path ... 空值` | 旧多行命令被合并；改用当前单行入口，无需手设变量 |
| 相机 busy / 无帧 | 关闭其他占用相机的程序，检查 USB3 接口/线缆；保留错误会话 |
| Expected one physical CH343 | 系统未找到实体 USB 转串口；检查独立供电/USB，别选虚拟 COM2/COM3 |
| Address already in use | 同类会话未停止；回原窗口 Ctrl+C，等退出后重开；不要全局杀所有 WSL/ROS 进程 |
| RViz 无话题 | 确认采集入口正在运行；source Humble；domain 相机 83/雷达 84；ROS_LOCALHOST_ONLY=1 |
| RViz TF 错误 | 原始/odom/map 使用对应配置；若里程计 LOST，先改善输入；不要随便发单位 TF 掩盖错误 |
| `Stereo is NOT SUPPORTED` | RViz 的立体显示器提示，本机普通 3D 显示可用；不是说 D435 双目算法不受支持 |
| WSL localhost proxy 警告 | 本机曾有失效代理配置；回环桥接已验证可用。网络下载与传感器收流分开排查 |

入口绑定本机回环、使用会话令牌，不开放局域网传感器服务。自动开启的 WSL 辅助程序隐藏运行，RViz 通过 WSLg 可见；按 Ctrl+C 释放设备并保存结果。每次使用新 data 子目录，长时间原始录像会快速占用磁盘，先用 20–60 秒会话。
