# Automatic RViz recording

English | [中文](SIMPLE_RECORDING.zh-CN.md)

Tabletop objects are sufficient for an input/tracking demonstration. Record the new layout; it is not independent object-position truth.

## 1. Video contract

`-Video -Record` saves an independent RViz view plus raw data. Screen capture is 10 fps, separate from actual ROS/algorithm input rate. Startup/teardown and repeated screen frames stay visible; no audio is recorded. Interactive mouse movements affect a different RViz window.

| Output | Meaning |
| --- | --- |
| `rviz-live.mp4`, `video.json` | H.264 video and encoding/exit metadata |
| `raw.db3` | Raw sensor replay source, not an ordinary video |
| `live-result.json`, `poses.json`, `status.json` | Measured algorithm outputs |
| `scene-note.json` | Human scene note, not automatic object recognition |

## 2. Preserved examples

The adjusted `live-camera-20261009-012157-871` recording is 35 s, 1440×1000, 350 frames. It visibly contains the stated tissue/box/bottle; the algorithm did not identify or measure their movement. RGB-D has 156 inputs/155 poses, LOST=0, without stationary or trajectory truth. [Evidence](../evidence/video-tabletop-adjusted-20261009.json).

The earlier 35.9 s example and failed recorder remain preserved. Objects not clearly visible are not added to its claim. [Earlier review](../evidence/video-demo-20261009.json).

## 3. Next motion and local media

Separate camera motion from object motion. For object change, fix the camera and record one measured move and event time. No indoor media is pushed to GitHub. Existing raw data also supports [unattended replay](OFFLINE_REPLAY.md).

## 4. Commands

Use the shell shown by each block. Keep the order, use new output names, and check whether the task has already run before starting it.

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File D:\workspace\be2\Personal-Learning-Physical\scripts\start_live.ps1 -Sensor camera -Algorithm rgbd -Seconds 30 -Video -Record -NoGui
```
