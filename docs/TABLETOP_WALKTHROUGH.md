# Box cup and paper notebook experiment walkthrough

English | [中文](TABLETOP_WALKTHROUGH.zh-CN.md)

For this configured Windows/WSL computer and its D435/L2. First collect four fixed-sensor events per modality, then test odometry and author inputs separately. Paste one command block at a time. The [Chinese walkthrough](TABLETOP_WALKTHROUGH.zh-CN.md) includes every command for native loader and LiDAR-core checks; this companion covers the complete capture workflow and its evaluation boundaries.

## 1. Arrange the scene

Use B01 for the central box, C01 for the cup on its left, and N01 for the paper notebook on its right. Leave a wall corner, table and textured background visible. Start with the camera roughly 1–2 m away, adjusted for valid depth; hold placement and parameters constant within a modality. Prefer an opaque empty cup. Record transparent/reflective depth holes as a separate condition.

Face the notebook cover toward the sensor if it can stand securely; otherwise lay it flat and evaluate visible cover support. Do not lean it against the box, which will move separately. Thin edges may provide few L2 returns. Mark box positions A and B. Measure 30 cm if a ruler is available; otherwise label displacement unmeasured and retain a qualitative movement trial. Photograph the layout and record independent event video when possible.

The notebook becomes the occluder only in the occlusion trial, so exclude it from that trial's static-support labels. Keep the cup and background stable. Verify actual occlusion separately for camera and LiDAR views.

## 2. Open PowerShell and preview

Win+X → Terminal/Windows PowerShell, window A. The prompt must begin `PS`. If it is a Bash prompt, enter `exit` first.

```powershell
Set-Location -LiteralPath D:\workspace\be2\Personal-Learning-Physical
```

```powershell
[math]::Round((Get-PSDrive D).Free / 1GB, 1)
```

Allow roughly 30 GiB for four camera trials and checks, then review actual usage. Four-stream raw recording is much larger than MP4. Approximately 71 GiB was available when preparing this guide.

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\start_live.ps1 -Sensor camera -Video -CheckOnly
```

Expect `Environment check passed. Sensors were not opened.` Then preview:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\start_live.ps1 -Sensor camera
```

The script opens WSL and RViz. Show RGB, Depth 0-5m, Left/Right IR and Current cloud from Displays. Check that all three objects fit, stationary text is readable and the box has valid depth. Black depth means invalid; reflective cup holes and projector dots in IR can occur. Drag/zoom the 3D view. A raw preview has no trajectory. Once arranged, keep the sensor fixed, Ctrl+C in A and wait for `Saved session`.

## 3. Capture each camera event

In A, start one unlimited raw capture with video:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\start_live.ps1 -Sensor camera -Algorithm sensor -SessionType stationary -Record -Video
```

`stationary` declares the sensor fixed throughout the entire recording, including before/after the timer. Objects may move in the specified event. Wait for a real updating RViz view.

Open a second PowerShell, window B:

```powershell
Set-Location -LiteralPath D:\workspace\be2\Personal-Learning-Physical
```

Run exactly one timer command per fresh capture:

```powershell
.venv\Scripts\python.exe scripts\scene_timeline.py --latest camera --event static --fixed-sensor
```

```powershell
.venv\Scripts\python.exe scripts\scene_timeline.py --latest camera --event occlusion --fixed-sensor
```

```powershell
.venv\Scripts\python.exe scripts\scene_timeline.py --latest camera --event removal --fixed-sensor
```

```powershell
.venv\Scripts\python.exe scripts\scene_timeline.py --latest camera --event move --fixed-sensor
```

Confirm B's SESSION matches A. The timer counts down five seconds, then runs this schedule:

| Time | Action |
| --- | --- |
| 0–20 s | Keep original layout |
| 20 s | Start the event; aim to finish by 25 s and press SPACE in B |
| 25–60 s | Hold the new state; mark late completion honestly |
| 60 s | Restore original layout; aim to finish by 65 s and press SPACE again |
| 65–80 s | Hold the restored state |
| 80 s | Ctrl+C in A and wait for capture/video finalization |

Static: touch nothing throughout. Occlusion: place the notebook before the box without moving the box, then return the notebook; label partial occlusion honestly if the notebook cannot cover it. Removal: remove the box and expose its former space/background, then return it to A. Movement: move the box A→B, then back A, keeping cup/notebook fixed.

The timer does not stop capture. A keypress is an operator completion report, including keyboard-return delay, not detected motion. Cues do not establish actual completion. Missing marks remain missing. If the sensor is bumped or an action fails, press Q in B, stop A and start a fresh session. Aborted trials retain data and withdraw the fixed-export declaration.

## 4. Inspect and verify

Outputs include `raw.db3`, `rviz-live.mp4`, capture/results JSON, `session-note.json`, `trial-scene.json` and `events.csv`. This video is raw RGB-D preview, not semantic mapping.

Immediately after the static capture, save its directory in B:

```powershell
$taskCameraStatic = Get-ChildItem -LiteralPath .\data -Directory -Filter 'live-camera-*' | Sort-Object Name -Descending | Select-Object -First 1 -ExpandProperty FullName
```

```powershell
Invoke-Item -LiteralPath $taskCameraStatic
```

```powershell
Get-Content -LiteralPath (Join-Path $taskCameraStatic 'trial-scene.json')
```

Expect `timeline_completed`; nonstatic events require both completion marks. Physical verification remains false and measured displacement remains null until independently documented. If B was closed, set the variable to the verified static session path rather than assuming the latest session is static.

After capture stops:

```powershell
.venv\Scripts\python.exe scripts\verify_camera_recording.py (Join-Path $taskCameraStatic 'raw.db3') --output (Join-Path $taskCameraStatic 'raw-replay-check.json')
```

Expect `verified` and matching four-stream counts. Use a new evidence filename for another check; never overwrite failures.

## 5. Repeat for L2

Stop camera capture first. Power L2 independently, fix its base and preview sufficient returns from the scene. Do not hard-code a COM number; the launcher resolves the physical CH343 port.

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\start_live.ps1 -Sensor lidar -Video -CheckOnly
```

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\start_live.ps1 -Sensor lidar
```

Use Current cloud / Intensity in RViz. Sparse changing scan coverage is expected; no trajectory in sensor mode. Stop preview with Ctrl+C. For each event, restart A:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\start_live.ps1 -Sensor lidar -Algorithm sensor -SessionType stationary -Lines 50 -Record -Video
```

