<div align="center">

# Personal-Learning-Physical

</div>

English | [中文](README.zh-CN.md)

D435 and Unitree L2 capture, odometry trials and hardware-input checks. This branch remains separate from main; original recordings and indoor videos stay local.

## 1. Background and objectives

Occlusion, removal, object movement and historical pose correction change spatial correspondence. We test whether stable geometry survives, queried target coordinates remain valid, and reassociation improves recovery over simple protection.

Replay one room recording within each task group: DUFOMap/BeautyMap for map cleaning, ConceptGraphs/HOV-SG for semantic targets. Match input, poses, events and budgets, then score the groups separately. The [common-scene comparison design](METHOD_COMPARISON.md) specifies events, expected video, metrics, budgets and failure rules. Quality comparison remains pending beyond existing streaming and loader checks.

## 2. Start here

| Task | Guide |
| --- | --- |
| Shared research question and cross-repository experiments | [Comparison design](METHOD_COMPARISON.md) |
| Camera preview, stereo/RGB-D and mapping | [Camera](docs/CAMERA_GUIDE.md) |
| L2 preview, ICP/KISS and LIO prerequisites | [LiDAR](docs/LIDAR_GUIDE.md) |
| Controlled motions and acceptance targets | [Test plan](docs/TEST_PLAN.md) |
| Mapping-core adapters and future integration | [Integration](docs/MAIN_INTEGRATION.md) |
| Real RGB-D export and native loader checks | [RGB-D input](docs/RGBD_MAIN_INPUT.md) |
| Environment and startup errors | [Environment](docs/ENVIRONMENT.md) |
| Actual execution and failures | [Live checks](docs/LIVE_VALIDATION.md), [round 4](docs/CAMERA_TEST_ROUND4.md) |
| Full video and same-recording comparisons | [Recording](docs/SIMPLE_RECORDING.md), [replay](docs/OFFLINE_REPLAY.md) |
| Post-fall and concurrent low-light checks | [Latest hardware checks](docs/POSTFALL_LOWLIGHT.md) |
| File roles and historical evidence | [Cleanup](docs/CLEANUP.md), [archive](docs/archive/INDEX.md) |

## 3. Minimal start

In Windows PowerShell, start one session per sensor. Ctrl+C stops it and saves results.

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File D:\workspace\be2\Personal-Learning-Physical\scripts\start_live.ps1 -Sensor camera
```

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File D:\workspace\be2\Personal-Learning-Physical\scripts\start_live.ps1 -Sensor lidar
```

## 4. Current boundaries

The SDK reports **D435 without IMU**. Four-stream replay and initial stereo checks pass; post-fall absolute depth accuracy remains unmeasured. Improved live camera input is about 8 Hz, not a 30 Hz algorithm guarantee; strict 99% coverage still has failures.

L2 streaming recovered after power checks. Earlier fixed ICP/KISS drift failed; device-time scaling, IMU, LIO and cross-sensor fusion remain unresolved. Two simultaneous streams are not fusion.

DUFOMap fixed-input processing ran. BeautyMap's original small-map boundary error remains; padding is a separate diagnostic. Both semantic native loaders passed 8/8 real RGB-D frames, but hardware SAM/CLIP mapping and semantic quality have not run.

`scripts/`, `configs/rviz/`, `docs/` and lightweight `evidence/` are portable. `data/`, environments, SDK caches and indoor media are local; a fresh clone does not contain earlier videos.
