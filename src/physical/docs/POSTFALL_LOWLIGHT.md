# Post-fall, low-light and concurrent sensor checks

English | [中文](POSTFALL_LOWLIGHT.zh-CN.md)

Basic camera function passed initial checks; post-fall absolute depth accuracy is unverified. L2 recovered valid points/IMU after power checks. Raw recordings and indoor videos remain local; [numeric evidence](../evidence/postfall-dual-lowlight-20261009.json) is portable.

## 1. Camera and projector

The SDK reports D435, USB 3.2, no IMU, firmware 5.17.0.10. No firmware, calibration or self-calibration was changed. Raw four-stream replay and sampled stereo geometry passed initial screening, with a startup pause still needing cold-start checks.

Three 25-second projector on/off/on recordings restore the original setting. Depth behavior matches low-texture expectations; RGB is not brightened by IR projection. No lux meter, independent distance or new fixed-state declaration exists.

L2 remains active in all three runs, about 1.5 million valid points each. Native SDK and local decode agree on the checked segment. Without an L2-off control or controlled targets, this does not rule out optical interference.

## 2. Simultaneous operation

Two paired sessions verify coexistence, separate algorithms and four valid RViz videos. Camera domain/port is 83/17635; LiDAR is 84/17636. Their origins are independent, not a fused `/odom`.

Camera input is about 8.11/8.17 Hz with 97.51/98.14% valid coverage. The strict 99% gate fails. KISS's 100% output is not a quality guarantee; LiDAR poses still wander. Preserve the small CRC/sequence losses rather than calling all runs error-free.

## 3. Timing and limits

Nearest line-packet receipt p95 offsets are about 2.20–2.22 ms; 50-line cloud-end matching is about 110 ms. A nearby individual packet does not synchronize the whole ≈0.23 s cloud. Host QPC resolution 100 ns is not sensor timing accuracy.

Next verify cold starts, independently measured depth, confirmed-fixed LiDAR, device clock/IMU, rigid extrinsics and controlled reprojection. Initial fixed-odometry targets remain <5 cm/<2°. No LIO, cross-sensor fusion, moving trajectory accuracy or hardware semantic quality is accepted. [Test plan](TEST_PLAN.md).

Start the two sensor sessions in separate Windows PowerShell windows, with the first view running before the second recorder. Never open the same sensor twice. [Full session evidence and commands](POSTFALL_LOWLIGHT.zh-CN.md).

## 4. Commands

Use the shell shown by each block. Keep the order, use new output names, and check whether the task has already run before starting it.

```powershell
Set-Location -LiteralPath D:\workspace\be2\Personal-Learning-Physical
.venv\Scripts\python.exe scripts\verify_camera_recording.py data\postfall-dark-probe-20261009-022442\camera\raw.db3 --output data\postfall-dark-probe-20261009-022442\camera\playback-recheck.json
.venv\Scripts\python.exe scripts\export_stereo.py data\postfall-dark-probe-20261009-022442\camera\raw.db3 --stride 15 --output data\postfall-stereo-recheck
.venv\Scripts\python.exe scripts\audit_camera_health.py data\postfall-dark-probe-20261009-022442\camera --stereo data\postfall-stereo-recheck --reference-capture data\static-20261008-221334\camera\capture.json --output data\postfall-health-recheck
```

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\capture_pair.ps1 -Seconds 25 -Session lowlight-on-a -Emitter on
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\capture_pair.ps1 -Seconds 25 -Session lowlight-off-b -Emitter off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\capture_pair.ps1 -Seconds 25 -Session lowlight-on-c -Emitter on
```

```text
D:\workspace\be2\Personal-Learning-Physical\data\live-camera-20261009-023303-779\rviz-live.mp4   RGB-D
D:\workspace\be2\Personal-Learning-Physical\data\live-lidar-20261009-023307-581\rviz-live.mp4    ICP
D:\workspace\be2\Personal-Learning-Physical\data\live-camera-20261009-023416-505\rviz-live.mp4   IR stereo
D:\workspace\be2\Personal-Learning-Physical\data\live-lidar-20261009-023420-197\rviz-live.mp4    KISS
```

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File D:\workspace\be2\Personal-Learning-Physical\scripts\start_live.ps1 -Sensor camera -Algorithm stereo -SessionType preview -Seconds 60 -Record -Video
```

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File D:\workspace\be2\Personal-Learning-Physical\scripts\start_live.ps1 -Sensor lidar -Algorithm kiss -SessionType preview -Seconds 60 -Record -Video
```

```powershell
Set-Location -LiteralPath D:\workspace\be2\Personal-Learning-Physical
.venv\Scripts\python.exe scripts\audit_pair.py data\dark-on-qpc-a-20261009-023004 --output data\pair-time-recheck
```