In B, run one matching command per new session:

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

Follow the same actions and SPACE marks, then stop A after 80 s and wait for saving. Immediately after the static session:

```powershell
$taskLidarStatic = Get-ChildItem -LiteralPath .\data -Directory -Filter 'live-lidar-*' | Sort-Object Name -Descending | Select-Object -First 1 -ExpandProperty FullName
```

```powershell
.venv\Scripts\python.exe scripts\audit_l2.py $taskLidarStatic
```

Inspect `audit.json` and `capture.json`: point/IMU packets nonzero, few CRC/sequence losses. Current reference rates are about 216 lines/s, 250 IMU packets/s and 4.3 groups/s with 50 lines. The live receive CSV lacks the packet timing table needed for all offline audit rates; use capture fields 102/104 too. L2 time scaling near 2 remains unresolved; no LIO/fusion acceptance follows.

## 6. WSL RViz and algorithms

For a live source, open window C and enter `wsl -d Ubuntu-22.04`. In Bash, separately run `source /opt/ros/humble/setup.bash`, then `export ROS_DOMAIN_ID=83 ROS_LOCALHOST_ONLY=1`, then `ros2 topic list`. Use domain 84 for L2. Manual RViz configurations are `configs/rviz/camera_raw.rviz` and `lidar_raw.rviz`; close manually opened RViz yourself. Detailed copyable commands are in the [Chinese walkthrough](TABLETOP_WALKTHROUGH.zh-CN.md#8-手动进入-wsl-查看话题与-rviz) and the [camera](CAMERA_GUIDE.md)/[LiDAR](LIDAR_GUIDE.md) guides.

For separate fixed 60 s odometry tests, keep all objects still, run one command at a time and do not start the event timer:

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

Initial goals: trajectory near origin, translation excursion <5 cm, rotation <2°, valid steady-state coverage >95%. KISS has no native LOST field. Earlier fixed L2 trials failed; preserve new failures. Separate captures do not support a fair algorithm ranking.

For an optional moving-camera mapping demonstration, keep objects still, pause five seconds at the start, move slowly, revisit and stop with Ctrl+C:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\start_live.ps1 -Sensor camera -Algorithm rgbd-slam -SessionType motion -Record -Video
```

Enable RGB-D global map. Keyframes accumulate; loop closure is conditional. This is RTAB-Map, not ConceptGraphs/HOV-SG, and moving input cannot use identity-pose export.

## 7. Author inputs and quality goals

The [Chinese walkthrough section 10](TABLETOP_WALKTHROUGH.zh-CN.md#10-真正接入四个作者核心) gives full Windows export, WSL loader, official L2 decoding, DUFOMap, BeautyMap and rendering commands. Export eight static RGB-D frames first, then expect each native loader to pass 8/8. These commands do not run SAM/CLIP mapping. Freeze query texts before outcomes: `a box`, `a cup`, `a paper notebook`.

Actual physical semantic cores and full-event time-aligned adapters remain pending. Existing LiDAR input smoke consumes approximately 40 s, not the full 80 s event. Original BeautyMap boundary failures and padded diagnostics remain separate. Do not invent unsupported `-Algorithm conceptgraphs` options or quality scores from loader success.

Four pilots per modality establish raw replay, video and event records. Formal goals are static deletion <5%, visible-removal recall >80% and independently referenced surface-anchor error <10 cm; missing labels/measurements leave scores empty. Follow the [comparison protocol](../METHOD_COMPARISON.md) for common inputs, validation/test sessions, low-light factors and delayed pose correction. Raw indoor media stays in ignored `data/`; main remains untouched and unmerged.
