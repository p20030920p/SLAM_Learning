# Hardware Practice

English | [中文](README.zh-CN.md)

D435 / Unitree L2 capture, odometry trials and mapping-input checks.

## Guides

| Task | Entry |
| --- | --- |
| Setup and capture | [Environment](docs/ENVIRONMENT.md) · [Camera](docs/CAMERA_GUIDE.md) · [LiDAR](docs/LIDAR_GUIDE.md) |
| Controlled experiments | [Walkthrough](docs/TABLETOP_WALKTHROUGH.md) · [Design](METHOD_COMPARISON.md) |
| Mapping and replay | [Integration](docs/MAIN_INTEGRATION.md) · [RGB-D](docs/RGBD_MAIN_INPUT.md) · [Replay](docs/OFFLINE_REPLAY.md) |
| Recorded checks | [Validation](docs/LIVE_VALIDATION.md) · [Latest checks](docs/POSTFALL_LOWLIGHT.md) · [Archive](docs/archive/INDEX.md) |

## Usage

After [setup](docs/ENVIRONMENT.md), run from the repository root in PowerShell:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File src/physical/scripts/start_live.ps1 -Sensor camera
powershell.exe -NoProfile -ExecutionPolicy Bypass -File src/physical/scripts/start_live.ps1 -Sensor lidar
```

Use a separate terminal for each sensor; Ctrl+C saves the session. Internal scripts use `src/physical/` as their project root. Original machine paths in detailed logs remain historical.

## Status

D435 has no IMU. Capture and 8/8-frame semantic loader checks passed; hardware semantic mapping remains in progress. L2 streaming recovered, while earlier ICP/KISS drift checks failed. Full recordings, SDK caches and environments stay local.
