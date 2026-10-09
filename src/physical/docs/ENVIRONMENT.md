# Local environment and recovery

English | [中文](ENVIRONMENT.zh-CN.md)

The current hardware project root is `src/physical/` inside this repository. Earlier device data and caches remain in the retained standalone checkout. Rebuild commands below use the current directory; historical reports retain their original paths.

This is a host-specific configuration, not a portable machine image. Git contains code, configuration and lightweight evidence; recordings, SDK caches, weights and environments stay local.

## 1. Installed components

| Location | Role |
| --- | --- |
| Windows `.venv` | Python 3.12, RealSense, NumPy, OpenCV-headless, pyserial; `requirements.txt` |
| Ubuntu-22.04 `/opt/ros/humble` | ROS2 Humble, RViz, RTAB-Map 0.23.7, system Python 3.10, scientific libraries and ffmpeg |
| WSL `.cache/kiss-venv` | KISS-ICP 1.3.0, separate NumPy ABI; `requirements-kiss-wsl.txt` |
| `.cache/unilidar_sdk2` | Pinned official SDK geometry/decode reference |

`-CheckOnly` checks software, not live devices. Create environments only when absent; do not overwrite main's author environments. New hosts also require compatible ROS/WSLg dependencies from official installers.

## 2. Troubleshooting

| Symptom | Check |
| --- | --- |
| Bash syntax error after a Windows command | Return to the `PS ...>` prompt |
| Camera busy/no frames | Existing camera owner, USB3 cable and port |
| Physical CH343 not found | Power/physical USB; do not select a virtual COM port |
| Address in use | Stop the previous session with Ctrl+C; no global process kill |
| RViz topics missing | Source Humble; camera domain 83 or LiDAR 84; localhost-only |
| TF queue errors | Correct raw/odom/map view and tracking input; no artificial identity TF |
| `Stereo is NOT SUPPORTED` | Display stereoscopy warning; ordinary 3D still works |

The loopback transport uses session tokens. Ctrl+C releases the owned devices and saves results. Start with 20–60 s recordings; raw data grows quickly. [Detailed recovery](ENVIRONMENT.zh-CN.md).

## 3. Commands

Use the shell shown by each block. Keep the order, use new output names, and check whether the task has already run before starting it.

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File D:\workspace\be2\SLAM_Personal_Guide\src\physical\scripts\start_live.ps1 -CheckOnly
```

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File D:\workspace\be2\SLAM_Personal_Guide\src\physical\scripts\start_live.ps1 -Sensor lidar -Algorithm kiss -CheckOnly
```

```powershell
Set-Location -LiteralPath D:\workspace\be2\SLAM_Personal_Guide\src\physical
```

```powershell
& C:\Users\qzl\AppData\Local\Programs\Python\Python312\python.exe -m venv .venv
```

```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

```bash
cd /mnt/d/workspace/be2/Personal-Learning-Physical
```

```bash
python3 -m venv .cache/kiss-venv
```

```bash
.cache/kiss-venv/bin/python -m pip install -r requirements-kiss-wsl.txt
```
